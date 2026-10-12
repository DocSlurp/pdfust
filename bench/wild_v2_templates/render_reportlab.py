"""Render wild-v2 documents with ReportLab platypus (untagged PDF).

Font policy: documents whose text is fully WinAnsi-encodable use the
unembedded Standard 14 Type 1 fonts (Helvetica, Times, Courier); other Latin,
Cyrillic and Greek documents embed Noto Sans TrueType subsets; Japanese,
Chinese and Korean documents use ReportLab's non-embedded Adobe CID fonts.
ReportLab does not shape complex scripts, so Arabic, Hebrew, Devanagari and
Thai documents are not routed here. Charts are native ReportLab vector
drawings. ``form`` blocks become real AcroForm widgets that are filled later
by pylopdf.
"""

# ruff: noqa: ANN401, C901, E501, PLR0912, PLC0415, PLR0911, PLR2004, RUF059, FBT001, ARG002, ARG001
from __future__ import annotations

import os
from html import escape
from typing import TYPE_CHECKING, Any

from bench.wild_templates.model import tokens
from bench.wild_v2_templates.fonts import LATIN

if TYPE_CHECKING:
    from pathlib import Path

CID_FONTS = {"ja": "HeiseiKakuGo-W5", "zh-CN": "STSong-Light", "zh-TW": "MSung-Light", "ko": "HYGothic-Medium"}
PAGE_SIZES = {"A4": (595.2756, 841.8898), "Letter": (612.0, 792.0), "slide": (960.0, 540.0)}
_SKIP_KEYS = {"kind", "rendering", "cls", "src", "wrap", "figure_kind", "id", "render", "mathml", "starmath", "photo",
              "chart", "align", "widths", "name", "field_type", "language"}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple):
        return [s for v in value for s in _strings(v)]
    if isinstance(value, dict):
        return [s for k, v in value.items() if k not in _SKIP_KEYS for s in _strings(v)]
    return []


def _registered() -> None:
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont

    if "NotoSans" in pdfmetrics.getRegisteredFontNames():
        return
    for name, key in (("NotoSans", "regular"), ("NotoSans-Bold", "bold"), ("NotoSans-Italic", "italic"),
                      ("NotoSerif", "serif"), ("NotoSerif-Bold", "serif_bold"), ("NotoSansMono", "mono")):
        pdfmetrics.registerFont(TTFont(name, str(LATIN[key][0])))
    for family, regular, bold, italic in (("NotoSans", "NotoSans", "NotoSans-Bold", "NotoSans-Italic"),
                                          ("NotoSerif", "NotoSerif", "NotoSerif-Bold", "NotoSerif")):
        addMapping(family, 0, 0, regular)
        addMapping(family, 1, 0, bold)
        addMapping(family, 0, 1, italic)
        addMapping(family, 1, 1, bold)
    from reportlab.pdfbase import _cidfontdata

    # ReportLab maps MSung-Light (traditional Chinese) to the simplified-Chinese UniGB encoding,
    # which leaves zh-TW glyphs unrenderable in most viewers; use the CNS Unicode CMap instead.
    _cidfontdata.defaultUnicodeEncodings["MSung-Light"] = ("cht", "UniCNS-UCS2-H")
    for cid in CID_FONTS.values():
        pdfmetrics.registerFont(UnicodeCIDFont(cid))
        for bold in (0, 1):
            for italic in (0, 1):
                addMapping(cid, bold, italic, cid)


def font_policy(doc: dict[str, Any]) -> dict[str, str]:
    """Choose body, bold, italic and mono fonts for one document."""
    lang = doc["metadata"]["lang"]
    key = lang if lang in CID_FONTS else lang.split("-")[0]
    if key in CID_FONTS:
        cid = CID_FONTS[key]
        return {"body": cid, "bold": cid, "italic": cid, "mono": "Courier", "kind": "cid"}
    text = "".join(_strings(doc["pages"])) + "".join(_strings(doc["metadata"])) + doc.get("running_header", "") + doc.get("running_footer", "")
    try:
        text.encode("cp1252")
        winansi = True
    except UnicodeEncodeError:
        winansi = False
    serif = doc["theme"].get("rl_serif", False)
    if winansi:
        if serif:
            return {"body": "Times-Roman", "bold": "Times-Bold", "italic": "Times-Italic", "mono": "Courier", "kind": "standard14"}
        return {"body": "Helvetica", "bold": "Helvetica-Bold", "italic": "Helvetica-Oblique", "mono": "Courier", "kind": "standard14"}
    family = "NotoSerif" if serif else "NotoSans"
    return {"body": family, "bold": f"{family}-Bold", "italic": "NotoSans-Italic", "mono": "NotoSansMono", "kind": "truetype"}


