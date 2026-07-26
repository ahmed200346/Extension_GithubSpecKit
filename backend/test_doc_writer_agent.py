# test_doc_writer_agent.py
"""
test_doc_writer_agent.py — Validation isolée et évaluation par métriques colorisées
du Documentation Writer Agent (Orchestrateur Éditorial).
Consolide les outputs du Parser, Summary, Glossary et Diagram Agents.
"""

import os
import sys
import json
from pathlib import Path

# Importations des services, outils et schémas de l'application
from app.services.doc_writer_service import DocWriterAgentService
from app.services.evaluation_service import DocWriterEvaluatorService
from app.schemas.doc_writer_agent_schema import DocWriterOutputModel
from app.schemas.parsing_agent_schema import ParsingAgentOutput
from app.schemas.summary_agent_schema import SummaryOutputModel
from app.schemas.glossary_agent_schema import GlossaryOutputModel
from app.schemas.diagram_agent_schema import DiagramOutputModel

# ==============================================================================
# CONFIGURATION : Préfixe du fichier cible à évaluer (ex: "tasks(1)" ou "spec(1)")
# ==============================================================================
TARGET_PREFIX = "tasks(1)"  # Exige : tasks(1)_parsed.json, tasks(1)_summary.json, etc.
SPEC_FILE_NAME = "doc_writer_spec.json"  # Spécification de structure
# ==============================================================================
def get_metric_color_tag(score: float) -> str:
    """Attribue un émoji de couleur selon les seuils critiques de performance."""
    if score == 100.0:
        return "🟢"
    elif score >= 80.0:
        return "🟡"
    return "🔴"


