"""Build an offline, standalone HTML demonstration from a retained pipeline run."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, NoReturn

from bench.pipeline_repair import validate
from bench.silver import guard_path

ROOT = Path(__file__).resolve().parent.parent
# HTML and CSS remain readable as a static template.
# ruff: noqa: E501

MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_SPAN = 4096


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


def _read(path: Path, limit: int = MAX_ARTIFACT_BYTES) -> bytes:
    path = guard_path(path)
    if path.stat().st_size > limit:
        _fail("Demo input exceeds admission")
    data = path.read_bytes()
    if len(data) > limit:
        _fail("Demo input grew above admission")
    return data


class _SafeHTML(HTMLParser):
    """Retain static Markdown structure and bounded table spans only."""

    allowed = frozenset(
        {
            "p",
            "table",
            "tr",
            "td",
            "th",
            "thead",
            "tbody",
            "br",
            "ul",
            "ol",
            "li",
            "strong",
            "em",
            "code",
            "pre",
            "blockquote",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "hr",
        }
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed:
            self.parts.append(html.escape(self.get_starttag_text() or ""))
            return
        spans = []
        for key, value in attrs:
            if (
                tag in {"td", "th"}
                and key in {"rowspan", "colspan"}
                and value is not None
                and len(value) <= len(str(MAX_SPAN))
                and value.isascii()
                and value.isdigit()
                and 1 <= int(value) <= MAX_SPAN
            ):
                spans.append(f' {key}="{int(value)}"')
        self.parts.append(f"<{tag}{''.join(spans)}>")

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>" if tag in self.allowed else html.escape(f"</{tag}>"))

    def handle_data(self, data: str) -> None:
        self.parts.append(html.escape(data))


def render_markdown(markdown: str) -> str:
    """Render Markdown plus sanitized static HTML tables without links or images."""
    from markdown_it import MarkdownIt  # noqa: PLC0415 - optional demo dependency.

    parser = MarkdownIt("commonmark", {"html": True, "linkify": False}).enable("table")
    parser.disable(["image", "link", "autolink"])
    sanitizer = _SafeHTML()
    sanitizer.feed(str(parser.render(markdown)))
    sanitizer.close()
    return "".join(sanitizer.parts)


def document(  # noqa: PLR0913 - explicit viewer panels.
    *, page_id: str, png: bytes, markdown: str, native: dict[str, Any], output: dict[str, Any], metadata: dict[str, Any]
) -> str:
    """Embed escaped output and a source raster without executable source content."""
    escape = html.escape
    image = base64.b64encode(png).decode("ascii")
    native_json = escape(json.dumps(native, ensure_ascii=False, indent=2))
    output_json = escape(json.dumps(output, ensure_ascii=False, indent=2))
    meta = escape(json.dumps(metadata, ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PDF pipeline demonstration — {escape(page_id)}</title>
<style>
body{{margin:0;padding:24px;background:#f6f5f1;color:#222;font:16px/1.5 system-ui,sans-serif}}
h1{{font-size:24px}}h2{{font-size:19px}}.grid{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px}}
section{{padding:20px;background:white;border:1px solid #bbb;border-radius:8px;min-width:0}}
img{{width:100%;height:auto;display:block}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #aaa;padding:6px;text-align:left;vertical-align:top}}
details{{margin-top:16px}}.markdown{{overflow:auto}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
</style>
<h1>PDF pipeline demonstration</h1>
<p>Page {escape(page_id)}. Retained experiment output; this viewer makes no model requests.</p>
<div class="grid"><section><h2>Complete source page</h2>
<img alt="Full source PDF page" src="data:image/png;base64,{image}">
<p><a href="source.pdf" download>Download the verified source PDF</a></p>
</section><section><h2>Selected pipeline Markdown</h2><div class="markdown">{render_markdown(markdown)}</div>
<details><summary>Literal Markdown</summary><pre>{escape(markdown)}</pre></details></section></div>
<div class="grid" style="margin-top:24px"><section><h2>Before: native vector state</h2><pre>{native_json}</pre></section>
<section><h2>After: selected structure and source ownership</h2><pre>{output_json}</pre></section></div>
<details><summary>Run and source provenance</summary><pre>{meta}</pre></details></html>"""


