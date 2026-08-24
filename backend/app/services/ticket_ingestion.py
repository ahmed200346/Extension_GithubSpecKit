import hashlib
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models import (
    Project,
    Artifact,
    Ticket,
    TicketStatus,
    TicketEvent,
    TicketEventType,
    AuthorType,
)
from app.utils.path_builder import BASE_DIR, extract_project_name_from_path


# ─────────────────────────────────────────────────────────────────────────────
# current-task.json  — single source of truth for in_progress / done
# ─────────────────────────────────────────────────────────────────────────────

_CURRENT_TASK_FILE = BASE_DIR / ".task_runtime" / "current-task.json"


def _read_current_task() -> Dict[str, Any]:
    """
    Read .task_runtime/current-task.json.
    Never cached — every call sees the latest write from the orchestrator.
    Returns {} if the file is missing or malformed.
    """
    try:
        if _CURRENT_TASK_FILE.exists():
            return json.loads(_CURRENT_TASK_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _write_current_task(task_id: str, status: str) -> None:
    """
    Write-back ticket status to .task_runtime/current-task.json.
    Maintains the 'tasks' map and updates the top-level status if the ticket is the current one.
    """
    try:
        data = _read_current_task()
        if not data:
            # If the file is missing or empty, we don't have enough context (project_name, etc.)
            # to create a new valid current-task.json from scratch.
            return

        # 1. Update the full tasks map
        tasks = data.get("tasks", {})
        if not isinstance(tasks, dict):
            tasks = {}
        tasks[task_id] = status
        data["tasks"] = tasks

        # 2. Update top-level status if this is the active task
        if data.get("task_id") == task_id:
            data["status"] = status

        # 3. Update timestamp
        data["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # 4. Atomic write (temp file -> replace)
        temp_file = _CURRENT_TASK_FILE.with_suffix(".json.tmp")
        temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp_file.replace(_CURRENT_TASK_FILE)
    except Exception as e:
        # We log and swallow the error to ensure that a file write failure
        # doesn't crash the primary database update flow.
        import logging
        logging.getLogger(__name__).error(f"[WriteBack] Failed to update current-task.json: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Parsing helpers
# ─────────────────────────────────────────────────────────────────────────────

def compute_file_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_task_lines(content: str) -> List[Dict[str, Any]]:
    """
    Parse a tasks.md file and return one dict per task:
        id, title, description, checkbox_state, line_number
    checkbox_state is stored for display purposes only — it does NOT drive status.
    """
    lines = content.splitlines()
    tasks_by_id: Dict[str, Dict[str, Any]] = {}
    in_task_list = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        task_match = re.match(r'^-\s*\[([xX\s~/])\]\s*(.+)$', stripped)
        if task_match:
            checkbox = task_match.group(1)
            task_text = task_match.group(2).strip()

            id_match = re.match(r'^(T\d+)', task_text)
            task_id = id_match.group(1) if id_match else f"task_{len(tasks_by_id) + 1}"

            if checkbox.lower() == 'x':
                checkbox_state = "checked"
            elif checkbox in ('~', '/'):
                checkbox_state = "in_progress"
            else:
                checkbox_state = "unchecked"

            title = task_text
            if id_match:
                title = task_text[len(task_id):].strip().lstrip(":- ").strip()

            task_data = {
                "id": task_id,
                "title": title or task_text,
                "description": "",
                "checkbox_state": checkbox_state,
                "line_number": i,
            }

            # Keep first occurrence per ID (no status-based dedup needed)
            if task_id not in tasks_by_id:
                tasks_by_id[task_id] = task_data

            in_task_list = True
            continue

        if in_task_list and stripped and not stripped.startswith("- ["):
            if tasks_by_id and not stripped.startswith("#"):
                latest = max(tasks_by_id.values(), key=lambda t: t["line_number"])
                latest["description"] += ("\n" if latest["description"] else "") + stripped
        elif stripped.startswith("#"):
            in_task_list = False

    return sorted(tasks_by_id.values(), key=lambda t: t["line_number"])


# ─────────────────────────────────────────────────────────────────────────────
# Status helper (used only by update_ticket_status API, not ingestion)
# ─────────────────────────────────────────────────────────────────────────────

def can_auto_transition(current: TicketStatus, target: TicketStatus) -> bool:
    order = {TicketStatus.todo: 0, TicketStatus.in_progress: 1, TicketStatus.done: 2}
    return order.get(target, 0) >= order.get(current, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Core ingestion
# ─────────────────────────────────────────────────────────────────────────────

def ingest_task_file(
    db: Session,
    file_path: Path,
    project: Project,
    artifact: Optional[Artifact] = None,
) -> List[Ticket]:
    """
    Ingest a single tasks.md file into the tickets table.

    Status rules — simple and absolute:
    • Ingestion ALWAYS sets / keeps every ticket as `todo`.
    • Only current-task.json can set a ticket to `in_progress` or `done`.
    • The `_sync_current_task_to_db` watcher in main.py handles that promotion.
    • Checkbox state is stored for display only; it NEVER drives status here.
    """
    file_path_str = str(file_path.resolve())
    content = file_path.read_text(encoding="utf-8")
    file_hash = compute_file_hash(content)
    parsed_tasks = parse_task_lines(content)

    tickets = []

    for position, parsed in enumerate(parsed_tasks):
        task_source_path = f"{file_path_str}#{parsed['id']}"

        existing_ticket = (
            db.query(Ticket)
            .filter(
                Ticket.project_id == project.id,
                Ticket.source_file_path == task_source_path,
            )
            .first()
        )

        if existing_ticket:
            # Update metadata (title, description, checkbox display, hash).
            # Never touch the status — the watcher owns it.
            changed = False

            if existing_ticket.title != parsed["title"]:
                existing_ticket.title = parsed["title"]
                changed = True
            if existing_ticket.description != parsed["description"]:
                existing_ticket.description = parsed["description"]
                changed = True
            if existing_ticket.checkbox_state != parsed["checkbox_state"]:
                existing_ticket.checkbox_state = parsed["checkbox_state"]
                changed = True
            if existing_ticket.source_file_hash != file_hash:
                existing_ticket.source_file_hash = file_hash
                changed = True
            if existing_ticket.line_number != parsed["line_number"]:
                existing_ticket.line_number = parsed["line_number"]
                changed = True

            if changed:
                db.add(existing_ticket)
                db.commit()
                db.refresh(existing_ticket)

            tickets.append(existing_ticket)

        else:
            # Brand-new ticket → always starts as todo.
            ticket = Ticket(
                project_id=project.id,
                ticket_id=parsed.get("id"),  # Le ticket_id du fichier (ex: "T001")
                source_file_path=task_source_path,
                title=parsed["title"],
                description=parsed["description"],
                status=TicketStatus.todo,
                line_number=parsed["line_number"],
                checkbox_state=parsed["checkbox_state"],
                source_file_hash=file_hash,
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)

            db.add(TicketEvent(
                ticket_id=ticket.id,
                event_type=TicketEventType.status_change,
                author_type=AuthorType.agent,
                event_metadata={"from": None, "to": TicketStatus.todo.value, "source": "initial_ingestion"},
            ))
            db.commit()

            tickets.append(ticket)

    return tickets


def ingest_all_tasks(
    db: Session,
    tasks_dir: Path,
    project_name: Optional[str] = None,
) -> List[Ticket]:
    """
    Scan a directory for tasks.md and ingest it.  Idempotent.
    """
    if not tasks_dir.exists():
        return []

    if not project_name:
        project_name = extract_project_name_from_path(tasks_dir)

    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        project = Project(name=project_name)
        db.add(project)
        db.commit()
        db.refresh(project)

    task_files = [tasks_dir / "tasks.md"]
    if not task_files[0].exists():
        task_files = sorted(tasks_dir.glob("*.md"))

    all_tickets = []
    for task_file in task_files:
        artifact = (
            db.query(Artifact)
            .filter(
                Artifact.project_id == project.id,
                Artifact.source_path == str(task_file.resolve()),
            )
            .first()
        )
        all_tickets.extend(ingest_task_file(db, task_file, project, artifact))

    return all_tickets


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_ticket_by_id(db: Session, ticket_id: str) -> Optional[Ticket]:
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets_by_project(
    db: Session,
    project_id: str,
    status_filter: Optional[str] = None,
) -> List[Ticket]:
    query = db.query(Ticket).filter(Ticket.project_id == project_id)
    if status_filter:
        try:
            query = query.filter(Ticket.status == TicketStatus(status_filter))
        except ValueError:
            pass
    return query.order_by(Ticket.line_number).all()


def update_ticket_status(
    db: Session,
    ticket_id: str,
    new_status: str,
    author_type: AuthorType = AuthorType.human,
    source: str = "api_patch",
) -> Optional[Ticket]:
    """
    Explicit status update (called by the sync watcher and the PATCH API).
    Always applies — no forward-only restriction at this layer.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None

    try:
        target_status = TicketStatus(new_status)
    except ValueError:
        return None

    old_status = ticket.status
    if old_status == target_status:
        return ticket

    event_type = (
        TicketEventType.status_change
        if can_auto_transition(old_status, target_status)
        else TicketEventType.status_override
    )

    ticket.status = target_status
    db.add(TicketEvent(
        ticket_id=ticket.id,
        event_type=event_type,
        author_type=author_type,
        event_metadata={"from": old_status.value, "to": target_status.value, "source": source},
    ))
    db.commit()
    db.refresh(ticket)

    # Write-back to current-task.json to keep AI and Watcher in sync
    _write_current_task(ticket.ticket_id, target_status.value)

    return ticket


def add_ticket_comment(
    db: Session,
    ticket_id: str,
    body: str,
    author_type: AuthorType = AuthorType.human,
) -> Optional[Ticket]:
    from app.models import TicketComment

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None

    comment = TicketComment(ticket_id=ticket.id, author_type=author_type, body=body)
    db.add(comment)
    db.add(TicketEvent(
        ticket_id=ticket.id,
        event_type=TicketEventType.comment_added,
        author_type=author_type,
        event_metadata={"comment_id": str(comment.id)},
    ))
    db.commit()
    db.refresh(comment)
    return comment


def add_agent_comment(db: Session, ticket_id: str, body: str):
    return add_ticket_comment(db, ticket_id, body, AuthorType.agent)


def get_ticket_events(db: Session, ticket_id: str) -> List[TicketEvent]:
    return (
        db.query(TicketEvent)
        .filter(TicketEvent.ticket_id == ticket_id)
        .order_by(TicketEvent.created_at)
        .all()
    )


def get_ticket_comments(db: Session, ticket_id: str) -> List:
    from app.models import TicketComment
    return (
        db.query(TicketComment)
        .filter(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at)
        .all()
    )


def get_project_progress(db: Session, project_id: str) -> Dict[str, Any]:
    tickets = db.query(Ticket).filter(Ticket.project_id == project_id).all()
    total = len(tickets)
    done = sum(1 for t in tickets if t.status == TicketStatus.done)
    in_progress = sum(1 for t in tickets if t.status == TicketStatus.in_progress)
    todo = sum(1 for t in tickets if t.status == TicketStatus.todo)
    return {
        "total": total,
        "done": done,
        "in_progress": in_progress,
        "todo": todo,
        "progress_pct": round(done / total * 100, 1) if total > 0 else 0.0,
    }


def find_tickets_by_commit_message(
    db: Session,
    commit_message: str,
    project_id: str,
) -> List[Ticket]:
    ticket_ids = re.findall(r'\bT(\d+)\b', commit_message, re.IGNORECASE)
    tickets = []
    for tid in ticket_ids:
        ticket = db.query(Ticket).filter(
            Ticket.project_id == project_id,
            Ticket.title.contains(f"T{tid}"),
        ).first()
        if ticket:
            tickets.append(ticket)
    return tickets


def apply_commit_refinement(
    db: Session,
    commit_message: str,
    project_id: str,
) -> List[Ticket]:
    tickets = find_tickets_by_commit_message(db, commit_message, project_id)
    msg_lower = commit_message.lower()
    for ticket in tickets:
        if any(w in msg_lower for w in ["finish", "complete", "done", "close"]):
            update_ticket_status(db, str(ticket.id), "done", AuthorType.agent, source="commit_refinement")
        elif any(w in msg_lower for w in ["start", "begin", "implement", "wip"]):
            update_ticket_status(db, str(ticket.id), "in_progress", AuthorType.agent, source="commit_refinement")
    return tickets
