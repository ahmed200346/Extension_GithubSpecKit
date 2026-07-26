# """
# test_parsing_agent.py — Validation isolée et évaluation par métriques de l'agent de parsing.
# """

# import os
# import sys
# import json
# from pathlib import Path

# from app.services.parser_service import run_parsing_agent
# from app.utils.markdown_parser import pre_parse_markdown_to_sections, calculate_file_hash
# from app.core.metrics import calculate_sar, calculate_sir, calculate_tfs, calculate_exr, extract_heuristic_questions

# # IMPORTATION DU SERVICE D'ÉVALUATION ISOLE
# from app.services.evaluation_service import ParsingEvaluatorService

# # ==============================================================================
# # CONFIGURATION : Spécifiez le fichier à évaluer
# # ==============================================================================
# TARGET_FILE_NAME = "spec(1).md"  
# TEMPLATE_FILE_NAME = "sdd_templates.json"
# # ==============================================================================

# def run_isolated_parsing_test():
#     backend_dir = Path(__file__).resolve().parent          # .../StageTalan/backend
#     project_root = backend_dir.parent                      # .../StageTalan
#     test_files_dir = project_root / "test_files"           # .../StageTalan/test_files
#     target_path = test_files_dir / TARGET_FILE_NAME
#     template_path = backend_dir / "app" / "resources" / TEMPLATE_FILE_NAME

#     print("=" * 75)
#     print("        TEST D'ÉVALUATION ET DE FIABILITÉ - PARSING AGENT")
#     print("=" * 75)

#     if not test_files_dir.exists():
#         print(f"[❌] Erreur : Le dossier '{test_files_dir}' n'existe pas.")
#         sys.exit(1)

#     if not target_path.exists():
#         print(f"[⚠️] Fichier '{TARGET_FILE_NAME}' introuvable dans '{test_files_dir.relative_to(project_root)}'.")
#         print("\n📂 Fichiers Markdown disponibles :")
#         for f in test_files_dir.glob("*.md"):
#             print(f"   - {f.name}")
#         sys.exit(1)

#     # 1. Lecture du fichier
#     with open(target_path, "r", encoding="utf-8") as f:
#         file_content = f.read()

#     # 2. Parsing déterministe (Python AST)
#     python_sections = pre_parse_markdown_to_sections(file_content)
#     file_hash = calculate_file_hash(file_content)

#     print(f"[📂] Fichier cible : {TARGET_FILE_NAME}")
#     print(f"[⚙️] Pré-découpage Python terminé : {len(python_sections)} sections isolées.")
#     print("-" * 75)

#     # 3. Exécution du LLM et calcul des métriques
#     print("[⌛] Analyse de l'Agent de Ingestion en cours (Gemma/Ollama)...")
    
#     parsed_doc = None
#     success = False
    
#     try:
#         parsed_doc = run_parsing_agent(
#             file_name=TARGET_FILE_NAME,
#             file_content=file_content
#         )
#         success = True
#         print("[OK] Réponse reçue et validée par Pydantic !\n")
        
#         # Sauvegarde physique du JSON sous le nom exact : constitution(1)_parsed.json
#         outputs_dir = test_files_dir / "outputs"
#         outputs_dir.mkdir(exist_ok=True)
#         output_json_path = outputs_dir / f"{Path(TARGET_FILE_NAME).stem}_parsed.json"
#         with open(output_json_path, "w", encoding="utf-8") as out_f:
#             out_f.write(parsed_doc.model_dump_json(indent=4))
#         print(f"[💾] JSON sauvegardé sous : {output_json_path.relative_to(project_root)}")

#     except Exception as e:
#         print(f"[❌] ÉCHEC DU PARSING : {e}")

#     # 4. ÉVALUATION DES MÉTRIQUES VIA LE SERVICE ISOLE (DASHBOARD MULTI-PROJETS)
#     print("\n" + "📊" + " " + "ÉVALUATION DES MÉTRIQUES DE FIABILITÉ (DASHBOARD)")
#     print("-" * 75)
    
#     sar_score, sir_score, tfs_score, exr_score = 0.0, 0.0, 0.0, 0.0
    
#     if success and parsed_doc:
#         # Chargement sécurisé du template de configuration
#         template_config = {}
#         if template_path.exists():
#             with open(template_path, 'r', encoding='utf-8') as f:
#                 template_config = json.load(f)
        
#         # Calcul des rapports d'évaluation (QA + Management KPIs)
#         report = ParsingEvaluatorService.evaluate(parsed_doc, template_config)
#         tech = report["technical_evaluation"]
#         mgmt = report["project_management_kpis"]
        
