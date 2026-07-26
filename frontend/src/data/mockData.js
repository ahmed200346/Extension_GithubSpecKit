import { tokens } from "../theme";

export const mockDataDocuments = [
  {
    id: 1,
    name: "constitution(1)",
    projectName: "Learning Platform API",
    version: "v1.0",
    status: "Finished",
    kpi: 85.6,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 90.0,
          structural_integrity_recall: 75.0,
          graph_relational_integrity: 100.0,
          macro_micro_traceability_index: 100.0,
          model_template_conformity: 100.0,
        },
        project_management_kpis: {
          health_index: 100.0,
          completeness_score: 75.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 12,
          total_edges_extracted: 6,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 100.0,
          conciseness_precision_score: 100.0,
          extraction_completeness_rate: 100.0,
          brief_word_count: 51,
          hallucinations_detected_count: 0,
        },
        project_management_kpis: {
          extracted_technologies_count: 9,
          architectural_constraints_count: 10,
          external_dependencies_count: 5,
          external_risk_exposure: "ÉLEVÉ",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 100.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 100.0,
          anti_tautology_adherence: 91.7,
          contextual_anchor_precision: 100.0,
          structural_noise_count: 0,
          case_duplicates_count: 0,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 12,
          business_domain_terms_count: 1,
          technical_stack_terms_count: 11,
          explicit_terms_count: 11,
          implicit_terms_inferred_count: 1,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 100.0,
          diagram_coverage_rate: 100.0,
          relational_completeness_rate: 100.0,
          structural_rule_adherence: 66.7,
        },
        project_management_kpis: {
          total_generated_diagrams: 3,
          diagram_types_breakdown: "2 flowcharts, 1 sequenceDiagram",
          total_mermaid_lines_count: 63,
          average_lines_per_diagram: 21.0,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 100.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 100.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 1337,
          total_source_identifiers_count: 12,
          retained_identifiers_count: 12,
          embedded_diagrams_count: 3,
          glossary_terms_count: 12,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 100.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 100.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 8,
          file_size_kb: 769.8,
          rendered_diagram_images_count: 3,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 2,
    name: "api_guidelines(1)",
    projectName: "E-Commerce Backend",
    version: "v1.2",
    status: "Finished",
    kpi: 92.3,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 95.0,
          structural_integrity_recall: 85.0,
          graph_relational_integrity: 100.0,
          macro_micro_traceability_index: 95.0,
          model_template_conformity: 100.0,
        },
        project_management_kpis: {
          health_index: 100.0,
          completeness_score: 85.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 15,
          total_edges_extracted: 8,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 100.0,
          conciseness_precision_score: 95.0,
          extraction_completeness_rate: 100.0,
          brief_word_count: 62,
          hallucinations_detected_count: 0,
        },
        project_management_kpis: {
          extracted_technologies_count: 12,
          architectural_constraints_count: 8,
          external_dependencies_count: 3,
          external_risk_exposure: "MOYEN",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 100.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 95.0,
          anti_tautology_adherence: 95.0,
          contextual_anchor_precision: 100.0,
          structural_noise_count: 0,
          case_duplicates_count: 0,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 18,
          business_domain_terms_count: 3,
          technical_stack_terms_count: 15,
          explicit_terms_count: 16,
          implicit_terms_inferred_count: 2,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 98.0,
          diagram_coverage_rate: 95.0,
          relational_completeness_rate: 97.0,
          structural_rule_adherence: 85.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 4,
          diagram_types_breakdown: "2 flowcharts, 1 sequenceDiagram, 1 classDiagram",
          total_mermaid_lines_count: 78,
          average_lines_per_diagram: 19.5,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 100.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 100.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 1850,
          total_source_identifiers_count: 18,
          retained_identifiers_count: 18,
          embedded_diagrams_count: 4,
          glossary_terms_count: 18,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 100.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 98.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 12,
          file_size_kb: 1250.5,
          rendered_diagram_images_count: 4,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 3,
    name: "security_policy(1)",
    projectName: "Healthcare Portal",
    version: "v2.0",
    status: "parsing",
    kpi: 78.9,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 85.0,
          structural_integrity_recall: 70.0,
          graph_relational_integrity: 95.0,
          macro_micro_traceability_index: 90.0,
          model_template_conformity: 95.0,
        },
        project_management_kpis: {
          health_index: 95.0,
          completeness_score: 70.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 10,
          total_edges_extracted: 5,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 95.0,
          conciseness_precision_score: 90.0,
          extraction_completeness_rate: 95.0,
          brief_word_count: 45,
          hallucinations_detected_count: 1,
        },
        project_management_kpis: {
          extracted_technologies_count: 7,
          architectural_constraints_count: 12,
          external_dependencies_count: 4,
          external_risk_exposure: "ÉLEVÉ",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 95.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 90.0,
          anti_tautology_adherence: 88.0,
          contextual_anchor_precision: 95.0,
          structural_noise_count: 1,
          case_duplicates_count: 0,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 14,
          business_domain_terms_count: 4,
          technical_stack_terms_count: 10,
          explicit_terms_count: 12,
          implicit_terms_inferred_count: 2,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 95.0,
          diagram_coverage_rate: 90.0,
          relational_completeness_rate: 92.0,
          structural_rule_adherence: 78.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 2,
          diagram_types_breakdown: "1 flowchart, 1 sequenceDiagram",
          total_mermaid_lines_count: 42,
          average_lines_per_diagram: 21.0,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 95.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 95.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 980,
          total_source_identifiers_count: 14,
          retained_identifiers_count: 14,
          embedded_diagrams_count: 2,
          glossary_terms_count: 14,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 95.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 100.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 6,
          file_size_kb: 520.3,
          rendered_diagram_images_count: 2,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 4,
    name: "architecture_decision_records(1)",
    projectName: "IoT Platform",
    version: "v1.5",
    status: "parallel_enrichment",
    kpi: 88.2,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 92.0,
          structural_integrity_recall: 80.0,
          graph_relational_integrity: 100.0,
          macro_micro_traceability_index: 95.0,
          model_template_conformity: 100.0,
        },
        project_management_kpis: {
          health_index: 100.0,
          completeness_score: 80.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 14,
          total_edges_extracted: 7,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 100.0,
          conciseness_precision_score: 95.0,
          extraction_completeness_rate: 100.0,
          brief_word_count: 58,
          hallucinations_detected_count: 0,
        },
        project_management_kpis: {
          extracted_technologies_count: 10,
          architectural_constraints_count: 9,
          external_dependencies_count: 6,
          external_risk_exposure: "MOYEN",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 100.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 95.0,
          anti_tautology_adherence: 93.0,
          contextual_anchor_precision: 100.0,
          structural_noise_count: 0,
          case_duplicates_count: 1,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 16,
          business_domain_terms_count: 2,
          technical_stack_terms_count: 14,
          explicit_terms_count: 14,
          implicit_terms_inferred_count: 2,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 100.0,
          diagram_coverage_rate: 97.0,
          relational_completeness_rate: 98.0,
          structural_rule_adherence: 90.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 5,
          diagram_types_breakdown: "3 flowcharts, 1 sequenceDiagram, 1 classDiagram",
          total_mermaid_lines_count: 95,
          average_lines_per_diagram: 19.0,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 100.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 100.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 1520,
          total_source_identifiers_count: 16,
          retained_identifiers_count: 16,
          embedded_diagrams_count: 5,
          glossary_terms_count: 16,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 100.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 100.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 10,
          file_size_kb: 980.2,
          rendered_diagram_images_count: 5,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 5,
    name: "deployment_guide(1)",
    projectName: "Mobile Banking App",
    version: "v1.0",
    status: "writing",
    kpi: 81.5,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 88.0,
          structural_integrity_recall: 72.0,
          graph_relational_integrity: 95.0,
          macro_micro_traceability_index: 92.0,
          model_template_conformity: 98.0,
        },
        project_management_kpis: {
          health_index: 98.0,
          completeness_score: 72.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 11,
          total_edges_extracted: 5,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 95.0,
          conciseness_precision_score: 90.0,
          extraction_completeness_rate: 95.0,
          brief_word_count: 48,
          hallucinations_detected_count: 0,
        },
        project_management_kpis: {
          extracted_technologies_count: 8,
          architectural_constraints_count: 7,
          external_dependencies_count: 4,
          external_risk_exposure: "FAIBLE",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 95.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 92.0,
          anti_tautology_adherence: 90.0,
          contextual_anchor_precision: 95.0,
          structural_noise_count: 0,
          case_duplicates_count: 0,
          classification_errors_count: 1,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 10,
          business_domain_terms_count: 2,
          technical_stack_terms_count: 8,
          explicit_terms_count: 9,
          implicit_terms_inferred_count: 1,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 97.0,
          diagram_coverage_rate: 93.0,
          relational_completeness_rate: 95.0,
          structural_rule_adherence: 82.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 3,
          diagram_types_breakdown: "2 flowcharts, 1 sequenceDiagram",
          total_mermaid_lines_count: 55,
          average_lines_per_diagram: 18.3,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 95.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 95.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 1100,
          total_source_identifiers_count: 10,
          retained_identifiers_count: 10,
          embedded_diagrams_count: 3,
          glossary_terms_count: 10,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 98.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 97.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 7,
          file_size_kb: 650.4,
          rendered_diagram_images_count: 3,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 6,
    name: "api_reference(1)",
    projectName: "Learning Platform API",
    version: "v2.1",
    status: "Finished",
    kpi: 94.7,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 98.0,
          structural_integrity_recall: 90.0,
          graph_relational_integrity: 100.0,
          macro_micro_traceability_index: 98.0,
          model_template_conformity: 100.0,
        },
        project_management_kpis: {
          health_index: 100.0,
          completeness_score: 90.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 18,
          total_edges_extracted: 10,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 100.0,
          conciseness_precision_score: 98.0,
          extraction_completeness_rate: 100.0,
          brief_word_count: 70,
          hallucinations_detected_count: 0,
        },
        project_management_kpis: {
          extracted_technologies_count: 14,
          architectural_constraints_count: 11,
          external_dependencies_count: 2,
          external_risk_exposure: "FAIBLE",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 100.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 98.0,
          anti_tautology_adherence: 96.0,
          contextual_anchor_precision: 100.0,
          structural_noise_count: 0,
          case_duplicates_count: 0,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 20,
          business_domain_terms_count: 4,
          technical_stack_terms_count: 16,
          explicit_terms_count: 18,
          implicit_terms_inferred_count: 2,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 100.0,
          diagram_coverage_rate: 100.0,
          relational_completeness_rate: 100.0,
          structural_rule_adherence: 92.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 6,
          diagram_types_breakdown: "3 flowcharts, 2 sequenceDiagram, 1 classDiagram",
          total_mermaid_lines_count: 110,
          average_lines_per_diagram: 18.3,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 100.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 100.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 2100,
          total_source_identifiers_count: 20,
          retained_identifiers_count: 20,
          embedded_diagrams_count: 6,
          glossary_terms_count: 20,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 100.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 100.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 14,
          file_size_kb: 1420.6,
          rendered_diagram_images_count: 6,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 7,
    name: "test_strategy(1)",
    projectName: "E-Commerce Backend",
    version: "v1.3",
    status: "layout",
    kpi: 76.4,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 82.0,
          structural_integrity_recall: 68.0,
          graph_relational_integrity: 92.0,
          macro_micro_traceability_index: 88.0,
          model_template_conformity: 92.0,
        },
        project_management_kpis: {
          health_index: 92.0,
          completeness_score: 68.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 9,
          total_edges_extracted: 4,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 90.0,
          conciseness_precision_score: 85.0,
          extraction_completeness_rate: 90.0,
          brief_word_count: 40,
          hallucinations_detected_count: 1,
        },
        project_management_kpis: {
          extracted_technologies_count: 6,
          architectural_constraints_count: 8,
          external_dependencies_count: 5,
          external_risk_exposure: "ÉLEVÉ",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 90.0,
          categorization_accuracy_rate: 95.0,
          definition_precision_score: 88.0,
          anti_tautology_adherence: 85.0,
          contextual_anchor_precision: 90.0,
          structural_noise_count: 2,
          case_duplicates_count: 1,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 8,
          business_domain_terms_count: 2,
          technical_stack_terms_count: 6,
          explicit_terms_count: 7,
          implicit_terms_inferred_count: 1,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 92.0,
          diagram_coverage_rate: 88.0,
          relational_completeness_rate: 90.0,
          structural_rule_adherence: 75.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 2,
          diagram_types_breakdown: "1 flowchart, 1 sequenceDiagram",
          total_mermaid_lines_count: 38,
          average_lines_per_diagram: 19.0,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 90.0,
          traceability_preservation_rate: 95.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 90.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 850,
          total_source_identifiers_count: 8,
          retained_identifiers_count: 8,
          embedded_diagrams_count: 2,
          glossary_terms_count: 8,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 95.0,
          page_budget_adherence: 92.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 95.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 5,
          file_size_kb: 420.1,
          rendered_diagram_images_count: 2,
          overflow_events_detected_count: 1,
        },
      },
    },
  },
  {
    id: 8,
    name: "user_manual(1)",
    projectName: "Healthcare Portal",
    version: "v1.8",
    status: "Finished",
    kpi: 90.1,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 94.0,
          structural_integrity_recall: 82.0,
          graph_relational_integrity: 100.0,
          macro_micro_traceability_index: 96.0,
          model_template_conformity: 100.0,
        },
        project_management_kpis: {
          health_index: 100.0,
          completeness_score: 82.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 13,
          total_edges_extracted: 7,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 100.0,
          conciseness_precision_score: 92.0,
          extraction_completeness_rate: 98.0,
          brief_word_count: 55,
          hallucinations_detected_count: 0,
        },
        project_management_kpis: {
          extracted_technologies_count: 11,
          architectural_constraints_count: 9,
          external_dependencies_count: 3,
          external_risk_exposure: "MOYEN",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 100.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 96.0,
          anti_tautology_adherence: 94.0,
          contextual_anchor_precision: 100.0,
          structural_noise_count: 0,
          case_duplicates_count: 0,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 15,
          business_domain_terms_count: 3,
          technical_stack_terms_count: 12,
          explicit_terms_count: 13,
          implicit_terms_inferred_count: 2,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 99.0,
          diagram_coverage_rate: 96.0,
          relational_completeness_rate: 97.0,
          structural_rule_adherence: 88.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 4,
          diagram_types_breakdown: "2 flowcharts, 1 sequenceDiagram, 1 classDiagram",
          total_mermaid_lines_count: 72,
          average_lines_per_diagram: 18.0,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 100.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 100.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 1650,
          total_source_identifiers_count: 15,
          retained_identifiers_count: 15,
          embedded_diagrams_count: 4,
          glossary_terms_count: 15,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 100.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 99.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 9,
          file_size_kb: 820.7,
          rendered_diagram_images_count: 4,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 9,
    name: "changelog_release_notes(1)",
    projectName: "IoT Platform",
    version: "v1.0",
    status: "parallel_enrichment",
    kpi: 83.7,
    viewer: "view",
    agentEvaluations: {
      parsing: {
        agent_evaluated: "Parsing Agent",
        technical_evaluation: {
          schema_adherence_rate: 87.0,
          structural_integrity_recall: 73.0,
          graph_relational_integrity: 96.0,
          macro_micro_traceability_index: 91.0,
          model_template_conformity: 96.0,
        },
        project_management_kpis: {
          health_index: 96.0,
          completeness_score: 73.0,
          readiness_status: "READY_FOR_EXECUTION",
          total_nodes_extracted: 10,
          total_edges_extracted: 5,
        },
      },
      summary: {
        agent_evaluated: "Summary Agent",
        technical_evaluation: {
          maturity_alignment_score: 96.0,
          conciseness_precision_score: 88.0,
          extraction_completeness_rate: 94.0,
          brief_word_count: 42,
          hallucinations_detected_count: 0,
        },
        project_management_kpis: {
          extracted_technologies_count: 7,
          architectural_constraints_count: 6,
          external_dependencies_count: 4,
          external_risk_exposure: "FAIBLE",
        },
      },
      glossary: {
        agent_evaluated: "Glossary Agent",
        technical_evaluation: {
          term_coverage_rate: 94.0,
          categorization_accuracy_rate: 100.0,
          definition_precision_score: 90.0,
          anti_tautology_adherence: 89.0,
          contextual_anchor_precision: 94.0,
          structural_noise_count: 1,
          case_duplicates_count: 0,
          classification_errors_count: 0,
          language_drift_detected: false,
        },
        project_management_kpis: {
          total_extracted_terms: 9,
          business_domain_terms_count: 2,
          technical_stack_terms_count: 7,
          explicit_terms_count: 8,
          implicit_terms_inferred_count: 1,
        },
      },
      diagram: {
        agent_evaluated: "Diagram Agent",
        technical_evaluation: {
          syntax_validity_rate: 96.0,
          diagram_coverage_rate: 91.0,
          relational_completeness_rate: 93.0,
          structural_rule_adherence: 80.0,
        },
        project_management_kpis: {
          total_generated_diagrams: 3,
          diagram_types_breakdown: "2 flowcharts, 1 sequenceDiagram",
          total_mermaid_lines_count: 50,
          average_lines_per_diagram: 16.7,
        },
      },
      docWriter: {
        agent_evaluated: "Documentation Writer Agent",
        technical_evaluation: {
          document_structure_completeness: 96.0,
          traceability_preservation_rate: 100.0,
          diagram_embedding_validity: 100.0,
          glossary_format_and_placement: 96.0,
        },
        project_management_kpis: {
          total_markdown_word_count: 920,
          total_source_identifiers_count: 9,
          retained_identifiers_count: 9,
          embedded_diagrams_count: 2,
          glossary_terms_count: 9,
        },
      },
      layout: {
        agent_evaluated: "Layout Agent",
        technical_evaluation: {
          render_success_rate: 100.0,
          diagram_visual_render_rate: 100.0,
          page_budget_adherence: 96.0,
          visual_overflow_rate: 100.0,
          styling_consistency_score: 98.0,
        },
        project_management_kpis: {
          pdf_generated_success: true,
          total_pdf_pages_count: 6,
          file_size_kb: 480.3,
          rendered_diagram_images_count: 2,
          overflow_events_detected_count: 0,
        },
      },
    },
  },
  {
    id: 9,
    name: "Incident Response Playbook",
    version: "v1.8",
    kpi: "Security",
    viewer: "view",
  },
];

