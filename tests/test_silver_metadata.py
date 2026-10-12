"""Verify descriptive silver metadata denominators and geometry semantics."""

from __future__ import annotations

import json
import zlib

import pytest

import pdfust

pytest.importorskip("pypdf")

from bench.feature_cases import page_pdf, raw_pdf, stream_object, text_op
from bench.silver_metadata import analyze_pdf, union_area


def _simple_pdf(
    content: bytes, *, attributes: str = "", extra_page: str = "", extras: tuple[bytes | str, ...] = ()
) -> bytes:
    return raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R /Version /2.0 >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents 4 0 R {extra_page} >>",
            stream_object(content, attributes),
            *extras,
        ]
    )


def test_union_area_does_not_double_count_overlap() -> None:
    assert union_area([(0, 0, 100, 100), (50, 0, 150, 100), (0, 0, 0, 100)]) == 15000
    assert union_area([]) == 0


def test_raster_only_counts_placements_and_clips_page_bounds() -> None:
    data = _simple_pdf(
        b"q 100 0 0 100 -50 0 cm /Im Do Q q 100 0 0 100 0 0 cm /Im Do Q q 10 0 0 10 200 0 cm /Im Do Q",
        extra_page="/Resources << /XObject << /Im 5 0 R >> >>",
        extras=(
            stream_object(
                b"\xff\x00\x00",
                "/Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8",
            ),
        ),
    )
    result = analyze_pdf(data)
    assert result["errors"] == []
    page = result["pages"][0]
    assert page["image_placement_count"] == 3
    assert [image["clipped_bbox_coverage_percent"] for image in page["images"]] == [50, 100, 0]
    assert page["images"][2]["clipped_bbox"] == [100, 90, 100, 100]
    assert page["image_placement_coverage_bins"] == {
        "0-10": 1,
        "10-25": 0,
        "25-50": 0,
        "50-75": 1,
        "75-100": 1,
    }
    assert page["image_coverage_percent"] == 100
    assert page["image_individual_sum_percent"] == 150
    assert result["percent_pages_with_images"] == 100
    assert result["image_coverage_bins"]["75-100"] == 1
    assert result["content"]["image_resource_count"] == 1
    assert result["content"]["image_resources"][0]["encoded_payload_bytes"] == 3
    assert page["text"]["characters"] == 0
    assert result["content"]["text_showing_operand_bytes_executed"] == 0
    assert result["declared_pdf_version"] == "1.7"
    assert result["effective_pdf_version"] == "2.0"
    json.dumps(result, allow_nan=False)


def test_empty_page_has_valid_zero_values_and_undefined_ratio() -> None:
    result = analyze_pdf(page_pdf(""))
    assert result["errors"] == []
    assert result["pages"][0]["image_placement_count"] == 0
    assert result["pages"][0]["image_placement_coverage_bins"] == {
        "0-10": 0,
        "10-25": 0,
        "25-50": 0,
        "50-75": 0,
        "75-100": 0,
    }
    assert result["pages"][0]["text"]["word_count"] == 0
    assert result["percent_pages_with_images"] == 0
    assert result["image_coverage_bins"]["0-10"] == 1
    assert result["content"]["decoded_content_bytes"] == 0
    assert result["content"]["content_encoded_to_decoded_ratio"] is None
    assert result["content"]["decoded_content_string_fraction"] is None


def test_compressed_and_plain_content_have_same_decoded_string_counts() -> None:
    ops = (text_op("Bookkeeper", 10, 20) + "\n").encode() * 10
    resources = "/Resources << /Font << /F1 5 0 R >> >>"
    fonts = ("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",)
    plain = analyze_pdf(_simple_pdf(ops, extra_page=resources, extras=fonts))
    compressed = analyze_pdf(
        _simple_pdf(zlib.compress(ops), attributes="/Filter /FlateDecode", extra_page=resources, extras=fonts)
    )
    assert plain["errors"] == compressed["errors"] == []
    assert plain["content"]["decoded_content_string_operand_bytes"] == 100
    assert compressed["content"]["decoded_content_string_operand_bytes"] == 100
    assert compressed["content"]["decoded_content_bytes"] == plain["content"]["decoded_content_bytes"]
    assert compressed["content"]["content_encoded_to_decoded_ratio"] < 1
    assert plain["content"]["content_encoded_to_decoded_ratio"] == 1
    assert plain["raw_string_token_bytes"] == compressed["raw_string_token_bytes"] == 0
    assert plain["pages"][0]["text"]["adjacent_repeated_characters"] == 30
    assert plain["pages"][0]["text"]["duplicate_positioned_words"] == 9
    assert plain["pages"][0]["text"]["duplicate_positioned_spans"] == 9


