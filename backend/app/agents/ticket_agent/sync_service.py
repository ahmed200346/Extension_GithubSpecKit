"""
Sync Service — Pure Database Synchronization Logic

Extracted from main.py to provide a clean, testable service for
updating ticket statuses in the database based on current-task.json.

Supports:
- Real-time sync from current-task.json (StatusWatcher)
- Full state refresh: scans entire project for complete synchronization
- Structure sync: prepares for ingestion from tasks.md (StructureWatcher)
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import (
    Ticket,
    Project,
    TicketStatus,
    AuthorType,
    TicketEvent,
    TicketEventType,
)
from app.services.ticket_ingestion import update_ticket_status, parse_task_lines
# Import inside functions to avoid circular import with manager.py
# from app.agents.ticket_agent.manager import get_ticket_manager
from app.utils.path_builder import BASE_DIR

logger = logging.getLogger(__name__)


class SyncService:
    """
    Service responsible for synchronizing ticket statuses to the database.

    Three sync modes:
    1. sync_current_task() - Real-time from current-task.json (StatusWatcher)
    2. full_state_refresh() - Complete project scan for consistency (Refresh button)
    3. prepare_structure_sync() - Reads tasks.md for ingestion prep (StructureWatcher)
    """

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or settings.TARGET_PROJECT_PATH or str(BASE_DIR)
        self._current_task_file = Path(self.project_path) / ".task_runtime" / "current-task.json"
        self._project_root = Path(self.project_path)

    @property
    def current_task_file(self) -> Path:
        return self._current_task_file

    @property
    def project_root(self) -> Path:
        return self._project_root

    # ═══════════════════════════════════════════════════════════════════════
    # 1. REAL-TIME SYNC (current-task.json → DB)
    # ═══════════════════════════════════════════════════════════════════════

    async def sync_current_task(self) -> Dict[str, Any]:
        """
        Read current-task.json and update ticket statuses in the DB.

        Two things are synced:
        - The single `task_id`/`status` pair (legacy / "what AI is doing right now")
        - The full `tasks` map, if present — every task_id -> status entry
          is applied. This lets status recover even if backend wasn't running.

        Returns a debug dict describing every step taken.
        """
        result = {
            "file_path": str(self.current_task_file),
            "file_exists": self.current_task_file.exists(),
            "raw_content": None,
            "parsed": None,
            "task_id": None,
            "project_name": None,
            "target_status": None,
            "project_found": False,
            "project_id": None,
            "all_ticket_source_paths": [],
            "ticket_found": False,
            "ticket_id": None,
            "ticket_current_status": None,
            "action": None,
            "error": None,
            "bulk_sync": [],
        }

        logger.info("=" * 60)
        logger.info("[SyncService] sync_current_task() called")
        logger.info(f"[SyncService] Checking file: {self.current_task_file}")
        logger.info(f"[SyncService] File exists: {result['file_exists']}")

        if not self.current_task_file.exists():
            result["error"] = "File does not exist"
            logger.error(f"[SyncService] ABORT — file not found: {self.current_task_file}")
            return result

        try:
            raw = self.current_task_file.read_text(encoding="utf-8")
            result["raw_content"] = raw
            logger.info(f"[SyncService] Raw file content:\n{raw}")
            data = json.loads(raw)
            result["parsed"] = data
            logger.info(f"[SyncService] Parsed JSON: {data}")
        except (json.JSONDecodeError, OSError) as e:
            result["error"] = str(e)
            logger.error(f"[SyncService] ABORT — could not read/parse file: {e}")
            return result

        task_id: str = data.get("task_id", "")
        raw_status: str = data.get("status", "in_progress")
        project_name: str = data.get("project_name", "")

        result["task_id"] = task_id
        result["project_name"] = project_name
        result["target_status"] = raw_status

        logger.info(f"[SyncService] task_id={task_id!r}  status={raw_status!r}  project={project_name!r}")

        if not task_id:
            result["error"] = "task_id is empty"
            logger.error("[SyncService] ABORT — task_id is empty in current-task.json")
            return result

        db = SessionLocal()
        try:
            # ── Project lookup ──────────────────────────────────────────────────
            project = None
            if project_name:
                project = db.query(Project).filter(Project.name == project_name).first()
                if project:
                    result["project_found"] = True
                    result["project_id"] = str(project.id)
                    logger.info(f"[SyncService] Project found: {project.name!r} id={project.id}")
                else:
                    logger.warning(f"[SyncService] Project NOT found in DB for name={project_name!r}")
                    all_projects = db.query(Project).all()
                    names = [p.name for p in all_projects]
                    logger.warning(f"[SyncService] Projects currently in DB: {names}")
            else:
                logger.warning("[SyncService] project_name is empty — will search across all projects")

            # ── Ticket lookup ───────────────────────────────────────────────────
            if result["project_id"]:
                sample_tickets = (
                    db.query(Ticket)
                    .filter(Ticket.project_id == project.id)
                    .all()
                )
                result["all_ticket_source_paths"] = [t.source_file_path for t in sample_tickets]
                logger.info(
                    f"[SyncService] Tickets in project ({len(sample_tickets)} total), source_paths:\n"
                    + "\n".join(f"  [{t.status.value}] {t.source_file_path}" for t in sample_tickets)
                )
            else:
                sample_tickets = db.query(Ticket).limit(20).all()
                result["all_ticket_source_paths"] = [t.source_file_path for t in sample_tickets]
                logger.info(
                    f"[SyncService] First 20 tickets across all projects:\n"
                    + "\n".join(f"  [{t.status.value}] {t.source_file_path}" for t in sample_tickets)
                )

            # ── Ticket lookup (3-strategy fallback) ─────────────────────────────
            ticket = self._find_ticket_for_task(db, project, project_name, task_id)

            if not ticket:
                result["error"] = f"No ticket matched task_id {task_id!r}"
                logger.error(
                    f"[SyncService] No ticket found matching task_id={task_id!r}\n"
                    f"        Hint: check that tasks.md was ingested for project {project_name!r}"
                )
            else:
                result["ticket_found"] = True
                result["ticket_id"] = str(ticket.id)
                result["ticket_current_status"] = ticket.status.value
                logger.info(
                    f"[SyncService] Ticket found: id={ticket.id} title={ticket.title!r} "
                    f"status={ticket.status.value!r} source_file_path={ticket.source_file_path!r}"
                )

                # ── Status update ────────────────────────────────────────────────
                try:
                    target = TicketStatus(raw_status)
                except ValueError:
                    logger.warning(
                        f"[SyncService] Unrecognised status {raw_status!r}, defaulting to in_progress"
                    )
                    target = TicketStatus.in_progress

                result["target_status"] = target.value

                if ticket.status == target:
                    result["action"] = "no_change"
                    logger.info(
                        f"[SyncService] Ticket {task_id} is already {target.value} — nothing to do."
                    )
                else:
                    logger.info(
                        f"[SyncService] Updating ticket {task_id}: "
                        f"{ticket.status.value!r} → {target.value!r}"
                    )
                    update_ticket_status(db, str(ticket.id), target.value, AuthorType.agent, source="watcher")
                    result["action"] = f"{ticket.status.value} -> {target.value}"
                    logger.info(f"[SyncService] ✅ Ticket {task_id} updated to {target.value}")
                    
                    # Trigger audit if task is marked as done
                    if target == TicketStatus.done:
                        await self._trigger_audit_if_needed(db, ticket, task_id, project_name)

            # ── Bulk sync from the full `tasks` status map, if present ─────────
            tasks_map = data.get("tasks")
            if isinstance(tasks_map, dict):
                logger.info(f"[SyncService] Bulk-syncing {len(tasks_map)} task(s) from `tasks` map…")
                for map_task_id, map_status in tasks_map.items():
                    entry = {"task_id": map_task_id, "status": map_status}
                    try:
                        map_target = TicketStatus(map_status)
                    except ValueError:
                        entry["error"] = f"Unrecognised status {map_status!r}"
                        logger.warning(f"[SyncService] Bulk: skipping {map_task_id} — {entry['error']}")
                        result["bulk_sync"].append(entry)
                        continue

                    map_ticket = self._find_ticket_for_task(
                        db, project if result["project_id"] else None, project_name, map_task_id
                    )
                    if not map_ticket:
                        entry["error"] = "No matching ticket"
                        logger.warning(f"[SyncService] Bulk: no ticket found for {map_task_id}")
                        result["bulk_sync"].append(entry)
                        continue

                    entry["ticket_id"] = str(map_ticket.id)
                    if map_ticket.status == map_target:
                        entry["action"] = "no_change"
                    else:
                        entry["action"] = f"{map_ticket.status.value} -> {map_target.value}"
                        update_ticket_status(db, str(map_ticket.id), map_target.value, AuthorType.agent, source="watcher")
                        logger.info(f"[SyncService] Bulk: {map_task_id} {entry['action']}")
                        
                        # Trigger audit if task is marked as done
                        if map_target == TicketStatus.done:
                            await self._trigger_audit_if_needed(db, map_ticket, map_task_id, project_name)
                    result["bulk_sync"].append(entry)
        except Exception as e:
            result["error"] = str(e)
            logger.exception(f"[SyncService] Unexpected exception: {e}")
        finally:
            db.close()

        logger.info("=" * 60)
        return result

    # ═══════════════════════════════════════════════════════════════════════
    # 2. FULL STATE REFRESH (Complete Project Scan)
    # ═══════════════════════════════════════════════════════════════════════

    async def full_state_refresh(self) -> Dict[str, Any]:
        """
        Complete project state synchronization.
        Scans all tasks.md files in the project, reads current-task.json,
        and ensures all ticket statuses are consistent.

        Used by "Refresh Process" button in frontend.

        Returns comprehensive sync report.
        """
        logger.info("=" * 60)
        logger.info("[SyncService] full_state_refresh() started")

        result = {
            "project_path": str(self.project_root),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tasks_md_files": [],
            "current_task_json": None,
            "sync_results": [],
            "discrepancies": [],
            "summary": {
                "total_tickets": 0,
                "updated": 0,
                "discrepancies_found": 0,
                "errors": 0,
            }
        }

        db = SessionLocal()
        try:
            # ── Step 1: Find all tasks.md files in project ──────────────────────
            tasks_md_files = list(self.project_root.rglob("specs/tasks.md"))
            tasks_md_files.extend(self.project_root.rglob("tasks.md"))
            # Deduplicate
            seen = set()
            unique_files = []
            for f in tasks_md_files:
                if f not in seen:
                    seen.add(f)
                    unique_files.append(f)
            tasks_md_files = unique_files

            logger.info(f"[SyncService] Found {len(tasks_md_files)} tasks.md file(s)")

            for tasks_file in tasks_md_files:
                file_info = self._analyze_tasks_md(db, tasks_file)
                result["tasks_md_files"].append(file_info)

            # ── Step 2: Read current-task.json for real-time status ─────────────
            current_task_data = None
            if self.current_task_file.exists():
                try:
                    raw = self.current_task_file.read_text(encoding="utf-8")
                    current_task_data = json.loads(raw)
                    result["current_task_json"] = current_task_data
                    logger.info(f"[SyncService] current-task.json loaded: {current_task_data.get('task_id')}")
                except Exception as e:
                    logger.error(f"[SyncService] Failed to read current-task.json: {e}")
                    result["current_task_json_error"] = str(e)

            # ── Step 3: Sync all tickets against current-task.json tasks map ────
            if current_task_data and isinstance(current_task_data.get("tasks"), dict):
                tasks_map = current_task_data["tasks"]
                logger.info(f"[SyncService] Syncing {len(tasks_map)} tasks from current-task.json")

                for task_id, expected_status in tasks_map.items():
                    sync_result = await self._sync_single_task(db, task_id, expected_status, current_task_data.get("project_name"))
                    result["sync_results"].append(sync_result)
                    result["summary"]["total_tickets"] += 1
                    if sync_result.get("action") and sync_result["action"] != "no_change":
                        result["summary"]["updated"] += 1
                    if sync_result.get("error"):
                        result["summary"]["errors"] += 1

            # ── Step 4: Detect discrepancies (tickets in DB but not in tasks map) ──
            all_tickets = db.query(Ticket).all()
            for ticket in all_tickets:
                # Check if ticket has a corresponding entry in current-task.json
                in_current_task = False
                if current_task_data and isinstance(current_task_data.get("tasks"), dict):
                    in_current_task = ticket.ticket_id in current_task_data["tasks"]

                if not in_current_task and ticket.status != TicketStatus.todo:
                    # Ticket has a status but not tracked in current-task.json
                    discrepancy = {
                        "ticket_id": ticket.ticket_id,
                        "db_status": ticket.status.value,
                        "source_file": ticket.source_file_path,
                        "issue": "Status set but not in current-task.json tasks map"
                    }
                    result["discrepancies"].append(discrepancy)
                    result["summary"]["discrepancies_found"] += 1

            # ── Step 5: Also sync from current-task.json single task_id ──────────
            if current_task_data and current_task_data.get("task_id"):
                single_task_id = current_task_data["task_id"]
                single_status = current_task_data.get("status", "in_progress")
                # Only if not already in tasks map
                if not (current_task_data.get("tasks") and single_task_id in current_task_data["tasks"]):
                    sync_result = await self._sync_single_task(db, single_task_id, single_status, current_task_data.get("project_name"))
                    result["sync_results"].append(sync_result)

        except Exception as e:
            result["error"] = str(e)
            logger.exception(f"[SyncService] full_state_refresh failed: {e}")
            result["summary"]["errors"] += 1
        finally:
            db.close()

        logger.info(f"[SyncService] full_state_refresh complete: {result['summary']}")
        logger.info("=" * 60)
        return result

    async def _sync_single_task(
        self,
        db: Session,
        task_id: str,
        status: str,
        project_name: str = None
    ) -> Dict[str, Any]:
        """Sync a single task ID to the given status."""
        result = {
            "task_id": task_id,
            "target_status": status,
            "action": None,
            "error": None,
        }

        try:
            target = TicketStatus(status)
        except ValueError:
            result["error"] = f"Invalid status: {status}"
            return result

        ticket = self._find_ticket_for_task(db, None, project_name, task_id)
        if not ticket:
            result["error"] = f"No ticket found for {task_id}"
            return result

        result["ticket_id"] = str(ticket.id)
        result["current_status"] = ticket.status.value

        if ticket.status == target:
            result["action"] = "no_change"
        else:
            update_ticket_status(db, str(ticket.id), target.value, AuthorType.agent, source="watcher")
            result["action"] = f"{ticket.status.value} -> {target.value}"
            logger.info(f"[SyncService] Refreshed {task_id}: {result['action']}")
            
            # Trigger audit if task is marked as done
            if target == TicketStatus.done:
                await self._trigger_audit_if_needed(db, ticket, task_id, project_name)

        return result

    def _analyze_tasks_md(self, db: Session, tasks_file: Path) -> Dict[str, Any]:
        """Analyze a tasks.md file for structure info."""
        info = {
            "file_path": str(tasks_file),
            "exists": tasks_file.exists(),
            "task_count": 0,
            "tasks": [],
            "project_name": None,
        }

        if not tasks_file.exists():
            return info

        try:
            content = tasks_file.read_text(encoding="utf-8")
            parsed = parse_task_lines(content)
            info["task_count"] = len(parsed)
            info["tasks"] = [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "checkbox_state": t["checkbox_state"],
                    "line_number": t["line_number"],
                }
                for t in parsed
            ]

            # Try to determine project name from path
            relative = tasks_file.relative_to(self.project_root)
            if len(relative.parts) >= 2 and relative.parts[0] == "specs":
                info["project_name"] = relative.parts[1]

        except Exception as e:
            info["error"] = str(e)

        return info

    # ═══════════════════════════════════════════════════════════════════════
    # 3. STRUCTURE SYNC PREPARATION (tasks.md → Ingestion Ready)
    # ═══════════════════════════════════════════════════════════════════════

    def prepare_structure_sync(self) -> Dict[str, Any]:
        """
        Prepare for structure synchronization (triggered by StructureWatcher).
        Reads tasks.md and returns structured data for frontend notification.

        Does NOT modify database - only reads and reports.
        """
        logger.info("[SyncService] prepare_structure_sync() called")

        result = {
            "project_path": str(self.project_root),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tasks_md_found": False,
            "tasks_md_path": None,
            "tasks_md_hash": None,
            "task_count": 0,
            "tasks": [],
            "ready_for_ingestion": False,
            "message": "",
        }

        # Find tasks.md
        tasks_md_files = list(self.project_root.rglob("specs/tasks.md"))
        tasks_md_files.extend(self.project_root.rglob("tasks.md"))

        if not tasks_md_files:
            result["message"] = "No tasks.md found in project"
            return result

        tasks_file = tasks_md_files[0]  # Use first found
        result["tasks_md_found"] = True
        result["tasks_md_path"] = str(tasks_file)

        try:
            content = tasks_file.read_text(encoding="utf-8")
            result["tasks_md_hash"] = hashlib.sha256(content.encode()).hexdigest()[:16]

            parsed = parse_task_lines(content)
            result["task_count"] = len(parsed)
            result["tasks"] = [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "checkbox_state": t["checkbox_state"],
                    "line_number": t["line_number"],
                }
                for t in parsed
            ]

            # Check if we have valid tasks with IDs
            valid_tasks = [t for t in parsed if t["id"].startswith("T") and t["id"][1:].isdigit()]
            result["ready_for_ingestion"] = len(valid_tasks) > 0
            result["message"] = f"Found {len(valid_tasks)} valid tasks ready for ingestion"

        except Exception as e:
            result["error"] = str(e)
            result["message"] = f"Error reading tasks.md: {e}"

        logger.info(f"[SyncService] Structure sync prep: {result['message']}")
        return result

    # ═══════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _find_ticket_for_task(
        self,
        db: Session,
        project: Optional[Project],
        project_name: str,
        task_id: str
    ) -> Optional[Ticket]:
        """
        Locate the ticket matching task_id using a 3-strategy fallback:
        project-scoped match -> path-similarity match -> global match.
        """
        like_pattern = f"%#{task_id}"

        # Strategy 1: project-scoped
        if project:
            ticket = (
                db.query(Ticket)
                .filter(Ticket.source_file_path.like(like_pattern))
                .filter(Ticket.project_id == project.id)
                .first()
            )
            if ticket:
                return ticket

        # Strategy 2: path-similarity match against the watched project root
        current_task_file_dir = self.current_task_file.parent.parent
        current_project_path = str(current_task_file_dir).replace("\\", "/")
        all_matching_tickets = db.query(Ticket).filter(Ticket.source_file_path.like(like_pattern)).all()
        for candidate in all_matching_tickets:
            if current_project_path in candidate.source_file_path.replace("\\", "/"):
                return candidate

        # Strategy 3: global fallback (may be wrong project, but better than nothing)
        return db.query(Ticket).filter(Ticket.source_file_path.like(like_pattern)).first()

    async def _trigger_audit_if_needed(self, db: Session, ticket: Ticket, task_id: str, project_name: str):
        """
        Trigger conformity audit for a completed task.
        This runs the auditor to evaluate code quality, requirements coverage, etc.
        """
        try:
            # Lazy import to avoid circular dependency with manager.py
            from app.agents.ticket_agent.manager import get_ticket_manager
            manager = get_ticket_manager()
            if not manager or not manager.enable_auditor:
                logger.info(f"[SyncService] Auditor not enabled, skipping audit for {task_id}")
                return

            logger.info(f"[SyncService] Triggering audit for completed task {task_id}")

            # Get the git diff for this task
            git_diff = ""
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "log", "--oneline", "-10", "--grep", task_id],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                commit_hashes = [line.split()[0] for line in result.stdout.strip().split('\n') if line.strip()]
                
                if commit_hashes:
                    diff_result = subprocess.run(
                        ["git", "show", commit_hashes[0], "--no-merges"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    git_diff = diff_result.stdout
            except Exception as e:
                logger.warning(f"[SyncService] Could not get git diff for {task_id}: {e}")

            # Run the audit
            from app.agents.ticket_agent.auditor import Auditor
            from app.models import TicketEvent, TicketEventType, AuthorType

            auditor = Auditor()
            
            audit_result = await auditor.audit_task_completion(
                task_id=task_id,
                git_diff=git_diff,
                changed_files=[ticket.source_file_path] if ticket.source_file_path else [],
                criteria=["requirements", "code_quality", "architecture", "traceability"],
                spec_documents={},
                commit_messages=[],
                branch_name="",
                task_title=ticket.title,
                task_description=ticket.description or ""
            )

            # Store audit result as ticket event
            if audit_result and not audit_result.get("error"):
                event = TicketEvent(
                    ticket_id=ticket.id,
                    event_type=TicketEventType.audit_completed,
                    author_type=AuthorType.agent,
                    event_metadata=audit_result
                )
                db.add(event)
                db.commit()
                logger.info(f"[SyncService] Audit completed for {task_id}: {audit_result.get('verdict', 'N/A')}")
            else:
                logger.warning(f"[SyncService] Audit failed for {task_id}: {audit_result.get('error', 'Unknown')}")

        except Exception as e:
            logger.error(f"[SyncService] Audit trigger failed for {task_id}: {e}")
            db.rollback()

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic info about paths and configuration."""
        from app.utils.path_builder import BASE_DIR as PATH_BUILDER_BASE_DIR

        return {
            "BASE_DIR": str(PATH_BUILDER_BASE_DIR),
            "TARGET_PROJECT_PATH_setting": settings.TARGET_PROJECT_PATH,
            "computed_current_task_file": str(self.current_task_file),
            "project_path_used": self.project_path,
            "project_root": str(self.project_root),
        }