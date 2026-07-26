# app/services/evaluation_service.py
from typing import Dict, Any, List

# Importation unifiée des schémas de production
from app.schemas.parsing_agent_schema import ParsingAgentOutput
from app.schemas.summary_agent_schema import SummaryOutputModel
from app.schemas.glossary_agent_schema import GlossaryOutputModel
from app.schemas.diagram_agent_schema import DiagramOutputModel


class ParsingEvaluatorService:
    """
    Service autonome d'évaluation et de calcul de métriques de fiabilité (QA)
    et de pilotage (Gestion de Projet) pour les documents techniques de Spec Kit.
    Analyse structurelle avancée basée sur la topologie du graphe et la traçabilité macro/micro.
    """

    @classmethod
    def evaluate(cls, parsed_data: ParsingAgentOutput, template_config: Dict[str, Any]) -> Dict[str, Any]:
        doc_type = parsed_data.doc_type.value

        # 1. Calcul des métriques de fiabilité technique et topologique (QA)
        technical_metrics = cls._calculate_technical_metrics(parsed_data, template_config, doc_type)

        # 2. Calcul des KPI de gestion de projet et maturité (Management)
        management_kpis = cls._calculate_management_kpis(parsed_data, template_config, doc_type)

        return {
            "document_type": doc_type,
            "project_name": parsed_data.project_info.get("project_name", "Inconnu"),
            "technical_evaluation": technical_metrics,
            "project_management_kpis": management_kpis
        }

    @staticmethod
    def _calculate_technical_metrics(
        parsed_data: ParsingAgentOutput, 
        template_config: Dict[str, Any],
        doc_type: str
    ) -> Dict[str, Any]:
        filler_words = ["tbd", "n/a", "none", "not specified", "todo", "a definir", "manquant"]
        semantic_voids = 0
        truncations = 0
        quality_alerts = []

        for section in parsed_data.sections:
            content_clean = section.raw_content.lower().strip()
            if any(filler == content_clean or f"[{filler}]" in content_clean for filler in filler_words):
                semantic_voids += 1
            if "..." in section.raw_content or "etc." in section.raw_content.lower():
                truncations += 1

        sar_score = max(0.0, 100.0 - (semantic_voids * 20.0) - (truncations * 10.0))

        required_sections = template_config.get(doc_type, {}).get("required_sections", [])
        required_names = {sec["name"].lower().strip() for sec in required_sections}
        mapped_fields = {s.mapped_to_template_field.lower().strip() for s in parsed_data.sections if s.mapped_to_template_field}
        
        if required_names:
            missing_sections = required_names.difference(mapped_fields)
            sir_score = ((len(required_names) - len(missing_sections)) / len(required_names)) * 100.0
            for missing in missing_sections:
                quality_alerts.append(f"Section requise absente des correspondances : {missing}")
        else:
            sir_score = 100.0

        elements = parsed_data.elements
        relationships = parsed_data.relationships
        
        if not relationships:
            gri_score = 100.0
        else:
            valid_nodes = set()
            for el in elements:
                if el.identifier:
                    valid_nodes.add(str(el.identifier).lower().strip())
                if el.content:
                    valid_nodes.add(el.content[:30].lower().strip())

            valid_relations = 0
            for rel in relationships:
                src = str(rel.source).lower().strip()
                tgt = str(rel.to).lower().strip()
                
                src_valid = any(src in node or node in src for node in valid_nodes)
                tgt_valid = any(tgt in node or node in tgt for node in valid_nodes)
                
                if src_valid and tgt_valid:
                    valid_relations += 1
                else:
                    quality_alerts.append(f"Relation orpheline détectée : Lien brisé entre '{rel.source}' et '{rel.to}'")
            
            gri_score = (valid_relations / len(relationships)) * 100.0

        if not elements:
            mmti_score = 100.0
        else:
            valid_section_titles = {s.title.lower().strip() for s in parsed_data.sections}
            linked_elements = 0
            
            for el in elements:
                if el.source_section and el.source_section.lower().strip() in valid_section_titles:
                    linked_elements += 1
                else:
                    quality_alerts.append(f"Défaut d'ancrage : L'élément '{el.identifier or el.content[:20]}' pointe vers une section introuvable")
            
            mmti_score = (linked_elements / len(elements)) * 100.0

        expected_element_types = {t.lower().strip() for t in template_config.get(doc_type, {}).get("expected_element_types", [])}
        if not elements or not expected_element_types:
            mtc_score = 100.0
        else:
            correct_types = sum(1 for el in elements if el.type.lower().strip() in expected_element_types)
            mtc_score = (correct_types / len(elements)) * 100.0
            
        if len(elements) == 0 and len(parsed_data.sections) > 0:
            quality_alerts.append("Extraction stérile : Aucun élément micro-technique (nœud) n'a pu être extrait")

        return {
            "schema_adherence_rate": round(sar_score, 1),
            "structural_integrity_recall": round(sir_score, 1),
            "graph_relational_integrity": round(gri_score, 1),
            "macro_micro_traceability_index": round(mmti_score, 1),
            "model_template_conformity": round(mtc_score, 1),
            "quality_alerts": quality_alerts
        }

    @staticmethod
    def _calculate_management_kpis(
        parsed_data: ParsingAgentOutput, 
        template_config: Dict[str, Any], 
        doc_type: str
    ) -> Dict[str, Any]:
        gaps = parsed_data.structural_gaps
        open_questions = parsed_data.open_questions
        sections = parsed_data.sections

        required_sections = template_config.get(doc_type, {}).get("required_sections", [])
        required_names = {sec["name"].lower().strip() for sec in required_sections}
        mapped_fields = {s.mapped_to_template_field.lower().strip() for s in sections if s.mapped_to_template_field}

        completeness_score = (
            round((len(mapped_fields.intersection(required_names)) / len(required_names)) * 100, 1)
            if required_names else 100.0
        )

        high_gaps = sum(1 for g in gaps if g.priority.upper() in ["HAUTE", "HIGH"])
        medium_gaps = sum(1 for g in gaps if g.priority.upper() in ["MOYENNE", "MEDIUM"])
        low_gaps = sum(1 for g in gaps if g.priority.upper() in ["BASSE", "LOW"])

        health_index = 100.0
        health_index -= (high_gaps * 15.0)
        health_index -= (medium_gaps * 5.0)
        health_index -= (len(open_questions) * 8.0)
        
        total_words = sum(len(s.raw_content.split()) for s in sections)
        if total_words > 400 and len(gaps) == 0 and len(open_questions) == 0:
            health_index -= 25.0

        health_index = max(0.0, round(health_index, 1))

        if health_index >= 85 and high_gaps == 0 and len(open_questions) <= 2:
            readiness_status = "READY_FOR_EXECUTION"
        elif health_index >= 55:
            readiness_status = "NEEDS_REFINEMENT"
        else:
            readiness_status = "BLOCKED"

        return {
            "health_index": health_index,
            "completeness_score": completeness_score,
            "readiness_status": readiness_status,
            "extracted_metrics_summary": {
                "total_nodes_extracted": len(parsed_data.elements),
                "total_edges_extracted": len(parsed_data.relationships)
            },
            "gaps_summary": {
                "high_severity": high_gaps,
                "medium_severity": medium_gaps,
                "low_severity": low_gaps,
                "unresolved_uncertainties": len(open_questions)
            }
        }


