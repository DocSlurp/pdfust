"""Render authored wild-v1 documents to flat ODF text (FODT) for LibreOffice Writer.

Flat ODF gives exact control over page size, running header/footer fields,
heading outline levels (exported as bookmarks), wrapped image frames, table
spans and per-script fonts/languages. Images are embedded as base64.
"""

# ruff: noqa: E501, C901, PLR0911, PLR0912, PLC0415, ISC004
from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import escape

from bench.wild_templates.model import tokens

if TYPE_CHECKING:
    from pathlib import Path

PAGE_SIZES = {"Letter": ("21.59cm", "27.94cm"), "A4": ("21.0cm", "29.7cm")}
NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
      'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
      'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
      'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
      'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
      'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
      'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" '
      'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
      'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
      'xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0"')
ASIAN = {"ja": ("Noto Sans CJK JP", "ja", "JP"), "zh-CN": ("Noto Sans CJK SC", "zh", "CN"),
         "zh-TW": ("Noto Sans CJK TC", "zh", "TW"), "ko": ("Noto Sans CJK KR", "ko", "KR")}
# Noto Sans Hebrew has no digits; LibreOffice then draws RTL-context digits with broken fallback
# advances, so Hebrew uses Liberation Sans (Hebrew plus digits) for the complex-script slot.
COMPLEX = {"he": ("Liberation Sans", "he", "IL"), "ar": ("Noto Naskh Arabic", "ar", "SA"),
           "th": ("Noto Sans Thai", "th", "TH"), "hi": ("Noto Sans Devanagari", "hi", "IN")}


def x(text: str) -> str:
    """Escape XML text, keeping line breaks as ODF line breaks."""
    return escape(text, {'"': "&quot;"}).replace("\n", "<text:line-break/>")


def inline(markup: str) -> str:
    """Render inline markup to ODF spans and links."""
    out = []
    for style, text, href in tokens(markup):
        if style == "bold":
            out.append(f'<text:span text:style-name="Strong">{x(text)}</text:span>')
        elif style == "italic":
            out.append(f'<text:span text:style-name="Emph">{x(text)}</text:span>')
        elif style == "link":
            out.append(f'<text:a xlink:type="simple" xlink:href="{x(href or "")}" text:style-name="Link">{x(text)}</text:a>')
        else:
            out.append(x(text))
    return "".join(out)


def _footer_fields(template: str) -> str:
    text = x(template)
    text = text.replace("{pages}", '<text:page-count style:num-format="1">1</text:page-count>')
    return text.replace("{page}", '<text:page-number style:num-format="1" text:select-page="current">1</text:page-number>')


