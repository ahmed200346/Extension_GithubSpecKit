import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base

import app.models

# Import routers
from app.api.v1.endpoints import pipeline
from app.api.v1.endpoints import tickets

# Import Ticket Agent lifespan
from app.agents.ticket_agent import ticket_agent_lifespan

# 1. Création automatique des tables BDD si elles n'existent pas et synchronisation des ENUMs natifs
Base.metadata.create_all(bind=engine)
app.models.sync_native_enums(engine)

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Combined lifespan: starts Ticket Agent watcher + any other startup/shutdown logic.
    """
    logger.info("[lifespan] Server starting...")

    # Start Ticket Agent (includes file watcher)
    async with ticket_agent_lifespan(app):
        logger.info("[lifespan] Ticket Agent started")
        yield

    logger.info("[lifespan] Server shutting down...")


# 2. Initialisation UNIQUE de FastAPI
app = FastAPI(
    title="Spec Kit Extension - AgentDocx API",
    version="1.0.0",
    description="API FastAPI d'orchestration Multi-Agents LangGraph pour Spec Kit",
    lifespan=lifespan,
)

# 3. Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Inclusion des Routers
# -> Prefix /api/v1/docs : Requis par le Frontend React (AddDocument.jsx & Documents.jsx)
app.include_router(pipeline.router, prefix="/api/v1/docs", tags=["Documents & Pipeline Frontend"])

# -> Prefix /api/v1/pipeline : Conservé pour scripts CLI, Watcher ou outils externes
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline CLI"])

# -> Prefix /api/v1 : Endpoints Kanban (tickets, progress, ingest, commit-refine, ticket-agent)
app.include_router(tickets.router, prefix="/api/v1", tags=["Tickets Kanban"])


# 5. Endpoints de santé (Health Checks)
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "SpecKit Extension API is running!",
        "swagger_docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/debug-current-task", tags=["Debug"])
async def debug_current_task():
    """
    GET /debug-current-task
    Runs the full sync logic via TicketManager and returns detailed diagnostics.
    """
    from app.agents.ticket_agent import get_ticket_manager
    from app.config import settings
    from app.utils.path_builder import BASE_DIR

    manager = get_ticket_manager()
    if not manager:
        return {"error": "Ticket Manager not initialized"}

    result = manager.force_sync()

    # Add additional debug info about paths
    result["debug_paths"] = {
        "BASE_DIR": str(BASE_DIR),
        "TARGET_PROJECT_PATH_setting": settings.TARGET_PROJECT_PATH,
        "computed_current_task_file": str(manager.current_task_file),
        "manager_status": manager.get_status(),
    }

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)