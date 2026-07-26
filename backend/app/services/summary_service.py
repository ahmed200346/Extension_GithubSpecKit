import json
from typing import Dict, Any
from app.schemas.summary_agent_schema import SummaryOutputModel
from app.schemas.parsing_agent_schema import ParsingAgentOutput
from app.utils.summary_pruner import SummaryPrunerService
from app.services.evaluation_service import ParsingEvaluatorService
from app.core.prompts import get_summary_agent_prompt

from app.core.llm_client import ollama_openai_client, get_ollama_model
from app.core.llm_utils import parse_and_validate_json

class SummaryAgentService:
    """
    Service d'orchestration pour le Summary Agent.
    Exploite le client OpenAI-compatible centralisé pour garantir l'homogénéité du pipeline.
    """

    def generate_summary(self, parsed_json_dict: Dict[str, Any], summary_spec_dict: Dict[str, Any]) -> SummaryOutputModel:
        """
        Exécute le pipeline complet du Summary Agent à l'aide du client unifié.
        Prend en entrée le JSON du parser et la configuration fonctionnelle du résumé.
        """
        # 1. Outil 1 : Élagage sémantique du contenu (Smart Content Pruner)
        pruned_payload = SummaryPrunerService.prune_payload(parsed_json_dict)

        # 2. Validation de l'objet d'entrée et extraction du type de document
        parsed_data = ParsingAgentOutput(**parsed_json_dict)
        doc_type = parsed_data.doc_type.value if hasattr(parsed_data.doc_type, 'value') else parsed_data.doc_type

        # 3. Outil 2 : Calculateur d'Ancrage Factuel (KPI du Parser avec config locale vide)
        parser_management_kpis = ParsingEvaluatorService._calculate_management_kpis(
            parsed_data=parsed_data,
            template_config={},
            doc_type=doc_type
        )

        # 4. Construction du prompt système basé sur summary_spec_dict
        system_prompt = get_summary_agent_prompt(summary_spec_dict, parser_management_kpis)

        # 5. Payload d'entrée utilisateur (JSON élagué et compacté)
        user_prompt = json.dumps(pruned_payload, ensure_ascii=False)

        # 6. Appel déterministe au LLM Ollama/Gemma
        response = ollama_openai_client.chat.completions.create(
            model=get_ollama_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        raw_output = response.choices[0].message.content

        # 7. Extraction Regex et validation avec le schéma Pydantic strict
        return parse_and_validate_json(raw_output, SummaryOutputModel)