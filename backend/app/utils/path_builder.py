from pathlib import Path
from typing import Dict, Optional

# 🎯 Racine du projet StageTalan/ (3 niveaux au-dessus de backend/app/utils)
BASE_DIR = Path(__file__).resolve().parents[3]

def extract_project_name_from_path(file_path: Path) -> str:
    """
    Extrait le nom du projet principal situé sous le dossier 'specs/'.
    Exemples :
    - specs/001-expense-tracker-cli/spec.md -> 001-expense-tracker-cli
    - specs/001-expense-tracker-cli/checklists/requirements.md -> 001-expense-tracker-cli
    - specs/spec(1).md -> spec(1)
    - specs/constitution.md -> constitution
    """
    parts = file_path.parts
    if "specs" in parts:
        idx = parts.index("specs")
        # Cas 1 : Fichier directement sous 'specs/' (ex: specs/spec(1).md)
        if idx + 1 == len(parts) - 1:
            return file_path.stem
        # Cas 2 : Fichier dans un sous-dossier sous 'specs/' (ex: specs/001-expense-tracker-cli/...)
        elif idx + 1 < len(parts) - 1:
            return parts[idx + 1]

    # Fallback si 'specs' n'est pas dans le chemin
    parent_name = file_path.parent.name
    if parent_name in ["specs", "", "."]:
        return file_path.stem
    return parent_name
# def extract_project_name_from_path(file_path: Path) -> str:
#     """
#     Extrait le nom du projet principal situé sous le dossier 'specs/'.
#     Exemples :
#     - specs/001-expense-tracker-cli/spec.md -> 001-expense-tracker-cli
#     - specs/001-expense-tracker-cli/checklists/requirements.md -> 001-expense-tracker-cli
#     """
#     parts = file_path.parts
#     if "specs" in parts:
#         idx = parts.index("specs")
#         # Le dossier projet est le dossier situé juste après 'specs'
#         if idx + 1 < len(parts) - 1:
#             return parts[idx + 1]

#     # Fallback si 'specs' n'est pas dans le chemin
#     parent_name = file_path.parent.name
#     if parent_name in ["specs", "", "."]:
#         return "default_project"
#     return parent_name


