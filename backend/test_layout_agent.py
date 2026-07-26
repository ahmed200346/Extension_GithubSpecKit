# test_layout_agent.py
"""
test_layout_agent.py — Validation isolée et évaluation par métriques colorisées
du Layout Agent (Rendu & Design PDF).
Prend en entrée le document Markdown unifié de Doc Writer et compile le PDF final.
"""

import os
import sys
import json
from pathlib import Path

# Importations des services et schémas de l'application
from app.services.layout_service import LayoutAgentService
from app.services.evaluation_service import LayoutEvaluatorService
from app.schemas.layout_agent_schema import LayoutOutputModel, LayoutPublicationStatus

# ==============================================================================
# CONFIGURATION : Préfixe du fichier cible à évaluer (ex: "tasks(1)" ou "spec(1)")
# ==============================================================================
TARGET_PREFIX = "requirements(1)"  # Lit : test_files/outputs/markdowns/tasks(1)_doc.md
LAYOUT_SPEC_FILE_NAME = "layout_spec.json"  # Spécification de la charte graphique
# ==============================================================================


def get_metric_color_tag(score: float) -> str:
    """Attribue un émoji de couleur selon les seuils critiques de performance."""
    if score == 100.0:
        return "🟢"
    elif score >= 80.0:
        return "🟡"
    return "🔴"


