"""Invisible (render mode 3) text is document text; spans keep naming fonts.

OCR layers under scans are invisible text. Default extraction must keep them,
word gaps must survive size changes between words, and an explicit option must
leave them out. Span font names must also exist for non-embedded fonts.
"""

from __future__ import annotations

import pdfust


def _scan_like_doc() -> pdfust.Document:
    """One page whose only text is an invisible layer with per-word sizes."""
    doc = pdfust.Document()
    page = doc.new_page(width=300, height=200)
    page.insert_ocr_text_layer(
        [
            (10, 20, 40, 32, "Quarterly"),
            (44, 20, 70, 31, "report"),
            (74, 20, 100, 34, "summary"),
        ]
    )
    return doc


def test_invisible_text_is_included_by_default() -> None:
    page = _scan_like_doc()[0]
    assert page.get_text().split() == ["Quarterly", "report", "summary"]
    assert "Quarterly report summary" in page.to_markdown()


def test_markdown_keeps_spaces_between_spans_of_different_size() -> None:
    markdown = _scan_like_doc()[0].to_markdown()
    assert "Quarterlyreport" not in markdown
    assert "reportsummary" not in markdown


def test_include_invisible_false_leaves_the_layer_out() -> None:
    doc = _scan_like_doc()
    page = doc[0]
    assert page.get_text(include_invisible=False) == ""
    assert page.to_markdown(include_invisible=False) == ""
    assert doc.get_text(include_invisible=False) == ""
    # The per-call option does not stick.
    assert doc.skip_invisible_text is False
    assert "Quarterly" in page.get_text()


def test_skip_invisible_text_property_and_spans() -> None:
    doc = _scan_like_doc()
    doc.skip_invisible_text = True
    page = doc[0]
    assert page.get_text() == ""
    assert page.get_text(include_invisible=True).split() == ["Quarterly", "report", "summary"]
    spans = page.get_text_spans()
    assert spans
    assert all(span["invisible"] for span in spans)


def test_span_font_name_for_non_embedded_font() -> None:
    doc = pdfust.Document()
    page = doc.new_page(width=300, height=200)
    page.insert_text((20, 50), "Plain words", fontname="helv", fontsize=12)
    fonts = {span["font"] for span in page.get_text_spans()}
    assert fonts
    assert all(fonts), fonts
    assert any("Helvetica" in font for font in fonts)
