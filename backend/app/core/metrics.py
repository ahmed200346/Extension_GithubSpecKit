# app/core/metrics.py
"""
metrics.py — Calculateur de métriques d'évaluation pour les agents (Version Finale Unifiée).
Évalue le Parsing, la Synthèse (Summary), le Glossaire et la Modélisation Graphique (Diagrams).
"""

import re
import difflib
from typing import List, Dict, Any
import math
# ===========================================================================
# 1. MÉTRIQUES POUR LE PARSING AGENT
# ===========================================================================

def calculate_sar(success: bool) -> float:
    """
    Schema Adherence Rate (SAR) :
    Retourne 100% si le JSON a pu être validé par Pydantic, sinon 0%.
    """
    return 100.0 if success else 0.0


def calculate_sir(input_sections: List[Dict[str, Any]], output_sections: List[Any]) -> float:
    """
    Structural Integrity Recall (SIR) :
    Mesure le pourcentage de sections physiques d'origine qui ont été 
    conservées dans le JSON final généré par le LLM.
    """
    if not input_sections:
        return 100.0
    if not output_sections:
        return 0.0
    return (len(output_sections) / len(input_sections)) * 100


def calculate_tfs(input_sections: List[Dict[str, Any]], output_sections: List[Any]) -> float:
    """
    Text Fidelity Score (TFS) Amélioré :
    Compare le contenu textuel brut pour s'assurer qu'aucune information n'a été 
    altérée ou résumée.
    """
    if not input_sections:
        return 100.0
        
    input_map = {sec["title"].strip().lower(): sec["raw_content"].strip() for sec in input_sections}
    output_map = {getattr(sec, "title", sec.get("title", "")).strip().lower(): getattr(sec, "raw_content", sec.get("raw_content", "")).strip() for sec in output_sections}

    scores = []
    for title, in_content in input_map.items():
        if not in_content:
            continue
            
        if title in output_map:
            out_content = output_map[title]
            if in_content == out_content:
                scores.append(1.0)
            else:
                ratio = difflib.SequenceMatcher(None, in_content, out_content).ratio()
                scores.append(ratio)
        else:
            matched_fallback = False
            for out_title, out_content in output_map.items():
                if in_content in out_content or out_content in in_content:
                    scores.append(difflib.SequenceMatcher(None, in_content, out_content).ratio())
                    matched_fallback = True
                    break
            if not matched_fallback:
                scores.append(0.0)
            
    return (sum(scores) / len(scores)) * 100 if scores else 100.0


def extract_heuristic_questions(raw_markdown: str) -> List[str]:
    """Extrait de manière déterministe les questions réelles du texte source."""
    lines = raw_markdown.splitlines()
    questions = []
    for line in lines:
        line = line.strip()
        if "?" in line:
            cleaned = re.sub(r"^[-*\s]*([Qq]uestion|[Qq])?\s*[:\-\s]*", "", line)
            match = re.search(r"([^?]+\?)", cleaned)
            if match:
                questions.append(match.group(1).strip())
            else:
                questions.append(cleaned)
    return [q for q in questions if q]


def calculate_exr(raw_markdown: str, open_questions: List[str]) -> float:
    """Extraction Recall (ExR) : Mesure la capacité à extraire les questions réouvertes."""
    gt_questions = extract_heuristic_questions(raw_markdown)
    if not gt_questions:
        return 100.0
        
    found_count = 0
    for gt in gt_questions:
        for oq in open_questions:
            if gt.lower() in oq.lower() or oq.lower() in gt.lower():
                found_count += 1
                break
            elif difflib.SequenceMatcher(None, gt.lower(), oq.lower()).ratio() > 0.7:
                found_count += 1
                break
                
    return (found_count / len(gt_questions)) * 100


def calculate_gri(elements: List[Any], relationships: List[Any]) -> float:
    """Graph Relational Integrity (GRI) : Vérifie la validité des liens du graphe."""
    if not relationships:
        return 100.0
        
    valid_nodes = set()
    for el in elements:
        ident = getattr(el, "identifier", el.get("identifier"))
        content = getattr(el, "content", el.get("content", ""))
        if ident:
            valid_nodes.add(str(ident).lower())
        if content:
            valid_nodes.add(content[:30].strip().lower())

    valid_relations = 0
    for rel in relationships:
        source = str(getattr(rel, "from", rel.get("from", ""))).lower()
        target = str(getattr(rel, "to", rel.get("to", ""))).lower()
        
        source_valid = any(source in node or node in source for node in valid_nodes)
        target_valid = any(target in node or node in target for node in valid_nodes)
        
        if source_valid and target_valid:
            valid_relations += 1
            
    return (valid_relations / len(relationships)) * 100


