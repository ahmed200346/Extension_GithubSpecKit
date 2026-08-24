import uuid
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _enum_values(enum_cls):
    """SQLAlchemy sends the Python Enum member's .name to Postgres by default.
    Our native enum types are populated from .value (see sync_native_enums), and
    ArtifactType.data_model's name ("data_model") differs from its value
    ("data-model") — without this, inserts fail with InvalidTextRepresentation."""
    return [e.value for e in enum_cls]



# ============================================
# ENUMS
# ============================================

class ArtifactType(str, Enum):
    spec = "spec"
    plan = "plan"
    task = "task"
    constitution = "constitution"
    requirements = "requirements"
    contracts = "contracts"
    data_model = "data-model"
    research = "research"
    quickstart = "quickstart"
    autres = "autres"


class GeneratedBy(str, Enum):
    agent = "agent"
    user = "user"


class PipelineStage(str, Enum):
    """Étape courante du pipeline pour le suivi temps réel sur le dashboard."""
    parsing = "parsing"
    parallel_enrichment = "parallel_enrichment"   # Summary / Diagram / Glossary
    summary = "summary"                             # Summary Agent (individual stage)
    glossary = "glossary"                           # Glossary Agent (individual stage)
    diagram = "diagram"                             # Diagram Agent (individual stage)
    writing = "writing"                             # Documentation Writer
    layout = "layout"                               # Design/Layout Agent
    rendering = "rendering"                         # Markdown/HTML -> PDF Generator
    completed = "completed"
    failed = "failed"


class TicketStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TicketEventType(str, Enum):
    status_change = "status_change"
    status_override = "status_override"
    comment_added = "comment_added"


class AuthorType(str, Enum):
    human = "human"
    agent = "agent"


def sync_native_enums(engine):
    """
    S'assure que les types ENUM PostgreSQL natifs possèdent toutes les valeurs 
    définies dans les classes Enum Python/SQLAlchemy (ex: constitution, requirements, contracts).
    """
    native_enums = [
        (ArtifactType, "artifact_type_enum"),
        (GeneratedBy, "generated_by_enum"),
        (PipelineStage, "pipeline_stage_enum"),
    ]

    try:
        with engine.connect() as conn:
            for enum_cls, enum_name in native_enums:
                query = text(
                    "SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = :name"
                )
                existing_labels = {r[0] for r in conn.execute(query, {"name": enum_name}).fetchall()}
                if not existing_labels:
                    continue
                for item in enum_cls:
                    if item.value not in existing_labels:
                        try:
                            conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{item.value}'"))
                            conn.commit()
                        except Exception:
                            pass
    except Exception as e:
        print(f"[WARN] Impossible de synchroniser les enums DB: {e}")


