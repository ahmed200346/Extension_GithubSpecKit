import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from app.database import SessionLocal
from app.models import PipelineStage
from app.services.db_service import update_pipeline_stage_data

# Services & Outils
from app.services.parser_service import run_parsing_agent
from app.services.summary_service import SummaryAgentService
from app.services.glossary_service import GlossaryAgentService
from app.services.diagram_service import DiagramAgentService
from app.services.doc_writer_service import DocWriterAgentService
from app.services.layout_service import LayoutAgentService
from app.utils.glossary_tools import GlossaryHarvesterService
from app.utils.diagram_tools import DiagramExporterTool
from app.utils.path_builder import build_pipeline_paths

# Evaluators
from app.services.evaluation_service import (
    ParsingEvaluatorService,
    SummaryEvaluatorService,
    GlossaryEvaluatorService,
    DiagramEvaluatorService,
    DocWriterEvaluatorService
)

# Schemas & State
from app.schemas.parsing_agent_schema import ParsingAgentOutput
from app.schemas.diagram_agent_schema import DiagramOutputModel
from app.schemas.layout_agent_schema import LayoutOutputModel
from app.graph.state import GraphState

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/


def _save_json(file_path: Path, data: Any) -> None:
    """Sauvegarde un dictionnaire ou modèle Pydantic au format JSON."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        if hasattr(data, "model_dump_json"):
            f.write(data.model_dump_json(indent=4))
        else:
            json.dump(data, f, indent=4, ensure_ascii=False)


def _to_json_primitive(data: Any) -> Any:
    """Convertit n'importe quel objet/Pydantic/Dataclass en structure JSON Python pure."""
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if hasattr(data, "dict"):
        return data.dict()
    try:
        return json.loads(json.dumps(data, default=str, ensure_ascii=False))
    except Exception:
        return str(data)


def _sync_stage_to_db(
    run_id: Optional[Any],
    stage: PipelineStage,
    output_attr: Optional[str] = None,
    output_data: Optional[Any] = None,
    eval_attr: Optional[str] = None,
    eval_data: Optional[Dict[str, Any]] = None
):
    """Met à jour le statut, les sorties et l'évaluation JSON dans la BDD."""
    if not run_id:
        return
    
    clean_output = _to_json_primitive(output_data) if output_attr else None
    clean_eval = _to_json_primitive(eval_data) if eval_attr else None

    db = SessionLocal()
    try:
        update_pipeline_stage_data(
            db=db,
            run_id=run_id,
            stage=stage,
            output_attr=output_attr,
            output_data=clean_output,
            eval_attr=eval_attr,
            eval_data=clean_eval
        )
        if eval_attr:
            print(f"[💾 BDD Sync OK] Stage {stage.value} -> {eval_attr} enregistré.")
    except Exception as exc:
        print(f"[⚠️ BDD ERROR] Échec de synchronisation BDD pour stage {stage}: {exc}")
    finally:
        db.close()


# ------------------------------------------------------------------------------
# 1. PARSING NODE
# ------------------------------------------------------------------------------
def parsing_node(state: GraphState) -> Dict[str, Any]:
    print("\n[🚀 NODE] Exécution du Parsing Agent...")
    file_name = state["file_name"]
    file_content = state["file_content"]
    run_id = state.get("run_id")
    version_label = state.get("version_label", "1.0")

    paths = build_pipeline_paths(file_name, version_label=version_label)

    parsed_doc = run_parsing_agent(file_name=file_name, file_content=file_content)
    parsed_json_dict = parsed_doc.model_dump()

    template_path = BASE_DIR / "app" / "resources" / "sdd_templates.json"
    template_config = {}
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            template_config = json.load(f)

    report = ParsingEvaluatorService.evaluate(parsed_doc, template_config)

    # 1. Sauvegarde sur Fichier Disk
    _save_json(paths["parsed_json"], parsed_doc)
    _save_json(paths["parsing_eval"], report)
    print(f"[💾 Disk] Enregistré : {paths['parsed_json'].name} & {paths['parsing_eval'].name}")

    # 2. Sauvegarde en BDD PostgreSQL
    _sync_stage_to_db(
        run_id=run_id,
        stage=PipelineStage.parallel_enrichment,
        output_attr="structured_json",
        output_data=parsed_json_dict,
        eval_attr="parsing_eval",
        eval_data=report
    )

    return {
        "parsed_json_dict": parsed_json_dict,
        "parsed_doc": parsed_doc,
        "parsing_metrics": report
    }


