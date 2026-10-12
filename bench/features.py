"""Compare rich PDF conversion behavior without treating syntax probes as quality scores.

Run ``uv sync --group bench-rich && uv run python -m bench.features``.
Full raw outputs, fixture PDFs, warnings, failures, versions, and parsed
Markdown observations are retained for review. No OCR inference is enabled.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import platform
import statistics
import subprocess
import time
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from importlib import metadata
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import pdfust
from bench.feature_cases import ROOT, FeatureCase, build_cases

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class Adapter:
    """One explicitly configured public conversion entry point."""

    name: str
    kind: Literal["markdown", "text"]
    options: str
    call: Callable[[bytes], str]


def _pdfust(data: bytes, *, text_tables: bool = False) -> str:
    with pdfust.open(stream=data) as doc:
        return doc.to_markdown(table_strategy="text" if text_tables else "lines")


def _pymupdf(data: bytes, *, actual_text: bool = False) -> str:
    module = importlib.import_module("pymupdf")
    with module.open(stream=data, filetype="pdf") as doc:
        if actual_text:
            flags = module.TEXTFLAGS_TEXT & ~module.TEXT_IGNORE_ACTUALTEXT
            return "\n\n".join(page.get_text(flags=flags) for page in doc)
        return "\n\n".join(page.get_text() for page in doc)


def _pymupdf4llm(data: bytes, *, layout: bool, html_tables: bool = False) -> str:
    module = importlib.import_module("pymupdf4llm")
    module.use_layout(layout)
    pymupdf = importlib.import_module("pymupdf")
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        options: dict[str, Any] = {"embed_images": True, "show_progress": False}
        if layout:
            options["use_ocr"] = False
        if html_tables:
            options["table_output"] = "html"
        return cast("str", module.to_markdown(doc, **options))


def _pypdf(data: bytes) -> str:
    module = importlib.import_module("pypdf")
    return "\n\n".join(page.extract_text() or "" for page in module.PdfReader(io.BytesIO(data)).pages)


def _pdfplumber(data: bytes) -> str:
    module = importlib.import_module("pdfplumber")
    with module.open(io.BytesIO(data)) as doc:
        return "\n\n".join(page.extract_text() or "" for page in doc.pages)


ADAPTERS = (
    Adapter("pdfust", "markdown", "to_markdown(); bordered tables", _pdfust),
    Adapter(
        "pdfust-text-tables",
        "markdown",
        "to_markdown(table_strategy='text')",
        lambda data: _pdfust(data, text_tables=True),
    ),
    Adapter("pymupdf", "text", "Page.get_text(); default producer order", _pymupdf),
    Adapter(
        "pymupdf-actualtext",
        "text",
        "TEXTFLAGS_TEXT with TEXT_IGNORE_ACTUALTEXT cleared",
        lambda data: _pymupdf(data, actual_text=True),
    ),
    Adapter(
        "pymupdf4llm-legacy",
        "markdown",
        "use_layout(False); embed_images=True; no OCR",
        lambda data: _pymupdf4llm(data, layout=False),
    ),
    Adapter(
        "pymupdf4llm-layout",
        "markdown",
        "use_layout(True); embed_images=True; use_ocr=False",
        lambda data: _pymupdf4llm(data, layout=True),
    ),
    Adapter(
        "pymupdf4llm-html-tables",
        "markdown",
        "layout mode; embedded images; OCR off; table_output='html'",
        lambda data: _pymupdf4llm(data, layout=True, html_tables=True),
    ),
    Adapter("pypdf", "text", "Page.extract_text(); default options", _pypdf),
    Adapter("pdfplumber", "text", "Page.extract_text(); default options", _pdfplumber),
)


class _HtmlObservations(HTMLParser):
    """Count emitted HTML structure without assuming visual correctness."""

    def __init__(self) -> None:
        super().__init__()
        self.tables = 0
        self.superscripts = 0
        self.subscripts = 0
        self.spans: list[dict[str, str]] = []
        self.text: list[str] = []
        self.anchors: list[str] = []

    def handle_data(self, data: str) -> None:
        """Retain text inside HTML tables for the same literal-content probes."""
        self.text.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Collect the table and baseline markup Markdown itself cannot express."""
        self.tables += tag == "table"
        self.superscripts += tag == "sup"
        self.subscripts += tag == "sub"
        self.anchors.extend(value for name, value in attrs if name == "id" and value)
        if tag in {"td", "th"}:
            span = {name: value for name, value in attrs if name in {"rowspan", "colspan"} and value is not None}
            if span:
                self.spans.append(span)


