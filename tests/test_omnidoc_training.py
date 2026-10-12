"""Training geometry contracts ignore recognition text and respect known parents."""

from __future__ import annotations

import io
from copy import deepcopy
from typing import Any

import pytest
from bench.omnidoc_training import (
    CJK_FONT,
    _realism_pdf,
    compact_metadata,
    geometry,
    ink_measure,
    parent_group,
    realistic_recipe,
    reference_style,
    select_rows,
    suppressed,
    synthetic_recipe,
)

import pdfust


def row(identifier: str) -> dict[str, Any]:
    return {
        "page_info": {
            "image_path": identifier,
            "width": 100,
            "height": 200,
            "page_attribute": {"layout": "single_column", "data_source": "book", "language": "english"},
        },
        "layout_dets": [
            {
                "anno_id": "b0",
                "category_type": "text_block",
                "poly": [10, 20, 80, 20, 80, 90, 10, 90],
                "text": "This recognition answer must not enter geometry",
                "order": 1,
            }
        ],
    }


def test_known_parent_separation_and_uuid_uncertainty() -> None:
    assert parent_group("book_page_003.png") == "book"
    assert parent_group("page-uuid.png") is None
    rows = [row("book_page_003.png"), row("other_page_001.png"), row("third_page_002.png")]
    chosen = select_rows(rows, {"book_page_004.png"}, 2)
    assert {r["page_info"]["image_path"] for r in chosen} == {"other_page_001.png", "third_page_002.png"}


def test_geometry_ignores_all_recognition_and_private_metadata() -> None:
    reference = row("x.png")
    changed = deepcopy(reference)
    changed["layout_dets"][0].update(text="different answer", html="secret", latex="equation", target="private")
    assert geometry(reference) == geometry(changed)
    contract = geometry(reference)
    assert contract["split"] == "TRAINING"
    assert contract["blocks"][0]["normalized_bbox"] == [0.1, 0.1, 0.8, 0.45]


def test_synthetic_recipe_uses_authored_text_and_preserves_envelopes() -> None:
    contract = geometry(row("x.png"))
    recipe = synthetic_recipe(contract, 2)
    assert recipe["split"] == "TRAINING"
    assert recipe["blocks"][0]["source_block_id"] == "b0"
    assert recipe["blocks"][0]["bbox"] == [61.2, 122.4, 489.6, 550.8]
    assert "recognition answer" not in str(recipe)
    altered = deepcopy(contract)
    altered["blocks"][0]["text"] = "reference text that must not enter output"
    assert synthetic_recipe(altered, 2) == recipe


def test_reference_masks_and_discarded_blocks_are_never_authored_content() -> None:
    for category in ("chart_mask", "algorithm_mask", "table_mask", "text_mask", "need_mask", "abandon"):
        assert suppressed(category)
    assert suppressed("text_block", ignored=True)
    assert not suppressed("text_block")


def test_image_style_projection_ignores_recognition_strings() -> None:
    image_module = pytest.importorskip("PIL.Image")
    image = image_module.new("RGB", (100, 200), "white")
    contract = geometry(row("fixture.png"))
    style = reference_style(image, contract, {"language": "english", "data_source": "book"})
    changed = deepcopy(contract)
    changed["blocks"][0].update(text="REFERENCE SECRET", html="hidden", latex="formula")
    other = reference_style(image, changed, {"language": "english", "data_source": "book"})
    assert style == other
    assert style["recognition_used"] is False
    assert realistic_recipe(contract, style, 0) == realistic_recipe(changed, other, 0)
    assert "REFERENCE SECRET" not in str(realistic_recipe(changed, other, 0))


def test_masked_region_is_white_in_render_and_has_no_source_words() -> None:
    image_module = pytest.importorskip("PIL.Image")
    contract = geometry(row("fixture.png"))
    contract["blocks"][0]["category"] = "algorithm_mask"
    style = reference_style(
        image_module.new("RGB", (100, 200), (240, 180, 200)), contract, {"language": "english", "data_source": "book"}
    )
    recipe = realistic_recipe(contract, style, 0)
    assert recipe["blocks"][0]["paint"].startswith("suppressed")
    data = _realism_pdf(recipe, b"")
    with pdfust.open(stream=data) as document:
        assert document.get_text() == ""
        render = image_module.open(io.BytesIO(document[0].render(dpi=72, background=(255, 255, 255))))
    assert render.getpixel((100, 200))[:3] == (255, 255, 255)
    assert render.getpixel((10, 10))[:3] != (255, 255, 255)


def test_vertical_cjk_authored_render_remains_inside_page() -> None:
    image_module = pytest.importorskip("PIL.Image")
    if not CJK_FONT.exists():
        pytest.skip("Local CJK authoring font is not installed")
    contract = geometry(row("fixture.png"))
    contract["blocks"][0]["bbox"] = [10, 20, 15, 190]
    style = reference_style(
        image_module.new("RGB", (100, 200), "white"),
        contract,
        {"language": "traditional_chinese", "data_source": "historical_document"},
    )
    recipe = realistic_recipe(contract, style, 0)
    assert recipe["blocks"][0]["vertical"]
    with pdfust.open(stream=_realism_pdf(recipe, CJK_FONT.read_bytes())) as document:
        assert document.get_text().strip()
        for word in document[0].get_text("words"):
            assert 0 <= word[0] <= word[2] <= 612
            assert 0 <= word[1] <= word[3] <= recipe["height"]


def test_ink_diagnostics_measure_pixels_instead_of_declared_boxes() -> None:
    image_module = pytest.importorskip("PIL.Image")
    white = ink_measure(image_module.new("RGB", (32, 32), "white"))
    black = ink_measure(image_module.new("RGB", (32, 32), "black"))
    assert white["dark_fraction"] == 0
    assert black["dark_fraction"] == 1
    assert black["nonwhite_fraction"] == 1


def test_narrow_latin_credit_is_rotated_without_off_page_words() -> None:
    image_module = pytest.importorskip("PIL.Image")
    contract = geometry(row("fixture.png"))
    contract["blocks"][0]["bbox"] = [98.5, 20, 99.5, 160]
    style = reference_style(
        image_module.new("RGB", (100, 200), "white"), contract, {"language": "english", "data_source": "newspaper"}
    )
    recipe = realistic_recipe(contract, style, 0)
    assert recipe["blocks"][0]["vertical_latin"]
    with pdfust.open(stream=_realism_pdf(recipe, b"")) as document:
        words = document[0].get_text("words")
        assert len(words) == 3
        assert all(0 <= word[0] <= word[2] <= 612 for word in words)
        assert all(0 <= word[1] <= word[3] <= recipe["height"] for word in words)


def test_compact_metadata_preserves_measurements_and_unknowns() -> None:
    metadata: dict[str, Any] = {
        "effective_pdf_version": "1.7",
        "raw_string_token_fraction": None,
        "errors": ["unknown string measurement"],
        "content": {"font_resources": [{"name": "Verbose"}], "decoded_content_bytes": 123},
        "pages": [{"images": [], "image_coverage_percent": 0, "text": {"word_count": 12}}],
    }
    compact = compact_metadata(metadata)
    assert compact["raw_string_token_fraction"] is None
    assert compact["errors"] == metadata["errors"]
    assert compact["content"] == {"decoded_content_bytes": 123}
    assert compact["pages"][0]["text"]["word_count"] == 12
    assert "font_resources" in metadata["content"]
