"""Validate authored math probes without certifying mathematical extraction."""

from __future__ import annotations

import re
import warnings

import pytest
from bench.silver_math import ENCODINGS, FORMULAS, MathCase, generate_cases

import pylopdf

CASES = generate_cases()


def test_math_cases_cover_related_encodings_deterministically() -> None:
    assert len(CASES) == 40
    assert len({case["id"] for case in CASES}) == 40
    assert generate_cases() == CASES
    assert {case["encoding"] for case in CASES} == set(ENCODINGS)
    assert len({case["reference_math"] for case in CASES}) == len(FORMULAS) == 4
    assert len({case["producer_group"] for case in CASES}) == 4
    for case in CASES:
        assert case["license"] == "MIT"
        assert case["provenance"] == "repository-authored"
        assert "Silver" in case["notes"]
        assert len(case["expected_text"]) == 1
        assert case["expected_text"][0].startswith("Reference ")
        assert case["encoding"] not in case["expected_text"][0]
        assert case["reference_math"] not in case["pdf"].decode("latin-1")


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_math_cases_load_and_extract_visible_anchor(case: MathCase) -> None:
    # Unmapped Type3 warnings are deliberate; checking an anchor is not a claim
    # that a formula's mathematical structure survived extraction.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", pylopdf.PylopdfWarning)
        with pylopdf.open(stream=case["pdf"]) as document:
            assert len(document) == 1
            text = document[0].get_text()
            assert case["expected_text"][0] in text
            assert case["expected_text"][0] in document.to_markdown()


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_each_math_encoding_has_a_nonblank_formula(encoding: str) -> None:
    case = next(case for case in CASES if case["id"] == f"math-quadratic-{encoding}")
    with pylopdf.open(stream=case["pdf"]) as document:
        # This display-coordinate region excludes both digital headings.
        pixmap = document[0].get_pixmap(dpi=72, clip=(35, 145, 550, 290))
        assert pixmap.n == 4
        assert sum(value < 180 for value in pixmap.samples[0::4]) > 300
        assert all(value == 255 for value in pixmap.samples[3::4])


def _case(encoding: str) -> MathCase:
    return next(case for case in CASES if case["id"] == f"math-quadratic-{encoding}")


def test_math_fonts_and_content_are_genuine_encoding_interventions() -> None:
    literal = _case("literal-tj")["pdf"]
    kerned = _case("split-kerned-tj")["pdf"]
    assert b"(X = \\(-B +/- SQRT" in literal
    assert b" Tj ET" in literal
    assert b"] TJ" in kerned
    assert b" -8 " in kerned
    assert b"/ActualText <feff" in _case("actualtext")["pdf"]
    mapped = _case("type3-mapped")["pdf"]
    unmapped = _case("type3-unmapped")["pdf"]
    multichar = _case("tounicode-multichar")["pdf"]
    assert b"/Subtype /Type3" in mapped
    assert b"/ToUnicode 7 0 R" in mapped
    assert b"/Subtype /Type3" in unmapped
    assert b"/ToUnicode" not in unmapped
    # At least one CMap source byte maps to two UTF-16 code units.
    assert re.search(rb"<[0-9A-F]{2}> <[0-9a-f]{8}>", multichar)
    assert b"/Subtype /Type0" not in multichar
    positioned = _case("positioned-math")["pdf"]
    assert b"/F1 9 Tf" in positioned
    assert b" m " in positioned
    assert b" l S" in positioned


def test_outline_and_raster_formulas_have_no_formula_text_layer() -> None:
    for encoding in ("vector-outlines", "raster-image", "type3-unmapped"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pylopdf.PylopdfWarning)
            with pylopdf.open(stream=_case(encoding)["pdf"]) as document:
                text = document[0].get_text()
                assert "SQRT" not in text
                if encoding == "raster-image":
                    assert len(document[0].get_images()) == 1
                if encoding == "vector-outlines":
                    assert len(document[0].get_drawings()) > 100
    assert b"/Subtype /Image" in _case("raster-image")["pdf"]
    assert b"/Subtype /Image" not in _case("vector-outlines")["pdf"]
    assert b"3 Tr" in _case("raster-invisible-text")["pdf"]
    with pylopdf.open(stream=_case("raster-invisible-text")["pdf"]) as document:
        assert "SQRT" in document[0].get_text()
        assert len(document[0].get_images()) == 1
