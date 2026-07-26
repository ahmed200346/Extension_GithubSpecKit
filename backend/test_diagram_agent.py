# test_diagram_agent.py
import asyncio
import json
import sys
from pathlib import Path

# Importations des composants du projet
from app.services.diagram_service import DiagramAgentService
from app.utils.diagram_tools import DiagramExporterTool
from app.services.evaluation_service import DiagramEvaluatorService
from app.schemas.parsing_agent_schema import ParsingAgentOutput

# Répertoire du script actuel (backend/)
SCRIPT_DIR = Path(__file__).resolve().parent

# 1. Détection dynamique du dossier test_files/outputs
# On teste si test_files est au niveau local (backend/test_files) ou au niveau parent (StageTalan/test_files)
if (SCRIPT_DIR / "test_files").exists():
    ROOT_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR.parent  # Remonte à StageTalan/

OUTPUTS_DIR = ROOT_DIR / "test_files" / "outputs"
SPEC_PATH = SCRIPT_DIR / "app" / "resources" / "diagram_spec.json"


def resolve_parsed_file(outputs_dir: Path, user_input: str) -> Path:
    """Recherche intelligente du fichier JSON dans le dossier outputs/."""
    target_path = outputs_dir / user_input
    if target_path.exists():
        return target_path

    clean_input = user_input.replace(" ", "").lower()
    for file in outputs_dir.glob("*.json"):
        clean_filename = file.name.replace(" ", "").lower()
        if clean_filename == clean_input or clean_input in clean_filename:
            return file

    return target_path