# ===========================================================================
# 2. MÉTRIQUES POUR LE SUMMARY AGENT
# ===========================================================================

def calculate_wca(executive_brief: str, min_words: int = 30, max_words: int = 150) -> float:
    """Word Count Adherence (WCA) : Respect de la longueur du résumé."""
    if not executive_brief:
        return 0.0
    words = executive_brief.split()
    word_count = len(words)
    if min_words <= word_count <= max_words:
        return 100.0
    deviation = (min_words - word_count) / min_words if word_count < min_words else (word_count - max_words) / max_words
    return max(0.0, (1.0 - deviation) * 100)


def calculate_gsc(languages_and_frameworks: List[str], parsed_elements: List[Dict[str, Any]]) -> float:
    """Graph Stack Content (GSC) : Alignement de la stack avec le graphe parsé."""
    if not languages_and_frameworks:
        return 100.0
    if not parsed_elements:
        return 0.0

    valid_references = set()
    for el in parsed_elements:
        valid_references.add(el.get("content", "").lower())
        valid_references.add(el.get("identifier", "").lower())

    matched_count = sum(1 for tech in languages_and_frameworks if any(tech.lower() in ref for ref in valid_references))
    return (matched_count / len(languages_and_frameworks)) * 100


def calculate_mac(maturity_assessment: str, structural_gaps: List[Dict[str, Any]]) -> float:
    """Maturity Assessment Coherence (MAC) : Prise en compte des lacunes documentaires."""
    if not structural_gaps:
        return 100.0
    if not maturity_assessment:
        return 0.0
    assessment_lower = maturity_assessment.lower()
    matched_gaps = sum(1 for gap in structural_gaps if gap.get("missing_section", "").lower() in assessment_lower or "gap" in assessment_lower)
    return (matched_gaps / len(structural_gaps)) * 100


# ===========================================================================
# 3. MÉTRIQUES POUR LE GLOSSARY AGENT
# ===========================================================================

def calculate_ata(items: List[Dict[str, Any]]) -> float:
    """Anti-Tautology Adherence (ATA) : Taux de définitions non tautologiques."""
    if not items:
        return 100.0
    violations = sum(1 for item in items if str(item.get("term", "")).strip().lower() in str(item.get("project_definition", "")).strip().lower())
    return ((len(items) - violations) / len(items)) * 100


def calculate_cap(items: List[Dict[str, Any]], parsed_elements: List[Dict[str, Any]], parsed_sections: List[Dict[str, Any]]) -> float:
    """Contextual Anchor Precision (CAP) : Précision géométrique des ancres."""
    if not items:
        return 100.0
    valid_anchors = {str(el.get("identifier")).strip().lower() for el in parsed_elements if el.get("identifier")}
    valid_anchors.update({str(sec.get("title")).strip().lower() for sec in parsed_sections if sec.get("title")})

    matched_anchors = sum(1 for item in items if str(item.get("contextual_anchor", "")).strip().lower() in valid_anchors)
    return (matched_anchors / len(items)) * 100


# ===========================================================================
# 4. NOUVELLES MÉTRIQUES POUR LE DIAGRAM AGENT
# ===========================================================================

ALLOWED_DIAGRAM_HEADERS = {
    "flowchart", "sequencediagram", "classdiagram", "erdiagram",
    "statediagram", "gantt", "mindmap", "pie"
}

def calculate_svr(diagrams: List[Dict[str, Any]]) -> float:
    """
    Syntax Validity Rate (SVR) :
    Vérifie la validité syntaxique globale des schémas Mermaid générés.
    S'assure que le code commence par un entête valide, ne contient pas de balises
    markdown corrompues et respecte les paires de balises de nœuds.
    """
    if not diagrams:
        return 0.0

    valid_count = 0
    for diag in diagrams:
        code = str(diag.get("mermaid_code", "")).strip()
        if not code or code.startswith("```"):
            continue

        first_line = code.split("\n")[0].strip().lower()
        has_valid_header = any(first_line.startswith(h) for h in ALLOWED_DIAGRAM_HEADERS)

        # Vérification des anomalies de nœuds sans identifiant ou de crochets non fermés
        has_unmatched_brackets = code.count("[") != code.count("]") or code.count("{") != code.count("}")

        if has_valid_header and not has_unmatched_brackets:
            valid_count += 1

    return (valid_count / len(diagrams)) * 100


