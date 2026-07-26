# app/core/llm_utils.py
"""
llm_utils.py — Outils de nettoyage, réparation et d'extraction sécurisée 
pour les réponses JSON et Markdown des modèles LLM.
"""

import re
import json
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def clean_markdown_response(raw_response: str) -> str:
    """
    Nettoie la réponse brute du LLM pour garantir un document Markdown pur :
    1. Supprime les balises englobantes ```markdown ... ``` ou ``` ... ```.
    2. Élimine le texte conversationnel d'introduction avant le premier titre (#).
    3. Normalise les fins de lignes.
    """
    if not raw_response:
        return ""

    text = raw_response.strip()

    # 1. Supprime le bloc de code englobant complet (ex: ```markdown # Titre ... ```)
    pattern_full_fence = r"^```(?:markdown|md)?\s*\n(.*?)\n```$"
    match = re.search(pattern_full_fence, text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()

    # 2. Supprime les phrases d'introduction conversationnelles avant le premier titre (#)
    first_header_idx = text.find("#")
    if first_header_idx > 0:
        preamble = text[:first_header_idx].strip()
        if len(preamble) < 250 and not preamble.startswith(">"):
            text = text[first_header_idx:].strip()

    # 3. Supprime les remarques de conclusion courantes (bloc de clôture isolé)
    if text.endswith("```"):
        text = re.sub(r"\n```$", "", text).strip()

    return text


def extract_json_from_text(text: str) -> str:
    """
    Isole et extrait la structure JSON principale (délimitée par le premier { et le dernier }) 
    présente dans une chaîne de caractères.
    """
    if not text:
        return "{}"
        
    cleaned = text.strip()
    
    # 1. Suppression des blocs de code Markdown ```json ... ```
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
        
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
        
    cleaned = cleaned.strip()
    
    # 2. Extraction délimitée entre le premier '{' et le dernier '}'
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]

    return cleaned


def repair_json_string(json_str: str) -> str:
    """
    Répare automatiquement les erreurs de syntaxe JSON courantes générées par les LLM :
    1. Échappe les sauts de ligne littéraux et tabulations situés à l'intérieur des chaînes de caractères.
    2. Supprime les virgules traînantes (trailing commas) devant '}' ou ']'.
    """
    if not json_str:
        return "{}"

    # 1. Traitement des sauts de ligne physiques à l'intérieur des chaînes entre guillemets
    def _escape_inside_quotes(match: re.Match) -> str:
        s = match.group(0)
        # Remplacement des saut de ligne physiques et tabulations
        s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return s

    # Regex ciblant les chaînes entre guillemets "..." (en gérant les guillemets échappés)
    pattern_strings = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    repaired = re.sub(pattern_strings, _escape_inside_quotes, json_str, flags=re.DOTALL)

    # 2. Suppression des virgules traînantes (ex: {"a": 1, })
    repaired = re.sub(r',\s*([}\]])', r'\1', repaired)

    return repaired


def parse_and_validate_json(raw_response: str, schema: Type[T]) -> T:
    """
    Extrait le JSON d'une réponse LLM, répare les erreurs de syntaxe de contrôle
    et valide l'objet résultant avec le schéma Pydantic fourni.
    """
    extracted_json = extract_json_from_text(raw_response)

    # Tentative 1 : Validation directe
    try:
        return schema.model_validate_json(extracted_json)
    except Exception:
        pass

    # Tentative 2 : Après réparation de la syntaxe JSON (sauts de ligne dans les strings, trailing commas)
    repaired_json = repair_json_string(extracted_json)
    try:
        return schema.model_validate_json(repaired_json)
    except Exception:
        pass

    # Tentative 3 : Désérialisation permissive (strict=False) puis validation Pydantic
    try:
        dict_data = json.loads(repaired_json, strict=False)
        return schema.model_validate(dict_data)
    except Exception:
        pass

    try:
        dict_data = json.loads(extracted_json, strict=False)
        return schema.model_validate(dict_data)
    except Exception as e:
        # En cas d'échec définitif, afficher le JSON réparé pour examen
        print(f"\n[❌ ERROR] Échec de la validation Pydantic.")
        print(f"JSON extrait tenté : \n{repaired_json}\n")
        raise e