class SummaryEvaluatorService:
    """
    Service autonome d'évaluation pour le Summary Agent.
    """

    @classmethod
    def evaluate(cls, summary_data: SummaryOutputModel, parsed_data: ParsingAgentOutput) -> Dict[str, Any]:
        technical_metrics = cls._calculate_technical_metrics(summary_data, parsed_data)
        management_kpis = cls._calculate_management_kpis(summary_data)

        return {
            "agent_evaluated": "Summary Agent",
            "project_name": parsed_data.project_info.get("project_name", "Inconnu"),
            "technical_evaluation": technical_metrics,
            "project_management_kpis": management_kpis
        }

    @staticmethod
    def _calculate_technical_metrics(
        summary_data: SummaryOutputModel, 
        parsed_data: ParsingAgentOutput
    ) -> Dict[str, Any]:
        parser_kpis = ParsingEvaluatorService._calculate_management_kpis(parsed_data, {}, parsed_data.doc_type.value)
        real_status = parser_kpis.get("readiness_status", "BLOCKED")
        narrative_assessment = summary_data.maturity_assessment.upper()
        
        alignment_success = False
        if real_status == "READY_FOR_EXECUTION" and ("PRÊT" in narrative_assessment or "READY" in narrative_assessment):
            alignment_success = True
        elif real_status == "NEEDS_REFINEMENT" and ("IMMATURE" in narrative_assessment or "REFINEMENT" in narrative_assessment or "PRÊT" in narrative_assessment):
            alignment_success = True
        elif real_status == "BLOCKED" and ("CRITIQUE" in narrative_assessment or "BLOCKED" in narrative_assessment):
            alignment_success = True

        mas_score = 100.0 if alignment_success else 40.0

        full_parsed_text = " ".join([s.raw_content.lower() for s in parsed_data.sections])
        hallucinated_entities = 0
        
        web_base_tokens = ["html5", "html", "css3", "css", "javascript", "js", "typescript", "api"]
        is_web_project = "localstorage" in full_parsed_text or "wcag" in full_parsed_text

        all_extracted_tech = (
            summary_data.technical_stack.languages_and_frameworks +
            summary_data.technical_stack.architectural_constraints +
            summary_data.critical_dependencies
        )

        for item in all_extracted_tech:
            item_clean = item.lower().strip()
            item_replaced = item_clean.replace("/", " ")
            words = [w.strip(",.()\"'") for w in item_replaced.split() if len(w.strip(",.()\"'")) > 3]
            
            match_found = any(word in full_parsed_text for word in words)
            if not match_found and is_web_project:
                match_found = any(word in web_base_tokens for word in words)
                
            if not match_found and words:
                hallucinated_entities += 1

        lang_count = len(summary_data.technical_stack.languages_and_frameworks)
        const_count = len(summary_data.technical_stack.architectural_constraints)
        dep_count = len(summary_data.critical_dependencies)

        ecr_score = 0.0
        if lang_count >= 2: ecr_score += 35.0
        elif lang_count == 1: ecr_score += 15.0

        if const_count >= 2: ecr_score += 35.0
        elif const_count == 1: ecr_score += 15.0

        if dep_count >= 1: ecr_score += 30.0

        final_mas = max(0.0, mas_score - (hallucinated_entities * 20.0))
        final_ecr = max(0.0, ecr_score - (hallucinated_entities * 15.0))

        word_count = len(summary_data.executive_brief.split())
        if word_count == 0:
            cps_score = 0.0
        elif 30 <= word_count <= 150:
            cps_score = 100.0  
        elif word_count < 30:
            cps_score = 60.0   
        else:
            cps_score = 70.0   

        return {
            "maturity_alignment_score": round(final_mas, 1),
            "conciseness_precision_score": cps_score,
            "extraction_completeness_rate": round(final_ecr, 1),
            "brief_word_count": word_count,
            "hallucinations_detected_count": hallucinated_entities
        }

    @staticmethod
    def _calculate_management_kpis(summary_data: SummaryOutputModel) -> Dict[str, Any]:
        languages_count = len(summary_data.technical_stack.languages_and_frameworks)
        constraints_count = len(summary_data.technical_stack.architectural_constraints)
        dependencies_count = len(summary_data.critical_dependencies)

        if dependencies_count >= 4:
            risk_exposure = "ÉLEVÉ"
        elif 1 <= dependencies_count <= 3:
            risk_exposure = "MODÉRÉ"
        else:
            risk_exposure = "FAIBLE"

        return {
            "extracted_technologies_count": languages_count,
            "architectural_constraints_count": constraints_count,
            "external_dependencies_count": dependencies_count,
            "external_risk_exposure": risk_exposure
        }


