import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session

from app.models import (
    Project,
    Artifact,
    DocVersion,
    PipelineRun,
    ArtifactType,
    PipelineStage,
    GeneratedBy,
)


def compute_sha256(file_path: Path) -> str:
    """Calcule l'empreinte SHA-256 du contenu d'un fichier Markdown."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def detect_artifact_type(file_path: Path) -> ArtifactType:
    """Détermine dynamiquement le type d'artefact."""
    name = file_path.name.lower()

    if "constitution" in name:
        return ArtifactType.constitution
    elif "requirement" in name:
        return ArtifactType.requirements
    elif "contract" in name:
        return ArtifactType.contracts
    elif "data-model" in name or "data_model" in name:
        return ArtifactType.data_model
    elif "research" in name:
        return ArtifactType.research
    elif "quickstart" in name:
        return ArtifactType.quickstart
    elif "plan" in name:
        return ArtifactType.plan
    elif "task" in name:
        return ArtifactType.task

    return ArtifactType.spec


def compute_global_kpi_score(eval_dicts: List[Optional[Dict[str, Any]]]) -> Optional[float]:
    """
    Calcule de manière sécurisée la moyenne globale des KPI techniques 
    à partir des évaluations JSON disponibles.
    Gère l'absence de clés (KeyError) et les étapes omises (ex: constitution ou spec minimale).
    """
    extracted_scores = []

    for eval_dict in eval_dicts:
        if not eval_dict or not isinstance(eval_dict, dict):
            continue

        # Extraction sécurisée du bloc technical_evaluation
        tech_eval = eval_dict.get("technical_evaluation", {})
        if not isinstance(tech_eval, dict):
            tech_eval = {}

        # Combinaison pour inspecter toutes les métriques sans crash
        metrics_source = {**eval_dict, **tech_eval}

        for key, val in metrics_source.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                key_lower = key.lower()
                # Exclure les compteurs d'éléments, tailles de fichiers et statistiques d'octets
                if any(ignored in key_lower for ignored in ["count", "kb", "size", "total", "lines", "word", "errors"]):
                    continue
                # Conserver uniquement les scores et taux exprimés en pourcentage ou index
                if any(indicator in key_lower for indicator in ["score", "rate", "integrity", "conformity", "index", "adherence"]):
                    extracted_scores.append(float(val))

    if not extracted_scores:
        return None

    return round(sum(extracted_scores) / len(extracted_scores), 1)


def get_or_create_project(
    db: Session, project_name: str, repo_url: Optional[str] = None
) -> Project:
    """Récupère un projet existant ou le crée en BDD."""
    project = db.query(Project).filter(Project.name == project_name).first()
    if not project:
        project = Project(name=project_name, repo_url=repo_url)
        db.add(project)
        db.commit()
        db.refresh(project)
    return project


def check_file_exists_only(
    db: Session, file_path: Path, project_name: str
) -> bool:
    """
    Lecture seule : verifie si la VERSION EXACTE (par SHA-256) d'un fichier 
    a DEJA ETE TRAITEE AVEC SUCCES en BDD.
    Permet la détection automatique de v2, v3... vn lors des modifications de fichier.
    """
    from app.utils.path_builder import sanitize_path_string
    file_path_str = sanitize_path_string(file_path.resolve().as_posix())
    new_hash = compute_sha256(file_path)
    project = get_or_create_project(db, project_name)

    artifact = (
        db.query(Artifact)
        .filter(Artifact.project_id == project.id, Artifact.source_path == file_path_str)
        .first()
    )
    if not artifact:
        return False

    # Si le hash du fichier sur disque diffère du hash courant, il s'agit d'une nouvelle version à traiter
    if artifact.current_file_hash != new_hash:
        return False

    completed_run = (
        db.query(PipelineRun)
        .filter(
            PipelineRun.artifact_id == artifact.id, 
            PipelineRun.current_stage == PipelineStage.completed
        )
        .first()
    )
    return completed_run is not None


