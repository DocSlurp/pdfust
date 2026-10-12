"""Native consumers find the CJK fallback fonts through PDFUST_FONTS_DIR (no Python extras)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from conftest import build_nonembedded_cjk_pdf

FONTS = Path(__file__).parents[1] / "fonts"
JP_DIR = FONTS / "pdfust-fonts-jp" / "src" / "pdfust_fonts_jp"

# Bypasses Document._ensure_fallback_fonts, which is what Python callers use to find the
# installed extras, so only the Rust-side discovery can supply a font.
_CHILD = """
import hashlib, sys
import pdfust
doc = pdfust.open(stream=sys.stdin.buffer.read())
print(hashlib.sha256(doc._doc.render_page_png(1, 1.0, None, None)).hexdigest())
"""


def _render_digest(env_dir: Path | None) -> str:
    env = {k: v for k, v in os.environ.items() if k != "PDFUST_FONTS_DIR"}
    if env_dir is not None:
        env["PDFUST_FONTS_DIR"] = str(env_dir)
    result = subprocess.run(  # noqa: S603 - fixed interpreter and script.
        [sys.executable, "-c", _CHILD],
        input=build_nonembedded_cjk_pdf(),
        capture_output=True,
        env=env,
        check=True,
    )
    return result.stdout.decode().strip()


def test_fonts_dir_env_supplies_nonembedded_cjk_glyphs() -> None:
    blank = _render_digest(None)
    drawn = _render_digest(JP_DIR)
    assert drawn != blank


def test_fonts_dir_env_accepts_site_packages_layout() -> None:
    assert _render_digest(FONTS / "pdfust-fonts-jp" / "src") == _render_digest(JP_DIR)