def test_repeated_form_counts_execution_separately_from_unique_stream_bytes() -> None:
    form = text_op("ABC", 10, 20).encode()
    result = analyze_pdf(
        _simple_pdf(
            b"/Fm Do /Fm Do",
            extra_page="/Resources << /XObject << /Fm 5 0 R >> >>",
            extras=(
                stream_object(
                    form, "/Type /XObject /Subtype /Form /BBox [0 0 100 100] /Resources << /Font << /F1 6 0 R >> >>"
                ),
                "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            ),
        )
    )
    assert result["errors"] == []
    assert result["content"]["decoded_content_bytes"] == len(form) + len(b"/Fm Do /Fm Do")
    assert result["content"]["decoded_content_string_operand_bytes"] == 3
    assert result["content"]["text_showing_operand_bytes_executed"] == 6
    assert result["content"]["operators"]["Tj"] == 2


def test_raw_lexical_strings_exclude_stream_binary_and_comments() -> None:
    data = _simple_pdf(
        b"% ignored (stream string)\n",
        extra_page=r"/Label (a\(b\)) /Hex <4142> /Name /NotAString",
    )
    result = analyze_pdf(data)
    assert result["errors"] == []
    assert result["raw_string_token_bytes"] == len(rb"(a\(b\))") + len(b"<4142>")
    assert result["raw_string_token_fraction"] == result["raw_string_token_bytes"] / len(data)


def test_actual_text_render_modes_and_vector_clipping_inventory() -> None:
    result = analyze_pdf(
        page_pdf(
            "/Span << /ActualText (real) >> BDC BT /F1 12 Tf 3 Tr (fake) Tj ET EMC 0 0 10 10 re W n 0 0 m 10 10 l S"
        )
    )
    assert result["errors"] == []
    content = result["content"]
    assert content["actual_text_properties"] == ["real"]
    assert content["text_render_mode_operator_counts"] == {"3": 1}
    assert content["clipping_operator_count"] == 1
    assert content["vector_paint_operator_count"] == 1
    assert content["decoded_content_string_operand_bytes"] == 8
    assert content["text_showing_operand_bytes_executed"] == 4


def test_failed_parser_returns_null_and_structured_error() -> None:
    result = analyze_pdf(b"not a PDF")
    assert result["pages"] is None
    assert result["errors"][0]["scope"] == "document"
    assert result["errors"][0]["type"]


def test_failed_image_measurement_keeps_coverage_and_placement_bins_null(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_images(_page: pdfust.Page) -> list[pdfust.ImageInfo]:
        msg = "controlled image measurement failure"
        raise RuntimeError(msg)

    monkeypatch.setattr(pdfust.Page, "get_images", fail_images)
    result = analyze_pdf(page_pdf(""))
    page = result["pages"][0]
    assert page["images"] is None
    assert page["image_placement_count"] is None
    assert page["image_placement_coverage_bins"] is None
    assert page["image_coverage_percent"] is None
    assert result["image_coverage_bins"] is None
    assert result["percent_pages_with_images"] is None
    assert result["errors"][0]["scope"] == "page:0:images"


@pytest.mark.parametrize("separator", [b"", b" ", b"\n", b"\x0c"])
def test_stream_dictionary_delimiter_excludes_binary_strings(separator: bytes) -> None:
    payload = b"opaque binary (not a PDF string <or hex"
    stream = b"<< /Length " + str(len(payload)).encode() + b" >>" + separator + b"stream\n"
    stream += payload + b"\nendstream"
    result = analyze_pdf(_simple_pdf(b"", extra_page="/Label (visible)", extras=(stream,)))
    assert result["errors"] == []
    assert result["raw_string_token_bytes"] == len(b"(visible)")
