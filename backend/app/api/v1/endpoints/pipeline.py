import json
import hashlib
import traceback
import urllib.parse
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Modèles et session BDD
from app.database import get_db
from app.models import (
    Project, Artifact, DocVersion, PipelineRun, ArtifactType, PipelineStage, GeneratedBy,
    Ticket, TicketStatus, TicketEvent, TicketEventType, AuthorType,
)
from app.services.db_service import (
    should_process_file,
    check_file_exists_only,
    create_pipeline_run,
    get_next_version,
    create_doc_version_pending,
    save_successful_run,
    save_failed_run,
)
from app.utils.path_builder import build_pipeline_paths, extract_project_name_from_path, sanitize_path_string, BASE_DIR
from app.graph.workflow import create_pipeline_workflow

router = APIRouter()
app_graph = create_pipeline_workflow()

# In-memory task state store (keyed by project_name)
_task_state_store: Dict[str, Dict[str, Any]] = {}

PIPELINE_STATUS = {
    "is_running": False,
    "current_file": None
}


# ============================================
# UTILITAIRES
# ============================================

def to_posix_str(path_obj: Any) -> str:
    """Conversion fiable d'un chemin vers format POSIX strict, SANS caracteres de controle."""
    if path_obj is None:
        return ""
    return sanitize_path_string(Path(path_obj).as_posix())


def get_effective_project_name(file_path_obj: Path, provided_project_name: Optional[str] = None) -> str:
    """
    Normalise le nom du projet.
    Force le nom de la racine si 'memory' ou '.specify/memory' est detecte.
    """
    raw_project = provided_project_name.strip() if provided_project_name and provided_project_name.strip() else None
    if raw_project:
        raw_project = urllib.parse.unquote(raw_project.replace("+", " "))
    
    clean_p = sanitize_path_string(raw_project) if raw_project else ""
    path_posix = file_path_obj.as_posix().lower()

    if clean_p.lower() in ("memory", "", "default project") or ".specify" in path_posix:
        root_project = BASE_DIR.name
        if root_project in (".", "", "backend"):
            root_project = "TestExtension"
        return root_project
    return clean_p


def load_json_if_exists(file_path: Optional[Any]) -> Optional[Dict[str, Any]]:
    if not file_path:
        return None
    p = Path(to_posix_str(file_path))
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def calculate_global_kpi(evaluations: Dict[str, Optional[Dict[str, Any]]]) -> float:
    scores = []
    for agent_eval in evaluations.values():
        if not agent_eval or not isinstance(agent_eval, dict):
            continue
        for section in ["technical_evaluation", "project_management_kpis"]:
            section_data = agent_eval.get(section, {})
            if isinstance(section_data, dict):
                for key, val in section_data.items():
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        if any(term in key for term in ["score", "rate", "index", "adherence", "conformity", "completeness"]):
                            scores.append(float(val))
    return round(sum(scores) / len(scores), 1) if scores else 0.0


# ============================================
# ROUTES PIPELINE ACCESSIBLES VIA /api/v1/docs
# ============================================

@router.get("/status")
async def get_pipeline_status():
    return PIPELINE_STATUS


@router.get("/progress")
async def get_pipeline_progress(db: Session = Depends(get_db)):
    """
    GET /progress - Retourne la progression actuelle du pipeline.
    Utilisé par le frontend pour afficher l'état en temps réel.
    """
    # Récupérer la dernière exécution en cours ou la plus récente
    latest_run = (
        db.query(PipelineRun)
        .filter(PipelineRun.current_stage != PipelineStage.completed)
        .filter(PipelineRun.current_stage != PipelineStage.failed)
        .order_by(PipelineRun.started_at.desc())
        .first()
    )
    
    if not latest_run:
        # Pas de pipeline en cours, chercher le dernier complété
        latest_run = (
            db.query(PipelineRun)
            .order_by(PipelineRun.started_at.desc())
            .first()
        )
    
    if not latest_run:
        return {
            "is_running": False,
            "current_stage": None,
            "progress_percent": 0,
            "message": "No pipeline runs found"
        }
    
    # Calculer le pourcentage de progression basé sur le stage
    stage_progress = {
        PipelineStage.parsing: 10,
        PipelineStage.parallel_enrichment: 25,
        PipelineStage.summary: 35,
        PipelineStage.glossary: 45,
        PipelineStage.diagram: 55,
        PipelineStage.writing: 70,
        PipelineStage.layout: 85,
        PipelineStage.rendering: 95,
        PipelineStage.completed: 100,
        PipelineStage.failed: 0,
    }
    
    progress = stage_progress.get(latest_run.current_stage, 0)
    is_running = latest_run.current_stage not in [PipelineStage.completed, PipelineStage.failed]
    
    return {
        "is_running": is_running,
        "current_stage": latest_run.current_stage.value,
        "progress_percent": progress,
        "run_id": str(latest_run.id),
        "started_at": latest_run.started_at.isoformat() if latest_run.started_at else None,
        "message": f"Pipeline {latest_run.current_stage.value}"
    }