# ============================================
# Project / Artifact / DocVersion
# ============================================

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    artifacts = relationship(
        "Artifact", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("project_id", "source_path", name="uq_artifact_project_path"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    current_file_hash = Column(String(64), nullable=True)
    source_path = Column(String(500), nullable=False)
    artifact_type = Column(
        SAEnum(ArtifactType, name="artifact_type_enum", values_callable=_enum_values),
        nullable=False,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="artifacts")
    doc_versions = relationship(
        "DocVersion",
        back_populates="artifact",
        cascade="all, delete-orphan",
        order_by="DocVersion.version_no",
    )
    pipeline_runs = relationship(
        "PipelineRun",
        back_populates="artifact",
        cascade="all, delete-orphan",
        order_by="PipelineRun.started_at",
    )

    def __repr__(self) -> str:
        return f"<Artifact id={self.id} source_path={self.source_path!r}>"


# Dans app/models.py (classe DocVersion)

class DocVersion(Base):
    __tablename__ = "doc_versions"
    __table_args__ = (
        UniqueConstraint("artifact_id", "version_no", name="uq_docversion_artifact_versionno"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    artifact_id = Column(
        UUID(as_uuid=True), ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False
    )
    
    # Numéro séquentiel interne (1, 2, 3...)
    version_no = Column(Integer, nullable=False)
    
    # Label affiché (ex: "1.0", "2.0")
    version_label = Column(String(20), nullable=False, default="1.0")
    
    pdf_path = Column(String(500), nullable=False)
    source_file_hash = Column(String(64), nullable=False)
    generated_at = Column(DateTime, server_default=func.now(), nullable=False)
    sections_summary = Column(JSONB, nullable=True)
    commit_hash = Column(String(40), nullable=True)
    generated_by = Column(
        SAEnum(GeneratedBy, name="generated_by_enum", values_callable=_enum_values),
        nullable=False,
        default=GeneratedBy.agent,
    )
    pipeline_run_id = Column(
        UUID(as_uuid=True), ForeignKey("pipeline_runs.id", ondelete="SET NULL"), nullable=True
    )

    global_kpi_score = Column(Float, nullable=True)

    artifact = relationship("Artifact", back_populates="doc_versions")
    pipeline_run = relationship("PipelineRun", back_populates="doc_version")

    def __repr__(self) -> str:
        return f"<DocVersion id={self.id} v{self.version_label} artifact_id={self.artifact_id}>"

# ============================================
# PipelineRun — Suivi complet & Évaluations BDD + Outputs
# ============================================

class PipelineRun(Base):
    """
    Une ligne = une exécution complète du pipeline.
    Stocke les résultats bruts + les JSONs d'évaluation pour les 6 agents.
    """
    __tablename__ = "pipeline_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    artifact_id = Column(
        UUID(as_uuid=True), ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False
    )

    current_stage = Column(
        SAEnum(PipelineStage, name="pipeline_stage_enum", values_callable=_enum_values),
        nullable=False,
        default=PipelineStage.parsing,
    )

    # --- 1. Sorties brutes des Agents ---
    structured_json = Column(JSONB, nullable=True)      # Output Parsing Agent
    summary_output = Column(Text, nullable=True)          # Output Summary Agent
    diagram_output = Column(JSONB, nullable=True)         # Output Diagram Agent
    glossary_output = Column(JSONB, nullable=True)        # Output Glossary Agent
    written_doc = Column(Text, nullable=True)              # Output Documentation Writer
    layout_output = Column(Text, nullable=True)            # Output Design/Layout Agent

    # --- 2. Évaluations JSON des 6 Agents (Pop-up Frontend) ---
    parsing_eval = Column(JSONB, nullable=True)          # Eval Parsing Agent
    summary_eval = Column(JSONB, nullable=True)          # Eval Summary Agent
    glossary_eval = Column(JSONB, nullable=True)         # Eval Glossary Agent
    diagram_eval = Column(JSONB, nullable=True)          # Eval Diagram Agent
    writer_eval = Column(JSONB, nullable=True)           # Eval Documentation Writer Agent
    layout_eval = Column(JSONB, nullable=True)           # Eval Layout Agent

    # --- 3. KPI Global combiné ---
    global_kpi_score = Column(Float, nullable=True)

    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    artifact = relationship("Artifact", back_populates="pipeline_runs")
    doc_version = relationship("DocVersion", back_populates="pipeline_run", uselist=False)

    def __repr__(self) -> str:
        return f"<PipelineRun id={self.id} stage={self.current_stage} score={self.global_kpi_score}>"


# ============================================
# Ticket — Suivi des tâches issues de tasks.md
# ============================================

class Ticket(Base):
    """
    Représente une tâche issue d'un fichier tasks.md
    """
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("project_id", "ticket_id", name="uq_ticket_project_ticketid"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    artifact_id = Column(
        UUID(as_uuid=True), ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True
    )
    
    ticket_id = Column(String(50), nullable=False)  # ex: "T001", "T002"
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(
        SAEnum(TicketStatus, name="ticket_status_enum", values_callable=_enum_values),
        nullable=False,
        default=TicketStatus.todo,
    )
    
    # Métadonnées du fichier source
    source_file_path = Column(String(500), nullable=True)
    source_file_hash = Column(String(64), nullable=True)
    
    # Checkbox state (pour affichage uniquement, pas pour la logique)
    checkbox_state = Column(String(20), nullable=True)  # "checked", "unchecked", "in_progress"
    line_number = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    events = relationship(
        "TicketEvent",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketEvent.created_at",
    )
    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketComment.created_at",
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} ticket_id={self.ticket_id!r} status={self.status}>"


class TicketEvent(Base):
    """
    Événement lié à un ticket (changement de statut, commentaire, etc.)
    """
    __tablename__ = "ticket_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    ticket_id = Column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    
    event_type = Column(
        SAEnum(TicketEventType, name="ticket_event_type_enum", values_callable=_enum_values),
        nullable=False,
    )
    
    author_name = Column(String(255), nullable=True)
    author_type = Column(
        SAEnum(AuthorType, name="author_type_enum", values_callable=_enum_values),
        nullable=False,
        default=AuthorType.human,
    )
    
    old_status = Column(SAEnum(TicketStatus, name="ticket_status_enum", values_callable=_enum_values), nullable=True)
    new_status = Column(SAEnum(TicketStatus, name="ticket_status_enum", values_callable=_enum_values), nullable=True)
    
    comment = Column(Text, nullable=True)
    event_metadata = Column(JSONB, nullable=True)  # Renommé de 'metadata' (réservé par SQLAlchemy)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    ticket = relationship("Ticket", back_populates="events")

    def __repr__(self) -> str:
        return f"<TicketEvent id={self.id} type={self.event_type} ticket_id={self.ticket_id}>"


class TicketComment(Base):
    """
    Commentaire sur un ticket
    """
    __tablename__ = "ticket_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    ticket_id = Column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    
    author_name = Column(String(255), nullable=True)
    author_type = Column(
        SAEnum(AuthorType, name="author_type_enum", values_callable=_enum_values),
        nullable=False,
        default=AuthorType.human,
    )
    
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    ticket = relationship("Ticket", back_populates="comments")

    def __repr__(self) -> str:
        return f"<TicketComment id={self.id} ticket_id={self.ticket_id}>"