def run_isolated_layout_agent_test():
    backend_dir = Path(__file__).resolve().parent          # .../StageTalan/backend
    project_root = backend_dir.parent                      # .../StageTalan
    test_files_dir = project_root / "test_files"           # .../StageTalan/test_files
    outputs_dir = test_files_dir / "outputs"               # .../StageTalan/test_files/outputs
    markdowns_dir = outputs_dir / "markdowns"              # .../StageTalan/test_files/outputs/markdowns
    documents_dir = outputs_dir / "documents"              # .../StageTalan/test_files/outputs/documents

    # Chemins des fichiers source et destination
    input_md_path = markdowns_dir / f"{TARGET_PREFIX}_doc.md"
    output_pdf_path = documents_dir / f"{TARGET_PREFIX}_spec.pdf"
    
    # Chemin de la ressource layout_spec.json
    spec_path = backend_dir / "app" / "resources" / LAYOUT_SPEC_FILE_NAME

    print("=" * 75)
    print("      TEST D'ÉVALUATION ET DE FIABILITÉ - LAYOUT AGENT (RENDU PDF)")
    print("=" * 75)

    # 1. Vérification du répertoire Markdown source
    if not markdowns_dir.exists():
        print(f"[❌] Erreur : Le dossier des fichiers Markdown source '{markdowns_dir}' n'existe pas.")
        sys.exit(1)

    # 2. Vérification et création du répertoire de sortie pour les PDF
    documents_dir.mkdir(parents=True, exist_ok=True)

    # 3. Chargement du document Markdown source généré par Doc Writer
    print(f"[📂] Chargement du document Markdown source : '{input_md_path.name}'")
    if not input_md_path.exists():
        print(f"[❌] Erreur : Fichier Markdown introuvable : {input_md_path}")
        print("     Veuillez exécuter le test du Documentation Writer Agent au préalable.")
        sys.exit(1)

    with open(input_md_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    # 4. Chargement de la charte graphique layout_spec.json
    layout_spec_dict = {}
    if spec_path.exists():
        print(f"[⚙️] Charte graphique '{LAYOUT_SPEC_FILE_NAME}' chargée avec succès.")
        with open(spec_path, "r", encoding="utf-8") as f:
            layout_spec_dict = json.load(f)
    else:
        print(f"[⚠️] Charte graphique '{LAYOUT_SPEC_FILE_NAME}' introuvable sous app/resources/.")

    print("-" * 75)

    # 5. Exécution du Layout Agent (Rendu visuel & Compilation PDF)
    print("[⌛] Conversion des diagrammes Mermaid et compilation du PDF en cours...")
    layout_result: LayoutOutputModel = None
    success = False

    try:
        service = LayoutAgentService()
        layout_result = service.process_layout_and_render(
            markdown_text=markdown_text,
            layout_spec_dict=layout_spec_dict,
            project_name=TARGET_PREFIX,
            output_pdf_path=str(output_pdf_path)
        )
        success = layout_result.pdf_generated
        
        if success:
            print("[OK] Fichier PDF généré et validé par Pydantic !\n")
            print(f"[💾] Document PDF sauvegardé sous : {output_pdf_path.relative_to(project_root)}")
        else:
            print("[❌] Échec de la compilation du PDF.")

    except Exception as e:
        print(f"[❌] ÉCHEC CRITIQUE DE LA GÉNÉRATION DU PDF : {e}")

    # 6. ÉVALUATION DES MÉTRIQUES VIA LE SERVICE ISOLÉ (DASHBOARD)
    print("\n📊 ÉVALUATION DES MÉTRIQUES DE FIABILITÉ VISUELLE & IMPRESSION (DASHBOARD)")
    print("-" * 75)

    rsr_score, dvr_score, pba_score, vor_score, scs_score = 0.0, 0.0, 0.0, 0.0, 0.0

    if success and layout_result:
        tech = layout_result.technical_evaluation
        mgmt = layout_result.project_management_kpis

        rsr_score = tech.get("render_success_rate", 0.0)
        dvr_score = tech.get("diagram_visual_render_rate", 0.0)
        pba_score = tech.get("page_budget_adherence", 0.0)
        vor_score = tech.get("visual_overflow_rate", 0.0)
        scs_score = tech.get("styling_consistency_score", 0.0)

        # Affichage des 5 métriques de fiabilité visuelle
        print(f"1. Render Success Rate (RSR)          : {get_metric_color_tag(rsr_score)} {rsr_score:.1f}%")
        print(f"2. Diagram Visual Render Rate (DVR)   : {get_metric_color_tag(dvr_score)} {dvr_score:.1f}%")
        print(f"3. Page Budget Adherence (PBA)         : {get_metric_color_tag(pba_score)} {pba_score:.1f}%")
        print(f"4. Visual Overflow Rate (VOR)         : {get_metric_color_tag(vor_score)} {vor_score:.1f}%")
        print(f"5. Styling Consistency Score (SCS)    : {get_metric_color_tag(scs_score)} {scs_score:.1f}%")
        print("-" * 75)

        # Affichage des KPIs de gestion
        print("📈 KPIs DE COMPILATION ET LIVRABILITÉ DOCUMENTAIRE")
        print("-" * 75)
        print(f"• Projet identifié                       : {layout_result.project_name}")

        status_colors = {
            "READY_FOR_PUBLICATION": "🟢 READY_FOR_PUBLICATION (PDF certifié conforme et imprimable)",
            "NEEDS_REFINEMENT": "🟡 NEEDS_REFINEMENT (Dépassements légers de marge ou mise en page à ajuster)",
            "BLOCKED": "🔴 BLOCKED (Erreur critique de compilation PDF ou débordement majeur)"
        }
        status_val = layout_result.layout_publication_status.value if hasattr(layout_result.layout_publication_status, 'value') else str(layout_result.layout_publication_status)
        print(f"• STATUT DE PUBLICATION PDF              : {status_colors.get(status_val, status_val)}")
        print(f"• Nombre total de pages générées         : {layout_result.page_count} pages")
        print(f"• Taille du fichier PDF                  : {layout_result.file_size_kb:.1f} Ko")
        print(f"• Diagrammes Mermaid convertis en images : {layout_result.rendered_diagrams_count}")
        print(f"• Événements de débordement détectés      : {mgmt.get('overflow_events_detected_count', 0)}")

    else:
        print(f"1. Render Success Rate (RSR)          : 🔴 0.0%")
        print(f"2. Diagram Visual Render Rate (DVR)   : 🔴 0.0%")
        print(f"3. Page Budget Adherence (PBA)         : 🔴 0.0%")
        print(f"4. Visual Overflow Rate (VOR)         : 🔴 0.0%")
        print(f"5. Styling Consistency Score (SCS)    : 🔴 0.0%")
        print("-" * 75)
        print("📈 KPIs DE COMPILATION ET LIVRABILITÉ DOCUMENTAIRE")
        print("-" * 75)
        print("• STATUT DE PUBLICATION PDF              : 🔴 BLOCKED (LAYOUT AGENT FAILED)")

    print("-" * 75)

    # 7. DIAGNOSTIC DU RAPPORT DE FIABILITÉ VISUELLE
    print("📝 ANALYSE DIAGNOSTIQUE DU PIPELINE DU RENDU :")
    if not success or not layout_result:
        print("   ❌ Alerte : Échec de la compilation du PDF.")
    else:
        print("   ✅ Succès : Compilation PDF effectuée sans erreur binaire.")

        if dvr_score < 100.0:
            print(f"   ⚠️ Attention : Certains schémas Mermaid n'ont pas pu être convertis en images ({dvr_score:.1f}%).")
        else:
            print("   ✅ Succès : 100% des diagrammes Mermaid convertis et insérés dans le PDF.")

        if vor_score < 90.0:
            print(f"   ⚠️ Attention : Risque de débordement texte/tableau détecté hors des marges A4 ({vor_score:.1f}%).")
        else:
            print("   ✅ Succès : Alignement spatial parfait, aucun débordement de marge.")

        if pba_score < 80.0:
            print(f"   ⚠️ Attention : Le volume de pages dévie du budget théorique attendu ({pba_score:.1f}%).")
        else:
            print("   ✅ Succès : Densité documentaire optimale et respect du budget de pages.")

        if scs_score < 100.0:
            print(f"   ⚠️ Attention : La charte graphique n'a été que partiellement appliquée ({scs_score:.1f}%).")
        else:
            print("   ✅ Succès : Charte graphique et en-têtes 100% conformes à layout_spec.json.")

    print("=" * 75)


if __name__ == "__main__":
    run_isolated_layout_agent_test()