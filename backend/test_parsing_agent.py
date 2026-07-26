# test_parsing_agent.py
"""
test_parsing_agent.py — Validation isolée et évaluation par métriques de l'agent de parsing.
Version enrichie prenant en compte la topologie des graphes et la traçabilité macro/micro.
"""

import os
import sys
import json
from pathlib import Path

from app.services.parser_service import run_parsing_agent
from app.utils.markdown_parser import pre_parse_markdown_to_sections, calculate_file_hash
from app.services.evaluation_service import ParsingEvaluatorService

# ==============================================================================
# CONFIGURATION : Spécifiez le fichier à évaluer
# ==============================================================================
TARGET_FILE_NAME = "constitution(1).md"  # Le fichier de la constitution
TEMPLATE_FILE_NAME = "sdd_templates.json"
# ==============================================================================

def run_isolated_parsing_test():
    backend_dir = Path(__file__).resolve().parent          # .../StageTalan/backend
    project_root = backend_dir.parent                      # .../StageTalan
    test_files_dir = project_root / "test_files"           # .../StageTalan/test_files
    target_path = test_files_dir / TARGET_FILE_NAME
    template_path = backend_dir / "app" / "resources" / TEMPLATE_FILE_NAME

    print("=" * 75)
    print("        TEST D'ÉVALUATION ET DE FIABILITÉ EN TERMINAL - PARSING AGENT")
    print("=" * 75)

    if not test_files_dir.exists():
        print(f"[❌] Erreur : Le dossier '{test_files_dir}' n'existe pas.")
        sys.exit(1)

    if not target_path.exists():
        print(f"[⚠️] Fichier '{TARGET_FILE_NAME}' introuvable dans '{test_files_dir.relative_to(project_root)}'.")
        print("\n📂 Fichiers Markdown disponibles :")
        for f in test_files_dir.glob("*.md"):
            print(f"   - {f.name}")
        sys.exit(1)

    # 1. Lecture du fichier
    with open(target_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    # 2. Parsing déterministe (Python AST)
    python_sections = pre_parse_markdown_to_sections(file_content)
    file_hash = calculate_file_hash(file_content)

    print(f"[📂] Fichier cible : {TARGET_FILE_NAME}")
    print(f"[⚙️] Pré-découpage Python terminé : {len(python_sections)} sections isolées.")
    
    # Affichage de l'arbre des sections détectées
    for sec in python_sections:
        if hasattr(sec, "title"):
            title = sec.title
            level = getattr(sec, "level", 1)
        elif isinstance(sec, dict):
            title = sec.get("title", "")
            level = sec.get("level", 1)
        else:
            title = str(sec)
            level = 1
            
        indent = "    " * (level - 1)
        connector = "└── " if level > 1 else "├── "
        print(f"    {indent}{connector}[H{level}] {title}")

    print("-" * 75)

    # 3. Exécution du LLM et calcul des métriques
    print("[⌛] Analyse hybride (Graphe + Gabarit) par l'Agent Ingestion en cours...")
    
    parsed_doc = None
    success = False
    
    try:
        parsed_doc = run_parsing_agent(
            file_name=TARGET_FILE_NAME,
            file_content=file_content
        )
        success = True
        print("[OK] Réponse reçue et validée par la structure Pydantic ultime !\n")
        
        # Sauvegarde physique du JSON sous le nom exact : constitution(1)_parsed.json
        outputs_dir = test_files_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        output_json_path = outputs_dir / f"{Path(TARGET_FILE_NAME).stem}_parsed.json"
        with open(output_json_path, "w", encoding="utf-8") as out_f:
            out_f.write(parsed_doc.model_dump_json(indent=4))
        print(f"[💾] JSON Sauvegardé sous : {output_json_path.relative_to(project_root)}")

    except Exception as e:
        print(f"[❌] ÉCHEC CRITIQUE DE VALIDATION DU SCHÉMA : {e}")

    # 4. ÉVALUATION DES MÉTRIQUES EN TERMINAL (DASHBOARD QUALITÉ ENRICHIE)
    print("\n" + "📊" + " " + "ÉVALUATION DES MÉTRIQUES DE FIABILITÉ ET LOGIQUE DE GRAPHE")
    print("-" * 75)
    
    sar_score, sir_score, gri_score, mmti_score, mtc_score = 0.0, 0.0, 0.0, 0.0, 0.0
    quality_alerts = []
    
    if success and parsed_doc:
        # Chargement sécurisé du template de configuration
        template_config = {}
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
        
        # Calcul des rapports d'évaluation via le nouveau service topologique
        report = ParsingEvaluatorService.evaluate(parsed_doc, template_config)
        tech = report["technical_evaluation"]
        mgmt = report["project_management_kpis"]
        
        # Extraction des nouvelles métriques topologiques
        sar_score = tech["schema_adherence_rate"]
        sir_score = tech["structural_integrity_recall"]
        gri_score = tech["graph_relational_integrity"]
        mmti_score = tech["macro_micro_traceability_index"]
        mtc_score = tech["model_template_conformity"]
        quality_alerts = tech["quality_alerts"]
        
        # Affichage des scores techniques
        print(f"1. Schema Adherence Rate (SAR)          : {sar_score:.1f}%")
        print(f"2. Structural Integrity Recall (SIR)    : {sir_score:.1f}%")
        print(f"3. Graph Relational Integrity (GRI)     : {gri_score:.1f}%")
        print(f"4. Macro-Micro Traceability Index (MMTI): {mmti_score:.1f}%")
        print(f"5. Model Template Conformity (MTC)      : {mtc_score:.1f}%")
        print("-" * 75)
        
        # Affichage des alertes qualité si existantes
        if quality_alerts:
            print("⚠️  ALERTES DE TRAÇABILITÉ ET LOGIQUE DÉTECTÉES :")
            for alert in quality_alerts:
                print(f"   • {alert}")
            print("-" * 75)
        
        # Affichage des KPIs de Gestion de Projet
        print("📈 KPIs DE GESTION DE PROJET (GOUVERNANCE MANAGÉRIALE)")
        print("-" * 75)
        print(f"• Identité du Projet                : {report['project_name']}")
        print(f"• Classification Documentaire       : {report['document_type'].upper()}")
        print(f"• Volume du Graphe Extrait          : {mgmt['extracted_metrics_summary']['total_nodes_extracted']} Nœds | {mgmt['extracted_metrics_summary']['total_edges_extracted']} Relations")
        print(f"• Taux de complétude des sections   : {mgmt['completeness_score']:.1f}%")
        print(f"• INDICE DE SANTÉ DOCUMENTAIRE      : {mgmt['health_index']:.1f}/100")
        
        status_colors = {
            "READY_FOR_EXECUTION": "🟢 READY_FOR_EXECUTION",
            "NEEDS_REFINEMENT": "🟡 NEEDS_REFINEMENT",
            "BLOCKED": "🔴 BLOCKED"
        }
        print(f"• JALON DE MATURITÉ (READINESS)     : {status_colors.get(mgmt['readiness_status'])}")
        print(f"• Analyse des écarts (Gaps)         : Haute: {mgmt['gaps_summary']['high_severity']} | Moyenne: {mgmt['gaps_summary']['medium_severity']} | Basse: {mgmt['gaps_summary']['low_severity']}")
        print(f"• Incertitudes non résolues (TBD)   : {mgmt['gaps_summary']['unresolved_uncertainties']}")
    else:
        print(f"1. Schema Adherence Rate (SAR)          : 0.0%")
        print(f"2. Structural Integrity Recall (SIR)    : 0.0%")
        print(f"3. Graph Relational Integrity (GRI)     : 0.0%")
        print(f"4. Macro-Micro Traceability Index (MMTI): 0.0%")
        print(f"5. Model Template Conformity (MTC)      : 0.0%")
        print("-" * 75)
        print("📈 KPIs DE GESTION DE PROJET (GOUVERNANCE MANAGÉRIALE)")
        print("-" * 75)
        print("• JALON DE MATURITÉ (READINESS)     : 🔴 BLOCKED (PARSING FAILED)")
        
    print("-" * 75)

    # 5. DIAGNOSTIC LOGIQUE DU PIPELINE DE PRODUCTION
    print("📝 ANALYSE DIAGNOSTIQUE DU PIPELINE DE COMPARAISON :")
    
    if not success or not parsed_doc:
        print("   ❌ Alerte Critique : Les contraintes de cohésion de l'agent ont été violées.")
        print("      Vérifie si le LLM n'a pas généré une contradiction logique ou un JSON corrompu.")
    else:
        print("   Resilience Check :")
        if sar_score == 100.0:
            print("   ✅ Parfait : Aucun mot vide (TBD/Todo) ou placeholder n'a pollué l'extraction.")
        else:
            print("   ⚠️  Attention : Présence de vide sémantique ou de troncatures paresseuses dans le texte.")

        print("   Structure & Topologie Check :")
        if sir_score == 100.0:
            print("   ✅ Parfait : L'intégralité de l'arborescence des chapitres d'origine a été conservée.")
        else:
            print("   ❌ Manquement : Certaines sections requises par le template manquent à l'appel.")

        if gri_score == 100.0:
            print("   ✅ Parfait : Intégrité relationnelle absolue. Toutes les relations pointent vers des nœuds réels.")
        else:
            print("   ❌ Erreur topologique : Des liens orphelins (arcs brisés) polluent le graphe de données.")

        if mmti_score == 100.0:
            print("   ✅ Parfait : Alignement bi-échelle total. 100% des micro-données sont ancrées dans une section physique.")
        else:
            print("   ⚠️  Défaut d'ancrage : Des éléments extraits flottent sans origine physique traçable.")

    print("=" * 75)

if __name__ == "__main__":
    run_isolated_parsing_test()
