"""Check authored silver inputs independently of inferred reading relationships."""

from __future__ import annotations

import struct

import pytest
from bench.silver_layouts import generate_cases

import pdfust

CASES = generate_cases()


def test_layout_source_integrity() -> None:
    assert len(CASES) == 64
    assert len({case["id"] for case in CASES}) == 64
    assert len({case["producer_group"] for case in CASES}) == 16
    assert [case["pdf"] for case in CASES] == [case["pdf"] for case in generate_cases()]
    assert all(case["license"] == "MIT" and case["provenance"] == "repository-authored" for case in CASES)
    # References stay outside the PDF: no metadata attachment or hidden text mode.
    assert all(b"/EmbeddedFiles" not in case["pdf"] and b"/ActualText" not in case["pdf"] for case in CASES)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_layout_visible_sources(case: dict) -> None:
    with pdfust.open(stream=case["pdf"]) as document:
        assert document.page_count == case["page_count"]
        text = document.get_text()
        # Overprints and geometry can legitimately change ordering or spacing.
        # The title is an ordinary visible source anchor in every physical page.
        for page in range(document.page_count):
            assert f"page {page + 1}" in text
            assert case["expected_text"][0] in text
        if case["family"] in {"image-inset", "image-flow", "mixed-panels", "rotated-page", "cropped-page"}:
            images = document[0].get_images()
            assert len(images) == (2 if case["family"] == "image-flow" else 1)
            assert all(image["width"] == 16 and image["height"] == 16 for image in images)
        if case["family"] == "headers-footers":
            assert text.count("Recurring report header") == document.page_count
            assert text.count("Recurring report footer") == document.page_count
        if case["family"] == "form-fields":
            assert b"/AcroForm" in case["pdf"]
            assert b"/Subtype /Widget" in case["pdf"]
            assert "Ada Example" in text


@pytest.mark.parametrize(
    "family", ["image-flow", "rotated-page", "cropped-page", "multilevel-table", "form-fields", "duplicate-overprint"]
)
def test_layout_bounded_render(family: str) -> None:
    case = next(case for case in CASES if case["family"] == family and case["id"].endswith("v3"))
    with pdfust.open(stream=case["pdf"]) as document:
        png = document.render_page(0, scale=0.2, max_size=256 * 1024)
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        assert 50 <= width <= 200
        assert 50 <= height <= 200