def inspect_output(output: str, kind: str, case: FeatureCase) -> dict[str, Any]:
    """Parse actual Markdown syntax and separately check known literal content."""
    syntax: dict[str, Any] = {}
    plain = output
    if kind == "markdown":
        markdown = importlib.import_module("markdown_it")
        plugin = importlib.import_module("mdit_py_plugins.dollarmath")
        parser = markdown.MarkdownIt("commonmark").enable(["table", "strikethrough"]).use(plugin.dollarmath_plugin)
        tokens = parser.parse(output)
        flat = [child for token in tokens for child in ([token] + (token.children or []))]
        syntax = {
            "headings": sum(token.type == "heading_open" for token in flat),
            "strong": sum(token.type == "strong_open" for token in flat),
            "emphasis": sum(token.type == "em_open" for token in flat),
            "code": sum(token.type in {"code_inline", "fence", "code_block"} for token in flat),
            "lists": sum(token.type in {"bullet_list_open", "ordered_list_open"} for token in flat),
            "tables": sum(token.type == "table_open" for token in flat),
            "table_alignment": [
                token.attrGet("style") for token in flat if token.type == "th_open" and token.attrGet("style")
            ],
            "images": sum(token.type == "image" for token in flat),
            "image_sources": [token.attrGet("src") for token in flat if token.type == "image"],
            "links": [token.attrGet("href") for token in flat if token.type == "link_open"],
            "math": sum(token.type in {"math_inline", "math_block", "math_block_label"} for token in flat),
            "raw_html": sum(token.type in {"html_inline", "html_block"} for token in flat),
        }
        html = _HtmlObservations()
        for token in flat:
            if token.type in {"html_inline", "html_block"}:
                html.feed(token.content)
        syntax.update(
            {
                "html_tables": html.tables,
                "html_superscripts": html.superscripts,
                "html_subscripts": html.subscripts,
                "html_table_spans": html.spans,
                "html_anchors": html.anchors,
                "internal_link_targets": {
                    href: href[1:] in html.anchors for href in syntax["links"] if href and href.startswith("#")
                },
            }
        )
        plain_parts = []
        for token in flat:
            if token.type in {"text", "code_inline", "fence", "code_block", "math_inline", "math_block"}:
                plain_parts.append(token.content)
            elif token.type in {"html_inline", "html_block"}:
                fragment = _HtmlObservations()
                fragment.feed(token.content)
                plain_parts.extend(fragment.text)
        plain = "\n".join(plain_parts)
    positions = [plain.find(value) for value in case.expected_order]
    return {
        "syntax": syntax,
        "literal_text": {value: value in plain for value in case.expected_text},
        "reference_order": None
        if not positions
        else all(position >= 0 for position in positions) and all(left < right for left, right in pairwise(positions)),
        "math_reference_literal": None if case.reference_math is None else case.reference_math in output,
        "replacement_characters": output.count("\ufffd"),
        "utf8_bytes": len(output.encode("utf-8")),
    }


def source_inventory(case: FeatureCase) -> dict[str, Any]:
    """Record recoverable source objects through pdfust's separate APIs."""
    with warnings.catch_warnings(record=True) as captured, pdfust.open(stream=case.data) as doc:
        inventory: dict[str, Any] = {
            "pages": doc.page_count,
            "metadata": doc.metadata,
            "forms": doc.get_form_fields(),
            "attachments": doc.embfile_names(),
            "toc": doc.get_toc(),
            "links": [],
            "images": [],
            "tables": [],
            "spans": [],
            "annotations": [],
            "vector_paths": 0,
        }
        for page in doc:
            inventory["annotations"].extend(page.annots())
            inventory["vector_paths"] += len(page.get_drawings())
            inventory["links"].extend(page.get_links())
            inventory["images"].extend(
                {"bbox": image["bbox"], "ext": image["ext"], "bytes": len(image["image"])}
                for image in page.get_images()
            )
            inventory["tables"].extend(
                {"rows": table.row_count, "columns": table.col_count, "values": table.extract()}
                for table in page.find_tables()
            )
            layout = page.get_text("dict")
            inventory["spans"].extend(
                {"font": span["font"], "flags": span["flags"], "text": span["text"]}
                for block in layout["blocks"]
                for line in block["lines"]
                for span in line["spans"]
            )
        inventory["warnings"] = [str(item.message) for item in captured]
        return inventory


