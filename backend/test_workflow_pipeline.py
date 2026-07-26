import sys
from pathlib import Path
from app.graph.workflow import create_pipeline_workflow

TARGET_FILE_NAME = "tasks(1).md"

def print_unified_dashboard(final_state: dict):
    """Affiche le tableau de bord consolidé des 6 agents du pipeline."""
    print("\n" + "=" * 80)
    print("      DASHBOARD DE FIABILITÉ MULTI-AGENTS (PIPELINE LANGGRAPH)")
    print("=" * 80)
    
    # 1. METRIQUES PARSER
    p_metrics = final_state.get("parsing_metrics", {}).get("technical_evaluation", {})
    print("1. PARSING AGENT METRICS:")
    print(f"   • Schema Adherence (SAR)          : {p_metrics.get('schema_adherence_rate', 0):.1f}%")
    print(f"   • Structural Integrity (SIR)     : {p_metrics.get('structural_integrity_recall', 0):.1f}%")
    print(f"   • Graph Relational Integrity (GRI): {p_metrics.get('graph_relational_integrity', 0):.1f}%")
    
    # 2. METRIQUES SUMMARY
    s_metrics = final_state.get("summary_metrics", {}).get("technical_evaluation", {})
    print("\n2. SUMMARY AGENT METRICS (PARALLÈLE A):")
    print(f"   • Maturity Alignment (MAS)       : {s_metrics.get('maturity_alignment_score', 0):.1f}%")
    print(f"   • Conciseness & Precision (CPS)  : {s_metrics.get('conciseness_precision_score', 0):.1f}%")
    print(f"   • Extraction Completeness (ECR)  : {s_metrics.get('extraction_completeness_rate', 0):.1f}%")
    
    # 3. METRIQUES GLOSSARY
    g_metrics = final_state.get("glossary_metrics", {}).get("technical_evaluation", {})
    print("\n3. GLOSSARY AGENT METRICS (PARALLÈLE B):")
    print(f"   • Term Coverage Rate (TCR)        : {g_metrics.get('term_coverage_rate', 0):.1f}%")
    print(f"   • Categorization Accuracy (CAR)   : {g_metrics.get('categorization_accuracy_rate', 0):.1f}%")
    print(f"   • Anti-Tautology Adherence (ATA)  : {g_metrics.get('anti_tautology_adherence', 0):.1f}%")
    print(f"   • Contextual Anchor Precision(CAP): {g_metrics.get('contextual_anchor_precision', 0):.1f}%")

    # 4. METRIQUES DIAGRAM
    d_metrics = final_state.get("diagram_metrics", {}).get("technical_evaluation", {})
    print("\n4. DIAGRAM AGENT METRICS (PARALLÈLE C):")
    print(f"   • Syntax Validity Rate (SVR)      : {d_metrics.get('syntax_validity_rate', 0):.1f}%")
    print(f"   • Diagram Coverage Rate (DCR)     : {d_metrics.get('diagram_coverage_rate', 0):.1f}%")
    print(f"   • Relational Completeness (RCR)  : {d_metrics.get('relational_completeness_rate', 0):.1f}%")
    print(f"   • Structural Rule Adherence (SRA) : {d_metrics.get('structural_rule_adherence', 0):.1f}%")
    if final_state.get("diagram_pdf_path"):
        print(f"   • Export PDF Diagrammes           : {final_state.get('diagram_pdf_path')}")

    # 5. METRIQUES DOC WRITER
    dw_metrics = final_state.get("doc_writer_metrics", {})
    dw_tech = dw_metrics.get("technical_evaluation", {})
    print("\n5. DOCUMENTATION WRITER AGENT METRICS (CONVERGENCE):")
    print(f"   • Document Structure Completeness (DSC): {dw_tech.get('document_structure_completeness', 0):.1f}%")
    print(f"   • Traceability Preservation Rate (TPR)  : {dw_tech.get('traceability_preservation_rate', 0):.1f}%")
    print(f"   • Diagram Embedding Validity (DEV)     : {dw_tech.get('diagram_embedding_validity', 0):.1f}%")
    print(f"   • Glossary Format & Placement (GFF)    : {dw_tech.get('glossary_format_and_placement', 0):.1f}%")
    print(f"   • Readiness Status                     : 🟢 {dw_metrics.get('documentation_readiness_status', 'N/A')}")
    if final_state.get("doc_writer_md_path"):
        print(f"   • Fichier Markdown Généré             : {final_state.get('doc_writer_md_path')}")

    # 6. METRIQUES LAYOUT AGENT
    l_metrics = final_state.get("layout_metrics", {})
    l_tech = l_metrics.get("technical_evaluation", {})
    print("\n6. LAYOUT & PUBLICATION AGENT METRICS (CERTIFICATION PDF):")
    print(f"   • Render Success Rate (RSR)       : {l_tech.get('render_success_rate', 0):.1f}%")
    print(f"   • Diagram Visual Render Rate (DVR): {l_tech.get('diagram_visual_render_rate', 0):.1f}%")
    print(f"   • Page Budget Adherence (PBA)     : {l_tech.get('page_budget_adherence', 0):.1f}%")
    print(f"   • Visual Overflow Rate (VOR)      : {l_tech.get('visual_overflow_rate', 0):.1f}%")
    print(f"   • Styling Consistency Score (SCS) : {l_tech.get('styling_consistency_score', 0):.1f}%")
    print(f"   • Publication Status              : 🟢 {l_metrics.get('layout_publication_status', 'N/A')}")
    if final_state.get("layout_pdf_path"):
        print(f"   • Document PDF Final Généré       : {final_state.get('layout_pdf_path')}")
    if final_state.get("layout_eval_path"):
        print(f"   • Fichier Évaluation JSON         : {final_state.get('layout_eval_path')}")
    print("=" * 80)