def rl_markup(markup: str) -> str:
    """Inline markup to ReportLab paragraph markup."""
    out = []
    for style, text, href in tokens(markup):
        body = escape(text, quote=False).replace("\n", "<br/>")
        if style == "bold":
            out.append(f"<b>{body}</b>")
        elif style == "italic":
            out.append(f"<i>{body}</i>")
        elif style == "link":
            out.append(f'<a href="{escape(href or "")}" color="#1f4e8c"><u>{body}</u></a>')
        else:
            out.append(body)
    return "".join(out)


class Renderer:
    """Build platypus flowables for one document at one scale."""

    def __init__(self, doc: dict[str, Any], assets: Path, scale: float) -> None:
        """Prepare fonts and paragraph styles."""
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle

        _registered()
        self.doc = doc
        self.assets = assets
        self.scale = scale
        self.fonts = font_policy(doc)
        theme = doc["theme"]
        self.accent = colors.HexColor(theme.get("accent", "#24476b"))
        slide = doc["page_size"] == "slide"
        size = float(theme.get("rl_size", 17 if slide else 9.5)) * scale
        self.size = size
        width, height = PAGE_SIZES[doc["page_size"]]
        self.margin = float(theme.get("rl_margin", 42 if slide else 50))
        self.frame_width = width - 2 * self.margin
        body, bold = self.fonts["body"], self.fonts["bold"]
        self.leading = 1.32
        cid = self.fonts["kind"] == "cid"
        wrap = "CJK" if cid else None
        base = {"fontName": body, "fontSize": size, "leading": size * self.leading, "wordWrap": wrap}
        self.styles = {
            "body": ParagraphStyle("body", spaceAfter=size * 0.55, **base),
            "small": ParagraphStyle("small", **{**base, "fontSize": size * 0.86, "leading": size * 0.86 * 1.3}, textColor=colors.HexColor("#444444"), spaceAfter=size * 0.4),
            "right": ParagraphStyle("right", alignment=2, spaceAfter=size * 0.5, **base),
            "center": ParagraphStyle("center", alignment=1, spaceAfter=size * 0.5, **base),
            "lead": ParagraphStyle("lead", **{**base, "fontSize": size * 1.12, "leading": size * 1.12 * 1.35}, spaceAfter=size * 0.6),
            "brand": ParagraphStyle("brand", **{**base, "fontName": bold, "fontSize": size * 1.6, "leading": size * 1.9}, textColor=self.accent),
            "h1": ParagraphStyle("h1", **{**base, "fontName": bold, "fontSize": size * 1.9, "leading": size * 2.25}, textColor=self.accent, spaceAfter=size * 0.6),
            "h2": ParagraphStyle("h2", **{**base, "fontName": bold, "fontSize": size * 1.35, "leading": size * 1.65}, textColor=self.accent, spaceBefore=size * 0.7, spaceAfter=size * 0.4),
            "h3": ParagraphStyle("h3", **{**base, "fontName": bold, "fontSize": size * 1.1, "leading": size * 1.4}, spaceBefore=size * 0.5, spaceAfter=size * 0.3),
            "cell": ParagraphStyle("cell", **{**base, "fontSize": size * 0.92, "leading": size * 0.92 * 1.22}),
            "cellr": ParagraphStyle("cellr", alignment=2, **{**base, "fontSize": size * 0.92, "leading": size * 0.92 * 1.22}),
            "cellc": ParagraphStyle("cellc", alignment=1, **{**base, "fontSize": size * 0.92, "leading": size * 0.92 * 1.22}),
            "head": ParagraphStyle("head", **{**base, "fontName": bold, "fontSize": size * 0.92, "leading": size * 0.92 * 1.22}),
            "caption": ParagraphStyle("caption", **{**base, "fontName": self.fonts["italic"], "fontSize": size * 0.82, "leading": size * 1.05}, textColor=colors.HexColor("#555555"), spaceBefore=2, spaceAfter=size * 0.7),
            "tcaption": ParagraphStyle("tcaption", **{**base, "fontName": bold, "fontSize": size * 0.95, "leading": size * 1.2}, spaceAfter=3),
            "footnote": ParagraphStyle("footnote", **{**base, "fontSize": size * 0.78, "leading": size * 1.0}, textColor=colors.HexColor("#444444"), spaceAfter=2),
            "code": ParagraphStyle("code", fontName=self.fonts["mono"], fontSize=size * 0.82, leading=size * 0.82 * 1.3),
            "list": ParagraphStyle("list", **base, spaceAfter=size * 0.15),
        }
        self.outline: list[tuple[int, str]] = []

    # ---------------------------------------------------------------- leaves

    def para(self, markup: str, style: str = "body") -> Any:
        """One paragraph flowable."""
        from reportlab.platypus import Paragraph

        return Paragraph(rl_markup(markup), self.styles[style])

    def heading(self, block: dict[str, Any]) -> Any:
        """Heading paragraph tagged for the outline."""
        flowable = self.para(block["text"], f"h{min(block['level'], 3)}")
        flowable._wild_outline = (block["level"], block["text"])  # noqa: SLF001 - read in afterFlowable
        return flowable

    def items(self, items: list[Any], ordered: bool, depth: int = 0) -> Any:
        """(Nested) list flowable."""
        from reportlab.platypus import ListFlowable, ListItem

        entries = []
        for entry in items:
            if isinstance(entry, dict):
                entries.append(ListItem([self.para(entry["text"], "list"), self.items(entry["items"], entry["ordered"], depth + 1)]))
            else:
                entries.append(ListItem(self.para(entry, "list")))
        kind = ("1", "a", "i")[depth % 3] if ordered else "bullet"
        return ListFlowable(entries, bulletType=kind, start=None if ordered else "•", leftIndent=self.size * 1.6,
                            bulletFontName="Helvetica" if self.fonts["kind"] == "cid" else self.fonts["body"], bulletFontSize=self.size * 0.95, spaceAfter=self.size * 0.4)

    def table(self, block: dict[str, Any]) -> list[Any]:
        """Ruled or borderless table with spans and right-aligned numerals."""
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle

        if block["rendering"] in {"chart_data", "screenshot"}:
            return []
        values = block["values"]
        cols = len(values[0])
        header_rows = block["header_rows"]
        align = block.get("align") or ["l"] * cols
        totals = set(block.get("total_rows") or [])
        data = []
        for r, row in enumerate(values):
            cells = []
            for c, value in enumerate(row):
                if value is None:
                    cells.append("")
                    continue
                style = "head" if r < header_rows or r in totals else {"r": "cellr", "c": "cellc"}.get(align[c], "cell")
                cells.append(self.para(value, style))
                if style == "head" and align[c] == "r":
                    cells[-1].style = cells[-1].style.clone("headr", alignment=2)
            data.append(cells)
        shares = block.get("widths") or [100 / cols] * cols
        width = self.frame_width * float(block.get("width_share", 1.0))
        commands: list[tuple[Any, ...]] = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                           ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
        for span in block["spans"]:
            if span["row_span"] > 1 or span["column_span"] > 1:
                c, r = span["column"], span["row"]
                commands.append(("SPAN", (c, r), (c + span["column_span"] - 1, r + span["row_span"] - 1)))
        if block["rendering"] == "ruled":
            commands += [("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8f98"))]
            if header_rows:
                commands.append(("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#e6ebf2")))
        else:
            if header_rows:
                commands.append(("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 1.1, self.accent))
            commands += [("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f4f5f7")) for r in range(header_rows + 1, len(values), 2)]
        for r in totals:
            commands.append(("LINEABOVE", (0, r), (-1, r), 1.2, colors.black))
        flow: list[Any] = []
        if block.get("caption"):
            flow.append(self.para(block["caption"], "tcaption"))
        table = Table(data, colWidths=[width * s / 100 for s in shares], repeatRows=header_rows, hAlign="LEFT")
        table.setStyle(TableStyle(commands))
        table.spaceAfter = self.size * 0.9
        flow.append(table)
        return flow

    def chart(self, spec: dict[str, Any], width: float) -> Any:
        """Native vector bar or line chart with real text labels."""
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.charts.legends import Legend
        from reportlab.graphics.charts.linecharts import HorizontalLineChart
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.lib import colors

        data = spec["spec"]
        height = width * spec["size"][1] / spec["size"][0]
        drawing = Drawing(width, height)
        chart = VerticalBarChart() if spec["type"] == "bar" else HorizontalLineChart()
        chart.x, chart.y = 46, 34
        chart.width, chart.height = width - 60, height - 70
        chart.data = [tuple(values) for _, values in data["series"]]
        chart.categoryAxis.categoryNames = list(data["categories"])
        font = self.fonts["body"]
        chart.categoryAxis.labels.fontName = chart.valueAxis.labels.fontName = font
        chart.categoryAxis.labels.fontSize = chart.valueAxis.labels.fontSize = 7.5
        chart.valueAxis.valueMin = data.get("min", 0)
        top = data.get("max") or max(max(v) for _, v in data["series"]) * 1.15
        chart.valueAxis.valueMax = top
        chart.valueAxis.valueStep = (top - data.get("min", 0)) / data.get("ticks", 4)
        chart.valueAxis.labelTextFormat = data["tick_format"]
        chart.valueAxis.visibleGrid = True
        chart.valueAxis.gridStrokeColor = colors.HexColor("#e3e3e3")
        palette = [colors.HexColor(c) for c in data.get("colors", ["#2f5d8a", "#e0a43a", "#6a9b5e", "#b0453f"])]
        for index in range(len(chart.data)):
            if spec["type"] == "bar":
                chart.bars[index].fillColor = palette[index % len(palette)]
                chart.bars[index].strokeColor = None
            else:
                chart.lines[index].strokeColor = palette[index % len(palette)]
                chart.lines[index].strokeWidth = 2
        drawing.add(chart)
        if data.get("title"):
            drawing.add(String(46, height - 14, data["title"], fontName=self.fonts["bold"], fontSize=9))
        legend = Legend()
        legend.x, legend.y = 46, 10
        legend.dx = legend.dy = 7
        legend.fontName, legend.fontSize = font, 7.5
        legend.alignment = "right"
        legend.columnMaximum = 1
        legend.deltax = 90
        legend.colorNamePairs = [(palette[i % len(palette)], name) for i, (name, _) in enumerate(data["series"])]
        drawing.add(legend)
        return drawing

    def figure_flowables(self, block: dict[str, Any]) -> list[Any]:
        """Image or chart plus caption."""
        from reportlab.platypus import Image

        width_cm = float(block.get("width_cm", 15.0))
        width = min(width_cm * 28.3465 * self.scale, self.frame_width)
        if block["figure_kind"] == "chart" and block.get("rl_vector"):
            item = self.chart(block["chart"], width)
        else:
            from PIL import Image as PILImage

            path = self.assets / block["src"]
            with PILImage.open(path) as image:
                px_w, px_h = image.size
            height = width * px_h / px_w
            item = Image(str(path), width=width, height=height)
        item.hAlign = "CENTER"
        flow = [item]
        if block.get("caption"):
            flow.append(self.para(block["caption"], "caption"))
        return flow

    def boxed(self, block: dict[str, Any]) -> Any:
        """Callout or sidebar as a shaded single-cell table."""
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle

        inner = []
        if block.get("title"):
            inner.append(self.para(f"**{block['title']}**", "body"))
        inner.append(self.para(block["text"], "body"))
        warn = "warn" in block.get("cls", "")
        edge = colors.HexColor("#c0392b" if warn else "#2b6cb0" if "note" in block.get("cls", "") else "#d08c2b")
        background = colors.HexColor("#fdf0ee" if warn else "#eef4fb" if "note" in block.get("cls", "") else "#fbf6ec")
        if block["kind"] == "sidebar":
            edge, background = self.accent, colors.HexColor("#f1f4f8")
        table = Table([[inner]], colWidths=[self.frame_width])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), background), ("LINEBEFORE", (0, 0), (0, -1), 3, edge),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5)]))
        table.spaceAfter = self.size * 0.8
        return table

    def code(self, block: dict[str, Any]) -> list[Any]:
        """Monospace code block on a grey panel."""
        from reportlab.lib import colors
        from reportlab.platypus import Preformatted, Table, TableStyle

        flow = []
        if block.get("caption"):
            flow.append(self.para(f"**{block['caption']}**", "small"))
        table = Table([[Preformatted(block["text"], self.styles["code"])]], colWidths=[self.frame_width])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f3f5")),
                                   ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9ccd2"))]))
        table.spaceAfter = self.size * 0.8
        flow.append(table)
        return flow

    def equation(self, block: dict[str, Any]) -> Any:
        """Centred linear equation with an optional right-aligned number."""
        from reportlab.platypus import Table, TableStyle

        table = Table([[self.para(block["text"], "center"), self.para(block["number"], "right")]],
                      colWidths=[self.frame_width - 50, 50])
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        table.spaceAfter = self.size * 0.5
        return table

    def form(self, block: dict[str, Any]) -> list[Any]:
        """AcroForm rows (widgets are created empty and filled afterwards)."""
        from reportlab.platypus import Flowable

        renderer = self

        class FormRow(Flowable):
            def __init__(self, fields: list[dict[str, Any]]) -> None:
                super().__init__()
                self.fields = fields
                tall = any(f.get("multiline") for f in fields)
                self.height = (58 if tall else 34) * renderer.scale + 6

            def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
                self.width = available_width
                return available_width, self.height

            def draw(self) -> None:
                canvas = self.canv
                total = sum(f["width"] for f in self.fields)
                x = 0.0
                label_size = 7.4 * renderer.scale
                for spec in self.fields:
                    share = self.width * spec["width"] / total
                    canvas.setFont(renderer.fonts["body"], label_size)
                    canvas.setFillColorRGB(0.25, 0.25, 0.25)
                    box_h = self.height - label_size - 8
                    if spec["field_type"] == "checkbox":
                        canvas.acroForm.checkbox(name=spec["name"], x=x, y=box_h / 2 - 5, size=11, buttonStyle="check",
                                                 borderColor=None, fillColor=None, relative=True, checked=False)
                        canvas.setFont(renderer.fonts["body"], 8.6 * renderer.scale)
                        canvas.setFillColorRGB(0, 0, 0)
                        canvas.drawString(x + 16, box_h / 2 - 3, spec["label"])
                    else:
                        canvas.drawString(x, self.height - label_size, spec["label"])
                        kwargs: dict[str, Any] = {"name": spec["name"], "x": x, "y": 2, "width": share - 10, "height": box_h - 2,
                                                  "relative": True, "borderWidth": 0.6, "fontName": "Helvetica", "fontSize": 0,
                                                  "tooltip": spec["label"]}
                        if spec["field_type"] == "choice":
                            canvas.acroForm.choice(value=spec["options"][0], options=list(spec["options"]), fieldFlags="combo", **kwargs)
                        else:
                            flags = []
                            if spec["field_type"] == "comb":
                                flags.append("comb")
                            if spec.get("multiline"):
                                flags.append("multiline")
                            canvas.acroForm.textfield(value="", fieldFlags=" ".join(flags), maxlen=spec["max_len"] or 400, **kwargs)
                    x += share

        flow: list[Any] = []
        if block["title"]:
            flow.append(self.heading({"level": 2, "text": block["title"]}))
        flow += [FormRow(row) for row in block["rows"]]
        return flow

    # ---------------------------------------------------------------- containers

    def columns_flow(self, columns: list[list[dict[str, Any]]]) -> Any:
        """Build each column's flowables at the column width (tables, boxes and figures size to it)."""
        full = self.frame_width
        self.frame_width = full / len(columns) - 10
        try:
            children = [self.flowables(column) for column in columns]
        finally:
            self.frame_width = full
        return self.side_by_side(children)

    def side_by_side(self, children: list[list[Any]], shares: list[float] | None = None) -> Any:
        """Lay out flowable lists in one table row."""
        from reportlab.platypus import Table, TableStyle

        shares = shares or [1 / len(children)] * len(children)
        table = Table([children], colWidths=[self.frame_width * s for s in shares])
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 10)]))
        table.spaceAfter = self.size * 0.5
        return table

    def flowables(self, blocks: list[dict[str, Any]]) -> list[Any]:
        """Flowables for a block list (wrap figures absorb following paragraphs)."""
        from reportlab.platypus import ImageAndFlowables, Table

        flow: list[Any] = []
        index = 0
        while index < len(blocks):
            block = blocks[index]
            kind = block["kind"]
            index += 1
            if kind == "figure" and block.get("wrap") in {"left", "right"}:
                taken = []
                while index < len(blocks) and blocks[index]["kind"] == "paragraph" and len(taken) < 3:
                    taken.append(self.para(blocks[index]["text"], "body"))
                    index += 1
                parts = self.figure_flowables(block)
                holder = Table([[p] for p in parts], colWidths=[parts[0].drawWidth if hasattr(parts[0], "drawWidth") else parts[0].width])
                holder._restrictSize = holder.wrap  # noqa: SLF001 - ImageAndFlowables expects an Image-like sizing hook
                flow.append(ImageAndFlowables(holder, taken, imageSide=block["wrap"], imageLeftPadding=8, imageRightPadding=8))
                continue
            flow += self.block(block)
        return flow

    def block(self, block: dict[str, Any]) -> list[Any]:
        """Flowables for one block."""
        kind = block["kind"]
        cls = block.get("cls", "")
        if kind == "heading":
            return [self.heading(block)]
        if kind == "paragraph":
            style = next((s for s in ("small", "right", "center", "lead", "brand") if s in cls.split()), "body")
            if "muted" in cls.split() or "meta" in cls.split():
                style = "small"
            return [self.para(block["text"], style)]
        if kind == "list":
            return [self.items(block["items"], block["ordered"])]
        if kind == "table":
            return self.table(block)
        if kind == "figure":
            return self.figure_flowables(block)
        if kind in {"callout", "sidebar"}:
            return [self.boxed(block)]
        if kind == "footnote":
            return [self.para(block["text"], "footnote")]
        if kind == "code":
            return self.code(block)
        if kind == "equation":
            return [self.equation(block)]
        if kind == "form":
            return self.form(block)
        if kind == "fields":
            return [self.para(f"**{label}:** {value}", "body") for label, value in block["items"]]
        if kind == "pair" or (kind == "group" and ("split" in cls or "letterhead" in cls)):
            return [self.columns_flow([[child] for child in block["blocks"]])]
        if kind == "columns":
            children = block["blocks"]
            count = block.get("count", 2)
            weights = [len(" ".join(_strings(child))) + 400 * (child["kind"] in {"figure", "table"}) for child in children]
            target, columns, acc = sum(weights) / count, [[] for _ in range(count)], 0.0
            for child, weight in zip(children, weights, strict=True):
                slot = min(int(acc / target) if target else 0, count - 1)
                columns[slot].append(child)
                acc += weight
            return [self.columns_flow(columns)]
        if kind == "group":
            return self.flowables(block["blocks"])
        raise ValueError(kind)


