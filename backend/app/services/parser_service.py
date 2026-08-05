import json
from pathlib import Path
from app.schemas.parsing_agent_schema import ParsingAgentOutput
from app.utils.markdown_parser import pre_parse_markdown_to_sections, calculate_file_hash
from app.core.llm_client import ollama_openai_client, get_ollama_model
from app.core.llm_utils import parse_and_validate_json
from app.core.prompts import get_parsing_agent_prompt

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
TEMPLATES_PATH = BASE_DIR / "app" / "resources" / "sdd_templates.json"


def load_sdd_templates() -> dict:
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_parsing_agent(file_name: str, file_content: str) -> ParsingAgentOutput:
    """
    Exécute le premier agent du pipeline (Parsing Agent) à l'aide d'une approche hybride.
    Prend en charge l'ensemble des 10 types de documents définis dans l'Enum DocumentType.
    """
    # 1. Analyse AST déterministe en Python
    file_hash = calculate_file_hash(file_content)
    pre_parsed_sections = pre_parse_markdown_to_sections(file_content)
    
    # 2. Chargement du dictionnaire de gabarits locaux
    sdd_db = load_sdd_templates()
    
    # Isolation stricte du nom de fichier
    file_name_only = Path(file_name).name.lower()
    
    if "constitution" in file_name_only or "rule" in file_name_only:
        inferred_type = "constitution"
        template_key = "constitution"
    elif "task" in file_name_only or "todo" in file_name_only:
        inferred_type = "task"
        template_key = "task"
    elif "requirement" in file_name_only:
        inferred_type = "requirements"
        template_key = "requirements"
    elif "contract" in file_name_only:
        inferred_type = "contracts"
        template_key = "contracts"
    elif "data-model" in file_name_only or "data_model" in file_name_only or "datamodel" in file_name_only:
        inferred_type = "data-model"
        template_key = "data-model"
    elif "research" in file_name_only:
        inferred_type = "research"
        template_key = "research"
    elif "quickstart" in file_name_only:
        inferred_type = "quickstart"
        template_key = "quickstart"
    elif any(keyword in file_name_only for keyword in ["plan", "architect", "schema"]):
        inferred_type = "plan"
        template_key = "plan"
    elif "spec" in file_name_only:
        inferred_type = "spec"
        template_key = "spec"
    else:
        inferred_type = "autres"
        template_key = "spec"
        
    # Chargement du gabarit
    sdd_template = sdd_db.get(template_key, {})
    if not sdd_template:
        sdd_template = {
            "description": f"Gabarit générique pour document de type {inferred_type}.",
            "required_sections": [],
            "expected_element_types": []
        }
        
    project_indicators = sdd_db.get("project_source_indicators", {})

    # 3. Récupération du Prompt Système
    system_prompt = get_parsing_agent_prompt(
        inferred_type=inferred_type,
        sdd_template=sdd_template,
        project_indicators=project_indicators
    )

    # 4. Payload d'entrée
    user_message = {
        "file_name": Path(file_name).name,
        "file_hash": file_hash,
        "doc_type_suggested": inferred_type,
        "sections_to_process": pre_parsed_sections
    }

    # 5. Appel au LLM Ollama
    response = ollama_openai_client.chat.completions.create(
        model=get_ollama_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_message, ensure_ascii=False)}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    raw_output = response.choices[0].message.content
    return parse_and_validate_json(raw_output, ParsingAgentOutput)
