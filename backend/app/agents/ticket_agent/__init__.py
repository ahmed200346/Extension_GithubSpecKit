"""
Ticket Agent — Universal Agent Module

Exports the main components for the Universal Ticket Agent architecture.
"""

from .manager import (
    TicketManager,
    get_ticket_manager,
    set_ticket_manager,
    ticket_agent_lifespan,
    create_ticket_manager,
)
from .watcher import StructureWatcher, StatusWatcher
from .sync_service import SyncService
from .auditor import Auditor, audit_task_on_completion

__all__ = [
    "TicketManager",
    "get_ticket_manager",
    "set_ticket_manager",
    "ticket_agent_lifespan",
    "create_ticket_manager",
    "StructureWatcher",
    "StatusWatcher",
    "SyncService",
    "Auditor",
    "audit_task_on_completion",
]