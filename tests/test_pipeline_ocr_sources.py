"""CPU-only contracts for optional OCR source discovery and page ownership."""

import io
from collections import Counter

import pytest
from bench.feature_cases import stream_object, text_op
from bench.pipeline_ocr_sources import discover_regions, extract, select_four, whitespace_projection
from bench.silver_layouts import _serialize
from PIL import Image

import pdfust


def test_regions_reject_native_coverage_and_overlapping_placements() -> None:
    native = [{"bbox": [10, 10, 90, 30], "text": "Header"}]
    placements = [
        {"bbox": [0, 0, 100, 100]},
        {"bbox": [20, 150, 200, 300]},
        {"bbox": [180, 200, 300, 350]},
        {"bbox": [350, 150, 550, 400]},
    ]
    result = discover_regions([0, 0, 600, 800], native, placements, 150)
    assert [region["placement"] for region in result["regions"]] == [3]
    assert Counter(row["reason"] for row in result["rejected"]) == {
        "native_text_intersection": 1,
        "overlapping_image_placements": 2,
    }


def test_region_bounds_refuse_complete_over_limit_collection() -> None:
    with pytest.raises(ValueError, match="exceed"):
        discover_regions([0, 0, 600, 800], [], [{"bbox": [0, i * 30, 20, i * 30 + 20]} for i in range(9)], 150)
    with pytest.raises(ValueError, match="exceed"):
        discover_regions([0, 0, 1500, 1500], [], [{"bbox": [0, 0, 1500, 1500]}], 300)


def test_whitespace_ablation_preserves_characters_and_marks_approximate_geometry() -> None:
    projected = whitespace_projection([{"text": "North  12 日本語", "bbox": [0, 0, 130, 10]}])
    assert [word["text"] for word in projected] == ["North", "12", "日本語"]
    assert all(word["geometry"].startswith("approximate") for word in projected)
    assert len({word["id"] for word in projected}) == 3


def _fake_ocr(_page: pdfust.Page, **_kwargs: object) -> list[dict]:
    return [{"bbox": pdfust.Rect(100, 200, 350, 220), "text": "North 12", "confidence": 0.9}]


def test_empty_extract_preserves_original_and_reextracts_retained_boxes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdfust.Page, "get_text_ocr", _fake_ocr)
    with pdfust.Document() as document:
        page = document.new_page(width=600, height=800)
        before = document.tobytes()
        result = extract(page)
        assert document.tobytes() == before
        assert page.get_text() == ""
        assert result["source"]["page_size"] == [0, 0, 600, 800]
        assert " ".join(word["text"] for word in result["source"]["words"]) == "North 12"
        assert result["diagnostics"]["recognized_box_count"] == 1
        assert result["diagnostics"]["reextracted_word_count"] == 2
        assert all(word["origin"] == "ocr_reextracted" for word in result["source"]["words"])


def test_existing_text_skips_empty_mode_without_clone_or_engine() -> None:
    with pdfust.Document() as document:
        page = document.new_page()
        page.insert_text((20, 20), "Header")
        result = extract(page)
        assert result["diagnostics"]["status"] == "skipped_existing_native_text"
        assert result["diagnostics"]["clone_serialized_bytes"] == 0
        assert [word["text"] for word in result["source"]["words"]] == ["Header"]


def test_mixed_page_import_preserves_native_words_and_original(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdfust.Page, "get_text_ocr", _fake_ocr)
    raster = io.BytesIO()
    Image.new("RGB", (200, 200), "white").save(raster, format="PNG")
    with pdfust.Document() as document:
        page = document.new_page(width=600, height=800)
        page.insert_text((20, 30), "Header")
        page.insert_text((20, 750), "Footer")
        page.insert_image((100, 100, 400, 400), stream=raster.getvalue())
        before = document.tobytes()
        result = extract(page, mode="uncovered_images")
        assert document.tobytes() == before
        assert Counter(word["text"] for word in result["source"]["words"]) == {
            "Header": 1,
            "Footer": 1,
            "North": 1,
            "12": 1,
        }
        assert Counter(word["origin"] for word in result["source"]["words"]) == {"native": 2, "ocr_reextracted": 2}
        assert len({word["id"] for word in result["source"]["words"]}) == 4


def test_native_text_inside_image_is_visible_abstention() -> None:
    raster = io.BytesIO()
    Image.new("RGB", (200, 200), "white").save(raster, format="PNG")
    with pdfust.Document() as document:
        page = document.new_page()
        page.insert_image((100, 100, 400, 400), stream=raster.getvalue())
        page.insert_text((120, 200), "Already searchable")
        result = extract(page, mode="uncovered_images")
        assert result["diagnostics"]["status"] == "abstained_no_uncovered_image_regions"
        assert result["diagnostics"]["rejected_regions"][0]["reason"] == "native_text_intersection"


def test_selected_page_clone_materializes_inherited_resources_and_boxes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pdfust.Page, "get_text_ocr", lambda *_args, **_kwargs: [])
    data = _serialize(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            (
                "<< /Type /Pages /Count 2 /Kids [3 0 R 4 0 R] /MediaBox [0 0 600 800] "
                "/CropBox [20 20 580 780] /Rotate 90 /Resources << /Font << /F1 7 0 R >> >> >>"
            ),
            "<< /Type /Page /Parent 2 0 R /Contents 5 0 R >>",
            "<< /Type /Page /Parent 2 0 R /Contents 6 0 R >>",
            stream_object(text_op("Inherited header", 40, 700)),
            stream_object(""),
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ],
        "1.7",
    )
    with pdfust.Document(stream=data) as document:
        before = document.tobytes()
        result = extract(document[1])
        assert result["source"]["page_size"] == list(document[1].rect)
        assert result["diagnostics"]["status"] == "recognized_no_text"
        assert document.tobytes() == before
        assert "Inherited header" in document[0].get_text()