@router.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    """GET /projects - Liste tous les projets avec leur nombre d'artefacts."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "repo_url": p.repo_url,
            "artifact_count": len(p.artifacts),
            "created_at": p.created_at.isoformat() if p.created_at else "",
        }
        for p in projects
    ]


@router.get("/task-state/{project_name}")
async def get_task_state(project_name: str, db: Session = Depends(get_db)):
    """GET /task-state/{project_name} - État courant des tâches pour le Kanban.
    Authoritative version: reads from current-task.json and Database.
    """
    # 1. Read current-task.json for the active task ID
    current_task_json_path = BASE_DIR / ".task_runtime" / "current-task.json"
    current_task_data = {}
    if current_task_json_path.exists():
        try:
            current_task_data = json.loads(current_task_json_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 2. Get all tickets for this project from DB to build the status map
    from app.models import Project, Ticket
    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        return {
            "current_task": 0,
            "total_tasks": 0,
            "task_status": {},
            "started_at": None,
            "updated_at": None,
        }

    tickets = db.query(Ticket).filter(Ticket.project_id == project.id).all()

    # Map ticket_id (e.g. "T001") to its status value
    task_status_map = {t.ticket_id: t.status.value for t in tickets if t.ticket_id}

    # Determine the current task numeric index (T001 -> 1)
    active_task_id = current_task_data.get("task_id")
    current_task_idx = 0
    if active_task_id:
        match = re.match(r'T(\d+)', active_task_id)
        if match:
            current_task_idx = int(match.group(1))

    return {
        "current_task": current_task_idx,
        "total_tasks": len(tickets),
        "task_status": task_status_map,
        "started_at": current_task_data.get("started_at"),
        "updated_at": current_task_data.get("updated_at"),
    }


class TaskStateUpdate(BaseModel):
    current_task_id: Optional[str] = None
    current_task_file: Optional[str] = None
    task_status: Dict[str, str] = {}
    started_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/task-state/{project_name}")
async def update_task_state(project_name: str, state: TaskStateUpdate, db: Session = Depends(get_db)):
    """
    POST /task-state/{project_name}
    Kept for backward compatibility with the VS Code extension.
    Status updates are now driven exclusively by current-task.json via the file watcher.
    This endpoint only stores the state in memory for the GET endpoint to return.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    clean_task_id = state.current_task_id.lstrip("#") if state.current_task_id else None

    # Store in memory for GET /task-state/{project_name} to return
    _task_state_store[project_name] = {
        "current_task_id": clean_task_id or state.current_task_id,
        "current_task_file": state.current_task_file,
        "task_status": state.task_status,
        "started_at": state.started_at or now,
        "updated_at": now,
    }

    return {"status": "ok", "updated_at": now}


@router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    artifacts = db.query(Artifact).order_by(Artifact.created_at.desc()).all()
    result = []

    for artifact in artifacts:
        versions = (
            db.query(DocVersion)
            .filter(DocVersion.artifact_id == artifact.id)
            .order_by(DocVersion.version_no.desc())
            .all()
        )

        if versions:
            for doc_ver in versions:
                run_for_eval = doc_ver.pipeline_run or (
                    db.query(PipelineRun)
                    .filter(PipelineRun.artifact_id == artifact.id)
                    .order_by(PipelineRun.started_at.desc())
                    .first()
                )

                stage_status = "completed"
                if run_for_eval:
                    stage_status = (
                        run_for_eval.current_stage.value 
                        if hasattr(run_for_eval.current_stage, "value") 
                        else str(run_for_eval.current_stage)
                    )

                kpi_val = doc_ver.global_kpi_score
                if kpi_val is None and run_for_eval:
                    kpi_val = run_for_eval.global_kpi_score

                version_display = doc_ver.version_label or f"{doc_ver.version_no}.0"
                if not version_display.startswith("v"):
                    version_display = f"v{version_display}"

                agent_evaluations = {}
                if run_for_eval:
                    agent_evaluations = {
                        "parsing": run_for_eval.parsing_eval or {},
                        "summary": run_for_eval.summary_eval or {},
                        "glossary": run_for_eval.glossary_eval or {},
                        "diagram": run_for_eval.diagram_eval or {},
                        "docWriter": run_for_eval.writer_eval or {},
                        "layout": run_for_eval.layout_eval or {},
                    }

                artifact_name = Path(to_posix_str(artifact.source_path)).stem

                result.append({
                    "id": str(doc_ver.id),
                    "name": artifact_name,
                    "projectName": artifact.project.name if artifact.project else "Default Project",
                    "version": version_display,
                    "status": stage_status,
                    "kpi": round(kpi_val, 1) if kpi_val is not None else None,
                    "doc_version_id": str(doc_ver.id),
                    "pipeline_run_id": str(run_for_eval.id) if run_for_eval else None,
                    "agentEvaluations": agent_evaluations,
                    "generated_at": (doc_ver.generated_at or artifact.created_at).isoformat() if (doc_ver.generated_at or artifact.created_at) else None
                })
        else:
            latest_run = (
                db.query(PipelineRun)
                .filter(PipelineRun.artifact_id == artifact.id)
                .order_by(PipelineRun.started_at.desc())
                .first()
            )
            stage_status = "pending"
            if latest_run:
                stage_status = (
                    latest_run.current_stage.value 
                    if hasattr(latest_run.current_stage, "value") 
                    else str(latest_run.current_stage)
                )

            kpi_val = latest_run.global_kpi_score if latest_run else None

            agent_evaluations = {}
            if latest_run:
                agent_evaluations = {
                    "parsing": latest_run.parsing_eval or {},
                    "summary": latest_run.summary_eval or {},
                    "glossary": latest_run.glossary_eval or {},
                    "diagram": latest_run.diagram_eval or {},
                    "docWriter": latest_run.writer_eval or {},
                    "layout": latest_run.layout_eval or {},
                }

            artifact_name = Path(to_posix_str(artifact.source_path)).stem

            result.append({
                "id": str(artifact.id),
                "name": artifact_name,
                "projectName": artifact.project.name if artifact.project else "Default Project",
                "version": "v1.0",
                "status": stage_status,
                "kpi": round(kpi_val, 1) if kpi_val is not None else None,
                "doc_version_id": None,
                "pipeline_run_id": str(latest_run.id) if latest_run else None,
                "agentEvaluations": agent_evaluations,
                "generated_at": artifact.created_at.isoformat() if artifact.created_at else None
            })

    return result


