"""Render wild-v2 documents to flat ODF for LibreOffice Writer.

Extends the wild-v1 FODT writer with hard page breaks, nested lists, code
blocks, LibreOffice Math objects (MathML with a StarMath annotation) and 16:9
pages. ``scale`` multiplies every font size and frame width so an overflowing
document can be shrunk uniformly.
"""

# ruff: noqa: E501, FBT001, ARG002, TRY003, EM101
from __future__ import annotations

import re
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from bench.wild_templates import fodt_render
from bench.wild_templates.fodt_render import FodtWriter, inline, x

if TYPE_CHECKING:
    from pathlib import Path

MATH_NS = 'xmlns:math="http://www.w3.org/1998/Math/MathML" '

EXTRA_STYLES = (
    '<style:style style:name="PageBreak" style:family="paragraph" style:parent-style-name="Standard">'
    '<style:paragraph-properties fo:break-before="page" fo:margin-top="0cm" fo:margin-bottom="0cm" fo:line-height="0.05cm"/>'
    '<style:text-properties fo:font-size="1pt" style:font-size-asian="1pt" style:font-size-complex="1pt"/></style:style>'
    '<style:style style:name="Code" style:family="paragraph" style:parent-style-name="Standard">'
    '<style:paragraph-properties fo:margin-top="0cm" fo:margin-bottom="0cm" fo:line-height="118%" fo:background-color="#f2f3f5" '
    'fo:padding-left="0.2cm" fo:padding-right="0.2cm" fo:border-left="0.5pt solid #c9ccd2" fo:border-right="0.5pt solid #c9ccd2" '
    'style:join-border="true" fo:text-align="start" style:writing-mode="lr-tb"/>'
    '<style:text-properties style:font-name="Noto Sans Mono" fo:font-size="8.5pt" style:font-name-asian="Noto Sans Mono" '
    'style:font-name-complex="Noto Sans Mono" style:font-size-asian="8.5pt" style:font-size-complex="8.5pt"/></style:style>'
    '<style:style style:name="CodeCaption" style:family="paragraph" style:parent-style-name="Body">'
    '<style:paragraph-properties fo:keep-with-next="always" fo:margin-top="0.15cm" fo:margin-bottom="0.05cm"/>'
    '<style:text-properties fo:font-size="8.5pt" fo:font-weight="bold" fo:color="#555555"/></style:style>'
    '<style:style style:name="CodeEnd" style:family="paragraph" style:parent-style-name="Standard">'
    '<style:paragraph-properties fo:margin-bottom="0.2cm" fo:line-height="0.1cm"/><style:text-properties fo:font-size="2pt"/></style:style>'
    '<style:style style:name="Equation" style:family="paragraph" style:parent-style-name="Body">'
    '<style:paragraph-properties fo:text-align="center" fo:margin-top="0.15cm" fo:margin-bottom="0.3cm" style:writing-mode="lr-tb"/></style:style>'
    '<style:style style:name="Formula" style:family="graphic"><style:graphic-properties style:vertical-pos="middle" '
    'style:vertical-rel="text" fo:margin-left="0.1cm" fo:margin-right="0.1cm" fo:border="none" fo:padding="0cm"/></style:style>'
    '<text:list-style style:name="LLegal">'
    + "".join(
        f'<text:list-level-style-number text:level="{n}" style:num-suffix="{suffix}" style:num-prefix="{prefix}" style:num-format="{fmt}"'
        f'{display}><style:list-level-properties text:list-level-position-and-space-mode="label-alignment">'
        f'<style:list-level-label-alignment text:label-followed-by="listtab" text:list-tab-stop-position="{0.8 * n + 0.2:.2f}cm" '
        f'fo:text-indent="-0.8cm" fo:margin-left="{0.8 * n + 0.2:.2f}cm"/></style:list-level-properties></text:list-level-style-number>'
        for n, prefix, suffix, fmt, display in ((1, "", ".", "1", ""), (2, "", "", "1", ' text:display-levels="2"'),
                                                (3, "(", ")", "a", ""), (4, "(", ")", "i", "")))
    + "</text:list-style>"
)
_SIZE = re.compile(r'((?:fo:font-size|style:font-size-asian|style:font-size-complex)=")([0-9.]+)pt"')


def _code_line(line: str) -> str:
    out = []
    for run in re.split(r"( {2,}|\t)", line):
        if run == "\t":
            out.append("<text:tab/>")
        elif run.startswith("  ") and not run.strip():
            out.append(f'<text:s text:c="{len(run)}"/>')
        else:
            out.append(x(run))
    return "".join(out)