# ------------------------------------------------------------------------------
# 2. SUMMARY NODE
# ------------------------------------------------------------------------------
def summary_node(state: GraphState) -> Dict[str, Any]:
    print("\n[🚀 NODE] Exécution du Summary Agent...")
    file_name = state["file_name"]
    parsed_json_dict = state["parsed_json_dict"]
    parsed_doc = state["parsed_doc"]
    run_id = state.get("run_id")
    version_label = state.get("version_label", "1.0")

    paths = build_pipeline_paths(file_name, version_label=version_label)

    spec_path = BASE_DIR / "app" / "resources" / "summary_spec.json"
    summary_spec_dict = {}
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            summary_spec_dict = json.load(f)

    agent_service = SummaryAgentService()
    summary_doc = agent_service.generate_summary(
        parsed_json_dict=parsed_json_dict,
        summary_spec_dict=summary_spec_dict
    )

    report = SummaryEvaluatorService.evaluate(summary_doc, parsed_doc)
    summary_text = summary_doc.model_dump_json() if hasattr(summary_doc, "model_dump_json") else str(summary_doc)

    # 1. Sauvegarde sur Fichier Disk
    _save_json(paths["summary_json"], summary_doc)
    _save_json(paths["summary_eval"], report)

    # 2. Sauvegarde en BDD PostgreSQL
    _sync_stage_to_db(
        run_id=run_id,
        stage=PipelineStage.parallel_enrichment,
        output_attr="summary_output",
        output_data=summary_text,
        eval_attr="summary_eval",
        eval_data=report
    )

    return {
        "summary_doc": summary_doc,
        "summary_metrics": report
    }


# ------------------------------------------------------------------------------
# 3. GLOSSARY NODE
# ------------------------------------------------------------------------------
def glossary_node(state: GraphState) -> Dict[str, Any]:
    print("\n[🚀 NODE] Exécution du Glossary Agent...")
    file_name = state["file_name"]
    parsed_json_dict = state["parsed_json_dict"]
    parsed_doc = state["parsed_doc"]
    run_id = state.get("run_id")
    version_label = state.get("version_label", "1.0")

    paths = build_pipeline_paths(file_name, version_label=version_label)

    spec_path = BASE_DIR / "app" / "resources" / "glossary_spec.json"
    glossary_spec_dict = {}
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            glossary_spec_dict = json.load(f)

    valid_anchors = GlossaryHarvesterService.generate_and_cache_anchors(parsed_json_dict)
    candidate_terms = GlossaryHarvesterService.harvest_candidates(parsed_json_dict)

    agent_service = GlossaryAgentService()
    glossary_doc = agent_service.generate_glossary(
        parsed_json_dict=parsed_json_dict,
        glossary_spec_dict=glossary_spec_dict,
        valid_anchors=valid_anchors
    )

    report = GlossaryEvaluatorService.evaluate(glossary_doc, parsed_doc, candidate_terms)
    glossary_dict = glossary_doc.model_dump() if hasattr(glossary_doc, "model_dump") else glossary_doc

    # 1. Sauvegarde sur Fichier Disk
    _save_json(paths["glossary_json"], glossary_doc)
    _save_json(paths["glossary_eval"], report)

    # 2. Sauvegarde en BDD PostgreSQL
    _sync_stage_to_db(
        run_id=run_id,
        stage=PipelineStage.parallel_enrichment,
        output_attr="glossary_output",
        output_data=glossary_dict,
        eval_attr="glossary_eval",
        eval_data=report
    )

    return {
        "glossary_doc": glossary_doc,
        "glossary_metrics": report
    }


# ------------------------------------------------------------------------------
# 4. DIAGRAM NODE
# ------------------------------------------------------------------------------
def diagram_node(state: GraphState) -> Dict[str, Any]:
    print("\n[🚀 NODE] Exécution du Diagram Agent...")
    file_name = state["file_name"]
    parsed_json_dict = state["parsed_json_dict"]
    parsed_doc = state["parsed_doc"]
    run_id = state.get("run_id")
    version_label = state.get("version_label", "1.0")

    paths = build_pipeline_paths(file_name, version_label=version_label)

    spec_path = BASE_DIR / "app" / "resources" / "diagram_spec.json"
    diagram_spec_dict = {}
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            diagram_spec_dict = json.load(f)

    agent_service = DiagramAgentService()
    diagram_output = None

    try:
        diagram_output = agent_service.generate_diagrams(
            parsed_json_dict=parsed_json_dict,
            diagram_spec_dict=diagram_spec_dict
        )
    except Exception as exc:
        print(f"[⚠️ WARNING] Diagram Agent error : {exc}")
        return {"diagram_doc": None, "diagram_metrics": {}, "diagram_pdf_path": None}

    pdf_path_str = None
    try:
        diagrams_dict = diagram_output.model_dump()
        pdf_path = asyncio.run(DiagramExporterTool.render_diagrams_to_pdf(
            file_stem=paths["prefix"],
            diagrams_data=diagrams_dict,
            output_dir=paths["diagrams_dir"]
        ))
        pdf_path_str = str(pdf_path)
    except Exception as exc:
        print(f"[⚠️ Erreur Rendu Diagramme] {exc}")

    report = DiagramEvaluatorService.evaluate(
        diagram_data=diagram_output,
        parsed_data=parsed_doc
    )
    diagram_dict = diagram_output.model_dump() if hasattr(diagram_output, "model_dump") else diagram_output

    # 1. Sauvegarde sur Fichier Disk
    _save_json(paths["diagrams_json"], diagram_output)
    _save_json(paths["diagram_eval"], report)

    # 2. Sauvegarde en BDD PostgreSQL
    _sync_stage_to_db(
        run_id=run_id,
        stage=PipelineStage.parallel_enrichment,
        output_attr="diagram_output",
        output_data=diagram_dict,
        eval_attr="diagram_eval",
        eval_data=report
    )

    return {
        "diagram_doc": diagram_output,
        "diagram_metrics": report,
        "diagram_pdf_path": pdf_path_str
    }


