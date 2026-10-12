"""Compare locale font sharing with explicit uncached loads in isolated Linux processes.

Run with: uv run python bench/font_sharing.py
This measures retained font bytes, not page rendering or a historical release.
"""

from __future__ import annotations

import argparse
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import pdfust

ROOT = Path(__file__).resolve().parent.parent
MAX_DOCUMENTS = 64


def main() -> None:
    """Run each ownership mode in a fresh process and report time and peak RSS."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("shared", "uncached"))
    parser.add_argument("--documents", type=int, default=16)
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("RSS units and this comparison are validated on Linux only")
    if not 1 <= args.documents <= MAX_DOCUMENTS:
        parser.error("--documents must be between 1 and 64")
    if args.mode is None:
        for mode in ("uncached", "shared"):
            subprocess.run(  # noqa: S603 - fixed interpreter and repository script.
                [sys.executable, str(Path(__file__).resolve()), "--mode", mode, "--documents", str(args.documents)],
                check=True,
            )
        return
    base = ROOT / "fonts" / "pdfust-fonts-jp" / "src" / "pdfust_fonts_jp"
    sans = str(base / "NotoSansJP-Regular.otf")
    serif = str(base / "NotoSerifJP-Regular.otf")
    documents = [pdfust.Document() for _ in range(args.documents)]
    start = time.perf_counter()
    for document in documents:
        if args.mode == "shared":
            document._doc.set_fallback_font_locale_files([("ja", sans, serif)])  # noqa: SLF001
        else:
            document._doc.set_fallback_font_files(sans, serif)  # noqa: SLF001
    print(
        json.dumps(
            {
                "mode": args.mode,
                "documents": len(documents),
                "elapsed_seconds": time.perf_counter() - start,
                "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            }
        )
    )


if __name__ == "__main__":
    main()
