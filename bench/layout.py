"""Measure end-to-end Markdown and structured extraction, with baseline comparisons.

Run ``uv run python bench/layout.py`` after ``uv sync``. Keep the JSON report
from a baseline checkout, then pass it with ``--baseline`` on the candidate.
Synthetic PDF generation and output validation are outside the timed region.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import partial
from importlib import metadata as package_metadata
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pdfust

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "bench" / "results" / "layout-latest.json"
CORPUS_NAMES = ("bill-hr815.pdf", "f1040.pdf", "patent-us223898.pdf", "usrguide.pdf")
Task = Literal["markdown", "markdown-no-tables", "words", "blocks", "dict"]
TASKS: tuple[Task, ...] = ("markdown", "markdown-no-tables", "words", "blocks", "dict")
Mode = Literal["fresh", "reused"]
MODES: tuple[Mode, ...] = ("fresh", "reused")


def _grid_pdf() -> bytes:
    """Create a minimal vector grid to overlay through the public PDF API."""
    rules = ["0 G 1 w"]
    rules.extend(f"40 {792 - y} m 550 {792 - y} l" for y in range(480, 601, 30))
    rules.extend(f"{x} 312 m {x} 192 l" for x in (40, 210, 380, 550))
    stream = "\n".join([*rules, "S"]).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << >> /Contents 4 0 R >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"),
    )
    return bytes(output)


@dataclass(frozen=True)
class Measurement:
    """One workload's timing and exact input/output identity."""

    sample: str
    task: Task
    mode: Mode
    pages: int
    input_sha256: str
    output_sha256: str
    output_bytes: int
    median_ms: float


def _synthetic_pdf(page_count: int, *, unicode_text: bool) -> bytes:
    """Build deterministic prose and a 4x3 grid without optional font packages."""
    with pdfust.Document() as doc, pdfust.open(stream=_grid_pdf()) as grid:
        for index in range(page_count):
            page = doc.new_page(width=612, height=792)
            page.insert_text((40, 45), f"Benchmark section {index + 1}", fontsize=18)
            if unicode_text:
                # Unicode fixture data: invisible OCR text tests extraction,
                # not OCR inference or embedded-font shaping performance.
                text = (
                    "\u65e5\u672c\u8a9e\u306e\u6587\u7ae0\u3068\u62bd\u51fa\u7d50\u679c\u3092\u78ba\u8a8d\u3057\u307e\u3059。"
                    * 4
                )
                page.insert_ocr_text_layer([(40, y, 550, y + 12, text) for y in range(70, 430, 18)])
            else:
                text = "Positioned text supports Markdown and structured extraction. " * 2
                page.insert_text((40, 82), "\n".join([text] * 20), fontsize=8)
            page.show_pdf_page((0, 0, 612, 792), grid)
            for row in range(4):
                for column in range(3):
                    page.insert_text((50 + column * 170, 500 + row * 30), f"Cell {row}-{column}", fontsize=10)
        return doc.tobytes()


def _samples(*, synthetic_only: bool) -> dict[str, bytes]:
    """Read selected licensed corpus files and generate cache-boundary cases."""
    samples = (
        {}
        if synthetic_only
        else {name: (ROOT / "tests" / "assets" / "real_world" / name).read_bytes() for name in CORPUS_NAMES}
    )
    for page_count in (1, 8, 16):
        for unicode_text in (False, True):
            script = "unicode-ocr" if unicode_text else "ascii"
            samples[f"synthetic-{script}-{page_count}p"] = _synthetic_pdf(page_count, unicode_text=unicode_text)
    return samples


def _extract(doc: pdfust.Document, task: Task) -> object:
    """Return the complete public result, retaining all structured pages."""
    if task == "markdown":
        return doc.to_markdown()
    if task == "markdown-no-tables":
        return doc.to_markdown(table_strategy=None)
    return [page.get_text(task) for page in doc]


def _fresh_extract(data: bytes, task: Task) -> object:
    """Include document opening, public extraction, and closing in the timing."""
    with pdfust.open(stream=data) as doc:
        return _extract(doc, task)


def _output_identity(output: object) -> tuple[str, int]:
    """Hash full text or canonical structured JSON outside extraction timing."""
    text = (
        output
        if isinstance(output, str)
        else json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    encoded = text.encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), len(encoded)


def _measure(call: Callable[[], object], repetitions: int) -> tuple[float, str, int]:
    """Warm up once, then verify every timed result against the warmup."""
    expected_hash, output_bytes = _output_identity(call())
    timings: list[float] = []
    for _ in range(repetitions):
        start = time.perf_counter()
        output = call()
        timings.append((time.perf_counter() - start) * 1000)
        if _output_identity(output) != (expected_hash, output_bytes):
            msg = "Benchmark output changed between repetitions"
            raise RuntimeError(msg)
        del output
    return statistics.median(timings), expected_hash, output_bytes


def measure_sample(name: str, data: bytes, repetitions: int) -> list[Measurement]:
    """Measure each task independently, with fresh and reused Documents."""
    input_hash = hashlib.sha256(data).hexdigest()
    with pdfust.open(stream=data) as doc:
        pages = doc.page_count
    results: list[Measurement] = []
    for task in TASKS:
        for mode in MODES:
            if mode == "fresh":
                elapsed, output_hash, size = _measure(partial(_fresh_extract, data, task), repetitions)
            else:
                with pdfust.open(stream=data) as doc:
                    elapsed, output_hash, size = _measure(partial(_extract, doc, task), repetitions)
            results.append(Measurement(name, task, mode, pages, input_hash, output_hash, size, elapsed))
        if results[-1].output_sha256 != results[-2].output_sha256:
            msg = f"Fresh and reused output differ for {name}: {task}"
            raise RuntimeError(msg)
        print(f"{name}: {task} done")
    return results


