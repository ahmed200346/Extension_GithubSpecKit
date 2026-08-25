from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import tickets, pipeline
from app.agents.ticket_agent.manager import ticket_agent_lifespan
from app.health_check import health, root
from starlette.types import ASGIApp, Scope, Receive, Send
import logging

logger = logging.getLogger(__name__)

class WebSocketCORSMiddleware:
    """
    Custom ASGI middleware to prevent 403 Forbidden on WebSocket connections
    by ensuring the Origin header is handled permissively during development.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket":
            # In development, we bypass the origin check by removing the origin header.
            # This prevents 403 Forbidden errors when connecting from different origins
            # (like the VS Code webview).
            logger.info(f"[WebSocketCORSMiddleware] WebSocket connection attempt: path={scope.get('path')}")
            scope["headers"] = [
                (k, v) for k, v in scope.get("headers", [])
                if k.lower() != b"origin"
            ]
        await self.app(scope, receive, send)

app = FastAPI(
    title="SpecKit Extension API",
    version="1.0.0",
    lifespan=ticket_agent_lifespan
)

# Add WebSocket CORS middleware FIRST (runs first for WebSocket, ignored for HTTP)
app.add_middleware(WebSocketCORSMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(tickets.router, prefix="/api/v1", tags=["Tickets"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])

# Health check endpoints
app.add_api_route("/health", health, methods=["GET"])
app.add_api_route("/", root, methods=["GET"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
