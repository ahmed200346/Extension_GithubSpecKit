# app/utils/diagram_tools.py
import os
import re
import platform
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx
from PIL import Image, ImageDraw, ImageFont

# --- CHEMINS CENTRALISÉS (outputs/data/diagrams/) ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent                             # StageTalan/
DEFAULT_DIAGRAMS_DIR = PROJECT_ROOT / "outputs" / "data" / "diagrams"


class DiagramExporterTool:
    """
    Boîte d'outils d'exportation graphique pour le Diagram Agent.
    Gère la conversion du code Mermaid.js en images PNG (via mmdc ou Kroki),
    l'assainissement automatique de la syntaxe, la mise en page et la compilation en PDF.
    """

    @classmethod
    def sanitize_mermaid_code(cls, mermaid_code: str) -> str:
        """
        Nettoie et corrige automatiquement les erreurs de syntaxe courantes
        générées dans le code Mermaid par les LLMs.
        """
        if not mermaid_code:
            return ""

        code = str(mermaid_code).strip()

        # 1. Supprime les blocs de code Markdown (```mermaid ... ```) s'ils existent
        code = re.sub(r"^```(?:mermaid)?\s*\n?", "", code, flags=re.MULTILINE)
        code = re.sub(r"\n?\s*```$", "", code, flags=re.MULTILINE)

        # 2. Normalisation Unicode (espaces insécables, espaces invisibles, saut de ligne Windows)
        code = code.replace("\xa0", " ").replace("\u200b", "").replace("\r\n", "\n")
        
        # Normalisation des guillemets typographiques (intelligents) vers guillemets standards
        code = code.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

        # 3. Corrige les espaces entre toutes les formes Mermaid et les guillemets
        # Exemple: { "Text" } -> {"Text"} | [ "Text" ] -> ["Text"] | ( "Text" ) -> ("Text")
        code = re.sub(r'(\{+|\[+|\(+\|\>)\s+"', r'\1"', code)
        code = re.sub(r'"\s+(\}+|\]+|\)+\|?)', r'"\1', code)
        code = re.sub(r"(\{+|\[+|\(+\|\>)\s+'", r"\1'", code)
        code = re.sub(r"'\s+(\}+|\]+|\)+\|?)", r"'\1", code)

        # Correctifs ciblés pour les losanges de décision
        code = re.sub(r'\{\s+"', '{"', code)
        code = re.sub(r'"\s+\}', '"}', code)
        code = re.sub(r"\{\s+'", "{'", code)
        code = re.sub(r"'\s+\}", "'}", code)

        # 4. Suppression des sauts de lignes multiples inutiles
        code = re.sub(r'\n\s*\n', '\n', code)

        return code.strip()

    @staticmethod
    def _get_npm_prefix() -> str | None:
        try:
            result = subprocess.run(
                ["npm", "config", "get", "prefix"],
                capture_output=True, text=True, timeout=10, shell=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @classmethod
    def _find_mmdc(cls) -> List[str]:
        for cmd in [["mmdc"], ["mmdc.cmd"]]:
            try:
                subprocess.run([*cmd, "--version"], check=True, capture_output=True, timeout=10)
                return cmd
            except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue

        prefix = cls._get_npm_prefix()
        if prefix:
            candidates = []
            if platform.system() == "Windows":
                candidates = [
                    os.path.join(prefix, "mmdc.cmd"),
                    os.path.join(prefix, "node_modules", ".bin", "mmdc.cmd"),
                    os.path.join(prefix, "node_modules", "@mermaid-js", "mermaid-cli", "node_modules", ".bin", "mmdc.cmd"),
                ]
            else:
                candidates = [
                    os.path.join(prefix, "bin", "mmdc"),
                    os.path.join(prefix, "node_modules", ".bin", "mmdc"),
                ]
            for path in candidates:
                if os.path.isfile(path):
                    return [path]

        if platform.system() == "Windows":
            hardcoded = [
                os.path.expandvars(r"%APPDATA%\npm\mmdc.cmd"),
                os.path.expandvars(r"%LOCALAPPDATA%\npm\mmdc.cmd"),
                os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\npm\mmdc.cmd"),
                r"C:\Program Files\nodejs\mmdc.cmd",
                r"C:\Program Files (x86)\nodejs\mmdc.cmd",
            ]
            for path in hardcoded:
                if os.path.isfile(path):
                    return [path]

        raise RuntimeError("mermaid-cli not found")

    @classmethod
    def _render_mermaid_mmdc(cls, mermaid_code: str, output_path: Path) -> bool:
        mmdc_cmd = cls._find_mmdc()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as f:
            f.write(mermaid_code)
            mmd_path = f.name

        try:
            result = subprocess.run(
                [
                    *mmdc_cmd,
                    "-i", mmd_path,
                    "-o", str(output_path),
                    "-b", "white",
                    "-t", "default",
                    "-s", "3",
                    "--width", "2400",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                shell=(platform.system() == "Windows"),
            )
            return result.returncode == 0
        except Exception:
            return False
        finally:
            if os.path.exists(mmd_path):
                os.unlink(mmd_path)

    @staticmethod
    async def _render_mermaid_kroki(mermaid_code: str, output_path: Path) -> bool:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://kroki.io",
                    json={
                        "diagram_source": mermaid_code,
                        "diagram_type": "mermaid",
                        "output_format": "png",
                    },
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                output_path.write_bytes(response.content)
                return True
        except Exception as exc:
            print(f"[⚠️ KROKI FALLBACK FAILED] {exc}")
            return False

    @classmethod
    async def render_mermaid_to_png(cls, mermaid_code: str, output_path: Path) -> bool:
        # Nettoyage automatique du code avant toute tentative de rendu
        clean_code = cls.sanitize_mermaid_code(mermaid_code)
        
        try:
            if cls._render_mermaid_mmdc(clean_code, output_path):
                return True
        except RuntimeError:
            pass
        return await cls._render_mermaid_kroki(clean_code, output_path)

    @staticmethod
    def _render_page(
        index: int,
        title: str,
        description: str,
        diagram_png: Path | None,
        tmpdir: Path,
        error_text: str | None = None,
        raw_code: str | None = None,
    ) -> Path:
        page_width, page_height = 1240, 1754
        page = Image.new("RGB", (page_width, page_height), "white")
        draw = ImageDraw.Draw(page)

        try:
            title_font = ImageFont.truetype("arial.ttf", 40)
            desc_font = ImageFont.truetype("arial.ttf", 22)
            code_font = ImageFont.truetype("arial.ttf", 16)
            error_font = ImageFont.truetype("arial.ttf", 20)
            footer_font = ImageFont.truetype("arial.ttf", 14)
        except OSError:
            title_font = desc_font = code_font = error_font = footer_font = ImageFont.load_default()

        margin = 60
        y = margin

        draw.text((margin, y), f"{index}. {title}", fill="#1a1a1a", font=title_font)
        y += 65
        draw.text((margin, y), description, fill="#555555", font=desc_font)
        y += 50

        if error_text:
            draw.rectangle([margin, y, page_width - margin, y + 40], fill="#ffebee", outline="#f44336")
            draw.text((margin + 10, y + 8), f"⚠ {error_text}", fill="#c62828", font=error_font)
            y += 60

            if raw_code:
                draw.text((margin, y), "Raw Mermaid code:", fill="#333333", font=desc_font)
                y += 35
                lines = raw_code.split("\n")
                for line in lines[:40]:
                    draw.text((margin + 10, y), line[:90], fill="#666666", font=code_font)
                    y += 22
        else:
            available_height = page_height - y - margin - 50
            available_width = page_width - (margin * 2)

            if diagram_png and diagram_png.exists():
                try:
                    diagram = Image.open(diagram_png).convert("RGBA")
                    white_bg = Image.new("RGBA", diagram.size, (255, 255, 255, 255))
                    diagram = Image.alpha_composite(white_bg, diagram).convert("RGB")

                    img_w, img_h = diagram.size
                    scale = min(available_width / img_w, available_height / img_h)

                    new_w, new_h = int(img_w * scale), int(img_h * scale)
                    diagram = diagram.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    x = (page_width - new_w) // 2
                    page.paste(diagram, (x, y))
                except Exception as e:
                    draw.text((margin, y), f"[Image paste error: {e}]", fill="red", font=error_font)

        draw.text(
            (margin, page_height - 30),
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            fill="#999999",
            font=footer_font,
        )

        page_path = tmpdir / f"page_{index:03d}.png"
        page.save(page_path, "PNG")
        return page_path

    @classmethod
    async def render_diagrams_to_pdf(
        cls, 
        file_stem: str, 
        diagrams_data: Dict[str, Any],
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Génère les planches d'images PNG pour l'ensemble des diagrammes
        et compile le tout dans un fichier PDF.
        """
        diagrams = diagrams_data.get("diagrams", []) if isinstance(diagrams_data, dict) else []
        if not diagrams:
            raise ValueError("No diagrams to render")

        target_dir = output_dir if output_dir is not None else DEFAULT_DIAGRAMS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            page_paths = []

            for i, diag in enumerate(diagrams, start=1):
                title = diag.get("title", f"Diagram {i}")
                description = diag.get("description", "")
                mermaid_code = diag.get("mermaid_code", "")

                if not str(mermaid_code).strip():
                    continue

                png_path = tmpdir / f"diag_{i:03d}.png"
                success = await cls.render_mermaid_to_png(str(mermaid_code), png_path)

                if not success:
                    page_path = cls._render_page(
                        i, title, description, None, tmpdir,
                        error_text="Could not render diagram — invalid Mermaid syntax",
                        raw_code=str(mermaid_code),
                    )
                else:
                    page_path = cls._render_page(i, title, description, png_path, tmpdir)

                page_paths.append(page_path)

            if not page_paths:
                raise RuntimeError("No pages were rendered")

            import img2pdf
            filename = f"{file_stem}_diagrams.pdf"
            pdf_path = target_dir / filename

            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert([str(p) for p in page_paths]))

        return pdf_path
# # app/utils/diagram_tools.py
# import os
# import re
# import platform
# import subprocess
# import tempfile
# from pathlib import Path
# from datetime import datetime
# from typing import Dict, Any, List, Optional

# import httpx
# from PIL import Image, ImageDraw, ImageFont

# # --- CHEMINS CENTRALISÉS (outputs/data/diagrams/) ---
# BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
# PROJECT_ROOT = BASE_DIR.parent                             # StageTalan/
# DEFAULT_DIAGRAMS_DIR = PROJECT_ROOT / "outputs" / "data" / "diagrams"


# class DiagramExporterTool:
#     """
#     Boîte d'outils d'exportation graphique pour le Diagram Agent.
#     Gère la conversion du code Mermaid.js en images PNG (via mmdc ou Kroki),
#     l'assainissement automatique de la syntaxe, la mise en page et la compilation en PDF.
#     """

#     @classmethod
#     def sanitize_mermaid_code(cls, mermaid_code: str) -> str:
#         """
#         Nettoie et corrige automatiquement les erreurs de syntaxe courantes
#         générées dans le code Mermaid par les LLMs.
#         """
#         if not mermaid_code:
#             return ""

#         code = str(mermaid_code).strip()

#         # 1. Supprime les blocs de code Markdown (```mermaid ... ```) s'ils existent
#         code = re.sub(r"^```(?:mermaid)?\s*\n?", "", code, flags=re.MULTILINE)
#         code = re.sub(r"\n?\s*```$", "", code, flags=re.MULTILINE)

#         # 2. Normalisation Unicode (suppression des espaces insécables \xa0 et guillemets intelligents)
#         code = code.replace("\xa0", " ").replace("\u200b", "")
#         code = code.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

#         # 3. Corrige les espaces entre toutes les formes Mermaid et les guillemets
#         # Exemple: { "Text" } -> {"Text"} | [ "Text" ] -> ["Text"] | ( "Text" ) -> ("Text")
#         code = re.sub(r'(\{+|\[+|\(+\|\>)\s+"', r'\1"', code)
#         code = re.sub(r'"\s+(\}+|\]+|\)+\|?)', r'"\1', code)

#         # Correctifs ciblés pour les losanges de décision { "..." } et { '...' }
#         code = re.sub(r'\{\s+"', '{"', code)
#         code = re.sub(r'"\s+\}', '"}', code)
#         code = re.sub(r"\{\s+'", "{'", code)
#         code = re.sub(r"'\s+\}", "'}", code)

#         # 4. Suppression des saut de lignes multiples inutiles
#         code = re.sub(r'\n\s*\n', '\n', code)

#         return code.strip()

#     @staticmethod
#     def _get_npm_prefix() -> str | None:
#         try:
#             result = subprocess.run(
#                 ["npm", "config", "get", "prefix"],
#                 capture_output=True, text=True, timeout=10, shell=True
#             )
#             if result.returncode == 0:
#                 return result.stdout.strip()
#         except Exception:
#             pass
#         return None

#     @classmethod
#     def _find_mmdc(cls) -> List[str]:
#         for cmd in [["mmdc"], ["mmdc.cmd"]]:
#             try:
#                 subprocess.run([*cmd, "--version"], check=True, capture_output=True, timeout=10)
#                 return cmd
#             except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
#                 continue

#         prefix = cls._get_npm_prefix()
#         if prefix:
#             candidates = []
#             if platform.system() == "Windows":
#                 candidates = [
#                     os.path.join(prefix, "mmdc.cmd"),
#                     os.path.join(prefix, "node_modules", ".bin", "mmdc.cmd"),
#                     os.path.join(prefix, "node_modules", "@mermaid-js", "mermaid-cli", "node_modules", ".bin", "mmdc.cmd"),
#                 ]
#             else:
#                 candidates = [
#                     os.path.join(prefix, "bin", "mmdc"),
#                     os.path.join(prefix, "node_modules", ".bin", "mmdc"),
#                 ]
#             for path in candidates:
#                 if os.path.isfile(path):
#                     return [path]

#         if platform.system() == "Windows":
#             hardcoded = [
#                 os.path.expandvars(r"%APPDATA%\npm\mmdc.cmd"),
#                 os.path.expandvars(r"%LOCALAPPDATA%\npm\mmdc.cmd"),
#                 os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\npm\mmdc.cmd"),
#                 r"C:\Program Files\nodejs\mmdc.cmd",
#                 r"C:\Program Files (x86)\nodejs\mmdc.cmd",
#             ]
#             for path in hardcoded:
#                 if os.path.isfile(path):
#                     return [path]

#         raise RuntimeError("mermaid-cli not found")

#     @classmethod
#     def _render_mermaid_mmdc(cls, mermaid_code: str, output_path: Path) -> bool:
#         mmdc_cmd = cls._find_mmdc()

#         with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as f:
#             f.write(mermaid_code)
#             mmd_path = f.name

#         try:
#             result = subprocess.run(
#                 [
#                     *mmdc_cmd,
#                     "-i", mmd_path,
#                     "-o", str(output_path),
#                     "-b", "white",
#                     "-t", "default",
#                     "-s", "3",
#                     "--width", "2400",
#                 ],
#                 capture_output=True,
#                 text=True,
#                 timeout=60,
#                 shell=(platform.system() == "Windows"),
#             )
#             return result.returncode == 0
#         except Exception:
#             return False
#         finally:
#             if os.path.exists(mmd_path):
#                 os.unlink(mmd_path)

#     @staticmethod
#     async def _render_mermaid_kroki(mermaid_code: str, output_path: Path) -> bool:
#         try:
#             async with httpx.AsyncClient(timeout=60.0) as client:
#                 response = await client.post(
#                     "https://kroki.io",
#                     json={
#                         "diagram_source": mermaid_code,
#                         "diagram_type": "mermaid",
#                         "output_format": "png",
#                     },
#                     headers={"Content-Type": "application/json"},
#                 )
#                 response.raise_for_status()
#                 output_path.write_bytes(response.content)
#                 return True
#         except Exception as exc:
#             print(f"[⚠️ KROKI FALLBACK FAILED] {exc}")
#             return False

#     @classmethod
#     async def render_mermaid_to_png(cls, mermaid_code: str, output_path: Path) -> bool:
#         # Nettoyage automatique avant rendu
#         clean_code = cls.sanitize_mermaid_code(mermaid_code)
        
#         try:
#             if cls._render_mermaid_mmdc(clean_code, output_path):
#                 return True
#         except RuntimeError:
#             pass
#         return await cls._render_mermaid_kroki(clean_code, output_path)

#     @staticmethod
#     def _render_page(
#         index: int,
#         title: str,
#         description: str,
#         diagram_png: Path | None,
#         tmpdir: Path,
#         error_text: str | None = None,
#         raw_code: str | None = None,
#     ) -> Path:
#         page_width, page_height = 1240, 1754
#         page = Image.new("RGB", (page_width, page_height), "white")
#         draw = ImageDraw.Draw(page)

#         try:
#             title_font = ImageFont.truetype("arial.ttf", 40)
#             desc_font = ImageFont.truetype("arial.ttf", 22)
#             code_font = ImageFont.truetype("arial.ttf", 16)
#             error_font = ImageFont.truetype("arial.ttf", 20)
#             footer_font = ImageFont.truetype("arial.ttf", 14)
#         except OSError:
#             title_font = desc_font = code_font = error_font = footer_font = ImageFont.load_default()

#         margin = 60
#         y = margin

#         draw.text((margin, y), f"{index}. {title}", fill="#1a1a1a", font=title_font)
#         y += 65
#         draw.text((margin, y), description, fill="#555555", font=desc_font)
#         y += 50

#         if error_text:
#             draw.rectangle([margin, y, page_width - margin, y + 40], fill="#ffebee", outline="#f44336")
#             draw.text((margin + 10, y + 8), f"⚠ {error_text}", fill="#c62828", font=error_font)
#             y += 60

#             if raw_code:
#                 draw.text((margin, y), "Raw Mermaid code:", fill="#333333", font=desc_font)
#                 y += 35
#                 lines = raw_code.split("\n")
#                 for line in lines[:40]:
#                     draw.text((margin + 10, y), line[:90], fill="#666666", font=code_font)
#                     y += 22
#         else:
#             available_height = page_height - y - margin - 50
#             available_width = page_width - (margin * 2)

#             if diagram_png and diagram_png.exists():
#                 try:
#                     diagram = Image.open(diagram_png).convert("RGBA")
#                     white_bg = Image.new("RGBA", diagram.size, (255, 255, 255, 255))
#                     diagram = Image.alpha_composite(white_bg, diagram).convert("RGB")

#                     img_w, img_h = diagram.size
#                     scale = min(available_width / img_w, available_height / img_h)

#                     new_w, new_h = int(img_w * scale), int(img_h * scale)
#                     diagram = diagram.resize((new_w, new_h), Image.Resampling.LANCZOS)

#                     x = (page_width - new_w) // 2
#                     page.paste(diagram, (x, y))
#                 except Exception as e:
#                     draw.text((margin, y), f"[Image paste error: {e}]", fill="red", font=error_font)

#         draw.text(
#             (margin, page_height - 30),
#             f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
#             fill="#999999",
#             font=footer_font,
#         )

#         page_path = tmpdir / f"page_{index:03d}.png"
#         page.save(page_path, "PNG")
#         return page_path

#     @classmethod
#     async def render_diagrams_to_pdf(
#         cls, 
#         file_stem: str, 
#         diagrams_data: Dict[str, Any],
#         output_dir: Optional[Path] = None
#     ) -> Path:
#         """
#         Génère les planches d'images PNG pour l'ensemble des diagrammes
#         et compile le tout dans un fichier PDF sous outputs/data/diagrams/.
#         """
#         diagrams = diagrams_data.get("diagrams", []) if isinstance(diagrams_data, dict) else []
#         if not diagrams:
#             raise ValueError("No diagrams to render")

#         target_dir = output_dir if output_dir is not None else DEFAULT_DIAGRAMS_DIR
#         target_dir.mkdir(parents=True, exist_ok=True)

#         with tempfile.TemporaryDirectory() as tmpdir_str:
#             tmpdir = Path(tmpdir_str)
#             page_paths = []

#             for i, diag in enumerate(diagrams, start=1):
#                 title = diag.get("title", f"Diagram {i}")
#                 description = diag.get("description", "")
#                 mermaid_code = diag.get("mermaid_code", "")

#                 if not str(mermaid_code).strip():
#                     continue

#                 png_path = tmpdir / f"diag_{i:03d}.png"
#                 success = await cls.render_mermaid_to_png(str(mermaid_code), png_path)

#                 if not success:
#                     page_path = cls._render_page(
#                         i, title, description, None, tmpdir,
#                         error_text="Could not render diagram — invalid Mermaid syntax",
#                         raw_code=str(mermaid_code),
#                     )
#                 else:
#                     page_path = cls._render_page(i, title, description, png_path, tmpdir)

#                 page_paths.append(page_path)

#             if not page_paths:
#                 raise RuntimeError("No pages were rendered")

#             import img2pdf
#             filename = f"{file_stem}_diagrams.pdf"
#             pdf_path = target_dir / filename

#             with open(pdf_path, "wb") as f:
#                 f.write(img2pdf.convert([str(p) for p in page_paths]))

#         return pdf_path