# ------------------------------------------------------------------------------
# 5. DOC WRITER NODE
# ------------------------------------------------------------------------------
def doc_writer_node(state: GraphState) -> Dict[str, Any]:
    print("\n[🚀 NODE] Exécution du Documentation Writer Agent...")
    file_name = state["file_name"]
    run_id = state.get("run_id")
    version_label = state.get("version_label", "1.0")

    paths = build_pipeline_paths(file_name, version_label=version_label)

    parsed_json_dict = state.get("parsed_json_dict") or {}
    parsed_doc = state.get("parsed_doc")
    summary_doc = state.get("summary_doc")
    summary_json_dict = summary_doc.model_dump() if hasattr(summary_doc, "model_dump") else (summary_doc or {})
    glossary_doc = state.get("glossary_doc")
    glossary_json_dict = glossary_doc.model_dump() if hasattr(glossary_doc, "model_dump") else (glossary_doc or {})
    diagram_doc = state.get("diagram_doc")
    
    if diagram_doc and hasattr(diagram_doc, "model_dump"):
        diagrams_json_dict = diagram_doc.model_dump()
    elif isinstance(diagram_doc, dict):
        diagrams_json_dict = diagram_doc
    else:
        diagrams_json_dict = {"project_name": paths["prefix"], "diagrams": []}

    spec_path = BASE_DIR / "app" / "resources" / "doc_writer_spec.json"
    doc_writer_spec_dict = {}
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            doc_writer_spec_dict = json.load(f)

    service = DocWriterAgentService()
    doc_writer_output = None
    eval_report = {}
    md_path_str = None
    eval_path_str = None

    try:
        doc_writer_output = service.generate_documentation(
            parsed_json_dict=parsed_json_dict,
            summary_json_dict=summary_json_dict,
            glossary_json_dict=glossary_json_dict,
            diagrams_json_dict=diagrams_json_dict,
            doc_writer_spec_dict=doc_writer_spec_dict
        )

        output_md_path = paths["doc_md"]
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(doc_writer_output.markdown_content)
        md_path_str = str(output_md_path)

        fallback_diagram = diagram_doc if isinstance(diagram_doc, DiagramOutputModel) else DiagramOutputModel(**diagrams_json_dict)

        eval_report = DocWriterEvaluatorService.evaluate(
            markdown_text=doc_writer_output.markdown_content,
            parsed_data=parsed_doc,
            summary_data=summary_doc,
            glossary_data=glossary_doc,
            diagram_data=fallback_diagram
        )

        eval_report_dict = _to_json_primitive(eval_report)

        # 1. Sauvegarde sur Fichier Disk
        eval_json_path = paths["doc_eval"]
        _save_json(eval_json_path, eval_report)
        eval_path_str = str(eval_json_path)

        # 2. Sauvegarde en BDD PostgreSQL avec le stage 'writing'
        _sync_stage_to_db(
            run_id=run_id,
            stage=PipelineStage.writing,
            output_attr="written_doc",
            output_data=doc_writer_output.markdown_content,
            eval_attr="writer_eval",
            eval_data=eval_report_dict
        )
        print(f"[💾 BDD] Évaluation DocWriter synchronisée dans PostgreSQL (writer_eval)")

    except Exception as exc:
        print(f"[❌ ERROR] Exécution DocWriterAgent : {exc}")

    return {
        "doc_writer_doc": doc_writer_output,
        "doc_writer_metrics": eval_report,
        "doc_writer_md_path": md_path_str,
        "doc_writer_eval_path": eval_path_str
    }