@router.delete("/documents/{doc_version_id}")
async def delete_document_version(doc_version_id: str, db: Session = Depends(get_db)):
    """Delete a specific document version and its associated data."""
    try:
        doc_version = db.query(DocVersion).filter(DocVersion.id == doc_version_id).first()
        if not doc_version:
            raise HTTPException(status_code=404, detail="Document version not found")
        
        # Delete the PDF file if it exists
        if doc_version.pdf_path and Path(doc_version.pdf_path).exists():
            Path(doc_version.pdf_path).unlink()
        
        # Delete associated pipeline run if exists
        if doc_version.pipeline_run_id:
            db.query(PipelineRun).filter(PipelineRun.id == doc_version.pipeline_run_id).delete()
        
        # Delete the document version
        db.delete(doc_version)
        db.commit()
        
        return {"status": "success", "message": f"Document version {doc_version_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.delete("/artifacts/{artifact_id}")
async def delete_artifact(artifact_id: str, db: Session = Depends(get_db)):
    """Delete an artifact and all its versions."""
    try:
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Delete all document versions and their files
        versions = db.query(DocVersion).filter(DocVersion.artifact_id == artifact_id).all()
        for version in versions:
            if version.pdf_path and Path(version.pdf_path).exists():
                Path(version.pdf_path).unlink()
        
        # Delete all pipeline runs
        db.query(PipelineRun).filter(PipelineRun.artifact_id == artifact_id).delete()
        
        # Delete all document versions
        db.query(DocVersion).filter(DocVersion.artifact_id == artifact_id).delete()
        
        # Delete the artifact itself
        db.delete(artifact)
        db.commit()
        
        return {"status": "success", "message": f"Artifact {artifact_id} and all versions deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete artifact: {str(e)}")


@router.post("/upload")
async def upload_and_process_document(
    file: UploadFile = File(...),
    projectName: str = Form(...),
    db: Session = Depends(get_db)
):
    global PIPELINE_STATUS

    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .md sont acceptés.")

    file.filename = sanitize_path_string(file.filename)
    project_clean = get_effective_project_name(Path(file.filename), projectName)
    
    import tempfile
    # Use system temporary directory instead of creating any folder in the project root
    dest_dir = Path(tempfile.gettempdir()) / "speckit_uploads" / project_clean
    dest_dir.mkdir(parents=True, exist_ok=True)

    file_path = dest_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    file_path_posix = Path(to_posix_str(file_path.resolve()))
    
    should_run, new_hash, artifact = should_process_file(db, file_path_posix, project_clean)
    if not should_run:
        return {
            "status": "skipped",
            "message": "Fichier identique déjà existant.",
            "artifact_id": str(artifact.id)
        }

    PIPELINE_STATUS["is_running"] = True
    PIPELINE_STATUS["current_file"] = to_posix_str(file_path_posix)

    pipeline_run = create_pipeline_run(db, artifact.id)
    next_version_no, next_version_label = get_next_version(db, artifact.id)

    # Création de la DocVersion en statut 'pending' dès le début du traitement pour gestion v1, v2... vn
    doc_version = create_doc_version_pending(
        db=db,
        artifact=artifact,
        pipeline_run=pipeline_run,
        version_label=next_version_label,
        version_no=next_version_no
    )

    try:
        paths = build_pipeline_paths(
            file_name=to_posix_str(file_path_posix),
            version_label=next_version_label,
            project_name=project_clean
        )

        initial_state = {
            "file_name": to_posix_str(file_path_posix),
            "file_content": content.decode("utf-8", errors="ignore"),
            "version_label": next_version_label,
            "run_id": pipeline_run.id,
            "doc_version_id": str(doc_version.id),
            "prefix": paths["prefix"],
            "project_name": project_clean,
            "final_pdf_path": to_posix_str(paths["final_pdf"])
        }

        # Exécution synchrone du graphe d'agents
        final_state = await app_graph.ainvoke(initial_state)

        evaluations = {
            "parsing": load_json_if_exists(paths.get("parsing_eval")),
            "summary": load_json_if_exists(paths.get("summary_eval")),
            "glossary": load_json_if_exists(paths.get("glossary_eval")),
            "diagram": load_json_if_exists(paths.get("diagram_eval")),
            "writer": load_json_if_exists(paths.get("doc_eval")),
            "layout": load_json_if_exists(paths.get("layout_eval")),
        }

        global_kpi = calculate_global_kpi(evaluations)

        layout_pdf_path = final_state.get("layout_pdf_path")
        if layout_pdf_path:
            final_pdf_path = to_posix_str(layout_pdf_path)
        else:
            final_pdf_path = to_posix_str(paths.get("final_pdf"))

        # Mise à jour et finalisation de la DocVersion
        doc_version = save_successful_run(
            db=db,
            artifact=artifact,
            pipeline_run=pipeline_run,
            new_hash=new_hash,
            pdf_path=final_pdf_path,
            doc_version=doc_version,
            structured_json=final_state.get("parsed_json_dict"),
            summary_output=str(final_state.get("summary_doc")) if final_state.get("summary_doc") else None,
            diagram_output=final_state.get("diagram_doc").model_dump() if hasattr(final_state.get("diagram_doc"), "model_dump") else final_state.get("diagram_doc"),
            glossary_output=final_state.get("glossary_doc").model_dump() if hasattr(final_state.get("glossary_doc"), "model_dump") else final_state.get("glossary_doc"),
            written_doc=final_state.get("doc_writer_doc").markdown_content if hasattr(final_state.get("doc_writer_doc"), "markdown_content") else None,
            layout_output=str(final_state.get("layout_doc")) if final_state.get("layout_doc") else None,
            parsing_eval=evaluations["parsing"],
            summary_eval=evaluations["summary"],
            glossary_eval=evaluations["glossary"],
            diagram_eval=evaluations["diagram"],
            writer_eval=evaluations["writer"],
            layout_eval=evaluations["layout"],
            global_kpi_score=global_kpi
        )

        return {
            "status": "completed",
            "artifact_id": str(artifact.id),
            "doc_version_id": str(doc_version.id),
            "message": "Upload et traitement réussis."
        }

    except Exception as e:
        save_failed_run(db, pipeline_run, str(e))
        tb_str = traceback.format_exc()
        import sys as _sys
        _sys.stderr.write(f"❌ [PIPELINE] Erreur lors du traitement : {tb_str}\n")
        _sys.stderr.flush()
        _diag_log = Path("pipeline_error_traceback.log")
        _diag_log.write_text(tb_str, encoding="utf-8")
        raise HTTPException(status_code=500, detail=f"Erreur Pipeline: {str(e)}\n{tb_str}")
    
    finally:
        PIPELINE_STATUS["is_running"] = False
        PIPELINE_STATUS["current_file"] = None


@router.get("/pdf/{doc_version_id}")
async def view_pdf(doc_version_id: UUID, db: Session = Depends(get_db)):
    doc_ver = db.query(DocVersion).filter(DocVersion.id == doc_version_id).first()
    if not doc_ver or not doc_ver.pdf_path:
        raise HTTPException(status_code=404, detail="PDF non trouvé.")

    pdf_file = Path(to_posix_str(doc_ver.pdf_path))
    if not pdf_file.exists():
        raise HTTPException(status_code=404, detail="Fichier PDF introuvable sur le disque.")

    return FileResponse(
        path=pdf_file,
        media_type="application/pdf",
        filename=pdf_file.name,
        headers={"Content-Disposition": "inline"}
    )


@router.get("/download/{doc_version_id}")
async def download_pdf(doc_version_id: UUID, db: Session = Depends(get_db)):
    doc_ver = db.query(DocVersion).filter(DocVersion.id == doc_version_id).first()
    if not doc_ver or not doc_ver.pdf_path:
        raise HTTPException(status_code=404, detail="PDF non trouvé.")

    pdf_file = Path(to_posix_str(doc_ver.pdf_path))
    if not pdf_file.exists():
        raise HTTPException(status_code=404, detail="Fichier PDF introuvable sur le disque.")

    return FileResponse(
        path=pdf_file,
        media_type="application/pdf",
        filename=pdf_file.name,
        headers={"Content-Disposition": f"attachment; filename={pdf_file.name}"}
    )


@router.get("/artifact/{artifact_id}")
async def get_artifact_details(artifact_id: UUID, db: Session = Depends(get_db)):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artefact non trouvé.")

    versions = db.query(DocVersion).filter(DocVersion.artifact_id == artifact.id).order_by(DocVersion.version_no.desc()).all()

    version_list = []
    for v in versions:
        version_list.append({
            "id": str(v.id),
            "version_no": v.version_no,
            "version_label": v.version_label,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "global_kpi_score": v.global_kpi_score
        })

    artifact_name = Path(to_posix_str(artifact.source_path)).stem

    return {
        "id": str(artifact.id),
        "name": artifact_name,
        "projectName": artifact.project.name if artifact.project else "Default Project",
        "source_path": to_posix_str(artifact.source_path),
        "versions": version_list
    }


@router.get("/diagnose-path")
async def diagnose_path(file_path: str = "", project_name: str = ""):
    import os
    import sys as _sys
    results = []
    
    try:
        p = Path(file_path)
        results.append({"step": "Path(file_path)", "ok": True, "value": str(p)})
    except Exception as e:
        results.append({"step": "Path(file_path)", "ok": False, "error": str(e)})
    
    try:
        r = p.resolve()
        results.append({"step": "resolve()", "ok": True, "value": str(r)})
    except Exception as e:
        results.append({"step": "resolve()", "ok": False, "error": str(e)})
    
    try:
        posix = r.as_posix()
        results.append({"step": "as_posix()", "ok": True, "value": posix})
    except Exception as e:
        results.append({"step": "as_posix()", "ok": False, "error": str(e)})
    
    from app.utils.path_builder import sanitize_path_string
    try:
        clean = sanitize_path_string(file_path)
        results.append({"step": "sanitize_path_string()", "ok": True, "value": clean})
    except Exception as e:
        results.append({"step": "sanitize_path_string()", "ok": False, "error": str(e)})
    
    from app.utils.path_builder import extract_project_name_from_path
    try:
        pn = extract_project_name_from_path(Path(file_path))
        results.append({"step": "extract_project_name_from_path()", "ok": True, "value": pn})
    except Exception as e:
        results.append({"step": "extract_project_name_from_path()", "ok": False, "error": str(e)})
    
    from app.utils.path_builder import build_pipeline_paths
    try:
        paths = build_pipeline_paths(file_name=file_path, project_name=project_name or pn)
        results.append({"step": "build_pipeline_paths() mkdir", "ok": True, "dirs_created": str(paths.get("base_output_dir"))})
    except Exception as e:
        results.append({"step": "build_pipeline_paths() mkdir", "ok": False, "error": str(e)})
    
    try:
        import tempfile
        tmp_dir = Path(tempfile.gettempdir()) / "speckit_diag" / (project_name or "test_diag")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = tmp_dir / "_diag_test_.tmp"
        tmp_file.write_bytes(b"test")
        results.append({"step": "write_bytes()", "ok": True, "path": str(tmp_file)})
        tmp_file.unlink()
    except Exception as e:
        results.append({"step": "write_bytes()", "ok": False, "error": str(e)})
    
    results.append({"step": "CWD", "value": os.getcwd()})
    from app.utils.path_builder import BASE_DIR
    results.append({"step": "path_builder.BASE_DIR", "value": str(BASE_DIR)})
    results.append({"step": "sys.path[0]", "value": _sys.path[0] if _sys.path else "empty"})
    
    return {"project_name": project_name, "file_path": file_path, "cwd": os.getcwd(), "tests": results}


@router.get("/check-file")
async def check_file_status(
    file_path: str,
    project_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Vérification stricte en LECTURE SEULE.
    Ne crée AUCUN enregistrement en base de données si le fichier n'a pas été traité.
    """
    clean_path_str = to_posix_str(sanitize_path_string(file_path))
    file_path_obj = Path(clean_path_str)
    
    if not file_path_obj.exists():
        return {"exists_in_db": False}

    p_name = get_effective_project_name(file_path_obj, project_name)
    
    # Appel de la fonction de lecture seule mis à jour
    exists = check_file_exists_only(db, file_path_obj, p_name)

    return {"exists_in_db": bool(exists)}
# import json
# import hashlib
# import traceback
# import urllib.parse
# from pathlib import Path
# from typing import Optional, Dict, Any, List
# from uuid import UUID
# from datetime import datetime, timezone

# from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# from sqlalchemy.orm import Session

# # Modèles et session BDD
# from app.database import get_db
# from app.models import Project, Artifact, DocVersion, PipelineRun, ArtifactType, PipelineStage, GeneratedBy
# from app.services.db_service import (
#     should_process_file,
#     check_file_exists_only,
#     create_pipeline_run,
#     get_next_version,
#     save_successful_run,
#     save_failed_run,
# )
# from app.utils.path_builder import build_pipeline_paths, extract_project_name_from_path, sanitize_path_string, BASE_DIR
# from app.graph.workflow import create_pipeline_workflow

# router = APIRouter()
# app_graph = create_pipeline_workflow()

# PIPELINE_STATUS = {
#     "is_running": False,
#     "current_file": None
# }


# # ============================================
# # UTILITAIRES
# # ============================================

# def to_posix_str(path_obj: Any) -> str:
#     """Conversion fiable d'un chemin vers format POSIX strict, SANS caracteres de controle."""
#     if path_obj is None:
#         return ""
#     return sanitize_path_string(Path(path_obj).as_posix())


# def get_effective_project_name(file_path_obj: Path, provided_project_name: Optional[str] = None) -> str:
#     """
#     Normalise le nom du projet.
#     Force le nom de la racine si 'memory' ou '.specify/memory' est detecte.
#     """
#     raw_project = provided_project_name.strip() if provided_project_name and provided_project_name.strip() else None
#     if raw_project:
#         raw_project = urllib.parse.unquote(raw_project.replace("+", " "))
    
#     clean_p = sanitize_path_string(raw_project) if raw_project else ""
#     path_posix = file_path_obj.as_posix().lower()

#     if clean_p.lower() in ("memory", "", "default project") or ".specify" in path_posix:
#         root_project = BASE_DIR.name
#         if root_project in (".", "", "backend"):
#             root_project = "TestExtension"
#         return root_project
#     return clean_p


# def load_json_if_exists(file_path: Optional[Any]) -> Optional[Dict[str, Any]]:
#     if not file_path:
#         return None
#     p = Path(to_posix_str(file_path))
#     if p.exists():
#         try:
#             return json.loads(p.read_text(encoding="utf-8"))
#         except Exception:
#             return None
#     return None


# def calculate_global_kpi(evaluations: Dict[str, Optional[Dict[str, Any]]]) -> float:
#     scores = []
#     for agent_eval in evaluations.values():
#         if not agent_eval or not isinstance(agent_eval, dict):
#             continue
#         for section in ["technical_evaluation", "project_management_kpis"]:
#             section_data = agent_eval.get(section, {})
#             if isinstance(section_data, dict):
#                 for key, val in section_data.items():
#                     if isinstance(val, (int, float)) and not isinstance(val, bool):
#                         if any(term in key for term in ["score", "rate", "index", "adherence", "conformity", "completeness"]):
#                             scores.append(float(val))
#     return round(sum(scores) / len(scores), 1) if scores else 0.0


# # ============================================
# # ROUTES PIPELINE ACCESSIBLES VIA /api/v1/docs
# # ============================================

# @router.get("/status")
# async def get_pipeline_status():
#     return PIPELINE_STATUS


# @router.get("/documents")
# async def list_documents(db: Session = Depends(get_db)):
#     artifacts = db.query(Artifact).order_by(Artifact.created_at.desc()).all()
#     result = []

#     for artifact in artifacts:
#         versions = (
#             db.query(DocVersion)
#             .filter(DocVersion.artifact_id == artifact.id)
#             .order_by(DocVersion.version_no.desc())
#             .all()
#         )

#         if versions:
#             for doc_ver in versions:
#                 run_for_eval = doc_ver.pipeline_run or (
#                     db.query(PipelineRun)
#                     .filter(PipelineRun.artifact_id == artifact.id)
#                     .order_by(PipelineRun.started_at.desc())
#                     .first()
#                 )

#                 stage_status = "completed"
#                 if run_for_eval:
#                     stage_status = (
#                         run_for_eval.current_stage.value 
#                         if hasattr(run_for_eval.current_stage, "value") 
#                         else str(run_for_eval.current_stage)
#                     )

#                 kpi_val = doc_ver.global_kpi_score
#                 if kpi_val is None and run_for_eval:
#                     kpi_val = run_for_eval.global_kpi_score

#                 version_display = doc_ver.version_label or f"{doc_ver.version_no}.0"
#                 if not version_display.startswith("v"):
#                     version_display = f"v{version_display}"

#                 agent_evaluations = {}
#                 if run_for_eval:
#                     agent_evaluations = {
#                         "parsing": run_for_eval.parsing_eval or {},
#                         "summary": run_for_eval.summary_eval or {},
#                         "glossary": run_for_eval.glossary_eval or {},
#                         "diagram": run_for_eval.diagram_eval or {},
#                         "docWriter": run_for_eval.writer_eval or {},
#                         "layout": run_for_eval.layout_eval or {},
#                     }

#                 artifact_name = Path(to_posix_str(artifact.source_path)).stem

#                 result.append({
#                     "id": str(doc_ver.id),
#                     "name": artifact_name,
#                     "projectName": artifact.project.name if artifact.project else "Default Project",
#                     "version": version_display,
#                     "status": stage_status,
#                     "kpi": round(kpi_val, 1) if kpi_val is not None else None,
#                     "doc_version_id": str(doc_ver.id),
#                     "pipeline_run_id": str(run_for_eval.id) if run_for_eval else None,
#                     "agentEvaluations": agent_evaluations
#                 })
#         else:
#             latest_run = (
#                 db.query(PipelineRun)
#                 .filter(PipelineRun.artifact_id == artifact.id)
#                 .order_by(PipelineRun.started_at.desc())
#                 .first()
#             )
#             stage_status = "pending"
#             if latest_run:
#                 stage_status = (
#                     latest_run.current_stage.value 
#                     if hasattr(latest_run.current_stage, "value") 
#                     else str(latest_run.current_stage)
#                 )

#             kpi_val = latest_run.global_kpi_score if latest_run else None

#             agent_evaluations = {}
#             if latest_run:
#                 agent_evaluations = {
#                     "parsing": latest_run.parsing_eval or {},
#                     "summary": latest_run.summary_eval or {},
#                     "glossary": latest_run.glossary_eval or {},
#                     "diagram": latest_run.diagram_eval or {},
#                     "docWriter": latest_run.writer_eval or {},
#                     "layout": latest_run.layout_eval or {},
#                 }

#             artifact_name = Path(to_posix_str(artifact.source_path)).stem

#             result.append({
#                 "id": str(artifact.id),
#                 "name": artifact_name,
#                 "projectName": artifact.project.name if artifact.project else "Default Project",
#                 "version": "v1.0",
#                 "status": stage_status,
#                 "kpi": round(kpi_val, 1) if kpi_val is not None else None,
#                 "doc_version_id": None,
#                 "pipeline_run_id": str(latest_run.id) if latest_run else None,
#                 "agentEvaluations": agent_evaluations
#             })

#     return result


# @router.post("/upload")
# async def upload_and_process_document(
#     file: UploadFile = File(...),
#     projectName: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     global PIPELINE_STATUS

#     if not file.filename.endswith(".md"):
#         raise HTTPException(status_code=400, detail="Seuls les fichiers .md sont acceptés.")

#     file.filename = sanitize_path_string(file.filename)
#     project_clean = get_effective_project_name(Path(file.filename), projectName)
    
#     # Créer le répertoire cible sous <RACINE>/specs/<projectName>/
#     dest_dir = BASE_DIR / "specs" / project_clean
#     dest_dir.mkdir(parents=True, exist_ok=True)

#     file_path = dest_dir / file.filename
#     content = await file.read()
#     file_path.write_bytes(content)

#     file_path_posix = Path(to_posix_str(file_path.resolve()))
    
#     should_run, new_hash, artifact = should_process_file(db, file_path_posix, project_clean)
#     if not should_run:
#         return {
#             "status": "skipped",
#             "message": "Fichier identique déjà existant.",
#             "artifact_id": str(artifact.id)
#         }

#     PIPELINE_STATUS["is_running"] = True
#     PIPELINE_STATUS["current_file"] = to_posix_str(file_path_posix)

#     pipeline_run = create_pipeline_run(db, artifact.id)
#     _, next_version_label = get_next_version(db, artifact.id)

#     try:
#         paths = build_pipeline_paths(
#             file_name=to_posix_str(file_path_posix),
#             version_label=next_version_label,
#             project_name=project_clean
#         )

#         initial_state = {
#             "file_name": to_posix_str(file_path_posix),
#             "file_content": content.decode("utf-8", errors="ignore"),
#             "version_label": next_version_label,
#             "run_id": pipeline_run.id,
#             "prefix": paths["prefix"],
#             "project_name": project_clean,
#             "final_pdf_path": to_posix_str(paths["final_pdf"])
#         }

#         # Exécution synchrone du graphe d'agents
#         final_state = await app_graph.ainvoke(initial_state)

#         evaluations = {
#             "parsing": load_json_if_exists(paths.get("parsing_eval")),
#             "summary": load_json_if_exists(paths.get("summary_eval")),
#             "glossary": load_json_if_exists(paths.get("glossary_eval")),
#             "diagram": load_json_if_exists(paths.get("diagram_eval")),
#             "writer": load_json_if_exists(paths.get("doc_eval")),
#             "layout": load_json_if_exists(paths.get("layout_eval")),
#         }

#         global_kpi = calculate_global_kpi(evaluations)

#         layout_pdf_path = final_state.get("layout_pdf_path")
#         if layout_pdf_path:
#             final_pdf_path = to_posix_str(layout_pdf_path)
#         else:
#             final_pdf_path = to_posix_str(paths.get("final_pdf"))

#         # Création et sauvegarde définitive de la DocVersion seulement après succès
#         doc_version = save_successful_run(
#             db=db,
#             artifact=artifact,
#             pipeline_run=pipeline_run,
#             new_hash=new_hash,
#             pdf_path=final_pdf_path,
#             structured_json=final_state.get("parsed_json_dict"),
#             summary_output=str(final_state.get("summary_doc")) if final_state.get("summary_doc") else None,
#             diagram_output=final_state.get("diagram_doc").model_dump() if hasattr(final_state.get("diagram_doc"), "model_dump") else final_state.get("diagram_doc"),
#             glossary_output=final_state.get("glossary_doc").model_dump() if hasattr(final_state.get("glossary_doc"), "model_dump") else final_state.get("glossary_doc"),
#             written_doc=final_state.get("doc_writer_doc").markdown_content if hasattr(final_state.get("doc_writer_doc"), "markdown_content") else None,
#             layout_output=str(final_state.get("layout_doc")) if final_state.get("layout_doc") else None,
#             parsing_eval=evaluations["parsing"],
#             summary_eval=evaluations["summary"],
#             glossary_eval=evaluations["glossary"],
#             diagram_eval=evaluations["diagram"],
#             writer_eval=evaluations["writer"],
#             layout_eval=evaluations["layout"],
#             global_kpi_score=global_kpi
#         )

#         return {
#             "status": "completed",
#             "artifact_id": str(artifact.id),
#             "doc_version_id": str(doc_version.id),
#             "message": "Upload et traitement réussis."
#         }

#     except Exception as e:
#         save_failed_run(db, pipeline_run, str(e))
#         tb_str = traceback.format_exc()
#         import sys as _sys
#         _sys.stderr.write(f"❌ [PIPELINE] Erreur lors du traitement : {tb_str}\n")
#         _sys.stderr.flush()
#         _diag_log = Path("pipeline_error_traceback.log")
#         _diag_log.write_text(tb_str, encoding="utf-8")
#         raise HTTPException(status_code=500, detail=f"Erreur Pipeline: {str(e)}\n{tb_str}")
    
#     finally:
#         PIPELINE_STATUS["is_running"] = False
#         PIPELINE_STATUS["current_file"] = None


# @router.get("/pdf/{doc_version_id}")
# async def view_pdf(doc_version_id: UUID, db: Session = Depends(get_db)):
#     doc_ver = db.query(DocVersion).filter(DocVersion.id == doc_version_id).first()
#     if not doc_ver or not doc_ver.pdf_path:
#         raise HTTPException(status_code=404, detail="PDF non trouvé.")

#     pdf_file = Path(to_posix_str(doc_ver.pdf_path))
#     if not pdf_file.exists():
#         raise HTTPException(status_code=404, detail="Fichier PDF introuvable sur le disque.")

#     return FileResponse(
#         path=pdf_file,
#         media_type="application/pdf",
#         filename=pdf_file.name,
#         headers={"Content-Disposition": "inline"}
#     )


# @router.get("/download/{doc_version_id}")
# async def download_pdf(doc_version_id: UUID, db: Session = Depends(get_db)):
#     doc_ver = db.query(DocVersion).filter(DocVersion.id == doc_version_id).first()
#     if not doc_ver or not doc_ver.pdf_path:
#         raise HTTPException(status_code=404, detail="PDF non trouvé.")

#     pdf_file = Path(to_posix_str(doc_ver.pdf_path))
#     if not pdf_file.exists():
#         raise HTTPException(status_code=404, detail="Fichier PDF introuvable sur le disque.")

#     return FileResponse(
#         path=pdf_file,
#         media_type="application/pdf",
#         filename=pdf_file.name,
#         headers={"Content-Disposition": f"attachment; filename={pdf_file.name}"}
#     )


# @router.get("/artifact/{artifact_id}")
# async def get_artifact_details(artifact_id: UUID, db: Session = Depends(get_db)):
#     artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
#     if not artifact:
#         raise HTTPException(status_code=404, detail="Artefact non trouvé.")

#     versions = db.query(DocVersion).filter(DocVersion.artifact_id == artifact.id).order_by(DocVersion.version_no.desc()).all()

#     version_list = []
#     for v in versions:
#         version_list.append({
#             "id": str(v.id),
#             "version_no": v.version_no,
#             "version_label": v.version_label,
#             "created_at": v.created_at.isoformat() if v.created_at else None,
#             "global_kpi_score": v.global_kpi_score
#         })

#     artifact_name = Path(to_posix_str(artifact.source_path)).stem

#     return {
#         "id": str(artifact.id),
#         "name": artifact_name,
#         "projectName": artifact.project.name if artifact.project else "Default Project",
#         "source_path": to_posix_str(artifact.source_path),
#         "versions": version_list
#     }


# @router.get("/diagnose-path")
# async def diagnose_path(file_path: str = "", project_name: str = ""):
#     import os
#     import sys as _sys
#     results = []
    
#     try:
#         p = Path(file_path)
#         results.append({"step": "Path(file_path)", "ok": True, "value": str(p)})
#     except Exception as e:
#         results.append({"step": "Path(file_path)", "ok": False, "error": str(e)})
    
#     try:
#         r = p.resolve()
#         results.append({"step": "resolve()", "ok": True, "value": str(r)})
#     except Exception as e:
#         results.append({"step": "resolve()", "ok": False, "error": str(e)})
    
#     try:
#         posix = r.as_posix()
#         results.append({"step": "as_posix()", "ok": True, "value": posix})
#     except Exception as e:
#         results.append({"step": "as_posix()", "ok": False, "error": str(e)})
    
#     from app.utils.path_builder import sanitize_path_string
#     try:
#         clean = sanitize_path_string(file_path)
#         results.append({"step": "sanitize_path_string()", "ok": True, "value": clean})
#     except Exception as e:
#         results.append({"step": "sanitize_path_string()", "ok": False, "error": str(e)})
    
#     from app.utils.path_builder import extract_project_name_from_path
#     try:
#         pn = extract_project_name_from_path(Path(file_path))
#         results.append({"step": "extract_project_name_from_path()", "ok": True, "value": pn})
#     except Exception as e:
#         results.append({"step": "extract_project_name_from_path()", "ok": False, "error": str(e)})
    
#     from app.utils.path_builder import build_pipeline_paths
#     try:
#         paths = build_pipeline_paths(file_name=file_path, project_name=project_name or pn)
#         results.append({"step": "build_pipeline_paths() mkdir", "ok": True, "dirs_created": str(paths.get("base_output_dir"))})
#     except Exception as e:
#         results.append({"step": "build_pipeline_paths() mkdir", "ok": False, "error": str(e)})
    
#     try:
#         tmp_dir = Path("specs") / (project_name or "test_diag")
#         tmp_dir.mkdir(parents=True, exist_ok=True)
#         tmp_file = tmp_dir / "_diag_test_.tmp"
#         tmp_file.write_bytes(b"test")
#         results.append({"step": "write_bytes()", "ok": True, "path": str(tmp_file)})
#         tmp_file.unlink()
#     except Exception as e:
#         results.append({"step": "write_bytes()", "ok": False, "error": str(e)})
    
#     results.append({"step": "CWD", "value": os.getcwd()})
#     from app.utils.path_builder import BASE_DIR
#     results.append({"step": "path_builder.BASE_DIR", "value": str(BASE_DIR)})
#     results.append({"step": "sys.path[0]", "value": _sys.path[0] if _sys.path else "empty"})
    
#     return {"project_name": project_name, "file_path": file_path, "cwd": os.getcwd(), "tests": results}


# @router.get("/check-file")
# async def check_file_status(
#     file_path: str,
#     project_name: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """
#     Vérification stricte en LECTURE SEULE.
#     Ne crée AUCUN enregistrement en base de données si le fichier n'a pas été traité.
#     """
#     clean_path_str = to_posix_str(sanitize_path_string(file_path))
#     file_path_obj = Path(clean_path_str)
    
#     if not file_path_obj.exists():
#         return {"exists_in_db": False}

#     p_name = get_effective_project_name(file_path_obj, project_name)
    
#     # Appel de la fonction de lecture seule
#     exists = check_file_exists_only(db, file_path_obj, p_name)

#     return {"exists_in_db": bool(exists)}