def calculate_dcr(diagrams: List[Dict[str, Any]], parsed_elements: List[Dict[str, Any]]) -> float:
    """
    Diagram Element Coverage Rate (DCR) - Traçabilité :
    Mesure le pourcentage d'éléments clés du graphe (Entities, Endpoints, User Stories)
    qui sont explicitement représentés dans le texte source des schémas Mermaid.
    """
    if not parsed_elements or not diagrams:
        return 100.0 if not parsed_elements else 0.0

    all_diagrams_code = " ".join(str(d.get("mermaid_code", "")).lower() for d in diagrams)

    target_elements = [
        el for el in parsed_elements 
        if el.get("type") in ["ENTITY", "ENDPOINT", "USER_STORY", "REQUIREMENT", "DATABASE", "MODEL"]
    ]

    if not target_elements:
        return 100.0

    found_count = 0
    for el in target_elements:
        ident = str(el.get("identifier", "")).lower()
        content = str(el.get("content", "")).lower()
        
        # Recherche si l'identifiant ou un extrait du contenu est présent dans un des diagrammes
        if (ident and ident in all_diagrams_code) or (content and content[:20] in all_diagrams_code):
            found_count += 1

    return (found_count / len(target_elements)) * 100


def calculate_rcr(diagrams: List[Dict[str, Any]], parsed_relationships: List[Dict[str, Any]]) -> float:
    """
    Relational Completeness Rate (RCR) :
    Mesure si les relations entre entités définies dans le graphe ('relationships')
    sont conservées et modélisées sous forme de liaisons/flèches (-->, ->>, ||--o{) dans les diagrammes.
    """
    if not parsed_relationships:
        return 100.0
    if not diagrams:
        return 0.0

    all_diagrams_code = " ".join(str(d.get("mermaid_code", "")).lower() for d in diagrams)

    matched_relations = 0
    for rel in parsed_relationships:
        source = str(rel.get("source", rel.get("from", ""))).lower()
        target = str(rel.get("to", "")).lower()

        if source and target and (source in all_diagrams_code) and (target in all_diagrams_code):
            matched_relations += 1

    return (matched_relations / len(parsed_relationships)) * 100


def calculate_sra(diagrams: List[Dict[str, Any]]) -> float:
    """
    Structural Rule Adherence (SRA) :
    Évalue le respect des contraintes structurelles de la spécification :
    1. Pour les 'flowchart' : Vérifie la présence de losanges de décision '{?}' (non-linéarité).
    2. Pour les 'erDiagram' : Vérifie l'absence de notation UML incompatible (ex: +field: type).
    """
    if not diagrams:
        return 100.0

    compliant_diagrams = 0
    for diag in diagrams:
        code = str(diag.get("mermaid_code", "")).strip()
        diag_type = str(diag.get("type", "")).lower()

        if "flowchart" in diag_type:
            # Règle de non-linéarité : doit contenir au moins un losange de décision {?}
            has_decision = "{" in code and "}" in code
            if has_decision:
                compliant_diagrams += 1
        elif "erdiagram" in diag_type:
            # Règle d'attribut ER : ne doit pas contenir de notation UML de type '+id:'
            has_uml_notation = bool(re.search(r'\+\s*\w+\s*:', code))
            if not has_uml_notation:
                compliant_diagrams += 1
        else:
            compliant_diagrams += 1

    return (compliant_diagrams / len(diagrams)) * 100
# ===========================================================================
# 5. MÉTRIQUES POUR LE DOCUMENTATION WRITER AGENT
# ===========================================================================

EXPECTED_DOC_WRITER_SECTIONS = [
    "Executive Summary",
    "Architecture Workflows",
    "Detailed Technical Specifications",
    "Project Governance",
    "Glossary"
]

