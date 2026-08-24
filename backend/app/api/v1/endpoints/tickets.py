from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Project,
    Artifact,
    DocVersion,
    Ticket,
    TicketStatus,
    TicketEvent,
    TicketEventType,
    AuthorType,
)
from app.services.ticket_ingestion import (
    ingest_all_tasks,
    get_ticket_by_id,
    get_tickets_by_project,
    update_ticket_status,
    add_ticket_comment,
    get_ticket_events,
    get_ticket_comments,
    get_project_progress,
    apply_commit_refinement,
)
from app.utils.path_builder import BASE_DIR, extract_project_name_from_path
from app.agents.ticket_agent import get_ticket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class TicketResponse(BaseModel):
    id: str
    project_id: str
    ticket_id: Optional[str] = None
    source_file_path: str
    title: str
    description: Optional[str] = None
    status: str
    line_number: Optional[int] = None
    checkbox_state: Optional[str] = None
    source_file_hash: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TicketCommentResponse(BaseModel):
    id: str
    ticket_id: str
    author_type: str
    body: str
    created_at: str

    class Config:
        from_attributes = True


class TicketEventResponse(BaseModel):
    id: str
    ticket_id: str
    event_type: str
    author_type: str
    payload: Optional[Dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New status: todo, in_progress, or done")


class CommentCreateRequest(BaseModel):
    body: str = Field(..., min_length=1, description="Comment body")
    author_type: Optional[str] = Field("human", description="human or agent")


class IngestRequest(BaseModel):
    tasks_dir: Optional[str] = None
    project_name: Optional[str] = None


class CommitRefineRequest(BaseModel):
    commit_message: str = Field(..., min_length=1)
    project_name: Optional[str] = None


class AuditRequest(BaseModel):
    task_id: str
    git_diff: str
    changed_files: List[str]
    criteria: List[str]
    spec_documents: Optional[Dict[str, str]] = None
    commit_messages: Optional[List[str]] = None
    branch_name: Optional[str] = ""
    task_title: Optional[str] = ""
    task_description: Optional[str] = ""


class StructureSyncResponse(BaseModel):
    tasks_md_found: bool
    tasks_md_path: Optional[str] = None
    tasks_md_hash: Optional[str] = None
    task_count: int
    tasks: List[Dict[str, Any]]
    ready_for_ingestion: bool
    message: str


class RefreshResponse(BaseModel):
    project_path: str
    timestamp: str
    tasks_md_files: List[Dict[str, Any]]
    current_task_json: Optional[Dict[str, Any]] = None
    sync_results: List[Dict[str, Any]]
    discrepancies: List[Dict[str, Any]]
    summary: Dict[str, Any]


class ProgressResponse(BaseModel):
    total: int
    done: int
    in_progress: int
    todo: int
    progress_pct: float


class TicketMetricsResponse(BaseModel):
    task_id: str
    conformity_score: Optional[float] = None
    verdict: Optional[str] = None
    requirement_coverage: Optional[float] = None
    code_quality: Optional[float] = None
    architecture: Optional[float] = None
    traceability: Optional[float] = None
    last_audit_at: Optional[str] = None
    progress_pct: float
    status: str


class ProjectMetricsResponse(BaseModel):
    project_name: str
    total_tickets: int
    done_tickets: int
    in_progress_tickets: int
    todo_tickets: int
    overall_progress_pct: float
    avg_conformity_score: Optional[float] = None
    tickets_with_audit: int
    tickets_by_verdict: Dict[str, int]
    tickets_metrics: List[TicketMetricsResponse]


def _to_ticket_response(t: Ticket) -> TicketResponse:
    """Convert Ticket ORM to TicketResponse."""
    return TicketResponse(
        id=str(t.id),
        project_id=str(t.project_id),
        ticket_id=t.ticket_id,
        source_file_path=t.source_file_path,
        title=t.title,
        description=t.description,
        status=t.status.value,
        line_number=t.line_number,
        checkbox_state=t.checkbox_state,
        source_file_hash=t.source_file_hash,
        created_at=t.created_at.isoformat() if t.created_at else "",
        updated_at=t.updated_at.isoformat() if t.updated_at else "",
    )


@router.get("/tickets", response_model=List[TicketResponse])
async def list_tickets(
    project_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    GET /tickets - List all tickets, optionally filtered by project or status.
    """
    if project_name:
        project = db.query(Project).filter(Project.name == project_name).first()
        if not project:
            return []
        tickets = get_tickets_by_project(db, str(project.id), status)
    else:
        query = db.query(Ticket)
        if status:
            try:
                status_enum = TicketStatus(status)
                query = query.filter(Ticket.status == status_enum)
            except ValueError:
                pass
        tickets = query.order_by(Ticket.project_id, Ticket.line_number).all()

    return [_to_ticket_response(t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /tickets/{id} - Get a single ticket by ID.
    """
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _to_ticket_response(ticket)


@router.get("/tickets/{ticket_id}/metrics", response_model=TicketMetricsResponse)
async def get_ticket_metrics(
    ticket_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /tickets/{ticket_id}/metrics - Get metrics for a specific ticket.
    Returns conformity score, verdict and other audit metrics if available,
    plus progress percentage based on status.
    """
    from app.core.metrics import calculate_sar
    from fastapi import HTTPException
    from app.services.ticket_ingestion import get_ticket_by_id

    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get latest audit event for this ticket
    audit_event = (
        db.query(TicketEvent)
        .filter(TicketEvent.ticket_id == ticket.id)
        .filter(TicketEvent.event_metadata.isnot(None))
        .order_by(TicketEvent.created_at.desc())
        .first()
    )

    conformity_score = None
    verdict = None
    requirement_coverage = None
    code_quality = None
    architecture = None
    traceability = None
    last_audit_at = None
    agent_metrics = None

    if audit_event and audit_event.event_metadata:
        meta = audit_event.event_metadata
        conformity_score = meta.get("conformity_score")
        verdict = meta.get("verdict")
        if meta.get("requirement_coverage"):
            requirement_coverage = meta["requirement_coverage"].get("score")
        if meta.get("code_quality"):
            code_quality = meta["code_quality"].get("score")
        if meta.get("architecture"):
            architecture = meta["architecture"].get("score")
        if meta.get("traceability"):
            traceability = meta["traceability"].get("score")
        last_audit_at = audit_event.created_at.isoformat() if audit_event.created_at else None

        # Collect agent metrics if available
        if any([requirement_coverage, code_quality, architecture, traceability]):
            agent_metrics = {
                "requirement_coverage": requirement_coverage,
                "code_quality": code_quality,
                "architecture": architecture,
                "traceability": traceability
            }

    # Calculate progress based on status
    progress_pct = 100.0 if ticket.status.value == "done" else (50.0 if ticket.status.value == "in_progress" else 0.0)

    return TicketMetricsResponse(
        task_id=ticket.ticket_id,
        conformity_score=conformity_score,
        verdict=verdict,
        requirement_coverage=requirement_coverage,
        code_quality=code_quality,
        architecture=architecture,
        traceability=traceability,
        last_audit_at=last_audit_at,
        progress_pct=progress_pct,
        status=ticket.status.value,
        agent_metrics=agent_metrics,
    )


@router.patch("/tickets/{ticket_id}/status", response_model=TicketResponse)
async def patch_ticket_status(
    ticket_id: str,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    PATCH /tickets/{id}/status - Update ticket status.
    Backward moves (done -> in_progress, in_progress -> todo) are logged as status_override events.
    """
    try:
        target_status = TicketStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in TicketStatus]}",
        )

    ticket = update_ticket_status(db, ticket_id, request.status, AuthorType.human)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return _to_ticket_response(ticket)


