import json
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import de la session DB
from app.database import get_db

# Imports des services BDD
from app.services.db_service import (
    should_process_file,
    create_pipeline_run,
    get_next_version,
    save_successful_run,
    save_failed_run,
)

from app.utils.path_builder import build_pipeline_paths, extract_project_name_from_path
from app.graph.workflow import create_pipeline_workflow

router = APIRouter()
app_graph = create_pipeline_workflow()

# 🎯 État global du serveur (protection contre la concurrence)
PIPELINE_STATUS = {
    "is_running": False,
    "current_file": None
}


class PipelineRequest(BaseModel):
    file_path: str
    project_name: Optional[str] = None


def load_json_if_exists(file_path: Optional[Path]) -> Optional[Dict[str, Any]]:
    """Utilitaire pour charger un fichier JSON d'évaluation s'il existe sur le disque."""
    if file_path and file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def calculate_global_kpi(evaluations: Dict[str, Optional[Dict[str, Any]]]) -> float:
    """
    Calcule le KPI Global moyen à partir des vrais JSON d'évaluation des agents.
    Extrait automatiquement les scores et taux (ex: _score, _rate, health_index, etc.).
    """
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

    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 1)


@router.get("/status")
async def get_pipeline_status():
    """Endpoint consulté par le Watcher et la CLI pour vérifier la disponibilité."""
    return PIPELINE_STATUS