async def main():
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "constitution(1)_parsed.json"
    parsed_file_path = resolve_parsed_file(OUTPUTS_DIR, target_arg)

    print("\n" + "=" * 80)
    print(f"🚀 TEST DU DIAGRAM AGENT SUR : {parsed_file_path.name}")
    print(f"📂 Chemin d'accès détecté : {parsed_file_path}")
    print("=" * 80 + "\n")

    # 1. Vérification du fichier spec
    if not SPEC_PATH.exists():
        print(f"❌ Erreur : Fichier diagram_spec.json introuvable à :\n   {SPEC_PATH}")
        return

    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        diagram_spec = json.load(f)

    # 2. Vérification du fichier JSON parsé
    if not parsed_file_path.exists():
        print(f"❌ Erreur : Impossible de trouver le fichier : {parsed_file_path.name}\n")
        print(f"📋 Fichiers réellement disponibles dans {OUTPUTS_DIR} :")
        if OUTPUTS_DIR.exists():
            for jf in OUTPUTS_DIR.glob("*.json"):
                print(f"   • {jf.name}")
        return

    with open(parsed_file_path, "r", encoding="utf-8") as f:
        parsed_json_data = json.load(f)

    # 3. Inférence du Diagram Agent
    print("🧠 Inférence du Diagram Agent (Appel LLM)...")
    service = DiagramAgentService()
    diagram_output = service.generate_diagrams(
        parsed_json_dict=parsed_json_data,
        diagram_spec_dict=diagram_spec
    )

    print(f"✅ {len(diagram_output.diagrams)} diagramme(s) généré(s) avec succès.\n")

    for i, diag in enumerate(diagram_output.diagrams, 1):
        print(f"--- [Diagramme {i}] : {diag.title} ({diag.type}) ---")
        print(f"Description : {diag.description}")
        print("Code Mermaid :")
        print(diag.mermaid_code)
        print("-" * 60 + "\n")

    # 4. Rendu et exportation en PDF
    print("🎨 Rendu graphique (mmdc) et compilation PDF...")
    try:
        diagrams_dict = diagram_output.model_dump()
        file_stem = parsed_file_path.stem
        pdf_path = await DiagramExporterTool.render_diagrams_to_pdf(
            file_stem=file_stem,
            diagrams_data=diagrams_dict
        )
        print(f"📄 Fichier PDF généré avec succès : {pdf_path}\n")
    except Exception as exc:
        print(f"⚠️ Erreur lors du rendu PDF : {exc}\n")

    # 5. Évaluation globale via DiagramEvaluatorService
    print("📊 Calcul des Métriques de Qualité...")
    parsed_model = ParsingAgentOutput(**parsed_json_data)
    evaluation = DiagramEvaluatorService.evaluate(
        diagram_data=diagram_output,
        parsed_data=parsed_model
    )

    tech_eval = evaluation["technical_evaluation"]
    kpis = evaluation["project_management_kpis"]

    print("\n" + "=" * 80)
    print("📈 RAPPORT D'ÉVALUATION DU DIAGRAM AGENT")
    print("=" * 80)
    print(f"Projet           : {evaluation['project_name']}")
    print(f"Statut Rendu     : {evaluation['diagram_rendering_status']}")
    print("-" * 80)
    print("MÉTRIQUES TECHNIQUES (QA) :")
    print(f"  • SVR (Syntax Validity Rate)         : {tech_eval['syntax_validity_rate']}%")
    print(f"  • DCR (Diagram Coverage Rate)        : {tech_eval['diagram_coverage_rate']}%")
    print(f"  • RCR (Relational Completeness Rate) : {tech_eval['relational_completeness_rate']}%")
    print(f"  • SRA (Structural Rule Adherence)   : {tech_eval['structural_rule_adherence']}%")
    print("-" * 80)
    print("KPIs MANAGEMENT :")
    print(f"  • Total Diagrammes Générés          : {kpis['total_generated_diagrams']}")
    print(f"  • Ventilation par Types             : {kpis['diagram_types_breakdown']}")
    print(f"  • Total Lignes Mermaid             : {kpis['total_mermaid_lines_count']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
# # test_diagram_agent.py
# import asyncio
# import json
# from pathlib import Path

# # Importations des composants du projet
# from app.services.diagram_service import DiagramAgentService
# from app.utils.diagram_tools import DiagramExporterTool
# from app.services.evaluation_service import DiagramEvaluatorService
# from app.schemas.parsing_agent_schema import ParsingAgentOutput

# # Chemins des fichiers de ressources et de test
# BASE_DIR = Path(__file__).resolve().parent
# SPEC_PATH = BASE_DIR / "app" / "resources" / "diagram_spec.json"

# # Exemple de graphe topologique issu du Parsing Agent (mock / fixture pour test)
# MOCK_PARSED_JSON = {
#     "parsing_rationale": "Parsing complet du projet CourseHub API.",
#     "project_info": {
#         "project_name": "CourseHub API",
#         "source_type": "scratch",
#         "brief_explanation": "Système de gestion de cours en ligne",
#         "source_context": "Spécification technique de la plateforme"
#     },
#     "doc_type": "spec",
#     "sections": [
#         {
#             "title": "1. System Architecture & Data Model",
#             "level": 2,
#             "raw_content": "The system uses PostgreSQL for persistence with User, Course, and Enrollment entities.",
#             "mapped_to_template_field": "system_architecture"
#         },
#         {
#             "title": "2. Course Management Workflow",
#             "level": 2,
#             "raw_content": "Instructors create courses, add modules, validate content, and publish.",
#             "mapped_to_template_field": "workflows"
#         }
#     ],
#     "elements": [
#         {
#             "type": "ENTITY",
#             "identifier": "USER_ENTITY",
#             "content": "User account containing int id PK, string email, and string role",
#             "source_section": "1. System Architecture & Data Model",
#             "attributes": {"fields": "id, email, role"}
#         },
#         {
#             "type": "ENTITY",
#             "identifier": "COURSE_ENTITY",
#             "content": "Course entity containing int id PK, string title, and string status",
#             "source_section": "1. System Architecture & Data Model",
#             "attributes": {"fields": "id, title, status"}
#         },
#         {
#             "type": "ENDPOINT",
#             "identifier": "POST_COURSES",
#             "content": "POST /api/v1/courses - Instructor creates a new course",
#             "source_section": "2. Course Management Workflow",
#             "attributes": {"method": "POST", "path": "/api/v1/courses"}
#         },
#         {
#             "type": "USER_STORY",
#             "identifier": "US_01",
#             "content": "As an Instructor, I want to create and publish a course",
#             "source_section": "2. Course Management Workflow",
#             "attributes": {}
#         }
#     ],
#     "relationships": [
#         {
#             "source": "USER_ENTITY",
#             "to": "COURSE_ENTITY",
#             "relation_type": "contains"
#         },
#         {
#             "source": "US_01",
#             "to": "POST_COURSES",
#             "relation_type": "implements"
#         }
#     ],
#     "structural_gaps": [],
#     "open_questions": []
# }


# async def main():
#     print("\n" + "=" * 80)
#     print("🚀 LANCEMENT DU TEST AUTONOME POUR LE DIAGRAM AGENT")
#     print("=" * 80 + "\n")

#     # 1. Chargement de la spécification
#     if not SPEC_PATH.exists():
#         print(f"❌ Erreur : Fichier {SPEC_PATH} introuvable.")
#         return

#     with open(SPEC_PATH, "r", encoding="utf-8") as f:
#         diagram_spec = json.load(f)

#     # 2. Instanciation du service et génération des diagrammes
#     print("🧠 Inférence du Diagram Agent (Appel LLM)...")
#     service = DiagramAgentService()
#     diagram_output = service.generate_diagrams(
#         parsed_json_dict=MOCK_PARSED_JSON,
#         diagram_spec_dict=diagram_spec
#     )

#     print(f"✅ {len(diagram_output.diagrams)} diagramme(s) généré(s) avec succès.\n")

#     # Affichage du code Mermaid généré
#     for i, diag in enumerate(diagram_output.diagrams, 1):
#         print(f"--- [Diagramme {i}] : {diag.title} ({diag.type}) ---")
#         print(f"Description : {diag.description}")
#         print("Code Mermaid :")
#         print(diag.mermaid_code)
#         print("-" * 60 + "\n")

#     # 3. Rendu et exportation en fichier PDF
#     print("🎨 Génération des planches PNG et compilation du PDF...")
#     try:
#         diagrams_dict = diagram_output.model_dump()
#         pdf_path = await DiagramExporterTool.render_diagrams_to_pdf(
#             file_stem="coursehub_spec",
#             diagrams_data=diagrams_dict
#         )
#         print(f"📄 Fichier PDF généré avec succès : {pdf_path}\n")
#     except Exception as exc:
#         print(f"⚠️ Erreur lors du rendu PDF : {exc}\n")

#     # 4. Évaluation globale via DiagramEvaluatorService
#     print("📊 Évaluation des Métriques de Fiabilité & Qualité...")
#     parsed_model = ParsingAgentOutput(**MOCK_PARSED_JSON)
#     evaluation = DiagramEvaluatorService.evaluate(
#         diagram_data=diagram_output,
#         parsed_data=parsed_model
#     )

#     # Display Rapport
#     tech_eval = evaluation["technical_evaluation"]
#     kpis = evaluation["project_management_kpis"]

#     print("\n" + "=" * 80)
#     print("📈 RAPPORT D'ÉVALUATION DU DIAGRAM AGENT")
#     print("=" * 80)
#     print(f"Projet           : {evaluation['project_name']}")
#     print(f"Statut Rendu     : {evaluation['diagram_rendering_status']}")
#     print("-" * 80)
#     print("MÉTRIQUES TECHNIQUES (QA) :")
#     print(f"  • SVR (Syntax Validity Rate)         : {tech_eval['syntax_validity_rate']}%")
#     print(f"  • DCR (Diagram Coverage Rate)        : {tech_eval['diagram_coverage_rate']}%")
#     print(f"  • RCR (Relational Completeness Rate) : {tech_eval['relational_completeness_rate']}%")
#     print(f"  • SRA (Structural Rule Adherence)   : {tech_eval['structural_rule_adherence']}%")
#     print("-" * 80)
#     print("KPIs MANAGEMENT :")
#     print(f"  • Total Diagrammes Générés          : {kpis['total_generated_diagrams']}")
#     print(f"  • Ventilation par Types             : {kpis['diagram_types_breakdown']}")
#     print(f"  • Total Lignes Mermaid             : {kpis['total_mermaid_lines_count']}")
#     print(f"  • Moyenne Lignes / Diagramme        : {kpis['average_lines_per_diagram']}")
#     print("=" * 80 + "\n")


# if __name__ == "__main__":
#     asyncio.run(main())