def run_case(case: FeatureCase, adapter: Adapter, repetitions: int, output_dir: Path) -> dict[str, Any]:
    """Retain failures and all full output while timing complete fresh conversions."""
    result: dict[str, Any] = {"adapter": adapter.name, "kind": adapter.kind, "options": adapter.options}
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            expected = adapter.call(case.data)
            expected_hash = hashlib.sha256(expected.encode("utf-8")).hexdigest()
            timings = []
            repeatable = True
            for _ in range(repetitions):
                start = time.perf_counter()
                output = adapter.call(case.data)
                timings.append((time.perf_counter() - start) * 1000)
                repeatable &= hashlib.sha256(output.encode("utf-8")).hexdigest() == expected_hash
            result["warnings"] = sorted({str(item.message) for item in captured})
        path = output_dir / f"{case.name}--{adapter.name}.out"
        path.write_bytes(expected.encode("utf-8"))
        result.update(
            {
                "status": "ok",
                "median_ms": statistics.median(timings),
                "repeatable": repeatable,
                "output_sha256": expected_hash,
                "raw_output": path.name,
                "observations": inspect_output(expected, adapter.kind, case),
            }
        )
    except Exception as exc:
        result.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return result


def format_report(report: dict[str, Any], output_dir: str) -> str:
    """Provide a review index without inventing a single correctness ranking."""
    lines = ["# Rich PDF to Markdown feature study", ""]
    lines.extend(f"- {key}: {value}" for key, value in report["metadata"].items())
    for index, run in enumerate(report.get("additional_runs", [])):
        versions = run["Versions"]
        selected_versions = ", ".join(
            f"{name} {versions.get(name, 'not installed')}" for name in ("docling", "marker-pdf", "surya-ocr", "torch")
        )
        lines.extend(
            [
                "",
                (
                    f"Additional run {index}: {run['Run at']}; {run['Environment']}; "
                    f"{run['CPU threads']} CPU threads; {run['Repetitions']} measured repetitions."
                ),
                f"Versions: {selected_versions}. OCR: {run['OCR']}. Hosted LLM: {run['Hosted LLM']}.",
                f"Source: {run['Source commit']}; dirty: {run['Source dirty']}.",
                f"Completion: {run.get('Completion', 'complete run')}.",
            ]
        )
        initializations = {
            result["adapter"]: result["initialization_ms"]
            for case in report["cases"]
            for result in case["results"]
            if result.get("run_index") == index
        }
        lines.extend(f"- {name} pipeline initialization: {elapsed:.3f} ms" for name, elapsed in initializations.items())
        weights = [
            item for item in run.get("Model files", []) if item["file"].endswith((".safetensors", ".pth", ".pt"))
        ]
        if weights:
            lines.extend(
                [
                    "",
                    "Cached model weights at run completion (includes unused variants):",
                    "",
                    "| Repository | Revision | File | Bytes | SHA-256 |",
                    "|---|---|---|---:|---|",
                ]
            )
            lines.extend(
                f"| {item['repository']} | {item['revision']} | {item['file']} | {item['bytes']} | {item['sha256']} |"
                for item in weights
            )
    lines.extend(
        [
            "",
            "Reproduce: `uv sync --group bench-rich && uv run python -m bench.features`.",
            "Optional Docling/Marker runs: see `bench/MODEL_BENCHMARKS.md`; their original run metadata",
            "and model fingerprints are retained separately in the JSON, alongside the earlier measurements.",
            "Only summaries and the compact timing/hash baseline are committed. Full JSON, source copies,",
            "raw outputs, structured sidecars, images, and logs are ignored local artifacts produced by the runners.",
            "One warmup plus median fresh-document conversion timings. Imports/model initialization occur",
            "before or during warmup. Page OCR is disabled; the Docling formula mode separately runs recognition.",
            "Source generation, syntax parsing, hashing, artifact serialization, and validation",
            "are outside the timer. Image embedding is enabled for PyMuPDF4LLM, so its output cost differs",
            "from converters that omit images. Timings across these tools are not equivalent-work rankings.",
            "",
            "PyMuPDF, pypdf, and pdfplumber provide plain-text baselines here; they are not Markdown converters.",
            "The JSON sidecar retains exact versions/options, source inventories, warnings, and literal probes.",
            "Raw `.out` files contain the full unmodified UTF-8 result, including multilingual fixture data.",
            "",
            "Syntax counts establish what markup was emitted, not whether the feature was reconstructed correctly.",
            "Text checks are strict substring probes of parsed text; they are not semantic or visual quality scores.",
            "Internal links need a target that resolves; a fragment-looking URL alone is insufficient.",
            "Math requires checking the reference expression, not counting symbols or math delimiters.",
            "Review table cell positions, merged spans, alignment, and image/caption association in the raw outputs.",
        ]
    )
    for case in report["cases"]:
        lines.extend(
            [
                "",
                f"## {case['name']}",
                "",
                ", ".join(case["features"]),
                "",
                case["notes"],
                "",
                f"Source: {case['source']}",
                "",
                f"Local input after running: `{output_dir}/{case['name']}.pdf`",
                "",
                "| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |",
                "|---|---|---:|---:|---|---|",
            ]
        )
        for result in case["results"]:
            if result["status"] != "ok":
                error = result["error"].replace("|", "\\|").replace("\n", " ")
                lines.append(f"| {result['adapter']} | {result['kind']} | n/a | n/a | n/a | {error} |")
                continue
            observed = result["observations"]
            checks = observed["literal_text"]
            counts = "/".join(
                str(observed["syntax"].get(name, "-"))
                for name in (
                    "headings",
                    "strong",
                    "emphasis",
                    "code",
                    "lists",
                    "tables",
                    "images",
                    "math",
                    "html_tables",
                )
            )
            counts += "/" + str(len(observed["syntax"]["links"])) if observed["syntax"] else "/-"
            link = "repeatable" if result["repeatable"] else "not repeatable"
            if result.get("structured_output"):
                link += "; local sidecar"
            lines.append(
                f"| {result['adapter']} | {result['kind']} | {result['median_ms']:.3f} | "
                f"{sum(checks.values())}/{len(checks)} | {counts} | {link} |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Write independently reviewable results for every selected feature case."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "bench" / "results" / "features-latest.json")
    parser.add_argument("--case", action="append", help="Run only named cases; may be repeated")
    args = parser.parse_args()
    if args.repetitions < 1 or args.output.suffix != ".json":
        parser.error("use positive --repetitions and a .json --output path")
    versions = {}
    for package in (
        "pdfust",
        "pymupdf",
        "pymupdf4llm",
        "pymupdf-layout",
        "pypdf",
        "pdfplumber",
        "markdown-it-py",
        "mdit-py-plugins",
        "pdfust-fonts-ar",
        "pdfust-fonts-he",
        "pdfust-fonts-hi",
        "pdfust-fonts-jp",
        "pdfust-fonts-ko",
        "pdfust-fonts-th",
        "pdfust-fonts-zh-cn",
        "pdfust-fonts-zh-tw",
    ):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not installed"
    cases = build_cases()
    if args.case:
        names = {case.name for case in cases}
        if set(args.case) - names:
            parser.error(f"unknown cases: {sorted(set(args.case) - names)}")
        cases = [case for case in cases if case.name in args.case]
    output_dir = args.output.parent / "feature-outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S607
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))  # noqa: S607
    report: dict[str, Any] = {
        "schema_version": 1,
        "metadata": {
            "Run at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "Source commit": commit + (" (dirty)" if dirty else ""),
            "Environment": f"{platform.platform()} / Python {platform.python_version()}",
            "Versions": ", ".join(f"{name} {version}" for name, version in versions.items()),
            "Repetitions": args.repetitions,
            "OCR": "disabled",
        },
        "cases": [],
    }
    for case in cases:
        (output_dir / f"{case.name}.pdf").write_bytes(case.data)
        record = {
            "name": case.name,
            "features": case.features,
            "notes": case.notes,
            "source": case.source,
            "source_values": case.source_values,
            "reference_math": case.reference_math,
            "input_sha256": hashlib.sha256(case.data).hexdigest(),
            "inventory": source_inventory(case),
            "results": [run_case(case, adapter, args.repetitions, output_dir) for adapter in ADAPTERS],
        }
        report["cases"].append(record)
        print(f"{case.name}: done")
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(format_report(report, output_dir.name), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