# ------------------------------------------------------------------------------
# 6. LAYOUT NODE
# ------------------------------------------------------------------------------
def layout_node(state: GraphState) -> Dict[str, Any]:
    print("\n[🚀 NODE] Exécution du Layout Agent...")
    file_name = state["file_name"]
    run_id = state.get("run_id")
    version_label = state.get("version_label", "1.0")

    paths = build_pipeline_paths(file_name, version_label=version_label)

    doc_writer_doc = state.get("doc_writer_doc")
    markdown_text = ""
    if doc_writer_doc and hasattr(doc_writer_doc, "markdown_content"):
        markdown_text = doc_writer_doc.markdown_content
    else:
        output_md_path = paths["doc_md"]
        if output_md_path.exists():
            with open(output_md_path, "r", encoding="utf-8") as f:
                markdown_text = f.read()

    spec_path = BASE_DIR / "app" / "resources" / "layout_spec.json"
    layout_spec_dict = {}
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            layout_spec_dict = json.load(f)

    output_pdf_path = paths["final_pdf"]
    eval_json_path = paths["layout_eval"]

    layout_result = None
    eval_report = {}
    pdf_path_str = None
    eval_path_str = None

    try:
        service = LayoutAgentService()
        layout_result = service.process_layout_and_render(
            markdown_text=markdown_text,
            layout_spec_dict=layout_spec_dict,
            project_name=paths["prefix"],
            output_pdf_path=str(output_pdf_path)
        )

        if layout_result and layout_result.pdf_generated:
            pdf_path_str = str(output_pdf_path)

            eval_report = {
                "project_name": layout_result.project_name,
                "layout_publication_status": str(
                    layout_result.layout_publication_status.value
                    if hasattr(layout_result.layout_publication_status, 'value')
                    else layout_result.layout_publication_status
                ),
                "page_count": layout_result.page_count,
                "file_size_kb": layout_result.file_size_kb,
                "rendered_diagrams_count": layout_result.rendered_diagrams_count,
                "technical_evaluation": layout_result.technical_evaluation,
                "project_management_kpis": layout_result.project_management_kpis,
                "execution_warnings": layout_result.execution_warnings
            }

            _save_json(eval_json_path, eval_report)
            eval_path_str = str(eval_json_path)

            # Enregistrement en BDD avec le stage 'rendering'
            _sync_stage_to_db(
                run_id=run_id,
                stage=PipelineStage.rendering,
                output_attr="layout_output",
                output_data=str(layout_result),
                eval_attr="layout_eval",
                eval_data=eval_report
            )

    except Exception as exc:
        print(f"[❌ ERROR] Exécution LayoutAgent : {exc}")

    return {
        "layout_doc": layout_result,
        "layout_metrics": eval_report,
        "layout_pdf_path": pdf_path_str,
        "layout_eval_path": eval_path_str
    }
# import json
# import asyncio
# from pathlib import Path
# from typing import Dict, Any, Optional

# from app.database import SessionLocal
# from app.models import PipelineStage
# from app.services.db_service import update_pipeline_stage_data

# # Services & Outils
# from app.services.parser_service import run_parsing_agent
# from app.services.summary_service import SummaryAgentService
# from app.services.glossary_service import GlossaryAgentService
# from app.services.diagram_service import DiagramAgentService
# from app.services.doc_writer_service import DocWriterAgentService
# from app.services.layout_service import LayoutAgentService
# from app.utils.glossary_tools import GlossaryHarvesterService
# from app.utils.diagram_tools import DiagramExporterTool
# from app.utils.path_builder import build_pipeline_paths

# # Evaluators
# from app.services.evaluation_service import (
#     ParsingEvaluatorService,
#     SummaryEvaluatorService,
#     GlossaryEvaluatorService,
#     DiagramEvaluatorService,
#     DocWriterEvaluatorService
# )

# # Schemas & State
# from app.schemas.parsing_agent_schema import ParsingAgentOutput
# from app.schemas.diagram_agent_schema import DiagramOutputModel
# from app.schemas.layout_agent_schema import LayoutOutputModel
# from app.graph.state import GraphState

# BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/


# def _save_json(file_path: Path, data: Any) -> None:
#     """Sauvegarde un dictionnaire ou modèle Pydantic au format JSON."""
#     file_path.parent.mkdir(parents=True, exist_ok=True)
#     with open(file_path, "w", encoding="utf-8") as f:
#         if hasattr(data, "model_dump_json"):
#             f.write(data.model_dump_json(indent=4))
#         else:
#             json.dump(data, f, indent=4, ensure_ascii=False)