def should_process_file(
    db: Session, file_path: Path, project_name: str
) -> Tuple[bool, str, Artifact]:
    """Verifie si le fichier doit etre traite (nouveau hash OU dernier pipeline non termine)."""
    from app.utils.path_builder import sanitize_path_string
    file_path_str = sanitize_path_string(file_path.resolve().as_posix())
    new_hash = compute_sha256(file_path)

    project = get_or_create_project(db, project_name)

    artifact = (
        db.query(Artifact)
        .filter(Artifact.project_id == project.id, Artifact.source_path == file_path_str)
        .first()
    )

    if not artifact:
        existing = (
            db.query(Artifact)
            .filter(Artifact.project_id == project.id, Artifact.current_file_hash == new_hash)
            .first()
        )
        if existing:
            existing.source_path = file_path_str
            db.commit()
            db.refresh(existing)
            artifact = existing
        else:
            artifact = Artifact(
                project_id=project.id,
                source_path=file_path_str,
                current_file_hash=new_hash,
                artifact_type=detect_artifact_type(file_path),
            )
            db.add(artifact)
            db.commit()
            db.refresh(artifact)
            return True, new_hash, artifact

    latest_run = (
        db.query(PipelineRun)
        .filter(PipelineRun.artifact_id == artifact.id)
        .order_by(PipelineRun.started_at.desc())
        .first()
    )

    if (
        artifact.current_file_hash == new_hash 
        and latest_run 
        and latest_run.current_stage == PipelineStage.completed
    ):
        return False, new_hash, artifact

    return True, new_hash, artifact


def create_pipeline_run(db: Session, artifact_id: uuid.UUID) -> PipelineRun:
    """Initialise une exécution de pipeline en BDD à l'étape 'parsing'."""
    run = PipelineRun(artifact_id=artifact_id, current_stage=PipelineStage.parsing)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_next_version(db: Session, artifact_id: uuid.UUID) -> Tuple[int, str]:
    """
    Calcule le numéro et le label de la prochaine version.
    - Si 1er passage : (1, "1.0")
    - Si modification : (2, "2.0"), (3, "3.0"), etc.
    """
    last_version = (
        db.query(DocVersion)
        .filter(DocVersion.artifact_id == artifact_id)
        .order_by(DocVersion.version_no.desc())
        .first()
    )

    if not last_version:
        return 1, "1.0"

    next_no = last_version.version_no + 1
    next_label = f"{next_no}.0"
    return next_no, next_label


def update_pipeline_stage_data(
    db: Session,
    run_id: uuid.UUID,
    stage: PipelineStage,
    output_attr: Optional[str] = None,
    output_data: Optional[Any] = None,
    eval_attr: Optional[str] = None,
    eval_data: Optional[Dict[str, Any]] = None,
):
    """Met à jour le statut courant, le rendu intermédiaire et l'évaluation JSON dans PostgreSQL."""
    try:
        run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if not run:
            return

        run.current_stage = stage

        if output_attr and output_data is not None and hasattr(run, output_attr):
            setattr(run, output_attr, output_data)

        if eval_attr and eval_data is not None and hasattr(run, eval_attr):
            setattr(run, eval_attr, eval_data)

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[⚠️ DB Update Error] Échec de la mise à jour pour le stage {stage.value}: {exc}")


def create_doc_version_pending(
    db: Session,
    artifact: Artifact,
    pipeline_run: PipelineRun,
    version_label: str,
    version_no: int,
) -> DocVersion:
    """Crée une DocVersion en status 'pending' au début du pipeline pour affichage immédiat."""
    doc_version = DocVersion(
        artifact_id=artifact.id,
        version_no=version_no,
        version_label=version_label,
        pdf_path="",
        source_file_hash=artifact.current_file_hash or "",
        generated_at=datetime.now(timezone.utc),
        generated_by=GeneratedBy.agent,
        pipeline_run_id=pipeline_run.id,
        global_kpi_score=None,
    )
    db.add(doc_version)
    db.commit()
    db.refresh(doc_version)
    return doc_version


