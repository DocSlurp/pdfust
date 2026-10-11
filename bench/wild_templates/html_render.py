"""Render authored wild-v1 documents to print HTML for headless Chromium."""

# ruff: noqa: E501, C901, PLR0911, PLR0912
from __future__ import annotations

import html
from typing import Any

from bench.wild_templates.model import tokens

LANG_FONTS = {
    "ja": "'Noto Sans CJK JP'", "zh-CN": "'Noto Sans CJK SC'", "zh-TW": "'Noto Sans CJK TC'", "ko": "'Noto Sans CJK KR'",
    "ar": "'Noto Naskh Arabic'", "he": "'Noto Sans Hebrew'", "hi": "'Noto Sans Devanagari'", "th": "'Noto Sans Thai'",
}
FALLBACK = ("'Noto Sans CJK JP', 'Noto Naskh Arabic', 'Noto Sans Hebrew', 'Noto Sans Devanagari', 'Noto Sans Thai', "
            "'Noto Sans Symbols', 'Noto Sans Symbols 2', 'JetBrainsMono Nerd Font', 'Noto Color Emoji'")


def e(text: str) -> str:
    """Escape for HTML text and attributes."""
    return html.escape(text, quote=True)


def inline(markup: str) -> str:
    """Render inline markup to HTML."""
    out = []
    for style, text, href in tokens(markup):
        if style == "bold":
            out.append(f"<strong>{e(text)}</strong>")
        elif style == "italic":
            out.append(f"<em>{e(text)}</em>")
        elif style == "link":
            out.append(f"<a href='{e(href or '')}'>{e(text)}</a>")
        else:
            out.append(e(text))
    return "".join(out).replace("\n", "<br>")


def _css_content(template: str) -> str:
    """Turn ``'Page {page} of {pages}'`` into a CSS ``content`` value."""
    parts: list[str] = []
    rest = template
    while rest:
        index = min((rest.find(k) for k in ("{page}", "{pages}") if k in rest), default=-1)
        if index < 0:
            parts.append(_css_string(rest))
            break
        if index:
            parts.append(_css_string(rest[:index]))
        if rest.startswith("{pages}", index):
            parts.append("counter(pages)")
            rest = rest[index + 7:]
        else:
            parts.append("counter(page)")
            rest = rest[index + 6:]
    return " ".join(parts) or '""'


def _css_string(text: str) -> str:
    # Literal UTF-8 is safe here; hex escapes would swallow a following space.
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _table(block: dict[str, Any]) -> str:
    if block["rendering"] in {"chart_data", "screenshot"}:
        return ""  # values exist only inside the preceding chart or screenshot image
    values = block["values"]
    spans = {(s["row"], s["column"]): s for s in block["spans"]}
    align = block.get("align") or ["l"] * len(values[0])
    classes = f"t {block['rendering']} {block.get('cls', '')}".strip()
    widths = block.get("widths")
    out = [f"<table class='{classes}'>"]
    if block.get("caption"):
        out.append(f"<caption>{inline(block['caption'])}</caption>")
    if widths:
        out.append("<colgroup>" + "".join(f"<col style='width:{w}%'>" for w in widths) + "</colgroup>")
    total_rows = set(block.get("total_rows", []))
    for r, row in enumerate(values):
        if r == 0 and block["header_rows"]:
            out.append("<thead>")
        if r == block["header_rows"]:
            out.append("<tbody>")
        tr_class = " class='total'" if r in total_rows else ""
        out.append(f"<tr{tr_class}>")
        for c, value in enumerate(row):
            if value is None:
                continue
            span = spans[(r, c)]
            tag = "th" if r < block["header_rows"] else "td"
            attrs = ""
            if span["column_span"] > 1:
                attrs += f" colspan='{span['column_span']}'"
            if span["row_span"] > 1:
                attrs += f" rowspan='{span['row_span']}'"
            cls = {"r": "num", "c": "ctr"}.get(align[c], "")
            if span["column_span"] > 1:
                cls = "ctr group"
            if cls:
                attrs += f" class='{cls}'"
            out.append(f"<{tag}{attrs}>{e(value)}</{tag}>")
        out.append("</tr>")
        if r == block["header_rows"] - 1:
            out.append("</thead>")
    out.append("</tbody></table>")
    return "".join(out)


def _figure(block: dict[str, Any]) -> str:
    wrap = block.get("wrap", "none")
    style = f" style='width:{block.get('width', '45%')}'"
    cls = {"left": "fl", "right": "fr"}.get(wrap, "blockfig")
    inner = block["svg"] if block.get("svg") else f"<img src='assets/{e(block['src'])}' alt='{e(block.get('alt', ''))}'>"
    caption = f"<figcaption>{inline(block['caption'])}</figcaption>" if block.get("caption") else ""
    return f"<figure class='{cls} {block.get('cls', '')}'{style}>{inner}{caption}</figure>"


