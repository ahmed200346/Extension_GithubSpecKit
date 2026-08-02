from pathlib import Path
from typing import Dict, Optional, Any

# 🎯 Racine du projet StageTalan/ (3 niveaux au-dessus de backend/app/utils)
BASE_DIR = Path(__file__).resolve().parents[3]


def sanitize_path_string(path_str: str) -> str:
    """
    Nettoyage preventif de TOUS les caracteres de controle ASCII (0x00-0x1F)
    et remplacement des backslashes Windows par des slashes POSIX.
    """
    clean_str = str(path_str)
    # 1. Remplacement des backslashes par des slashes EN PREMIER
    #    pour empecher les sequences \00x d'etre interpretees comme echappements octaux
    clean_str = clean_str.replace("\\", "/")
    # 2. Nettoyage de TOUS les caracteres de controle ASCII (0x00-0x1F)
    for i in range(0, 32):
        clean_str = clean_str.replace(chr(i), "")
    return clean_str


def extract_project_name_from_path(file_path: Path) -> str:
    """
    Extrait le nom du projet principal situe sous le dossier 'specs/'.
    
    Exemples :
    - specs/001-expense-tracker-cli/spec.md -> 001-expense-tracker-cli
    - specs/001-expense-tracker-cli/checklists/requirements.md -> 001-expense-tracker-cli
    - specs/spec(1).md -> spec(1)
    - specs/constitution.md -> constitution
    """
    # 1. Conversion POSIX stricte du chemin d'entree
    file_path = Path(file_path)
    posix_str = file_path.as_posix()
    posix_parts = posix_str.split("/")
    
    # 2. Localiser le dossier 'specs'
    if "specs" in posix_parts:
        idx = posix_parts.index("specs")
        
        # Cas 1 : Fichier directement sous 'specs/' (ex: specs/spec(1).md)
        if idx + 1 == len(posix_parts) - 1:
            # Nettoyer le stem du fichier (peut contenir des caracteres de controle)
            return sanitize_path_string(file_path.stem)
        
        # Cas 2 : Fichier dans un sous-dossier sous 'specs/' (ex: specs/001-notification-service-api/spec.md)
        elif idx + 1 < len(posix_parts) - 1:
            project_folder = posix_parts[idx + 1]
            # Nettoyage du nom du projet (au cas ou il contienne des sequences d'echappement)
            return sanitize_path_string(project_folder)

    # 3. Fallback si 'specs' n'est pas trouve dans le chemin
    parent_name = file_path.parent.name
    if parent_name in ["specs", "", "."]:
        return sanitize_path_string(file_path.stem)
    return sanitize_path_string(parent_name)


def build_pipeline_paths(
    file_name: str, 
    version_label: str = "1.0", 
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    🎯 Génère l'ensemble des répertoires et chemins absolus de sortie de la pipeline
    organisés PAR PROJET sous la structure isolée StageTalan/outputs/<nom_projet>/.
    
    ✅ Tous les chemins sont manipulés via pathlib.Path et convertis en format POSIX
       avant toute opération d'E/S disque ou transmission entre fonctions.
    
    Params:
        file_name: Chemin du fichier source (peut contenir des séquences d'échappement sur Windows)
        version_label: Label de version (ex: "1.0" → "v1.0")
        project_name: Nom du projet (déterminé automatiquement si non fourni)
    
    Returns:
        Dictionnaire avec tous les chemins de la pipeline (type Dict[str, Path | str])
    """
    
    # ============ ÉTAPE 1 : Nettoyage strict du file_name ============
    clean_file_str = sanitize_path_string(file_name)
    file_path = Path(clean_file_str)
    stem = file_path.stem  # Ex: "spec" ou "requirements"

    # ============ ÉTAPE 2 : Détermination du project_name ============
    if not project_name:
        project_name = extract_project_name_from_path(file_path)
    
    # 🛡️ Nettoyage du project_name (même s'il est fourni, on le sanitize)
    project_name = sanitize_path_string(project_name)
    
    # ============ ÉTAPE 3 : Génération du version_prefix ============
    # Préfixe de version (ex: "1.0" -> "v1.0", puis "spec_v1.0")
    clean_version = version_label if version_label.startswith("v") else f"v{version_label}"
    version_prefix = f"{stem}_{clean_version}"

    # ============ ÉTAPE 4 : Construction de l'arborescence sous outputs/<project_name>/ ============
    outputs_base = BASE_DIR / "outputs"
    project_output_dir = outputs_base / project_name

    data_dir = project_output_dir / "data"
    markdown_dir = project_output_dir / "markdowns"
    eval_dir = project_output_dir / "evaluations"
    pdf_dir = project_output_dir / "pdf"
    diagrams_dir = project_output_dir / "diagrams"

    # ============ ÉTAPE 5 : Création automatique de tous les dossiers requis ============
    # 🎯 Les opérations de mkdir() utilisent Path objects directement (pas de strings)
    for folder in [outputs_base, project_output_dir, data_dir, markdown_dir, eval_dir, pdf_dir, diagrams_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    # ============ ÉTAPE 6 : Retour du dictionnaire avec tous les chemins ============
    # 💡 Les chemins de fichiers sont retournés comme Path objects
    # Les consommateurs les convertissent en POSIX via .as_posix() si nécessaire
    return {
        # ━━ Préfixes et dossiers principaux
        "prefix": stem,
        "version_prefix": version_prefix,
        "base_output_dir": project_output_dir,
        "data_dir": data_dir,
        "markdown_dir": markdown_dir,
        "evaluations_dir": eval_dir,
        "pdf_dir": pdf_dir,
        "diagrams_dir": diagrams_dir,
        
        # ━━ Fichiers de données (StageTalan/outputs/<project_name>/data/)
        "parsed_json": data_dir / f"{version_prefix}_parsed.json",
        "summary_json": data_dir / f"{version_prefix}_summary.json",
        "glossary_json": data_dir / f"{version_prefix}_glossary.json",
        "diagrams_json": data_dir / f"{version_prefix}_diagrams.json",
        
        # ━━ Document Markdown (StageTalan/outputs/<project_name>/markdowns/)
        "doc_md": markdown_dir / f"{version_prefix}_doc.md",
        
        # ━━ Fichiers d'évaluation (StageTalan/outputs/<project_name>/evaluations/)
        "parsing_eval": eval_dir / f"{version_prefix}_parsing_eval.json",
        "summary_eval": eval_dir / f"{version_prefix}_summary_eval.json",
        "glossary_eval": eval_dir / f"{version_prefix}_glossary_eval.json",
        "diagram_eval": eval_dir / f"{version_prefix}_diagram_eval.json",
        "doc_eval": eval_dir / f"{version_prefix}_doc_eval.json",
        "layout_eval": eval_dir / f"{version_prefix}_layout_eval.json",
        
        # ━━ PDF Final (StageTalan/outputs/<project_name>/pdf/)
        "final_pdf": pdf_dir / f"{version_prefix}.pdf",
    }