def run_isolated_doc_writer_test():
    backend_dir = Path(__file__).resolve().parent          # .../StageTalan/backend
    project_root = backend_dir.parent                      # .../StageTalan
    test_files_dir = project_root / "test_files"           # .../StageTalan/test_files
    outputs_dir = test_files_dir / "outputs"               # .../StageTalan/test_files/outputs
    
    # Chemins des 4 fichiers JSON amont
    parsed_path = outputs_dir / f"{TARGET_PREFIX}_parsed.json"
    summary_path = outputs_dir / f"{TARGET_PREFIX}_summary.json"
    glossary_path = outputs_dir / f"{TARGET_PREFIX}_glossary.json"
    diagrams_path = outputs_dir / f"{TARGET_PREFIX}_diagrams.json"
    
    # Chemin de la ressource doc_writer_spec.json
    spec_path = backend_dir / "app" / "resources" / SPEC_FILE_NAME

    print("=" * 75)
    print("      TEST D'ÉVALUATION ET DE FIABILITÉ - DOCUMENTATION WRITER AGENT")
    print("=" * 75)

    # 1. Vérification du répertoire de sortie
    if not outputs_dir.exists():
        print(f"[❌] Erreur : Le dossier des sorties '{outputs_dir}' n'existe pas.")
        sys.exit(1)

    # 2. Chargement sécurisé des 4 outputs JSON des agents précédents
    print(f"[📂] Chargement des artefacts amont pour le préfixe : '{TARGET_PREFIX}'")
    
    if not parsed_path.exists():
        print(f"[❌] Erreur : Fichier parsé introuvable : {parsed_path.name}")
        sys.exit(1)
    with open(parsed_path, "r", encoding="utf-8") as f:
        parsed_json_dict = json.load(f)

    if not summary_path.exists():
        print(f"[❌] Erreur : Fichier summary introuvable : {summary_path.name}")
        sys.exit(1)
    with open(summary_path, "r", encoding="utf-8") as f:
        summary_json_dict = json.load(f)

    if not glossary_path.exists():
        print(f"[❌] Erreur : Fichier glossaire introuvable : {glossary_path.name}")
        sys.exit(1)
    with open(glossary_path, "r", encoding="utf-8") as f:
        glossary_json_dict = json.load(f)

    # Diagrammes (Fallback gracieux si l'agent diagramme n'a pas encore été exécuté)
    diagrams_json_dict = {"project_name": TARGET_PREFIX, "diagrams": []}
    if diagrams_path.exists():
        print(f"[✅] Artefact Diagrammes détecté : {diagrams_path.name}")
        with open(diagrams_path, "r", encoding="utf-8") as f:
            diagrams_json_dict = json.load(f)
    else:
        print(f"[⚠️] Attention : Fichier diagrammes '{diagrams_path.name}' introuvable. Mode dégradé actif.")

    # 3. Chargement de la ressource doc_writer_spec.json
    doc_writer_spec_dict = {}
    if spec_path.exists():
        print(f"[⚙️] Spécification '{SPEC_FILE_NAME}' chargée avec succès.")
        with open(spec_path, "r", encoding="utf-8") as f:
            doc_writer_spec_dict = json.load(f)
    else:
        print(f"[⚠️] Spécification '{SPEC_FILE_NAME}' introuvable sous app/resources/.")

    print("-" * 75)

    # 4. Exécution du Documentation Writer Agent
    print("[⌛] Consolidation et rédaction du document Markdown en cours...")
    doc_result = None
    success = False

    try:
        service = DocWriterAgentService()
        doc_result = service.generate_documentation(
            parsed_json_dict=parsed_json_dict,
            summary_json_dict=summary_json_dict,
            glossary_json_dict=glossary_json_dict,
            diagrams_json_dict=diagrams_json_dict,
            doc_writer_spec_dict=doc_writer_spec_dict
        )
        success = True
        print("[OK] Document Markdown généré et validé par Pydantic !\n")

        # Sauvegarde physique du fichier Markdown
        markdowns_dir = outputs_dir / "markdowns"
        markdowns_dir.mkdir(parents=True, exist_ok=True)
        output_md_path = markdowns_dir / f"{TARGET_PREFIX}_doc.md"
        
        with open(output_md_path, "w", encoding="utf-8") as out_f:
            out_f.write(doc_result.markdown_content)
        print(f"[💾] Document Markdown sauvegardé sous : {output_md_path.relative_to(project_root)}")

    except Exception as e:
        print(f"[❌] ÉCHEC DE LA GÉNÉRATION DE LA DOCUMENTATION : {e}")

    # 5. ÉVALUATION DES MÉTRIQUES VIA LE SERVICE ISOLÉ (DASHBOARD)
    print("\n📊 ÉVALUATION DES MÉTRIQUES DE FIABILITÉ ÉDITORIALE (DASHBOARD)")
    print("-" * 75)

    dsc_score, tpr_score, dev_score, gff_score = 0.0, 0.0, 0.0, 0.0

    if success and doc_result:
        # Reconstitution des objets Pydantic pour l'évaluateur
        parsed_obj = ParsingAgentOutput(**parsed_json_dict)
        summary_obj = SummaryOutputModel(**summary_json_dict)
        glossary_obj = GlossaryOutputModel(**glossary_json_dict)
        diagram_obj = DiagramOutputModel(**diagrams_json_dict)

        report = DocWriterEvaluatorService.evaluate(
            markdown_text=doc_result.markdown_content,
            parsed_data=parsed_obj,
            summary_data=summary_obj,
            glossary_data=glossary_obj,
            diagram_data=diagram_obj
        )

        tech = report["technical_evaluation"]
        mgmt = report["project_management_kpis"]

        dsc_score = tech["document_structure_completeness"]
        tpr_score = tech["traceability_preservation_rate"]
        dev_score = tech["diagram_embedding_validity"]
        gff_score = tech["glossary_format_and_placement"]

        # Affichage des 4 métriques de fiabilité technique
        print(f"1. Document Structure Completeness (DSC) : {get_metric_color_tag(dsc_score)} {dsc_score:.1f}%")
        print(f"2. Traceability Preservation Rate (TPR)   : {get_metric_color_tag(tpr_score)} {tpr_score:.1f}%")
        print(f"3. Diagram Embedding Validity (DEV)      : {get_metric_color_tag(dev_score)} {dev_score:.1f}%")
        print(f"4. Glossary Format & Placement (GFF)     : {get_metric_color_tag(gff_score)} {gff_score:.1f}%")
        print("-" * 75)

        # Affichage des KPIs de gestion
        print("📈 KPIs DE CONSOLIDATION ET MATURITÉ ÉDITORIALE")
        print("-" * 75)
        print(f"• Projet identifié                       : {report['project_name']}")

        status_colors = {
            "READY_FOR_PDF_EXPORT": "🟢 READY_FOR_PDF_EXPORT (Prêt pour compilation PDF / Layout Agent)",
            "NEEDS_REFINEMENT": "🟡 NEEDS_REFINEMENT (Manque des sections ou pertes de traçabilité)",
            "BLOCKED": "🔴 BLOCKED (Ruptures majeures dans le document Markdown)"
        }
        print(f"• STATUT D'EXPORTATION PDF               : {status_colors.get(report['documentation_readiness_status'])}")
        print(f"• Volume de mots générés                 : {mgmt['total_markdown_word_count']} mots")
        print(f"• Identifiants source traçables          : {mgmt['retained_identifiers_count']} / {mgmt['total_source_identifiers_count']}")
        print(f"• Diagrammes visuels intégrés           : {mgmt['embedded_diagrams_count']}")
        print(f"• Termes de glossaire consolidés         : {mgmt['glossary_terms_count']}")

    else:
        print(f"1. Document Structure Completeness (DSC) : 🔴 0.0%")
        print(f"2. Traceability Preservation Rate (TPR)   : 🔴 0.0%")
        print(f"3. Diagram Embedding Validity (DEV)      : 🔴 0.0%")
        print(f"4. Glossary Format & Placement (GFF)     : 🔴 0.0%")
        print("-" * 75)
        print("📈 KPIs DE CONSOLIDATION ET MATURITÉ ÉDITORIALE")
        print("-" * 75)
        print("• STATUT D'EXPORTATION PDF               : 🔴 BLOCKED (DOC WRITER FAILED)")

    print("-" * 75)

    # 6. DIAGNOSTIC DU RAPPORT DE FIABILITÉ
    print("📝 ANALYSE DIAGNOSTIQUE DU PIPELINE ÉDITORIAL :")
    if not success or not doc_result:
        print("   ❌ Alerte : Échec de la génération ou de la validation Pydantic.")
    else:
        print("   ✅ Succès : Document Markdown généré avec succès.")

        if dsc_score < 100.0:
            print(f"   ⚠️ Attention : Certaines sections requises de la spécification sont manquantes ({dsc_score:.1f}%).")
        else:
            print("   ✅ Succès : Plan et structure 100% conformes à la spécification.")

        if tpr_score < 90.0:
            print(f"   ⚠️ Attention : Des identifiants atomiques (US, FR, Entités) ont été omis ({tpr_score:.1f}%).")
        else:
            print("   ✅ Succès : Traçabilité intégrale préservée (>90% d'ancres conservées).")

        if dev_score < 100.0:
            print(f"   ❌ Alerte : Des diagrammes Mermaid n'ont pas été insérés correctement.")
        else:
            print("   ✅ Succès : 100% des diagrammes intégrés sous forme de blocs ```mermaid.")

        if gff_score < 100.0:
            print(f"   ❌ Alerte : Problème de formatage du Glossaire (position non terminale ou absence de tableau).")
        else:
            print("   ✅ Succès : Glossaire terminal formaté en tableau Markdown parfait (GFF : 100%).")

    print("=" * 75)


if __name__ == "__main__":
    run_isolated_doc_writer_test()