def save_successful_run(
    db: Session,
    artifact: Artifact,
    pipeline_run: PipelineRun,
    new_hash: str,
    pdf_path: str,
    doc_version: Optional[DocVersion] = None,
    # --- Outputs ---
    structured_json: Optional[Dict[str, Any]] = None,
    summary_output: Optional[str] = None,
    diagram_output: Optional[Dict[str, Any]] = None,
    glossary_output: Optional[Dict[str, Any]] = None,
    written_doc: Optional[str] = None,
    layout_output: Optional[str] = None,
    # --- Évaluations JSON ---
    parsing_eval: Optional[Dict[str, Any]] = None,
    summary_eval: Optional[Dict[str, Any]] = None,
    glossary_eval: Optional[Dict[str, Any]] = None,
    diagram_eval: Optional[Dict[str, Any]] = None,
    writer_eval: Optional[Dict[str, Any]] = None,
    layout_eval: Optional[Dict[str, Any]] = None,
    # --- Score KPI ---
    global_kpi_score: Optional[float] = None,
    commit_hash: Optional[str] = None,
) -> DocVersion:
    """Marque le PipelineRun comme terminé et génère la DocVersion avec son numéro v1.0, v2.0..."""
    pipeline_run.current_stage = PipelineStage.completed
    pipeline_run.completed_at = datetime.now(timezone.utc)

    if structured_json: pipeline_run.structured_json = structured_json
    if summary_output: pipeline_run.summary_output = summary_output
    if diagram_output: pipeline_run.diagram_output = diagram_output
    if glossary_output: pipeline_run.glossary_output = glossary_output
    if written_doc: pipeline_run.written_doc = written_doc
    if layout_output: pipeline_run.layout_output = layout_output

    if parsing_eval: pipeline_run.parsing_eval = parsing_eval
    if summary_eval: pipeline_run.summary_eval = summary_eval
    if glossary_eval: pipeline_run.glossary_eval = glossary_eval
    if diagram_eval: pipeline_run.diagram_eval = diagram_eval
    if writer_eval: pipeline_run.writer_eval = writer_eval
    if layout_eval: pipeline_run.layout_eval = layout_eval

    # 🎯 Calcul/Secours automatique du KPI global s'il est None ou égal à 0.0
    if not global_kpi_score or global_kpi_score == 0.0:
        computed_score = compute_global_kpi_score([
            parsing_eval,
            summary_eval,
            glossary_eval,
            diagram_eval,
            writer_eval,
            layout_eval,
        ])
        if computed_score is not None:
            global_kpi_score = computed_score

    pipeline_run.global_kpi_score = global_kpi_score

    # Récupérer la DocVersion existante
    if not doc_version:
        doc_version = (
            db.query(DocVersion)
            .filter(DocVersion.pipeline_run_id == pipeline_run.id)
            .first()
        )

    if not doc_version:
        # Fallback : créer si n'existe pas
        next_version_no, next_version_label = get_next_version(db, artifact.id)
        doc_version = DocVersion(
            artifact_id=artifact.id,
            version_no=next_version_no,
            version_label=next_version_label,
            pdf_path=pdf_path,
            source_file_hash=new_hash,
            generated_by=GeneratedBy.agent,
            pipeline_run_id=pipeline_run.id,
            global_kpi_score=global_kpi_score,
            commit_hash=commit_hash,
        )
        db.add(doc_version)
    else:
        # Mettre à jour la DocVersion existante
        doc_version.pdf_path = pdf_path
        doc_version.source_file_hash = new_hash
        doc_version.global_kpi_score = global_kpi_score
        doc_version.commit_hash = commit_hash

    artifact.current_file_hash = new_hash

    db.commit()
    db.refresh(doc_version)
    return doc_version


def save_failed_run(db: Session, pipeline_run: PipelineRun, error_message: str):
    """Marque une exécution comme échouée."""
    pipeline_run.current_stage = PipelineStage.failed
    pipeline_run.error_message = error_message
    pipeline_run.completed_at = datetime.now(timezone.utc)
    db.commit()
# import hashlib
# import uuid
# from datetime import datetime, timezone
# from pathlib import Path
# from typing import Optional, Tuple, Dict, Any, List
# from sqlalchemy.orm import Session

# from app.models import (
#     Project,
#     Artifact,
#     DocVersion,
#     PipelineRun,
#     ArtifactType,
#     PipelineStage,
#     GeneratedBy,
# )


# def compute_sha256(file_path: Path) -> str:
#     """Calcule l'empreinte SHA-256 du contenu d'un fichier Markdown."""
#     return hashlib.sha256(file_path.read_bytes()).hexdigest()


