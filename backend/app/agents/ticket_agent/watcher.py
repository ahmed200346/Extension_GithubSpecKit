"""
Ticket Agent Watchers — Dual File System Monitoring

Two watchers for autonomous spec-to-dashboard flow:
1. StructureWatcher — Watches specs/tasks.md for structure changes (new tasks, modifications)
2. StatusWatcher — Watches .task_runtime/current-task.json for real-time status updates
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Callable, Awaitable, Set
from watchfiles import awatch, Change

logger = logging.getLogger(__name__)


class BaseWatcher:
    """Base class for file watchers with common functionality."""

    def __init__(
        self,
        watch_path: Path,
        debounce_ms: int = 500,
        name: str = "Watcher"
    ):
        self.watch_path = watch_path
        self.debounce_ms = debounce_ms
        self.name = name

        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_trigger_time = 0.0

        logger.info(f"[{self.name}] Initialized for: {watch_path}")
        logger.info(f"[{self.name}] Debounce: {debounce_ms}ms")

    @property
    def is_watching(self) -> bool:
        return self._running

    async def run(self, handler: Callable[[Set[tuple]], Awaitable[None]]) -> None:
        """Main watch loop - runs until stopped."""
        self._running = True

        # Ensure watch directory exists
        self.watch_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{self.name}] Starting watch loop...")

        try:
            async for changes in awatch(str(self.watch_path), debounce=int(self.debounce_ms / 1000)):
                if not self._running:
                    break

                await self._handle_changes(changes, handler)

        except asyncio.CancelledError:
            logger.info(f"[{self.name}] Watch loop cancelled")
            raise
        except Exception as e:
            logger.exception(f"[{self.name}] Unexpected error in watch loop: {e}")
        finally:
            self._running = False
            logger.info(f"[{self.name}] Watch loop stopped")

    async def _handle_changes(self, changes: Set[tuple], handler: Callable) -> None:
        """Process file system changes with debouncing."""
        import time
        now = time.time()
        if now - self._last_trigger_time < (self.debounce_ms / 1000):
            logger.debug(f"[{self.name}] Debouncing - skipping rapid successive changes")
            return

        self._last_trigger_time = now

        # Filter relevant changes
        relevant_changes = self._filter_changes(changes)
        if relevant_changes:
            logger.info(f"[{self.name}] Changes detected: {relevant_changes}")
            await handler(relevant_changes)

    def _filter_changes(self, changes: Set[tuple]) -> Set[tuple]:
        """Override in subclasses to filter relevant file changes."""
        return changes

    async def stop(self) -> None:
        """Stop the watcher gracefully."""
        logger.info(f"[{self.name}] Stopping...")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(f"[{self.name}] Stopped")


class StructureWatcher(BaseWatcher):
    """
    Watches specs/tasks.md for structural changes.
    Triggers when tasks.md is created, modified, or deleted.
    Used to signal frontend that ingestion is available.
    Also creates .task_runtime/ directory when tasks.md is detected.
    """

    def __init__(
        self,
        project_path: Path,
        debounce_ms: int = 1000,
        on_structure_change: Optional[Callable[[dict], Awaitable[None]]] = None
    ):
        # Watch the specs directory (parent of tasks.md)
        specs_path = project_path / "specs"
        super().__init__(specs_path, debounce_ms, name="StructureWatcher")

        self.project_path = project_path
        self.on_structure_change = on_structure_change
        self._last_tasks_hash: Optional[str] = None

        logger.info(f"[StructureWatcher] Monitoring specs/ for tasks.md changes")

    def _ensure_task_runtime(self) -> None:
        """Create .task_runtime/ directory if it doesn't exist."""
        task_runtime_dir = self.project_path / ".task_runtime"
        task_runtime_dir.mkdir(parents=True, exist_ok=True)
        
        # Also create config.json if it doesn't exist
        config_path = task_runtime_dir / "config.json"
        if not config_path.exists():
            import json
            config = {
                "project_name": self.project_path.name,
                "auto_created": True,
                "created_at": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
            }
            config_path.write_text(json.dumps(config, indent=2))
            logger.info(f"[StructureWatcher] Created .task_runtime/config.json")

    def _filter_changes(self, changes: Set[tuple]) -> Set[tuple]:
        """Only care about tasks.md files."""
        relevant = set()
        for change_type, changed_path in changes:
            changed_file = Path(changed_path)
            if changed_file.name == "tasks.md":
                relevant.add((change_type, changed_path))
            elif changed_file.suffix == ".md" and "task" in changed_file.name.lower():
                # Also catch task-related markdown files
                relevant.add((change_type, changed_path))
        return relevant

    async def _handle_changes(self, changes: Set[tuple], handler: Callable) -> None:
        """Handle tasks.md changes - compute hash to detect actual content changes."""
        import hashlib
        import json

        # Ensure .task_runtime/ exists when tasks.md is detected
        self._ensure_task_runtime()

        for change_type, changed_path in changes:
            tasks_file = Path(changed_path)

            # Compute hash of tasks.md content
            current_hash = None
            if tasks_file.exists():
                try:
                    content = tasks_file.read_text(encoding="utf-8")
                    current_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                except Exception as e:
                    logger.error(f"[StructureWatcher] Failed to read tasks.md: {e}")

            # Only trigger if content actually changed
            if current_hash != self._last_tasks_hash:
                self._last_tasks_hash = current_hash

                event = {
                    "event_type": "structure_change",
                    "file": str(tasks_file),
                    "change_type": change_type.name,
                    "project_path": str(self.project_path),
                    "tasks_hash": current_hash,
                    "timestamp": asyncio.get_event_loop().time(),
                }

                logger.info(f"[StructureWatcher] Structure change detected: {event}")

                if self.on_structure_change:
                    try:
                        await self.on_structure_change(event)
                    except Exception as e:
                        logger.error(f"[StructureWatcher] Callback error: {e}")
            else:
                logger.debug("[StructureWatcher] tasks.md changed but content hash unchanged - ignoring")