def render(doc: dict[str, Any], assets: Path, out: Path, scale: float = 1.0) -> int:
    """Write ``out`` and return its page count."""
    from reportlab import rl_config
    from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate

    renderer = Renderer(doc, assets, scale)
    width, height = PAGE_SIZES[doc["page_size"]]
    margin = renderer.margin
    meta = doc["metadata"]
    pages = len(doc["pages"])

    def decorate(canvas: Any, template: Any) -> None:
        number = canvas.getPageNumber()
        canvas.saveState()
        canvas.setFont(renderer.fonts["body"], 7.5)
        canvas.setFillColorRGB(0.4, 0.4, 0.4)
        if doc.get("running_header"):
            canvas.drawString(margin, height - margin * 0.55, doc["running_header"].format(page=number, pages=pages))
        if doc.get("running_footer"):
            canvas.drawCentredString(width / 2, margin * 0.45, doc["running_footer"].format(page=number, pages=pages))
        canvas.restoreState()

    class Template(BaseDocTemplate):
        def afterFlowable(self, flowable: Any) -> None:  # noqa: N802 - ReportLab hook name
            entry = getattr(flowable, "_wild_outline", None)
            if entry:
                level, title = entry
                previous = renderer.outline[-1][0] if renderer.outline else 0
                level = min(level, previous + 1)  # outlines cannot skip levels (h2 directly after h0)
                key = f"h{len(renderer.outline)}"
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(title, key, level=level - 1, closed=False)
                renderer.outline.append((level, title))

    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    from datetime import datetime

    os.environ["SOURCE_DATE_EPOCH"] = str(int(datetime.fromisoformat(meta["created"].replace("Z", "+00:00")).timestamp()))
    invariant = rl_config.invariant
    rl_config.invariant = 1
    try:
        template = Template(str(out), pagesize=(width, height), leftMargin=margin, rightMargin=margin, topMargin=margin,
                            bottomMargin=margin, title=meta["title"], author=meta["author"], subject=meta["subject"],
                            keywords=", ".join(meta["keywords"]), creator=doc.get("creator_tool", "ReportLab platypus"),
                            lang=meta["lang"], invariant=1)
        frame = Frame(margin, margin, width - 2 * margin, height - 2 * margin, id="body", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        template.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=decorate)])
        story: list[Any] = []
        for index, blocks in enumerate(doc["pages"]):
            if index:
                story.append(PageBreak())
            story += renderer.flowables(blocks)
        template.build(story)
    finally:
        rl_config.invariant = invariant
        if epoch is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = epoch
    return template.page