# def _to_json_primitive(data: Any) -> Any:
#     """Convertit n'importe quel objet/Pydantic/Dataclass en structure JSON Python pure."""
#     if data is None:
#         return None
#     if hasattr(data, "model_dump"):
#         return data.model_dump()
#     if hasattr(data, "dict"):
#         return data.dict()
#     try:
#         # Forcer la conversion via JSON pour éliminer tout type non-standard
#         return json.loads(json.dumps(data, default=str, ensure_ascii=False))
#     except Exception:
#         return str(data)


# def _sync_stage_to_db(
#     run_id: Optional[Any],
#     stage: PipelineStage,
#     output_attr: Optional[str] = None,
#     output_data: Optional[Any] = None,
#     eval_attr: Optional[str] = None,
#     eval_data: Optional[Dict[str, Any]] = None
# ):
#     """Met à jour le statut, les sorties et l'évaluation JSON dans la BDD."""
#     if not run_id:
#         return
    
#     # Nettoyage systématique des données pour PostgreSQL JSONB
#     clean_output = _to_json_primitive(output_data) if output_attr else None
#     clean_eval = _to_json_primitive(eval_data) if eval_attr else None

#     db = SessionLocal()
#     try:
#         update_pipeline_stage_data(
#             db=db,
#             run_id=run_id,
#             stage=stage,
#             output_attr=output_attr,
#             output_data=clean_output,
#             eval_attr=eval_attr,
#             eval_data=clean_eval
#         )
#         if eval_attr:
#             print(f"[💾 BDD Sync OK] Stage {stage.value} -> {eval_attr} enregistré.")
#     except Exception as exc:
#         print(f"[⚠️ BDD ERROR] Échec de synchronisation BDD pour stage {stage}: {exc}")
#     finally:
#         db.close()
# # def _sync_stage_to_db(
# #     run_id: Optional[Any],
# #     stage: PipelineStage,
# #     output_attr: Optional[str] = None,
# #     output_data: Optional[Any] = None,
# #     eval_attr: Optional[str] = None,
# #     eval_data: Optional[Dict[str, Any]] = None
# # ):
# #     """Met à jour le statut, les sorties et l'évaluation JSON dans la BDD."""
# #     if not run_id:
# #         return
# #     db = SessionLocal()
# #     try:
# #         update_pipeline_stage_data(
# #             db=db,
# #             run_id=run_id,
# #             stage=stage,
# #             output_attr=output_attr,
# #             output_data=output_data,
# #             eval_attr=eval_attr,
# #             eval_data=eval_data
# #         )
# #     except Exception as exc:
# #         print(f"[⚠️ BDD ERROR] Échec de synchronisation BDD pour stage {stage}: {exc}")
# #     finally:
# #         db.close()


# # ------------------------------------------------------------------------------
# # 1. PARSING NODE
# # ------------------------------------------------------------------------------
# def parsing_node(state: GraphState) -> Dict[str, Any]:
#     print("\n[🚀 NODE] Exécution du Parsing Agent...")
#     file_name = state["file_name"]
#     file_content = state["file_content"]
#     run_id = state.get("run_id")
#     version_label = state.get("version_label", "1.0")

#     paths = build_pipeline_paths(file_name, version_label=version_label)

#     parsed_doc = run_parsing_agent(file_name=file_name, file_content=file_content)
#     parsed_json_dict = parsed_doc.model_dump()

#     template_path = BASE_DIR / "app" / "resources" / "sdd_templates.json"
#     template_config = {}
#     if template_path.exists():
#         with open(template_path, "r", encoding="utf-8") as f:
#             template_config = json.load(f)

#     report = ParsingEvaluatorService.evaluate(parsed_doc, template_config)

#     # 1. Sauvegarde sur Fichier Disk
#     _save_json(paths["parsed_json"], parsed_doc)
#     _save_json(paths["parsing_eval"], report)
#     print(f"[💾 Disk] Enregistré : {paths['parsed_json'].name} & {paths['parsing_eval'].name}")

#     # 2. Sauvegarde en BDD PostgreSQL
#     _sync_stage_to_db(
#         run_id=run_id,
#         stage=PipelineStage.parallel_enrichment,
#         output_attr="structured_json",
#         output_data=parsed_json_dict,
#         eval_attr="parsing_eval",
#         eval_data=report
#     )

#     return {
#         "parsed_json_dict": parsed_json_dict,
#         "parsed_doc": parsed_doc,
#         "parsing_metrics": report
#     }