class StatusWatcher(BaseWatcher):
    """
    Watches .task_runtime/current-task.json for real-time status updates.
    Triggers sync to database when AI writes progress.
    """

    def __init__(
        self,
        project_path: Path,
        sync_service: "SyncService",
        debounce_ms: int = 500,
        on_status_change: Optional[Callable[[dict], Awaitable[None]]] = None
    ):
        runtime_path = project_path / ".task_runtime"
        super().__init__(runtime_path, debounce_ms, name="StatusWatcher")

        self.project_path = project_path
        self.sync_service = sync_service
        self.on_status_change = on_status_change
        self._current_task_file = runtime_path / "current-task.json"

        logger.info(f"[StatusWatcher] Monitoring .task_runtime/ for current-task.json")

    def _filter_changes(self, changes: Set[tuple]) -> Set[tuple]:
        """Only care about current-task.json."""
        relevant = set()
        for change_type, changed_path in changes:
            changed_file = Path(changed_path)
            if changed_file.name == "current-task.json":
                relevant.add((change_type, changed_path))
        return relevant

    async def _handle_changes(self, changes: Set[tuple], handler: Callable) -> None:
        """Handle current-task.json changes - trigger sync."""
        for change_type, changed_path in changes:
            logger.info(f"[StatusWatcher] current-task.json changed: {change_type.name}")

            # Trigger sync via sync service
            try:
                result = await self.sync_service.sync_current_task()

                action = result.get("action", "unknown")
                ticket_found = result.get("ticket_found", False)
                bulk_count = len(result.get("bulk_sync", []))

                logger.info(f"[StatusWatcher] Sync result: action={action}, ticket_found={ticket_found}, bulk={bulk_count}")

                event = {
                    "event_type": "status_change",
                    "file": str(self._current_task_file),
                    "change_type": change_type.name,
                    "sync_result": result,
                    "timestamp": asyncio.get_event_loop().time(),
                }

                # Call optional callback (e.g., for auditor trigger)
                if self.on_status_change:
                    try:
                        await self.on_status_change(event)
                    except Exception as e:
                        logger.error(f"[StatusWatcher] Callback error: {e}")

                # Trigger auditor if task completed
                if action and "-> done" in action:
                    logger.info("[StatusWatcher] Task completed - auditor trigger available")

            except Exception as e:
                logger.error(f"[StatusWatcher] Sync failed: {e}")

    async def force_sync(self) -> dict:
        """Manually trigger a sync."""
        return await self.sync_service.sync_current_task()