def main():
    project_root = Path(__file__).resolve().parent.parent
    target_path = project_root / "test_files" / TARGET_FILE_NAME
    
    if not target_path.exists():
        print(f"[❌] Erreur : Fichier '{target_path}' introuvable.")
        sys.exit(1)
        
    with open(target_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    initial_state = {
        "file_name": TARGET_FILE_NAME,
        "file_content": file_content
    }

    pipeline = create_pipeline_workflow()
    print("[⚙️] Lancement du Pipeline Multi-Agents complet...")
    
    final_state = pipeline.invoke(initial_state)
    
    print_unified_dashboard(final_state)

if __name__ == "__main__":
    main()
# import sys
# from pathlib import Path
# from app.graph.workflow import create_pipeline_workflow

# TARGET_FILE_NAME = "tasks(1).md"

# def print_unified_dashboard(final_state: dict):
#     """Affiche le tableau de bord consolidé des 5 agents."""
#     print("\n" + "=" * 80)
#     print("      DASHBOARD DE FIABILITÉ MULTI-AGENTS (PIPELINE LANGGRAPH)")
#     print("=" * 80)
    
#     # 1. METRIQUES PARSER
#     p_metrics = final_state.get("parsing_metrics", {}).get("technical_evaluation", {})
#     print("1. PARSING AGENT METRICS:")
#     print(f"   • Schema Adherence (SAR)          : {p_metrics.get('schema_adherence_rate', 0):.1f}%")
#     print(f"   • Structural Integrity (SIR)     : {p_metrics.get('structural_integrity_recall', 0):.1f}%")
#     print(f"   • Graph Relational Integrity (GRI): {p_metrics.get('graph_relational_integrity', 0):.1f}%")
    
#     # 2. METRIQUES SUMMARY
#     s_metrics = final_state.get("summary_metrics", {}).get("technical_evaluation", {})
#     print("\n2. SUMMARY AGENT METRICS (PARALLÈLE A):")
#     print(f"   • Maturity Alignment (MAS)       : {s_metrics.get('maturity_alignment_score', 0):.1f}%")
#     print(f"   • Conciseness & Precision (CPS)  : {s_metrics.get('conciseness_precision_score', 0):.1f}%")
#     print(f"   • Extraction Completeness (ECR)  : {s_metrics.get('extraction_completeness_rate', 0):.1f}%")
    
#     # 3. METRIQUES GLOSSARY
#     g_metrics = final_state.get("glossary_metrics", {}).get("technical_evaluation", {})
#     print("\n3. GLOSSARY AGENT METRICS (PARALLÈLE B):")
#     print(f"   • Term Coverage Rate (TCR)        : {g_metrics.get('term_coverage_rate', 0):.1f}%")
#     print(f"   • Categorization Accuracy (CAR)   : {g_metrics.get('categorization_accuracy_rate', 0):.1f}%")
#     print(f"   • Anti-Tautology Adherence (ATA)  : {g_metrics.get('anti_tautology_adherence', 0):.1f}%")
#     print(f"   • Contextual Anchor Precision(CAP): {g_metrics.get('contextual_anchor_precision', 0):.1f}%")

#     # 4. METRIQUES DIAGRAM
#     d_metrics = final_state.get("diagram_metrics", {}).get("technical_evaluation", {})
#     print("\n4. DIAGRAM AGENT METRICS (PARALLÈLE C):")
#     print(f"   • Syntax Validity Rate (SVR)      : {d_metrics.get('syntax_validity_rate', 0):.1f}%")
#     print(f"   • Diagram Coverage Rate (DCR)     : {d_metrics.get('diagram_coverage_rate', 0):.1f}%")
#     print(f"   • Relational Completeness (RCR)  : {d_metrics.get('relational_completeness_rate', 0):.1f}%")
#     print(f"   • Structural Rule Adherence (SRA) : {d_metrics.get('structural_rule_adherence', 0):.1f}%")
#     if final_state.get("diagram_pdf_path"):
#         print(f"   • Export PDF                      : {final_state.get('diagram_pdf_path')}")

#     # 5. METRIQUES DOC WRITER
#     dw_metrics = final_state.get("doc_writer_metrics", {})
#     dw_tech = dw_metrics.get("technical_evaluation", {})
#     print("\n5. DOCUMENTATION WRITER AGENT METRICS (CONVERGENCE FINALE):")
#     print(f"   • Document Structure Completeness (DSC): {dw_tech.get('document_structure_completeness', 0):.1f}%")
#     print(f"   • Traceability Preservation Rate (TPR)  : {dw_tech.get('traceability_preservation_rate', 0):.1f}%")
#     print(f"   • Diagram Embedding Validity (DEV)     : {dw_tech.get('diagram_embedding_validity', 0):.1f}%")
#     print(f"   • Glossary Format & Placement (GFF)    : {dw_tech.get('glossary_format_and_placement', 0):.1f}%")
#     print(f"   • Readiness Status                     : 🟢 {dw_metrics.get('documentation_readiness_status', 'N/A')}")
#     if final_state.get("doc_writer_md_path"):
#         print(f"   • Fichier Markdown Généré             : {final_state.get('doc_writer_md_path')}")
#     if final_state.get("doc_writer_eval_path"):
#         print(f"   • Fichier Évaluation JSON             : {final_state.get('doc_writer_eval_path')}")
#     print("=" * 80)

# def main():
#     project_root = Path(__file__).resolve().parent.parent
#     target_path = project_root / "test_files" / TARGET_FILE_NAME
    
#     if not target_path.exists():
#         print(f"[❌] Erreur : Fichier '{target_path}' introuvable.")
#         sys.exit(1)
        
#     with open(target_path, "r", encoding="utf-8") as f:
#         file_content = f.read()

#     initial_state = {
#         "file_name": TARGET_FILE_NAME,
#         "file_content": file_content
#     }

#     pipeline = create_pipeline_workflow()
#     print("[⚙️] Lancement de l'orchestration LangGraph Multi-Agents...")
    
#     final_state = pipeline.invoke(initial_state)
    
#     print_unified_dashboard(final_state)

# if __name__ == "__main__":
#     main()