# # ------------------------------------------------------------------------------
# # 2. SUMMARY NODE
# # ------------------------------------------------------------------------------
# def summary_node(state: GraphState) -> Dict[str, Any]:
#     print("\n[🚀 NODE] Exécution du Summary Agent...")
#     file_name = state["file_name"]
#     parsed_json_dict = state["parsed_json_dict"]
#     parsed_doc = state["parsed_doc"]
#     run_id = state.get("run_id")
#     version_label = state.get("version_label", "1.0")

#     paths = build_pipeline_paths(file_name, version_label=version_label)

#     spec_path = BASE_DIR / "app" / "resources" / "summary_spec.json"
#     summary_spec_dict = {}
#     if spec_path.exists():
#         with open(spec_path, "r", encoding="utf-8") as f:
#             summary_spec_dict = json.load(f)

#     agent_service = SummaryAgentService()
#     summary_doc = agent_service.generate_summary(
#         parsed_json_dict=parsed_json_dict,
#         summary_spec_dict=summary_spec_dict
#     )

#     report = SummaryEvaluatorService.evaluate(summary_doc, parsed_doc)
#     summary_text = summary_doc.model_dump_json() if hasattr(summary_doc, "model_dump_json") else str(summary_doc)

#     # 1. Sauvegarde sur Fichier Disk
#     _save_json(paths["summary_json"], summary_doc)
#     _save_json(paths["summary_eval"], report)

#     # 2. Sauvegarde en BDD PostgreSQL
#     _sync_stage_to_db(
#         run_id=run_id,
#         stage=PipelineStage.parallel_enrichment,
#         output_attr="summary_output",
#         output_data=summary_text,
#         eval_attr="summary_eval",
#         eval_data=report
#     )

#     return {
#         "summary_doc": summary_doc,
#         "summary_metrics": report
#     }


# # ------------------------------------------------------------------------------
# # 3. GLOSSARY NODE
# # ------------------------------------------------------------------------------
# def glossary_node(state: GraphState) -> Dict[str, Any]:
#     print("\n[🚀 NODE] Exécution du Glossary Agent...")
#     file_name = state["file_name"]
#     parsed_json_dict = state["parsed_json_dict"]
#     parsed_doc = state["parsed_doc"]
#     run_id = state.get("run_id")
#     version_label = state.get("version_label", "1.0")

#     paths = build_pipeline_paths(file_name, version_label=version_label)

#     spec_path = BASE_DIR / "app" / "resources" / "glossary_spec.json"
#     glossary_spec_dict = {}
#     if spec_path.exists():
#         with open(spec_path, "r", encoding="utf-8") as f:
#             glossary_spec_dict = json.load(f)

#     valid_anchors = GlossaryHarvesterService.generate_and_cache_anchors(parsed_json_dict)
#     candidate_terms = GlossaryHarvesterService.harvest_candidates(parsed_json_dict)

#     agent_service = GlossaryAgentService()
#     glossary_doc = agent_service.generate_glossary(
#         parsed_json_dict=parsed_json_dict,
#         glossary_spec_dict=glossary_spec_dict,
#         valid_anchors=valid_anchors
#     )

#     report = GlossaryEvaluatorService.evaluate(glossary_doc, parsed_doc, candidate_terms)
#     glossary_dict = glossary_doc.model_dump() if hasattr(glossary_doc, "model_dump") else glossary_doc

#     # 1. Sauvegarde sur Fichier Disk
#     _save_json(paths["glossary_json"], glossary_doc)
#     _save_json(paths["glossary_eval"], report)

#     # 2. Sauvegarde en BDD PostgreSQL
#     _sync_stage_to_db(
#         run_id=run_id,
#         stage=PipelineStage.parallel_enrichment,
#         output_attr="glossary_output",
#         output_data=glossary_dict,
#         eval_attr="glossary_eval",
#         eval_data=report
#     )

#     return {
#         "glossary_doc": glossary_doc,
#         "glossary_metrics": report
#     }


# # ------------------------------------------------------------------------------
# # 4. DIAGRAM NODE
# # ------------------------------------------------------------------------------
# def diagram_node(state: GraphState) -> Dict[str, Any]:
#     print("\n[🚀 NODE] Exécution du Diagram Agent...")
#     file_name = state["file_name"]
#     parsed_json_dict = state["parsed_json_dict"]
#     parsed_doc = state["parsed_doc"]
#     run_id = state.get("run_id")
#     version_label = state.get("version_label", "1.0")

#     paths = build_pipeline_paths(file_name, version_label=version_label)

#     spec_path = BASE_DIR / "app" / "resources" / "diagram_spec.json"
#     diagram_spec_dict = {}
#     if spec_path.exists():
#         with open(spec_path, "r", encoding="utf-8") as f:
#             diagram_spec_dict = json.load(f)

#     agent_service = DiagramAgentService()
#     diagram_output = None