export const mockDataTeam = [
  {
    id: 1,
    name: "Jon Snow",
    email: "jonsnow@gmail.com",
    age: 35,
    phone: "(665)121-5454",
    access: "admin",
  },
  {
    id: 2,
    name: "Cersei Lannister",
    email: "cerseilannister@gmail.com",
    age: 42,
    phone: "(421)314-2288",
    access: "manager",
  },
  {
    id: 3,
    name: "Jaime Lannister",
    email: "jaimelannister@gmail.com",
    age: 45,
    phone: "(422)982-6739",
    access: "user",
  },
  {
    id: 4,
    name: "Anya Stark",
    email: "anyastark@gmail.com",
    age: 16,
    phone: "(921)425-6742",
    access: "admin",
  },
  {
    id: 5,
    name: "Daenerys Targaryen",
    email: "daenerystargaryen@gmail.com",
    age: 31,
    phone: "(421)445-1189",
    access: "user",
  },
  {
    id: 6,
    name: "Ever Melisandre",
    email: "evermelisandre@gmail.com",
    age: 150,
    phone: "(232)545-6483",
    access: "manager",
  },
  {
    id: 7,
    name: "Ferrara Clifford",
    email: "ferraraclifford@gmail.com",
    age: 44,
    phone: "(543)124-0123",
    access: "user",
  },
  {
    id: 8,
    name: "Rossini Frances",
    email: "rossinifrances@gmail.com",
    age: 36,
    phone: "(222)444-5555",
    access: "user",
  },
  {
    id: 9,
    name: "Harvey Roxie",
    email: "harveyroxie@gmail.com",
    age: 65,
    phone: "(444)555-6239",
    access: "admin",
  },
];

