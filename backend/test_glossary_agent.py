# test_glossary_agent.py
"""
test_glossary_agent.py — Validation isolée et évaluation par métriques colorisées de l'agent de glossaire sémantique.
Version finale synchronisée avec la topologie multi-échelles et les indices d'ancrage.
"""

import os
import sys
import json
from pathlib import Path

# Importations des services, outils et schémas de l'application
from app.services.glossary_service import GlossaryAgentService
from app.services.evaluation_service import GlossaryEvaluatorService
from app.utils.glossary_tools import GlossaryHarvesterService
from app.schemas.glossary_agent_schema import GlossaryOutputModel
from app.schemas.parsing_agent_schema import ParsingAgentOutput

# ==============================================================================
# CONFIGURATION : Spécifiez le fichier parsé à évaluer
# ==============================================================================
TARGET_PARSED_NAME = "tasks(1)_parsed.json"  # Fichier généré par le Parser Agent
SPEC_FILE_NAME = "glossary_spec.json"     # Spécification sémantique enrichie
# ==============================================================================

def get_metric_color_tag(score: float) -> str:
    """Attribue un émoji de couleur selon les seuils critiques de performance."""
    if score == 100.0:
        return "🟢"
    elif score >= 80.0:
        return "🟡"
    return "🔴"

