"""Source-only OCR admission inventory and projection regression checks."""

from typing import Any

import pytest
from bench.ocr_admission import inventory_conserved, source_page


def observed() -> dict[str, Any]:
    """Return OCR regions with punctuation and a whole-line region intact."""
    return {
        "id": "sample",
        "page_size": [600.0, 800.0],
        "words": [
            {"id": "r0", "text": "one  two!", "bbox": [1, 2, 30, 10], "confidence": 0.8},
            {"id": "r1", "text": "3.4", "bbox": [50, 2, 70, 10], "confidence": 0.9},
        ],
        "target": "must not enter projection",
        "observed_sha256": "frozen-hash",
    }


def test_projection_preserves_exact_ocr_regions() -> None:
    """Whole OCR regions retain strings and IDs without hidden target fields."""
    page = source_page(observed(), "/source-image.png", [])
    assert page["page_size"] == [0.0, 0.0, 600.0, 800.0]
    assert page["words"] == [
        {"id": "r0", "text": "one  two!", "bbox": [1, 2, 30, 10]},
        {"id": "r1", "text": "3.4", "bbox": [50, 2, 70, 10]},
    ]
    assert "target" not in page
    assert page["vector_candidates"] == []
    assert page["ocr_observed_sha256"] == "frozen-hash"


def test_duplicate_ocr_ids_refused() -> None:
    """Duplicate inventory IDs cannot masquerade as independent regions."""
    source = observed()
    source["words"][1]["id"] = "r0"
    with pytest.raises(ValueError, match="duplicate IDs"):
        source_page(source, "/source-image.png", [])


@pytest.mark.parametrize(("owned", "unresolved"), [(["r0"], ["r1"]), ([], ["r0", "r1"])])
def test_inventory_can_remain_unresolved(owned: list[str], unresolved: list[str]) -> None:
    """Source conservation permits abstention without dropping regions."""
    page = source_page(observed(), "/source-image.png", [])
    alternative = {"candidates": [{"cells": [{"source_ids": owned}]}], "unresolved_ids": unresolved}
    assert inventory_conserved(page, alternative)


@pytest.mark.parametrize(("owned", "unresolved"), [(["r0", "r0"], ["r1"]), (["r0"], []), (["r0"], ["foreign"])])
def test_inventory_rejects_duplicate_missing_or_foreign_ids(owned: list[str], unresolved: list[str]) -> None:
    """Counted ownership detects omissions and duplicate or fabricated sources."""
    page = source_page(observed(), "/source-image.png", [])
    alternative = {"candidates": [{"cells": [{"source_ids": owned}]}], "unresolved_ids": unresolved}
    assert not inventory_conserved(page, alternative)