def _math(block: dict[str, Any], scale: float) -> str:
    body = re.sub(r"<(/?)([a-zA-Z]+)", r"<\1math:\2", block["mathml"])
    visible = len(re.sub(r"\s", "", block["text"]))
    tall = any(tag in block["mathml"] for tag in ("<mfrac", "<munderover", "<msubsup", "<mtable"))
    width = max(1.2, 0.24 * visible) * scale
    height = (1.35 if tall else 0.6) * scale
    annotation = f'<math:annotation encoding="StarMath 5.0">{x(block["starmath"])}</math:annotation>'
    return (f'<draw:frame draw:style-name="Formula" text:anchor-type="as-char" svg:width="{width:.2f}cm" svg:height="{height:.2f}cm" draw:z-index="1">'
            f'<draw:object><math:math display="block"><math:semantics><math:mrow>{body}</math:mrow>{annotation}</math:semantics></math:math>'
            "</draw:object></draw:frame>")


class Writer(FodtWriter):
    """FODT writer with the wild-v2 block kinds."""

    def __init__(self, doc: dict[str, Any], assets: Path, scale: float) -> None:
        """Bind the document, assets and fit scale."""
        super().__init__(doc, assets)
        self.scale = scale

    def items(self, items: list[Any], ordered: bool, style: str | None) -> str:
        """Emit a (possibly nested) list."""
        parts = []
        for entry in items:
            if isinstance(entry, dict):
                parts.append(f'<text:list-item><text:p text:style-name="ListPara">{inline(entry["text"])}</text:p>'
                             f"{self.items(entry['items'], entry['ordered'], None)}</text:list-item>")
            else:
                parts.append(f'<text:list-item><text:p text:style-name="ListPara">{inline(entry)}</text:p></text:list-item>')
        attr = f' text:style-name="{style}"' if style else ""
        return f"<text:list{attr}>{''.join(parts)}</text:list>"

    def block(self, block: dict[str, Any]) -> str:
        """Emit one authored block."""
        kind = block["kind"]
        if kind == "list":
            nested = any(isinstance(entry, dict) for entry in block["items"])
            style = ("LLegal" if nested else "LNum") if block["ordered"] else "LBullet"
            return self.items(block["items"], block["ordered"], style)
        if kind == "code":
            caption = f'<text:p text:style-name="CodeCaption">{inline(block["caption"])}</text:p>' if block.get("caption") else ""
            lines = "".join(f'<text:p text:style-name="Code">{_code_line(line)}</text:p>' for line in block["text"].split("\n"))
            return caption + lines + '<text:p text:style-name="CodeEnd"/>'
        if kind == "equation":
            number = f"<text:tab/>{x(block['number'])}" if block["number"] else ""
            return f'<text:p text:style-name="Equation">{_math(block, self.scale)}{number}</text:p>'
        if kind == "form":
            raise ValueError("AcroForm sections are only produced by the ReportLab renderer")
        if kind == "figure":
            block = {**block, "width_cm": block.get("width_cm", 7.0) * self.scale}
        if kind == "table" and block.get("width_cm"):
            block = {**block, "width_cm": block["width_cm"] * self.scale}
        return super().block(block)


def document_fodt(doc: dict[str, Any], assets: Path, scale: float = 1.0) -> str:
    """Render the complete FODT with explicit page breaks between authored pages."""
    shell = deepcopy({k: v for k, v in doc.items() if k != "pages"})
    shell["blocks"] = []
    slide = doc["page_size"] == "slide"
    if slide:
        shell["page_size"] = "A4"
    writer = Writer(doc, assets, scale)
    pages = []
    for index, blocks in enumerate(doc["pages"]):
        prefix = '<text:p text:style-name="PageBreak"/>' if index else ""
        pages.append(prefix + "".join(writer.block(b) for b in blocks))
    body = "".join(pages)
    text = fodt_render.document_fodt(shell, assets)
    text = text.replace("<office:document ", f"<office:document {MATH_NS}", 1)
    text = text.replace("</office:styles>", EXTRA_STYLES + "</office:styles>", 1)
    text = text.replace("</office:automatic-styles>", "".join(writer.auto) + "</office:automatic-styles>", 1)
    text = text.replace("<office:text></office:text>", f"<office:text>{body}</office:text>", 1)
    if slide:
        text = text.replace('fo:page-width="21.0cm" fo:page-height="29.7cm"', 'fo:page-width="33.867cm" fo:page-height="19.05cm"')
        text = text.replace('style:print-orientation="portrait"', 'style:print-orientation="landscape"')
    if scale != 1.0:
        text = _SIZE.sub(lambda m: f'{m.group(1)}{float(m.group(2)) * scale:.2f}pt"', text)
    return text