def _comparison(current: Measurement, baseline: Measurement | None) -> str:
    """Report ratios only when input and complete output match exactly."""
    if baseline is None:
        return "n/a"
    if current.input_sha256 != baseline.input_sha256:
        return "input changed"
    if current.output_sha256 != baseline.output_sha256:
        return "output changed"
    if current.median_ms <= 0 or baseline.median_ms <= 0:
        return "n/a"
    return f"{baseline.median_ms / current.median_ms:.2f}x"


def format_report(
    measurements: list[Measurement],
    metadata: dict[str, str | int],
    baseline: list[Measurement],
    baseline_metadata: dict[str, str | int],
) -> str:
    """Publish all timings, payload sizes, and eligible speedups together."""
    lines = ["# Markdown and structured-output benchmark", ""]
    lines.extend(f"- {key}: {value}" for key, value in metadata.items())
    if baseline_metadata:
        lines.append("")
        lines.append("Baseline metadata (compare matching environments and repetition counts):")
        lines.extend(f"- {key}: {value}" for key, value in baseline_metadata.items())
    lines.extend(
        [
            "",
            "One warmup plus median timings. Fresh includes opening, all-page extraction, and closing.",
            "Reused repeats the task on one Document after warmup; it does not promise every page is cached.",
            "Each task owns an independent Document. Synthetic generation, JSON serialization, hashing,",
            "and output validation are outside the timer. Structured results retain all requested pages.",
            "Output bytes are UTF-8 Markdown or compact, sorted-key UTF-8 JSON for structured results.",
            "Reproduce: uv sync && uv run python bench/layout.py (default: five repetitions).",
            "Save a baseline with --output /tmp/layout-baseline.json; compare with",
            "--baseline /tmp/layout-baseline.json. Use --synthetic-only to omit corpus files.",
            "",
            "Corpus: bill-hr815, f1040, patent-us223898, and usrguide from tests/assets/real_world.",
            "Sources and licenses are documented in that directory's README. Synthetic cases contain",
            "20 prose lines and one 4x3 bordered table per page, at 1, 8, and 16 pages.",
            "Unicode cases use invisible Japanese OCR text without model inference or font extras.",
            "The page counts exercise workloads below, at, and above the current eight-page caches.",
            "",
            "Speedup = baseline median / candidate median; below 1.00x is a regression.",
            "A ratio requires matching PDF and full-output SHA-256 hashes. Changed outputs need review",
            "before claiming a speedup. Matching hashes establish repeatability, not extraction quality.",
            "",
            "| Sample | Pages | Task | Mode | Output bytes | Median ms | Speedup |",
            "|---|---:|---|---|---:|---:|---:|",
        ]
    )
    previous = {(item.sample, item.task, item.mode): item for item in baseline}
    for item in measurements:
        ratio = _comparison(item, previous.get((item.sample, item.task, item.mode)))
        lines.append(
            f"| {item.sample} | {item.pages} | {item.task} | {item.mode} | "
            f"{item.output_bytes} | {item.median_ms:.3f} | {ratio} |",
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Write standalone Markdown and JSON reports without replacing other benchmarks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON path; Markdown uses the same stem")
    parser.add_argument("--baseline", type=Path, help="Previous JSON report for exact-output speedup comparisons")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    if args.output.suffix != ".json":
        parser.error("--output must have a .json suffix")
    baseline_data = {} if args.baseline is None else json.loads(args.baseline.read_text(encoding="utf-8"))
    if args.baseline is not None and baseline_data.get("schema_version") != 1:
        parser.error("unsupported baseline schema_version; expected 1")
    baseline = [Measurement(**item) for item in baseline_data.get("measurements", [])]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S607
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))  # noqa: S607
    font_extras = []
    for locale in ("ar", "he", "hi", "jp", "ko", "th", "zh-cn", "zh-tw"):
        package = f"pdfust-fonts-{locale}"
        try:
            font_extras.append(f"{package} {package_metadata.version(package)}")
        except package_metadata.PackageNotFoundError:
            continue
    metadata = {
        "Run at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "Environment": (
            f"{platform.platform()} / Python {platform.python_version()} / {platform.processor() or platform.machine()}"
        ),
        "Machine": f"{platform.machine()} / {os.cpu_count()} logical CPUs",
        "pdfust": pdfust.__version__,
        "Font extras": ", ".join(font_extras) or "none",
        "Source commit": commit + (" (dirty)" if dirty else ""),
        "Repetitions": args.repetitions,
        "Selection": "synthetic only" if args.synthetic_only else "corpus and synthetic",
    }
    measurements = [
        result
        for name, data in _samples(synthetic_only=args.synthetic_only).items()
        for result in measure_sample(name, data, args.repetitions)
    ]
    report = {"schema_version": 1, "metadata": metadata, "measurements": [asdict(item) for item in measurements]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(
        format_report(measurements, metadata, baseline, baseline_data.get("metadata", {})),
        encoding="utf-8",
    )
    print(f"Wrote {args.output} and {args.output.with_suffix('.md')}")


if __name__ == "__main__":
    main()
