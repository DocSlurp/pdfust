"""Render wild-v2 documents to print HTML for headless Chromium (tagged PDF output).

Reuses the wild-v1 print stylesheet and leaf renderers, adding explicit page
sections, nested lists, code blocks, MathML equations and 16:9 slides.
"""

# ruff: noqa: E501, PLR0911, FBT001, TRY003, EM101
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from bench.wild_templates import html_render
from bench.wild_templates.html_render import e, inline

PAGE_SIZES = {"A4": "A4", "Letter": "Letter", "slide": "338.67mm 190.5mm"}

EXTRA_CSS = """
section.pg { break-after: page; position: relative; }
section.pg:last-child { break-after: auto; }
pre.code { font-family: 'Noto Sans Mono', 'JetBrainsMono Nerd Font', monospace; font-size: .82em; background: #f4f5f7;
  border: .6pt solid #d5d8de; border-radius: 3px; padding: 6px 8px; white-space: pre-wrap; margin: .3em 0 .8em; line-height: 1.32; }
p.codecap { font-size: .8em; color: #555; margin: .5em 0 .1em; font-weight: 600; }
div.eq { display: flex; align-items: center; margin: .5em 0 .8em; }
div.eq math { flex: 1; font-size: 1.12em; }
div.eq span.no { width: 3em; text-align: end; }
ol ol { list-style-type: lower-alpha; } ol ol ol { list-style-type: lower-roman; }
ul ul { list-style-type: circle; }
.callout.warn { border-inline-start-color: #c0392b; background: #fdf0ee; }
.callout.note { border-inline-start-color: #2b6cb0; background: #eef4fb; }
.pair { align-items: stretch; }
.box { border: .7pt solid #9aa3ad; padding: 6px 9px; border-radius: 3px; }
.center { text-align: center; } .big { font-size: 1.4em; } .huge { font-size: 2.2em; font-weight: 700; }
.stamp { display: inline-block; border: 2px solid #b03030; color: #b03030; padding: 2px 10px; transform: rotate(-4deg); font-weight: 700; letter-spacing: .1em; }
.receipt { width: 72mm; margin: 0 auto 8mm; font-family: 'Noto Sans Mono', monospace; font-size: .86em; border: .5pt dashed #999; padding: 4mm; }
.receipt table.t { font-size: 1em; }
.menu-item { display: flex; justify-content: space-between; }
"""

SLIDE_CSS = """
html { font-size: 17pt !important; }
h1 { font-size: 1.9em !important; border-bottom: 3px solid var(--accent); padding-bottom: .15em; }
h2 { font-size: 1.35em !important; border: none !important; }
li { margin-bottom: .35em; }
table.t { font-size: .8em; }
"""


def _scaled_width(width: str, scale: float) -> str:
    match = re.fullmatch(r"([0-9.]+)%", width)
    return f"{float(match.group(1)) * scale:.1f}%" if match else width


def _items(items: list[Any], ordered: bool) -> str:
    tag = "ol" if ordered else "ul"
    parts = []
    for entry in items:
        if isinstance(entry, dict):
            parts.append(f"<li>{inline(entry['text'])}{_items(entry['items'], entry['ordered'])}</li>")
        else:
            parts.append(f"<li>{inline(entry)}</li>")
    return f"<{tag}>" + "".join(parts) + f"</{tag}>"


def block_html(block: dict[str, Any], scale: float) -> str:
    """Render one authored block (containers recurse here so new kinds may nest)."""
    kind = block["kind"]
    cls = f" class='{block['cls']}'" if block.get("cls") else ""
    if kind == "list":
        html = _items(block["items"], block["ordered"])
        return html.replace("<ol>", f"<ol{cls}>", 1).replace("<ul>", f"<ul{cls}>", 1) if cls else html
    if kind == "code":
        caption = f"<p class='codecap'>{inline(block['caption'])}</p>" if block.get("caption") else ""
        return f"{caption}<pre class='code'><code>{e(block['text'])}</code></pre>"
    if kind == "equation":
        number = f"<span class='no'>{e(block['number'])}</span>" if block["number"] else ""
        return f"<div class='eq'><math display='block'>{block['mathml']}</math>{number}</div>"
    if kind == "form":
        raise ValueError("AcroForm sections are only produced by the ReportLab renderer")
    if kind == "figure":
        block = {**block, "width": _scaled_width(block.get("width", "45%"), scale)}
        return html_render.block_html(block)
    if kind == "columns":
        return f"<div class='cols' style='column-count:{block.get('count', 2)}'>" + "".join(block_html(b, scale) for b in block["blocks"]) + "</div>"
    if kind == "pair":
        return "<div class='pair'>" + "".join(f"<div>{block_html(b, scale)}</div>" for b in block["blocks"]) + "</div>"
    if kind == "group":
        return f"<div{cls}>" + "".join(block_html(b, scale) for b in block["blocks"]) + "</div>"
    return html_render.block_html(block)


def document_html(doc: dict[str, Any], scale: float = 1.0) -> str:
    """Render the complete document; ``scale`` shrinks type and figures uniformly to fit pages."""
    shell = deepcopy({k: v for k, v in doc.items() if k != "pages"})
    shell["blocks"] = []
    theme = shell["theme"]
    size = theme.get("font_size", "10pt")
    value = float(size.removesuffix("pt"))
    theme["font_size"] = f"{value * scale:.2f}pt"
    extra = EXTRA_CSS + (SLIDE_CSS.replace("17pt", f"{17 * scale:.2f}pt") if doc["page_size"] == "slide" else "")
    theme["extra_css"] = f":root {{ --accent: {theme.get('accent', '#24476b')}; }}" + extra + theme.get("extra_css", "")
    shell["page_size"] = PAGE_SIZES[doc["page_size"]]
    if doc["page_size"] == "slide":
        theme.setdefault("margins", "12mm 16mm 12mm 16mm")
    page = html_render.document_html(shell)
    body = "".join(f"<section class='pg' data-page='{n}'>" + "".join(block_html(b, scale) for b in blocks) + "</section>"
                   for n, blocks in enumerate(doc["pages"], start=1))
    return page.replace("<body></body>", f"<body>{body}</body>", 1)