export const mockDataContacts = [
  {
    id: 1,
    name: "Jon Snow",
    email: "jonsnow@gmail.com",
    age: 35,
    phone: "(665)121-5454",
    address: "0912 Won Street, Alabama, SY 10001",
    city: "New York",
    zipCode: "10001",
    registrarId: 123512,
  },
  {
    id: 2,
    name: "Cersei Lannister",
    email: "cerseilannister@gmail.com",
    age: 42,
    phone: "(421)314-2288",
    address: "1234 Main Street, New York, NY 10001",
    city: "New York",
    zipCode: "13151",
    registrarId: 123512,
  },
  {
    id: 3,
    name: "Jaime Lannister",
    email: "jaimelannister@gmail.com",
    age: 45,
    phone: "(422)982-6739",
    address: "3333 Want Blvd, Estanza, NAY 42125",
    city: "New York",
    zipCode: "87281",
    registrarId: 4132513,
  },
  {
    id: 4,
    name: "Anya Stark",
    email: "anyastark@gmail.com",
    age: 16,
    phone: "(921)425-6742",
    address: "1514 Main Street, New York, NY 22298",
    city: "New York",
    zipCode: "15551",
    registrarId: 123512,
  },
  {
    id: 5,
    name: "Daenerys Targaryen",
    email: "daenerystargaryen@gmail.com",
    age: 31,
    phone: "(421)445-1189",
    address: "11122 Welping Ave, Tenting, CD 21321",
    city: "Tenting",
    zipCode: "14215",
    registrarId: 123512,
  },
  {
    id: 6,
    name: "Ever Melisandre",
    email: "evermelisandre@gmail.com",
    age: 150,
    phone: "(232)545-6483",
    address: "1234 Canvile Street, Esvazark, NY 10001",
    city: "Esvazark",
    zipCode: "10001",
    registrarId: 123512,
  },
  {
    id: 7,
    name: "Ferrara Clifford",
    email: "ferraraclifford@gmail.com",
    age: 44,
    phone: "(543)124-0123",
    address: "22215 Super Street, Everting, ZO 515234",
    city: "Evertin",
    zipCode: "51523",
    registrarId: 123512,
  },
  {
    id: 8,
    name: "Rossini Frances",
    email: "rossinifrances@gmail.com",
    age: 36,
    phone: "(222)444-5555",
    address: "4123 Ever Blvd, Wentington, AD 142213",
    city: "Esteras",
    zipCode: "44215",
    registrarId: 512315,
  },
  {
    id: 9,
    name: "Harvey Roxie",
    email: "harveyroxie@gmail.com",
    age: 65,
    phone: "(444)555-6239",
    address: "51234 Avery Street, Cantory, ND 212412",
    city: "Colunza",
    zipCode: "111234",
    registrarId: 928397,
  },
  {
    id: 10,
    name: "Enteri Redack",
    email: "enteriredack@gmail.com",
    age: 42,
    phone: "(222)444-5555",
    address: "4123 Easer Blvd, Wentington, AD 142213",
    city: "Esteras",
    zipCode: "44215",
    registrarId: 533215,
  },
  {
    id: 11,
    name: "Steve Goodman",
    email: "stevegoodmane@gmail.com",
    age: 11,
    phone: "(444)555-6239",
    address: "51234 Fiveton Street, CunFory, ND 212412",
    city: "Colunza",
    zipCode: "1234",
    registrarId: 92197,
  },
];