class DualWatcherManager:
    """
    Manages both StructureWatcher and StatusWatcher.
    Provides unified interface for the TicketManager.
    """

    def __init__(
        self,
        project_path: Path,
        sync_service: "SyncService",
        structure_debounce_ms: int = 1000,
        status_debounce_ms: int = 500,
    ):
        self.project_path = project_path
        self.sync_service = sync_service

        self.structure_watcher = StructureWatcher(
            project_path=project_path,
            debounce_ms=structure_debounce_ms,
            on_structure_change=self._on_structure_change
        )

        self.status_watcher = StatusWatcher(
            project_path=project_path,
            sync_service=sync_service,
            debounce_ms=status_debounce_ms,
            on_status_change=self._on_status_change
        )

        self._structure_callback: Optional[Callable[[dict], Awaitable[None]]] = None
        self._status_callback: Optional[Callable[[dict], Awaitable[None]]] = None

        logger.info("[DualWatcherManager] Initialized with StructureWatcher + StatusWatcher")

    def set_structure_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Set callback for structure changes (tasks.md)."""
        self._structure_callback = callback

    def set_status_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Set callback for status changes (current-task.json)."""
        self._status_callback = callback

    async def _on_structure_change(self, event: dict) -> None:
        """Internal handler for structure changes."""
        if self._structure_callback:
            try:
                await self._structure_callback(event)
            except Exception as e:
                logger.error(f"[DualWatcherManager] Structure callback error: {e}")

    async def _on_status_change(self, event: dict) -> None:
        """Internal handler for status changes."""
        if self._status_callback:
            try:
                await self._status_callback(event)
            except Exception as e:
                logger.error(f"[DualWatcherManager] Status callback error: {e}")

    async def start(self) -> None:
        """Start both watchers concurrently."""
        logger.info("[DualWatcherManager] Starting both watchers...")

        self.structure_watcher._task = asyncio.create_task(
            self.structure_watcher.run(self.structure_watcher._handle_changes)
        )
        self.status_watcher._task = asyncio.create_task(
            self.status_watcher.run(self.status_watcher._handle_changes)
        )

        # Wait a bit for both to start
        await asyncio.sleep(0.1)
        logger.info("[DualWatcherManager] Both watchers started")

    async def stop(self) -> None:
        """Stop both watchers gracefully."""
        logger.info("[DualWatcherManager] Stopping both watchers...")

        await asyncio.gather(
            self.structure_watcher.stop(),
            self.status_watcher.stop(),
            return_exceptions=True
        )

        logger.info("[DualWatcherManager] Both watchers stopped")

    @property
    def is_watching(self) -> bool:
        return self.structure_watcher.is_watching and self.status_watcher.is_watching

    def get_status(self) -> dict:
        """Get status of both watchers."""
        return {
            "structure_watcher": {
                "running": self.structure_watcher.is_watching,
                "watch_path": str(self.structure_watcher.watch_path),
                "last_tasks_hash": self.structure_watcher._last_tasks_hash,
            },
            "status_watcher": {
                "running": self.status_watcher.is_watching,
                "watch_path": str(self.status_watcher.watch_path),
                "current_task_file": str(self.status_watcher._current_task_file),
            },
        }