"""Bundled locale sharing preserves per-call budgets and file freshness."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from conftest import build_nonembedded_cjk_pdf

import pdfust

FONT = Path(__file__).parents[1] / "fonts" / "pdfust-fonts-jp" / "src" / "pdfust_fonts_jp" / "NotoSansJP-Regular.otf"


def _configure(doc: pdfust.Document, font: Path, limit: int | None) -> None:
    # Automatic locale discovery uses this native boundary; explicit setters
    # intentionally have different ownership and do not use the shared registry.
    doc._doc.set_fallback_font_locale_files(  # noqa: SLF001
        [("ja", str(font), str(font))], max_font_size=limit
    )


def test_shared_locale_font_still_enforces_each_callers_limit(tmp_path: Path) -> None:
    font = tmp_path / "bundled.otf"
    font.write_bytes(b"A" * 64)
    first = pdfust.open()
    _configure(first, font, None)
    second = pdfust.open()

    with pytest.raises(pdfust.LimitError) as caught:
        _configure(second, font, 63)

    assert caught.value.code == "font_input_size"
    _configure(second, font, 64)


def test_modified_locale_font_is_read_again_under_new_limit(tmp_path: Path) -> None:
    font = tmp_path / "bundled.otf"
    font.write_bytes(b"A" * 64)
    first = pdfust.open()
    _configure(first, font, None)

    font.write_bytes(b"B" * 16)
    second = pdfust.open()
    _configure(second, font, 16)
    with pytest.raises(pdfust.LimitError) as caught:
        _configure(second, font, 15)
    assert caught.value.code == "font_input_size"


@pytest.mark.skipif(os.name == "nt", reason="Unix file identity distinguishes preserved timestamps")
def test_replaced_locale_font_with_same_size_and_mtime_is_read_again(tmp_path: Path) -> None:
    font = tmp_path / "bundled.otf"
    original = FONT.read_bytes()
    font.write_bytes(original)
    first = pdfust.open(stream=build_nonembedded_cjk_pdf())
    first.set_fallback_font(None)
    _configure(first, font, None)
    before = first.render_page(0)
    original_stat = font.stat()

    # A package update can preserve size and timestamps. New inode identity
    # must invalidate the entry while already-open Documents retain their bytes.
    replacement = tmp_path / "replacement.otf"
    replacement.write_bytes(b"BAD!" + original[4:])
    os.utime(replacement, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    replacement.replace(font)
    assert font.stat().st_size == original_stat.st_size
    assert font.stat().st_mtime_ns == original_stat.st_mtime_ns

    second = pdfust.open(stream=build_nonembedded_cjk_pdf())
    second.set_fallback_font(None)
    _configure(second, font, None)
    assert second.render_page(0) != before
    assert first.render_page(0) == before