export const mockDataInvoices = [
  {
    id: 1,
    name: "Jon Snow",
    email: "jonsnow@gmail.com",
    cost: "21.24",
    phone: "(665)121-5454",
    date: "03/12/2022",
  },
  {
    id: 2,
    name: "Cersei Lannister",
    email: "cerseilannister@gmail.com",
    cost: "1.24",
    phone: "(421)314-2288",
    date: "06/15/2021",
  },
  {
    id: 3,
    name: "Jaime Lannister",
    email: "jaimelannister@gmail.com",
    cost: "11.24",
    phone: "(422)982-6739",
    date: "05/02/2022",
  },
  {
    id: 4,
    name: "Anya Stark",
    email: "anyastark@gmail.com",
    cost: "80.55",
    phone: "(921)425-6742",
    date: "03/21/2022",
  },
  {
    id: 5,
    name: "Daenerys Targaryen",
    email: "daenerystargaryen@gmail.com",
    cost: "1.24",
    phone: "(421)445-1189",
    date: "01/12/2021",
  },
  {
    id: 6,
    name: "Ever Melisandre",
    email: "evermelisandre@gmail.com",
    cost: "63.12",
    phone: "(232)545-6483",
    date: "11/02/2022",
  },
  {
    id: 7,
    name: "Ferrara Clifford",
    email: "ferraraclifford@gmail.com",
    cost: "52.42",
    phone: "(543)124-0123",
    date: "02/11/2022",
  },
  {
    id: 8,
    name: "Rossini Frances",
    email: "rossinifrances@gmail.com",
    cost: "21.24",
    phone: "(222)444-5555",
    date: "05/02/2021",
  },
];