# 🆕 ROUTE POUR LE SCAN INITIAL DU WATCHER
@router.get("/check-file")
async def check_file_status(
    file_path: str,
    project_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Interrogé par initial_scan() dans spec_watcher.py.
    Vérifie si le fichier est déjà enregistré en BDD ET avec un contenu identique (Hash SHA-256).
    """
    file_path_obj = Path(file_path)
    
    # Si le fichier n'existe pas physiquement
    if not file_path_obj.exists():
        return {"exists_in_db": False}

    p_name = project_name or extract_project_name_from_path(file_path_obj)

    # Réutilisation directe de votre service db_service
    # should_run = True si le fichier est NOUVEAU ou SI SON CONTENU A CHANGÉ
    should_run, _, _ = should_process_file(db, file_path_obj, p_name)

    # Si should_run est False, le fichier est DÉJÀ en BDD et À JOUR => exists_in_db = True
    return {"exists_in_db": not should_run}


@router.post("/run")
async def run_pipeline(
    request: PipelineRequest, 
    db: Session = Depends(get_db)
):
    """Exécute le pipeline, évalue les 6 agents et sauvegarde le résultat en BDD."""
    global PIPELINE_STATUS

    # 1. Protection contre les exécutions concurrentes
    if PIPELINE_STATUS["is_running"]:
        raise HTTPException(
            status_code=429,
            detail=f"Pipeline déjà en cours d'exécution sur : {PIPELINE_STATUS['current_file']}"
        )

    file_path_obj = Path(request.file_path)
    if not file_path_obj.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Fichier introuvable sur le disque : {request.file_path}"
        )

    # Extraire dynamiquement le vrai dossier projet mère sous specs/
    project_name = request.project_name or extract_project_name_from_path(file_path_obj)

    # 2. Vérification DB : le fichier a-t-il changé ? (Hash SHA-256)
    should_run, new_hash, artifact = should_process_file(db, file_path_obj, project_name)
    if not should_run:
        return {
            "status": "skipped",
            "message": "Aucun changement détecté dans le fichier (Hash identique). Exécution ignorée.",
            "artifact_id": str(artifact.id)
        }

    # 3. Verrouillage du serveur et création du PipelineRun en BDD
    PIPELINE_STATUS["is_running"] = True
    PIPELINE_STATUS["current_file"] = request.file_path

    pipeline_run = create_pipeline_run(db, artifact.id)

    try:
        # 🎯 CALCUL AUTOMATIQUE DE LA PROCHAINE VERSION (v1.0, v2.0, ...)
        _, next_version_label = get_next_version(db, artifact.id)

        # 🎯 UTILISATION DE LA NOUVELLE STRUCTURE PAR PROJET
        paths = build_pipeline_paths(
            file_name=request.file_path, 
            version_label=next_version_label, 
            project_name=project_name
        )
        file_content = file_path_obj.read_text(encoding="utf-8")

        initial_state = {
            "file_name": request.file_path,
            "file_content": file_content,
            "version_label": next_version_label,
            "run_id": pipeline_run.id,
            "prefix": paths["prefix"]
        }

        # 4. Lancement du workflow LangGraph
        final_state = await app_graph.ainvoke(initial_state)

        # 5. Chargement des JSON d'évaluation des 6 Agents pour le Frontend
        evaluations = {
            "parsing": load_json_if_exists(paths.get("parsing_eval")),
            "summary": load_json_if_exists(paths.get("summary_eval")),
            "glossary": load_json_if_exists(paths.get("glossary_eval")),
            "diagram": load_json_if_exists(paths.get("diagram_eval")),
            "writer": load_json_if_exists(paths.get("doc_eval")),
            "layout": load_json_if_exists(paths.get("layout_eval")),
        }

        # Calcul du score KPI Global
        global_kpi = calculate_global_kpi(evaluations)

        # 6. Enregistrement des résultats et évals dans la base de données
        doc_version = save_successful_run(
            db=db,
            artifact=artifact,
            pipeline_run=pipeline_run,
            new_hash=new_hash,
            pdf_path=str(paths["final_pdf"]),
            # Sorties brutes
            structured_json=final_state.get("parsed_json_dict"),
            summary_output=str(final_state.get("summary_doc")) if final_state.get("summary_doc") else None,
            diagram_output=final_state.get("diagram_doc").model_dump() if hasattr(final_state.get("diagram_doc"), "model_dump") else final_state.get("diagram_doc"),
            glossary_output=final_state.get("glossary_doc").model_dump() if hasattr(final_state.get("glossary_doc"), "model_dump") else final_state.get("glossary_doc"),
            written_doc=final_state.get("doc_writer_doc").markdown_content if hasattr(final_state.get("doc_writer_doc"), "markdown_content") else None,
            layout_output=str(final_state.get("layout_doc")) if final_state.get("layout_doc") else None,
            # Évaluations JSON pour le Pop-up Frontend
            parsing_eval=evaluations["parsing"],
            summary_eval=evaluations["summary"],
            glossary_eval=evaluations["glossary"],
            diagram_eval=evaluations["diagram"],
            writer_eval=evaluations["writer"],
            layout_eval=evaluations["layout"],
            # KPI Global pour le tableau principal
            global_kpi_score=global_kpi
        )

        return {
            "status": "success",
            "version_no": doc_version.version_no,
            "version_label": doc_version.version_label,
            "global_kpi_score": global_kpi,
            "pdf_path": str(paths["final_pdf"]),
            "data": final_state
        }

    except Exception as e:
        save_failed_run(db, pipeline_run, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'exécution du pipeline : {str(e)}"
        )

    finally:
        # 7. Libération du serveur
        PIPELINE_STATUS["is_running"] = False
        PIPELINE_STATUS["current_file"] = None
# import json
# from pathlib import Path
# from typing import Optional, Dict, Any

# from fastapi import APIRouter, HTTPException, Depends, status
# from pydantic import BaseModel
# from sqlalchemy.orm import Session

# # Import de la session DB
# from app.database import get_db

# # Imports des services BDD
# from app.services.db_service import (
#     should_process_file,
#     create_pipeline_run,
#     get_next_version,
#     save_successful_run,
#     save_failed_run,
# )

# from app.utils.path_builder import build_pipeline_paths
# from app.graph.workflow import create_pipeline_workflow

# router = APIRouter()
# app_graph = create_pipeline_workflow()

# # 🎯 État global du serveur (protection contre la concurrence)
# PIPELINE_STATUS = {
#     "is_running": False,
#     "current_file": None
# }


# class PipelineRequest(BaseModel):
#     file_path: str
#     project_name: Optional[str] = None


# def load_json_if_exists(file_path: Optional[Path]) -> Optional[Dict[str, Any]]:
#     """Utilitaire pour charger un fichier JSON d'évaluation s'il existe sur le disque."""
#     if file_path and file_path.exists():
#         try:
#             return json.loads(file_path.read_text(encoding="utf-8"))
#         except Exception:
#             return None
#     return None


# def calculate_global_kpi(evaluations: Dict[str, Optional[Dict[str, Any]]]) -> float:
#     """
#     Calcule le KPI Global moyen à partir des vrais JSON d'évaluation des agents.
#     Extrait automatiquement les scores et taux (ex: _score, _rate, health_index, etc.).
#     """
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

#     if not scores:
#         return 0.0

#     return round(sum(scores) / len(scores), 1)


# @router.get("/status")
# async def get_pipeline_status():
#     """Endpoint consulté par le Watcher et la CLI pour vérifier la disponibilité."""
#     return PIPELINE_STATUS


# # 🆕 ROUTE POUR LE SCAN INITIAL DU WATCHER
# @router.get("/check-file")
# async def check_file_status(
#     file_path: str,
#     project_name: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """
#     Interrogé par initial_scan() dans spec_watcher.py.
#     Vérifie si le fichier est déjà enregistré en BDD ET avec un contenu identique (Hash SHA-256).
#     """
#     file_path_obj = Path(file_path)
    
#     # Si le fichier n'existe pas physiquement
#     if not file_path_obj.exists():
#         return {"exists_in_db": False}

#     p_name = project_name or file_path_obj.parent.name or "Default Project"

#     # Réutilisation directe de votre service db_service
#     # should_run = True si le fichier est NOUVEAU ou SI SON CONTENU A CHANGÉ
#     should_run, _, _ = should_process_file(db, file_path_obj, p_name)

#     # Si should_run est False, le fichier est DÉJÀ en BDD et À JOUR => exists_in_db = True
#     return {"exists_in_db": not should_run}


# @router.post("/run")
# async def run_pipeline(
#     request: PipelineRequest, 
#     db: Session = Depends(get_db)
# ):
#     """Exécute le pipeline, évalue les 6 agents et sauvegarde le résultat en BDD."""
#     global PIPELINE_STATUS

#     # 1. Protection contre les exécutions concurrentes
#     if PIPELINE_STATUS["is_running"]:
#         raise HTTPException(
#             status_code=429,
#             detail=f"Pipeline déjà en cours d'exécution sur : {PIPELINE_STATUS['current_file']}"
#         )

#     file_path_obj = Path(request.file_path)
#     if not file_path_obj.exists():
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, 
#             detail=f"Fichier introuvable sur le disque : {request.file_path}"
#         )

#     project_name = request.project_name or file_path_obj.parent.name or "Default Project"

#     # 2. Vérification DB : le fichier a-t-il changé ? (Hash SHA-256)
#     should_run, new_hash, artifact = should_process_file(db, file_path_obj, project_name)
#     if not should_run:
#         return {
#             "status": "skipped",
#             "message": "Aucun changement détecté dans le fichier (Hash identique). Exécution ignorée.",
#             "artifact_id": str(artifact.id)
#         }

#     # 3. Verrouillage du serveur et création du PipelineRun en BDD
#     PIPELINE_STATUS["is_running"] = True
#     PIPELINE_STATUS["current_file"] = request.file_path

#     pipeline_run = create_pipeline_run(db, artifact.id)

#     try:
#         # 🎯 CALCUL AUTOMATIQUE DE LA PROCHAINE VERSION (v1.0, v2.0, ...)
#         _, next_version_label = get_next_version(db, artifact.id)

#         # 🎯 UTILISATION DE LA NOUVELLE STRUCTURE PAR PROJET
#         paths = build_pipeline_paths(
#             file_name=request.file_path, 
#             version_label=next_version_label, 
#             project_name=project_name
#         )
#         file_content = file_path_obj.read_text(encoding="utf-8")

#         initial_state = {
#             "file_name": request.file_path,
#             "file_content": file_content,
#             "version_label": next_version_label,
#             "run_id": pipeline_run.id,
#             "prefix": paths["prefix"]
#         }

#         # 4. Lancement du workflow LangGraph
#         final_state = await app_graph.ainvoke(initial_state)

#         # 5. Chargement des JSON d'évaluation des 6 Agents pour le Frontend
#         evaluations = {
#             "parsing": load_json_if_exists(paths.get("parsing_eval")),
#             "summary": load_json_if_exists(paths.get("summary_eval")),
#             "glossary": load_json_if_exists(paths.get("glossary_eval")),
#             "diagram": load_json_if_exists(paths.get("diagram_eval")),
#             "writer": load_json_if_exists(paths.get("doc_eval")),
#             "layout": load_json_if_exists(paths.get("layout_eval")),
#         }

#         # Calcul du score KPI Global
#         global_kpi = calculate_global_kpi(evaluations)

#         # 6. Enregistrement des résultats et évals dans la base de données
#         doc_version = save_successful_run(
#             db=db,
#             artifact=artifact,
#             pipeline_run=pipeline_run,
#             new_hash=new_hash,
#             pdf_path=str(paths["final_pdf"]),
#             # Sorties brutes
#             structured_json=final_state.get("parsed_json_dict"),
#             summary_output=str(final_state.get("summary_doc")) if final_state.get("summary_doc") else None,
#             diagram_output=final_state.get("diagram_doc").model_dump() if hasattr(final_state.get("diagram_doc"), "model_dump") else final_state.get("diagram_doc"),
#             glossary_output=final_state.get("glossary_doc").model_dump() if hasattr(final_state.get("glossary_doc"), "model_dump") else final_state.get("glossary_doc"),
#             written_doc=final_state.get("doc_writer_doc").markdown_content if hasattr(final_state.get("doc_writer_doc"), "markdown_content") else None,
#             layout_output=str(final_state.get("layout_doc")) if final_state.get("layout_doc") else None,
#             # Évaluations JSON pour le Pop-up Frontend
#             parsing_eval=evaluations["parsing"],
#             summary_eval=evaluations["summary"],
#             glossary_eval=evaluations["glossary"],
#             diagram_eval=evaluations["diagram"],
#             writer_eval=evaluations["writer"],
#             layout_eval=evaluations["layout"],
#             # KPI Global pour le tableau principal
#             global_kpi_score=global_kpi
#         )

#         return {
#             "status": "success",
#             "version_no": doc_version.version_no,
#             "version_label": doc_version.version_label,
#             "global_kpi_score": global_kpi,
#             "pdf_path": str(paths["final_pdf"]),
#             "data": final_state
#         }

#     except Exception as e:
#         save_failed_run(db, pipeline_run, str(e))
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Erreur lors de l'exécution du pipeline : {str(e)}"
#         )

#     finally:
#         # 7. Libération du serveur
#         PIPELINE_STATUS["is_running"] = False
#         PIPELINE_STATUS["current_file"] = None
