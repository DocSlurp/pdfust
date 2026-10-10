"""Residual density proposals keep exact IDs and explicit overlap decisions."""

from __future__ import annotations

from bench import p003_structure_density as density


def test_aligned_source_tracks_preserve_literal_ids() -> None:
    """Three aligned rows supply one source-only hypothesis, not a table label."""
    words = [
        {"id": f"w{r}-{c}", "text": "same", "bbox": [10 + c * 70, 10 + r * 20, 20 + c * 70, 20 + r * 20]}
        for r in range(3)
        for c in range(2)
    ]
    source = {"page_size": [0, 0, 100, 100], "words": words}
    result = density.select(source, [w["id"] for w in words])
    assert len(result["accepted"]) == 1
    assert result["owned_word_count"] == 6
    assert result["accepted"][0]["source_ids"] == [w["id"] for w in words]
    assert result["selection_uses_references"] is False


def test_negative_single_segment_and_empty_residual_no_crop() -> None:
    """No aligned gap evidence yields no invented proposal, retaining uncovered words."""
    words = [{"id": f"w{r}", "text": "prose literal", "bbox": [10, 10 + r * 20, 80, 20 + r * 20]} for r in range(3)]
    source = {"page_size": [0, 0, 100, 100], "words": words}
    result = density.select(source, [w["id"] for w in words])
    assert result["accepted"] == []
    assert result["uncovered_residual_ids"] == [w["id"] for w in words]
    assert density.select(source, [])["raw_proposals"] == []


def test_overlapping_track_windows_retained_as_rejections() -> None:
    """Capacity windows never duplicate ownership or silently merge accepted crops."""
    words = [
        {"id": f"w{r}-{c}", "text": str(r), "bbox": [10 + c * 70, 10 + r * 20, 20 + c * 70, 20 + r * 20]}
        for r in range(10)
        for c in range(2)
    ]
    result = density.select({"page_size": [0, 0, 100, 250], "words": words}, [w["id"] for w in words])
    assert len(result["raw_proposals"]) > len(result["accepted"])
    assert len(result["accepted"]) <= 8
    assert any(d["reason"] == "overlap_with_retained_proposal" for d in result["decisions"])
    ids = [i for a in result["accepted"] for i in a["source_ids"]]
    assert len(ids) == len(set(ids))
