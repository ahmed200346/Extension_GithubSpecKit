# app/tools/doc_writer_tools.py

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent                             # StageTalan/

# Séparation claire : Markdown dans data/, PDF final dans documents/
DEFAULT_MARKDOWN_DIR = str(PROJECT_ROOT / "outputs" / "data" / "markdown")
DEFAULT_DOCUMENTS_DIR = str(PROJECT_ROOT / "outputs" / "documents")


def extract_markdown_toc(markdown_content: str) -> List[str]:
    if not markdown_content:
        return []

    lines = markdown_content.splitlines()
    toc = []
    
    for line in lines:
        line_clean = line.strip()
        if re.match(r"^#{1,3}\s+", line_clean):
            title = re.sub(r"^#{1,3}\s+", "", line_clean).strip()
            toc.append(title)

    return toc


def save_markdown_artifact(
    markdown_content: str, 
    project_name: str, 
    output_dir: str = DEFAULT_MARKDOWN_DIR
) -> str:
    """
    Sauvegarde le brouillon Markdown intermédiaire dans outputs/data/markdown/.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    safe_name = re.sub(r"[^\w\-_]", "_", project_name.lower())
    file_name = f"{safe_name}_doc.md"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return os.path.abspath(file_path)


def resolve_diagram_references(
    markdown_content: str, 
    diagrams_pdf_or_images: List[str]
) -> str:
    if not markdown_content or not diagrams_pdf_or_images:
        return markdown_content

    updated_md = markdown_content
    pdf_attachment_note = "\n\n> 📄 **Attached Visual Artifact**: " + ", ".join(
        [os.path.basename(path) for path in diagrams_pdf_or_images]
    )
    
    if "## 2. Architecture Workflows" in updated_md:
        updated_md = updated_md.replace(
            "## 2. Architecture Workflows & Visual Diagrams",
            f"## 2. Architecture Workflows & Visual Diagrams{pdf_attachment_note}"
        )

    return updated_md


def compile_markdown_to_pdf(
    markdown_path: str, 
    output_pdf_dir: str = DEFAULT_DOCUMENTS_DIR
) -> Optional[str]:
    """
    Compile le document final en PDF dans outputs/documents/.
    """
    os.makedirs(output_pdf_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(markdown_path))[0]
    # Retire la mention '_doc' si présente pour un nom de livre propre
    clean_title = base_name.replace("_doc", "")
    pdf_path = os.path.join(output_pdf_dir, f"{clean_title}.pdf")

    return os.path.abspath(pdf_path)


def sanitize_mermaid_blocks(markdown_content: str) -> str:
    if not markdown_content:
        return markdown_content

    def clean_mermaid_code(match):
        mermaid_code = match.group(1)
        cleaned_code = re.sub(
            r'participant\s+(\w+)\s+as\s+"([^"]+)"',
            lambda m: f'participant {m.group(1)} as "{m.group(2).replace("/", " ").replace("\\", "").strip()}"',
            mermaid_code
        )
        return f"```mermaid\n{cleaned_code}\n```"

    pattern = r"```mermaid\s*\n(.*?)\n```"
    return re.sub(pattern, clean_mermaid_code, markdown_content, flags=re.DOTALL)
# # app/tools/doc_writer_tools.py

# import os
# import re
# from pathlib import Path
# from typing import List, Dict, Any, Optional
# from datetime import datetime

# # Détermination dynamique de outputs/documents
# BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
# PROJECT_ROOT = BASE_DIR.parent                             # StageTalan/
# DEFAULT_DOCUMENTS_DIR = str(PROJECT_ROOT / "outputs" / "documents")


# def extract_markdown_toc(markdown_content: str) -> List[str]:
#     """Extrait de manière déterministe la table des matières (TOC)."""
#     if not markdown_content:
#         return []

#     lines = markdown_content.splitlines()
#     toc = []
    
#     for line in lines:
#         line_clean = line.strip()
#         if re.match(r"^#{1,3}\s+", line_clean):
#             title = re.sub(r"^#{1,3}\s+", "", line_clean).strip()
#             toc.append(title)

#     return toc


# def save_markdown_artifact(
#     markdown_content: str, 
#     project_name: str, 
#     output_dir: str = DEFAULT_DOCUMENTS_DIR
# ) -> str:
#     """
#     Sauvegarde le contenu Markdown généré dans outputs/documents.
#     """
#     os.makedirs(output_dir, exist_ok=True)
    
#     safe_name = re.sub(r"[^\w\-_]", "_", project_name.lower())
#     file_name = f"{safe_name}_doc.md"
#     file_path = os.path.join(output_dir, file_name)

#     with open(file_path, "w", encoding="utf-8") as f:
#         f.write(markdown_content)

#     return os.path.abspath(file_path)


# def resolve_diagram_references(
#     markdown_content: str, 
#     diagrams_pdf_or_images: List[str]
# ) -> str:
#     """Associe ou remplace les balises de diagrammes par les références visuelles."""
#     if not markdown_content or not diagrams_pdf_or_images:
#         return markdown_content

#     updated_md = markdown_content
#     pdf_attachment_note = "\n\n> 📄 **Attached Visual Artifact**: " + ", ".join(
#         [os.path.basename(path) for path in diagrams_pdf_or_images]
#     )
    
#     if "## 2. Architecture Workflows" in updated_md:
#         updated_md = updated_md.replace(
#             "## 2. Architecture Workflows & Visual Diagrams",
#             f"## 2. Architecture Workflows & Visual Diagrams{pdf_attachment_note}"
#         )

#     return updated_md


# def compile_markdown_to_pdf(
#     markdown_path: str, 
#     output_pdf_dir: str = DEFAULT_DOCUMENTS_DIR
# ) -> Optional[str]:
#     """Moteur de rendu pour convertir le Markdown unifié en fichier PDF dans outputs/documents."""
#     os.makedirs(output_pdf_dir, exist_ok=True)
    
#     base_name = os.path.splitext(os.path.basename(markdown_path))[0]
#     pdf_path = os.path.join(output_pdf_dir, f"{base_name}.pdf")

#     return os.path.abspath(pdf_path)


# def sanitize_mermaid_blocks(markdown_content: str) -> str:
#     """Assainit les blocs ```mermaid dans le document Markdown."""
#     if not markdown_content:
#         return markdown_content

#     def clean_mermaid_code(match):
#         mermaid_code = match.group(1)
#         cleaned_code = re.sub(
#             r'participant\s+(\w+)\s+as\s+"([^"]+)"',
#             lambda m: f'participant {m.group(1)} as "{m.group(2).replace("/", " ").replace("\\", "").strip()}"',
#             mermaid_code
#         )
#         return f"```mermaid\n{cleaned_code}\n```"

#     pattern = r"```mermaid\s*\n(.*?)\n```"
#     return re.sub(pattern, clean_mermaid_code, markdown_content, flags=re.DOTALL)