class FodtWriter:
    """Accumulate automatic styles while emitting body XML."""

    def __init__(self, doc: dict[str, Any], assets: Path) -> None:
        """Bind one document and its assets directory."""
        self.doc = doc
        self.assets = assets
        self.auto: list[str] = []
        self.tables = 0
        self.frames = 0
        self.sections = 0
        self.rtl = doc.get("dir") == "rtl"
        self.content_width = float(doc["theme"].get("content_cm", 17.0))

    def table(self, block: dict[str, Any]) -> str:
        """Emit one table with column widths, borders and spans."""
        if block["rendering"] in {"chart_data", "screenshot"}:
            return ""  # values exist only inside the preceding chart or screenshot image
        self.tables += 1
        name = f"Tbl{self.tables}"
        values = block["values"]
        cols = len(values[0])
        width = block.get("width_cm", self.content_width)
        widths = block.get("widths") or [100 / cols] * cols
        ruled = block["rendering"] == "ruled"
        mode = ' style:writing-mode="rl-tb"' if self.rtl else ""
        self.auto.append(f'<style:style style:name="{name}" style:family="table"><style:table-properties style:width="{width:.2f}cm" table:align="margins" fo:margin-bottom="0.3cm"{mode}/></style:style>')
        for c, share in enumerate(widths):
            self.auto.append(f'<style:style style:name="{name}.C{c}" style:family="table-column"><style:table-column-properties style:column-width="{width * share / 100:.2f}cm" style:rel-column-width="{int(share * 100)}*"/></style:style>')
        border = "0.5pt solid #7f858d"
        if ruled:
            self.auto.append(f'<style:style style:name="{name}.H" style:family="table-cell"><style:table-cell-properties fo:padding="0.08cm" fo:border="{border}" fo:background-color="#e4eaf2"/></style:style>')
            self.auto.append(f'<style:style style:name="{name}.D" style:family="table-cell"><style:table-cell-properties fo:padding="0.08cm" fo:border="{border}"/></style:style>')
        else:
            self.auto.append(f'<style:style style:name="{name}.H" style:family="table-cell"><style:table-cell-properties fo:padding="0.08cm" fo:border="none" fo:border-bottom="1.1pt solid #24476b"/></style:style>')
            self.auto.append(f'<style:style style:name="{name}.D" style:family="table-cell"><style:table-cell-properties fo:padding="0.08cm" fo:border="none"/></style:style>')
        self.auto.append(f'<style:style style:name="{name}.T" style:family="table-cell"><style:table-cell-properties fo:padding="0.08cm" fo:border="{border if ruled else "none"}" fo:border-top="1.4pt solid #333333"/></style:style>')
        spans = {(s["row"], s["column"]): s for s in block["spans"]}
        align = block.get("align") or ["l"] * cols
        total_rows = set(block.get("total_rows", []))
        out = []
        if block.get("caption"):
            out.append(f'<text:p text:style-name="TableCaption">{inline(block["caption"])}</text:p>')
        out.append(f'<table:table table:name="{name}" table:style-name="{name}">')
        out += [f'<table:table-column table:style-name="{name}.C{c}"/>' for c in range(cols)]
        for r, row in enumerate(values):
            header = r < block["header_rows"]
            if r == 0 and header:
                out.append("<table:table-header-rows>")
            out.append("<table:table-row>")
            for c, value in enumerate(row):
                if value is None:
                    out.append("<table:covered-table-cell/>")
                    continue
                span = spans[(r, c)]
                attrs = ""
                if span["column_span"] > 1:
                    attrs += f' table:number-columns-spanned="{span["column_span"]}"'
                if span["row_span"] > 1:
                    attrs += f' table:number-rows-spanned="{span["row_span"]}"'
                style = "H" if header else "T" if r in total_rows else "D"
                para = "TableHeading" if header else "TableTotal" if r in total_rows else "TableContents"
                if align[c] == "r" and span["column_span"] == 1 and not header:
                    para += "Right"
                elif span["column_span"] > 1:
                    para = "TableHeading"
                out.append(f'<table:table-cell table:style-name="{name}.{style}" office:value-type="string"{attrs}>'
                           f'<text:p text:style-name="{para}">{x(value)}</text:p></table:table-cell>')
            out.append("</table:table-row>")
            if header and r == block["header_rows"] - 1:
                out.append("</table:table-header-rows>")
        out.append("</table:table>")
        return "".join(out)

    def figure(self, block: dict[str, Any]) -> str:
        """Emit a wrapped (or centred) frame holding the image and its caption."""
        from PIL import Image

        self.frames += 1
        path = self.assets / block["src"]
        with Image.open(path) as image:
            px_w, px_h = image.size
        width = block.get("width_cm", 7.0)
        height = width * px_h / px_w
        data = base64.b64encode(path.read_bytes()).decode()
        wrap = block.get("wrap", "none")
        if self.rtl and wrap in {"left", "right"}:
            wrap = "right" if wrap == "left" else "left"
        # ODF wrap names the side where text flows: a frame floated left lets text run on its right.
        odf_wrap, pos = {"left": ("right", "left"), "right": ("left", "right")}.get(wrap, ("none", "center"))
        name = f"fr{self.frames}"
        self.auto.append(f'<style:style style:name="{name}" style:family="graphic" style:parent-style-name="Frame"><style:graphic-properties draw:fill="none" style:wrap="{odf_wrap}" '
                         f'style:number-wrapped-paragraphs="no-limit" fo:margin-left="0.35cm" fo:margin-right="0.35cm" fo:margin-top="0.1cm" '
                         f'fo:margin-bottom="0.25cm" style:vertical-pos="top" style:vertical-rel="paragraph" style:horizontal-pos="{pos}" '
                         f'style:horizontal-rel="paragraph" fo:border="none" fo:padding="0cm"/></style:style>')
        self.auto.append(f'<style:style style:name="{name}i" style:family="graphic" style:parent-style-name="Graphics"><style:graphic-properties draw:fill="none" style:vertical-pos="top" style:vertical-rel="baseline" fo:border="none"/></style:style>')
        caption = f'<text:p text:style-name="Caption">{inline(block["caption"])}</text:p>' if block.get("caption") else ""
        box_height = height + (0.9 if caption else 0.1)
        image = (f'<draw:frame draw:style-name="{name}i" draw:name="Image{self.frames}" text:anchor-type="as-char" svg:width="{width:.2f}cm" '
                 f'svg:height="{height:.2f}cm" draw:z-index="1"><draw:image draw:mime-type="{"image/png" if path.suffix == ".png" else "image/jpeg"}">'
                 f'<office:binary-data>{data}</office:binary-data></draw:image><svg:title>{x(block.get("alt", ""))}</svg:title></draw:frame>')
        return (f'<text:p text:style-name="Body"><draw:frame draw:style-name="{name}" draw:name="Figure{self.frames}" text:anchor-type="paragraph" '
                f'svg:width="{width:.2f}cm" draw:z-index="0"><draw:text-box fo:min-height="{box_height:.2f}cm">'
                f'<text:p text:style-name="FigureImage">{image}</text:p>{caption}</draw:text-box></draw:frame></text:p>')

    def block(self, block: dict[str, Any]) -> str:
        """Emit one authored block."""
        kind = block["kind"]
        style = {"small": "Small", "right": "BodyRight", "lead": "Lead", "brand": "Brand", "meta": "Small",
                 "muted": "Small"}.get(block.get("cls", ""), "Body")
        if kind == "heading":
            return f'<text:h text:style-name="Heading_20_{block["level"]}" text:outline-level="{block["level"]}">{inline(block["text"])}</text:h>'
        if kind == "paragraph":
            return f'<text:p text:style-name="{style}">{inline(block["text"])}</text:p>'
        if kind == "list":
            list_style = "LNum" if block["ordered"] else "LBullet"
            items = "".join(f'<text:list-item><text:p text:style-name="ListPara">{inline(i)}</text:p></text:list-item>' for i in block["items"])
            return f'<text:list text:style-name="{list_style}">{items}</text:list>'
        if kind == "table":
            return self.table(block)
        if kind == "figure":
            return self.figure(block)
        if kind in {"sidebar", "callout"}:
            para = "Sidebar" if kind == "sidebar" else "Callout"
            title = f'<text:p text:style-name="{para}Title">{inline(block["title"])}</text:p>' if block.get("title") else ""
            return f'{title}<text:p text:style-name="{para}">{inline(block["text"])}</text:p>'
        if kind == "footnote":
            return f'<text:p text:style-name="Footnote">{inline(block["text"])}</text:p>'
        if kind == "fields":
            return "".join(f'<text:p text:style-name="Field"><text:span text:style-name="Strong">{x(label)}:</text:span><text:tab/>'
                           f'<text:span text:style-name="FieldValue">{x(value)}</text:span></text:p>' for label, value in block["items"])
        if kind in {"columns", "pair"}:
            self.sections += 1
            name = f"Sect{self.sections}"
            count = block.get("count", 2)
            self.auto.append(f'<style:style style:name="{name}" style:family="section"><style:section-properties text:dont-balance-text-columns="false">'
                             f'<style:columns fo:column-count="{count}" fo:column-gap="0.6cm"/></style:section-properties></style:style>')
            parts = []
            for index, child in enumerate(block["blocks"]):
                if kind == "pair" and index:
                    parts.append('<text:p text:style-name="ColumnBreak"/>')
                parts.append(self.block(child))
            return f'<text:section text:style-name="{name}" text:name="{name}">{"".join(parts)}</text:section>'
        if kind == "group":
            return "".join(self.block(child) for child in block["blocks"])
        if kind in {"header", "footer"}:
            return ""
        raise ValueError(kind)


