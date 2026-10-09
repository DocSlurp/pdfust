"""CPU-only admission and source invariance checks for operator evidence."""

import hashlib
import json
import zlib

import pytest
from bench.feature_cases import page_pdf, raw_pdf, stream_object
from bench.lowlevel_operators import extract_operators


def test_literal_text_and_adjustments_preserve_source_bytes() -> None:
    raw = page_pdf("BT /F1 12 Tf 1 0 0 1 40 700 Tm [(AB) -20 <4344>] TJ ET")
    result = extract_operators(raw)
    assert result["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["complete_for_page"]
    assert result["glyph_operator_mapping"] == "unavailable"
    operation = result["operators"][3]
    assert operation["operator"] == "TJ"
    left, adjustment, right = operation["operands"][0]
    assert left["bytes_hex"] == "4142"
    assert right["bytes_hex"] == "4344"
    assert adjustment == -20
    assert left["unicode_status"] == "not_font_decoded"
    assert result["source_string_bytes"] == 4
    assert json.dumps(result, sort_keys=True) == json.dumps(extract_operators(raw), sort_keys=True)


def test_equal_pixels_do_not_imply_equal_operator_encoding() -> None:
    pymupdf = pytest.importorskip("pymupdf")
    variants = (
        "BT /F1 12 Tf 1 0 0 1 40 700 Tm (AB CD) Tj ET",
        "BT /F1 12 Tf 1 0 0 1 40 700 Tm [(AB CD)] TJ ET",
        "BT /F1 12 Tf 1 0 0 1 40 700 Tm (AB) Tj ( CD) Tj ET",
        "q BT /F1 12 Tf 1 0 0 1 40 700 Tm (AB CD) Tj ET Q",
    )
    pixels, glyphs, operators = [], [], []
    for content in variants:
        raw = page_pdf(content)
        with pymupdf.open(stream=raw, filetype="pdf") as document:
            pixels.append(hashlib.sha256(document[0].get_pixmap(alpha=True).samples).hexdigest())
            glyphs.append([char for run in document[0].get_texttrace() for char in run["chars"]])
        operators.append(extract_operators(raw)["operators"])
    assert len(set(pixels)) == 1
    assert all(value == glyphs[0] for value in glyphs)
    assert all(value != operators[0] for value in operators[1:])


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        ("q " * 33 + "Q " * 33, "nesting"),
        ("BT (x) Tj", "unterminated"),
        ("Q", "unbalanced"),
        ("[" * 33 + "]" * 33 + " TJ", "nesting"),
        ("BT (" + "x" * 65537 + ") Tj ET", "string bytes"),
        ("0 g\n" * 4097, "operator count"),
        ("% " + "x" * (256 * 1024), "decoded content"),
    ],
)
def test_complete_refusal(content: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        extract_operators(page_pdf(content))


def test_flate_is_bounded_before_complete_decompression() -> None:
    raw = raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents 4 0 R >>",
            stream_object(zlib.compress(b"x" * (256 * 1024 + 1)), "/Filter /FlateDecode"),
        ]
    )
    with pytest.raises(ValueError, match="decoded content"):
        extract_operators(raw)


def test_actualtext_is_source_observation_and_xobjects_are_not_traversed() -> None:
    result = extract_operators(page_pdf("/Span << /ActualText (different) >> BDC BT (x) Tj ET EMC /X1 Do"))
    assert result["operators"][0]["operands"][1]["/ActualText"]["parser_text"] == "different"
    assert not result["complete_for_page"]
    assert result["unsupported_xobject_calls"][0]["operator"] == "Do"


def test_input_and_page_admission() -> None:
    with pytest.raises(ValueError, match="2 MiB"):
        extract_operators(b"x" * (2 * 1024 * 1024 + 1))
    for page in (-1, True, 1):
        with pytest.raises(ValueError, match="page index"):
            extract_operators(page_pdf(""), page)


def test_multiple_streams_and_compression() -> None:
    raw = raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents [4 0 R 5 0 R] >>",
            stream_object("q"),
            stream_object(zlib.compress(b"Q"), "/Filter /FlateDecode"),
        ]
    )
    assert [item["operator"] for item in extract_operators(raw)["operators"]] == ["q", "Q"]