@router.post("/tickets/{ticket_id}/comments", response_model=TicketCommentResponse)
async def post_comment(
    ticket_id: str,
    request: CommentCreateRequest,
    db: Session = Depends(get_db),
):
    """
    POST /tickets/{id}/comments - Add a comment to a ticket.
    """
    try:
        author = AuthorType(request.author_type) if request.author_type else AuthorType.human
    except ValueError:
        author = AuthorType.human

    comment = add_ticket_comment(db, ticket_id, request.body, author)
    if not comment:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketCommentResponse(
        id=str(comment.id),
        ticket_id=str(comment.ticket_id),
        author_type=comment.author_type.value,
        body=comment.body,
        created_at=comment.created_at.isoformat() if comment.created_at else "",
    )


@router.get("/tickets/{ticket_id}/comments", response_model=List[TicketCommentResponse])
async def list_comments(
    ticket_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /tickets/{id}/comments - List all comments for a ticket.
    """
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    comments = get_ticket_comments(db, ticket_id)
    return [
        TicketCommentResponse(
            id=str(c.id),
            ticket_id=str(c.ticket_id),
            author_type=c.author_type.value,
            body=c.body,
            created_at=c.created_at.isoformat() if c.created_at else "",
        )
        for c in comments
    ]


@router.get("/tickets/{ticket_id}/events", response_model=List[TicketEventResponse])
async def list_events(
    ticket_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /tickets/{id}/events - List all events for a ticket.
    """
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    events = get_ticket_events(db, ticket_id)
    return [
        TicketEventResponse(
            id=str(e.id),
            ticket_id=str(e.ticket_id),
            event_type=e.event_type.value,
            author_type=e.author_type.value,
            payload=e.event_metadata,
            created_at=e.created_at.isoformat() if e.created_at else "",
        )
        for e in events
    ]


@router.post("/ingest", response_model=List[TicketResponse])
async def ingest_tasks(
    request: IngestRequest,
    db: Session = Depends(get_db),
):
    """
    POST /ingest - Ingest all tasks/*.md files into tickets (idempotent).
    """
    if request.tasks_dir:
        tasks_dir = Path(request.tasks_dir)
    else:
        project_name = request.project_name
        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required when tasks_dir is not provided")

        from app.models import Project, Artifact
        project = db.query(Project).filter(Project.name == project_name).first()
        if project:
            artifact = db.query(Artifact).filter(Artifact.project_id == project.id).first()
            if artifact:
                tasks_dir = Path(artifact.source_path).parent
            else:
                tasks_dir = BASE_DIR / "specs" / project_name
        else:
            tasks_dir = BASE_DIR / "specs" / project_name

    if not tasks_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tasks directory not found. Attempted path: {tasks_dir}. Please ensure the project name matches the folder name in /specs/"
        )

    project_name = request.project_name or extract_project_name_from_path(tasks_dir)

    tickets = ingest_all_tasks(db, tasks_dir, project_name)

    return [_to_ticket_response(t) for t in tickets]


