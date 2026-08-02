# app/services/diagram_service.py
import json
import re
from typing import Dict, Any, List

# Importations des schémas requis
from app.schemas.diagram_agent_schema import DiagramOutputModel, DiagramItem
from app.schemas.parsing_agent_schema import ParsingAgentOutput

# Importations des composants d'infrastructure
from app.core.prompts import get_diagram_agent_prompt
from app.core.llm_client import ollama_openai_client, get_ollama_model
from app.core.llm_utils import parse_and_validate_json


class DiagramAgentService:
    """
    Service d'orchestration pour le Diagram Agent.
    Exploite le client Ollama/OpenAI-compatible centralisé pour analyser la topologie
    du document parsé et générer des schémas d'architecture Mermaid.js valides
    avec thème bleu technique professionnel.
    """

    # Configuration Mermaid thème bleu technique professionnel
    MERMAID_TECH_BLUE_THEME = """%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#1A365D',
    'primaryTextColor': '#1A202C',
    'primaryBorderColor': '#2B6CB0',
    'lineColor': '#2B6CB0',
    'secondaryColor': '#EBF8FF',
    'tertiaryColor': '#EBF8FF',
    'background': '#FFFFFF',
    'mainBkg': '#FFFFFF',
    'secondBkg': '#EBF8FF',
    'tertiaryBkg': '#F7FAFC',
    'secondaryTextColor': '#4A5568',
    'fontSize': '16px',
    'fontFamily': 'Inter, system-ui, sans-serif',
    'nodePadding': '15px',
    'borderRadius': '8px',
    'edgeLabelBackground': '#EBF8FF',
    'clusterBkg': '#F7FAFC',
    'clusterBorder': '#2B6CB0',
    'defaultLinkColor': '#2B6CB0',
    'titleColor': '#1A365D',
    'actorBorder': '#2B6CB0',
    'actorBkg': '#EBF8FF',
    'actorTextColor': '#1A365D',
    'actorLineColor': '#2B6CB0',
    'signalColor': '#2B6CB0',
    'signalTextColor': '#1A202C',
    'labelBoxBorderColor': '#2B6CB0',
    'labelBoxBkgColor': '#EBF8FF',
    'labelTextColor': '#1A202C',
    'loopTextColor': '#1A202C',
    'arrowHeadColor': '#2B6CB0',
    'sequenceNumberColor': '#1A365D',
    'sequenceActorBorder': '#2B6CB0',
    'sequenceActorBkg': '#EBF8FF',
    'sequenceArrowColor': '#2B6CB0',
    'noteBkgColor': '#FFF5EB',
    'noteBorderColor': '#DD6B20',
    'noteTextColor': '#1A202C'
  }
}}%%
"""
    _INIT_BLOCK_PATTERN = re.compile(r"^%%\{init:.*?\}%%\s*\n?", re.DOTALL)

    @staticmethod
    def clean_mermaid_code(code: str) -> str:
        """
        Nettoie le code Mermaid, injecte le thème bleu technique professionnel,
        et corrige les erreurs de syntaxe courantes générées par le LLM.
        Version idempotente : rejouable sans dupliquer en-tête ou thème.
        """
        if not code:
            return ""

        code = str(code).strip()

        # 1. Supprime les blocs de code Markdown
        code = re.sub(r"^```(?:mermaid)?\s*\n?", "", code, flags=re.MULTILINE)
        code = re.sub(r"\n?\s*```$", "", code, flags=re.MULTILINE)

        # 2. Normalisation Unicode
        code = code.replace("\xa0", " ").replace("\u200b", "").replace("\r\n", "\n")
        code = code.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'").replace("«", '"').replace("»", '"')

        # 3. Extraire et RETIRER un éventuel bloc d'init déjà présent
        existing_init = None
        init_match = DiagramAgentService._INIT_BLOCK_PATTERN.match(code)
        if init_match:
            existing_init = init_match.group(0).rstrip("\n")
            code = code[init_match.end():].strip()

        # 4. Vérification / Ajout de l'en-tête de diagramme UNIQUEMENT sur le corps
        valid_headers = ("flowchart", "graph", "sequenceDiagram", "classDiagram", "erDiagram", "stateDiagram", "gantt", "mindmap", "pie", "gitGraph", "C4Context")
        lines = [line.strip() for line in code.split("\n") if line.strip()]
        first_line = lines[0] if lines else ""

        if not any(first_line.startswith(hdr) for hdr in valid_headers):
            code = f"flowchart TD\n{code}"

        # 5. Correction des formes de nœuds invalides ou doublons
        code = re.sub(r'\(\[([^\]]+)\]\)', r'["\1"]', code)
        code = re.sub(r'\(\(([^)]+)\)\)', r'["\1"]', code)
        code = re.sub(r'\[\[([^\]]+)\]\]', r'["\1"]', code)
        code = re.sub(r'\{\{([^}]+)\}\}', r'["\1"]', code)

        # 6. Encapsulation automatique des libellés de nœuds avec guillemets (Auto-Quoting Engine)
        def quote_node_label(match):
            node_id = match.group(1)
            open_symbol = match.group(2)
            label = match.group(3).strip()
            close_symbol = match.group(4)

            if (label.startswith('"') and label.endswith('"')) or (label.startswith("'") and label.endswith("'")):
                clean_label = label[1:-1].replace('"', "'")
                return f'{node_id}{open_symbol}"{clean_label}"{close_symbol}'

            clean_label = label.replace('"', "'")
            return f'{node_id}{open_symbol}"{clean_label}"{close_symbol}'

        node_pattern = re.compile(r'(\b[A-Za-z0-9_]+)(\[\s*|\(\s*|\{\s*)("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^\]\}\)]+)(\s*\]|\s*\)|\s*\})')

        cleaned_lines = []
        in_er_block = False

        for line in code.split("\n"):
            line_str = line.rstrip()
            stripped = line_str.strip()

            if not stripped:
                cleaned_lines.append(line_str)
                continue

            if any(stripped.startswith(hdr) for hdr in valid_headers) or stripped.startswith("subgraph") or stripped == "end":
                cleaned_lines.append(line_str)
                continue

            if "erDiagram" in code:
                if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*\{', stripped):
                    in_er_block = True
                    cleaned_lines.append(line_str)
                    continue
                if stripped == "}" and in_er_block:
                    in_er_block = False
                    cleaned_lines.append(line_str)
                    continue
                if in_er_block:
                    match_attr = re.match(r'^\+?\s*(\w+)\s*:\s*(\w+)\s*(PK|FK)?\s*$', stripped)
                    if match_attr:
                        field_name, type_name, key_marker = match_attr.group(1), match_attr.group(2), match_attr.group(3) or ''
                        fixed = f"{type_name} {field_name}" + (f" {key_marker}" if key_marker else "")
                        leading = line_str[:len(line_str) - len(line_str.lstrip())]
                        cleaned_lines.append(leading + fixed)
                        continue

            line_str = re.sub(
                r'(-->|---|==>|-\.->)\|([^"|\n]+)\|',
                lambda m: f'{m.group(1)}|"{m.group(2).strip().replace(chr(34), chr(39))}"|',
                line_str
            )
            line_str = node_pattern.sub(quote_node_label, line_str)
            cleaned_lines.append(line_str)

        code = "\n".join(cleaned_lines)
        code = re.sub(r'-->\|([^|]+)\|>', r'-->|\1|', code)
        code = re.sub(r'\n\s*\n', '\n', code)

        # 7. Réinjection du thème : réutilise celui déjà présent si possible
        theme_block = existing_init if existing_init else DiagramAgentService.MERMAID_TECH_BLUE_THEME.strip()
        code = f"{theme_block}\n{code}"

        return code.strip()

    def generate_diagrams(
        self, 
        parsed_json_dict: Dict[str, Any], 
        diagram_spec_dict: Dict[str, Any]
    ) -> DiagramOutputModel:
        """
        Exécute le pipeline complet de génération de diagrammes d'architecture
        avec thème bleu technique professionnel.
        """
        # 1. Validation structurelle de l'objet d'entrée (ParsingAgentOutput)
        ParsingAgentOutput(**parsed_json_dict)

        # 2. Construction du Prompt Système enrichi
        system_prompt = get_diagram_agent_prompt(
            diagram_spec=diagram_spec_dict,
            parsed_project_data=parsed_json_dict
        )

        # 3. Payload d'entrée utilisateur (JSON parsé épuré)
        user_prompt = json.dumps(parsed_json_dict, ensure_ascii=False)

        # 4. Inférence LLM via le client centralisé
        response = ollama_openai_client.chat.completions.create(
            model=get_ollama_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        raw_output = response.choices[0].message.content

        # 5. Extraction Regex et validation Pydantic
        diagram_doc = parse_and_validate_json(raw_output, DiagramOutputModel)

        # 6. Post-traitement et nettoyage de la syntaxe Mermaid pour chaque schéma
        sanitized_items: List[DiagramItem] = []
        for diag in diagram_doc.diagrams:
            cleaned_code = self.clean_mermaid_code(diag.mermaid_code)
            sanitized_items.append(
                DiagramItem(
                    title=diag.title,
                    type=diag.type,
                    description=diag.description,
                    mermaid_code=cleaned_code
                )
            )

        # Limiter le résultat à 4 diagrammes maximum
        return DiagramOutputModel(diagrams=sanitized_items[:4])