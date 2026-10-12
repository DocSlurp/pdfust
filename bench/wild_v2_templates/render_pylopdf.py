"""Render wild-v2 documents with pylopdf's own generation API (untagged PDF).

Text goes through ``Page.insert_textbox`` with system Noto OpenType fonts, so
krilla subset-embeds every face and HarfRust shapes Arabic, Hebrew,
Devanagari, Thai and CJK. Each text box uses the first font in the language
stack that covers all of its glyphs. Rules, panels and table grids are drawn
in a small hand-written vector PDF that is placed under the text with
``show_pdf_page(overlay=False)``; images use ``insert_image``. Layout is a
simple top-to-bottom flow with exact measurement through a scratch document.
"""

# ruff: noqa: ANN401, C901, E501, PLR0912, PLR0913, PLR2004, PLR0917, D401, PLC0415, TRY003, EM101, EM102, FBT001, PLW2901
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.wild_templates.model import links, plain
from bench.wild_v2_templates.fonts import LATIN, stack

if TYPE_CHECKING:
    from pathlib import Path

PAGE_SIZES = {"A4": (595.2756, 841.8898), "Letter": (612.0, 792.0), "slide": (960.0, 540.0)}


class Overflow(Exception):  # noqa: N818 - control-flow signal, not an error condition
    """Raised when authored content does not fit its page at the current scale."""


def _rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def vector_pdf(width: float, height: float, operators: list[str]) -> bytes:
    """A minimal one-page PDF whose content stream holds the given path operators."""
    content = "\n".join(operators).encode("ascii")
    bodies = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
              f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.4f} {height:.4f}] /Contents 4 0 R /Resources << >> >>".encode(),
              b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"]
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for number, body in enumerate(bodies, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(bodies) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(bodies) + 1, xref)
    return bytes(out)