# def detect_artifact_type(file_path: Path) -> ArtifactType:
#     """Détermine dynamiquement le type d'artefact."""
#     name = file_path.name.lower()

#     if "constitution" in name:
#         return ArtifactType.constitution
#     elif "requirement" in name:
#         return ArtifactType.requirements
#     elif "contract" in name:
#         return ArtifactType.contracts
#     elif "data-model" in name or "data_model" in name:
#         return ArtifactType.data_model
#     elif "research" in name:
#         return ArtifactType.research
#     elif "quickstart" in name:
#         return ArtifactType.quickstart
#     elif "plan" in name:
#         return ArtifactType.plan
#     elif "task" in name:
#         return ArtifactType.task

#     return ArtifactType.spec


# def compute_global_kpi_score(eval_dicts: List[Optional[Dict[str, Any]]]) -> Optional[float]:
#     """
#     Calcule de manière sécurisée la moyenne globale des KPI techniques 
#     à partir des évaluations JSON disponibles.
#     Gère l'absence de clés (KeyError) et les étapes omises (ex: constitution ou spec minimale).
#     """
#     extracted_scores = []

#     for eval_dict in eval_dicts:
#         if not eval_dict or not isinstance(eval_dict, dict):
#             continue

#         # Extraction sécurisée du bloc technical_evaluation
#         tech_eval = eval_dict.get("technical_evaluation", {})
#         if not isinstance(tech_eval, dict):
#             tech_eval = {}

#         # Combinaison pour inspecter toutes les métriques sans crash
#         metrics_source = {**eval_dict, **tech_eval}

#         for key, val in metrics_source.items():
#             if isinstance(val, (int, float)) and not isinstance(val, bool):
#                 key_lower = key.lower()
#                 # Exclure les compteurs d'éléments, tailles de fichiers et statistiques d'octets
#                 if any(ignored in key_lower for ignored in ["count", "kb", "size", "total", "lines", "word", "errors"]):
#                     continue
#                 # Conserver uniquement les scores et taux exprimés en pourcentage ou index
#                 if any(indicator in key_lower for indicator in ["score", "rate", "integrity", "conformity", "index", "adherence"]):
#                     extracted_scores.append(float(val))

#     if not extracted_scores:
#         return None

#     return round(sum(extracted_scores) / len(extracted_scores), 1)


# def get_or_create_project(
#     db: Session, project_name: str, repo_url: Optional[str] = None
# ) -> Project:
#     """Récupère un projet existant ou le crée en BDD."""
#     project = db.query(Project).filter(Project.name == project_name).first()
#     if not project:
#         project = Project(name=project_name, repo_url=repo_url)
#         db.add(project)
#         db.commit()
#         db.refresh(project)
#     return project


# def check_file_exists_only(
#     db: Session, file_path: Path, project_name: str
# ) -> bool:
#     """Lecture seule : verifie si un fichier a DEJA ETE TRAITE AVEC SUCCES en BDD."""
#     from app.utils.path_builder import sanitize_path_string
#     file_path_str = sanitize_path_string(file_path.resolve().as_posix())
#     project = get_or_create_project(db, project_name)

#     artifact = (
#         db.query(Artifact)
#         .filter(Artifact.project_id == project.id, Artifact.source_path == file_path_str)
#         .first()
#     )
#     if not artifact:
#         return False

#     completed_run = (
#         db.query(PipelineRun)
#         .filter(
#             PipelineRun.artifact_id == artifact.id, 
#             PipelineRun.current_stage == PipelineStage.completed
#         )
#         .first()
#     )
#     return completed_run is not None


# def should_process_file(
#     db: Session, file_path: Path, project_name: str
# ) -> Tuple[bool, str, Artifact]:
#     """Verifie si le fichier doit etre traite (nouveau hash OU dernier pipeline non termine)."""
#     from app.utils.path_builder import sanitize_path_string
#     file_path_str = sanitize_path_string(file_path.resolve().as_posix())
#     new_hash = compute_sha256(file_path)

#     project = get_or_create_project(db, project_name)

