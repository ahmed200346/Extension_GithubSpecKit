# app/utils/layout_tools.py
"""
layout_tools.py — Outils de compilation PDF et de rendu visuel pour le Layout Agent.

Version HD : 
- Diagrammes à proportions naturelles (Aspect Ratio) & Typographie augmentée (11pt)
- Table des matières RÉELLEMENT cliquable (liens internes + panneau de signets PDF)
- Thème bleu technique piloté par layout_spec.json
"""

import os
import re
import shutil
import subprocess
import tempfile
from typing import Dict, Any, List, Tuple, Optional

from PIL import Image as PILImage,ImageDraw

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image as RLImage,
    KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas as pdf_canvas

print("[LAYOUT] layout_tools.py v3.0 (TOC cliquable, signets PDF, thème dynamique) actif")


# ===========================================================================
# 0. UTILITAIRES DE THÈME (lecture de layout_spec.json avec valeurs par défaut)
# ===========================================================================

def _color(hex_value: str, fallback: str) -> colors.Color:
    try:
        return colors.HexColor(hex_value or fallback)
    except Exception:
        return colors.HexColor(fallback)


def _build_theme(layout_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Construit un dictionnaire de thème (couleurs, typographie, marges) à partir de layout_spec.json."""
    branding = layout_spec.get("branding_theme", {}) or {}
    typo = layout_spec.get("typography_rules", {}) or {}
    doc_meta = layout_spec.get("document_metadata", {}) or {}
    margins = doc_meta.get("margins_mm", {}) or {}
    diagram_limits = layout_spec.get("diagram_rendering_limits", {}) or {}

    from reportlab.lib.units import mm as MM

    return {
        "primary": _color(branding.get("primary_color"), "#1A365D"),
        "secondary": _color(branding.get("secondary_color"), "#2B6CB0"),
        "accent": _color(branding.get("accent_color"), "#38A169"),
        "bg_light": _color(branding.get("background_light"), "#F7FAFC"),
        "text": _color(branding.get("text_color"), "#2D3748"),
        "border": _color(branding.get("border_color"), "#CBD5E0"),
        "font_heading": branding.get("font_family_heading", "Helvetica-Bold"),
        "font_body": branding.get("font_family_body", "Helvetica"),
        "page_size": letter if str(doc_meta.get("page_size", "A4")).upper() == "LETTER" else A4,
        "margin_top": margins.get("top", 22) * MM,
        "margin_bottom": margins.get("bottom", 20) * MM,
        "margin_left": margins.get("left", 18) * MM,
        "margin_right": margins.get("right", 18) * MM,
        "typo": {
            "h1": typo.get("h1", {"font_size": 22, "leading": 26, "space_after": 12}),
            "h2": typo.get("h2", {"font_size": 14.5, "leading": 18, "space_after": 8}),
            "h3": typo.get("h3", {"font_size": 12, "leading": 15, "space_after": 6}),
            "body": typo.get("body", {"font_size": 11.0, "leading": 15.5, "space_after": 7}),
            "table_cell": typo.get("table_cell", {"font_size": 9.0, "leading": 12.0}),
            "code": typo.get("code", {"font_size": 9.0, "leading": 12.0}),
        },
        "max_width_pt": diagram_limits.get("max_width_pt", 504),
        "max_height_pt": diagram_limits.get("max_height_pt", 650),
        "fallback_scaling_strategy": diagram_limits.get("fallback_scaling_strategy", "fit_to_width"),
    }


# ===========================================================================
# 1. NETTOYAGE ET ENRICHISSEMENT DU CODE MERMAID (thème bleu technique)
# ===========================================================================

MERMAID_THEME_CONFIG_FULL = """%%{init: {
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

_VALID_MERMAID_HEADERS = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "erDiagram",
    "stateDiagram", "gantt", "mindmap", "pie", "gitGraph", "C4Context"
)

_NODE_PATTERN = re.compile(
    r'(\b[A-Za-z0-9_]+)(\[\s*|\(\s*|\{\s*)'
    r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^\]\}\)]+)'
    r'(\s*\]|\s*\)|\s*\})'
)


def _quote_node_label(match: "re.Match") -> str:
    node_id, open_symbol, label, close_symbol = match.groups()
    label = label.strip()
    if (label.startswith('"') and label.endswith('"')) or (label.startswith("'") and label.endswith("'")):
        clean_label = label[1:-1].replace('"', "'")
    else:
        clean_label = label.replace('"', "'")
    return f'{node_id}{open_symbol}"{clean_label}"{close_symbol}'


_INIT_BLOCK_PATTERN = re.compile(r"^%%\{init:.*?\}%%\s*\n?", re.DOTALL)