#         # Mapping des variables locales pour la Section 5 (Diagnostic d'origine)
#         sar_score = tech["schema_adherence_rate"]
#         sir_score = tech["structural_integrity_recall"]
#         tfs_score = tech["text_fidelity_score"]
#         exr_score = tech["extraction_recall"]
        
#         # Affichage des scores techniques
#         print(f"1. Schema Adherence Rate (SAR)      : {sar_score:.1f}%")
#         if tech['contradictions']:
#             print(f"   ⚠️ Contradictions détectées      : {tech['contradictions']}")
#         print(f"2. Structural Integrity Recall (SIR): {sir_score:.1f}%")
#         print(f"3. Text Fidelity Score (TFS)        : {tfs_score:.1f}%")
#         print(f"4. Extraction Recall (ExR)          : {exr_score:.1f}%")
#         print("-" * 75)
        
#         # Affichage des KPIs de Gestion de Projet
#         print("📈 KPIs DE GESTION DE PROJET (MANAGEMENT)")
#         print("-" * 75)
#         print(f"• Projet identifié                  : {report['project_name']}")
#         print(f"• Type de document déterminé        : {report['document_type'].upper()}")
#         print(f"• Taux de complétude du gabarit     : {mgmt['completeness_score']:.1f}%")
#         print(f"• INDICE DE SANTÉ DOCUMENTAIRE      : {mgmt['health_index']:.1f}/100")
        
#         status_colors = {
#             "READY_FOR_EXECUTION": "🟢 READY_FOR_EXECUTION",
#             "NEEDS_REFINEMENT": "🟡 NEEDS_REFINEMENT",
#             "BLOCKED": "🔴 BLOCKED"
#         }
#         print(f"• STATUT D'AVANCEMENT DU PROJET     : {status_colors.get(mgmt['readiness_status'])}")
#         print(f"• Synthèse des écarts (Gaps)        : Haute: {mgmt['gaps_summary']['high_severity']} | Moyenne: {mgmt['gaps_summary']['medium_severity']} | Basse: {mgmt['gaps_summary']['low_severity']}")
#         print(f"• Incertitudes non résolues (TBD)   : {mgmt['gaps_summary']['unresolved_uncertainties']}")
#     else:
#         # Affichage dégradé si le LLM échoue
#         print(f"1. Schema Adherence Rate (SAR)      : 0.0%")
#         print(f"2. Structural Integrity Recall (SIR): 0.0%")
#         print(f"3. Text Fidelity Score (TFS)        : 0.0%")
#         print(f"4. Extraction Recall (ExR)          : 0.0%")
#         print("-" * 75)
#         print("📈 KPIs DE GESTION DE PROJET (MANAGEMENT)")
#         print("-" * 75)
#         print("• STATUT D'AVANCEMENT DU PROJET     : 🔴 BLOCKED (PARSING FAILED)")
        
#     print("-" * 75)

#     # 5. DIAGNOSTIC DU RAPPORT DE FIABILITÉ (D'ORIGINE - NON MODIFIE)
#     print("📝 ANALYSE DIAGNOSTIQUE DU PIPELINE :")
    
#     if not success or not parsed_doc:
#         print("   ❌ Alerte : Le format de sortie du LLM a violé le schéma Pydantic.")
#         print("      Le traitement s'est arrêté pour empêcher la corruption des données.")
#     else:
#         print("   ✅ Succès : Schéma JSON 100% respecté.")
        
#         if sir_score < 100:
#             print(f"   ❌ Alerte : Le LLM a omis de copier {len(python_sections) - len(parsed_doc.sections)} sections.")
#         else:
#             print("   ✅ Succès : Aucune section n'a été perdue lors du transfert.")

#         if tfs_score < 99.0:
#             print(f"   ⚠️ Attention : Le modèle a altéré ou résumé des exigences (Fidélité : {tfs_score:.1f}%).")
#         else:
#             print("   ✅ Succès : Intégrité textuelle préservée (aucune reformulation).")

#         if exr_score < 100:
#             gt_questions = extract_heuristic_questions(file_content)
#             print(f"   ⚠️ Attention : {len(gt_questions) - len(parsed_doc.open_questions)} questions sources n'ont pas été identifiées.")
#             print(f"      - Questions réelles attendues ({len(gt_questions)}) :")
#             for q in gt_questions:
#                 print(f"        * {q}")
#             print(f"      - Questions réellement capturées ({len(parsed_doc.open_questions)}) :")
#             for q in parsed_doc.open_questions:
#                 print(f"        * {q}")
#         else:
#             print("   ✅ Succès : 100% des questions ouvertes identifiées.")

#     print("=" * 75)

# if __name__ == "__main__":
#     run_isolated_parsing_test()