def document_fodt(doc: dict[str, Any], assets: Path) -> str:
    """Render one complete FODT document including metadata, styles and master page."""
    writer = FodtWriter(doc, assets)
    body = "".join(writer.block(b) for b in doc["blocks"])
    meta = doc["metadata"]
    lang = meta["lang"]
    base = lang.split("-")[0]
    theme = doc["theme"]
    western_font = theme.get("lo_font", "Noto Serif")
    heading_font = theme.get("lo_heading_font", "Noto Sans")
    western_lang, _, western_country = lang.partition("-")
    asian = ASIAN.get(lang, ASIAN["ja"])
    complex_ = COMPLEX.get(base, COMPLEX["he"])
    if lang in ASIAN:
        western_lang, western_country = "en", "US"
    rtl = doc.get("dir") == "rtl"
    mode = "rl-tb" if rtl else "lr-tb"
    align = "end" if rtl else "start"
    width, height = PAGE_SIZES[doc["page_size"]]
    accent = theme.get("accent", "#24476b")
    keywords = "".join(f"<meta:keyword>{x(k)}</meta:keyword>" for k in meta["keywords"])
    fonts = sorted({western_font, heading_font, "Noto Sans", "Noto Serif", "Noto Sans Mono", asian[0], complex_[0]})
    font_decls = "".join(f'<style:font-face style:name="{f}" svg:font-family="&apos;{f}&apos;"/>' for f in fonts)
    text_props = (f'style:font-name="{western_font}" fo:font-size="{theme.get("lo_size", "10pt")}" fo:language="{western_lang}" '
                  f'fo:country="{western_country or "US"}" style:font-name-asian="{asian[0]}" style:language-asian="{asian[1]}" '
                  f'style:country-asian="{asian[2]}" style:font-size-asian="{theme.get("lo_size", "10pt")}" style:font-name-complex="{complex_[0]}" '
                  f'style:language-complex="{complex_[1]}" style:country-complex="{complex_[2]}" style:font-size-complex="{theme.get("lo_size", "10pt")}"')

    def para(name: str, parent: str = "Body", ppr: str = "", tpr: str = "", extra: str = "") -> str:
        return (f'<style:style style:name="{name}" style:family="paragraph" style:parent-style-name="{parent}"{extra}>'
                f'<style:paragraph-properties {ppr}/><style:text-properties {tpr}/></style:style>')

    def heading(level: int, size: str) -> str:
        return (f'<style:style style:name="Heading_20_{level}" style:display-name="Heading {level}" style:family="paragraph" '
                f'style:parent-style-name="Standard" style:next-style-name="Body" style:default-outline-level="{level}" style:class="text">'
                f'<style:paragraph-properties fo:margin-top="{0.5 if level > 1 else 0.1}cm" fo:margin-bottom="0.18cm" fo:keep-with-next="always" fo:text-align="{align}"/>'
                f'<style:text-properties style:font-name="{heading_font}" fo:font-size="{size}" fo:font-weight="bold" fo:color="{accent}" '
                f'style:font-size-asian="{size}" style:font-weight-asian="bold" style:font-size-complex="{size}" style:font-weight-complex="bold"/></style:style>')

    border_box = 'fo:padding="0.2cm" fo:border-left="2.5pt solid #d08c2b" fo:background-color="#fbf6ec" fo:margin-top="0.15cm"'
    side_box = f'fo:padding="0.2cm" fo:border-top="2pt solid {accent}" fo:background-color="#f1f4f8" fo:margin-top="0.15cm"'
    styles = "".join([
        f'<style:default-style style:family="paragraph"><style:paragraph-properties style:writing-mode="{mode}" fo:hyphenation-ladder-count="no-limit"/>'
        f'<style:text-properties {text_props} fo:hyphenate="false"/></style:default-style>',
        '<style:style style:name="Standard" style:family="paragraph" style:class="text"/>',
        '<style:style style:name="Frame" style:family="graphic"><style:graphic-properties text:anchor-type="paragraph" '
        'style:wrap="parallel" style:number-wrapped-paragraphs="no-limit" style:vertical-pos="top" style:vertical-rel="paragraph" '
        'style:horizontal-pos="center" style:horizontal-rel="paragraph" draw:fill="none" fo:border="none" fo:padding="0cm"/></style:style>',
        '<style:style style:name="Graphics" style:family="graphic"><style:graphic-properties text:anchor-type="as-char" '
        'style:vertical-pos="top" style:vertical-rel="baseline" draw:fill="none" fo:border="none" fo:padding="0cm"/></style:style>',
        para("Body", "Standard", f'fo:margin-top="0cm" fo:margin-bottom="0.2cm" fo:line-height="128%" fo:text-align="{align}" style:writing-mode="{mode}"'),
        para("BodyRight", "Body", 'fo:text-align="end"'),
        para("Lead", "Body", "", 'fo:font-size="11.5pt" fo:color="#333333"'),
        para("Brand", "Body", "", f'style:font-name="{heading_font}" fo:font-size="16pt" fo:font-weight="bold" fo:color="{accent}"'),
        para("Small", "Body", "", 'fo:font-size="8.5pt" fo:color="#444444" style:font-size-complex="8.5pt" style:font-size-asian="8.5pt"'),
        para("ListPara", "Body", 'fo:margin-bottom="0.08cm"'),
        para("Caption", "Body", 'fo:margin-top="0.1cm"', 'fo:font-size="8.5pt" fo:font-style="italic" fo:color="#555555" style:font-size-complex="8.5pt"'),
        para("FigureImage", "Body", 'fo:text-align="center" fo:margin-bottom="0cm"'),
        para("TableCaption", "Body", 'fo:keep-with-next="always" fo:margin-top="0.2cm" fo:margin-bottom="0.1cm"', 'fo:font-weight="bold" style:font-weight-complex="bold" style:font-weight-asian="bold"'),
        para("TableContents", "Body", f'fo:margin-bottom="0cm" fo:line-height="115%" fo:text-align="{align}"', 'fo:font-size="9pt" style:font-size-complex="9pt" style:font-size-asian="9pt"'),
        para("TableContentsRight", "TableContents", 'fo:text-align="end"'),
        para("TableHeading", "TableContents", 'fo:text-align="center"', 'fo:font-weight="bold" style:font-weight-complex="bold" style:font-weight-asian="bold"'),
        para("TableTotal", "TableContents", "", 'fo:font-weight="bold" style:font-weight-complex="bold"'),
        para("TableTotalRight", "TableTotal", 'fo:text-align="end"'),
        para("Sidebar", "Body", side_box, 'fo:font-size="9pt" style:font-size-complex="9pt" style:font-size-asian="9pt"'),
        para("SidebarTitle", "Sidebar", 'fo:keep-with-next="always"', f'fo:font-weight="bold" fo:color="{accent}" style:font-weight-complex="bold"'),
        para("Callout", "Body", border_box),
        para("CalloutTitle", "Callout", 'fo:keep-with-next="always"', 'fo:font-weight="bold" style:font-weight-complex="bold"'),
        para("Footnote", "Body", 'fo:margin-bottom="0.05cm"', 'fo:font-size="8pt" fo:color="#444444" style:font-size-complex="8pt" style:font-size-asian="8pt"'),
        para("Field", "Body", 'fo:padding-bottom="0.05cm" fo:border-bottom="0.5pt solid #888888" fo:margin-bottom="0.25cm"'),
        para("ColumnBreak", "Body", 'fo:break-before="column"'),
        para("Header", "Standard", f'fo:text-align="{"start" if rtl else "end"}" style:writing-mode="{mode}"', 'fo:font-size="8pt" fo:color="#666666" style:font-size-complex="8pt" style:font-size-asian="8pt"'),
        para("Footer", "Standard", 'fo:text-align="center"', 'fo:font-size="8pt" fo:color="#666666" style:font-size-complex="8pt" style:font-size-asian="8pt"'),
        heading(1, "19pt"), heading(2, "13.5pt"), heading(3, "11pt"),
        '<style:style style:name="Strong" style:family="text"><style:text-properties fo:font-weight="bold" style:font-weight-asian="bold" style:font-weight-complex="bold"/></style:style>',
        '<style:style style:name="Emph" style:family="text"><style:text-properties fo:font-style="italic" style:font-style-asian="italic" style:font-style-complex="italic"/></style:style>',
        f'<style:style style:name="Link" style:family="text"><style:text-properties fo:color="{accent}" style:text-underline-style="solid" style:text-underline-width="auto" style:text-underline-color="font-color"/></style:style>',
        '<style:style style:name="FieldValue" style:family="text"><style:text-properties style:font-name="Noto Sans Mono"/></style:style>',
        '<text:outline-style style:name="Outline">' + "".join(
            f'<text:outline-level-style text:level="{n}" style:num-format=""><style:list-level-properties/></text:outline-level-style>' for n in range(1, 11)) + "</text:outline-style>",
        '<text:list-style style:name="LBullet">' + "".join(
            f'<text:list-level-style-bullet text:level="{n}" text:bullet-char="•"><style:list-level-properties text:list-level-position-and-space-mode="label-alignment">'
            f'<style:list-level-label-alignment text:label-followed-by="listtab" text:list-tab-stop-position="{0.5 * n + 0.1:.2f}cm" fo:text-indent="-0.4cm" fo:margin-left="{0.5 * n + 0.1:.2f}cm"/>'
            '</style:list-level-properties></text:list-level-style-bullet>' for n in range(1, 4)) + "</text:list-style>",
        '<text:list-style style:name="LNum">' + "".join(
            f'<text:list-level-style-number text:level="{n}" style:num-suffix="." style:num-format="1"><style:list-level-properties text:list-level-position-and-space-mode="label-alignment">'
            f'<style:list-level-label-alignment text:label-followed-by="listtab" text:list-tab-stop-position="{0.6 * n + 0.1:.2f}cm" fo:text-indent="-0.5cm" fo:margin-left="{0.6 * n + 0.1:.2f}cm"/>'
            '</style:list-level-properties></text:list-level-style-number>' for n in range(1, 4)) + "</text:list-style>",
    ])
    margin = theme.get("lo_margin", "1.9cm")
    page_layout = (f'<style:page-layout style:name="pm1"><style:page-layout-properties fo:page-width="{width}" fo:page-height="{height}" '
                   f'style:print-orientation="portrait" fo:margin-top="1.3cm" fo:margin-bottom="1.2cm" fo:margin-left="{margin}" fo:margin-right="{margin}" '
                   f'style:writing-mode="{mode}"/><style:header-style><style:header-footer-properties fo:min-height="0.5cm" fo:margin-bottom="0.4cm"/>'
                   f'</style:header-style><style:footer-style><style:header-footer-properties fo:min-height="0.5cm" fo:margin-top="0.4cm"/></style:footer-style></style:page-layout>')
    header = f'<style:header><text:p text:style-name="Header">{_footer_fields(doc["running_header"])}</text:p></style:header>' if doc.get("running_header") else ""
    footer = f'<style:footer><text:p text:style-name="Footer">{_footer_fields(doc["running_footer"])}</text:p></style:footer>' if doc.get("running_footer") else ""
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<office:document {NS} office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">'
            f'<office:meta><dc:title>{x(meta["title"])}</dc:title><dc:subject>{x(meta["subject"])}</dc:subject>{keywords}'
            f'<meta:initial-creator>{x(meta["author"])}</meta:initial-creator><dc:creator>{x(meta["author"])}</dc:creator>'
            f'<meta:creation-date>{meta["created"].rstrip("Z")}</meta:creation-date><dc:date>{meta["created"].rstrip("Z")}</dc:date>'
            f'<dc:language>{x(lang)}</dc:language></office:meta>'
            f'<office:font-face-decls>{font_decls}</office:font-face-decls><office:styles>{styles}</office:styles>'
            f'<office:automatic-styles>{page_layout}{"".join(writer.auto)}</office:automatic-styles>'
            f'<office:master-styles><style:master-page style:name="Standard" style:page-layout-name="pm1">{header}{footer}</style:master-page></office:master-styles>'
            f'<office:body><office:text>{body}</office:text></office:body></office:document>')
