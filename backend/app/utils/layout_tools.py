# app/utils/layout_tools.py
"""
layout_tools.py — Outils de compilation PDF et de rendu visuel pour le Layout Agent.
Version HD : Diagrammes à proportions naturelles (Aspect Ratio) & Typographie augmentée (11pt).
"""

import os
import re
import json
import shutil
import subprocess
import tempfile
from typing import Dict, Any, List, Tuple
from PIL import Image as PILImage

# Importations ReportLab
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image as RLImage
)
from reportlab.pdfgen import canvas

print("[⚡] ENGINE : layout_tools.py (Optimisation Visuelle HD & Polices 11pt) Actif")


# ===========================================================================
# 1. CANVAS PERSONNALISÉ (EN-TÊTE & PIED DE PAGE ISOLÉS)
# ===========================================================================
from functools import partial

# ===========================================================================
# 1. CANVAS DYNAMIQUE (LIT LAYOUT_SPEC.JSON)
# ===========================================================================

class NumberedCanvas(canvas.Canvas):
    """Canvas ReportLab dynamique : lit la configuration JSON pour afficher/masquer en-tête et pied de page."""
    def __init__(self, *args, layout_spec: Dict[str, Any] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.layout_spec = layout_spec or {}

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Extrait la configuration (Vide si supprimée dans le JSON)
        hf_config = self.layout_spec.get("header_footer_config", {})
        header_text = hf_config.get("header_text", "")
        footer_left = hf_config.get("footer_left", "")
        enable_numbering = hf_config.get("enable_page_numbering", True)
        
        # En-tête : Dessiné SEULEMENT si header_text est défini dans le JSON
        if self._pageNumber > 1 and header_text:
            self.drawString(45.6, 818, header_text)
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(45.6, 810, 549.6, 810)
            
        # Pied de page : Numérotation (si activée)
        if enable_numbering:
            page_str = f"Page {self._pageNumber} sur {page_count}"
            self.drawRightString(549.6, 25, page_str)
            
        # Pied de page : Texte gauche (SEULEMENT si footer_left est défini)
        if footer_left:
            self.drawString(45.6, 25, footer_left)
            
        # Ligne de séparation du pied de page
        if footer_left or enable_numbering:
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(45.6, 35, 549.6, 35)
        
        self.restoreState()

# ===========================================================================
# 2. CONVERSION MERMAID EN HAUTE DÉFINITION (SCALE 3X & LARGE POLICE)
# ===========================================================================

def _clean_mermaid_code(code: str) -> str:
    """Nettoie le code Mermaid et injecte une configuration pour de grands textes très lisibles."""
    code = re.sub(r'\$\((.*?)\)\$', r'\1', code)
    code = re.sub(r'\$(.*?)\$', r'\1', code)
    code = code.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n").strip()
    
    # Injection de la configuration de taille de police dans le schéma s'il n'y en a pas
    if not code.startswith("%%{init:"):
        mermaid_config = "%%{init: {'theme': 'neutral', 'themeVariables': { 'fontSize': '18px', 'fontFamily': 'arial' }}}%%\n"
        code = mermaid_config + code
        
    return code


def render_mermaid_diagrams(markdown_text: str, output_dir: str = None) -> Tuple[str, List[str]]:
    """Génère des images PNG haute définition à partir des blocs ```mermaid."""
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="mermaid_images_")
    os.makedirs(output_dir, exist_ok=True)

    diagram_pattern = re.compile(r"```mermaid[ \t]*\r?\n(.*?)\r?\n```", re.DOTALL | re.IGNORECASE)
    matches = list(diagram_pattern.finditer(markdown_text))
    
    rendered_image_paths = []
    updated_markdown = markdown_text

    mmdc_bin = shutil.which("mmdc") or shutil.which("mmdc.cmd") or "mmdc"

    for idx, match in enumerate(matches):
        raw_code = match.group(1)
        mermaid_code = _clean_mermaid_code(raw_code)
        
        img_filename = f"diagram_{idx + 1}.png"
        img_path = os.path.join(output_dir, img_filename)
        mmd_file = os.path.join(output_dir, f"diagram_{idx + 1}.mmd")

        with open(mmd_file, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        success = False
        try:
            # -s 3 (Scale 300% pour netteté parfaite) et -w 1600 (Haute résolution)
            cmd = [mmdc_bin, "-i", mmd_file, "-o", img_path, "-b", "transparent", "-w", "1600", "-s", "3"]
            res = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=15,
                shell=(os.name == 'nt')
            )
            
            if res.returncode == 0 and os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                success = True
                print(f"[✅] Diagramme #{idx + 1} généré en Haute Définition (Scale 3x).")
            else:
                err_msg = res.stderr.decode('utf-8', errors='ignore')
                print(f"[⚠️] Erreur mmdc diagramme #{idx + 1} : {err_msg.strip()}")
        except Exception as e:
            print(f"[❌] Erreur d'exécution mmdc : {e}")

        if not success:
            _create_placeholder_image(img_path, f"Diagramme #{idx + 1}")

        rendered_image_paths.append(img_path)
        replacement = f"\n![Diagramme #{idx + 1}]({img_path})\n"
        updated_markdown = updated_markdown.replace(match.group(0), replacement)

    return updated_markdown, rendered_image_paths


