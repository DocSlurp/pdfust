"""Validate the library ``Page.ocr_fill`` policies on the wild-v1 DEV corpus.

Compares the library implementation with the recorded bench-only
``ocr-fill`` / ``ocr-adaptive`` numbers (``bench/wild_corpus.py``) on the same
levels and scoring (``audit_pdf``: character-bigram text F1 against truth).
DEV only; synthetic documents. Example::

    uv run python -m bench.ocr_fill_validate --levels L8_mixed L9_broken_tounicode
"""

# ruff: noqa: D103, E501, ISC004, S112
from __future__ import annotations

import argparse
import json
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import pdfust
from bench.silver import guard_path
from bench.wild_corpus import DEFAULT_DIRECTORY, _delta, _measure, audit_pdf, summarize

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEVELS = ("L8_mixed", "L9_broken_tounicode")
RECORDED = {  # bench/results/wild-v1-latest.md, text F1
    ("L8_mixed", "native"): 0.705,
    ("L8_mixed", "fill"): 0.835,
    ("L8_mixed", "adaptive"): 0.795,
    ("L9_broken_tounicode", "native"): 0.003,
    ("L9_broken_tounicode", "fill"): 0.745,
    ("L9_broken_tounicode", "adaptive"): 0.751,
}


def run(
    directory: Path, levels: tuple[str, ...], policies: tuple[str, ...], dpi: float, threads: int
) -> dict[str, Any]:
    directory = guard_path(directory)
    engine = pdfust.OcrEngine(threads=threads)
    truths: dict[str, dict[str, Any]] = {}
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    timings: dict[str, dict[str, float]] = defaultdict(lambda: {"pages": 0.0, "seconds": 0.0, "filled": 0.0})
    start = _measure()
    with tempfile.TemporaryDirectory(prefix="ocr-fill-") as tmp:
        for variant in sorted(p for p in (directory / "variants").iterdir() if p.is_dir()):
            truths[variant.name] = json.loads((directory / "docs" / variant.name / "truth.json").read_text())
            for level in levels:
                source = variant / f"{level}.pdf"
                for policy in ("native", *policies):
                    arm = f"{level}+{policy}"
                    target = source
                    if policy != "native":
                        target = Path(tmp) / f"{variant.name}-{arm}.pdf"
                        began = time.perf_counter()
                        with pdfust.open(str(source)) as doc:
                            for page in doc:
                                result = page.ocr_fill(policy=policy, dpi=dpi, engine=engine)  # type: ignore[arg-type]
                                timings[arm]["filled"] += result["filled"]
                                timings[arm]["pages"] += 1
                            doc.save(str(target))
                        timings[arm]["seconds"] += time.perf_counter() - began
                    row = audit_pdf(target, truths[variant.name])
                    row.update(doc_id=variant.name, level=arm)
                    rows[arm].append(row)
    summary = summarize([row for arm_rows in rows.values() for row in arm_rows])
    return {"summary": summary, "timings": dict(timings), "resources": _delta(start), "dpi": dpi, "threads": threads}


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Library OCR-fill validation (wild-v1 DEV)",
        "",
        f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}; `Page.ocr_fill`, dpi {result['dpi']}, "
        f"{result['threads']} OCR threads, PP-OCR via pdfust-ocr-models. Synthetic DEV documents; not a real-world claim.",
        "Text F1 is character-bigram multiset overlap against truth (`bench/wild_corpus.audit_pdf`). `Recorded` is the "
        "bench-only policy in `bench/results/wild-v1-latest.md`.",
        "",
        "| Arm | Docs | Text F1 | Recorded | Markdown F1 | Table cell recall | Pages | Filled words | s/page |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, entry in result["summary"].items():
        level, policy = arm.split("+", 1)
        timing = result["timings"].get(arm)
        pages = int(timing["pages"]) if timing else 0
        lines.append(
            f"| {arm} | {entry['documents']} | {entry['text_f1']:.3f} | {RECORDED.get((level, policy), float('nan')):.3f} | "
            f"{entry['markdown_f1']:.3f} | {entry['table_cell_recall'] or 0:.3f} | {pages or '—'} | "
            f"{int(timing['filled']) if timing else '—'} | "
            f"{(timing['seconds'] / pages) if pages else float('nan'):.2f} |"
        )
    resources = result["resources"]
    lines += [
        "",
        f"Whole run: {resources['wall_seconds']:.0f} s wall, {resources['cpu_seconds_self']:.0f} s CPU, peak RSS "
        f"{resources['peak_rss_kib_self'] / 1024:.0f} MiB ({resources['measurement']}).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--levels", nargs="+", default=list(DEFAULT_LEVELS))
    parser.add_argument("--policies", nargs="+", default=["fill", "adaptive"])
    parser.add_argument("--dpi", type=float, default=200)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "bench/results/ocr-fill-latest.md")
    args = parser.parse_args()
    result = run(args.directory, tuple(args.levels), tuple(args.policies), args.dpi, args.threads)
    args.output.write_text(render(result), encoding="utf-8")
    print(render(result))


if __name__ == "__main__":
    main()
