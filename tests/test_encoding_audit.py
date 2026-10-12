"""Check the metamorphic audit's independently authored expectations."""

from __future__ import annotations

import pytest
from bench.encoding_audit import REFERENCE, cases, encoded_pdf, evaluate, matrix

import pdfust


@pytest.mark.parametrize(
    "mode",
    [
        "literal",
        "glyph-tj",
        "array-tj",
        "hex",
        "shuffled",
        "flate",
        "contents-array",
        "inherited-resources",
        "form-xobject",
        "translated-crop",
    ],
)
def test_encoding_variants_preserve_known_cells(mode: str) -> None:
    with pdfust.open(stream=encoded_pdf(mode)) as document:
        assert [matrix(table) for table in document[0].get_layout().tables] == [REFERENCE]


def test_encoding_changes_preserve_pixels() -> None:
    with pdfust.open(stream=encoded_pdf()) as document:
        expected = document[0].get_pixmap(dpi=72).tobytes()
    for mode in (
        "glyph-tj",
        "array-tj",
        "hex",
        "shuffled",
        "flate",
        "contents-array",
        "inherited-resources",
        "form-xobject",
    ):
        with pdfust.open(stream=encoded_pdf(mode)) as document:
            assert document[0].get_pixmap(dpi=72).tobytes() == expected


def test_visibility_controls_do_not_claim_visible_truth() -> None:
    with pdfust.open(stream=encoded_pdf()) as document:
        baseline = document[0].get_pixmap(dpi=72).tobytes()
    for mode in ("clip-empty", "white-cover", "invisible-text"):
        with pdfust.open(stream=encoded_pdf(mode)) as document:
            assert [matrix(table) for table in document[0].get_layout().tables] == [REFERENCE]
            assert document[0].get_pixmap(dpi=72).tobytes() != baseline


def test_mixed_scan_defeats_page_empty_routing() -> None:
    result = evaluate(next(case for case in cases() if case.name == "mixed-scan"), repetitions=1)
    assert result["page_empty_ocr_gate"] is False
    assert result["unresolved_raster_evidence"] is True
    assert result["exact_grid"] is False


def test_image_routing_is_not_table_detection() -> None:
    observations = {case.name: evaluate(case, repetitions=1) for case in cases() if case.cohort == "ocr-negative"}
    assert observations["logo"]["unresolved_raster_evidence"] is True
    assert observations["logo"]["large_raster_gate"] is False
    assert observations["raster-illustration"]["large_raster_gate"] is True
    assert all(result["table_count"] == 0 for result in observations.values())