def build_pipeline_paths(
    file_name: str, 
    version_label: str = "1.0", 
    project_name: Optional[str] = None
) -> Dict[str, Path]:
    """
    Génère l'ensemble des répertoires et chemins absolus de sortie de la pipeline
    organisés PAR PROJET sous la structure isolée StageTalan/outputs/<nom_projet>/.
    """
    file_path = Path(file_name)
    stem = file_path.stem  # Ex: "spec" ou "requirements"

    # 1. Déduction automatique du projet principal (même dans des sous-dossiers comme checklists, plans, etc.)
    if not project_name:
        project_name = extract_project_name_from_path(file_path)

    # Préfixe de version (ex: "v1.0" -> "requirements_v1.0")
    clean_version = version_label if version_label.startswith("v") else f"v{version_label}"
    version_prefix = f"{stem}_{clean_version}"

    # 2. Arborescence isolée sous StageTalan/outputs/<project_name>/
    outputs_base = BASE_DIR / "outputs"
    project_output_dir = outputs_base / project_name

    data_dir = project_output_dir / "data"
    markdown_dir = project_output_dir / "markdowns"
    eval_dir = project_output_dir / "evaluations"
    pdf_dir = project_output_dir / "pdf"
    diagrams_dir = project_output_dir / "diagrams"

    # 3. Création automatique de tous les sous-répertoires requis
    for folder in [outputs_base, project_output_dir, data_dir, markdown_dir, eval_dir, pdf_dir, diagrams_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    # 4. Dictionnaire complet des chemins (Toutes les clés fonctionnelles conservées)
    return {
        # Préfixes et dossiers principaux
        "prefix": stem,
        "version_prefix": version_prefix,
        "base_output_dir": project_output_dir,
        "data_dir": data_dir,
        "markdown_dir": markdown_dir,
        "evaluations_dir": eval_dir,
        "pdf_dir": pdf_dir,
        "diagrams_dir": diagrams_dir,
        
        # Fichiers de données (StageTalan/outputs/<project_name>/data/)
        "parsed_json": data_dir / f"{version_prefix}_parsed.json",
        "summary_json": data_dir / f"{version_prefix}_summary.json",
        "glossary_json": data_dir / f"{version_prefix}_glossary.json",
        "diagrams_json": data_dir / f"{version_prefix}_diagrams.json",
        
        # Document Markdown (StageTalan/outputs/<project_name>/markdowns/)
        "doc_md": markdown_dir / f"{version_prefix}_doc.md",
        
        # Fichiers d'évaluation (StageTalan/outputs/<project_name>/evaluations/)
        "parsing_eval": eval_dir / f"{version_prefix}_parsing_eval.json",
        "summary_eval": eval_dir / f"{version_prefix}_summary_eval.json",
        "glossary_eval": eval_dir / f"{version_prefix}_glossary_eval.json",
        "diagram_eval": eval_dir / f"{version_prefix}_diagram_eval.json",
        "doc_eval": eval_dir / f"{version_prefix}_doc_eval.json",
        "layout_eval": eval_dir / f"{version_prefix}_layout_eval.json",
        
        # PDF Final (StageTalan/outputs/<project_name>/pdf/)
        "final_pdf": pdf_dir / f"{version_prefix}.pdf",
    }
# from pathlib import Path
# from typing import Dict, Optional

# # 🎯 Racine du projet StageTalan/ (3 niveaux au-dessus de backend/app/utils)
# BASE_DIR = Path(__file__).resolve().parents[3]


# def build_pipeline_paths(
#     file_name: str, 
#     version_label: str = "1.0", 
#     project_name: Optional[str] = None
# ) -> Dict[str, Path]:
#     """
#     Génère l'ensemble des répertoires et chemins absolus de sortie de la pipeline
#     organisés PAR PROJET sous la structure isolée StageTalan/outputs/<nom_projet>/.
#     """
#     file_path = Path(file_name)
#     stem = file_path.stem  # Ex: "spec" ou "requirements"

#     # 1. Déduction automatique du projet si non transmis (ex: nom du sous-dossier parent)
#     if not project_name:
#         project_name = file_path.parent.name
#         if project_name in ["specs", "", "."]:
#             project_name = "default_project"

#     # Préfixe de version (ex: "v1.0" -> "requirements_v1.0")
#     clean_version = version_label if version_label.startswith("v") else f"v{version_label}"
#     version_prefix = f"{stem}_{clean_version}"

#     # 2. Arborescence isolée sous StageTalan/outputs/<project_name>/
#     outputs_base = BASE_DIR / "outputs"
#     project_output_dir = outputs_base / project_name

#     data_dir = project_output_dir / "data"
#     markdown_dir = project_output_dir / "markdowns"
#     eval_dir = project_output_dir / "evaluations"
#     pdf_dir = project_output_dir / "pdf"
#     diagrams_dir = project_output_dir / "diagrams"

#     # 3. Création automatique de tous les sous-répertoires requis
#     for folder in [outputs_base, project_output_dir, data_dir, markdown_dir, eval_dir, pdf_dir, diagrams_dir]:
#         folder.mkdir(parents=True, exist_ok=True)

#     # 4. Dictionnaire complet des chemins (Toutes les clés fonctionnelles conservées)
#     return {
#         # Préfixes et dossiers principaux
#         "prefix": stem,
#         "version_prefix": version_prefix,
#         "base_output_dir": project_output_dir,
#         "data_dir": data_dir,
#         "markdown_dir": markdown_dir,
#         "evaluations_dir": eval_dir,
#         "pdf_dir": pdf_dir,
#         "diagrams_dir": diagrams_dir,
        
#         # Fichiers de données (StageTalan/outputs/<project_name>/data/)
#         "parsed_json": data_dir / f"{version_prefix}_parsed.json",
#         "summary_json": data_dir / f"{version_prefix}_summary.json",
#         "glossary_json": data_dir / f"{version_prefix}_glossary.json",
#         "diagrams_json": data_dir / f"{version_prefix}_diagrams.json",
        
#         # Document Markdown (StageTalan/outputs/<project_name>/markdowns/)
#         "doc_md": markdown_dir / f"{version_prefix}_doc.md",
        
#         # Fichiers d'évaluation (StageTalan/outputs/<project_name>/evaluations/)
#         "parsing_eval": eval_dir / f"{version_prefix}_parsing_eval.json",
#         "summary_eval": eval_dir / f"{version_prefix}_summary_eval.json",
#         "glossary_eval": eval_dir / f"{version_prefix}_glossary_eval.json",
#         "diagram_eval": eval_dir / f"{version_prefix}_diagram_eval.json",
#         "doc_eval": eval_dir / f"{version_prefix}_doc_eval.json",
#         "layout_eval": eval_dir / f"{version_prefix}_layout_eval.json",
        
#         # PDF Final (StageTalan/outputs/<project_name>/pdf/)
#         "final_pdf": pdf_dir / f"{version_prefix}.pdf",
#     }
