"""Training geometry contracts ignore recognition text and respect known parents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from bench.omnidoc_training import geometry, parent_group, select_rows, synthetic_recipe


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
