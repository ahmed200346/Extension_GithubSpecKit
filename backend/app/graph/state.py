from typing import TypedDict, Dict, Any, Optional
from app.schemas.parsing_agent_schema import ParsingAgentOutput
from app.schemas.summary_agent_schema import SummaryOutputModel
from app.schemas.glossary_agent_schema import GlossaryOutputModel


class GraphState(TypedDict):
    # Entrées initiales du système
    file_name: str
    file_content: str
    version_label: str
    run_id: Optional[Any]
    prefix: Optional[str]

    # 1. Parsing Agent : Résultats & Métriques
    parsed_json_dict: Optional[Dict[str, Any]]
    parsed_doc: Optional[ParsingAgentOutput]
    parsing_metrics: Optional[Dict[str, Any]]

    # 2. Summary Agent : Résultats & Métriques (Parallèle A)
    summary_doc: Optional[SummaryOutputModel]
    summary_metrics: Optional[Dict[str, Any]]

    # 3. Glossary Agent : Résultats & Métriques (Parallèle B)
    glossary_doc: Optional[GlossaryOutputModel]
    glossary_metrics: Optional[Dict[str, Any]]

    # 4. Diagram Agent : Résultats & Métriques (Parallèle C)
    diagram_doc: Optional[Any]
    diagram_metrics: Optional[Dict[str, Any]]
    diagram_pdf_path: Optional[str]

    # 5. Doc Writer Agent : Résultats, Métriques & Chemins
    doc_writer_doc: Optional[Any]
    doc_writer_metrics: Optional[Dict[str, Any]]
    doc_writer_md_path: Optional[str]
    doc_writer_eval_path: Optional[str]

    # 6. Layout Agent : Résultats, Métriques & Chemins (Publication PDF)
    layout_doc: Optional[Any]
    layout_metrics: Optional[Dict[str, Any]]
    layout_pdf_path: Optional[str]
    layout_eval_path: Optional[str]
# # app/graph/state.py
# from typing import TypedDict, Dict, Any, Optional
# from app.schemas.parsing_agent_schema import ParsingAgentOutput
# from app.schemas.summary_agent_schema import SummaryOutputModel
# from app.schemas.glossary_agent_schema import GlossaryOutputModel

# class GraphState(TypedDict):
#     # Entrées initiales du système
#     file_name: str
#     file_content: str
#     version_label: str
#     un_id: Optional[Any]
#     # 1. Parsing Agent : Résultats & Métriques
#     parsed_json_dict: Optional[Dict[str, Any]]
#     parsed_doc: Optional[ParsingAgentOutput]
#     parsing_metrics: Optional[Dict[str, Any]]
    
#     # 2. Summary Agent : Résultats & Métriques (Parallèle A)
#     summary_doc: Optional[SummaryOutputModel]
#     summary_metrics: Optional[Dict[str, Any]]
    
#     # 3. Glossary Agent : Résultats & Métriques (Parallèle B)
#     glossary_doc: Optional[GlossaryOutputModel]
#     glossary_metrics: Optional[Dict[str, Any]]

#     # 4. Diagram Agent : Résultats & Métriques (Parallèle C)
#     diagram_doc: Optional[Any]
#     diagram_metrics: Optional[Dict[str, Any]]
#     diagram_pdf_path: Optional[str]

#     # 5. Doc Writer Agent : Résultats, Métriques & Chemins (Convergence)
#     doc_writer_doc: Optional[Any]
#     doc_writer_metrics: Optional[Dict[str, Any]]
#     doc_writer_md_path: Optional[str]
#     doc_writer_eval_path: Optional[str]

#     # 6. Layout Agent : Résultats, Métriques & Chemins (Certification & Rendu PDF Final)
#     layout_doc: Optional[Any]
#     layout_metrics: Optional[Dict[str, Any]]
#     layout_pdf_path: Optional[str]
#     layout_eval_path: Optional[str]