#     try:
#         diagram_output = agent_service.generate_diagrams(
#             parsed_json_dict=parsed_json_dict,
#             diagram_spec_dict=diagram_spec_dict
#         )
#     except Exception as exc:
#         print(f"[⚠️ WARNING] Diagram Agent error : {exc}")
#         return {"diagram_doc": None, "diagram_metrics": {}, "diagram_pdf_path": None}

#     pdf_path_str = None
#     try:
#         diagrams_dict = diagram_output.model_dump()
#         pdf_path = asyncio.run(DiagramExporterTool.render_diagrams_to_pdf(
#             file_stem=paths["prefix"],
#             diagrams_data=diagrams_dict,
#             output_dir=paths["diagrams_dir"]
#         ))
#         pdf_path_str = str(pdf_path)
#     except Exception as exc:
#         print(f"[⚠️ Erreur Rendu Diagramme] {exc}")

#     report = DiagramEvaluatorService.evaluate(
#         diagram_data=diagram_output,
#         parsed_data=parsed_doc
#     )
#     diagram_dict = diagram_output.model_dump() if hasattr(diagram_output, "model_dump") else diagram_output

#     # 1. Sauvegarde sur Fichier Disk
#     _save_json(paths["diagrams_json"], diagram_output)
#     _save_json(paths["diagram_eval"], report)

#     # 2. Sauvegarde en BDD PostgreSQL
#     _sync_stage_to_db(
#         run_id=run_id,
#         stage=PipelineStage.writing,
#         output_attr="diagram_output",
#         output_data=diagram_dict,
#         eval_attr="diagram_eval",
#         eval_data=report
#     )

#     return {
#         "diagram_doc": diagram_output,
#         "diagram_metrics": report,
#         "diagram_pdf_path": pdf_path_str
#     }


# # ------------------------------------------------------------------------------
# # 5. DOC WRITER NODE
# # ------------------------------------------------------------------------------
# def doc_writer_node(state: GraphState) -> Dict[str, Any]:
#     print("\n[🚀 NODE] Exécution du Documentation Writer Agent...")
#     file_name = state["file_name"]
#     run_id = state.get("run_id")
#     version_label = state.get("version_label", "1.0")

#     paths = build_pipeline_paths(file_name, version_label=version_label)

#     parsed_json_dict = state.get("parsed_json_dict") or {}
#     parsed_doc = state.get("parsed_doc")
#     summary_doc = state.get("summary_doc")
#     summary_json_dict = summary_doc.model_dump() if hasattr(summary_doc, "model_dump") else (summary_doc or {})
#     glossary_doc = state.get("glossary_doc")
#     glossary_json_dict = glossary_doc.model_dump() if hasattr(glossary_doc, "model_dump") else (glossary_doc or {})
#     diagram_doc = state.get("diagram_doc")
    
#     if diagram_doc and hasattr(diagram_doc, "model_dump"):
#         diagrams_json_dict = diagram_doc.model_dump()
#     elif isinstance(diagram_doc, dict):
#         diagrams_json_dict = diagram_doc
#     else:
#         diagrams_json_dict = {"project_name": paths["prefix"], "diagrams": []}

#     spec_path = BASE_DIR / "app" / "resources" / "doc_writer_spec.json"
#     doc_writer_spec_dict = {}
#     if spec_path.exists():
#         with open(spec_path, "r", encoding="utf-8") as f:
#             doc_writer_spec_dict = json.load(f)

#     service = DocWriterAgentService()
#     doc_writer_output = None
#     eval_report = {}
#     md_path_str = None
#     eval_path_str = None

#     try:
#         doc_writer_output = service.generate_documentation(
#             parsed_json_dict=parsed_json_dict,
#             summary_json_dict=summary_json_dict,
#             glossary_json_dict=glossary_json_dict,
#             diagrams_json_dict=diagrams_json_dict,
#             doc_writer_spec_dict=doc_writer_spec_dict
#         )

#         output_md_path = paths["doc_md"]
#         with open(output_md_path, "w", encoding="utf-8") as f:
#             f.write(doc_writer_output.markdown_content)
#         md_path_str = str(output_md_path)

#         fallback_diagram = diagram_doc if isinstance(diagram_doc, DiagramOutputModel) else DiagramOutputModel(**diagrams_json_dict)

#         eval_report = DocWriterEvaluatorService.evaluate(
#             markdown_text=doc_writer_output.markdown_content,
#             parsed_data=parsed_doc,
#             summary_data=summary_doc,
#             glossary_data=glossary_doc,
#             diagram_data=fallback_diagram
#         )

