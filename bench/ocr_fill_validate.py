"""Validate the library ``Page.ocr_fill`` policies on the wild-v1 DEV corpus.

Compares the library implementation with the recorded bench-only
``ocr-fill`` / ``ocr-adaptive`` numbers (``bench/wild_corpus.py``) on the same
levels and scoring (``audit_pdf``: character-bigram text F1 against truth).
DEV only; synthetic documents. Example::

    uv run python -m bench.ocr_fill_validate --levels L8_mixed L9_broken_tounicode
"""

# ruff: noqa: D103, E501, ISC004
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


def run(  # noqa: PLR0913, PLR0917 - shard and cache controls are explicit.
    directory: Path,
    cache: Path,
    levels: tuple[str, ...],
    policies: tuple[str, ...],
    dpi: float,
    threads: int,
    shard: tuple[int, int],
) -> None:
    """Fill and audit every document of this shard, caching one JSON row per (document, arm)."""
    directory = guard_path(directory)
    cache.mkdir(parents=True, exist_ok=True)
    engine = pdfust.OcrEngine(threads=threads)
    index, count = shard
    variants = sorted(p for p in (directory / "variants").iterdir() if p.is_dir())
    with tempfile.TemporaryDirectory(prefix="ocr-fill-") as tmp:
        for number, variant in enumerate(variants):
            if number % count != index:
                continue
            truth = json.loads((directory / "docs" / variant.name / "truth.json").read_text())
            for level in levels:
                source = variant / f"{level}.pdf"
                for policy in ("native", *policies):
                    arm = f"{level}+{policy}"
                    row_path = cache / f"{variant.name}__{arm}.json"
                    if row_path.exists():
                        continue
                    target = source
                    timing = {"pages": 0, "seconds": 0.0, "filled": 0}
                    if policy != "native":
                        target = Path(tmp) / f"{variant.name}-{arm}.pdf"
                        began = time.perf_counter()
                        start = _measure()
                        with pdfust.open(str(source)) as doc:
                            for page in doc:
                                result = page.ocr_fill(policy=policy, dpi=dpi, engine=engine)  # type: ignore[arg-type]
                                timing["filled"] += result["filled"]
                                timing["pages"] += 1
                            doc.save(str(target))
                        timing["seconds"] = time.perf_counter() - began
                        timing["cpu_seconds"] = _delta(start)["cpu_seconds_self"]
                    row = audit_pdf(target, truth)
                    row.update(doc_id=variant.name, level=arm, timing=timing)
                    row_path.write_text(json.dumps(row), encoding="utf-8")


def aggregate(cache: Path, dpi: float, threads: int) -> dict[str, Any]:
    """Summarize cached rows per arm."""
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(cache.glob("*.json"))]
    timings: dict[str, dict[str, float]] = defaultdict(
        lambda: {"pages": 0.0, "seconds": 0.0, "filled": 0.0, "cpu": 0.0}
    )
    for row in rows:
        entry = timings[row["level"]]
        entry["pages"] += row["timing"]["pages"]
        entry["seconds"] += row["timing"]["seconds"]
        entry["filled"] += row["timing"]["filled"]
        entry["cpu"] += row["timing"].get("cpu_seconds", 0.0)
    return {"summary": summarize(rows), "timings": dict(timings), "dpi": dpi, "threads": threads}


def render(result: dict[str, Any]) -> str:
    lines = [
        "# Library OCR-fill validation (wild-v1 DEV)",
        "",
        f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}; `Page.ocr_fill`, dpi {result['dpi']}, "
        f"{result['threads']} OCR threads, PP-OCR via pdfust-ocr-models. Synthetic DEV documents; not a real-world claim.",
        "Text F1 is character-bigram multiset overlap against truth (`bench/wild_corpus.audit_pdf`). `Recorded` is the "
        "bench-only policy in `bench/results/wild-v1-latest.md`.",
        "",
        "| Arm | Docs | Text F1 | Recorded | Markdown F1 | Table cell recall | Pages | Filled words | s/page | cpu s/page |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, entry in result["summary"].items():
        level, policy = arm.split("+", 1)
        timing = result["timings"].get(arm)
        pages = int(timing["pages"]) if timing else 0
        lines.append(
            f"| {arm} | {entry['documents']} | {entry['text_f1']:.3f} | {RECORDED.get((level, policy), float('nan')):.3f} | "
            f"{entry['markdown_f1']:.3f} | {entry['table_cell_recall'] or 0:.3f} | {pages or '—'} | "
            f"{int(timing['filled']) if timing else '—'} | "
            f"{(timing['seconds'] / pages) if pages else float('nan'):.2f} | "
            f"{(timing['cpu'] / pages) if pages else float('nan'):.2f} |"
        )
    lines += [
        "",
        "`s/page` is wall time of `ocr_fill` plus the in-memory text/Markdown rebuild, measured on a host shared with other "
        "jobs (load average noted in the commit message), so treat it as an upper bound; `cpu s/page` is process CPU time "
        "(`getrusage`, whole process including OCR threads).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--cache", type=Path, default=ROOT / "bench/results/pdf-master-artifacts/ocr-fill-lib-v1")
    parser.add_argument("--levels", nargs="+", default=list(DEFAULT_LEVELS))
    parser.add_argument("--policies", nargs="+", default=["fill", "adaptive"])
    parser.add_argument("--dpi", type=float, default=200)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--shard", default="0/1", help="i/n: run documents whose index mod n equals i")
    parser.add_argument("--report", action="store_true", help="aggregate cached rows instead of running")
    parser.add_argument("--output", type=Path, default=ROOT / "bench/results/ocr-fill-latest.md")
    args = parser.parse_args()
    if not args.report:
        index, count = (int(part) for part in args.shard.split("/"))
        run(
            args.directory, args.cache, tuple(args.levels), tuple(args.policies), args.dpi, args.threads, (index, count)
        )
        return
    report = render(aggregate(args.cache, args.dpi, args.threads))
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
