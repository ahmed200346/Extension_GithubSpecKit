import re
import copy
from typing import Dict, Any

class SummaryPrunerService:
    """
    Outil d'Élagage Sémantique (Smart Content Pruner) pour l'Agent Summary.
    Supprime les structures de code lourdes (JSON, TypeScript, Bash) du champ
    raw_content pour ne conserver que la grammaire textuelle et les règles métiers.
    """

    @staticmethod
    def strip_code_blocks(raw_content: str) -> str:
        """
        Supprime les blocs de code Markdown (```...```) d'une chaîne de caractères
        tout en préservant le texte explicatif situé autour.
        """
        if not raw_content:
            return ""
        
        # Le flag re.DOTALL permet au '.' de capturer également les retours à la ligne (\n)
        # Supprime tout le contenu encapsulé entre les balises de code
        cleaned_text = re.sub(r'```.*?```', '', raw_content, flags=re.DOTALL)
        
        # Squeezage des lignes vides dupliquées pour compacter au maximum le volume de tokens
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)
        
        return cleaned_text.strip()

    @classmethod
    def prune_payload(cls, parsed_json_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prend le dictionnaire issu du Parsing Agent, effectue une copie profonde,
        et nettoie le contenu brut de chaque section pour l'Agent Summary.
        """
        # Copie profonde pour éviter de modifier par effet de bord le JSON d'origine en mémoire
        optimized_payload = copy.deepcopy(parsed_json_dict)
        
        if "sections" in optimized_payload and isinstance(optimized_payload["sections"], list):
            for section in optimized_payload["sections"]:
                if "raw_content" in section and section["raw_content"]:
                    # Application du nettoyage régex sur le contenu brut de la section
                    section["raw_content"] = cls.strip_code_blocks(section["raw_content"])
                    
        return optimized_payload