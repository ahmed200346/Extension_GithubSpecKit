# app/schemas/layout_agent_schema.py
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LayoutPublicationStatus(str, Enum):
    """Statuts d'arbitrage de la qualité de publication du document PDF."""
    READY_FOR_PUBLICATION = "READY_FOR_PUBLICATION"
    NEEDS_REFINEMENT = "NEEDS_REFINEMENT"
    BLOCKED = "BLOCKED"


class LayoutOutputModel(BaseModel):
    """
    Schéma de sortie Pydantic pour le Layout Agent.
    Structure le résultat de compilation PDF, le statut de publication 
    et les métriques d'évaluation visuelle.
    """
    project_name: str = Field(
        default="Inconnu", 
        description="Nom du projet traité"
    )
    pdf_file_path: str = Field(
        ..., 
        description="Chemin d'accès local ou URL du fichier PDF généré"
    )
    pdf_generated: bool = Field(
        default=False, 
        description="Indique si le PDF a été compilé sans erreur"
    )
    page_count: int = Field(
        default=0, 
        ge=0, 
        description="Nombre total de pages du document PDF"
    )
    file_size_kb: float = Field(
        default=0.0, 
        ge=0.0, 
        description="Taille du fichier PDF binaire en Kilooctets (Ko)"
    )
    rendered_diagrams_count: int = Field(
        default=0, 
        ge=0, 
        description="Nombre de diagrammes Mermaid convertis et insérés en images"
    )
    layout_publication_status: LayoutPublicationStatus = Field(
        default=LayoutPublicationStatus.BLOCKED,
        description="Statut d'arbitrage final (READY_FOR_PUBLICATION, NEEDS_REFINEMENT, BLOCKED)"
    )
    technical_evaluation: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores des métriques techniques du Layout Agent (RSR, DVR, PBA, VOR, SCS)"
    )
    project_management_kpis: Dict[str, Any] = Field(
        default_factory=dict,
        description="KPIs de gestion du rendu visuel et d'impression"
    )
    execution_warnings: Optional[List[str]] = Field(
        default_factory=list,
        description="Avertissements ou anomalies détectés lors de la compilation"
    )