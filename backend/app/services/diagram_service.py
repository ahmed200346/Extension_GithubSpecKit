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
    du document parsé et générer des schémas d'architecture Mermaid.js valides.
    """

    @staticmethod
    def clean_mermaid_code(code: str) -> str:
        """
        Applique une série de correctifs Regex déterministes sur le code Mermaid.js
        pour éliminer les erreurs courantes de syntaxe générées par le LLM.
        """
        if not code:
            return ""

        # 1. Suppression des balises markdown éventuelles
        code = code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)

        # 2. Correction des formes de nœuds incompatibles avec les moteurs de rendu
        code = re.sub(r'\(\[([^\]]+)\]\)', r'[\1]', code)
        code = re.sub(r'\(\(([^)]+)\)\)', r'[\1]', code)
        code = re.sub(r'\[\[([^\]]+)\]\]', r'[\1]', code)
        code = re.sub(r'\{\{([^}]+)\}\}', r'{\1}', code)

        # 3. Correction des flèches mal formées (ex: -->|label|> vers -->|label|)
        code = re.sub(r'-->\|([^|]+)\|>', r'-->|\1|', code)

        # 4. Correction des attributs erDiagram en style UML (+id: int vers int id)
        lines = code.split('\n')
        fixed_lines = []
        in_entity_block = False

        for line in lines:
            stripped = line.strip()

            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*\{', stripped):
                in_entity_block = True
                fixed_lines.append(line)
                continue
            if stripped == "}" and in_entity_block:
                in_entity_block = False
                fixed_lines.append(line)
                continue

            if in_entity_block:
                match1 = re.match(r'^\+?\s*(\w+)\s*:\s*(\w+)\s*(PK|FK)?\s*$', stripped)
                if match1:
                    field_name, type_name, key_marker = match1.group(1), match1.group(2), match1.group(3) or ''
                    fixed = f"{type_name} {field_name}" + (f" {key_marker}" if key_marker else "")
                    leading = line[:len(line) - len(line.lstrip())]
                    fixed_lines.append(leading + fixed)
                    continue

            fixed_lines.append(line)

        return "\n".join(fixed_lines).strip()

    def generate_diagrams(
        self, 
        parsed_json_dict: Dict[str, Any], 
        diagram_spec_dict: Dict[str, Any]
    ) -> DiagramOutputModel:
        """
        Exécute le pipeline complet de génération de diagrammes d'architecture.
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