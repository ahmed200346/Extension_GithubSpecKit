# app/schemas/diagram_agent_schema.py
"""
diagram_agent_schema.py — Modèles Pydantic de validation pour le Diagram Agent.
Garantit la conformité et la structure du JSON généré par le LLM.
"""

from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

# Types de diagrammes Mermaid.js strictement autorisés selon la spécification
DiagramType = Literal[
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "erDiagram",
    "stateDiagram",
    "gantt",
    "mindmap",
    "pie"
]


class DiagramItem(BaseModel):
    """Représente un diagramme individuel généré par l'agent."""
    title: str = Field(
        ..., 
        description="Titre explicite et descriptif du schéma (ex: CourseHub API Implementation Decision Flow)."
    )
    type: DiagramType = Field(
        ..., 
        description="Type du diagramme Mermaid.js (ex: flowchart, sequenceDiagram, erDiagram)."
    )
    description: str = Field(
        ..., 
        description="Court résumé opérationnel explicitant ce que le schéma modélise."
    )
    mermaid_code: str = Field(
        ..., 
        description="Code source brut en syntaxe Mermaid.js (sans balises markdown)."
    )

    model_config = ConfigDict(extra="ignore")


class DiagramOutputModel(BaseModel):
    """Conteneur principal validant la sortie globale du Diagram Agent."""
    diagrams: List[DiagramItem] = Field(
        default_factory=list,
        description="Liste contenant entre 1 et 4 diagrammes générés par l'agent."
    )

    model_config = ConfigDict(extra="ignore")