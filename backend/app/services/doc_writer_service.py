# app/services/doc_writer_service.py

import json
from typing import Dict, Any

# Importation du schéma de sortie
from app.schemas.doc_writer_agent_schema import (
    DocWriterOutputModel,
    DocReadinessStatus,
    IntegratedArtifactsSummary
)

# Importations des schémas amont pour validation
from app.schemas.parsing_agent_schema import ParsingAgentOutput
from app.schemas.summary_agent_schema import SummaryOutputModel
from app.schemas.glossary_agent_schema import GlossaryOutputModel
from app.schemas.diagram_agent_schema import DiagramOutputModel

# Outils et utilitaires
from app.core.prompts import get_doc_writer_prompt
from app.core.llm_client import ollama_openai_client, get_ollama_model
from app.core.llm_utils import clean_markdown_response
from app.utils.doc_writer_tools import extract_markdown_toc, sanitize_mermaid_blocks, save_markdown_artifact


class DocWriterAgentService:
    """
    Service d'orchestration pour le Documentation Writer Agent.
    Consolide les sorties des 4 agents amont (Parsing, Summary, Glossary, Diagrams)
    en un document Markdown unifié de niveau professionnel.
    """

    def generate_documentation(
        self,
        parsed_json_dict: Dict[str, Any],
        summary_json_dict: Dict[str, Any],
        glossary_json_dict: Dict[str, Any],
        diagrams_json_dict: Dict[str, Any],
        doc_writer_spec_dict: Dict[str, Any]
    ) -> DocWriterOutputModel:
        """
        Exécute le pipeline complet de consolidation et d'édition de la documentation.
        """
        # 1. Validation structurelle des objets d'entrée amont
        ParsingAgentOutput(**parsed_json_dict)
        SummaryOutputModel(**summary_json_dict)
        GlossaryOutputModel(**glossary_json_dict)
        DiagramOutputModel(**diagrams_json_dict)

        # 2. Extraction du nom du projet
        project_name = parsed_json_dict.get("project_info", {}).get("project_name", "Technical Project")

        # 3. Construction du System Prompt avec injection du fichier ressource doc_writer_spec
        system_prompt = get_doc_writer_prompt(doc_writer_spec=doc_writer_spec_dict)

        # 4. Assemblage du Payload utilisateur (Regroupement des 4 états)
        pipeline_state_payload = {
            "project_name": project_name,
            "parsed_data": parsed_json_dict,
            "summary_data": summary_json_dict,
            "diagrams_data": diagrams_json_dict,
            "glossary_data": glossary_json_dict
        }
        user_prompt = json.dumps(pipeline_state_payload, ensure_ascii=False)

        # 5. Inférence LLM via le client centralisé (Génération du Markdown unifié)
        response = ollama_openai_client.chat.completions.create(
            model=get_ollama_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )

        raw_markdown = response.choices[0].message.content

        # 6. Sanitisation et nettoyage de la réponse Markdown
        clean_md = clean_markdown_response(raw_markdown)
        clean_md = sanitize_mermaid_blocks(clean_md)

        # 7. Exécution des Outils déterministes (TOC et Sauvegarde sur disque)
        table_of_contents = extract_markdown_toc(clean_md)
        saved_filepath = save_markdown_artifact(clean_md, project_name=project_name)

        # 8. Calcul des statistiques de consolidation d'artéfacts
        integrated_artifacts = IntegratedArtifactsSummary(
            summary_integrated=True,
            total_elements_integrated=len(parsed_json_dict.get("elements", [])),
            total_diagrams_embedded=len(diagrams_json_dict.get("diagrams", [])),
            total_glossary_terms=len(glossary_json_dict.get("items", []))
        )

        # 9. Construction et validation de l'objet Pydantic final
        return DocWriterOutputModel(
            project_name=project_name,
            document_title=f"{project_name} - Technical Specification & Architecture Document",
            readiness_status=DocReadinessStatus.READY_FOR_PDF_EXPORT,
            markdown_content=clean_md,
            table_of_contents=table_of_contents,
            integrated_artifacts=integrated_artifacts,
            metadata={
                "word_count": len(clean_md.split()),
                "saved_markdown_path": saved_filepath
            }
        )