def build(run: Path, page_id: str, output: Path, *, image_edge: int = 1024) -> dict[str, Any]:
    """Verify the frozen PDF, render one page, and write only ignored local artifacts."""
    import pdfust  # noqa: PLC0415 - optional rendering dependency.
    from bench.pipeline_assembly import native_state  # noqa: PLC0415 - completed assembly artifact integration.

    if re.fullmatch(r"p[a-f0-9]{20}", page_id) is None:
        _fail("Page ID must be a frozen opaque page identifier")
    if image_edge not in (512, 1024):
        _fail("Image edge must be 512 or 1024")
    run = guard_path(run)
    output = guard_path(output)
    if not output.is_relative_to(ROOT / "bench/results/pdf-master-artifacts"):
        _fail("Demo output must be inside ignored bench/results/pdf-master-artifacts")
    frozen = json.loads(_read(run / "frozen.json"))
    records = [{k: r[k] for k in ("id", "pdf_path", "pdf_sha256", "page_number")} for r in frozen["records"]]
    record = next((r for r in records if r["id"] == page_id), None)
    if record is None:
        _fail("Page ID is absent from frozen run records")
    pdf = _read(Path(record["pdf_path"]), MAX_INPUT_BYTES)
    digest = hashlib.sha256(pdf).hexdigest()
    if digest != record["pdf_sha256"]:
        _fail("Frozen source PDF hash changed")
    result = json.loads(_read(run / f"{page_id}-result.json"))
    if result["status"] != "ok":
        _fail("Demo requires a completed page result")
    source = result["source"]
    chosen = json.loads(_read(run / f"{page_id}-structure.json"))
    validate(source, chosen)
    native = native_state(source)
    validate(source, native)
    markdown = _read(run / f"{page_id}.md").decode("utf-8")
    with pdfust.open(stream=pdf) as pdf_document:
        page = pdf_document[record["page_number"]]
        original_rotation = page.rotation
        if result.get("rotation_normalized"):
            page.set_rotation(0)
        png = page.render(dpi=72 * image_edge / max(page.rect.width, page.rect.height), background=(255, 255, 255))
    metadata = {
        "page_id": page_id,
        "page_number": record["page_number"],
        "source_sha256": digest,
        "policy": frozen["config"]["policy"],
        "model": frozen["config"].get("model"),
        "route": result.get("route"),
        "original_rotation": original_rotation,
        "rotation_normalized": bool(result.get("rotation_normalized")),
        "selected_choices": [c.get("answer", {}).get("choice") for c in result.get("calls", [])],
        "source_conserved": result.get("source_conserved"),
        "image_edge": image_edge,
        "source_scope": "full PDF page; retained extraction is not a pixel visibility guarantee",
    }
    ownership = {"state": chosen, "source_words": [{k: w[k] for k in ("id", "text", "bbox")} for w in source["words"]]}
    content = document(page_id=page_id, png=png, markdown=markdown, native=native, output=ownership, metadata=metadata)
    output.mkdir(parents=True, exist_ok=False)
    (output / "index.html").write_text(content, encoding="utf-8")
    (output / "source.pdf").write_bytes(pdf)
    return {
        "html": str(output / "index.html"),
        "source_sha256": digest,
        "image_edge": image_edge,
        "html_bytes": len(content.encode("utf-8")),
    }


def main() -> None:
    """Build an offline viewer from a completed retained experiment page."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--page", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-edge", type=int, choices=(512, 1024), default=1024)
    args = parser.parse_args()
    print(json.dumps(build(args.run, args.page, args.output, image_edge=args.image_edge)))


if __name__ == "__main__":
    main()