def clean_mermaid_code(code: str) -> str:
    if not code:
        return ""
    code = str(code).strip()

    code = re.sub(r"^```(?:mermaid)?\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"\n?\s*```$", "", code, flags=re.MULTILINE)

    code = code.replace("\xa0", " ").replace("\u200b", "").replace("\r\n", "\n")
    code = (code.replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2018", "'").replace("\u2019", "'")
                .replace("\u00ab", '"').replace("\u00bb", '"'))

    # --- 1. Extraire et RETIRER un éventuel bloc d'init déjà présent ---
    existing_init = None
    init_match = _INIT_BLOCK_PATTERN.match(code)
    if init_match:
        existing_init = init_match.group(0).rstrip("\n")
        code = code[init_match.end():].strip()

    # --- 2. Vérifier l'en-tête UNIQUEMENT sur le corps (sans le thème) ---
    lines = [l.strip() for l in code.split("\n") if l.strip()]
    first_line = lines[0] if lines else ""
    if not any(first_line.startswith(hdr) for hdr in _VALID_MERMAID_HEADERS):
        code = f"flowchart TD\n{code}"

    # --- 3. Corrections de formes/nœuds (inchangé) ---
    code = re.sub(r'\(\[([^\]]+)\]\)', r'["\1"]', code)
    code = re.sub(r'\(\(([^)]+)\)\)', r'["\1"]', code)
    code = re.sub(r'\[\[([^\]]+)\]\]', r'["\1"]', code)
    code = re.sub(r'\{\{([^}]+)\}\}', r'["\1"]', code)

    cleaned_lines: List[str] = []
    in_er_block = False
    is_er_diagram = "erDiagram" in code

    for raw_line in code.split("\n"):
        line_str = raw_line.rstrip()
        stripped = line_str.strip()

        if not stripped:
            cleaned_lines.append(line_str)
            continue

        if any(stripped.startswith(hdr) for hdr in _VALID_MERMAID_HEADERS) or \
           stripped.startswith("subgraph") or stripped == "end":
            cleaned_lines.append(line_str)
            continue

        if is_er_diagram:
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
                    field_name, type_name, key_marker = match_attr.groups()
                    fixed = f"{type_name} {field_name}" + (f" {key_marker}" if key_marker else "")
                    leading = line_str[:len(line_str) - len(line_str.lstrip())]
                    cleaned_lines.append(leading + fixed)
                    continue

        line_str = re.sub(
            r'(-->|---|==>|-\.->)\|([^"|\n]+)\|',
            lambda m: f'{m.group(1)}|"{m.group(2).strip().replace(chr(34), chr(39))}"|',
            line_str
        )
        line_str = _NODE_PATTERN.sub(_quote_node_label, line_str)
        cleaned_lines.append(line_str)

    code = "\n".join(cleaned_lines)
    code = re.sub(r'-->\|([^|]+)\|>', r'-->|\1|', code)
    code = re.sub(r'\n\s*\n', '\n', code)

    # --- 4. Réinjection du thème : réutilise celui déjà présent si possible ---
    theme_block = existing_init if existing_init else MERMAID_THEME_CONFIG_FULL.strip()
    code = f"{theme_block}\n{code}"

    return code.strip()


# ===========================================================================
# 2. RENDU DES DIAGRAMMES MERMAID EN IMAGES HD
# ===========================================================================

def _create_placeholder_image(output_path: str, label: str) -> None:
    """Crée une image de substitution lisible lorsque le rendu Mermaid échoue."""
    try:
        img = PILImage.new("RGB", (1000, 260), color="#EBF8FF")
        d = ImageDraw.Draw(img)
        d.rectangle([(0, 0), (999, 259)], outline="#2B6CB0", width=3)
        d.text((30, 110), f"[ Schema non compile : {label} ]", fill="#1A365D")
        img.save(output_path)
    except Exception:
        with open(output_path, "wb") as f:
            f.write(b"")


def render_mermaid_diagrams(
    markdown_text: str,
    output_dir: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Détecte les blocs ```mermaid``` du Markdown, les nettoie, les compile en PNG
    haute définition (via mmdc) avec le thème bleu technique, et remplace chaque
    bloc par une référence d'image Markdown standard.
    Retourne (markdown_mis_a_jour, liste_des_chemins_images).
    """
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="mermaid_images_")
    os.makedirs(output_dir, exist_ok=True)

    diagram_pattern = re.compile(r"```mermaid[ \t]*\r?\n(.*?)\r?\n```", re.DOTALL | re.IGNORECASE)
    matches = list(diagram_pattern.finditer(markdown_text))

    rendered_image_paths: List[str] = []
    updated_markdown = markdown_text
    mmdc_bin = shutil.which("mmdc") or shutil.which("mmdc.cmd") or "mmdc"

    for idx, match in enumerate(matches):
        mermaid_code = clean_mermaid_code(match.group(1))

        img_path = os.path.join(output_dir, f"diagram_{idx + 1}.png")
        mmd_file = os.path.join(output_dir, f"diag_{idx + 1}.mmd")
        with open(mmd_file, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        success = False
        try:
            # NB : on ne passe volontairement PAS de flag "-t" (theme) car le thème
            # est déjà injecté dans le fichier .mmd via %%{init: ...}%% ; le combiner
            # avec "-t dark" (bug de l'ancienne version) écrasait le thème bleu voulu.
            cmd = [mmdc_bin, "-i", mmd_file, "-o", img_path, "-b", "white", "-w", "1920", "-s", "3"]
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60, shell=(os.name == "nt")
            )
            if res.returncode == 0 and os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                success = True
                print(f"[LAYOUT] Diagramme #{idx + 1} rendu en HD (thème bleu technique).")
            else:
                print(f"[LAYOUT][WARN] Echec mmdc diagramme #{idx + 1} : {res.stderr}")
        except Exception as e:
            print(f"[LAYOUT][ERROR] Erreur d'execution mmdc : {e}")

        if not success:
            _create_placeholder_image(img_path, f"Diagramme #{idx + 1}")

        rendered_image_paths.append(img_path)
        updated_markdown = updated_markdown.replace(match.group(0), f"\n![Diagramme #{idx + 1}]({img_path})\n")

    return updated_markdown, rendered_image_paths


# ===========================================================================
# 3. AIDES DE RENDU MARKDOWN -> REPORTLAB
# ===========================================================================

def _escape_xml(text: str) -> str:
    return text.replace("&", "&").replace("<", "<").replace(">", ">")


def _inline_markdown_to_reportlab(text: str) -> str:
    """
    Convertit la syntaxe Markdown inline (gras, italique, code, liens) en
    balisage compatible ReportLab, en échappant correctement le XML au préalable.
    """
    text = _escape_xml(text)

    # Liens [texte](url)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s\)]+)\)",
        r'<link href="\2" color="#2B6CB0"><u>\1</u></link>',
        text
    )

    # ⚠️ CORRECTIF : on extrait le contenu des spans de code `...` dans des
    # espaces réservés AVANT d'appliquer gras/italique, puis on les réinjecte
    # à la fin. Sans ça, un identifiant comme `course_id` (un seul underscore)
    # laissait la regex d'italique chercher son underscore "jumeau" plus loin
    # dans le texte — parfois dans un AUTRE span de code (ex: `sequence_order`)
    # — ce qui ouvrait un <i> à l'intérieur d'un <font> et le refermait dans
    # un <font> différent plus loin : un croisement de balises XML invalide
    # qui faisait échouer toute la compilation du PDF ("saw </font> instead
    # of expected </i>"). Les espaces réservés ne contiennent ni "_" ni "*",
    # donc ils sont totalement invisibles pour les regex de gras/italique.
    code_spans: List[str] = []

    def _stash_code(match: "re.Match") -> str:
        code_spans.append(match.group(1))
        return f"\x00CODE{len(code_spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", _stash_code, text)

    # Gras **texte** ou __texte__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Italique *texte* ou _texte_ (après le gras pour éviter les conflits)
    text = re.sub(r"(?<!\*)\*(?!\*)([^\*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!_)_(?!_)([^_]+?)_(?!_)", r"<i>\1</i>", text)

    # Réinjection des spans de code, jamais vus par gras/italique
    for idx, code_content in enumerate(code_spans):
        text = text.replace(
            f"\x00CODE{idx}\x00",
            f'<font face="Courier" size="9.5" color="#1A365D">{code_content}</font>'
        )

    return text


def _is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False
    return bool(re.fullmatch(r"[\s\|:\-]+", stripped)) and "-" in stripped


def _split_table_row(line: str) -> List[str]:
    cells = line.strip()
    if cells.startswith("|"):
        cells = cells[1:]
    if cells.endswith("|"):
        cells = cells[:-1]
    return [c.strip() for c in cells.split("|")]


def _fit_image_dimensions(img_path: str, max_width: float, max_height: float) -> Tuple[float, float, bool]:
    """
    Calcule les dimensions d'une image en préservant son ratio d'aspect,
    pour qu'elle tienne dans (max_width, max_height). Retourne aussi un
    booléen "compressed_beyond_width_fit" indiquant si la stratégie
    'fit_to_width' n'a pas suffi (image encore trop haute) -> signal
    utile pour le rapport de débordement visuel.
    """
    try:
        with PILImage.open(img_path) as im:
            img_w, img_h = im.size
    except Exception:
        return max_width, max_height * 0.6, False

    if img_w <= 0 or img_h <= 0:
        return max_width, max_height * 0.6, False

    # Stratégie "fit_to_width" : on cale d'abord sur la largeur
    scale_w = max_width / img_w
    fit_w, fit_h = img_w * scale_w, img_h * scale_w

    overflow = False
    if fit_h > max_height:
        # La largeur seule ne suffit pas : on recale aussi sur la hauteur
        scale_h = max_height / img_h
        fit_w, fit_h = img_w * scale_h, img_h * scale_h
        overflow = True

    return fit_w, fit_h, overflow


# ===========================================================================
# 4. CANVAS AVEC NUMÉROTATION "Page X sur Y" + EN-TÊTE / PIED DE PAGE
# ===========================================================================

def _make_numbered_canvas(theme: Dict[str, Any], layout_spec: Dict[str, Any]):
    """Fabrique une classe Canvas liée au thème courant (recette standard ReportLab)."""

    hf_config = layout_spec.get("header_footer_config", {}) or {}
    header_text = hf_config.get("header_text", "")
    footer_left = hf_config.get("footer_left", "")

    class NumberedCanvas(pdf_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            pdf_canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self._draw_decorations(total_pages)
                pdf_canvas.Canvas.showPage(self)
            pdf_canvas.Canvas.save(self)

        def _draw_decorations(self, total_pages: int):
            self.saveState()
            page_num = self._pageNumber

            # En-tête (à partir de la 2e page, après la couverture)
            if page_num > 1 and header_text:
                self.setFont("Helvetica-Bold", 8)
                self.setFillColor(theme["primary"])
                self.drawString(theme["margin_left"], A4[1] - theme["margin_top"] + 10, header_text)
                self.setStrokeColor(theme["secondary"])
                self.setLineWidth(0.5)
                self.line(
                    theme["margin_left"], A4[1] - theme["margin_top"],
                    A4[0] - theme["margin_right"], A4[1] - theme["margin_top"]
                )

            # Pied de page : numérotation
            self.setFont("Helvetica", 8)
            self.setFillColor(theme["text"])
            self.drawRightString(
                A4[0] - theme["margin_right"], 25,
                f"Page {page_num} sur {total_pages}"
            )
            if footer_left:
                self.drawString(theme["margin_left"], 25, footer_left)

            self.setStrokeColor(theme["border"])
            self.setLineWidth(0.5)
            self.line(theme["margin_left"], 35, A4[0] - theme["margin_right"], 35)
            self.restoreState()

    return NumberedCanvas


# ===========================================================================
# 5. DOCTEMPLATE AVEC SIGNETS PDF + ENTRÉES DE TABLE DES MATIÈRES CLIQUABLES
# ===========================================================================
class _BookmarkedDocTemplate(BaseDocTemplate):
    """
    DocTemplate qui, à chaque titre (H1/H2/H3) rencontré pendant la construction :
      1. pose un signet PDF (panneau de navigation, comme les \section de LaTeX) ;
      2. notifie la TableOfContents avec une clé de lien -> entrées cliquables.
    Construit en deux passes (multiBuild) pour connaître les vrais numéros de page.

    IMPORTANT : le pied de page "Page X sur Y" est dessiné directement dans
    afterPage() (flux normal de pagination de ReportLab), et non plus via un
    Canvas personnalisé qui différait showPage(). Cette dernière approche
    empêchait le compteur de pages interne du document PDF d'avancer avant
    save(), ce qui faisait pointer TOUS les signets/liens internes
    (bookmarkPage) vers la même page non finalisée (= toujours la couverture).
    """

    HEADING_LEVELS = {"DocH1": 0, "DocH2": 1, "DocH3": 2}
    def __init__(self, *args, theme: Dict[str, Any], layout_spec: Dict[str, Any], **kwargs):
        BaseDocTemplate.__init__(self, *args, **kwargs)
        self._bookmark_counter = 0
        self._theme = theme
        self._layout_spec = layout_spec
        self._known_total_pages = None
        # Texte de chaque titre détecté, dans l'ordre : alimente "toc_entries"
        # attendu par calculate_scs() dans app/core/metrics.py.
        self._toc_entries_text: List[str] = []
        # Stocke les infos pour créer les liens cliquables dans la TOC : (level, text, page, key)
        self._toc_entries_for_links: List[Tuple[int, str, int, str]] = []

    def build(self, flowables, **kwargs):
        self._bookmark_counter = 0
        self._toc_entries_text = []
        self._toc_entries_for_links = []
        BaseDocTemplate.build(self, flowables, **kwargs)
        self._known_total_pages = self.page

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style_name = getattr(flowable.style, "name", "")
        if style_name not in self.HEADING_LEVELS:
            return

        level = self.HEADING_LEVELS[style_name]
        text = flowable.getPlainText()
        if not text.strip():
            return

        self._bookmark_counter += 1
        key = f"toc-anchor-{self._bookmark_counter}"

        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))
        self._toc_entries_text.append(text)
        self._toc_entries_for_links.append((level, text, self.page, key))


    def afterPage(self):
        """
        Dessine l'en-tête et le pied de page dans le flux normal de
        pagination de ReportLab (appelé après chaque page réellement
        finalisée) — contrairement à l'ancienne approche NumberedCanvas
        qui cassait bookmarkPage().
        """
        theme = self._theme
        hf_config = (self._layout_spec.get("header_footer_config", {}) or {})
        header_text = hf_config.get("header_text", "")
        footer_left = hf_config.get("footer_left", "")

        page_num = self.page
        total_pages = self._known_total_pages or page_num

        canv = self.canv
        canv.saveState()

        if page_num > 1 and header_text:
            canv.setFont("Helvetica-Bold", 8)
            canv.setFillColor(theme["primary"])
            canv.drawString(theme["margin_left"], A4[1] - theme["margin_top"] + 10, header_text)
            canv.setStrokeColor(theme["secondary"])
            canv.setLineWidth(0.5)
            canv.line(
                theme["margin_left"], A4[1] - theme["margin_top"],
                A4[0] - theme["margin_right"], A4[1] - theme["margin_top"]
            )

        canv.setFont("Helvetica", 8)
        canv.setFillColor(theme["text"])
        canv.drawRightString(
            A4[0] - theme["margin_right"], 25,
            f"Page {page_num} sur {total_pages}"
        )
        if footer_left:
            canv.drawString(theme["margin_left"], 25, footer_left)

        canv.setStrokeColor(theme["border"])
        canv.setLineWidth(0.5)
        canv.line(theme["margin_left"], 35, A4[0] - theme["margin_right"], 35)

        canv.restoreState()


# ===========================================================================
# 6. COMPILATION MARKDOWN -> PDF
# ===========================================================================

def compile_markdown_to_pdf(
    markdown_text: str,
    output_pdf_path: str,
    layout_spec: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compile le Markdown enrichi (doc.md + images de diagrammes déjà rendues)
    en un PDF avec :
      - une page de garde et une table des matières RÉELLEMENT cliquable
        (clic -> saut à la section, comme \tableofcontents en LaTeX) ;
      - un panneau de signets PDF (navigation latérale) ;
      - un thème bleu technique piloté par layout_spec.json ;
      - des tableaux, du code, des citations et des images correctement mis à
        l'échelle (sans déformation).
    """
    theme = _build_theme(layout_spec)
    doc_meta = layout_spec.get("document_metadata", {}) or {}
    project_title = doc_meta.get("title", "Documentation Technique")
    project_subtitle = doc_meta.get(
        "subtitle", "Documentation Technique & Architecture du Pipeline"
    )

    os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)

    # --- Styles ---
    styles = getSampleStyleSheet()
    typo = theme["typo"]

    title_style = ParagraphStyle(
        "CoverTitle", fontName=theme["font_heading"], fontSize=28, leading=34,
        textColor=theme["primary"], alignment=TA_CENTER, spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        "CoverSub", fontName=theme["font_body"], fontSize=13, leading=16,
        textColor=theme["text"], alignment=TA_CENTER, spaceAfter=24
    )
    h1_style = ParagraphStyle(
        "DocH1", parent=styles["Normal"], fontName=theme["font_heading"],
        fontSize=typo["h1"]["font_size"], leading=typo["h1"]["leading"],
        textColor=theme["primary"], spaceBefore=18, spaceAfter=typo["h1"]["space_after"],
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        "DocH2", parent=styles["Normal"], fontName=theme["font_heading"],
        fontSize=typo["h2"]["font_size"], leading=typo["h2"]["leading"],
        textColor=theme["secondary"], spaceBefore=16, spaceAfter=typo["h2"]["space_after"],
        keepWithNext=True
    )
    h3_style = ParagraphStyle(
        "DocH3", parent=styles["Normal"], fontName=theme["font_heading"],
        fontSize=typo["h3"]["font_size"], leading=typo["h3"]["leading"],
        textColor=theme["secondary"], spaceBefore=12, spaceAfter=typo["h3"]["space_after"],
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        "DocBody", parent=styles["Normal"], fontName=theme["font_body"],
        fontSize=typo["body"]["font_size"], leading=typo["body"]["leading"],
        textColor=theme["text"], spaceAfter=typo["body"]["space_after"]
    )
    bullet_style = ParagraphStyle(
        "DocBullet", parent=body_style, leftIndent=18, bulletIndent=6, spaceAfter=4
    )
    quote_style = ParagraphStyle(
        "DocQuote", parent=body_style, leftIndent=24, textColor=theme["secondary"],
        borderColor=theme["border"], italic=True
    )
    code_style = ParagraphStyle(
        "DocCode", parent=styles["Normal"], fontName="Courier",
        fontSize=typo["code"]["font_size"], leading=typo["code"]["leading"],
        textColor=theme["primary"]
    )
    tbl_hdr_style = ParagraphStyle(
        "TblHdr", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=typo["table_cell"]["font_size"], leading=typo["table_cell"]["leading"],
        textColor=colors.white
    )
    tbl_cell_style = ParagraphStyle(
        "TblCell", parent=styles["Normal"], fontName="Helvetica",
        fontSize=typo["table_cell"]["font_size"], leading=typo["table_cell"]["leading"],
        textColor=theme["text"]
    )

    toc_level_styles = [
        ParagraphStyle("TOC0", parent=body_style, fontName="Helvetica-Bold",
                        fontSize=11.5, leftIndent=0, spaceAfter=6, textColor=theme["primary"]),
        ParagraphStyle("TOC1", parent=body_style, fontSize=11, leftIndent=16,
                        spaceAfter=4, textColor=theme["text"]),
        ParagraphStyle("TOC2", parent=body_style, fontSize=10, leftIndent=32,
                        spaceAfter=3, textColor=theme["text"]),
    ]

    # --- Story : couverture + TOC + contenu ---
    story: List[Any] = []
    story.append(Spacer(1, 120))
    story.append(Paragraph(_escape_xml(project_title.upper()), title_style))
    story.append(Paragraph(_escape_xml(project_subtitle), subtitle_style))
    story.append(HRFlowable(width="60%", thickness=1, color=theme["secondary"], hAlign="CENTER"))
    story.append(PageBreak())

    story.append(Paragraph("Table des Matières", ParagraphStyle(
        "TOCTitle", fontName=theme["font_heading"], fontSize=16, leading=20,
        textColor=theme["primary"], spaceAfter=16
    )))
    toc = TableOfContents()
    toc.levelStyles = toc_level_styles
    toc.dotsMinLevel = 0
    story.append(toc)
    story.append(PageBreak())

    diagrams_overflow: List[str] = []
    diagrams_rendered = 0

    lines = markdown_text.splitlines()
    i, n = 0, len(lines)
    in_code_block = False
    code_buffer: List[str] = []

    def flush_code_block():
        if not code_buffer:
            return
        code_text = "<br/>".join(_escape_xml(l).replace(" ", "&nbsp;") for l in code_buffer)
        tbl = Table([[Paragraph(code_text, code_style)]], colWidths=[theme["max_width_pt"]])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), theme["bg_light"]),
            ("BOX", (0, 0), (-1, -1), 0.6, theme["secondary"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(Spacer(1, 4))
        story.append(tbl)
        story.append(Spacer(1, 6))
        code_buffer.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # --- Blocs de code ```
        if stripped.startswith("```"):
            if in_code_block:
                flush_code_block()
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        # --- Tableaux Markdown : ligne | a | b | suivie d'une ligne séparatrice
        if "|" in stripped and stripped.startswith("|") and i + 1 < n and _is_table_separator(lines[i + 1]):
            header_cells = _split_table_row(stripped)
            table_rows = [[Paragraph(_inline_markdown_to_reportlab(c), tbl_hdr_style) for c in header_cells]]
            j = i + 2
            while j < n and lines[j].strip().startswith("|"):
                row_cells = _split_table_row(lines[j])
                # Complète/tronque pour matcher le nombre de colonnes de l'en-tête
                row_cells = (row_cells + [""] * len(header_cells))[:len(header_cells)]
                table_rows.append([Paragraph(_inline_markdown_to_reportlab(c), tbl_cell_style) for c in row_cells])
                j += 1
            col_width = theme["max_width_pt"] / max(len(header_cells), 1)
            tbl = Table(table_rows, colWidths=[col_width] * len(header_cells), repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), theme["primary"]),
                ("GRID", (0, 0), (-1, -1), 0.5, theme["border"]),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, theme["bg_light"]]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(Spacer(1, 6))
            story.append(tbl)
            story.append(Spacer(1, 8))
            i = j
            continue

        # --- Images (diagrammes rendus par render_mermaid_diagrams)
        img_match = re.search(r"!\[.*?\]\((.*?)\)", line)
        if img_match:
            img_path = img_match.group(1)
            if os.path.exists(img_path):
                diagrams_rendered += 1
                fit_w, fit_h, overflowed = _fit_image_dimensions(
                    img_path, theme["max_width_pt"], theme["max_height_pt"]
                )
                if overflowed:
                    diagrams_overflow.append(os.path.basename(img_path))
                story.append(Spacer(1, 8))
                story.append(RLImage(img_path, width=fit_w, height=fit_h, hAlign="CENTER"))
                story.append(Spacer(1, 8))
            i += 1
            continue

        # --- Titres
        if stripped.startswith("#### "):
            story.append(Paragraph(_inline_markdown_to_reportlab(stripped[5:].strip()), h3_style))
        elif stripped.startswith("### "):
            story.append(KeepTogether(Paragraph(_inline_markdown_to_reportlab(stripped[4:].strip()), h3_style)))
        elif stripped.startswith("## "):
            story.append(KeepTogether(Paragraph(_inline_markdown_to_reportlab(stripped[3:].strip()), h2_style)))
        elif stripped.startswith("# "):
            story.append(KeepTogether(Paragraph(_inline_markdown_to_reportlab(stripped[2:].strip()), h1_style)))

        # --- Citations
        elif stripped.startswith("> "):
            story.append(Paragraph(_inline_markdown_to_reportlab(stripped[2:].strip()), quote_style))

        # --- Séparateur horizontal
        elif re.fullmatch(r"-{3,}", stripped) or re.fullmatch(r"\*{3,}", stripped):
            story.append(HRFlowable(width="100%", thickness=0.6, color=theme["border"], spaceBefore=6, spaceAfter=6))

        # --- Listes à puces / numérotées
        elif stripped.startswith(("- ", "* ")):
            item = _inline_markdown_to_reportlab(stripped[2:].strip())
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{item}", bullet_style))
        elif re.match(r"^\d+\.\s", stripped):
            item = _inline_markdown_to_reportlab(re.sub(r"^\d+\.\s", "", stripped))
            num = re.match(r"^(\d+)\.", stripped).group(1)
            story.append(Paragraph(f"{num}.&nbsp;&nbsp;{item}", bullet_style))

        # --- Paragraphe normal / ligne vide
        elif stripped:
            story.append(Paragraph(_inline_markdown_to_reportlab(stripped), body_style))
        else:
            story.append(Spacer(1, 4))

        i += 1

    if in_code_block:
        flush_code_block()

    # --- Construction du document (deux passes pour la TOC + signets) ---
    doc = _BookmarkedDocTemplate(
        output_pdf_path,
        pagesize=theme["page_size"],
        leftMargin=theme["margin_left"], rightMargin=theme["margin_right"],
        topMargin=theme["margin_top"], bottomMargin=theme["margin_bottom"],
        title=project_title, author=doc_meta.get("author", "Spec Kit Pipeline"),
        theme=theme, layout_spec=layout_spec
    )
    frame = Frame(
        theme["margin_left"], theme["margin_bottom"],
        theme["page_size"][0] - theme["margin_left"] - theme["margin_right"],
        theme["page_size"][1] - theme["margin_top"] - theme["margin_bottom"],
        id="main_frame"
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    doc.multiBuild(story)

    # ⚠️ CORRECTIF : l'ancien post-traitement PyMuPDF (_make_toc_entries_clickable)
    # rouvrait ce PDF juste après que doc.multiBuild() l'ait déjà écrit avec succès,
    # puis le ré-écrivait avec doc.save(pdf_path, incremental=True, ...) — une
    # opération fragile (verrouillage fichier, notamment sous Windows) qui pouvait
    # échouer silencieusement (except Exception: pass) et laisser le PDF tronqué
    # ou absent, alors qu'un fichier PARFAITEMENT VALIDE existait déjà.
    # Il est de toute façon inutile : le mécanisme natif ReportLab ci-dessus
    # (canv.bookmarkPage + notify("TOCEntry", (level, text, page, key))) produit
    # déjà une TOC réellement cliquable à lui seul, sans repasser par PyMuPDF.
    bookmarks_created = getattr(doc, "_bookmark_counter", 0) > 0
    primary_hex = (layout_spec.get("branding_theme", {}) or {}).get("primary_color") or "#1A365D"

    return {
        "output_pdf_path": output_pdf_path,
        "has_clickable_toc": bookmarks_created,
        "has_pdf_bookmarks": bookmarks_created,
        "diagrams_rendered_in_pdf": diagrams_rendered,
        "diagrams_overflowing": diagrams_overflow,
        "toc_entries": getattr(doc, "_toc_entries_text", []),
        "applied_primary_color": primary_hex,
        "has_page_numbers": True,
    }


def _make_toc_entries_clickable(pdf_path: str, toc_entries: List[Tuple[int, str, int, str]]) -> None:
    """
    Post-traite le PDF pour rendre les entrées de la Table des Matières cliquables.
    Ajoute des annotations de lien (Link Annotations) sur le texte de la TOC
    qui pointent vers les signets (bookmarks) correspondants.
    """
    if not toc_entries:
        return
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return

    try:
        doc = fitz.open(pdf_path)
        if len(doc) < 2:
            doc.close()
            return

        # La TOC est sur la page 2 (index 1) : page 1 = couverture, page 2 = TOC
        toc_page = doc[1]
        
        # Recherche le texte de chaque entrée de TOC dans la page et ajoute un lien
        for level, text, target_page, key in toc_entries:
            # Nettoie le texte pour la recherche (supprime numéros, espaces en trop)
            search_text = text.strip()
            if not search_text:
                continue
            
            # Recherche toutes les occurrences du texte sur la page TOC
            text_instances = toc_page.search_for(search_text, quads=False)
            for inst in text_instances:
                # Étend légèrement le rectangle pour couvrir toute la ligne (numéros de page inclus)
                # inst est un fitz.Rect (x0, y0, x1, y1)
                link_rect = fitz.Rect(inst.x0 - 5, inst.y0 - 1, inst.x1 + 50, inst.y1 + 1)
                
                # Ajoute l'annotation de lien interne (pointe vers le bookmark nommé)
                toc_page.insert_link({
                    "kind": fitz.LINK_NAMED,
                    "named": key,  # Le nom du bookmark (ex: "toc-anchor-1")
                    "from": link_rect,
                })
        
        doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()
    except Exception:
        # En cas d'erreur, on laisse le PDF sans liens cliquables dans la TOC
        # Les signets du panneau de navigation fonctionnent quand même
        pass


# ===========================================================================
# 7. INSPECTION DU PDF GÉNÉRÉ (métadonnées + rapport de débordement visuel)
# ===========================================================================

def _count_pages_fallback(pdf_path: str) -> int:
    """Compte les pages sans dépendance externe si PyMuPDF n'est pas disponible."""
    try:
        with open(pdf_path, "rb") as f:
            data = f.read()
        count = len(re.findall(rb"/Type\s*/Page[^s]", data))
        return count if count > 0 else 1
    except Exception:
        return 0


def inspect_generated_pdf(
    pdf_path: str,
    compilation_result: Dict[str, Any],
    rendered_diagrams_count: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Inspecte le PDF produit pour en extraire les métriques nécessaires à
    l'arbitrage de publication (LayoutEvaluatorService).
    Retourne (rendered_pdf_metadata, layout_overflow_report).
    """
    pdf_generated = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0
    page_count = 0
    file_size_bytes = os.path.getsize(pdf_path) if pdf_generated else 0

    if pdf_generated:
        try:
            import fitz  # PyMuPDF, optionnel selon l'environnement d'exécution
            with fitz.open(pdf_path) as doc:
                page_count = doc.page_count
        except ImportError:
            page_count = _count_pages_fallback(pdf_path)
        except Exception:
            page_count = _count_pages_fallback(pdf_path)

    diagrams_rendered_in_pdf = compilation_result.get("diagrams_rendered_in_pdf", 0)

    # ⚠️ CORRECTIF : file_size_bytes / rendered_diagrams_count / toc_entries /
    # applied_primary_color / has_page_numbers manquaient entièrement, alors
    # que app/core/metrics.py (calculate_rsr, calculate_dvr, calculate_scs)
    # les lit sous ces noms précis. Résultat : RSR=0 systématique,
    # DVR=0 dès qu'un diagramme existe, SCS proche de 0 — indépendamment de
    # la qualité réelle du PDF produit. On conserve les anciennes clés
    # (diagrams_rendered_in_pdf, overflow_diagrams_count) pour ne rien casser
    # ailleurs, et on ajoute celles réellement attendues par metrics.py.
    rendered_pdf_metadata = {
        "pdf_generated": pdf_generated,
        "page_count": page_count,
        "file_size_bytes": file_size_bytes,
        "has_clickable_toc": compilation_result.get("has_clickable_toc", False),
        "has_pdf_bookmarks": compilation_result.get("has_pdf_bookmarks", False),
        "diagrams_rendered_in_pdf": diagrams_rendered_in_pdf,
        "rendered_diagrams_count": diagrams_rendered_in_pdf,
        "toc_entries": compilation_result.get("toc_entries", []),
        "applied_primary_color": compilation_result.get("applied_primary_color"),
        "has_page_numbers": compilation_result.get("has_page_numbers", False),
    }

    diagrams_overflow = compilation_result.get("diagrams_overflowing", [])
    overflow_count = len(diagrams_overflow)
    overflow_rate = (overflow_count / rendered_diagrams_count * 100.0) if rendered_diagrams_count else 0.0

    layout_overflow_report = {
        "overflow_diagrams_count": overflow_count,
        "overflow_events_count": overflow_count,
        "total_rendered_blocks": max(rendered_diagrams_count, 1),
        "overflow_diagram_files": diagrams_overflow,
        "visual_overflow_rate": round(overflow_rate, 2),
        "render_success_rate": round(
            (diagrams_rendered_in_pdf / rendered_diagrams_count * 100.0)
            if rendered_diagrams_count else 100.0, 2
        ),
    }

    return rendered_pdf_metadata, layout_overflow_report
# # app/utils/layout_tools.py
# """
# layout_tools.py — Outils de compilation PDF et de rendu visuel pour le Layout Agent.

# Version HD : 
# - Diagrammes à proportions naturelles (Aspect Ratio) & Typographie augmentée (11pt)
# - Table des matières RÉELLEMENT cliquable (liens internes + panneau de signets PDF)
# - Thème bleu technique piloté par layout_spec.json
# """

# import os
# import re
# import shutil
# import subprocess
# import tempfile
# from typing import Dict, Any, List, Tuple, Optional

# from PIL import Image as PILImage

# from reportlab.lib.pagesizes import A4, letter
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.enums import TA_CENTER, TA_LEFT
# from reportlab.platypus import (
#     BaseDocTemplate, PageTemplate, Frame,
#     Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image as RLImage,
#     KeepTogether
# )
# from reportlab.platypus.tableofcontents import TableOfContents
# from reportlab.pdfgen import canvas as pdf_canvas

# print("[LAYOUT] layout_tools.py v3.0 (TOC cliquable, signets PDF, thème dynamique) actif")


# # ===========================================================================
# # 0. UTILITAIRES DE THÈME (lecture de layout_spec.json avec valeurs par défaut)
# # ===========================================================================

# def _color(hex_value: str, fallback: str) -> colors.Color:
#     try:
#         return colors.HexColor(hex_value or fallback)
#     except Exception:
#         return colors.HexColor(fallback)


# def _build_theme(layout_spec: Dict[str, Any]) -> Dict[str, Any]:
#     """Construit un dictionnaire de thème (couleurs, typographie, marges) à partir de layout_spec.json."""
#     branding = layout_spec.get("branding_theme", {}) or {}
#     typo = layout_spec.get("typography_rules", {}) or {}
#     doc_meta = layout_spec.get("document_metadata", {}) or {}
#     margins = doc_meta.get("margins_mm", {}) or {}
#     diagram_limits = layout_spec.get("diagram_rendering_limits", {}) or {}

#     from reportlab.lib.units import mm as MM

#     return {
#         "primary": _color(branding.get("primary_color"), "#1A365D"),
#         "secondary": _color(branding.get("secondary_color"), "#2B6CB0"),
#         "accent": _color(branding.get("accent_color"), "#38A169"),
#         "bg_light": _color(branding.get("background_light"), "#F7FAFC"),
#         "text": _color(branding.get("text_color"), "#2D3748"),
#         "border": _color(branding.get("border_color"), "#CBD5E0"),
#         "font_heading": branding.get("font_family_heading", "Helvetica-Bold"),
#         "font_body": branding.get("font_family_body", "Helvetica"),
#         "page_size": letter if str(doc_meta.get("page_size", "A4")).upper() == "LETTER" else A4,
#         "margin_top": margins.get("top", 22) * MM,
#         "margin_bottom": margins.get("bottom", 20) * MM,
#         "margin_left": margins.get("left", 18) * MM,
#         "margin_right": margins.get("right", 18) * MM,
#         "typo": {
#             "h1": typo.get("h1", {"font_size": 22, "leading": 26, "space_after": 12}),
#             "h2": typo.get("h2", {"font_size": 14.5, "leading": 18, "space_after": 8}),
#             "h3": typo.get("h3", {"font_size": 12, "leading": 15, "space_after": 6}),
#             "body": typo.get("body", {"font_size": 11.0, "leading": 15.5, "space_after": 7}),
#             "table_cell": typo.get("table_cell", {"font_size": 9.0, "leading": 12.0}),
#             "code": typo.get("code", {"font_size": 9.0, "leading": 12.0}),
#         },
#         "max_width_pt": diagram_limits.get("max_width_pt", 504),
#         "max_height_pt": diagram_limits.get("max_height_pt", 650),
#         "fallback_scaling_strategy": diagram_limits.get("fallback_scaling_strategy", "fit_to_width"),
#     }


# # ===========================================================================
# # 1. NETTOYAGE ET ENRICHISSEMENT DU CODE MERMAID (thème bleu technique)
# # ===========================================================================

# MERMAID_THEME_CONFIG_FULL = """%%{init: {
#   'theme': 'base',
#   'themeVariables': {
#     'primaryColor': '#1A365D',
#     'primaryTextColor': '#1A202C',
#     'primaryBorderColor': '#2B6CB0',
#     'lineColor': '#2B6CB0',
#     'secondaryColor': '#EBF8FF',
#     'tertiaryColor': '#EBF8FF',
#     'background': '#FFFFFF',
#     'mainBkg': '#FFFFFF',
#     'secondBkg': '#EBF8FF',
#     'tertiaryBkg': '#F7FAFC',
#     'secondaryTextColor': '#4A5568',
#     'fontSize': '16px',
#     'fontFamily': 'Inter, system-ui, sans-serif',
#     'nodePadding': '15px',
#     'borderRadius': '8px',
#     'edgeLabelBackground': '#EBF8FF',
#     'clusterBkg': '#F7FAFC',
#     'clusterBorder': '#2B6CB0',
#     'defaultLinkColor': '#2B6CB0',
#     'titleColor': '#1A365D',
#     'actorBorder': '#2B6CB0',
#     'actorBkg': '#EBF8FF',
#     'actorTextColor': '#1A365D',
#     'actorLineColor': '#2B6CB0',
#     'signalColor': '#2B6CB0',
#     'signalTextColor': '#1A202C',
#     'labelBoxBorderColor': '#2B6CB0',
#     'labelBoxBkgColor': '#EBF8FF',
#     'labelTextColor': '#1A202C',
#     'loopTextColor': '#1A202C',
#     'arrowHeadColor': '#2B6CB0',
#     'sequenceNumberColor': '#1A365D',
#     'sequenceActorBorder': '#2B6CB0',
#     'sequenceActorBkg': '#EBF8FF',
#     'sequenceArrowColor': '#2B6CB0',
#     'noteBkgColor': '#FFF5EB',
#     'noteBorderColor': '#DD6B20',
#     'noteTextColor': '#1A202C'
#   }
# }}%%
# """

# _VALID_MERMAID_HEADERS = (
#     "flowchart", "graph", "sequenceDiagram", "classDiagram", "erDiagram",
#     "stateDiagram", "gantt", "mindmap", "pie", "gitGraph", "C4Context"
# )

# _NODE_PATTERN = re.compile(
#     r'(\b[A-Za-z0-9_]+)(\[\s*|\(\s*|\{\s*)'
#     r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^\]\}\)]+)'
#     r'(\s*\]|\s*\)|\s*\})'
# )


# def _quote_node_label(match: "re.Match") -> str:
#     node_id, open_symbol, label, close_symbol = match.groups()
#     label = label.strip()
#     if (label.startswith('"') and label.endswith('"')) or (label.startswith("'") and label.endswith("'")):
#         clean_label = label[1:-1].replace('"', "'")
#     else:
#         clean_label = label.replace('"', "'")
#     return f'{node_id}{open_symbol}"{clean_label}"{close_symbol}'


# _INIT_BLOCK_PATTERN = re.compile(r"^%%\{init:.*?\}%%\s*\n?", re.DOTALL)

# def clean_mermaid_code(code: str) -> str:
#     if not code:
#         return ""
#     code = str(code).strip()

#     code = re.sub(r"^```(?:mermaid)?\s*\n?", "", code, flags=re.MULTILINE)
#     code = re.sub(r"\n?\s*```$", "", code, flags=re.MULTILINE)

#     code = code.replace("\xa0", " ").replace("\u200b", "").replace("\r\n", "\n")
#     code = (code.replace("\u201c", '"').replace("\u201d", '"')
#                 .replace("\u2018", "'").replace("\u2019", "'")
#                 .replace("\u00ab", '"').replace("\u00bb", '"'))

#     # --- 1. Extraire et RETIRER un éventuel bloc d'init déjà présent ---
#     existing_init = None
#     init_match = _INIT_BLOCK_PATTERN.match(code)
#     if init_match:
#         existing_init = init_match.group(0).rstrip("\n")
#         code = code[init_match.end():].strip()

#     # --- 2. Vérifier l'en-tête UNIQUEMENT sur le corps (sans le thème) ---
#     lines = [l.strip() for l in code.split("\n") if l.strip()]
#     first_line = lines[0] if lines else ""
#     if not any(first_line.startswith(hdr) for hdr in _VALID_MERMAID_HEADERS):
#         code = f"flowchart TD\n{code}"

#     # --- 3. Corrections de formes/nœuds (inchangé) ---
#     code = re.sub(r'\(\[([^\]]+)\]\)', r'["\1"]', code)
#     code = re.sub(r'\(\(([^)]+)\)\)', r'["\1"]', code)
#     code = re.sub(r'\[\[([^\]]+)\]\]', r'["\1"]', code)
#     code = re.sub(r'\{\{([^}]+)\}\}', r'["\1"]', code)

#     cleaned_lines: List[str] = []
#     in_er_block = False
#     is_er_diagram = "erDiagram" in code

#     for raw_line in code.split("\n"):
#         line_str = raw_line.rstrip()
#         stripped = line_str.strip()

#         if not stripped:
#             cleaned_lines.append(line_str)
#             continue

#         if any(stripped.startswith(hdr) for hdr in _VALID_MERMAID_HEADERS) or \
#            stripped.startswith("subgraph") or stripped == "end":
#             cleaned_lines.append(line_str)
#             continue

#         if is_er_diagram:
#             if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*\{', stripped):
#                 in_er_block = True
#                 cleaned_lines.append(line_str)
#                 continue
#             if stripped == "}" and in_er_block:
#                 in_er_block = False
#                 cleaned_lines.append(line_str)
#                 continue
#             if in_er_block:
#                 match_attr = re.match(r'^\+?\s*(\w+)\s*:\s*(\w+)\s*(PK|FK)?\s*$', stripped)
#                 if match_attr:
#                     field_name, type_name, key_marker = match_attr.groups()
#                     fixed = f"{type_name} {field_name}" + (f" {key_marker}" if key_marker else "")
#                     leading = line_str[:len(line_str) - len(line_str.lstrip())]
#                     cleaned_lines.append(leading + fixed)
#                     continue

#         line_str = re.sub(
#             r'(-->|---|==>|-\.->)\|([^"|\n]+)\|',
#             lambda m: f'{m.group(1)}|"{m.group(2).strip().replace(chr(34), chr(39))}"|',
#             line_str
#         )
#         line_str = _NODE_PATTERN.sub(_quote_node_label, line_str)
#         cleaned_lines.append(line_str)

#     code = "\n".join(cleaned_lines)
#     code = re.sub(r'-->\|([^|]+)\|>', r'-->|\1|', code)
#     code = re.sub(r'\n\s*\n', '\n', code)

#     # --- 4. Réinjection du thème : réutilise celui déjà présent si possible ---
#     theme_block = existing_init if existing_init else MERMAID_THEME_CONFIG_FULL.strip()
#     code = f"{theme_block}\n{code}"

#     return code.strip()


# # ===========================================================================
# # 2. RENDU DES DIAGRAMMES MERMAID EN IMAGES HD
# # ===========================================================================

# def _create_placeholder_image(output_path: str, label: str) -> None:
#     """Crée une image de substitution lisible lorsque le rendu Mermaid échoue."""
#     try:
#         img = PILImage.new("RGB", (1000, 260), color="#EBF8FF")
#         d = ImageDraw.Draw(img)
#         d.rectangle([(0, 0), (999, 259)], outline="#2B6CB0", width=3)
#         d.text((30, 110), f"[ Schema non compile : {label} ]", fill="#1A365D")
#         img.save(output_path)
#     except Exception:
#         with open(output_path, "wb") as f:
#             f.write(b"")


# def render_mermaid_diagrams(
#     markdown_text: str,
#     output_dir: Optional[str] = None
# ) -> Tuple[str, List[str]]:
#     """
#     Détecte les blocs ```mermaid``` du Markdown, les nettoie, les compile en PNG
#     haute définition (via mmdc) avec le thème bleu technique, et remplace chaque
#     bloc par une référence d'image Markdown standard.
#     Retourne (markdown_mis_a_jour, liste_des_chemins_images).
#     """
#     if not output_dir:
#         output_dir = tempfile.mkdtemp(prefix="mermaid_images_")
#     os.makedirs(output_dir, exist_ok=True)

#     diagram_pattern = re.compile(r"```mermaid[ \t]*\r?\n(.*?)\r?\n```", re.DOTALL | re.IGNORECASE)
#     matches = list(diagram_pattern.finditer(markdown_text))

#     rendered_image_paths: List[str] = []
#     updated_markdown = markdown_text
#     mmdc_bin = shutil.which("mmdc") or shutil.which("mmdc.cmd") or "mmdc"

#     for idx, match in enumerate(matches):
#         mermaid_code = clean_mermaid_code(match.group(1))

#         img_path = os.path.join(output_dir, f"diagram_{idx + 1}.png")
#         mmd_file = os.path.join(output_dir, f"diag_{idx + 1}.mmd")
#         with open(mmd_file, "w", encoding="utf-8") as f:
#             f.write(mermaid_code)

#         success = False
#         try:
#             # NB : on ne passe volontairement PAS de flag "-t" (theme) car le thème
#             # est déjà injecté dans le fichier .mmd via %%{init: ...}%% ; le combiner
#             # avec "-t dark" (bug de l'ancienne version) écrasait le thème bleu voulu.
#             cmd = [mmdc_bin, "-i", mmd_file, "-o", img_path, "-b", "white", "-w", "1920", "-s", "3"]
#             res = subprocess.run(
#                 cmd, capture_output=True, text=True, timeout=60, shell=(os.name == "nt")
#             )
#             if res.returncode == 0 and os.path.exists(img_path) and os.path.getsize(img_path) > 0:
#                 success = True
#                 print(f"[LAYOUT] Diagramme #{idx + 1} rendu en HD (thème bleu technique).")
#             else:
#                 print(f"[LAYOUT][WARN] Echec mmdc diagramme #{idx + 1} : {res.stderr}")
#         except Exception as e:
#             print(f"[LAYOUT][ERROR] Erreur d'execution mmdc : {e}")

#         if not success:
#             _create_placeholder_image(img_path, f"Diagramme #{idx + 1}")

#         rendered_image_paths.append(img_path)
#         updated_markdown = updated_markdown.replace(match.group(0), f"\n![Diagramme #{idx + 1}]({img_path})\n")

#     return updated_markdown, rendered_image_paths


# # ===========================================================================
# # 3. AIDES DE RENDU MARKDOWN -> REPORTLAB
# # ===========================================================================

# def _escape_xml(text: str) -> str:
#     return text.replace("&", "&").replace("<", "<").replace(">", ">")


# def _inline_markdown_to_reportlab(text: str) -> str:
#     """
#     Convertit la syntaxe Markdown inline (gras, italique, code, liens) en
#     balisage compatible ReportLab, en échappant correctement le XML au préalable.
#     """
#     text = _escape_xml(text)

#     # Liens [texte](url)
#     text = re.sub(
#         r"\[([^\]]+)\]\((https?://[^\s\)]+)\)",
#         r'<link href="\2" color="#2B6CB0"><u>\1</u></link>',
#         text
#     )
#     # Code inline `code`
#     text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="9.5" color="#1A365D">\1</font>', text)
#     # Gras **texte** ou __texte__
#     text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
#     text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
#     # Italique *texte* ou _texte_ (après le gras pour éviter les conflits)
#     text = re.sub(r"(?<!\*)\*(?!\*)([^\*]+?)\*(?!\*)", r"<i>\1</i>", text)
#     text = re.sub(r"(?<!_)_(?!_)([^_]+?)_(?!_)", r"<i>\1</i>", text)
#     return text


# def _is_table_separator(line: str) -> bool:
#     stripped = line.strip()
#     if "|" not in stripped:
#         return False
#     return bool(re.fullmatch(r"[\s\|:\-]+", stripped)) and "-" in stripped


# def _split_table_row(line: str) -> List[str]:
#     cells = line.strip()
#     if cells.startswith("|"):
#         cells = cells[1:]
#     if cells.endswith("|"):
#         cells = cells[:-1]
#     return [c.strip() for c in cells.split("|")]


# def _fit_image_dimensions(img_path: str, max_width: float, max_height: float) -> Tuple[float, float, bool]:
#     """
#     Calcule les dimensions d'une image en préservant son ratio d'aspect,
#     pour qu'elle tienne dans (max_width, max_height). Retourne aussi un
#     booléen "compressed_beyond_width_fit" indiquant si la stratégie
#     'fit_to_width' n'a pas suffi (image encore trop haute) -> signal
#     utile pour le rapport de débordement visuel.
#     """
#     try:
#         with PILImage.open(img_path) as im:
#             img_w, img_h = im.size
#     except Exception:
#         return max_width, max_height * 0.6, False

#     if img_w <= 0 or img_h <= 0:
#         return max_width, max_height * 0.6, False

#     # Stratégie "fit_to_width" : on cale d'abord sur la largeur
#     scale_w = max_width / img_w
#     fit_w, fit_h = img_w * scale_w, img_h * scale_w

#     overflow = False
#     if fit_h > max_height:
#         # La largeur seule ne suffit pas : on recale aussi sur la hauteur
#         scale_h = max_height / img_h
#         fit_w, fit_h = img_w * scale_h, img_h * scale_h
#         overflow = True

#     return fit_w, fit_h, overflow


# # ===========================================================================
# # 4. CANVAS AVEC NUMÉROTATION "Page X sur Y" + EN-TÊTE / PIED DE PAGE
# # ===========================================================================

# def _make_numbered_canvas(theme: Dict[str, Any], layout_spec: Dict[str, Any]):
#     """Fabrique une classe Canvas liée au thème courant (recette standard ReportLab)."""

#     hf_config = layout_spec.get("header_footer_config", {}) or {}
#     header_text = hf_config.get("header_text", "")
#     footer_left = hf_config.get("footer_left", "")

#     class NumberedCanvas(pdf_canvas.Canvas):
#         def __init__(self, *args, **kwargs):
#             pdf_canvas.Canvas.__init__(self, *args, **kwargs)
#             self._saved_page_states = []

#         def showPage(self):
#             self._saved_page_states.append(dict(self.__dict__))
#             self._startPage()

#         def save(self):
#             total_pages = len(self._saved_page_states)
#             for state in self._saved_page_states:
#                 self.__dict__.update(state)
#                 self._draw_decorations(total_pages)
#                 pdf_canvas.Canvas.showPage(self)
#             pdf_canvas.Canvas.save(self)

#         def _draw_decorations(self, total_pages: int):
#             self.saveState()
#             page_num = self._pageNumber

#             # En-tête (à partir de la 2e page, après la couverture)
#             if page_num > 1 and header_text:
#                 self.setFont("Helvetica-Bold", 8)
#                 self.setFillColor(theme["primary"])
#                 self.drawString(theme["margin_left"], A4[1] - theme["margin_top"] + 10, header_text)
#                 self.setStrokeColor(theme["secondary"])
#                 self.setLineWidth(0.5)
#                 self.line(
#                     theme["margin_left"], A4[1] - theme["margin_top"],
#                     A4[0] - theme["margin_right"], A4[1] - theme["margin_top"]
#                 )

#             # Pied de page : numérotation
#             self.setFont("Helvetica", 8)
#             self.setFillColor(theme["text"])
#             self.drawRightString(
#                 A4[0] - theme["margin_right"], 25,
#                 f"Page {page_num} sur {total_pages}"
#             )
#             if footer_left:
#                 self.drawString(theme["margin_left"], 25, footer_left)

#             self.setStrokeColor(theme["border"])
#             self.setLineWidth(0.5)
#             self.line(theme["margin_left"], 35, A4[0] - theme["margin_right"], 35)
#             self.restoreState()

#     return NumberedCanvas


# # ===========================================================================
# # 5. DOCTEMPLATE AVEC SIGNETS PDF + ENTRÉES DE TABLE DES MATIÈRES CLIQUABLES
# # ===========================================================================
# class _BookmarkedDocTemplate(BaseDocTemplate):
#     """
#     DocTemplate qui, à chaque titre (H1/H2/H3) rencontré pendant la construction :
#       1. pose un signet PDF (panneau de navigation, comme les \\section de LaTeX) ;
#       2. notifie la TableOfContents avec une clé de lien -> entrées cliquables.
#     Construit en deux passes (multiBuild) pour connaître les vrais numéros de page.

#     IMPORTANT : le pied de page "Page X sur Y" est dessiné directement dans
#     afterPage() (flux normal de pagination de ReportLab), et non plus via un
#     Canvas personnalisé qui différait showPage(). Cette dernière approche
#     empêchait le compteur de pages interne du document PDF d'avancer avant
#     save(), ce qui faisait pointer TOUS les signets/liens internes
#     (bookmarkPage) vers la même page non finalisée (= toujours la couverture).
#     """

#     HEADING_LEVELS = {"DocH1": 0, "DocH2": 1, "DocH3": 2}
#     def __init__(self, *args, theme: Dict[str, Any], layout_spec: Dict[str, Any], **kwargs):
#         BaseDocTemplate.__init__(self, *args, **kwargs)
#         self._bookmark_counter = 0
#         self._theme = theme
#         self._layout_spec = layout_spec
#         self._known_total_pages = None
#         # Texte de chaque titre détecté, dans l'ordre : alimente "toc_entries"
#         # attendu par calculate_scs() dans app/core/metrics.py.
#         self._toc_entries_text: List[str] = []
#         # Stocke les infos pour créer les liens cliquables dans la TOC : (level, text, page, key)
#         self._toc_entries_for_links: List[Tuple[int, str, int, str]] = []

#     def build(self, flowables, **kwargs):
#         self._bookmark_counter = 0
#         self._toc_entries_text = []
#         self._toc_entries_for_links = []
#         BaseDocTemplate.build(self, flowables, **kwargs)
#         self._known_total_pages = self.page

#     def afterFlowable(self, flowable):
#         if not isinstance(flowable, Paragraph):
#             return
#         style_name = getattr(flowable.style, "name", "")
#         if style_name not in self.HEADING_LEVELS:
#             return

#         level = self.HEADING_LEVELS[style_name]
#         text = flowable.getPlainText()
#         if not text.strip():
#             return

#         self._bookmark_counter += 1
#         key = f"toc-anchor-{self._bookmark_counter}"

#         self.canv.bookmarkPage(key)
#         self.canv.addOutlineEntry(text, key, level=level, closed=False)
#         self.notify("TOCEntry", (level, text, self.page, key))
#         self._toc_entries_text.append(text)
#         self._toc_entries_for_links.append((level, text, self.page, key))


#     def afterPage(self):
#         """
#         Dessine l'en-tête et le pied de page dans le flux normal de
#         pagination de ReportLab (appelé après chaque page réellement
#         finalisée) — contrairement à l'ancienne approche NumberedCanvas
#         qui cassait bookmarkPage().
#         """
#         theme = self._theme
#         hf_config = (self._layout_spec.get("header_footer_config", {}) or {})
#         header_text = hf_config.get("header_text", "")
#         footer_left = hf_config.get("footer_left", "")

#         page_num = self.page
#         total_pages = self._known_total_pages or page_num

#         canv = self.canv
#         canv.saveState()

#         if page_num > 1 and header_text:
#             canv.setFont("Helvetica-Bold", 8)
#             canv.setFillColor(theme["primary"])
#             canv.drawString(theme["margin_left"], A4[1] - theme["margin_top"] + 10, header_text)
#             canv.setStrokeColor(theme["secondary"])
#             canv.setLineWidth(0.5)
#             canv.line(
#                 theme["margin_left"], A4[1] - theme["margin_top"],
#                 A4[0] - theme["margin_right"], A4[1] - theme["margin_top"]
#             )

#         canv.setFont("Helvetica", 8)
#         canv.setFillColor(theme["text"])
#         canv.drawRightString(
#             A4[0] - theme["margin_right"], 25,
#             f"Page {page_num} sur {total_pages}"
#         )
#         if footer_left:
#             canv.drawString(theme["margin_left"], 25, footer_left)

#         canv.setStrokeColor(theme["border"])
#         canv.setLineWidth(0.5)
#         canv.line(theme["margin_left"], 35, A4[0] - theme["margin_right"], 35)

#         canv.restoreState()


# # ===========================================================================
# # 6. COMPILATION MARKDOWN -> PDF
# # ===========================================================================

# def compile_markdown_to_pdf(
#     markdown_text: str,
#     output_pdf_path: str,
#     layout_spec: Dict[str, Any]
# ) -> Dict[str, Any]:
#     """
#     Compile le Markdown enrichi (doc.md + images de diagrammes déjà rendues)
#     en un PDF avec :
#       - une page de garde et une table des matières RÉELLEMENT cliquable
#         (clic -> saut à la section, comme \tableofcontents en LaTeX) ;
#       - un panneau de signets PDF (navigation latérale) ;
#       - un thème bleu technique piloté par layout_spec.json ;
#       - des tableaux, du code, des citations et des images correctement mis à
#         l'échelle (sans déformation).
#     """
#     theme = _build_theme(layout_spec)
#     doc_meta = layout_spec.get("document_metadata", {}) or {}
#     project_title = doc_meta.get("title", "Documentation Technique")
#     project_subtitle = doc_meta.get(
#         "subtitle", "Documentation Technique & Architecture du Pipeline"
#     )

#     os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)

#     # --- Styles ---
#     styles = getSampleStyleSheet()
#     typo = theme["typo"]

#     title_style = ParagraphStyle(
#         "CoverTitle", fontName=theme["font_heading"], fontSize=28, leading=34,
#         textColor=theme["primary"], alignment=TA_CENTER, spaceAfter=8
#     )
#     subtitle_style = ParagraphStyle(
#         "CoverSub", fontName=theme["font_body"], fontSize=13, leading=16,
#         textColor=theme["text"], alignment=TA_CENTER, spaceAfter=24
#     )
#     h1_style = ParagraphStyle(
#         "DocH1", parent=styles["Normal"], fontName=theme["font_heading"],
#         fontSize=typo["h1"]["font_size"], leading=typo["h1"]["leading"],
#         textColor=theme["primary"], spaceBefore=18, spaceAfter=typo["h1"]["space_after"],
#         keepWithNext=True
#     )
#     h2_style = ParagraphStyle(
#         "DocH2", parent=styles["Normal"], fontName=theme["font_heading"],
#         fontSize=typo["h2"]["font_size"], leading=typo["h2"]["leading"],
#         textColor=theme["secondary"], spaceBefore=16, spaceAfter=typo["h2"]["space_after"],
#         keepWithNext=True
#     )
#     h3_style = ParagraphStyle(
#         "DocH3", parent=styles["Normal"], fontName=theme["font_heading"],
#         fontSize=typo["h3"]["font_size"], leading=typo["h3"]["leading"],
#         textColor=theme["secondary"], spaceBefore=12, spaceAfter=typo["h3"]["space_after"],
#         keepWithNext=True
#     )
#     body_style = ParagraphStyle(
#         "DocBody", parent=styles["Normal"], fontName=theme["font_body"],
#         fontSize=typo["body"]["font_size"], leading=typo["body"]["leading"],
#         textColor=theme["text"], spaceAfter=typo["body"]["space_after"]
#     )
#     bullet_style = ParagraphStyle(
#         "DocBullet", parent=body_style, leftIndent=18, bulletIndent=6, spaceAfter=4
#     )
#     quote_style = ParagraphStyle(
#         "DocQuote", parent=body_style, leftIndent=24, textColor=theme["secondary"],
#         borderColor=theme["border"], italic=True
#     )
#     code_style = ParagraphStyle(
#         "DocCode", parent=styles["Normal"], fontName="Courier",
#         fontSize=typo["code"]["font_size"], leading=typo["code"]["leading"],
#         textColor=theme["primary"]
#     )
#     tbl_hdr_style = ParagraphStyle(
#         "TblHdr", parent=styles["Normal"], fontName="Helvetica-Bold",
#         fontSize=typo["table_cell"]["font_size"], leading=typo["table_cell"]["leading"],
#         textColor=colors.white
#     )
#     tbl_cell_style = ParagraphStyle(
#         "TblCell", parent=styles["Normal"], fontName="Helvetica",
#         fontSize=typo["table_cell"]["font_size"], leading=typo["table_cell"]["leading"],
#         textColor=theme["text"]
#     )

#     toc_level_styles = [
#         ParagraphStyle("TOC0", parent=body_style, fontName="Helvetica-Bold",
#                         fontSize=11.5, leftIndent=0, spaceAfter=6, textColor=theme["primary"]),
#         ParagraphStyle("TOC1", parent=body_style, fontSize=11, leftIndent=16,
#                         spaceAfter=4, textColor=theme["text"]),
#         ParagraphStyle("TOC2", parent=body_style, fontSize=10, leftIndent=32,
#                         spaceAfter=3, textColor=theme["text"]),
#     ]

#     # --- Story : couverture + TOC + contenu ---
#     story: List[Any] = []
#     story.append(Spacer(1, 120))
#     story.append(Paragraph(_escape_xml(project_title.upper()), title_style))
#     story.append(Paragraph(_escape_xml(project_subtitle), subtitle_style))
#     story.append(HRFlowable(width="60%", thickness=1, color=theme["secondary"], hAlign="CENTER"))
#     story.append(PageBreak())

#     story.append(Paragraph("Table des Matières", ParagraphStyle(
#         "TOCTitle", fontName=theme["font_heading"], fontSize=16, leading=20,
#         textColor=theme["primary"], spaceAfter=16
#     )))
#     toc = TableOfContents()
#     toc.levelStyles = toc_level_styles
#     toc.dotsMinLevel = 0
#     story.append(toc)
#     story.append(PageBreak())

#     diagrams_overflow: List[str] = []
#     diagrams_rendered = 0

#     lines = markdown_text.splitlines()
#     i, n = 0, len(lines)
#     in_code_block = False
#     code_buffer: List[str] = []

#     def flush_code_block():
#         if not code_buffer:
#             return
#         code_text = "<br/>".join(_escape_xml(l).replace(" ", "&nbsp;") for l in code_buffer)
#         tbl = Table([[Paragraph(code_text, code_style)]], colWidths=[theme["max_width_pt"]])
#         tbl.setStyle(TableStyle([
#             ("BACKGROUND", (0, 0), (-1, -1), theme["bg_light"]),
#             ("BOX", (0, 0), (-1, -1), 0.6, theme["secondary"]),
#             ("LEFTPADDING", (0, 0), (-1, -1), 8),
#             ("RIGHTPADDING", (0, 0), (-1, -1), 8),
#             ("TOPPADDING", (0, 0), (-1, -1), 6),
#             ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
#         ]))
#         story.append(Spacer(1, 4))
#         story.append(tbl)
#         story.append(Spacer(1, 6))
#         code_buffer.clear()

#     while i < n:
#         line = lines[i]
#         stripped = line.strip()

#         # --- Blocs de code ```
#         if stripped.startswith("```"):
#             if in_code_block:
#                 flush_code_block()
#                 in_code_block = False
#             else:
#                 in_code_block = True
#             i += 1
#             continue
#         if in_code_block:
#             code_buffer.append(line)
#             i += 1
#             continue

#         # --- Tableaux Markdown : ligne | a | b | suivie d'une ligne séparatrice
#         if "|" in stripped and stripped.startswith("|") and i + 1 < n and _is_table_separator(lines[i + 1]):
#             header_cells = _split_table_row(stripped)
#             table_rows = [[Paragraph(_inline_markdown_to_reportlab(c), tbl_hdr_style) for c in header_cells]]
#             j = i + 2
#             while j < n and lines[j].strip().startswith("|"):
#                 row_cells = _split_table_row(lines[j])
#                 # Complète/tronque pour matcher le nombre de colonnes de l'en-tête
#                 row_cells = (row_cells + [""] * len(header_cells))[:len(header_cells)]
#                 table_rows.append([Paragraph(_inline_markdown_to_reportlab(c), tbl_cell_style) for c in row_cells])
#                 j += 1
#             col_width = theme["max_width_pt"] / max(len(header_cells), 1)
#             tbl = Table(table_rows, colWidths=[col_width] * len(header_cells), repeatRows=1)
#             tbl.setStyle(TableStyle([
#                 ("BACKGROUND", (0, 0), (-1, 0), theme["primary"]),
#                 ("GRID", (0, 0), (-1, -1), 0.5, theme["border"]),
#                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, theme["bg_light"]]),
#                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
#                 ("LEFTPADDING", (0, 0), (-1, -1), 6),
#                 ("RIGHTPADDING", (0, 0), (-1, -1), 6),
#                 ("TOPPADDING", (0, 0), (-1, -1), 5),
#                 ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
#             ]))
#             story.append(Spacer(1, 6))
#             story.append(tbl)
#             story.append(Spacer(1, 8))
#             i = j
#             continue

#         # --- Images (diagrammes rendus par render_mermaid_diagrams)
#         img_match = re.search(r"!\[.*?\]\((.*?)\)", line)
#         if img_match:
#             img_path = img_match.group(1)
#             if os.path.exists(img_path):
#                 diagrams_rendered += 1
#                 fit_w, fit_h, overflowed = _fit_image_dimensions(
#                     img_path, theme["max_width_pt"], theme["max_height_pt"]
#                 )
#                 if overflowed:
#                     diagrams_overflow.append(os.path.basename(img_path))
#                 story.append(Spacer(1, 8))
#                 story.append(RLImage(img_path, width=fit_w, height=fit_h, hAlign="CENTER"))
#                 story.append(Spacer(1, 8))
#             i += 1
#             continue

#         # --- Titres
#         if stripped.startswith("#### "):
#             story.append(Paragraph(_inline_markdown_to_reportlab(stripped[5:].strip()), h3_style))
#         elif stripped.startswith("### "):
#             story.append(KeepTogether(Paragraph(_inline_markdown_to_reportlab(stripped[4:].strip()), h3_style)))
#         elif stripped.startswith("## "):
#             story.append(KeepTogether(Paragraph(_inline_markdown_to_reportlab(stripped[3:].strip()), h2_style)))
#         elif stripped.startswith("# "):
#             story.append(KeepTogether(Paragraph(_inline_markdown_to_reportlab(stripped[2:].strip()), h1_style)))

#         # --- Citations
#         elif stripped.startswith("> "):
#             story.append(Paragraph(_inline_markdown_to_reportlab(stripped[2:].strip()), quote_style))

#         # --- Séparateur horizontal
#         elif re.fullmatch(r"-{3,}", stripped) or re.fullmatch(r"\*{3,}", stripped):
#             story.append(HRFlowable(width="100%", thickness=0.6, color=theme["border"], spaceBefore=6, spaceAfter=6))

#         # --- Listes à puces / numérotées
#         elif stripped.startswith(("- ", "* ")):
#             item = _inline_markdown_to_reportlab(stripped[2:].strip())
#             story.append(Paragraph(f"&bull;&nbsp;&nbsp;{item}", bullet_style))
#         elif re.match(r"^\d+\.\s", stripped):
#             item = _inline_markdown_to_reportlab(re.sub(r"^\d+\.\s", "", stripped))
#             num = re.match(r"^(\d+)\.", stripped).group(1)
#             story.append(Paragraph(f"{num}.&nbsp;&nbsp;{item}", bullet_style))

#         # --- Paragraphe normal / ligne vide
#         elif stripped:
#             story.append(Paragraph(_inline_markdown_to_reportlab(stripped), body_style))
#         else:
#             story.append(Spacer(1, 4))

#         i += 1

#     if in_code_block:
#         flush_code_block()

#     # --- Construction du document (deux passes pour la TOC + signets) ---
#     doc = _BookmarkedDocTemplate(
#         output_pdf_path,
#         pagesize=theme["page_size"],
#         leftMargin=theme["margin_left"], rightMargin=theme["margin_right"],
#         topMargin=theme["margin_top"], bottomMargin=theme["margin_bottom"],
#         title=project_title, author=doc_meta.get("author", "Spec Kit Pipeline"),
#         theme=theme, layout_spec=layout_spec
#     )
#     frame = Frame(
#         theme["margin_left"], theme["margin_bottom"],
#         theme["page_size"][0] - theme["margin_left"] - theme["margin_right"],
#         theme["page_size"][1] - theme["margin_top"] - theme["margin_bottom"],
#         id="main_frame"
#     )
#     doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

#     doc.multiBuild(story)

#     # --- Post-traitement : rendre les entrées de la TOC cliquables (liens internes) ---
#     # On utilise PyMuPDF pour ajouter des annotations de lien sur la page de la TOC (page 2)
#     _make_toc_entries_clickable(output_pdf_path, getattr(doc, "_toc_entries_for_links", []))

#     bookmarks_created = getattr(doc, "_bookmark_counter", 0) > 0
#     primary_hex = (layout_spec.get("branding_theme", {}) or {}).get("primary_color") or "#1A365D"

#     return {
#         "output_pdf_path": output_pdf_path,
#         "has_clickable_toc": bookmarks_created,
#         "has_pdf_bookmarks": bookmarks_created,
#         "diagrams_rendered_in_pdf": diagrams_rendered,
#         "diagrams_overflowing": diagrams_overflow,
#         "toc_entries": getattr(doc, "_toc_entries_text", []),
#         "applied_primary_color": primary_hex,
#         "has_page_numbers": True,
#     }


# def _make_toc_entries_clickable(pdf_path: str, toc_entries: List[Tuple[int, str, int, str]]) -> None:
#     """
#     Post-traite le PDF pour rendre les entrées de la Table des Matières cliquables.
#     Ajoute des annotations de lien (Link Annotations) sur le texte de la TOC
#     qui pointent vers les signets (bookmarks) correspondants.
#     """
#     if not toc_entries:
#         return
#     try:
#         import fitz  # PyMuPDF
#     except ImportError:
#         return

#     try:
#         doc = fitz.open(pdf_path)
#         if len(doc) < 2:
#             doc.close()
#             return

#         # La TOC est sur la page 2 (index 1) : page 1 = couverture, page 2 = TOC
#         toc_page = doc[1]
        
#         # Recherche le texte de chaque entrée de TOC dans la page et ajoute un lien
#         for level, text, target_page, key in toc_entries:
#             # Nettoie le texte pour la recherche (supprime numéros, espaces en trop)
#             search_text = text.strip()
#             if not search_text:
#                 continue
            
#             # Recherche toutes les occurrences du texte sur la page TOC
#             text_instances = toc_page.search_for(search_text, quads=False)
#             for inst in text_instances:
#                 # Étend légèrement le rectangle pour couvrir toute la ligne (numéros de page inclus)
#                 # inst est un fitz.Rect (x0, y0, x1, y1)
#                 link_rect = fitz.Rect(inst.x0 - 5, inst.y0 - 1, inst.x1 + 50, inst.y1 + 1)
                
#                 # Ajoute l'annotation de lien interne (pointe vers le bookmark nommé)
#                 toc_page.insert_link({
#                     "kind": fitz.LINK_NAMED,
#                     "named": key,  # Le nom du bookmark (ex: "toc-anchor-1")
#                     "from": link_rect,
#                 })
        
#         doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
#         doc.close()
#     except Exception:
#         # En cas d'erreur, on laisse le PDF sans liens cliquables dans la TOC
#         # Les signets du panneau de navigation fonctionnent quand même
#         pass


# # ===========================================================================
# # 7. INSPECTION DU PDF GÉNÉRÉ (métadonnées + rapport de débordement visuel)
# # ===========================================================================

# def _count_pages_fallback(pdf_path: str) -> int:
#     """Compte les pages sans dépendance externe si PyMuPDF n'est pas disponible."""
#     try:
#         with open(pdf_path, "rb") as f:
#             data = f.read()
#         count = len(re.findall(rb"/Type\s*/Page[^s]", data))
#         return count if count > 0 else 1
#     except Exception:
#         return 0


# def inspect_generated_pdf(
#     pdf_path: str,
#     compilation_result: Dict[str, Any],
#     rendered_diagrams_count: int
# ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
#     """
#     Inspecte le PDF produit pour en extraire les métriques nécessaires à
#     l'arbitrage de publication (LayoutEvaluatorService).
#     Retourne (rendered_pdf_metadata, layout_overflow_report).
#     """
#     pdf_generated = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0
#     page_count = 0
#     file_size_bytes = os.path.getsize(pdf_path) if pdf_generated else 0

#     if pdf_generated:
#         try:
#             import fitz  # PyMuPDF, optionnel selon l'environnement d'exécution
#             with fitz.open(pdf_path) as doc:
#                 page_count = doc.page_count
#         except ImportError:
#             page_count = _count_pages_fallback(pdf_path)
#         except Exception:
#             page_count = _count_pages_fallback(pdf_path)

#     diagrams_rendered_in_pdf = compilation_result.get("diagrams_rendered_in_pdf", 0)

#     # ⚠️ CORRECTIF : file_size_bytes / rendered_diagrams_count / toc_entries /
#     # applied_primary_color / has_page_numbers manquaient entièrement, alors
#     # que app/core/metrics.py (calculate_rsr, calculate_dvr, calculate_scs)
#     # les lit sous ces noms précis. Résultat : RSR=0 systématique,
#     # DVR=0 dès qu'un diagramme existe, SCS proche de 0 — indépendamment de
#     # la qualité réelle du PDF produit. On conserve les anciennes clés
#     # (diagrams_rendered_in_pdf, overflow_diagrams_count) pour ne rien casser
#     # ailleurs, et on ajoute celles réellement attendues par metrics.py.
#     rendered_pdf_metadata = {
#         "pdf_generated": pdf_generated,
#         "page_count": page_count,
#         "file_size_bytes": file_size_bytes,
#         "has_clickable_toc": compilation_result.get("has_clickable_toc", False),
#         "has_pdf_bookmarks": compilation_result.get("has_pdf_bookmarks", False),
#         "diagrams_rendered_in_pdf": diagrams_rendered_in_pdf,
#         "rendered_diagrams_count": diagrams_rendered_in_pdf,
#         "toc_entries": compilation_result.get("toc_entries", []),
#         "applied_primary_color": compilation_result.get("applied_primary_color"),
#         "has_page_numbers": compilation_result.get("has_page_numbers", False),
#     }

#     diagrams_overflow = compilation_result.get("diagrams_overflowing", [])
#     overflow_count = len(diagrams_overflow)
#     overflow_rate = (overflow_count / rendered_diagrams_count * 100.0) if rendered_diagrams_count else 0.0

#     layout_overflow_report = {
#         "overflow_diagrams_count": overflow_count,
#         "overflow_events_count": overflow_count,
#         "total_rendered_blocks": max(rendered_diagrams_count, 1),
#         "overflow_diagram_files": diagrams_overflow,
#         "visual_overflow_rate": round(overflow_rate, 2),
#         "render_success_rate": round(
#             (diagrams_rendered_in_pdf / rendered_diagrams_count * 100.0)
#             if rendered_diagrams_count else 100.0, 2
#         ),
#     }

#     return rendered_pdf_metadata, layout_overflow_report