class Layout:
    """Flow authored blocks onto pylopdf pages."""

    def __init__(self, doc: dict[str, Any], assets: Path, scale: float) -> None:
        """Create the target and scratch documents."""
        import pylopdf

        self.pylopdf = pylopdf
        self.doc = doc
        self.assets = assets
        self.scale = scale
        theme = doc["theme"]
        self.width, self.height = PAGE_SIZES[doc["page_size"]]
        slide = doc["page_size"] == "slide"
        self.margin = float(theme.get("py_margin", 44 if slide else 50))
        self.size = float(theme.get("py_size", 17 if slide else 9.5)) * scale
        self.lang = doc["metadata"]["lang"]
        self.rtl = doc.get("dir") == "rtl"
        self.accent = _rgb(theme.get("accent", "#24476b"))
        self.serif = theme.get("py_serif", False)
        self.out = pylopdf.Document()
        self._scratch_uses = 0
        self._scratch: Any = None
        self.font_cache: dict[tuple[str, bool, str], tuple[Path, int]] = {}
        self.toc: list[list[Any]] = []
        self.ops: list[str] = []
        self.page: Any = None
        self.page_number = 0
        self.y = 0.0

    # ---------------------------------------------------------------- text primitives

    def scratch(self) -> Any:
        """A throwaway page used only to measure text boxes."""
        if self._scratch is None or self._scratch_uses > 150:
            self._scratch = self.pylopdf.Document()
            self._scratch.new_page(width=2000, height=4000)
            self._scratch_uses = 0
        self._scratch_uses += 1
        return self._scratch[0]

    def font(self, text: str, *, bold: bool, role: str) -> tuple[Path, int]:
        """First font in the stack that covers ``text`` (cached per text/style)."""
        key = (text, bold, role)
        if key in self.font_cache:
            return self.font_cache[key]
        candidates = stack(self.lang, bold=bold, role="serif" if self.serif and role == "regular" else role)
        if role == "italic":
            candidates.insert(0, LATIN["italic"])
        for path, index in candidates:
            try:
                self.scratch().insert_textbox((0, 0, 1900, 3900), text, fontfile=str(path), fontindex=index, fontsize=8)
            except self.pylopdf.PdfError:
                continue
            self.font_cache[key] = (path, index)
            return path, index
        raise ValueError(f"No font covers {text!r}")

    def measure(self, text: str, width: float, size: float, *, bold: bool = False, role: str = "regular",
                lineheight: float = 1.28) -> float:
        """Height used by ``text`` wrapped to ``width``."""
        if not text.strip():
            return size * lineheight
        path, index = self.font(text, bold=bold, role=role)
        spare = self.scratch().insert_textbox((0, 0, width, 3900), text, fontfile=str(path), fontindex=index, fontsize=size,
                                              lineheight=lineheight)
        if spare < 0:
            raise Overflow(text[:40])
        return 3900 - spare

    def text(self, x: float, y: float, width: float, text: str, size: float, *, bold: bool = False, role: str = "regular",
             color: tuple[float, float, float] = (0.1, 0.1, 0.12), align: str = "start", lineheight: float = 1.28, bounded: bool = True) -> float:
        """Draw wrapped text at the display-space top-left ``(x, y)`` and return its height."""
        height = self.measure(text, width, size, bold=bold, role=role, lineheight=lineheight)
        if not text.strip():
            return height
        if bounded and y + height > self.height - self.margin + 2:
            raise Overflow(text[:40])
        path, index = self.font(text, bold=bold, role=role)
        mode = {"start": "right" if self.rtl else "left", "end": "left" if self.rtl else "right"}.get(align, align)
        constant = {"left": self.pylopdf.TEXT_ALIGN_LEFT, "right": self.pylopdf.TEXT_ALIGN_RIGHT,
                    "center": self.pylopdf.TEXT_ALIGN_CENTER, "justify": self.pylopdf.TEXT_ALIGN_JUSTIFY}[mode]
        spare = self.page.insert_textbox((x, y, x + width, y + height + size), text, fontfile=str(path), fontindex=index,
                                         fontsize=size, color=color, align=constant, lineheight=lineheight)
        if spare < 0:
            raise Overflow(text[:40])
        return height

    # ---------------------------------------------------------------- vector primitives

    def fill(self, x0: float, y0: float, x1: float, y1: float, color: tuple[float, float, float]) -> None:
        """Queue a filled rectangle (display coordinates)."""
        self.ops.append(f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg {x0:.2f} {self.height - y1:.2f} {x1 - x0:.2f} {y1 - y0:.2f} re f")

    def line(self, x0: float, y0: float, x1: float, y1: float, width: float = 0.6, color: tuple[float, float, float] = (0.54, 0.56, 0.6)) -> None:
        """Queue a stroked line (display coordinates)."""
        self.ops.append(f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} RG {width:.2f} w {x0:.2f} {self.height - y0:.2f} m {x1:.2f} {self.height - y1:.2f} l S")

    # ---------------------------------------------------------------- pages

    def new_page(self) -> None:
        """Finish the current page and start the next one."""
        self.finish_page()
        self.page = self.out.new_page(width=self.width, height=self.height)
        self.page_number += 1
        self.y = self.margin
        total = len(self.doc["pages"])
        small = 7.5
        color = (0.4, 0.4, 0.4)
        if self.doc.get("running_header"):
            self.text(self.margin, self.margin * 0.42, self.width - 2 * self.margin,
                      self.doc["running_header"].format(page=self.page_number, pages=total), small, color=color, bounded=False)
        if self.doc.get("running_footer"):
            self.text(self.margin, self.height - self.margin * 0.62, self.width - 2 * self.margin,
                      self.doc["running_footer"].format(page=self.page_number, pages=total), small, color=color, align="center",
                      bounded=False)

    def finish_page(self) -> None:
        """Place the queued vector graphics under the page text."""
        if self.page is not None and self.ops:
            source = self.pylopdf.Document(stream=vector_pdf(self.width, self.height, self.ops))
            self.page.show_pdf_page((0, 0, self.width, self.height), source, 0, overlay=False)
        self.ops = []

    # ---------------------------------------------------------------- blocks

    def flow(self, blocks: list[dict[str, Any]], x: float, width: float) -> None:
        """Lay out blocks top to bottom inside a column."""
        float_bottom, float_side, float_width = 0.0, "", 0.0
        for block in blocks:
            if block["kind"] == "figure" and block.get("wrap") in {"left", "right"}:
                side = block["wrap"]
                if self.rtl:
                    side = "right" if side == "left" else "left"
                share = float(block.get("width", "40%").rstrip("%")) / 100
                fig_width = width * share
                fx = x if side == "left" else x + width - fig_width
                top = self.y
                self.figure(block, fx, fig_width)
                float_bottom, float_side, float_width = self.y, side, fig_width + 12
                self.y = top
                continue
            if block["kind"] == "paragraph" and self.y < float_bottom:
                px = x + float_width if float_side == "left" else x
                self.block(block, px, width - float_width)
                continue
            self.y = max(self.y, float_bottom)
            self.block(block, x, width)
        self.y = max(self.y, float_bottom)

    def block(self, block: dict[str, Any], x: float, width: float) -> None:
        """Lay out one block."""
        kind = block["kind"]
        cls = block.get("cls", "").split()
        size = self.size
        if kind == "heading":
            factor = {1: 1.9, 2: 1.35}.get(block["level"], 1.1)
            self.y += size * (0.2 if block["level"] == 1 else 0.7)
            text = plain(block["text"])
            if self.y + size * factor * 3 > self.height - self.margin:
                raise Overflow(text)
            self.toc.append([block["level"], text, self.page_number])
            self.y += self.text(x, self.y, width, text, size * factor, bold=True, color=self.accent, lineheight=1.2)
            if block["level"] == 2 and self.doc["page_size"] != "slide":
                self.line(x, self.y + 1, x + width, self.y + 1, 0.5, tuple(0.5 + 0.5 * c for c in self.accent))
            self.y += size * 0.45
        elif kind == "paragraph":
            factor = 0.86 if {"small", "muted", "meta"} & set(cls) else 1.12 if "lead" in cls else 1.6 if "brand" in cls else 1.0
            align = "end" if "right" in cls else "center" if "center" in cls else "start"
            color = self.accent if "brand" in cls else (0.27, 0.27, 0.3) if factor < 1 else (0.1, 0.1, 0.12)
            text = plain(block["text"])
            height = self.text(x, self.y, width, text, size * factor, bold="brand" in cls, color=color, align=align)
            self._links(block["text"], x, self.y, width, height)
            self.y += height + size * 0.55
        elif kind == "list":
            self.items(block["items"], block["ordered"], x, width, 0)
            self.y += size * 0.35
        elif kind == "table":
            self.table(block, x, width)
        elif kind == "figure":
            share = float(block.get("width", "100%").rstrip("%")) / 100
            fig_width = min(width * share * self.scale, width)
            self.figure(block, x + (width - fig_width) / 2, fig_width)
        elif kind in {"callout", "sidebar"}:
            text = (plain(block["title"]) + "\n" if block.get("title") else "") + plain(block["text"])
            pad = 7
            height = self.measure(text, width - 2 * pad - 4, size) + 2 * pad
            if self.y + height > self.height - self.margin:
                raise Overflow(text[:30])
            warn = "warn" in cls
            background = (0.99, 0.94, 0.93) if warn else (0.93, 0.96, 0.98) if "note" in cls or kind == "sidebar" else (0.98, 0.96, 0.93)
            edge = (0.75, 0.22, 0.17) if warn else self.accent if kind == "sidebar" else (0.82, 0.55, 0.17)
            self.fill(x, self.y, x + width, self.y + height, background)
            bar_x = x + width - 3 if self.rtl else x
            self.fill(bar_x, self.y, bar_x + 3, self.y + height, edge)
            self.text(x + pad + 4, self.y + pad, width - 2 * pad - 4, text, size)
            self.y += height + size * 0.8
        elif kind == "footnote":
            self.y += self.text(x, self.y, width, plain(block["text"]), size * 0.78, color=(0.27, 0.27, 0.3)) + 2
        elif kind == "code":
            if block.get("caption"):
                self.y += self.text(x, self.y, width, plain(block["caption"]), size * 0.86, bold=True, color=(0.33, 0.33, 0.36))
            pad = 6
            height = self.measure(block["text"], width - 2 * pad, size * 0.82, role="mono", lineheight=1.3) + 2 * pad
            if self.y + height > self.height - self.margin:
                raise Overflow("code")
            self.fill(x, self.y, x + width, self.y + height, (0.95, 0.953, 0.96))
            self.text(x + pad, self.y + pad, width - 2 * pad, block["text"], size * 0.82, role="mono", lineheight=1.3, align="left")
            self.y += height + size * 0.8
        elif kind == "equation":
            height = self.text(x + 40, self.y + 3, width - 80, block["text"], size * 1.1, role="math", align="center")
            if block["number"]:
                self.text(x + width - 40, self.y + 3, 40, block["number"], size, align="right")
            self.y += height + size * 0.9
        elif kind == "fields":
            for label, value in block["items"]:
                self.y += self.text(x, self.y, width, f"{label}: {value}", size) + 3
        elif kind == "pair" or (kind == "group" and ({"split", "letterhead"} & set(cls))):
            self.side_by_side([[child] for child in block["blocks"]], x, width)
        elif kind == "columns":
            count = block.get("count", 2)
            weights = [len(plain(str(child.get("text", "")))) + 60 * len(child.get("items", [])) + 300 * (child["kind"] in {"figure", "table"})
                       for child in block["blocks"]]
            target, columns, acc = sum(weights) / count or 1, [[] for _ in range(count)], 0.0
            for child, weight in zip(block["blocks"], weights, strict=True):
                columns[min(int(acc / target), count - 1)].append(child)
                acc += weight
            self.side_by_side(columns, x, width)
        elif kind == "group":
            self.flow(block["blocks"], x, width)
        elif kind == "form":
            raise ValueError("AcroForm sections are only produced by the ReportLab renderer")
        else:
            raise ValueError(kind)

    def _links(self, markup: str, x: float, y: float, width: float, height: float) -> None:
        for link in links(markup):
            if link["href"].startswith(("http://", "https://", "mailto:")):
                self.page.add_link_annot((x, y, x + width, y + height), link["href"])

    def side_by_side(self, columns: list[list[dict[str, Any]]], x: float, width: float) -> None:
        """Lay out block lists in parallel columns; the cursor ends below the tallest."""
        gap = 14.0
        col_width = (width - gap * (len(columns) - 1)) / len(columns)
        top, bottom = self.y, self.y
        for index, blocks in enumerate(columns):
            slot = len(columns) - 1 - index if self.rtl else index
            self.y = top
            self.flow(blocks, x + slot * (col_width + gap), col_width)
            bottom = max(bottom, self.y)
        self.y = bottom

    def items(self, items: list[Any], ordered: bool, x: float, width: float, depth: int) -> None:
        """Bulleted or numbered (nested) list."""
        indent = self.size * 1.7
        for number, entry in enumerate(items, start=1):
            text = plain(entry["text"] if isinstance(entry, dict) else entry)
            if ordered:
                marker = (f"{number}.", f"{'abcdefghijklmnopqrstuvwxyz'[(number - 1) % 26]})", f"({['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x'][(number - 1) % 10]})")[depth % 3]
            else:
                marker = "•" if depth % 2 == 0 else "◦"
            text_x = x if self.rtl else x + indent
            marker_x = x + width - indent if self.rtl else x
            height = self.text(text_x, self.y, width - indent, text, self.size)
            self.text(marker_x, self.y, indent - 3, marker, self.size, align="end" if not self.rtl else "start")
            self.y += height + self.size * 0.18
            if isinstance(entry, dict):
                self.items(entry["items"], entry["ordered"], x if self.rtl else x + indent, width - indent, depth + 1)

    def figure(self, block: dict[str, Any], x: float, width: float) -> None:
        """Image with caption below."""
        from PIL import Image

        path = self.assets / block["src"]
        with Image.open(path) as image:
            px_w, px_h = image.size
        height = width * px_h / px_w
        if self.y + height > self.height - self.margin:
            raise Overflow(block["id"])
        self.page.insert_image((x, self.y, x + width, self.y + height), filename=str(path))
        self.y += height + 3
        if block.get("caption"):
            self.y += self.text(x, self.y, width, plain(block["caption"]), self.size * 0.82, role="italic", color=(0.33, 0.33, 0.36))
        self.y += self.size * 0.7

    def table(self, block: dict[str, Any], x: float, width: float) -> None:
        """Ruled or borderless table (column spans supported)."""
        if block["rendering"] in {"chart_data", "screenshot"}:
            return
        values = block["values"]
        cols = len(values[0])
        shares = block.get("widths") or [100 / cols] * cols
        widths = [width * s / sum(shares) for s in shares]
        starts = []
        position = x
        for w in widths:
            starts.append(position)
            position += w
        if self.rtl:
            starts = [x + width - (s - x) - w for s, w in zip(starts, widths, strict=True)]
        spans = {(s["row"], s["column"]): s["column_span"] for s in block["spans"]}
        if any(s["row_span"] > 1 for s in block["spans"]):
            raise ValueError("pylopdf tables support column spans only")
        align = block.get("align") or ["l"] * cols
        header_rows = block["header_rows"]
        totals = set(block.get("total_rows") or [])
        size = self.size * 0.92
        pad = 3.2
        ruled = block["rendering"] == "ruled"
        if block.get("caption"):
            self.y += self.text(x, self.y, width, plain(block["caption"]), self.size * 0.95, bold=True) + 3
        top = self.y
        row_edges = [top]
        for r, row in enumerate(values):
            heights = []
            cells = []
            for c, value in enumerate(row):
                if value is None:
                    continue
                span = spans.get((r, c), 1)
                cell_x = min(starts[c:c + span]) if self.rtl else starts[c]
                cell_w = sum(widths[c:c + span])
                bold = r < header_rows or r in totals
                heights.append(self.measure(value or " ", cell_w - 2 * pad, size, bold=bold))
                cells.append((cell_x, cell_w, value, bold, "center" if span > 1 else {"r": "end", "c": "center"}.get(align[c], "start")))
            row_height = max(heights) + 2 * pad
            if self.y + row_height > self.height - self.margin:
                raise Overflow(f"table {block['id']} row {r}")
            if r < header_rows:
                self.fill(x, self.y, x + width, self.y + row_height, (0.9, 0.92, 0.95) if ruled else (1, 1, 1))
            elif not ruled and (r - header_rows) % 2 == 1:
                self.fill(x, self.y, x + width, self.y + row_height, (0.96, 0.965, 0.97))
            for cell_x, cell_w, value, bold, cell_align in cells:
                if value:
                    self.text(cell_x + pad, self.y + pad, cell_w - 2 * pad, value, size, bold=bold, align=cell_align, lineheight=1.22)
                if ruled:
                    self.line(cell_x, self.y, cell_x, self.y + row_height)
                    self.line(cell_x + cell_w, self.y, cell_x + cell_w, self.y + row_height)
            if r in totals:
                self.line(x, self.y, x + width, self.y, 1.2, (0.15, 0.15, 0.15))
            self.y += row_height
            row_edges.append(self.y)
        if ruled:
            for edge in row_edges:
                self.line(x, edge, x + width, edge)
        elif header_rows:
            self.line(x, row_edges[header_rows], x + width, row_edges[header_rows], 1.1, self.accent)
            self.line(x, row_edges[-1], x + width, row_edges[-1], 0.6, (0.6, 0.6, 0.6))
        self.y += self.size * 0.9


def render(doc: dict[str, Any], assets: Path, out: Path, scale: float = 1.0) -> int:
    """Write ``out`` and return its page count; raises :class:`Overflow` when a page does not fit."""
    layout = Layout(doc, assets, scale)
    for blocks in doc["pages"]:
        layout.new_page()
        layout.flow(blocks, layout.margin, layout.width - 2 * layout.margin)
    layout.finish_page()
    meta = doc["metadata"]
    stamp = meta["created"].replace("-", "").replace(":", "").replace("T", "").rstrip("Z")
    layout.out.set_metadata({"title": meta["title"], "author": meta["author"], "subject": meta["subject"],
                             "keywords": ", ".join(meta["keywords"]), "creator": doc.get("creator_tool", "pylopdf generation"),
                             "producer": f"jev-pdf {layout.pylopdf.__version__} (krilla, HarfRust)",
                             "creationDate": f"D:{stamp}Z", "modDate": f"D:{stamp}Z"})
    if layout.toc:
        toc, previous = [], 0
        for level, title, page in layout.toc:
            level = min(level, previous + 1)
            toc.append([level, title, page])
            previous = level
        layout.out.set_toc(toc)
    layout.out.save(str(out), garbage=True, deflate=True)
    return len(layout.out)