class GlossaryEvaluatorService:
    """
    Service autonome d'évaluation pour le Glossary Agent.
    """

    @classmethod
    def evaluate(cls, glossary_data: GlossaryOutputModel, parsed_data: ParsingAgentOutput, candidate_terms: List[str]) -> Dict[str, Any]:
        technical_metrics = cls._calculate_technical_metrics(glossary_data, parsed_data, candidate_terms)
        management_kpis = cls._calculate_management_kpis(glossary_data)

        tcr = technical_metrics["term_coverage_rate"]
        car = technical_metrics["categorization_accuracy_rate"]
        dps = technical_metrics["definition_precision_score"]
        ata = technical_metrics["anti_tautology_adherence"]
        cap = technical_metrics["contextual_anchor_precision"]

        if tcr >= 90.0 and car == 100.0 and dps >= 90.0 and ata >= 90.0 and cap >= 90.0:
            semantic_status = "READY_FOR_ANCHORING"
        elif tcr >= 70.0 and car >= 70.0 and dps >= 60.0 and ata >= 70.0 and cap >= 70.0:
            semantic_status = "NEEDS_REFINEMENT"
        else:
            semantic_status = "BLOCKED"

        return {
            "agent_evaluated": "Glossary Agent",
            "project_name": glossary_data.project_name if glossary_data.project_name else parsed_data.project_info.get("project_name", "Inconnu"),
            "semantic_anchoring_status": semantic_status,
            "technical_evaluation": technical_metrics,
            "project_management_kpis": management_kpis
        }

    @staticmethod
    def _calculate_technical_metrics(
        glossary_data: GlossaryOutputModel, 
        parsed_data: ParsingAgentOutput, 
        candidate_terms: List[str]
    ) -> Dict[str, Any]:
        from app.core.metrics import calculate_ata, calculate_cap

        items_dict = [item.model_dump() if hasattr(item, "model_dump") else item for item in glossary_data.items]
        elements_dict = [el.model_dump() if hasattr(el, "model_dump") else el for el in parsed_data.elements]
        sections_dict = [sec.model_dump() if hasattr(sec, "model_dump") else sec for sec in parsed_data.sections]

        ata_score = calculate_ata(items_dict)
        cap_score = calculate_cap(items_dict, elements_dict, sections_dict)

        generated_terms = {item.term.lower().strip() for item in glossary_data.items}
        
        if not candidate_terms:
            tcr_score = 100.0
        else:
            matched_terms = sum(1 for term in candidate_terms if term.lower().strip() in generated_terms)
            tcr_score = (matched_terms / len(candidate_terms)) * 100.0

        tech_indicators = [
            "jwt", "api", "sdk", "localstorage", "postgres", "fastapi", "http", 
            "json", "orm", "alembic", "css", "ui", "rsc", "next.js", "tailwind", 
            "node", "jest", "ci", "cd", "branching", "workflow", "repo"
        ]
        metadata_indicators = ["version", "ratified", "amended", "amendment", "section", "identifier", "created", "status"]
        
        classification_errors = 0
        for item in glossary_data.items:
            cat_value = item.category.value if hasattr(item.category, "value") else str(item.category)
            term_clean = item.term.lower().strip()
            
            if cat_value == "BUSINESS_DOMAIN":
                if any(indicator in term_clean for indicator in tech_indicators):
                    classification_errors += 1
                elif any(meta in term_clean for meta in metadata_indicators):
                    classification_errors += 1
                    
        car_score = 100.0 - (classification_errors * 15.0) if glossary_data.items else 100.0
        car_score = max(0.0, car_score)

        structural_noise_count = 0
        case_duplicates = 0
        structural_noise_blacklist = ["ii", "iii", "iv", "v", "vi", "vii", "non", "tbd"]
        
        seen_terms = set()
        french_drift_detected = False
        french_words = [" est ", " pour ", " avec ", " dans ", " les ", " conçu ", " obligatoire "]
        
        for item in glossary_data.items:
            term_clean = item.term.lower().strip()
            
            if term_clean in seen_terms:
                case_duplicates += 1
            seen_terms.add(term_clean)
            
            if term_clean in structural_noise_blacklist:
                structural_noise_count += 1
            
            if any(word in item.project_definition.lower() for word in french_words):
                french_drift_detected = True

        dps_score = 100.0
        dps_score -= (case_duplicates * 15.0)
        dps_score -= (structural_noise_count * 20.0)
        
        if french_drift_detected:
            dps_score -= 40.0
            
        dps_score = max(0.0, dps_score)

        return {
            "term_coverage_rate": round(tcr_score, 1),
            "categorization_accuracy_rate": round(car_score, 1),
            "definition_precision_score": round(dps_score, 1),
            "anti_tautology_adherence": round(ata_score, 1),
            "contextual_anchor_precision": round(cap_score, 1),
            "structural_noise_count": structural_noise_count,
            "case_duplicates_count": case_duplicates,
            "classification_errors_count": classification_errors,
            "language_drift_detected": french_drift_detected
        }

    @staticmethod
    def _calculate_management_kpis(glossary_data: GlossaryOutputModel) -> Dict[str, Any]:
        total_items = len(glossary_data.items)
        business_count = 0
        tech_count = 0
        explicit_count = 0
        implicit_count = 0

        for item in glossary_data.items:
            cat_value = item.category.value if hasattr(item.category, "value") else str(item.category)
            disc_value = item.discovery.value if hasattr(item.discovery, "value") else str(item.discovery)

            if cat_value == "BUSINESS_DOMAIN":
                business_count += 1
            elif cat_value == "TECHNICAL_STACK":
                tech_count += 1

            if disc_value == "EXPLICIT":
                explicit_count += 1
            elif disc_value == "IMPLICIT":
                implicit_count += 1

        return {
            "total_extracted_terms": total_items,
            "business_domain_terms_count": business_count,
            "technical_stack_terms_count": tech_count,
            "explicit_terms_count": explicit_count,
            "implicit_terms_inferred_count": implicit_count
        }


