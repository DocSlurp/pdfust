"""Per-page timings of the Python API; mirrors scripts/bench.mjs.

Usage: python bench.py <repeats> <pdf...>  -> JSON on stdout
"""

from __future__ import annotations

import json
import os
import resource
import sys
import time

import pdfust

RENDER_PAGES = 12


def median(values: list[float]) -> float:
    return sorted(values)[len(values) // 2]


def main() -> None:
    repeats = int(sys.argv[1])
    out = {"engine": "python", "version": pdfust.__version__ if hasattr(pdfust, "__version__") else "?", "files": {}}
    for path in sys.argv[2:]:
        rows: dict[str, list[float]] = {"open": [], "text": [], "markdown": [], "markdownText": [], "render72": []}
        pages = 0
        for _ in range(repeats):
            t = time.perf_counter()
            doc = pdfust.open(path)
            rows["open"].append((time.perf_counter() - t) * 1000)
            pages = doc.page_count

            def timed(count: int, run) -> float:
                nonlocal doc
                doc.close()
                doc = pdfust.open(path)
                start = time.perf_counter()
                for i in range(count):
                    run(doc[i])
                return (time.perf_counter() - start) * 1000 / count

            rows["text"].append(timed(pages, lambda page: page.get_text("text")))
            rows["markdown"].append(timed(pages, lambda page: page.to_markdown(table_strategy="lines")))
            rows["markdownText"].append(timed(pages, lambda page: page.to_markdown(table_strategy="text")))
            rows["render72"].append(timed(min(pages, RENDER_PAGES), lambda page: page.render(dpi=72)))
            doc.close()
        out["files"][os.path.basename(path)] = {"pages": pages, **{k: round(median(v), 3) for k, v in rows.items()}}
    out["maxRssMb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()