export const mockTransactions = [
  {
    txId: "01e4dsa",
    user: "johndoe",
    date: "2021-09-01",
    cost: "43.95",
  },
  {
    txId: "0315dsaa",
    user: "jackdower",
    date: "2022-04-01",
    cost: "133.45",
  },
  {
    txId: "01e4dsa",
    user: "aberdohnny",
    date: "2021-09-01",
    cost: "43.95",
  },
  {
    txId: "51034szv",
    user: "goodmanave",
    date: "2022-11-05",
    cost: "200.95",
  },
  {
    txId: "0a123sb",
    user: "stevebower",
    date: "2022-11-02",
    cost: "13.55",
  },
  {
    txId: "01e4dsa",
    user: "aberdohnny",
    date: "2021-09-01",
    cost: "43.95",
  },
  {
    txId: "120s51a",
    user: "wootzifer",
    date: "2019-04-15",
    cost: "24.20",
  },
  {
    txId: "0315dsaa",
    user: "jackdower",
    date: "2022-04-01",
    cost: "133.45",
  },
];

export const mockBarData = [
  {
    country: "AD",
    "hot dog": 137,
    "hot dogColor": "hsl(229, 70%, 50%)",
    burger: 96,
    burgerColor: "hsl(296, 70%, 50%)",
    kebab: 72,
    kebabColor: "hsl(97, 70%, 50%)",
    donut: 140,
    donutColor: "hsl(340, 70%, 50%)",
  },
  {
    country: "AE",
    "hot dog": 55,
    "hot dogColor": "hsl(307, 70%, 50%)",
    burger: 28,
    burgerColor: "hsl(111, 70%, 50%)",
    kebab: 58,
    kebabColor: "hsl(273, 70%, 50%)",
    donut: 29,
    donutColor: "hsl(275, 70%, 50%)",
  },
  {
    country: "AF",
    "hot dog": 109,
    "hot dogColor": "hsl(72, 70%, 50%)",
    burger: 23,
    burgerColor: "hsl(96, 70%, 50%)",
    kebab: 34,
    kebabColor: "hsl(106, 70%, 50%)",
    donut: 152,
    donutColor: "hsl(256, 70%, 50%)",
  },
  {
    country: "AG",
    "hot dog": 133,
    "hot dogColor": "hsl(257, 70%, 50%)",
    burger: 52,
    burgerColor: "hsl(326, 70%, 50%)",
    kebab: 43,
    kebabColor: "hsl(110, 70%, 50%)",
    donut: 83,
    donutColor: "hsl(9, 70%, 50%)",
  },
  {
    country: "AI",
    "hot dog": 81,
    "hot dogColor": "hsl(190, 70%, 50%)",
    burger: 80,
    burgerColor: "hsl(325, 70%, 50%)",
    kebab: 112,
    kebabColor: "hsl(54, 70%, 50%)",
    donut: 35,
    donutColor: "hsl(285, 70%, 50%)",
  },
  {
    country: "AL",
    "hot dog": 66,
    "hot dogColor": "hsl(208, 70%, 50%)",
    burger: 111,
    burgerColor: "hsl(334, 70%, 50%)",
    kebab: 167,
    kebabColor: "hsl(182, 70%, 50%)",
    donut: 18,
    donutColor: "hsl(76, 70%, 50%)",
  },
  {
    country: "AM",
    "hot dog": 80,
    "hot dogColor": "hsl(87, 70%, 50%)",
    burger: 47,
    burgerColor: "hsl(141, 70%, 50%)",
    kebab: 158,
    kebabColor: "hsl(224, 70%, 50%)",
    donut: 49,
    donutColor: "hsl(274, 70%, 50%)",
  },
];