# ===========================================================================
# NOUVEAU : SERVICE D'ÉVALUATION DU DIAGRAM AGENT
# ===========================================================================

class DiagramEvaluatorService:
    """
    Service autonome d'évaluation pour le Diagram Agent.
    Valide la conformité syntaxique Mermaid.js, la traçabilité des entités,
    la complétude relationnelle et le respect des règles de modélisation.
    """

    @classmethod
    def evaluate(cls, diagram_data: DiagramOutputModel, parsed_data: ParsingAgentOutput) -> Dict[str, Any]:
        technical_metrics = cls._calculate_technical_metrics(diagram_data, parsed_data)
        management_kpis = cls._calculate_management_kpis(diagram_data)

        svr = technical_metrics["syntax_validity_rate"]
        sra = technical_metrics["structural_rule_adherence"]
        dcr = technical_metrics["diagram_coverage_rate"]

        # Statut de qualité du rendu visuel
        if svr == 100.0 and sra >= 90.0 and dcr >= 60.0:
            rendering_status = "READY_FOR_RENDERING"
        elif svr >= 75.0 and sra >= 75.0:
            rendering_status = "NEEDS_REFINEMENT"
        else:
            rendering_status = "BLOCKED"

        return {
            "agent_evaluated": "Diagram Agent",
            "project_name": parsed_data.project_info.get("project_name", "Inconnu"),
            "diagram_rendering_status": rendering_status,
            "technical_evaluation": technical_metrics,
            "project_management_kpis": management_kpis
        }

    @staticmethod
    def _calculate_technical_metrics(
        diagram_data: DiagramOutputModel, 
        parsed_data: ParsingAgentOutput
    ) -> Dict[str, Any]:
        from app.core.metrics import (
            calculate_svr, 
            calculate_dcr, 
            calculate_rcr, 
            calculate_sra
        )

        diagrams_dict = [
            diag.model_dump() if hasattr(diag, "model_dump") else diag 
            for diag in diagram_data.diagrams
        ]
        elements_dict = [
            el.model_dump() if hasattr(el, "model_dump") else el 
            for el in parsed_data.elements
        ]
        relationships_dict = [
            rel.model_dump() if hasattr(rel, "model_dump") else rel 
            for rel in parsed_data.relationships
        ]

        svr_score = calculate_svr(diagrams_dict)
        dcr_score = calculate_dcr(diagrams_dict, elements_dict)
        rcr_score = calculate_rcr(diagrams_dict, relationships_dict)
        sra_score = calculate_sra(diagrams_dict)

        return {
            "syntax_validity_rate": round(svr_score, 1),
            "diagram_coverage_rate": round(dcr_score, 1),
            "relational_completeness_rate": round(rcr_score, 1),
            "structural_rule_adherence": round(sra_score, 1)
        }

    @staticmethod
    def _calculate_management_kpis(diagram_data: DiagramOutputModel) -> Dict[str, Any]:
        total_diagrams = len(diagram_data.diagrams)
        diagram_type_counts = {}
        total_mermaid_lines = 0

        for diag in diagram_data.diagrams:
            diag_type = diag.type.value if hasattr(diag.type, "value") else str(diag.type)
            diagram_type_counts[diag_type] = diagram_type_counts.get(diag_type, 0) + 1
            code_lines = len(diag.mermaid_code.strip().split("\n")) if diag.mermaid_code else 0
            total_mermaid_lines += code_lines

        avg_lines_per_diagram = round(total_mermaid_lines / total_diagrams, 1) if total_diagrams > 0 else 0.0

        return {
            "total_generated_diagrams": total_diagrams,
            "diagram_types_breakdown": diagram_type_counts,
            "total_mermaid_lines_count": total_mermaid_lines,
            "average_lines_per_diagram": avg_lines_per_diagram
        }