def block_html(block: dict[str, Any]) -> str:
    """Render one authored block."""
    kind = block["kind"]
    cls = f" class='{block['cls']}'" if block.get("cls") else ""
    if kind == "heading":
        return f"<h{block['level']}{cls}>{inline(block['text'])}</h{block['level']}>"
    if kind == "paragraph":
        return f"<p{cls}>{inline(block['text'])}</p>"
    if kind == "list":
        tag = "ol" if block["ordered"] else "ul"
        return f"<{tag}{cls}>" + "".join(f"<li>{inline(i)}</li>" for i in block["items"]) + f"</{tag}>"
    if kind == "table":
        return _table(block)
    if kind == "figure":
        return _figure(block)
    if kind in {"sidebar", "callout"}:
        title = f"<p class='bt'>{inline(block['title'])}</p>" if block.get("title") else ""
        tag = "aside" if kind == "sidebar" else "div"
        return f"<{tag} class='{kind} {block.get('cls', '')}'>{title}<p>{inline(block['text'])}</p></{tag}>"
    if kind == "footnote":
        return f"<p class='footnote'>{inline(block['text'])}</p>"
    if kind == "fields":
        rows = "".join(f"<div class='field'><span class='lab'>{e(label)}:</span> <span class='val'>{e(value)}</span></div>"
                       for label, value in block["items"])
        return f"<div class='fields'>{rows}</div>"
    if kind == "columns":
        return f"<div class='cols' style='column-count:{block.get('count', 2)}'>" + "".join(block_html(b) for b in block["blocks"]) + "</div>"
    if kind == "pair":
        return "<div class='pair'>" + "".join(f"<div>{block_html(b)}</div>" for b in block["blocks"]) + "</div>"
    if kind == "group":
        return f"<div{cls}>" + "".join(block_html(b) for b in block["blocks"]) + "</div>"
    if kind in {"header", "footer"}:
        return ""
    raise ValueError(kind)