def calculate_dsc(markdown_text: str) -> float:
    """
    Document Structure Completeness (DSC) :
    Mesure la présence des 5 sections obligatoires définies dans la structure
    du System Prompt du Documentation Writer.
    """
    if not markdown_text:
        return 0.0
    
    md_lower = markdown_text.lower()
    found = sum(1 for sec in EXPECTED_DOC_WRITER_SECTIONS if sec.lower() in md_lower)
    return (found / len(EXPECTED_DOC_WRITER_SECTIONS)) * 100.0


def calculate_tpr(markdown_text: str, parsed_elements: List[Dict[str, Any]]) -> float:
    """
    Traceability Preservation Rate (TPR) :
    Vérifie que les identifiants exacts du graphe (ex: US-01, FR-001, ENT-USER)
    sont intégralement conservés dans le document Markdown final.
    """
    if not parsed_elements:
        return 100.0
    if not markdown_text:
        return 0.0

    target_identifiers = [
        str(el.get("identifier")).strip() 
        for el in parsed_elements 
        if el.get("identifier")
    ]

    if not target_identifiers:
        return 100.0

    found_count = sum(1 for ident in target_identifiers if ident in markdown_text)
    return (found_count / len(target_identifiers)) * 100.0


def calculate_dev(markdown_text: str, diagrams: List[Dict[str, Any]]) -> float:
    """
    Diagram Embedding Validity (DEV) :
    S'assure que 100% des diagrammes générés par le Diagram Agent sont 
    correctement intégrés sous forme de blocs ```mermaid dans le document Markdown.
    """
    if not diagrams:
        return 100.0
    if not markdown_text:
        return 0.0

    embedded_count = 0
    for diag in diagrams:
        title = str(diag.get("title", "")).strip().lower()
        code_snippet = str(diag.get("mermaid_code", "")).strip()[:30].lower()
        
        # Vérification de la présence du titre ou du début du code dans un bloc mermaid
        if (title and title in markdown_text.lower()) or (code_snippet and code_snippet in markdown_text.lower()):
            embedded_count += 1

    return (embedded_count / len(diagrams)) * 100.0


def calculate_gff(markdown_text: str, glossary_items: List[Dict[str, Any]]) -> float:
    """
    Glossary Format & Placement (GFF) :
    Vérifie deux critères cumulatifs :
    1. Le glossaire apparaît en position terminale (dernière section du Markdown).
    2. Les termes sont formatés dans un tableau Markdown avec séparateurs '|'.
    """
    if not glossary_items:
        return 100.0
    if not markdown_text:
        return 0.0

    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    if not lines:
        return 0.0

    # 1. Vérification du placement terminal (présence du glossaire dans les 35% derniers du document)
    last_third_content = "\n".join(lines[-int(len(lines) * 0.35):]).lower()
    has_terminal_placement = "glossary" in last_third_content or "glossaire" in last_third_content

    # 2. Vérification du format tableau Markdown (|---|---|)
    has_table_format = any("|" in line and "---" in line for line in lines)

    score = 0.0
    if has_terminal_placement:
        score += 50.0
    if has_table_format:
        score += 50.0

    return score


# ===========================================================================
# 6. MÉTRIQUES POUR LE LAYOUT AGENT (CONVERTISSEUR MD -> PDF)
# ===========================================================================

def calculate_rsr(pdf_generated: bool, file_size_bytes: int = 0) -> float:
    """
    Render Success Rate (RSR) :
    Vérifie que la compilation du document s'est déroulée sans erreur
    et que le fichier PDF résultant n'est pas vide (taille > 0 octets).
    """
    if pdf_generated and file_size_bytes > 0:
        return 100.0
    return 0.0


def calculate_dvr(markdown_text: str, rendered_pdf_metadata: Dict[str, Any]) -> float:
    """
    Diagram Visual Render Rate (DVR) :
    Vérifie que 100% des diagrammes ```mermaid présents dans le doc.md 
    sont effectivement convertis et intégrés sous forme d'images dans le PDF final.
    """
    if not markdown_text:
        return 100.0

    # 1. Compter le nombre de blocs ```mermaid dans le doc.md d'origine
    mermaid_blocks_in_md = len(re.findall(r"```mermaid", markdown_text, re.IGNORECASE))
    if mermaid_blocks_in_md == 0:
        return 100.0

    # 2. Compter le nombre d'images de diagrammes insérées dans le PDF
    rendered_diagrams_in_pdf = rendered_pdf_metadata.get("rendered_diagrams_count", 0)

    # Ratio de conversion visuelle des diagrammes
    return min(100.0, (rendered_diagrams_in_pdf / mermaid_blocks_in_md) * 100.0)


