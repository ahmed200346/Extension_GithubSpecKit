"""
Ticket Manager — Central Orchestrator for Universal Ticket Agent

This is the main entry point for the ticket agent subsystem.
Called by the FastAPI lifespan to start/stop the file watchers.
Coordinates: DualWatcherManager (StructureWatcher + StatusWatcher) → SyncService → Auditor
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Callable, Awaitable
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.utils.path_builder import BASE_DIR

from .watcher import DualWatcherManager, StructureWatcher, StatusWatcher
from .sync_service import SyncService
from .auditor import Auditor

logger = logging.getLogger(__name__)


class TicketManager:
    """
    Central orchestrator for the Ticket Agent.
    Manages dual watchers (Structure + Status) and coordinates sync/audit operations.

    Flow:
    - StructureWatcher detects tasks.md changes → signals "ready for ingestion"
    - Frontend calls ingest → SyncService creates tickets in DB
    - StatusWatcher detects current-task.json changes → real-time status sync
    - On status → done → Auditor validates conformity
    - Refresh button → full_state_refresh() for complete consistency
    """

    def __init__(
        self,
        project_path: Optional[str] = None,
        structure_debounce_ms: int = 1000,
        status_debounce_ms: int = 500,
        enable_auditor: bool = False,
        auditor_threshold: float = 75.0
    ):
        self.project_path = project_path or settings.TARGET_PROJECT_PATH or str(BASE_DIR)
        self.structure_debounce_ms = structure_debounce_ms
        self.status_debounce_ms = status_debounce_ms
        self.enable_auditor = enable_auditor
        self.auditor_threshold = auditor_threshold

        self._dual_watcher: Optional[DualWatcherManager] = None
        self._sync_service: Optional[SyncService] = None
        self._auditor: Optional[Auditor] = None
        self._running = False

        # Callbacks for frontend notification
        self._on_structure_change: Optional[Callable[[dict], Awaitable[None]]] = None
        self._on_status_change: Optional[Callable[[dict], Awaitable[None]]] = None

        logger.info(f"[TicketManager] Initialized for project: {self.project_path}")
        logger.info(f"[TicketManager] Structure debounce: {structure_debounce_ms}ms")
        logger.info(f"[TicketManager] Status debounce: {status_debounce_ms}ms")
        logger.info(f"[TicketManager] Auditor: {'enabled' if enable_auditor else 'disabled'} (threshold: {auditor_threshold})")

    @property
    def current_task_file(self) -> Path:
        """Get the path to current-task.json"""
        return Path(self.project_path) / ".task_runtime" / "current-task.json"

    @property
    def project_root(self) -> Path:
        return Path(self.project_path)

    @property
    def is_running(self) -> bool:
        return self._running

    def initialize(self) -> None:
        """Initialize all sub-components."""
        project_root = Path(self.project_path)

        self._sync_service = SyncService(project_path=self.project_path)

        self._dual_watcher = DualWatcherManager(
            project_path=project_root,
            sync_service=self._sync_service,
            structure_debounce_ms=self.structure_debounce_ms,
            status_debounce_ms=self.status_debounce_ms,
        )

        # Set up callbacks
        self._dual_watcher.set_structure_callback(self._handle_structure_change)
        self._dual_watcher.set_status_callback(self._handle_status_change)

        if self.enable_auditor:
            self._auditor = Auditor(
                sync_service=self._sync_service,
                threshold=self.auditor_threshold
            )

        logger.info("[TicketManager] Components initialized (DualWatcherManager + SyncService + Auditor)")

    async def _handle_structure_change(self, event: dict) -> None:
        """Internal handler for StructureWatcher events (tasks.md changes)."""
        logger.info(f"[TicketManager] Structure change event: {event.get('change_type')} on {event.get('file')}")

        # Notify external callback if registered
        if self._on_structure_change:
            try:
                await self._on_structure_change(event)
            except Exception as e:
                logger.error(f"[TicketManager] Structure change callback error: {e}")

        # Also prepare structure sync data for potential frontend polling
        try:
            structure_data = self._sync_service.prepare_structure_sync()
            event["structure_data"] = structure_data
        except Exception as e:
            logger.error(f"[TicketManager] Failed to prepare structure sync: {e}")

    async def _handle_status_change(self, event: dict) -> None:
        """Internal handler for StatusWatcher events (current-task.json changes)."""
        logger.info(f"[TicketManager] Status change event: sync completed")

        sync_result = event.get("sync_result", {})
        action = sync_result.get("action", "")

        # Trigger auditor if task completed (status -> done)
        if self.enable_auditor and action and "-> done" in action:
            task_id = sync_result.get("task_id")
            if task_id:
                logger.info(f"[TicketManager] Task {task_id} completed - triggering auto-audit")
                try:
                    audit_result = await self._auditor.auto_audit_on_done(
                        task_id=task_id,
                        project_path=self.project_path,
                    )
                    logger.info(f"[TicketManager] Auto-audit result for {task_id}: {audit_result.get('verdict')} ({audit_result.get('conformity_score')}/100)")
                except Exception as e:
                    logger.error(f"[TicketManager] Auto-audit failed for {task_id}: {e}")

        # Notify external callback if registered
        if self._on_status_change:
            try:
                await self._on_status_change(event)
            except Exception as e:
                logger.error(f"[TicketManager] Status change callback error: {e}")

    def set_structure_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Register callback for structure changes (tasks.md)."""
        self._on_structure_change = callback

    def set_status_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Register callback for status changes (current-task.json)."""
        self._on_status_change = callback

    async def start(self) -> None:
        """Start both watchers in the background."""
        if self._running:
            logger.warning("[TicketManager] Already running")
            return

        if not self._dual_watcher:
            self.initialize()

        self._running = True
        await self._dual_watcher.start()
        logger.info("[TicketManager] Dual watchers started (Structure + Status)")

        # Initial sync on startup
        try:
            result = await self._sync_service.sync_current_task()
            logger.info(f"[TicketManager] Initial sync: {result.get('action', 'completed')}")
        except Exception as e:
            logger.error(f"[TicketManager] Initial sync failed: {e}")

    async def stop(self) -> None:
        """Stop both watchers gracefully."""
        if not self._running:
            return

        self._running = False

        if self._dual_watcher:
            await self._dual_watcher.stop()

        logger.info("[TicketManager] Stopped")

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API METHODS (for endpoints)
    # ═══════════════════════════════════════════════════════════════════════

    async def force_sync(self) -> dict:
        """Manually trigger a real-time sync from current-task.json (StatusWatcher path)."""
        if not self._sync_service:
            self.initialize()
        return await self._sync_service.sync_current_task()

    def full_state_refresh(self) -> dict:
        """Complete project state synchronization (Refresh Process button)."""
        if not self._sync_service:
            self.initialize()
        return self._sync_service.full_state_refresh()

    def prepare_structure_sync(self) -> dict:
        """Prepare structure sync data from tasks.md (StructureWatcher path)."""
        if not self._sync_service:
            self.initialize()
        return self._sync_service.prepare_structure_sync()

    def get_status(self) -> dict:
        """Get comprehensive manager status."""
        status = {
            "running": self._running,
            "project_path": self.project_path,
            "current_task_file": str(self.current_task_file),
            "auditor_enabled": self.enable_auditor,
            "auditor_threshold": self.auditor_threshold,
        }

        if self._dual_watcher:
            status["watchers"] = self._dual_watcher.get_status()

        if self._sync_service:
            status["sync_diagnostics"] = self._sync_service.get_diagnostics()

        return status

    # ═══════════════════════════════════════════════════════════════════════
    # AUDITOR INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════

    async def audit_task_completion(
        self,
        task_id: str,
        git_diff: str,
        changed_files: list,
        criteria: list,
        spec_documents: dict = None,
        commit_messages: list = None,
        branch_name: str = "",
        task_title: str = "",
        task_description: str = "",
    ) -> dict:
        """
        Trigger audit for a completed task.
        Called when ticket transitions to 'done' (from frontend or API).
        """
        if not self.enable_auditor or not self._auditor:
            return {"auditor_enabled": False, "message": "Auditor not enabled"}

        return await self._auditor.audit_completion(
            task_id=task_id,
            git_diff=git_diff,
            changed_files=changed_files,
            criteria=criteria,
            spec_documents=spec_documents or {},
            commit_messages=commit_messages or [],
            branch_name=branch_name,
            task_title=task_title,
            task_description=task_description,
        )


# Global manager instance (set by lifespan)
_manager: Optional[TicketManager] = None


def get_ticket_manager() -> Optional[TicketManager]:
    """Get the global ticket manager instance."""
    return _manager


def set_ticket_manager(manager: TicketManager) -> None:
    """Set the global ticket manager instance."""
    global _manager
    _manager = manager


@asynccontextmanager
async def ticket_agent_lifespan(app):
    """
    FastAPI lifespan context manager for the Ticket Agent.
    Usage in main.py:
        from app.agents.ticket_agent.manager import ticket_agent_lifespan
        app = FastAPI(lifespan=ticket_agent_lifespan)
    """
    global _manager

    # Configuration from settings
    project_path = getattr(settings, 'TARGET_PROJECT_PATH', None) or str(BASE_DIR)
    structure_debounce_ms = getattr(settings, 'STRUCTURE_WATCH_DEBOUNCE_MS', 1000)
    status_debounce_ms = getattr(settings, 'STATUS_WATCH_DEBOUNCE_MS', 500)
    enable_auditor = getattr(settings, 'ENABLE_AUDITOR', False)
    auditor_threshold = getattr(settings, 'AUDITOR_THRESHOLD', 75.0)

    logger.info("[Lifespan] Starting Ticket Agent with Dual Watchers...")

    _manager = TicketManager(
        project_path=project_path,
        structure_debounce_ms=structure_debounce_ms,
        status_debounce_ms=status_debounce_ms,
        enable_auditor=enable_auditor,
        auditor_threshold=auditor_threshold
    )

    await _manager.start()

    try:
        yield
    finally:
        logger.info("[Lifespan] Shutting down Ticket Agent...")
        await _manager.stop()
        _manager = None


def create_ticket_manager(
    project_path: Optional[str] = None,
    structure_debounce_ms: int = 1000,
    status_debounce_ms: int = 500,
    enable_auditor: bool = False,
    auditor_threshold: float = 75.0
) -> TicketManager:
    """Factory function to create a TicketManager (for testing or manual use)."""
    return TicketManager(
        project_path=project_path,
        structure_debounce_ms=structure_debounce_ms,
        status_debounce_ms=status_debounce_ms,
        enable_auditor=enable_auditor,
        auditor_threshold=auditor_threshold
    )