export const mockPieData = [
  {
    id: "hack",
    label: "hack",
    value: 239,
    color: "hsl(104, 70%, 50%)",
  },
  {
    id: "make",
    label: "make",
    value: 170,
    color: "hsl(162, 70%, 50%)",
  },
  {
    id: "go",
    label: "go",
    value: 322,
    color: "hsl(291, 70%, 50%)",
  },
  {
    id: "lisp",
    label: "lisp",
    value: 503,
    color: "hsl(229, 70%, 50%)",
  },
  {
    id: "scala",
    label: "scala",
    value: 584,
    color: "hsl(344, 70%, 50%)",
  },
];

export const mockLineData = [
  {
    id: "japan",
    color: tokens("dark").greenAccent[500],
    data: [
      {
        x: "plane",
        y: 101,
      },
      {
        x: "helicopter",
        y: 75,
      },
      {
        x: "boat",
        y: 36,
      },
      {
        x: "train",
        y: 216,
      },
      {
        x: "subway",
        y: 35,
      },
      {
        x: "bus",
        y: 236,
      },
      {
        x: "car",
        y: 88,
      },
      {
        x: "moto",
        y: 232,
      },
      {
        x: "bicycle",
        y: 281,
      },
      {
        x: "horse",
        y: 1,
      },
      {
        x: "skateboard",
        y: 35,
      },
      {
        x: "others",
        y: 14,
      },
    ],
  },
  {
    id: "france",
    color: tokens("dark").blueAccent[300],
    data: [
      {
        x: "plane",
        y: 212,
      },
      {
        x: "helicopter",
        y: 190,
      },
      {
        x: "boat",
        y: 270,
      },
      {
        x: "train",
        y: 9,
      },
      {
        x: "subway",
        y: 75,
      },
      {
        x: "bus",
        y: 175,
      },
      {
        x: "car",
        y: 33,
      },
      {
        x: "moto",
        y: 189,
      },
      {
        x: "bicycle",
        y: 97,
      },
      {
        x: "horse",
        y: 87,
      },
      {
        x: "skateboard",
        y: 299,
      },
      {
        x: "others",
        y: 251,
      },
    ],
  },
  {
    id: "us",
    color: tokens("dark").redAccent[200],
    data: [
      {
        x: "plane",
        y: 191,
      },
      {
        x: "helicopter",
        y: 136,
      },
      {
        x: "boat",
        y: 91,
      },
      {
        x: "train",
        y: 190,
      },
      {
        x: "subway",
        y: 211,
      },
      {
        x: "bus",
        y: 152,
      },
      {
        x: "car",
        y: 189,
      },
      {
        x: "moto",
        y: 152,
      },
      {
        x: "bicycle",
        y: 8,
      },
      {
        x: "horse",
        y: 197,
      },
      {
        x: "skateboard",
        y: 107,
      },
      {
        x: "others",
        y: 170,
      },
    ],
  },
];

