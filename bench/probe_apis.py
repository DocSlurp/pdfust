"""Time the per-page inspection APIs used by routing probes.

Measures ``scan()`` (spans plus image placements), ``get_image_info()``,
``get_text_spans()``, ``get_fonts()``, ``widgets()``, ``annots()``,
``get_links()`` and ``get_images()`` (decoding, for contrast) against plain
``get_text()`` on the licensed real-world fixtures and, when present, the
wild-v1 DEV variants. One warmup pass, then the median of five passes per
document with a fresh ``Document`` per pass for the first call (cold) and a
reused one for the rest (warm). Writes ``bench/results/probe-apis-latest.md``.
"""

# ruff: noqa: D103, E501, ISC004
from __future__ import annotations

import argparse
import resource
import statistics
import time
import warnings
from pathlib import Path
from typing import Any

import pdfust

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "assets" / "real_world"
WILD = ROOT / "bench" / "results" / "pdf-master-artifacts" / "wild-v1" / "variants"
WILD_LEVELS = ("L0_tagged", "L4_raster", "L8_mixed", "R20_scanner_ocr_layer")
MAX_PAGES = 20

CALLS: dict[str, Any] = {
    "get_text": lambda p: p.get_text(),
    "scan": lambda p: p.scan(),
    "get_text_spans": lambda p: p.get_text_spans(),
    "get_image_info": lambda p: p.get_image_info(),
    "get_images (decodes)": lambda p: p.get_images(),
    "get_fonts": lambda p: p.get_fonts(),
    "widgets": lambda p: p.widgets(),
    "annots": lambda p: p.annots(),
    "get_links": lambda p: p.get_links(),
}


def collect(paths: list[Path], passes: int) -> dict[str, list[float]]:
    """Milliseconds per page per call, one sample per (document, call)."""
    samples: dict[str, list[float]] = {name: [] for name in CALLS}
    for path in paths:
        try:
            doc = pdfust.open(str(path))
        except pdfust.PdfError:
            continue
        with doc:
            pages = [doc[i] for i in range(min(len(doc), MAX_PAGES))]
            for name, call in CALLS.items():
                for page in pages:
                    call(page)  # warmup: fills font caches the same way for every call
                times = []
                for _ in range(passes):
                    start = time.perf_counter()
                    for page in pages:
                        call(page)
                    times.append((time.perf_counter() - start) * 1000 / len(pages))
                samples[name].append(statistics.median(times))
    return samples


def render(samples: dict[str, list[float]], documents: int) -> str:
    lines = [
        "# Per-page inspection API timings",
        "",
        f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}. {documents} documents (licensed real-world "
        "fixtures plus wild-v1 DEV variants when present), at most 20 pages each, median of 5 passes after a warmup, "
        "single thread, reused `Document`. Milliseconds per page; the p50/p90/max columns are over documents, not pages.",
        "",
        "| Call | Median ms/page | p90 ms/page | Max ms/page |",
        "|---|---:|---:|---:|",
    ]
    for name, values in samples.items():
        ordered = sorted(values)
        p90 = ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))]
        lines.append(f"| `{name}` | {statistics.median(ordered):.2f} | {p90:.2f} | {ordered[-1]:.2f} |")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    lines += [
        "",
        f"Process peak RSS {peak:.0f} MiB (getrusage, lifetime). `scan()` is one interpretation pass; "
        "`get_text_spans()` and `get_image_info()` are `scan()` with one product disabled.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wild", type=Path, default=WILD)
    parser.add_argument("--passes", type=int, default=5)
    parser.add_argument("--output", type=Path, default=ROOT / "bench/results/probe-apis-latest.md")
    args = parser.parse_args()
    paths = sorted(FIXTURES.glob("*.pdf"))
    if args.wild.exists():
        for variant in sorted(p for p in args.wild.iterdir() if p.is_dir()):
            paths += [variant / f"{level}.pdf" for level in WILD_LEVELS if (variant / f"{level}.pdf").exists()]
    warnings.simplefilter("ignore")
    samples = collect(paths, args.passes)
    report = render(samples, len(samples["scan"]))
    args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
