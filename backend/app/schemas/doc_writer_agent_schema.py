# app/schemas/doc_writer_agent_schema.py

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocReadinessStatus(str, Enum):
    """Statut de maturité opérationnelle du document consolidé pour publication/export PDF."""
    READY_FOR_PDF_EXPORT = "READY_FOR_PDF_EXPORT"
    NEEDS_REFINEMENT = "NEEDS_REFINEMENT"
    BLOCKED = "BLOCKED"


class IntegratedArtifactsSummary(BaseModel):
    """Synthèse quantitative de la consolidation des artéfacts issus des agents amont."""
    total_elements_integrated: int = Field(
        ..., 
        description="Nombre total d'éléments/nœuds du graphe (US, FR, Entités) réintégrés dans le texte."
    )
    total_diagrams_embedded: int = Field(
        ..., 
        description="Nombre de diagrammes Mermaid réintégrés dans la section architecture."
    )
    total_glossary_terms: int = Field(
        ..., 
        description="Nombre de termes et acronymes inclus dans la section Glossaire terminale."
    )


class DocWriterOutputModel(BaseModel):
    """
    Schéma Pydantic officiel de sortie pour le Documentation Writer Agent.
    Consolide le contenu Markdown unifié ainsi que les métadonnées de structure et de traçabilité.
    """
    project_name: str = Field(
        ..., 
        description="Nom extrait ou assigné au projet."
    )
    document_title: str = Field(
        default="Technical Specification & Architecture Document",
        description="Titre principal du document consolidé."
    )
    readiness_status: DocReadinessStatus = Field(
        ..., 
        description="Évaluation de la maturité globale du document."
    )
    markdown_content: str = Field(
        ..., 
        description="Le texte brut Markdown unifié complet, prêt pour la compilation déterministe en PDF."
    )
    table_of_contents: List[str] = Field(
        default_factory=list,
        description="Sommaire des sections principales détectées dans le document Markdown."
    )
    integrated_artifacts: IntegratedArtifactsSummary = Field(
        ..., 
        description="Statistiques de consolidation des objets de données des agents précédents."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées d'exécution (ex: horodatage, version de l'agent, nombre de mots)."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "CourseHub API",
                "document_title": "CourseHub API - Technical Specification & Architecture Document",
                "readiness_status": "READY_FOR_PDF_EXPORT",
                "markdown_content": "# CourseHub API...\n\n## 1. Executive Summary...",
                "table_of_contents": [
                    "1. Executive Summary & Architecture Overview",
                    "2. Architecture Workflows & Visual Diagrams",
                    "3. Detailed Technical Specifications & Business Rules",
                    "4. Project Governance & Structural Gaps",
                    "5. Technical & Domain Glossary (Terminology Reference)"
                ],
                "integrated_artifacts": {
                    "total_elements_integrated": 14,
                    "total_diagrams_embedded": 2,
                    "total_glossary_terms": 3
                },
                "metadata": {
                    "word_count": 1250,
                    "generated_at": "2026-07-21T14:30:00Z"
                }
            }
        }