export const mockGeographyData = [
  {
    id: "AFG",
    value: 520600,
  },
  {
    id: "AGO",
    value: 949905,
  },
  {
    id: "ALB",
    value: 329910,
  },
  {
    id: "ARE",
    value: 675484,
  },
  {
    id: "ARG",
    value: 432239,
  },
  {
    id: "ARM",
    value: 288305,
  },
  {
    id: "ATA",
    value: 415648,
  },
  {
    id: "ATF",
    value: 665159,
  },
  {
    id: "AUT",
    value: 798526,
  },
  {
    id: "AZE",
    value: 481678,
  },
  {
    id: "BDI",
    value: 496457,
  },
  {
    id: "BEL",
    value: 252276,
  },
  {
    id: "BEN",
    value: 440315,
  },
  {
    id: "BFA",
    value: 343752,
  },
  {
    id: "BGD",
    value: 920203,
  },
  {
    id: "BGR",
    value: 261196,
  },
  {
    id: "BHS",
    value: 421551,
  },
  {
    id: "BIH",
    value: 974745,
  },
  {
    id: "BLR",
    value: 349288,
  },
  {
    id: "BLZ",
    value: 305983,
  },
  {
    id: "BOL",
    value: 430840,
  },
  {
    id: "BRN",
    value: 345666,
  },
  {
    id: "BTN",
    value: 649678,
  },
  {
    id: "BWA",
    value: 319392,
  },
  {
    id: "CAF",
    value: 722549,
  },
  {
    id: "CAN",
    value: 332843,
  },
  {
    id: "CHE",
    value: 122159,
  },
  {
    id: "CHL",
    value: 811736,
  },
  {
    id: "CHN",
    value: 593604,
  },
  {
    id: "CIV",
    value: 143219,
  },
  {
    id: "CMR",
    value: 630627,
  },
  {
    id: "COG",
    value: 498556,
  },
  {
    id: "COL",
    value: 660527,
  },
  {
    id: "CRI",
    value: 60262,
  },
  {
    id: "CUB",
    value: 177870,
  },
  {
    id: "-99",
    value: 463208,
  },
  {
    id: "CYP",
    value: 945909,
  },
  {
    id: "CZE",
    value: 500109,
  },
  {
    id: "DEU",
    value: 63345,
  },
  {
    id: "DJI",
    value: 634523,
  },
  {
    id: "DNK",
    value: 731068,
  },
  {
    id: "DOM",
    value: 262538,
  },
  {
    id: "DZA",
    value: 760695,
  },
  {
    id: "ECU",
    value: 301263,
  },
  {
    id: "EGY",
    value: 148475,
  },
  {
    id: "ERI",
    value: 939504,
  },
  {
    id: "ESP",
    value: 706050,
  },
  {
    id: "EST",
    value: 977015,
  },
  {
    id: "ETH",
    value: 461734,
  },
  {
    id: "FIN",
    value: 22800,
  },
  {
    id: "FJI",
    value: 18985,
  },
  {
    id: "FLK",
    value: 64986,
  },
  {
    id: "FRA",
    value: 447457,
  },
  {
    id: "GAB",
    value: 669675,
  },
  {
    id: "GBR",
    value: 757120,
  },
  {
    id: "GEO",
    value: 158702,
  },
  {
    id: "GHA",
    value: 893180,
  },
  {
    id: "GIN",
    value: 877288,
  },
  {
    id: "GMB",
    value: 724530,
  },
  {
    id: "GNB",
    value: 387753,
  },
  {
    id: "GNQ",
    value: 706118,
  },
  {
    id: "GRC",
    value: 377796,
  },
  {
    id: "GTM",
    value: 66890,
  },
  {
    id: "GUY",
    value: 719300,
  },
  {
    id: "HND",
    value: 739590,
  },
  {
    id: "HRV",
    value: 929467,
  },
  {
    id: "HTI",
    value: 538961,
  },
  {
    id: "HUN",
    value: 146095,
  },
  {
    id: "IDN",
    value: 490681,
  },
  {
    id: "IND",
    value: 549818,
  },
  {
    id: "IRL",
    value: 630163,
  },
  {
    id: "IRN",
    value: 596921,
  },
  {
    id: "IRQ",
    value: 767023,
  },
  {
    id: "ISL",
    value: 478682,
  },
  {
    id: "ISR",
    value: 963688,
  },
  {
    id: "ITA",
    value: 393089,
  },
  {
    id: "JAM",
    value: 83173,
  },
  {
    id: "JOR",
    value: 52005,
  },
  {
    id: "JPN",
    value: 199174,
  },
  {
    id: "KAZ",
    value: 181424,
  },
  {
    id: "KEN",
    value: 60946,
  },
  {
    id: "KGZ",
    value: 432478,
  },
  {
    id: "KHM",
    value: 254461,
  },
  {
    id: "OSA",
    value: 942447,
  },
  {
    id: "KWT",
    value: 414413,
  },
  {
    id: "LAO",
    value: 448339,
  },
  {
    id: "LBN",
    value: 620090,
  },
  {
    id: "LBR",
    value: 435950,
  },
  {
    id: "LBY",
    value: 75091,
  },
  {
    id: "LKA",
    value: 595124,
  },
  {
    id: "LSO",
    value: 483524,
  },
  {
    id: "LTU",
    value: 867357,
  },
  {
    id: "LUX",
    value: 689172,
  },
  {
    id: "LVA",
    value: 742980,
  },
  {
    id: "MAR",
    value: 236538,
  },
  {
    id: "MDA",
    value: 926836,
  },
  {
    id: "MDG",
    value: 840840,
  },
  {
    id: "MEX",
    value: 353910,
  },
  {
    id: "MKD",
    value: 505842,
  },
  {
    id: "MLI",
    value: 286082,
  },
  {
    id: "MMR",
    value: 915544,
  },
  {
    id: "MNE",
    value: 609500,
  },
  {
    id: "MNG",
    value: 410428,
  },
  {
    id: "MOZ",
    value: 32868,
  },
  {
    id: "MRT",
    value: 375671,
  },
  {
    id: "MWI",
    value: 591935,
  },
  {
    id: "MYS",
    value: 991644,
  },
  {
    id: "NAM",
    value: 701897,
  },
  {
    id: "NCL",
    value: 144098,
  },
  {
    id: "NER",
    value: 312944,
  },
  {
    id: "NGA",
    value: 862877,
  },
  {
    id: "NIC",
    value: 90831,
  },
  {
    id: "NLD",
    value: 281879,
  },
  {
    id: "NOR",
    value: 224537,
  },
  {
    id: "NPL",
    value: 322331,
  },
  {
    id: "NZL",
    value: 86615,
  },
  {
    id: "OMN",
    value: 707881,
  },
  {
    id: "PAK",
    value: 158577,
  },
  {
    id: "PAN",
    value: 738579,
  },
  {
    id: "PER",
    value: 248751,
  },
  {
    id: "PHL",
    value: 557292,
  },
  {
    id: "PNG",
    value: 516874,
  },
  {
    id: "POL",
    value: 682137,
  },
  {
    id: "PRI",
    value: 957399,
  },
  {
    id: "PRT",
    value: 846430,
  },
  {
    id: "PRY",
    value: 720555,
  },
  {
    id: "QAT",
    value: 478726,
  },
  {
    id: "ROU",
    value: 259318,
  },
  {
    id: "RUS",
    value: 268735,
  },
  {
    id: "RWA",
    value: 136781,
  },
  {
    id: "ESH",
    value: 151957,
  },
  {
    id: "SAU",
    value: 111821,
  },
  {
    id: "SDN",
    value: 927112,
  },
  {
    id: "SDS",
    value: 966473,
  },
  {
    id: "SEN",
    value: 158085,
  },
  {
    id: "SLB",
    value: 178389,
  },
  {
    id: "SLE",
    value: 528433,
  },
  {
    id: "SLV",
    value: 353467,
  },
  {
    id: "ABV",
    value: 251,
  },
  {
    id: "SOM",
    value: 445243,
  },
  {
    id: "SRB",
    value: 202402,
  },
  {
    id: "SUR",
    value: 972121,
  },
  {
    id: "SVK",
    value: 319923,
  },
  {
    id: "SVN",
    value: 728766,
  },
  {
    id: "SWZ",
    value: 379669,
  },
  {
    id: "SYR",
    value: 16221,
  },
  {
    id: "TCD",
    value: 101273,
  },
  {
    id: "TGO",
    value: 498411,
  },
  {
    id: "THA",
    value: 506906,
  },
  {
    id: "TJK",
    value: 613093,
  },
  {
    id: "TKM",
    value: 327016,
  },
  {
    id: "TLS",
    value: 607972,
  },
  {
    id: "TTO",
    value: 936365,
  },
  {
    id: "TUN",
    value: 898416,
  },
  {
    id: "TUR",
    value: 237783,
  },
  {
    id: "TWN",
    value: 878213,
  },
  {
    id: "TZA",
    value: 442174,
  },
  {
    id: "UGA",
    value: 720710,
  },
  {
    id: "UKR",
    value: 74172,
  },
  {
    id: "URY",
    value: 753177,
  },
  {
    id: "USA",
    value: 658725,
  },
  {
    id: "UZB",
    value: 550313,
  },
  {
    id: "VEN",
    value: 707492,
  },
  {
    id: "VNM",
    value: 538907,
  },
  {
    id: "VUT",
    value: 650646,
  },
  {
    id: "PSE",
    value: 476078,
  },
  {
    id: "YEM",
    value: 957751,
  },
  {
    id: "ZAF",
    value: 836949,
  },
  {
    id: "ZMB",
    value: 714503,
  },
  {
    id: "ZWE",
    value: 405217,
  },
  {
    id: "KOR",
    value: 171135,
  },
];
