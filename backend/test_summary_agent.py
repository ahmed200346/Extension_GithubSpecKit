# test_summary_agent.py
"""
test_summary_agent.py — Validation isolée et évaluation par métriques de l'agent de synthèse.
Version finale exploitant la topologie du graphe et les contraintes multi-échelles.
"""

import os
import sys
import json
from pathlib import Path

# Importations des services et schémas de l'application
from app.services.summary_service import SummaryAgentService
from app.services.evaluation_service import SummaryEvaluatorService
from app.schemas.summary_agent_schema import SummaryOutputModel
from app.schemas.parsing_agent_schema import ParsingAgentOutput

# ==============================================================================
# CONFIGURATION : Spécifiez le fichier parsé à évaluer
# ==============================================================================
TARGET_PARSED_NAME = "requirements(1)_parsed.json"  # Fichier généré par le Parser Agent
SPEC_FILE_NAME = "summary_spec.json"            # Fichier de spécification sémantique
# ==============================================================================

def run_isolated_summary_test():
    backend_dir = Path(__file__).resolve().parent          # .../StageTalan/backend
    project_root = backend_dir.parent                      # .../StageTalan
    test_files_dir = project_root / "test_files"           # .../StageTalan/test_files
    outputs_dir = test_files_dir / "outputs"               # .../StageTalan/test_files/outputs
    
    target_parsed_path = outputs_dir / TARGET_PARSED_NAME
    spec_path = backend_dir / "app" / "resources" / SPEC_FILE_NAME

    print("=" * 75)
    print("        TEST D'ÉVALUATION ET DE FIABILITÉ - SUMMARY AGENT")
    print("=" * 75)

    # Vérifications de l'existence des répertoires et fichiers cibles
    if not outputs_dir.exists():
        print(f"[❌] Erreur : Le dossier des sorties '{outputs_dir}' n'existe pas.")
        sys.exit(1)

    if not target_parsed_path.exists():
        print(f"[❌] Erreur : Le fichier parsé '{TARGET_PARSED_NAME}' est introuvable sous '{outputs_dir.relative_to(project_root)}'.")
        print("      Veuillez d'abord exécuter test_parsing_agent.py pour le générer.")
        sys.exit(1)

    # 1. Chargement du fichier JSON issu du Parsing Agent
    print(f"[📂] Lecture du fichier parsé : {TARGET_PARSED_NAME}")
    with open(target_parsed_path, "r", encoding="utf-8") as f:
        parsed_json_dict = json.load(f)

    # 2. Chargement de la spécification de synthèse (summary_spec.json)
    summary_spec_dict = {}
    if spec_path.exists():
        print(f"[⚙️] Spécification '{SPEC_FILE_NAME}' chargée avec succès.")
        with open(spec_path, "r", encoding="utf-8") as f:
            summary_spec_dict = json.load(f)
    else:
        print(f"[⚠️] Spécification '{SPEC_FILE_NAME}' introuvable. Utilisation d'un gabarit générique.")
        summary_spec_dict = {
            "executive_brief": "Synthèse macro de l'intention de l'application.",
            "maturity_assessment": "Évaluation objective de la viabilité."
        }

    print("-" * 75)

    # 3. Exécution de l'Agent Summary
    print("[⌛] Génération de la synthèse en cours (Analyse de la topologie du graphe)...")
    
    summary_doc = None
    success = False
    try:
        agent_service = SummaryAgentService() 
        summary_doc = agent_service.generate_summary(
            parsed_json_dict=parsed_json_dict,
            summary_spec_dict=summary_spec_dict
        )
        success = True
        print("[OK] Synthèse générée et validée par Pydantic !\n")
        
        # Sauvegarde physique de la synthèse
        output_summary_path = outputs_dir / f"{TARGET_PARSED_NAME.replace('_parsed.json', '_summary.json')}"
        with open(output_summary_path, "w", encoding="utf-8") as out_f:
            out_f.write(summary_doc.model_dump_json(indent=4))
        print(f"[💾] Synthèse sauvegardée sous : {output_summary_path.relative_to(project_root)}")

    except Exception as e:
        print(f"[❌] ÉCHEC DE LA SYNTHÈSE : {e}")

    # 4. ÉVALUATION DES MÉTRIQUES VIA LE SERVICE ISOLE (DASHBOARD)
    print("\n" + "📊" + " " + "ÉVALUATION DES MÉTRIQUES DE FIABILITÉ (DASHBOARD)")
    print("-" * 75)
    
    mas_score, cps_score, ecr_score = 0.0, 0.0, 0.0
    hallucinations_count = 0
    
    if success and summary_doc:
        # Reconstitution de l'objet d'entrée pour le croisement des données du validateur
        parsed_data_obj = ParsingAgentOutput(**parsed_json_dict)
        
        # Calcul des métriques de fiabilité (QA) et KPIs d'architecture
        report = SummaryEvaluatorService.evaluate(summary_doc, parsed_data_obj)
        tech = report["technical_evaluation"]
        mgmt = report["project_management_kpis"]
        
        mas_score = tech["maturity_alignment_score"]
        cps_score = tech["conciseness_precision_score"]
        ecr_score = tech["extraction_completeness_rate"]
        hallucinations_count = tech["hallucinations_detected_count"]
        
        # Affichage des scores de fiabilité technique (QA)
        print(f"1. Maturity Alignment Score (MAS)   : {mas_score:.1f}%")
        print(f"2. Conciseness & Precision Score(CPS): {cps_score:.1f}% (Nombre de mots : {tech['brief_word_count']})")
        print(f"3. Extraction Completeness Rate (ECR): {ecr_score:.1f}%")
        print("-" * 75)
        
        # Affichage des KPIs d'Architecture pour la Gestion de Projet
        print("📈 KPIs D'ARCHITECTURE ET PILOTAGE (TOPOLOGIE & CONTRÔLE)")
        print("-" * 75)
        print(f"• Projet identifié                  : {report['project_name']}")
        print(f"• Technologies clés extraites       : {mgmt['extracted_technologies_count']}")
        print(f"• Contraintes physiques identifiées : {mgmt['architectural_constraints_count']}")
        print(f"• Dépendances externes critiques    : {mgmt['external_dependencies_count']}")
        print(f"• Entités hallucinées détectées     : {hallucinations_count}")
        
        risk_colors = {
            "FAIBLE": "🟢 FAIBLE",
            "MODÉRÉ": "🟡 MODÉRÉ",
            "ÉLEVÉ": "🔴 ÉLEVÉ"
        }
        print(f"• NIVEAU D'EXPOSITION AUX RISQUES   : {risk_colors.get(mgmt['external_risk_exposure'], mgmt['external_risk_exposure'])}")
    else:
        print(f"1. Maturity Alignment Score (MAS)   : 0.0%")
        print(f"2. Conciseness & Precision Score(CPS): 0.0%")
        print(f"3. Extraction Completeness Rate (ECR): 0.0%")
        print("-" * 75)
        print("📈 KPIs D'ARCHITECTURE ET PILOTAGE")
        print("-" * 75)
        print("• NIVEAU D'EXPOSITION AUX RISQUES   : 🔴 CRITIQUE (SUMMARY FAILED)")
        
    print("-" * 75)

    # 5. DIAGNOSTIC DU RAPPORT DE FIABILITÉ
    print("📝 ANALYSE DIAGNOSTIQUE DU PIPELINE SYNTHÈSE :")
    
    if not success or not summary_doc:
        print("   ❌ Alerte : Le format de sortie du LLM a violé la structure Pydantic.")
        print("      Veuillez vérifier les logs d'erreurs Ollama ou resserrer le prompt.")
    else:
        print("   ✅ Succès : Schéma JSON 100% valide et intègre.")
        
        if hallucinations_count > 0:
            print(f"   ❌ Alerte : {hallucinations_count} entité(s) ou outil(s) ont été inventé(s) ou extrapolés hors graphe.")
        
        if mas_score < 100.0:
            print("   ❌ Alerte : Le LLM a contredit l'indice mathématique ou n'a pas pris en compte les gaps du Parser.")
            print("      Il a mal qualifié la maturité ou a omis de mentionner les écarts structurels.")
        else:
            print("   ✅ Succès : Cohérence parfaite du diagnostic de maturité (Alignement Multi-Agents).")

        if cps_score == 70.0:
            print("   ⚠️ Attention : L'Executive Brief est trop verbeux (> 150 mots).")
        elif cps_score == 60.0:
            print("   ⚠️ Attention : L'Executive Brief est trop court (< 30 mots) pour guider Claude Code.")
        else:
            print("   ✅ Succès : Densité d'information optimale (Concision préservée entre 30 et 150 mots).")

        if ecr_score < 100.0:
            print("   ⚠️ Attention : L'agent a laissé une de ses listes techniques obligatoire vide ou a subi des pénalités d'hallucination.")
        else:
            print("   ✅ Succès : Cartographie technique et dépendances 100% validées.")

    print("=" * 75)

if __name__ == "__main__":
    run_isolated_summary_test()