def document_html(doc: dict[str, Any]) -> str:
    """Render one complete document with print CSS, running header/footer and fonts."""
    theme = doc["theme"]
    lang = doc["metadata"]["lang"]
    primary = LANG_FONTS.get(lang, LANG_FONTS.get(lang.split("-")[0], ""))
    body_font = theme.get("body_font", "'Noto Sans'")
    heading_font = theme.get("heading_font", body_font)
    stack = ", ".join(x for x in (primary, body_font, FALLBACK) if x)
    head_stack = ", ".join(x for x in (primary, heading_font, FALLBACK) if x)
    accent = theme.get("accent", "#24476b")
    size = doc["page_size"]
    margins = theme.get("margins", "18mm 17mm 20mm 17mm")
    boxes = ""
    if doc.get("running_header"):
        side = "top-right" if doc.get("dir") == "rtl" else "top-left"
        boxes += f"@{side}{{content:{_css_content(doc['running_header'])};font:8pt {stack};color:#666}}"
    if doc.get("running_footer"):
        boxes += f"@bottom-center{{content:{_css_content(doc['running_footer'])};font:8pt {stack};color:#666}}"
    css = f"""
@page {{ size: {size}; margin: {margins}; {boxes} }}
html {{ font-family: {stack}; font-size: {theme.get('font_size', '10pt')}; color: #1d1d1f; line-height: 1.42; }}
body {{ margin: 0; }}
h1, h2, h3 {{ font-family: {head_stack}; color: {accent}; line-height: 1.2; break-after: avoid; }}
h1 {{ font-size: 1.85em; margin: 0 0 .35em; }}
h2 {{ font-size: 1.3em; margin: 1.05em 0 .4em; border-bottom: 1px solid {accent}33; padding-bottom: 2px; }}
h3 {{ font-size: 1.08em; margin: .9em 0 .3em; }}
p {{ margin: 0 0 .6em; }}
a {{ color: {accent}; }}
ul, ol {{ margin: .2em 0 .7em; padding-inline-start: 1.4em; }}
ul, ol {{ display: flow-root; }}
.clear {{ clear: both; }}
:lang(ko) {{ word-break: keep-all; }}
li {{ margin-bottom: .2em; }}
table.t {{ border-collapse: collapse; width: 100%; margin: .4em 0 1em; font-size: .9em; break-inside: auto; }}
table.t caption {{ caption-side: top; text-align: start; font-weight: 600; color: #333; padding-bottom: 4px; font-size: .95em; }}
table.t th, table.t td {{ padding: 3.5px 6px; vertical-align: top; text-align: start; }}
table.ruled th, table.ruled td {{ border: .6pt solid #8a8f98; }}
table.ruled thead th {{ background: {accent}18; }}
table.borderless thead th {{ border-bottom: 1.2pt solid {accent}; color: {accent}; }}
table.borderless td {{ padding-top: 4px; padding-bottom: 4px; }}
table.borderless tbody tr:nth-child(even) td {{ background: #f5f6f8; }}
table.t td:empty {{ height: 1.2em; }}
td.num, th.num {{ text-align: end !important; font-variant-numeric: tabular-nums; white-space: nowrap; }}
td.ctr, th.ctr {{ text-align: center !important; }}
tr.total td {{ font-weight: 700; border-top: 1.4pt solid #333; }}
figure {{ margin: 0 0 .8em; }}
figure img, figure svg {{ width: 100%; height: auto; display: block; }}
figure.fl {{ float: left; margin: .2em 1.1em .6em 0; shape-outside: margin-box; }}
figure.fr {{ float: right; margin: .2em 0 .6em 1.1em; shape-outside: margin-box; }}
[dir=rtl] figure.fl {{ float: right; margin: .2em 0 .6em 1.1em; }}
[dir=rtl] figure.fr {{ float: left; margin: .2em 1.1em .6em 0; }}
figure.blockfig {{ margin: .6em auto 1em; }}
figure.shadow img {{ box-shadow: 0 1px 6px #0004; border: 1px solid #ccc; }}
figcaption {{ font-size: .82em; color: #555; margin-top: 4px; font-style: italic; }}
aside.sidebar {{ float: right; width: 34%; margin: .2em 0 .8em 1em; background: #f3f5f8; border-top: 3px solid {accent}; padding: .6em .8em; font-size: .9em; }}
[dir=rtl] aside.sidebar {{ float: left; margin: .2em 1em .8em 0; }}
aside.sidebar.wide {{ float: none; width: auto; margin: .8em 0; }}
div.callout {{ border-inline-start: 4px solid {theme.get('callout', '#d08c2b')}; background: #fbf6ec; padding: .5em .9em; margin: .7em 0; font-size: .95em; break-inside: avoid; }}
.bt {{ font-weight: 700; margin-bottom: .25em; color: {accent}; }}
p.footnote {{ font-size: .78em; color: #444; margin: 0 0 .25em; }}
p.footnote:first-of-type, hr + p.footnote {{ border-top: .6pt solid #999; padding-top: 4px; margin-top: 1em; }}
.cols {{ column-gap: 7mm; column-rule: .5pt solid #ddd; }}
.cols h2, .cols h3 {{ break-after: avoid; }}
.cols p {{ text-align: start; }}
.pair {{ display: flex; gap: 6mm; align-items: flex-start; }}
.pair > div {{ flex: 1; }}
.fields {{ display: grid; grid-template-columns: 1fr 1fr; gap: .45em 1.6em; margin: .5em 0 1em; }}
.field {{ border-bottom: .6pt solid #888; padding-bottom: 2px; }}
.field .lab {{ font-size: .8em; color: #555; }}
.field .val {{ font-family: 'Noto Sans Mono', {stack}; }}
.letterhead {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid {accent}; padding-bottom: 6px; margin-bottom: 10px; }}
.split {{ display: flex; gap: 8mm; }} .split > * {{ flex: 1; }}
.right {{ text-align: end; }} .small {{ font-size: .85em; color: #444; }} .muted {{ color: #666; }}
.lead {{ font-size: 1.1em; color: #333; }} .brand {{ font-size: 1.5em; font-weight: 700; color: {accent}; margin: 0; }}
.meta {{ font-size: .88em; }} .kicker {{ text-transform: uppercase; letter-spacing: .08em; font-size: .78em; color: {accent}; font-weight: 700; margin-bottom: .2em; }}
.masthead {{ text-align: center; border-top: 3px double {accent}; border-bottom: 3px double {accent}; padding: 4px 0 6px; margin-bottom: 10px; }}
.masthead h1 {{ margin: 0; font-size: 2.2em; }}
.icons {{ font-family: 'JetBrainsMono Nerd Font', {stack}; }}
{theme.get('extra_css', '')}
"""
    direction = doc.get("dir", "ltr")
    body = "".join(block_html(b) for b in doc["blocks"])
    meta = doc["metadata"]
    return (f"<!doctype html><html lang='{e(lang)}' dir='{direction}'><head><meta charset='utf-8'>"
            f"<title>{e(meta['title'])}</title><meta name='author' content='{e(meta['author'])}'>"
            f"<meta name='description' content='{e(meta['subject'])}'><meta name='keywords' content='{e(', '.join(meta['keywords']))}'>"
            f"<style>{css}</style></head><body>{body}</body></html>")