def test_metadata_selection_is_order_independent_and_requires_strata() -> None:
    layouts = ("other_layout", "1andmore_column", "double_column", "single_column")
    rows = [
        {
            "id": str(index),
            "diversity": {
                "attributes": {"layout": layout, "language": "zh" if index % 2 else "en", "data_source": str(index)}
            },
        }
        for index, layout in enumerate(layouts)
    ]
    assert select_four({"pages": rows}) == select_four({"pages": list(reversed(rows))})
    with pytest.raises(ValueError, match="stratum"):
        select_four({"pages": rows[:3]})


def test_direct_whitespace_mode_preserves_native_ids_and_explicit_approximation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pdfust.Page, "get_text_ocr", _fake_ocr)
    with pdfust.Document() as document:
        page = document.new_page(width=600, height=800)
        result = extract(page, tokenization="whitespace")
        words = result["source"]["words"]
        assert [word["text"] for word in words] == ["North", "12"]
        assert [word["id"] for word in words] == ["w0", "w1"]
        assert all(word["origin"] == "ocr_whitespace_projection" for word in words)
        assert all(word["geometry"].startswith("approximate") for word in words)
        assert [word["recognized_line_id"] for word in words] == ["r0", "r0"]
        assert result["diagnostics"]["reextracted_word_count"] is None
        assert page.get_text() == ""


def test_invalid_dpi_or_tokenization_refuses_before_ocr() -> None:
    with pdfust.Document() as document:
        page = document.new_page()
        with pytest.raises(ValueError, match="tokenization"):
            extract(page, tokenization="unknown")
        with pytest.raises(ValueError, match="DPI"):
            extract(page, dpi=False)
    with pytest.raises(ValueError, match="DPI"):
        discover_regions([0, 0, 600, 800], [], [], -150)


def test_whitespace_source_words_can_exceed_recognized_box_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    text = " ".join(str(index) for index in range(1500))
    monkeypatch.setattr(
        pdfust.Page,
        "get_text_ocr",
        lambda *_args, **_kwargs: [
            {"bbox": pdfust.Rect(20, 20 + row * 30, 500, 40 + row * 30), "text": text, "confidence": 0.9}
            for row in range(4)
        ],
    )
    with pdfust.Document() as document:
        page = document.new_page()
        before = document.tobytes()
        result = extract(page, tokenization="whitespace")
        assert len(result["source"]["words"]) == 6000
        assert result["diagnostics"]["recognized_box_count"] == 4
        assert result["diagnostics"]["admission"]["source_words"] == 65_536
        assert document.tobytes() == before


def test_source_limit_refusal_retains_before_limit_diagnostics_and_caller(monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import pipeline_ocr_sources  # noqa: PLC0415

    monkeypatch.setattr(pipeline_ocr_sources, "MAX_SOURCE_WORDS", 5)
    monkeypatch.setattr(
        pdfust.Page,
        "get_text_ocr",
        lambda *_args, **_kwargs: [{"bbox": pdfust.Rect(20, 20, 500, 40), "text": "A B C D E F", "confidence": 0.9}],
    )
    with pdfust.Document() as document:
        page = document.new_page()
        before = document.tobytes()
        with pytest.raises(pipeline_ocr_sources.SourceAdmissionError) as caught:
            extract(page, tokenization="whitespace")
        assert document.tobytes() == before
        observation = caught.value.diagnostics["source_admission_observation"]
        assert observation["phase"] == "complete"
        assert observation["words"] == 6
        assert len(caught.value.diagnostics["recognized"]) == 1


def test_native_character_admission_matches_character_units_including_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import pipeline_ocr_sources  # noqa: PLC0415

    monkeypatch.setattr(pipeline_ocr_sources, "MAX_SOURCE_CHARACTERS", 5)
    monkeypatch.setattr(
        pipeline_ocr_sources,
        "_native_words",
        lambda _page: [{"id": "w0", "text": "日本語", "bbox": [20, 20, 40, 40], "line": [0, 0]}],
    )
    with pdfust.Document() as document:
        result = extract(document.new_page())
        assert result["diagnostics"]["source_admission_observation"]["characters_including_ids"] == 5
    monkeypatch.setattr(pipeline_ocr_sources, "MAX_SOURCE_CHARACTERS", 4)
    with pdfust.Document() as document, pytest.raises(pipeline_ocr_sources.SourceAdmissionError):
        extract(document.new_page())


def test_recognized_box_admission_is_per_ocr_call(monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import pipeline_ocr_sources  # noqa: PLC0415

    monkeypatch.setattr(
        pdfust.Page,
        "get_text_ocr",
        lambda *_args, **_kwargs: [{"bbox": pdfust.Rect(20, 20, 500, 40), "text": "A", "confidence": 0.9}] * 4097,
    )
    with pdfust.Document() as document, pytest.raises(pipeline_ocr_sources.SourceAdmissionError) as caught:
        extract(document.new_page(), tokenization="whitespace")
    assert caught.value.diagnostics["last_region_recognized_box_count"] == 4097