def calculate_pba(markdown_text: str, actual_pdf_page_count: int) -> float:
    """
    Page Budget Adherence (PBA) Relié au Contexte :
    Calcule dynamiquement le nombre de pages théoriques nécessaires en fonction :
    - Du nombre de mots du doc.md (~350 mots / page PDF)
    - Du nombre de diagrammes et tableaux (chaque schéma consomme environ 0.5 page).
    """
    if not markdown_text or actual_pdf_page_count <= 0:
        return 0.0

    # Extraction du volume du doc.md source
    words = len(markdown_text.split())
    diagrams = len(re.findall(r"```mermaid", markdown_text, re.IGNORECASE))
    tables = len(re.findall(r"\|---", markdown_text))

    # Estimation dynamique de la surface requise pour CE doc.md
    estimated_pages = math.ceil((words / 350.0) + (diagrams * 0.5) + (tables * 0.2))
    estimated_pages = max(1, estimated_pages)

    # Marge de tolérance de ±1 page
    min_allowed = max(1, estimated_pages - 1)
    max_allowed = estimated_pages + 2

    if min_allowed <= actual_pdf_page_count <= max_allowed:
        return 100.0

    # Calcul de la déviation par rapport à la taille réelle du doc.md
    if actual_pdf_page_count < min_allowed:
        dev = (min_allowed - actual_pdf_page_count) / min_allowed
    else:
        dev = (actual_pdf_page_count - max_allowed) / max_allowed

    return max(0.0, (1.0 - dev) * 100.0)


def calculate_vor(markdown_text: str, layout_overflow_report: Dict[str, Any]) -> float:
    """
    Visual Overflow Rate (VOR) Relié à la Mise en Page :
    Compare les éléments à risque du doc.md (tableaux à nombreuses colonnes,
    lignes de code très larges) avec le rapport de débordement du moteur PDF.
    """
    if not markdown_text:
        return 100.0

    # S'il n'y a aucun débordement signalé lors de la compilation du doc.md
    overflow_events = layout_overflow_report.get("overflow_events_count", 0)
    total_rendered_blocks = layout_overflow_report.get("total_rendered_blocks", 1)

    if total_rendered_blocks == 0:
        return 100.0

    # Score d'intégrité visuelle sans tronquage (inverse de la pénalité)
    overflow_ratio = overflow_events / total_rendered_blocks
    return max(0.0, (1.0 - overflow_ratio) * 100.0)


def calculate_scs(markdown_text: str, rendered_pdf_metadata: Dict[str, Any], layout_spec: Dict[str, Any]) -> float:
    """
    Styling & Structural Consistency Score (SCS) :
    Vérifie la fidélité de conversion de la structure du doc.md vers le PDF :
    1. Les titres H1/H2 du doc.md sont-ils tous présents dans la Table des Matières du PDF ?
    2. La charte graphique (couleurs, polices de layout_spec.json) est-elle appliquée ?
    """
    if not markdown_text or not layout_spec:
        return 100.0

    checks = []

    # 1. Traçabilité des sections du doc.md vers la Table des Matières du PDF
    md_headings = re.findall(r"^##\s+(.+)$", markdown_text, re.MULTILINE)
    pdf_toc_entries = rendered_pdf_metadata.get("toc_entries", [])

    if md_headings:
        matched_headings = sum(1 for h in md_headings if any(h.strip().lower() in toc.lower() for toc in pdf_toc_entries))
        checks.append(matched_headings / len(md_headings))

    # 2. Conformité aux contraintes de style du layout_spec.json
    branding = layout_spec.get("branding_theme", {})
    if branding.get("primary_color"):
        checks.append(1.0 if rendered_pdf_metadata.get("applied_primary_color") == branding["primary_color"] else 0.0)

    if layout_spec.get("header_footer_config", {}).get("enable_page_numbering", True):
        checks.append(1.0 if rendered_pdf_metadata.get("has_page_numbers", False) else 0.0)

    if not checks:
        return 100.0

    return (sum(checks) / len(checks)) * 100.0