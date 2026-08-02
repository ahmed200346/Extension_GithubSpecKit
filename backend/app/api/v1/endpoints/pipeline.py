import json
import hashlib
import traceback
import urllib.parse
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
from app.models import Project, Artifact, DocVersion, PipelineRun, ArtifactType, PipelineStage, GeneratedBy
from app.services.db_service import (
    should_process_file,
    create_pipeline_run,
    get_next_version,
    save_successful_run,
    save_failed_run,
)
from app.utils.path_builder import build_pipeline_paths, extract_project_name_from_path, sanitize_path_string, BASE_DIR
from app.graph.workflow import create_pipeline_workflow

router = APIRouter()
app_graph = create_pipeline_workflow()

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
                    "agentEvaluations": agent_evaluations
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
                "agentEvaluations": agent_evaluations
            })

    return result


@router.post("/upload")
async def upload_and_process_document(
    file: UploadFile = File(...),
    projectName: str = Form(...),
    db: Session = Depends(get_db)
):
    global PIPELINE_STATUS

    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .md sont acceptés.")

    # 🛡️ Décoder l'URL encoding (ex: + -> espace, %20 -> espace) AVANT sanitize
    raw_project = projectName.strip() if projectName and projectName.strip() else "Default Project"
    decoded_project = urllib.parse.unquote(raw_project.replace("+", " "))
    project_clean = sanitize_path_string(decoded_project)
    file.filename = sanitize_path_string(file.filename)
    
    # Créer le répertoire cible sous <RACINE>/specs/<projectName>/ (pas backend/specs)
    dest_dir = BASE_DIR / "specs" / project_clean
    dest_dir.mkdir(parents=True, exist_ok=True)

    file_path = dest_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    # 🛡️ Conversion POSIX avant passage à should_process_file()
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

    # Créer la DocVersion en status "pending" dès le début pour affichage immédiat dans le frontend
    _, next_version_label = get_next_version(db, artifact.id)
    next_version_no, _ = get_next_version(db, artifact.id)
    doc_version = DocVersion(
        artifact_id=artifact.id,
        version_no=next_version_no,
        version_label=next_version_label,
        pdf_path="",
        source_file_hash=new_hash,
        generated_at=datetime.now(timezone.utc),
        generated_by=GeneratedBy.agent,
        pipeline_run_id=pipeline_run.id,
        global_kpi_score=None,
    )
    db.add(doc_version)
    db.commit()
    db.refresh(doc_version)

    try:
        
        # ============ ÉTAPE 3 : GÉNÉRATION DES CHEMINS DE LA PIPELINE ============
        # 🛡️ Passage du chemin en format POSIX à build_pipeline_paths()
        paths = build_pipeline_paths(
            file_name=to_posix_str(file_path_posix),
            version_label=next_version_label,
            project_name=project_clean
        )

        # Préparation de l'état initial pour LangGraph
        # 🎯 content est décodé de bytes vers str
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

        # ============ ÉTAPE 4 : EXÉCUTION DU WORKFLOW LANGGRAPH ============
        final_state = await app_graph.ainvoke(initial_state)

        # ============ ÉTAPE 5 : CHARGEMENT DES ÉVALUATIONS ============
        evaluations = {
            "parsing": load_json_if_exists(paths.get("parsing_eval")),
            "summary": load_json_if_exists(paths.get("summary_eval")),
            "glossary": load_json_if_exists(paths.get("glossary_eval")),
            "diagram": load_json_if_exists(paths.get("diagram_eval")),
            "writer": load_json_if_exists(paths.get("doc_eval")),
            "layout": load_json_if_exists(paths.get("layout_eval")),
        }

        global_kpi = calculate_global_kpi(evaluations)

        # ============ ÉTAPE 6 : SAUVEGARDE DES RÉSULTATS EN BDD ============
        # 🛡️ UTILISER LE CHEMIN EXACT RETOURNÉ PAR LE LAYOUT NODE (garantit cohérence)
        layout_pdf_path = final_state.get("layout_pdf_path")
        if layout_pdf_path:
            final_pdf_path = to_posix_str(layout_pdf_path)
        else:
            final_pdf_path = to_posix_str(paths.get("final_pdf"))

        doc_version = save_successful_run(
            db=db,
            artifact=artifact,
            pipeline_run=pipeline_run,
            new_hash=new_hash,
            pdf_path=final_pdf_path,
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
        # Forcer l'ecriture du traceback sur stderr (visible dans le canal Server)
        import sys as _sys
        _sys.stderr.write(f"❌ [PIPELINE] Erreur lors du traitement : {tb_str}\n")
        _sys.stderr.flush()
        # Aussi ecrire dans un fichier de diagnostic
        _diag_log = Path("pipeline_error_traceback.log")
        _diag_log.write_text(tb_str, encoding="utf-8")
        print(f"❌ [PIPELINE] Traceback ecrit dans: {_diag_log.resolve()}", flush=True)
        raise HTTPException(status_code=500, detail=f"Erreur Pipeline: {str(e)}\n{tb_str}")
    
    finally:
        PIPELINE_STATUS["is_running"] = False
        PIPELINE_STATUS["current_file"] = None


@router.get("/pdf/{doc_version_id}")
async def view_pdf(doc_version_id: UUID, db: Session = Depends(get_db)):
    """
    📄 Sert le fichier PDF pour le lecteur intégré.
    
    ✅ CORRECTION : Conversion POSIX du chemin PDF avant accès disque
    """
    doc_ver = db.query(DocVersion).filter(DocVersion.id == doc_version_id).first()
    if not doc_ver or not doc_ver.pdf_path:
        raise HTTPException(status_code=404, detail="PDF non trouvé.")

    # 🛡️ Conversion POSIX stricte avant opération d'E/S
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
    """
    ⬇️ Télécharge le fichier PDF généré.
    
    ✅ CORRECTION : Conversion POSIX du chemin avant accès disque
    """
    doc_ver = db.query(DocVersion).filter(DocVersion.id == doc_version_id).first()
    if not doc_ver or not doc_ver.pdf_path:
        raise HTTPException(status_code=404, detail="PDF non trouvé.")

    # 🛡️ Conversion POSIX stricte
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
    """
    🏷️ Retourne les détails complets d'un artefact et toutes ses versions.
    
    ✅ CORRECTION : Conversion POSIX de tous les chemins source_path
    """
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

    # 🛡️ Conversion POSIX du source_path
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
    """
    Diagnostique les operations de chemin qui causent [Errno 22].
    Teste chaque etape une par une et retourne le detail.
    """
    import os
    import sys as _sys
    results = []
    
    # Etape 1: tester Path()
    try:
        p = Path(file_path)
        results.append({"step": "Path(file_path)", "ok": True, "value": str(p)})
    except Exception as e:
        results.append({"step": "Path(file_path)", "ok": False, "error": str(e)})
    
    # Etape 2: tester resolve()
    try:
        r = p.resolve()
        results.append({"step": "resolve()", "ok": True, "value": str(r)})
    except Exception as e:
        results.append({"step": "resolve()", "ok": False, "error": str(e)})
    
    # Etape 3: tester as_posix()
    try:
        posix = r.as_posix()
        results.append({"step": "as_posix()", "ok": True, "value": posix})
    except Exception as e:
        results.append({"step": "as_posix()", "ok": False, "error": str(e)})
    
    # Etape 4: tester sanitize_path_string
    from app.utils.path_builder import sanitize_path_string
    try:
        clean = sanitize_path_string(file_path)
        results.append({"step": "sanitize_path_string()", "ok": True, "value": clean})
    except Exception as e:
        results.append({"step": "sanitize_path_string()", "ok": False, "error": str(e)})
    
    # Etape 5: tester extract_project_name_from_path
    from app.utils.path_builder import extract_project_name_from_path
    try:
        pn = extract_project_name_from_path(Path(file_path))
        results.append({"step": "extract_project_name_from_path()", "ok": True, "value": pn})
    except Exception as e:
        results.append({"step": "extract_project_name_from_path()", "ok": False, "error": str(e)})
    
    # Etape 6: tester build_pipeline_paths
    from app.utils.path_builder import build_pipeline_paths
    try:
        paths = build_pipeline_paths(file_name=file_path, project_name=project_name or pn)
        results.append({"step": "build_pipeline_paths() mkdir", "ok": True, "dirs_created": str(paths.get("base_output_dir"))})
    except Exception as e:
        results.append({"step": "build_pipeline_paths() mkdir", "ok": False, "error": str(e)})
    
    # Etape 7: tester write_bytes vers un fichier temporaire
    try:
        tmp_dir = Path("specs") / (project_name or "test_diag")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = tmp_dir / "_diag_test_.tmp"
        tmp_file.write_bytes(b"test")
        results.append({"step": "write_bytes()", "ok": True, "path": str(tmp_file)})
        tmp_file.unlink()
    except Exception as e:
        results.append({"step": "write_bytes()", "ok": False, "error": str(e)})
    
    # Etape 8: afficher CWD et BASE_DIR
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
    Verifie si le fichier existe deja en BDD et si son hash n'a pas change.
    """
    # Nettoyage immediat des parametres HTTP pour supprimer antislashs et caracteres de controle
    clean_path_str = to_posix_str(sanitize_path_string(file_path))
    file_path_obj = Path(clean_path_str)
    
    if not file_path_obj.exists():
        return {"exists_in_db": False}

    # Extraction du nom du projet (nettoyage du parametre HTTP)
    clean_project = sanitize_path_string(project_name) if project_name else None
    p_name = clean_project or extract_project_name_from_path(file_path_obj)
    
    # Verification en BDD (lecture seule, ne cree pas d'artifact)
    exists = should_process_file(db, file_path_obj, p_name)

    return {"exists_in_db": exists}