class DocWriterEvaluatorService:
    """
    Service autonome d'évaluation pour le Documentation Writer Agent.
    Valide la complétude de la structure Markdown, la conservation de la traçabilité (IDs),
    l'intégration des diagrammes Mermaid et la conformité du glossaire terminal.
    """

    @classmethod
    def evaluate(
        cls,
        markdown_text: str,
        parsed_data: ParsingAgentOutput,
        summary_data: SummaryOutputModel,
        glossary_data: GlossaryOutputModel,
        diagram_data: DiagramOutputModel
    ) -> Dict[str, Any]:
        technical_metrics = cls._calculate_technical_metrics(
            markdown_text=markdown_text,
            parsed_data=parsed_data,
            glossary_data=glossary_data,
            diagram_data=diagram_data
        )
        management_kpis = cls._calculate_management_kpis(
            markdown_text=markdown_text,
            parsed_data=parsed_data,
            glossary_data=glossary_data,
            diagram_data=diagram_data
        )

        dsc = technical_metrics["document_structure_completeness"]
        tpr = technical_metrics["traceability_preservation_rate"]
        dev = technical_metrics["diagram_embedding_validity"]
        gff = technical_metrics["glossary_format_and_placement"]

        # Arbitrage du statut de préparation du document pour publication / export PDF
        if dsc >= 80.0 and tpr >= 80.0 and dev >= 80.0 and gff >= 80.0:
            doc_status = "READY_FOR_PDF_EXPORT"
        elif dsc >= 60.0 and tpr >= 50.0:
            doc_status = "NEEDS_REFINEMENT"
        else:
            doc_status = "BLOCKED"

        return {
            "agent_evaluated": "Documentation Writer Agent",
            "project_name": parsed_data.project_info.get("project_name", "Inconnu"),
            "documentation_readiness_status": doc_status,
            "technical_evaluation": technical_metrics,
            "project_management_kpis": management_kpis
        }

    @staticmethod
    def _calculate_technical_metrics(
        markdown_text: str,
        parsed_data: ParsingAgentOutput,
        glossary_data: GlossaryOutputModel,
        diagram_data: DiagramOutputModel
    ) -> Dict[str, Any]:
        from app.core.metrics import (
            calculate_dsc,
            calculate_tpr,
            calculate_dev,
            calculate_gff
        )

        elements_dict = [
            el.model_dump() if hasattr(el, "model_dump") else el
            for el in parsed_data.elements
        ]
        glossary_dict = [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in glossary_data.items
        ]
        diagrams_dict = [
            diag.model_dump() if hasattr(diag, "model_dump") else diag
            for diag in diagram_data.diagrams
        ]

        dsc_score = calculate_dsc(markdown_text)
        tpr_score = calculate_tpr(markdown_text, elements_dict)
        dev_score = calculate_dev(markdown_text, diagrams_dict)
        gff_score = calculate_gff(markdown_text, glossary_dict)

        return {
            "document_structure_completeness": round(dsc_score, 1),
            "traceability_preservation_rate": round(tpr_score, 1),
            "diagram_embedding_validity": round(dev_score, 1),
            "glossary_format_and_placement": round(gff_score, 1)
        }

    @staticmethod
    def _calculate_management_kpis(
        markdown_text: str,
        parsed_data: ParsingAgentOutput,
        glossary_data: GlossaryOutputModel,
        diagram_data: DiagramOutputModel
    ) -> Dict[str, Any]:
        words_count = len(markdown_text.split()) if markdown_text else 0
        total_identifiers = len(parsed_data.elements)
        total_diagrams = len(diagram_data.diagrams)
        total_glossary_terms = len(glossary_data.items)

        # Calcul du nombre d'identifiants d'origine conservés dans le texte final
        retained_identifiers = 0
        for el in parsed_data.elements:
            ident = getattr(el, "identifier", None) or el.get("identifier")
            if ident and ident in markdown_text:
                retained_identifiers += 1

        return {
            "total_markdown_word_count": words_count,
            "total_source_identifiers_count": total_identifiers,
            "retained_identifiers_count": retained_identifiers,
            "embedded_diagrams_count": total_diagrams,
            "glossary_terms_count": total_glossary_terms
        }
