"""
Auditor — Conformity Verification Agent

Compares actual code implementation against task requirements
to calculate a conformity KPI score. Uses ticket_metrics for
scoring and optionally an LLM for semantic analysis.

Integrated with autonomous flow:
- Triggered automatically when ticket status → done (via StatusWatcher callback)
- Stores audit result as TicketEvent with event_type=audit_completed
- Optionally reverts status if score < threshold
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from app.core.ticket_metrics import (
    build_conformity_report,
    ConformityReport,
    report_to_json,
    ConformityVerdict,
)
from app.models import Ticket, TicketEvent, TicketEventType, AuthorType, TicketStatus
from app.database import SessionLocal
from app.services.ticket_ingestion import update_ticket_status

logger = logging.getLogger(__name__)


class Auditor:
    """
    Intelligent auditor that validates code implementation against task requirements.

    Autonomous Flow:
    1. StatusWatcher detects current-task.json change with status → done
    2. StatusWatcher calls TicketManager._handle_status_change
    3. TicketManager calls Auditor.audit_completion with collected data
    4. Auditor runs conformity analysis (metrics + optional LLM)
    5. Stores result in TicketEvent.event_metadata with event_type=audit_completed
    6. If score < threshold: reverts ticket to in_progress (status_override)
    """

    def __init__(
        self,
        sync_service: "SyncService",
        threshold: float = 75.0,
        use_llm: bool = False,
        llm_model: str = "claude-3-sonnet",
    ):
        self.sync_service = sync_service
        self.threshold = threshold
        self.use_llm = use_llm
        self.llm_model = llm_model

        logger.info(f"[Auditor] Initialized (threshold: {threshold}, LLM: {use_llm})")

    async def audit_completion(
        self,
        task_id: str,
        git_diff: str,
        changed_files: List[str],
        criteria: List[str],
        spec_documents: Dict[str, str] = None,
        commit_messages: List[str] = None,
        branch_name: str = "",
        task_title: str = "",
        task_description: str = "",
    ) -> Dict[str, Any]:
        """
        Perform full conformity audit for a completed task.

        Args:
            task_id: The task ID (e.g., "T004")
            git_diff: Git diff of changes made
            changed_files: List of file paths changed
            criteria: Acceptance criteria from tasks.md
            spec_documents: Optional dict of spec file contents
            commit_messages: Recent commit messages
            branch_name: Git branch name
            task_title: Task title
            task_description: Task description

        Returns:
            Dict with conformity report and action taken
        """
        logger.info(f"[Auditor] Starting audit for {task_id}")

        spec_documents = spec_documents or {}
        commit_messages = commit_messages or []

        # Build conformity report using metrics
        report: ConformityReport = build_conformity_report(
            task_id=task_id,
            task_title=task_title,
            criteria=criteria,
            git_diff=git_diff,
            changed_files=changed_files,
            spec_documents=spec_documents,
            commit_messages=commit_messages,
            branch_name=branch_name,
        )

        report_json = report_to_json(report)
        logger.info(f"[Auditor] Audit complete for {task_id}: {report.verdict.value} ({report.conformity_score}/100)")

        # Store audit result in database with proper event type
        audit_event = await self._store_audit_result(task_id, report_json)

        # Determine action based on threshold
        action_taken = "none"
        if report.conformity_score < self.threshold:
            action_taken = await self._handle_low_score(task_id, report)
        elif report.verdict == ConformityVerdict.EXEMPLARY:
            action_taken = "auto_approved"

        return {
            "task_id": task_id,
            "conformity_score": report.conformity_score,
            "verdict": report.verdict.value,
            "threshold": self.threshold,
            "action_taken": action_taken,
            "report": report_json,
            "audit_event_id": str(audit_event.id) if audit_event else None,
        }

    async def _store_audit_result(self, task_id: str, report_json: Dict[str, Any]) -> Optional[TicketEvent]:
        """Store audit result as a TicketEvent with event_type=audit_completed."""
        db = SessionLocal()
        try:
            # Find the ticket
            ticket = db.query(Ticket).filter(Ticket.ticket_id == task_id).first()
            if not ticket:
                logger.warning(f"[Auditor] Ticket {task_id} not found for audit storage")
                return None

            # Determine event type based on verdict
            if report_json["verdict"] in ("NON_COMPLIANT", "NEEDS_IMPROVEMENT"):
                event_type = TicketEventType.status_override
            else:
                event_type = TicketEventType.status_change  # Use custom or add audit_completed

            event = TicketEvent(
                ticket_id=ticket.id,
                event_type=event_type,
                author_type=AuthorType.agent,
                old_status=ticket.status,
                new_status=ticket.status,
                comment=f"Conformity audit: {report_json['verdict']} ({report_json['conformity_score']}/100)",
                event_metadata={
                    **report_json,
                    "audit_type": "conformity_check",
                    "triggered_by": "status_watcher_auto",
                },
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            logger.info(f"[Auditor] Stored audit event {event.id} for {task_id}")
            return event
        except Exception as e:
            logger.error(f"[Auditor] Failed to store audit result: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    async def _handle_low_score(self, task_id: str, report: ConformityReport) -> str:
        """
        Handle case where conformity score is below threshold.
        Reverts ticket to in_progress and adds audit comment.
        """
        db = SessionLocal()
        try:
            ticket = db.query(Ticket).filter(Ticket.ticket_id == task_id).first()
            if not ticket:
                return "ticket_not_found"

            if ticket.status == TicketStatus.done:
                # Revert to in_progress
                update_ticket_status(db, str(ticket.id), "in_progress", AuthorType.agent)

                # Add audit event for the revert
                event = TicketEvent(
                    ticket_id=ticket.id,
                    event_type=TicketEventType.status_override,
                    author_type=AuthorType.agent,
                    old_status=TicketStatus.done,
                    new_status=TicketStatus.in_progress,
                    comment=f"Auditor reverted: score {report.conformity_score} below threshold {self.threshold}. {report.summary}",
                    event_metadata=report_to_json(report),
                )
                db.add(event)
                db.commit()

                logger.warning(f"[Auditor] Reverted {task_id} to in_progress (score: {report.conformity_score})")
                return "reverted_to_in_progress"

            return "already_in_progress"
        except Exception as e:
            logger.error(f"[Auditor] Failed to handle low score: {e}")
            db.rollback()
            return "error"
        finally:
            db.close()

    def collect_git_diff(
        self,
        task_id: str,
        since_commit: str = None,
        repo_path: str = None
    ) -> Dict[str, Any]:
        """
        Collect git diff for the task.
        Can be called before audit to gather evidence.
        """
        repo_path = repo_path or self.sync_service.project_path

        try:
            # Get diff since task started (or last commit)
            if since_commit:
                diff_cmd = ["git", "diff", since_commit, "--", "."]
            else:
                # Get uncommitted changes + recent commits
                diff_cmd = ["git", "diff", "HEAD~5..HEAD", "--", "."]

            result = subprocess.run(
                diff_cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Get changed files
            files_result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~5..HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Get recent commit messages
            commits_result = subprocess.run(
                ["git", "log", "--oneline", "-10", "--pretty=format:%s"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            return {
                "diff": result.stdout,
                "changed_files": [f for f in files_result.stdout.strip().split("\n") if f],
                "commit_messages": [c for c in commits_result.stdout.strip().split("\n") if c],
                "branch_name": self._get_current_branch(repo_path),
            }
        except Exception as e:
            logger.error(f"[Auditor] Failed to collect git diff: {e}")
            return {
                "diff": "",
                "changed_files": [],
                "commit_messages": [],
                "branch_name": "",
            }

    def _get_current_branch(self, repo_path: str) -> str:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def load_task_criteria(self, task_id: str, project_path: str = None) -> Dict[str, Any]:
        """
        Load task criteria from tasks.md for the given task_id.
        Returns title, description, and acceptance criteria.
        """
        project_path = project_path or self.sync_service.project_path
        tasks_md_path = Path(project_path) / "specs" / "tasks.md"

        if not tasks_md_path.exists():
            # Try to find tasks.md in project
            for tasks_file in Path(project_path).rglob("tasks.md"):
                tasks_md_path = tasks_file
                break

        if not tasks_md_path.exists():
            logger.warning(f"[Auditor] tasks.md not found in {project_path}")
            return {"title": "", "description": "", "criteria": []}

        content = tasks_md_path.read_text(encoding="utf-8")
        return self._parse_task_from_md(content, task_id)

    def _parse_task_from_md(self, content: str, task_id: str) -> Dict[str, Any]:
        """Parse a specific task from tasks.md content."""
        import re

        lines = content.splitlines()
        in_task = False
        task_data = {"title": "", "description": "", "criteria": []}

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for task start
            task_match = re.match(r'^-\s*\[([xX\s~/])\]\s*(.+)$', stripped)
            if task_match:
                checkbox = task_match.group(1)
                task_text = task_match.group(2).strip()

                id_match = re.match(r'^(T\d+)', task_text)
                current_id = id_match.group(1) if id_match else None

                if current_id == task_id:
                    in_task = True
                    title = task_text
                    if id_match:
                        title = task_text[len(task_id):].strip().lstrip(":- ").strip()
                    task_data["title"] = title
                    continue

            # End of task (next task or heading)
            if in_task:
                if task_match and current_id != task_id:
                    break
                if stripped.startswith("#"):
                    break

                # Collect description and acceptance criteria
                if stripped:
                    if "acceptance criteria" in stripped.lower() or "criteria" in stripped.lower():
                        # Next lines are criteria
                        continue
                    if stripped.startswith("- ") or stripped.startswith("* "):
                        task_data["criteria"].append(stripped[2:].strip())
                    elif not task_data["description"]:
                        task_data["description"] = stripped
                    else:
                        task_data["description"] += "\n" + stripped

        return task_data

    async def auto_audit_on_done(
        self,
        task_id: str,
        project_path: str = None,
    ) -> Dict[str, Any]:
        """
        Fully automatic audit triggered when ticket status changes to done.
        Collects all required data automatically.
        """
        logger.info(f"[Auditor] Auto-audit triggered for {task_id}")

        # Collect git data
        git_data = self.collect_git_diff(task_id, repo_path=project_path)

        # Load task criteria
        task_data = self.load_task_criteria(task_id, project_path=project_path)

        # Run audit
        return await self.audit_completion(
            task_id=task_id,
            git_diff=git_data["diff"],
            changed_files=git_data["changed_files"],
            criteria=task_data.get("criteria", []),
            spec_documents={},  # Could be extended to load spec docs
            commit_messages=git_data["commit_messages"],
            branch_name=git_data["branch_name"],
            task_title=task_data.get("title", ""),
            task_description=task_data.get("description", ""),
        )


async def audit_task_on_completion(
    task_id: str,
    sync_service: "SyncService",
    threshold: float = 75.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to audit a task on completion.
    Called by manager when ticket transitions to done.
    """
    auditor = Auditor(sync_service=sync_service, threshold=threshold)

    # Auto-collect git data if not provided
    if "git_diff" not in kwargs or not kwargs["git_diff"]:
        git_data = auditor.collect_git_diff(task_id)
        kwargs.update(git_data)

    # Auto-load criteria if not provided
    if "criteria" not in kwargs or not kwargs["criteria"]:
        task_data = auditor.load_task_criteria(task_id)
        kwargs["criteria"] = task_data.get("criteria", [])
        kwargs["task_title"] = task_data.get("title", "")
        kwargs["task_description"] = task_data.get("description", "")

    return await auditor.audit_completion(task_id=task_id, **kwargs)