#         # ----------------------------------------------------------------------
#         # 1. Conversion sérialisable en dict pur pour la BDD PostgreSQL
#         # ----------------------------------------------------------------------
#         if hasattr(eval_report, "model_dump"):
#             eval_report_dict = eval_report.model_dump()
#         elif hasattr(eval_report, "dict"):
#             eval_report_dict = eval_report.dict()
#         elif isinstance(eval_report, dict):
#             eval_report_dict = eval_report
#         else:
#             eval_report_dict = json.loads(json.dumps(eval_report, default=str))

#         # 2. Sauvegarde sur Fichier Disk
#         eval_json_path = paths["doc_eval"]
#         _save_json(eval_json_path, eval_report)
#         eval_path_str = str(eval_json_path)

#         # 3. Sauvegarde en BDD PostgreSQL avec le dictionnaire converti
#         _sync_stage_to_db(
#             run_id=run_id,
#             stage=PipelineStage.layout,
#             output_attr="written_doc",
#             output_data=doc_writer_output.markdown_content,
#             eval_attr="writer_eval",
#             eval_data=eval_report_dict  # 👈 Envoi du dictionnaire sérialisable
#         )
#         print(f"[💾 BDD] Évaluation DocWriter synchronisée dans PostgreSQL (writer_eval)")

#     except Exception as exc:
#         print(f"[❌ ERROR] Exécution DocWriterAgent : {exc}")

#     return {
#         "doc_writer_doc": doc_writer_output,
#         "doc_writer_metrics": eval_report,
#         "doc_writer_md_path": md_path_str,
#         "doc_writer_eval_path": eval_path_str
#     }



# # ------------------------------------------------------------------------------
# # 6. LAYOUT NODE
# # ------------------------------------------------------------------------------
# def layout_node(state: GraphState) -> Dict[str, Any]:
#     print("\n[🚀 NODE] Exécution du Layout Agent...")
#     file_name = state["file_name"]
#     run_id = state.get("run_id")
#     version_label = state.get("version_label", "1.0")

#     paths = build_pipeline_paths(file_name, version_label=version_label)

#     doc_writer_doc = state.get("doc_writer_doc")
#     markdown_text = ""
#     if doc_writer_doc and hasattr(doc_writer_doc, "markdown_content"):
#         markdown_text = doc_writer_doc.markdown_content
#     else:
#         output_md_path = paths["doc_md"]
#         if output_md_path.exists():
#             with open(output_md_path, "r", encoding="utf-8") as f:
#                 markdown_text = f.read()

#     spec_path = BASE_DIR / "app" / "resources" / "layout_spec.json"
#     layout_spec_dict = {}
#     if spec_path.exists():
#         with open(spec_path, "r", encoding="utf-8") as f:
#             layout_spec_dict = json.load(f)

#     output_pdf_path = paths["final_pdf"]
#     eval_json_path = paths["layout_eval"]

#     layout_result = None
#     eval_report = {}
#     pdf_path_str = None
#     eval_path_str = None

#     try:
#         service = LayoutAgentService()
#         layout_result = service.process_layout_and_render(
#             markdown_text=markdown_text,
#             layout_spec_dict=layout_spec_dict,
#             project_name=paths["prefix"],
#             output_pdf_path=str(output_pdf_path)
#         )

#         if layout_result and layout_result.pdf_generated:
#             pdf_path_str = str(output_pdf_path)

#             eval_report = {
#                 "project_name": layout_result.project_name,
#                 "layout_publication_status": str(
#                     layout_result.layout_publication_status.value
#                     if hasattr(layout_result.layout_publication_status, 'value')
#                     else layout_result.layout_publication_status
#                 ),
#                 "page_count": layout_result.page_count,
#                 "file_size_kb": layout_result.file_size_kb,
#                 "rendered_diagrams_count": layout_result.rendered_diagrams_count,
#                 "technical_evaluation": layout_result.technical_evaluation,
#                 "project_management_kpis": layout_result.project_management_kpis,
#                 "execution_warnings": layout_result.execution_warnings
#             }

#             _save_json(eval_json_path, eval_report)
#             eval_path_str = str(eval_json_path)

#             # Enregistrement en BDD
#             _sync_stage_to_db(
#                 run_id=run_id,
#                 stage=PipelineStage.rendering,
#                 output_attr="layout_output",
#                 output_data=str(layout_result),
#                 eval_attr="layout_eval",
#                 eval_data=eval_report
#             )

#     except Exception as exc:
#         print(f"[❌ ERROR] Exécution LayoutAgent : {exc}")

#     return {
#         "layout_doc": layout_result,
#         "layout_metrics": eval_report,
#         "layout_pdf_path": pdf_path_str,
#         "layout_eval_path": eval_path_str
#     }