#     artifact = (
#         db.query(Artifact)
#         .filter(Artifact.project_id == project.id, Artifact.source_path == file_path_str)
#         .first()
#     )

#     if not artifact:
#         existing = (
#             db.query(Artifact)
#             .filter(Artifact.project_id == project.id, Artifact.current_file_hash == new_hash)
#             .first()
#         )
#         if existing:
#             existing.source_path = file_path_str
#             db.commit()
#             db.refresh(existing)
#             artifact = existing
#         else:
#             artifact = Artifact(
#                 project_id=project.id,
#                 source_path=file_path_str,
#                 current_file_hash=new_hash,
#                 artifact_type=detect_artifact_type(file_path),
#             )
#             db.add(artifact)
#             db.commit()
#             db.refresh(artifact)
#             return True, new_hash, artifact

#     # Correction : alignement sur la colonne started_at de models.py
#     latest_run = (
#         db.query(PipelineRun)
#         .filter(PipelineRun.artifact_id == artifact.id)
#         .order_by(PipelineRun.started_at.desc())
#         .first()
#     )

#     if (
#         artifact.current_file_hash == new_hash 
#         and latest_run 
#         and latest_run.current_stage == PipelineStage.completed
#     ):
#         return False, new_hash, artifact

#     return True, new_hash, artifact
# def create_pipeline_run(db: Session, artifact_id: uuid.UUID) -> PipelineRun:
#     """Initialise une exécution de pipeline en BDD à l'étape 'parsing'."""
#     run = PipelineRun(artifact_id=artifact_id, current_stage=PipelineStage.parsing)
#     db.add(run)
#     db.commit()
#     db.refresh(run)
#     return run


# def get_next_version(db: Session, artifact_id: uuid.UUID) -> Tuple[int, str]:
#     """
#     Calcule le numéro et le label de la prochaine version.
#     - Si 1er passage : (1, "1.0")
#     - Si modification : (2, "2.0"), (3, "3.0"), etc.
#     """
#     last_version = (
#         db.query(DocVersion)
#         .filter(DocVersion.artifact_id == artifact_id)
#         .order_by(DocVersion.version_no.desc())
#         .first()
#     )

#     if not last_version:
#         return 1, "1.0"

#     next_no = last_version.version_no + 1
#     next_label = f"{next_no}.0"
#     return next_no, next_label


# def update_pipeline_stage_data(
#     db: Session,
#     run_id: uuid.UUID,
#     stage: PipelineStage,
#     output_attr: Optional[str] = None,
#     output_data: Optional[Any] = None,
#     eval_attr: Optional[str] = None,
#     eval_data: Optional[Dict[str, Any]] = None,
# ):
#     """Met à jour le statut courant, le rendu intermédiaire et l'évaluation JSON dans PostgreSQL."""
#     try:
#         run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
#         if not run:
#             return

#         run.current_stage = stage

#         if output_attr and output_data is not None and hasattr(run, output_attr):
#             setattr(run, output_attr, output_data)

#         if eval_attr and eval_data is not None and hasattr(run, eval_attr):
#             setattr(run, eval_attr, eval_data)

#         db.commit()
#     except Exception as exc:
#         db.rollback()
#         print(f"[⚠️ DB Update Error] Échec de la mise à jour pour le stage {stage.value}: {exc}")


# def create_doc_version_pending(
#     db: Session,
#     artifact: Artifact,
#     pipeline_run: PipelineRun,
#     version_label: str,
#     version_no: int,
# ) -> DocVersion:
#     """Crée une DocVersion en status 'pending' au début du pipeline pour affichage immédiat."""
#     doc_version = DocVersion(
#         artifact_id=artifact.id,
#         version_no=version_no,
#         version_label=version_label,
#         pdf_path="",
#         source_file_hash=artifact.current_file_hash or "",
#         generated_at=datetime.now(timezone.utc),
#         generated_by=GeneratedBy.agent,
#         pipeline_run_id=pipeline_run.id,
#         global_kpi_score=None,
#     )
#     db.add(doc_version)
#     db.commit()
#     db.refresh(doc_version)
#     return doc_version