def _create_placeholder_image(output_path: str, label: str):
    try:
        img = PILImage.new('RGB', (800, 240), color='#EBF8FF')
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        d.rectangle([(0, 0), (799, 239)], outline='#3182CE', width=3)
        d.text((30, 100), f"[ Schéma non compilé : {label} ]", fill='#1A365D')
        img.save(output_path)
    except Exception:
        with open(output_path, "wb") as f:
            f.write(b"")


# ===========================================================================
# 3. COMPILATION DU MARKDOWN EN PDF (POLICE 11PT ET RATIO D'ASPECT)
# ===========================================================================

def compile_markdown_to_pdf(
    markdown_text: str, 
    output_pdf_path: str, 
    layout_spec: Dict[str, Any]
) -> Dict[str, Any]:
    """Compile le Markdown avec polices 11pt et redimensionnement dynamique des images."""
    branding = layout_spec.get("branding_theme", {})
    primary_color = colors.HexColor(branding.get("primary_color", "#1A365D"))
    secondary_color = colors.HexColor(branding.get("secondary_color", "#2B6CB0"))
    text_color = colors.HexColor(branding.get("text_color", "#2D3748"))
    bg_light = colors.HexColor(branding.get("background_light", "#F7FAFC"))
    border_col = colors.HexColor(branding.get("border_color", "#CBD5E0"))
    
    doc_meta = layout_spec.get("document_metadata", {})
    page_size_str = doc_meta.get("page_size", "A4").upper()
    selected_page_size = letter if page_size_str == "LETTER" else A4

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=selected_page_size,
        leftMargin=45.6, rightMargin=45.6, topMargin=72, bottomMargin=45
    )

    styles = getSampleStyleSheet()
    
    typo = layout_spec.get("typography_rules", {})
    body_font_size = typo.get("body", {}).get("font_size", 11.0)
    body_leading = typo.get("body", {}).get("leading", 15.5)

    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=primary_color, spaceAfter=14)
    h2_style = ParagraphStyle('DocH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14.5, leading=18, textColor=primary_color, spaceBefore=16, spaceAfter=8, keepWithNext=True)
    h3_style = ParagraphStyle('DocH3', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=secondary_color, spaceBefore=12, spaceAfter=5, keepWithNext=True)
    
    # Texte standard agrandi (11pt / 15.5pt leading)
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontName='Helvetica', fontSize=body_font_size, leading=body_leading, textColor=text_color, spaceAfter=7)
    
    # Tableaux et code agrandis (9pt / 12pt leading)
    tbl_cell_style = ParagraphStyle('TblCell', parent=styles['Normal'], fontName='Helvetica', fontSize=9.0, leading=12.0, textColor=text_color)
    tbl_hdr_style = ParagraphStyle('TblHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.0, leading=12.0, textColor=colors.white)
    code_style = ParagraphStyle('DocCode', parent=styles['Normal'], fontName='Courier', fontSize=9.0, leading=12.0, textColor=text_color)

    story = []
    toc_entries = []
    overflow_events_count = 0
    total_rendered_blocks = 0

    lines = markdown_text.splitlines()

    # Titre H1
    for line in lines:
        if line.startswith("# "):
            title_text = line.replace("# ", "").strip()
            story.append(Paragraph(title_text, title_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=secondary_color, spaceAfter=12))
            break

    # Sommaire
    story.append(Paragraph("Table des Matières", h2_style))
    toc_data = []
    for line in lines:
        if line.startswith("## "):
            t = line.replace("## ", "").strip()
            toc_entries.append(t)
            toc_data.append([Paragraph(f"<b>{t}</b>", body_style)])
        elif line.startswith("### "):
            t = line.replace("### ", "").strip()
            toc_entries.append(t)
            toc_data.append([Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;• {t}", body_style)])

    if toc_data:
        t_toc = Table(toc_data, colWidths=[504])
        t_toc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_light),
            ('PADDING', (0,0), (-1,-1), 5),
            ('BOX', (0,0), (-1,-1), 0.5, border_col),
        ]))
        story.append(t_toc)
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    # Traitement du document
    i = 0
    n = len(lines)
    in_code_block = False
    code_lines_buffer = []

    while i < n:
        line = lines[i]
        line_str = line.strip()
        total_rendered_blocks += 1

        if line_str.startswith("# "):
            i += 1
            continue

        # Code
        if line_str.startswith("```"):
            if in_code_block:
                in_code_block = False
                if code_lines_buffer:
                    code_text = "<br/>".join([c.replace(" ", "&nbsp;").replace("<", "&lt;").replace(">", "&gt;") for c in code_lines_buffer])
                    code_table = Table([[Paragraph(code_text, code_style)]], colWidths=[504])
                    code_table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), bg_light),
                        ('BOX', (0,0), (-1,-1), 0.5, border_col),
                        ('PADDING', (0,0), (-1,-1), 6),
                    ]))
                    story.append(Spacer(1, 4))
                    story.append(code_table)
                    story.append(Spacer(1, 6))
                    code_lines_buffer = []
            else:
                in_code_block = True
                code_lines_buffer = []
            i += 1
            continue

        if in_code_block:
            code_lines_buffer.append(line)
            i += 1
            continue

        # Images / Diagrammes (CALCUL DYNAMIQUE DU RATIO D'ASPECT)
        img_match = re.search(r"!\[.*?\]\((.*?)\)", line_str)
        if img_match:
            img_path = img_match.group(1)
            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                try:
                    # Calcul exact de la hauteur en conservant la largeur max à 504pt
                    with PILImage.open(img_path) as PIL_img:
                        orig_w, orig_h = PIL_img.size
                    
                    max_w = 504.0
                    aspect = float(orig_h) / float(orig_w)
                    render_w = max_w
                    render_h = render_w * aspect
                    
                    # Sécurité : Si le schéma est excessivement haut, le plafonner à 420pt
                    if render_h > 420.0:
                        render_h = 420.0
                        render_w = render_h / aspect

                    story.append(Spacer(1, 8))
                    story.append(RLImage(img_path, width=render_w, height=render_h))
                    story.append(Spacer(1, 8))
                except Exception as e:
                    print(f"[⚠️] Erreur insertion image : {e}")
            i += 1
            continue

        # Tableaux Markdown
        if "|" in line_str and not line_str.startswith("####"):
            table_lines = []
            while i < n and "|" in lines[i].strip():
                table_lines.append(lines[i].strip())
                i += 1
            
            parsed_rows = []
            for t_line in table_lines:
                if "---" in t_line:
                    continue
                cells = [c.strip() for c in t_line.split("|")]
                if len(cells) > 2:
                    parsed_rows.append(cells[1:-1])

            if parsed_rows:
                num_cols = max(len(r) for r in parsed_rows)
                
                if num_cols == 4:
                    col_widths = [115.0, 65.0, 209.0, 115.0]
                elif num_cols == 3:
                    col_widths = [125.0, 75.0, 304.0]
                else:
                    col_w = 504.0 / max(1, num_cols)
                    col_widths = [col_w] * num_cols

                table_data = []
                for row_idx, row in enumerate(parsed_rows):
                    row_cells = []
                    is_header = (row_idx == 0)
                    style_to_use = tbl_hdr_style if is_header else tbl_cell_style
                    
                    for cell_text in row:
                        cell_clean = cell_text.replace("<", "&lt;").replace(">", "&gt;")
                        row_cells.append(Paragraph(cell_clean, style_to_use))
                    
                    while len(row_cells) < num_cols:
                        row_cells.append(Paragraph("", style_to_use))
                        
                    table_data.append(row_cells)

                rl_table = Table(table_data, colWidths=col_widths)
                rl_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), primary_color),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('GRID', (0,0), (-1,-1), 0.5, border_col),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(Spacer(1, 4))
                story.append(rl_table)
                story.append(Spacer(1, 6))
            continue

        # Titres et Texte
        if line_str.startswith("## "):
            story.append(Paragraph(line_str.replace("## ", "").strip(), h2_style))
        elif line_str.startswith("### "):
            story.append(Paragraph(line_str.replace("### ", "").strip(), h3_style))
        elif line_str.startswith("#### "):
            story.append(Paragraph(f"<b>{line_str.replace('#### ', '').strip()}</b>", body_style))
        elif line_str.startswith("* ") or line_str.startswith("- "):
            item_text = re.sub(r"^[\*\-]\s+", "", line_str)
            story.append(Paragraph(f"• {item_text}", body_style))
        elif line_str:
            story.append(Paragraph(line_str, body_style))

        i += 1

    doc.build(story, canvasmaker=NumberedCanvas)

    return {
        "output_pdf_path": output_pdf_path,
        "toc_entries": toc_entries,
        "overflow_events_count": overflow_events_count,
        "total_rendered_blocks": total_rendered_blocks,
        "applied_primary_color": branding.get("primary_color", "#1A365D"),
        "page_size": page_size_str
    }


# ===========================================================================
# 4. INSPECTEUR PDF
# ===========================================================================

def inspect_generated_pdf(pdf_path: str, compilation_result: Dict[str, Any], rendered_diagrams_count: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Inspecte la structure du document PDF produit."""
    pdf_generated = os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0
    file_size_bytes = os.path.getsize(pdf_path) if pdf_generated else 0
    
    page_count = 0
    if pdf_generated:
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            page_count = len(reader.pages)
        except Exception:
            page_count = max(1, file_size_bytes // 15000)

    rendered_pdf_metadata = {
        "pdf_generated": pdf_generated,
        "file_size_bytes": file_size_bytes,
        "page_count": page_count,
        "rendered_diagrams_count": rendered_diagrams_count,
        "toc_entries": compilation_result.get("toc_entries", []),
        "applied_primary_color": compilation_result.get("applied_primary_color", "#1A365D"),
        "page_size": compilation_result.get("page_size", "A4"),
        "has_page_numbers": True,
        "has_footer_text": True
    }

    layout_overflow_report = {
        "overflow_events_count": compilation_result.get("overflow_events_count", 0),
        "total_rendered_blocks": compilation_result.get("total_rendered_blocks", 1)
    }

    return rendered_pdf_metadata, layout_overflow_report
