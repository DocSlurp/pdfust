"""Quality-blind source ownership and bounded crop acquisition contracts."""

from __future__ import annotations

import math

import pytest
from bench import p003_structure_acquisition as acquisition


def test_padding_height_bound_page_clipping() -> None:
    """Measured box height determines padding, capped independently of page content."""
    assert acquisition.padded([5, 5, 20, 20], [0, 0, 100, 100], [10, 20]) == ([0, 0, 32, 32], 12)
    assert acquisition.padded([20, 20, 30, 30], [0, 0, 100, 100], [2, 4]) == ([15.5, 15.5, 34.5, 34.5], 4.5)
    assert acquisition.padded([20, 20, 30, 30], [0, 0, 100, 100], []) == ([20, 20, 30, 30], 0)
    with pytest.raises(ValueError, match="Invalid"):
        acquisition.padded([0, 0, 10, 10], [0, 0, 100, 100], [math.nan])


def test_fullpage_allids_and_residual_padding_never_owns_context() -> None:
    """Pixel coverage can overlap while exact source ownership stays unchanged."""
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "a", "text": "retained", "bbox": [10, 10, 20, 20]},
            {"id": "b", "text": "context", "bbox": [21, 10, 30, 20]},
            {"id": "c", "text": "same", "bbox": [80, 80, 90, 90]},
        ],
    }
    regions = [
        {"id": "r0", "kind": "residual", "bbox": [10, 10, 20, 20], "source_ids": ["a"]},
        {"id": "r1", "kind": "detector_proposal", "bbox": [21, 10, 30, 20], "source_ids": ["b"]},
        {"id": "r2", "kind": "residual", "bbox": [80, 80, 90, 90], "source_ids": ["c"]},
    ]
    full = acquisition.proposals(source, regions, "fullpage")
    assert len(full) == 1
    assert full[0]["source_ids"] == ["a", "b", "c"]
    residual = acquisition.proposals(source, regions, "residual")
    assert len(residual) == 2
    assert residual[0]["source_ids"] == ["a"]
    assert residual[0]["context_only_source_ids"] == ["b"]
    assert residual[1]["source_ids"] == ["c"]
    with pytest.raises(ValueError, match="ownership"):
        acquisition.proposals(source, [*regions, regions[0]], "residual")


def test_empty_residual_keeps_explicit_receipt() -> None:
    """No source-owned words yields an omission receipt, not a fabricated crop."""
    source = {"page_size": [0, 0, 100, 100], "words": []}
    assert (
        acquisition.proposals(
            source, [{"id": "r0", "kind": "residual", "bbox": [10, 10, 20, 20], "source_ids": []}], "residual"
        )[0]["status"]
        == "no_owned_source_words"
    )
    assert acquisition.proposals(source, [], "fullpage")[0]["source_ids"] == []