def run_isolated_glossary_test():
    backend_dir = Path(__file__).resolve().parent          # .../StageTalan/backend
    project_root = backend_dir.parent                      # .../StageTalan
    test_files_dir = project_root / "test_files"           # .../StageTalan/test_files
    outputs_dir = test_files_dir / "outputs"               # .../StageTalan/test_files/outputs
    
    target_parsed_path = outputs_dir / TARGET_PARSED_NAME
    spec_path = backend_dir / "app" / "resources" / SPEC_FILE_NAME

    print("=" * 75)
    print("        TEST D'ÉVALUATION ET DE FIABILITÉ - GLOSSARY AGENT")
    print("=" * 75)

    # Vérifications de l'existence des répertoires et fichiers cibles
    if not outputs_dir.exists():
        print(f"[❌] Erreur : Le dossier des sorties '{outputs_dir}' n'existe pas.")
        sys.exit(1)

    if not target_parsed_path.exists():
        print(f"[❌] Erreur : Le fichier parsé '{TARGET_PARSED_NAME}' est introuvable sous '{outputs_dir.relative_to(project_root)}'.")
        sys.exit(1)

    # 1. Chargement du fichier JSON issu du Parsing Agent
    print(f"[📂] Lecture du fichier parsé : {TARGET_PARSED_NAME}")
    with open(target_parsed_path, "r", encoding="utf-8") as f:
        parsed_json_dict = json.load(f)

    # 2. Chargement de la spécification de glossaire (glossary_spec.json)
    glossary_spec_dict = {}
    if spec_path.exists():
        print(f"[⚙️] Spécification '{SPEC_FILE_NAME}' chargée avec succès.")
        with open(spec_path, "r", encoding="utf-8") as f:
            glossary_spec_dict = json.load(f)
    else:
        print(f"[⚠️] Spécification '{SPEC_FILE_NAME}' introuvable. Gabarit par défaut actif.")
        glossary_spec_dict = {"core_mission": "Extract terms.", "validation_contract": {}}

    # 3. Génération du cache topologique et récolte déterministe des termes candidats
    valid_anchors = GlossaryHarvesterService.generate_and_cache_anchors(parsed_json_dict)
    candidate_terms = GlossaryHarvesterService.harvest_candidates(parsed_json_dict)
    
    print(f"[🔍] Outil Harvester : {len(candidate_terms)} termes critiques identifiés sémantiquement.")
    print(f"[💾] Cache Topologique : {len(valid_anchors)} ancres valides sauvegardées sous backend/ressources/.")
    print("-" * 75)

    # 4. Exécution de l'Agent Glossary
    print("[⌛] Génération du glossaire en cours (Gemma/Ollama via Client centralisé)...")
    glossary_doc = None
    success = False
    
    try:
        agent_service = GlossaryAgentService()
        # Passage des données du cache (valid_anchors) à la méthode de génération
        glossary_doc = agent_service.generate_glossary(
            parsed_json_dict=parsed_json_dict,
            glossary_spec_dict=glossary_spec_dict,
            valid_anchors=valid_anchors
        )
        success = True
        print("[OK] Glossaire généré et validé par Pydantic !\n")
        
        # Sauvegarde physique du glossaire
        output_glossary_path = outputs_dir / f"{TARGET_PARSED_NAME.replace('_parsed.json', '_glossary.json')}"
        with open(output_glossary_path, "w", encoding="utf-8") as out_f:
            out_f.write(glossary_doc.model_dump_json(indent=4))
        print(f"[💾] Glossaire sauvegardé sous : {output_glossary_path.relative_to(project_root)}")

    except Exception as e:
        print(f"[❌] ÉCHEC DE LA GÉNÉRATION DU GLOSSAIRE : {e}")

    # 5. ÉVALUATION DES MÉTRIQUES VIA LE SERVICE ISOLE (DASHBOARD)
    print("\n📊 ÉVALUATION DES MÉTRIQUES DE FIABILITÉ (DASHBOARD)")
    print("-" * 75)
    
    tcr_score, car_score, dps_score, ata_score, cap_score = 0.0, 0.0, 0.0, 0.0, 0.0
    
    if success and glossary_doc:
        # Reconstitution de l'objet d'entrée pour le croisement des données du validateur
        parsed_data_obj = ParsingAgentOutput(**parsed_json_dict)
        
        # Calcul des métriques de fiabilité (QA) et KPIs sémantiques
        report = GlossaryEvaluatorService.evaluate(glossary_doc, parsed_data_obj, candidate_terms)
        tech = report["technical_evaluation"]
        mgmt = report["project_management_kpis"]
        
        tcr_score = tech["term_coverage_rate"]
        car_score = tech["categorization_accuracy_rate"]
        dps_score = tech["definition_precision_score"]
        ata_score = tech["anti_tautology_adherence"]
        cap_score = tech["contextual_anchor_precision"]
        
        # Affichage étendu des 5 métriques de fiabilité technique (QA)
        print(f"1. Term Coverage Rate (TCR)        : {get_metric_color_tag(tcr_score)} {tcr_score:.1f}%")
        print(f"2. Categorization Accuracy (CAR)    : {get_metric_color_tag(car_score)} {car_score:.1f}%")
        print(f"3. Definition Precision Score (DPS) : {get_metric_color_tag(dps_score)} {dps_score:.1f}%")
        print(f"4. Anti-Tautology Adherence (ATA)   : {get_metric_color_tag(ata_score)} {ata_score:.1f}%")
        print(f"5. Contextual Anchor Precision (CAP): {get_metric_color_tag(cap_score)} {cap_score:.1f}%")
        print("-" * 75)
        
        # Affichage des KPIs Sémantiques pour la Gestion de Projet
        print("📈 KPIs D'ARCHITECTURE ET ANCRAGE SÉMANTIQUE")
        print("-" * 75)
        print(f"• Projet identifié                  : {report['project_name']}")
        
        status_colors = {
            "READY_FOR_ANCHORING": "🟢 READY_FOR_ANCHORING (Aucun blocage topologique)",
            "NEEDS_REFINEMENT": "🟡 NEEDS_REFINEMENT (Qualité intermédiaire nécessitant révision)",
            "BLOCKED": "🔴 BLOCKED (Échec critique ou ruptures d'ancrage lourdes)"
        }
        print(f"• ANCRAGE SÉMANTIQUE GLOBAL         : {status_colors.get(report['semantic_anchoring_status'])}")
        print(f"• Total des termes documentés       : {mgmt['total_extracted_terms']}")
        print(f"• Termes métiers (Domain Objects)   : {mgmt['business_domain_terms_count']}")
        print(f"• Couche technique (Stack & Infra)  : {mgmt['technical_stack_terms_count']}")
        print(f"• Standards explicites capturés     : {mgmt['explicit_terms_count']}")
        print(f"• Standards implicites déduits      : {mgmt['implicit_terms_inferred_count']}")
    else:
        print(f"1. Term Coverage Rate (TCR)        : 🔴 0.0%")
        print(f"2. Categorization Accuracy (CAR)    : 🔴 0.0%")
        print(f"3. Definition Precision Score (DPS) : 🔴 0.0%")
        print(f"4. Anti-Tautology Adherence (ATA)   : 🔴 0.0%")
        print(f"5. Contextual Anchor Precision (CAP): 🔴 0.0%")
        print("-" * 75)
        print("📈 KPIs D'ARCHITECTURE ET ANCRAGE SÉMANTIQUE")
        print("-" * 75)
        print("• ANCRAGE SÉMANTIQUE GLOBAL         : 🔴 BLOCKED (GLOSSARY FAILED)")
        
    print("-" * 75)

    # 6. DIAGNOSTIC DU RAPPORT DE FIABILITÉ
    print("📝 ANALYSE DIAGNOSTIQUE DU PIPELINE GLOSSAIRE :")
    if not success or not glossary_doc:
        print("   ❌ Alerte : Le format de sortie du LLM a violé la structure Pydantic.")
    else:
        print("   ✅ Succès : Schéma JSON 100% valide et intègre.")
        
        if tcr_score < 90.0:
            print(f"   ⚠️ Attention : Le LLM a omis des termes identifiés par le Harvester sémantique ({tcr_score:.1f}%).")
        else:
            print("   ✅ Succès : Alignement de couverture optimal (>90%). Zéro omission critique.")

        if car_score < 100.0:
            print(f"   ❌ Alerte : Le modèle a commis {int(tech.get('classification_errors_count', 0))} erreur(s) d'étagement d'architecture.")
        else:
            print("   ✅ Succès : Classification rigoureuse des couches logicielle et métier (CAR : 100%).")

        # Extraction dynamique et affichage du compteur exact des violations ATA
        if ata_score < 100.0:
            violations = tech.get("tautology_violations_count", 1)
            print(f"   ❌ Alerte : {int(violations)} violation(s) anti-tautologie interceptée(s) dans les définitions.")
        else:
            print("   ✅ Succès : Définitions à haute densité opérationnelle (zéro redondance tautologique).")

        if cap_score < 100.0:
            print(f"   ❌ Alerte : Défaut d'ancrage géométrique détecté. Des termes pointent vers des identifiants invalides.")
        else:
            print("   ✅ Succès : Traçabilité géométrique parfaite (100% des ancres sont valides et mappées).")

        if tech.get("language_drift_detected", False):
            print("   ❌ Alerte : Dérive linguistique détectée (mots français présents dans les définitions).")
        else:
            print("   ✅ Succès : Strict respect de la gouvernance linguistique (100% English technique).")

    print("=" * 75)

if __name__ == "__main__":
    run_isolated_glossary_test()