# def save_successful_run(
#     db: Session,
#     artifact: Artifact,
#     pipeline_run: PipelineRun,
#     new_hash: str,
#     pdf_path: str,
#     doc_version: Optional["DocVersion"] = None,
#     # --- Outputs ---
#     structured_json: Optional[Dict[str, Any]] = None,
#     summary_output: Optional[str] = None,
#     diagram_output: Optional[Dict[str, Any]] = None,
#     glossary_output: Optional[Dict[str, Any]] = None,
#     written_doc: Optional[str] = None,
#     layout_output: Optional[str] = None,
#     # --- Évaluations JSON ---
#     parsing_eval: Optional[Dict[str, Any]] = None,
#     summary_eval: Optional[Dict[str, Any]] = None,
#     glossary_eval: Optional[Dict[str, Any]] = None,
#     diagram_eval: Optional[Dict[str, Any]] = None,
#     writer_eval: Optional[Dict[str, Any]] = None,
#     layout_eval: Optional[Dict[str, Any]] = None,
#     # --- Score KPI ---
#     global_kpi_score: Optional[float] = None,
#     commit_hash: Optional[str] = None,
# ) -> DocVersion:
#     """Marque le PipelineRun comme terminé et génère la DocVersion avec son numéro v1.0, v2.0..."""
#     pipeline_run.current_stage = PipelineStage.completed
#     pipeline_run.completed_at = datetime.now(timezone.utc)

#     if structured_json: pipeline_run.structured_json = structured_json
#     if summary_output: pipeline_run.summary_output = summary_output
#     if diagram_output: pipeline_run.diagram_output = diagram_output
#     if glossary_output: pipeline_run.glossary_output = glossary_output
#     if written_doc: pipeline_run.written_doc = written_doc
#     if layout_output: pipeline_run.layout_output = layout_output

#     if parsing_eval: pipeline_run.parsing_eval = parsing_eval
#     if summary_eval: pipeline_run.summary_eval = summary_eval
#     if glossary_eval: pipeline_run.glossary_eval = glossary_eval
#     if diagram_eval: pipeline_run.diagram_eval = diagram_eval
#     if writer_eval: pipeline_run.writer_eval = writer_eval
#     if layout_eval: pipeline_run.layout_eval = layout_eval

#     # 🎯 Calcul/Secours automatique du KPI global s'il est None ou égal à 0.0
#     if not global_kpi_score or global_kpi_score == 0.0:
#         computed_score = compute_global_kpi_score([
#             parsing_eval,
#             summary_eval,
#             glossary_eval,
#             diagram_eval,
#             writer_eval,
#             layout_eval,
#         ])
#         if computed_score is not None:
#             global_kpi_score = computed_score

#     pipeline_run.global_kpi_score = global_kpi_score

#     # Récupérer la DocVersion existante (créée au début du pipeline)
#     doc_version = (
#         db.query(DocVersion)
#         .filter(DocVersion.pipeline_run_id == pipeline_run.id)
#         .first()
#     )

#     if not doc_version:
#         # Fallback : créer si n'existe pas (compatibilité ascendante)
#         next_version_no, next_version_label = get_next_version(db, artifact.id)
#         doc_version = DocVersion(
#             artifact_id=artifact.id,
#             version_no=next_version_no,
#             version_label=next_version_label,
#             pdf_path=pdf_path,
#             source_file_hash=new_hash,
#             generated_by=GeneratedBy.agent,
#             pipeline_run_id=pipeline_run.id,
#             global_kpi_score=global_kpi_score,
#             commit_hash=commit_hash,
#         )
#         db.add(doc_version)
#     else:
#         # Mettre à jour la DocVersion existante
#         doc_version.pdf_path = pdf_path
#         doc_version.source_file_hash = new_hash
#         doc_version.global_kpi_score = global_kpi_score
#         doc_version.commit_hash = commit_hash

#     artifact.current_file_hash = new_hash

#     db.commit()
#     db.refresh(doc_version)
#     return doc_version


# def save_failed_run(db: Session, pipeline_run: PipelineRun, error_message: str):
#     """Marque une exécution comme échouée."""
#     pipeline_run.current_stage = PipelineStage.failed
#     pipeline_run.error_message = error_message
#     pipeline_run.completed_at = datetime.now(timezone.utc)
#     db.commit()