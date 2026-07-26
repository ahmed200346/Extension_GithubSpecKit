# app/utils/markdown_parser.py
import hashlib
import re
from typing import List, Dict, Any

def calculate_file_hash(content: str) -> str:
    """
    Calcule le hash SHA-256 du contenu d'un fichier.
    Utile pour détecter si le fichier .md a dérivé par rapport au PDF généré.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def pre_parse_markdown_to_sections(content: str) -> List[Dict[str, Any]]:
    """
    Découpe de manière déterministe le texte Markdown en une liste de sections 
    contenant le titre, le niveau et le contenu brut associé.
    Évite les oublis de contenu par le LLM.
    """
    lines = content.splitlines()
    sections = []
    
    current_title = "Header du document"
    current_level = 1
    current_content_lines = []
    
    # Regex pour détecter les titres Markdown (de # à ######)
    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")
    
    for line in lines:
        match = heading_pattern.match(line)
        if match:
            # Enregistrement de la section précédente avant de commencer la nouvelle
            if current_content_lines or current_title != "Header du document":
                sections.append({
                    "title": current_title,
                    "level": current_level,
                    "raw_content": "\n".join(current_content_lines).strip()
                })
            
            current_level = len(match.group(1))
            current_title = match.group(2).strip()
            current_content_lines = []
        else:
            current_content_lines.append(line)
            
    # Ajout de la dernière section du fichier
    if current_content_lines or current_title != "Header du document":
        sections.append({
            "title": current_title,
            "level": current_level,
            "raw_content": "\n".join(current_content_lines).strip()
        })
        
    return sections