@router.post("/commit-refine", response_model=List[TicketResponse])
async def commit_refine(
    request: CommitRefineRequest,
    db: Session = Depends(get_db),
):
    """
    POST /commit-refine - Refine ticket status based on commit message.
    Parses commit messages referencing task ids (e.g., T001) to sharpen In Progress/Done inference.
    """
    project_name = request.project_name or "001-task-management-api"
    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    tickets = apply_commit_refinement(db, request.commit_message, str(project.id))

    return [_to_ticket_response(t) for t in tickets]


@router.get("/progress", response_model=ProgressResponse)
async def project_progress(
    project_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    GET /progress - Get project-level progress (done/total tickets).
    """
    if project_name:
        project = db.query(Project).filter(Project.name == project_name).first()
        if not project:
            return ProgressResponse(total=0, done=0, in_progress=0, todo=0, progress_pct=0.0)
        progress = get_project_progress(db, str(project.id))
    else:
        tickets = db.query(Ticket).all()
        total = len(tickets)
        done = sum(1 for t in tickets if t.status == TicketStatus.done)
        in_progress = sum(1 for t in tickets if t.status == TicketStatus.in_progress)
        todo = sum(1 for t in tickets if t.status == TicketStatus.todo)
        progress = {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "todo": todo,
            "progress_pct": round(done / total * 100, 1) if total > 0 else 0.0,
        }

    return ProgressResponse(**progress)


@router.post("/sync-current-task")
async def sync_current_task():
    """
    POST /sync-current-task
    Reads .task_runtime/current-task.json and updates matching ticket statuses.
    Delegates to TicketManager for clean separation of concerns.
    """
    manager = get_ticket_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Ticket Manager not initialized")

    result = await manager.force_sync()
    if result.get("error") and not result.get("ticket_found") and not result.get("bulk_sync"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/ticket-agent/status")
async def ticket_agent_status():
    """
    GET /ticket-agent/status
    Returns the current status of the Ticket Agent (watchers, auditor, etc.).
    """
    manager = get_ticket_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Ticket Manager not initialized")
    return manager.get_status()


@router.get("/ticket-agent/structure-sync", response_model=StructureSyncResponse)
async def structure_sync():
    """
    GET /ticket-agent/structure-sync
    Prepares structure synchronization data from tasks.md.
    Called by frontend when StructureWatcher detects changes or on demand.
    Returns task list ready for ingestion.
    """
    manager = get_ticket_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Ticket Manager not initialized")

    result = manager.prepare_structure_sync()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/ticket-agent/full-refresh", response_model=RefreshResponse)
async def full_state_refresh():
    """
    POST /ticket-agent/full-refresh
    Forces a complete project state synchronization.
    Scans all tasks.md files and current-task.json for consistency.
    Called by "Refresh Process" button in frontend.
    """
    manager = get_ticket_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Ticket Manager not initialized")

    result = manager.full_state_refresh()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/ticket-agent/audit")
async def audit_task(
    request: AuditRequest,
):
    """
    POST /ticket-agent/audit
    Triggers conformity audit for a completed task.
    Called when ticket transitions to 'done' (from frontend or webhook).
    Returns conformity score and verdict.
    """
    manager = get_ticket_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Ticket Manager not initialized")

    if not manager.enable_auditor:
        raise HTTPException(status_code=400, detail="Auditor not enabled")

    result = await manager.audit_task_completion(
        task_id=request.task_id,
        git_diff=request.git_diff,
        changed_files=request.changed_files,
        criteria=request.criteria,
        spec_documents=request.spec_documents,
        commit_messages=request.commit_messages,
        branch_name=request.branch_name or "",
        task_title=request.task_title or "",
        task_description=request.task_description or "",
    )
    return result


@router.post("/ticket-agent/audit")
async def audit_task(
    request: AuditRequest,
):
    """
    POST /ticket-agent/audit
    Triggers conformity audit for a completed task.
    Called when ticket transitions to 'done' (from frontend or webhook).
    Returns conformity score and verdict.
    """
    manager = get_ticket_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Ticket Manager not initialized")

    if not manager.enable_auditor:
        raise HTTPException(status_code=400, detail="Auditor not enabled")

    result = await manager.audit_task_completion(
        task_id=request.task_id,
        git_diff=request.git_diff,
        changed_files=request.changed_files,
        criteria=request.criteria,
        spec_documents=request.spec_documents,
        commit_messages=request.commit_messages,
        branch_name=request.branch_name or "",
        task_title=request.task_title or "",
        task_description=request.task_description or "",
    )
    return result


class WriteCurrentTaskRequest(BaseModel):
    task_id: str
    status: str
    project_name: str
    tasks_map: Dict[str, str]


@router.post("/ticket-agent/write-current-task")
async def write_current_task(request: WriteCurrentTaskRequest):
    """
    POST /ticket-agent/write-current-task
    Writes the current task status to .task_runtime/current-task.json.
    Called by frontend when user updates task status via checkbox or drag-and-drop.
    The watcher will detect the change and sync to database.
    """
    import json
    from datetime import datetime
    from pathlib import Path
    from app.config import settings
    from app.utils.path_builder import BASE_DIR

    # Determine project path - use per-project .task_runtime/ under specs/
    project_name = request.project_name
    if project_name:
        project_specs_dir = BASE_DIR / "specs" / project_name
        task_runtime_dir = project_specs_dir / ".task_runtime"
    else:
        task_runtime_dir = BASE_DIR / ".task_runtime"
    task_runtime_dir.mkdir(parents=True, exist_ok=True)
    current_task_file = task_runtime_dir / "current-task.json"

    # Read existing data
    data = {}
    if current_task_file.exists():
        try:
            data = json.loads(current_task_file.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    # Update data
    data["task_id"] = request.task_id
    data["status"] = request.status
    data["project_name"] = request.project_name
    data["updated_at"] = datetime.utcnow().isoformat() + "Z"
    data["tasks"] = request.tasks_map

    # Atomic write
    temp_file = current_task_file.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp_file.replace(current_task_file)

    return {"success": True, "written": True}


@router.get("/ticket-agent/metrics", response_model=ProjectMetricsResponse)
async def get_project_metrics(
    project_name: str,
    db: Session = Depends(get_db),
):
    """
    GET /ticket-agent/metrics?project_name=...
    Returns conformity scores and progress metrics for all tickets in a project.
    Used by frontend to display progress percentage with quality metrics.
    """
    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    tickets = db.query(Ticket).filter(Ticket.project_id == project.id).all()

    tickets_metrics = []
    verdicts_count = {}
    total_conformity = 0
    audited_count = 0

    for ticket in tickets:
        # Get latest audit event for this ticket
        audit_event = (
            db.query(TicketEvent)
            .filter(TicketEvent.ticket_id == ticket.id)
            .filter(TicketEvent.event_metadata.isnot(None))
            .order_by(TicketEvent.created_at.desc())
            .first()
        )

        conformity_score = None
        verdict = None
        req_cov = None
        code_qual = None
        arch = None
        trace = None
        last_audit_at = None

        if audit_event and audit_event.event_metadata:
            meta = audit_event.event_metadata
            conformity_score = meta.get("conformity_score")
            verdict = meta.get("verdict")
            if meta.get("requirement_coverage"):
                req_cov = meta["requirement_coverage"].get("score")
            if meta.get("code_quality"):
                code_qual = meta["code_quality"].get("score")
            if meta.get("architecture"):
                arch = meta["architecture"].get("score")
            if meta.get("traceability"):
                trace = meta["traceability"].get("score")
            last_audit_at = audit_event.created_at.isoformat() if audit_event.created_at else None

            if conformity_score is not None:
                total_conformity += conformity_score
                audited_count += 1

            if verdict:
                verdicts_count[verdict] = verdicts_count.get(verdict, 0) + 1

        tickets_metrics.append(TicketMetricsResponse(
            task_id=ticket.ticket_id,
            conformity_score=conformity_score,
            verdict=verdict,
            requirement_coverage=req_cov,
            code_quality=code_qual,
            architecture=arch,
            traceability=trace,
            last_audit_at=last_audit_at,
            progress_pct=100.0 if ticket.status == TicketStatus.done else (50.0 if ticket.status == TicketStatus.in_progress else 0.0),
            status=ticket.status.value,
        ))

    total = len(tickets)
    done = sum(1 for t in tickets if t.status == TicketStatus.done)
    in_progress = sum(1 for t in tickets if t.status == TicketStatus.in_progress)
    todo = sum(1 for t in tickets if t.status == TicketStatus.todo)

    return ProjectMetricsResponse(
        project_name=project_name,
        total_tickets=total,
        done_tickets=done,
        in_progress_tickets=in_progress,
        todo_tickets=todo,
        overall_progress_pct=round(done / total * 100, 1) if total > 0 else 0.0,
        avg_conformity_score=round(total_conformity / audited_count, 1) if audited_count > 0 else None,
        tickets_with_audit=audited_count,
        tickets_by_verdict=verdicts_count,
        tickets_metrics=tickets_metrics,
    )


@router.get("/tickets/{ticket_id}/doc-pdf")
async def get_ticket_doc_pdf(
    ticket_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /tickets/{id}/doc-pdf - Get the latest doc_version PDF for the ticket's parent artifact.
    Returns clean empty state if the doc isn't generated yet.
    """
    from fastapi.responses import FileResponse
    from pathlib import Path as PathLib

    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not ticket.artifact_id:
        return {"exists": False, "message": "No artifact linked to this ticket"}

    doc_version = (
        db.query(DocVersion)
        .filter(DocVersion.artifact_id == ticket.artifact_id)
        .order_by(DocVersion.version_no.desc())
        .first()
    )

    if not doc_version or not doc_version.pdf_path:
        return {"exists": False, "message": "Document not generated yet"}

    pdf_file = Path(doc_version.pdf_path)
    if not pdf_file.exists():
        return {"exists": False, "message": "PDF file not found on disk"}

    return FileResponse(
        path=str(pdf_file),
        media_type="application/pdf",
        filename=pdf_file.name,
        headers={"Content-Disposition": "inline"},
    )


@router.websocket("/ws/tickets/{project_name}")
async def websocket_tickets(websocket: WebSocket, project_name: str):
    """
    WebSocket endpoint for real-time ticket updates.
    Connects to the Ticket Manager to receive real-time status changes.
    """
    await websocket.accept()
    logger.info(f"[WebSocket] Client connected for project: {project_name}")
    
    try:
        from app.agents.ticket_agent import get_ticket_manager
        manager = get_ticket_manager()
        
        if not manager:
            await websocket.send_json({"type": "error", "message": "Ticket manager not initialized"})
            await websocket.close()
            return
        
        # Register callback for status changes via manager
        async def on_status_change(event):
            try:
                await websocket.send_json({
                    "type": "status_change",
                    "event": event
                })
            except Exception:
                pass  # Client disconnected
        
        # Add callback to manager
        manager.set_status_callback(on_status_change)
        
        # Send initial connection confirmation
        await websocket.send_json({"type": "connected", "project": project_name})
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                # Handle incoming messages if needed (e.g., ping/pong)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
            except Exception:
                break
                
    except WebSocketDisconnect:
        logger.info(f"[WebSocket] Client disconnected for project: {project_name}")
    except Exception as e:
        logger.error(f"[WebSocket] Error for project {project_name}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        logger.info(f"[WebSocket] Connection closed for project: {project_name}")
