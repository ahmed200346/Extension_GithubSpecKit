# app/services/layout_service.py

import os
from typing import Dict, Any, Optional

# Importation du schéma de sortie Pydantic du Layout Agent
from app.schemas.layout_agent_schema import (
    LayoutOutputModel,
    LayoutPublicationStatus
)

from app.services.evaluation_service import LayoutEvaluatorService

from app.utils.layout_tools import (
    render_mermaid_diagrams,
    compile_markdown_to_pdf,
    inspect_generated_pdf
)

# ✅ Même fonction que celle utilisée par pipeline.py pour calculer paths["final_pdf"].
# On la réutilise ici pour garantir que le PDF est TOUJOURS écrit exactement
# là où la BDD s'attend à le trouver, quel que soit l'appelant.
from app.utils.path_builder import build_pipeline_paths


class LayoutAgentService:
    """
    Service d'orchestration pour le Layout Agent.
    Prend en entrée le Markdown unifié (doc.md) du Doc Writer,
    convertit les schémas Mermaid en images, applique la charte graphique (layout_spec.json),
    compile le PDF final et calcule les métriques d'évaluation visuelle.
    """

    def process_layout_and_render(
        self,
        markdown_text: str,
        layout_spec_dict: Dict[str, Any],
        project_name: str = "Technical Project",
        output_pdf_path: Optional[str] = None,
        file_name: Optional[str] = None,
        version_label: str = "1.0"
    ) -> LayoutOutputModel:
        """
        Exécute le pipeline complet de mise en page, conversion visuelle et compilation PDF.

        file_name / version_label : mêmes valeurs que celles passées à
        build_pipeline_paths() dans pipeline.py (typiquement disponibles dans
        le GraphState via state["file_name"] / state["version_label"]).
        Elles servent UNIQUEMENT à calculer le nom de fichier par défaut
        quand output_pdf_path n'est pas fourni explicitement.
        """
        execution_warnings = []

        # 1. Validation de l'entrée Markdown
        if not markdown_text or not markdown_text.strip():
            execution_warnings.append("Le texte Markdown source est vide.")
            return LayoutOutputModel(
                project_name=project_name,
                pdf_file_path="",
                pdf_generated=False,
                layout_publication_status=LayoutPublicationStatus.BLOCKED,
                execution_warnings=["Impossible de générer le PDF : document source vide."]
            )

        # 2. Configuration du chemin de sortie pour le fichier PDF
        if not output_pdf_path:
            # ⚠️ CORRECTIF : avant, ce fallback écrivait dans "exports/xxx.pdf"
            # (chemin relatif, convention de nom différente), totalement
            # déconnecté du chemin paths["final_pdf"] enregistré en BDD par
            # pipeline.py. Résultat : le bouton "Viewer" du frontend pointait
            # vers un fichier inexistant ("Fichier PDF introuvable sur le
            # disque"), même quand le PDF avait bien été généré... ailleurs.
            #
            # On utilise maintenant EXACTEMENT la même fonction que
            # pipeline.py pour calculer le chemin, ce qui élimine toute
            # possibilité de désynchronisation.
            paths = build_pipeline_paths(
                file_name=file_name or project_name,
                version_label=version_label,
                project_name=project_name
            )
            output_pdf_path = str(paths["final_pdf"])
        else:
            os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)

        # 3. ÉTAPE 1 : Conversion des diagrammes Mermaid en images PNG/SVG
        try:
            updated_markdown, rendered_diagram_paths = render_mermaid_diagrams(
                markdown_text=markdown_text
            )
        except Exception as e:
            updated_markdown = markdown_text
            rendered_diagram_paths = []
            execution_warnings.append(f"Avertissement lors du rendu des diagrammes Mermaid : {str(e)}")

        # 4. ÉTAPE 2 : Compilation du Markdown enrichi vers PDF via ReportLab
        compilation_result = {}
        pdf_generated = False
        try:
            compilation_result = compile_markdown_to_pdf(
                markdown_text=updated_markdown,
                output_pdf_path=output_pdf_path,
                layout_spec=layout_spec_dict
            )
            pdf_generated = compilation_result.get("output_pdf_path") is not None and os.path.exists(output_pdf_path)
        except Exception as e:
            execution_warnings.append(f"Erreur critique lors de la compilation PDF : {str(e)}")
            pdf_generated = False

        # 5. ÉTAPE 3 : Inspection binaire du PDF produit pour extraction des métadonnées
        # On exécute TOUJOURS l'inspection et l'évaluation, même en cas d'échec,
        # pour que layout_eval soit peuplé en BDD (évite "NA" dans le frontend)
        rendered_pdf_metadata, layout_overflow_report = inspect_generated_pdf(
            pdf_path=output_pdf_path,
            compilation_result=compilation_result,
            rendered_diagrams_count=len(rendered_diagram_paths)
        )

        # 6. ÉTAPE 4 : Calcul automatique des métriques et arbitrage de publication
        evaluation_result = LayoutEvaluatorService.evaluate(
            markdown_text=markdown_text,
            rendered_pdf_metadata=rendered_pdf_metadata,
            layout_overflow_report=layout_overflow_report,
            layout_spec=layout_spec_dict,
            project_name=project_name
        )

        # 7. Extraction des métriques et conversion du statut d'évaluation
        tech_eval = evaluation_result.get("technical_evaluation", {})
        mgmt_kpis = evaluation_result.get("project_management_kpis", {})
        raw_status = evaluation_result.get("layout_publication_status", "BLOCKED")

        try:
            publication_status = LayoutPublicationStatus(raw_status)
        except ValueError:
            publication_status = LayoutPublicationStatus.BLOCKED

        # 8. Construction et retour de l'objet Pydantic final
        return LayoutOutputModel(
            project_name=project_name,
            pdf_file_path=output_pdf_path,
            pdf_generated=rendered_pdf_metadata.get("pdf_generated", False),
            page_count=rendered_pdf_metadata.get("page_count", 0),
            file_size_kb=mgmt_kpis.get("file_size_kb", 0.0),
            rendered_diagrams_count=len(rendered_diagram_paths),
            layout_publication_status=publication_status,
            technical_evaluation=tech_eval,
            project_management_kpis=mgmt_kpis,
            execution_warnings=execution_warnings
        )