# ===========================================================================
# SERVICE D'ÉVALUATION DU LAYOUT AGENT (RENDU & DESIGN PDF)
# ===========================================================================

class LayoutEvaluatorService:
    """
    Service autonome d'évaluation pour le Layout Agent.
    Valide la compilation du PDF (RSR), la conversion des diagrammes (DVR),
    le respect du budget de pages (PBA), l'absence de débordements (VOR)
    et la conformité à la charte graphique (SCS).
    """

    @classmethod
    def evaluate(
        cls,
        markdown_text: str,
        rendered_pdf_metadata: Dict[str, Any],
        layout_overflow_report: Dict[str, Any],
        layout_spec: Dict[str, Any],
        project_name: str = "Inconnu"
    ) -> Dict[str, Any]:
        technical_metrics = cls._calculate_technical_metrics(
            markdown_text=markdown_text,
            rendered_pdf_metadata=rendered_pdf_metadata,
            layout_overflow_report=layout_overflow_report,
            layout_spec=layout_spec
        )
        management_kpis = cls._calculate_management_kpis(
            rendered_pdf_metadata=rendered_pdf_metadata,
            layout_overflow_report=layout_overflow_report
        )

        rsr = technical_metrics["render_success_rate"]
        dvr = technical_metrics["diagram_visual_render_rate"]
        pba = technical_metrics["page_budget_adherence"]
        vor = technical_metrics["visual_overflow_rate"]
        scs = technical_metrics["styling_consistency_score"]

        # Arbitrage du statut de validation de la qualité d'impression / publication
        if rsr == 100.0 and dvr >= 90.0 and vor >= 90.0 and scs >= 85.0 and pba >= 70.0:
            publication_status = "READY_FOR_PUBLICATION"
        elif rsr == 100.0 and vor >= 70.0:
            publication_status = "NEEDS_REFINEMENT"
        else:
            publication_status = "BLOCKED"

        return {
            "agent_evaluated": "Layout Agent",
            "project_name": project_name,
            "layout_publication_status": publication_status,
            "technical_evaluation": technical_metrics,
            "project_management_kpis": management_kpis
        }

    @staticmethod
    def _calculate_technical_metrics(
        markdown_text: str,
        rendered_pdf_metadata: Dict[str, Any],
        layout_overflow_report: Dict[str, Any],
        layout_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        from app.core.metrics import (
            calculate_rsr,
            calculate_dvr,
            calculate_pba,
            calculate_vor,
            calculate_scs
        )

        pdf_generated = rendered_pdf_metadata.get("pdf_generated", False)
        file_size_bytes = rendered_pdf_metadata.get("file_size_bytes", 0)
        actual_page_count = rendered_pdf_metadata.get("page_count", 0)

        rsr_score = calculate_rsr(pdf_generated, file_size_bytes)
        dvr_score = calculate_dvr(markdown_text, rendered_pdf_metadata)
        pba_score = calculate_pba(markdown_text, actual_page_count)
        vor_score = calculate_vor(markdown_text, layout_overflow_report)
        scs_score = calculate_scs(markdown_text, rendered_pdf_metadata, layout_spec)

        return {
            "render_success_rate": round(rsr_score, 1),
            "diagram_visual_render_rate": round(dvr_score, 1),
            "page_budget_adherence": round(pba_score, 1),
            "visual_overflow_rate": round(vor_score, 1),
            "styling_consistency_score": round(scs_score, 1)
        }

    @staticmethod
    def _calculate_management_kpis(
        rendered_pdf_metadata: Dict[str, Any],
        layout_overflow_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        file_size_bytes = rendered_pdf_metadata.get("file_size_bytes", 0)
        file_size_kb = round(file_size_bytes / 1024.0, 1) if file_size_bytes else 0.0
        page_count = rendered_pdf_metadata.get("page_count", 0)
        rendered_diagrams = rendered_pdf_metadata.get("rendered_diagrams_count", 0)
        overflow_events = layout_overflow_report.get("overflow_events_count", 0)

        return {
            "pdf_generated_success": rendered_pdf_metadata.get("pdf_generated", False),
            "total_pdf_pages_count": page_count,
            "file_size_kb": file_size_kb,
            "rendered_diagram_images_count": rendered_diagrams,
            "overflow_events_detected_count": overflow_events
        }