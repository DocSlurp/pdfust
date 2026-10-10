"""Regional source controls use synthetic geometry and complete literal inventories only."""
from __future__ import annotations

import pytest
from bench import p003_regional_tracks as regional


def fixture_source() -> dict:
    return {"page_size": [0, 0, 300, 200], "words": [
        {"id": f"w{r * 2 + c}", "text": "same", "bbox": [10 + 90 * c, 10 + 20 * r,
                                                                 40 + 90 * c, 20 + 20 * r]}
        for r in range(3) for c in range(2)
    ] + [{"id": "outside", "text": "outside literal", "bbox": [220, 10, 280, 20]}]}


def fixture_region() -> dict:
    return {"region_id": "a", "bbox": [0, 0, 200, 100], "source_ids": [f"w{i}" for i in range(6)]}


def test_all_profiles_preserve_owned_and_unowned_literal_inventory() -> None:
    source, region = fixture_source(), fixture_region()
    for gap, support in regional.PROFILES:
        result = regional.compose(source, [region], gap, support)
        state = result["state"]
        assert state["tables"][0]["values"] == [["same", "same"]] * 3
        owned = [i for cell in state["tables"][0]["cells"] for i in cell["source_ids"]]
        assert len(owned) == len(set(owned)) == 6
        assert state["unresolved_ids"] == ["outside"]


def test_crossing_whole_words_stay_unresolved() -> None:
    source, region = fixture_source(), fixture_region()
    source["words"].extend([
        {"id": "cross_column", "text": "unsplittable full literal", "bbox": [30, 75, 130, 85]},
        {"id": "cross_region", "text": "complete edge literal", "bbox": [190, 40, 205, 50]},
    ])
    region["source_ids"].extend(["cross_column", "cross_region"])
    result = regional.compose(source, [region], 0.5, 0.5)
    assert result["state"]["unresolved_ids"] == ["outside", "cross_column", "cross_region"]
    assert result["regions"][0]["plan"]["excluded_ids"] == ["cross_region"]
    assert {w["text"] for w in result["regions"][0]["ambiguity_inventory"]} == {
        "unsplittable full literal", "complete edge literal",
    }


def test_all_overlapping_proposals_are_refused_without_winner() -> None:
    source, region = fixture_source(), fixture_region()
    other = {"region_id": "b", "bbox": [150, 0, 290, 100], "source_ids": ["outside"]}
    result = regional.compose(source, [region, other], 0.5, 0.1)
    assert result["conflicting_region_ids"] == ["a", "b"]
    assert result["state"]["tables"] == []
    assert result["unresolved_word_count"] == len(source["words"])


def test_tatr_columns_with_source_rows_are_a_separate_fixed_control() -> None:
    source, region = fixture_source(), fixture_region()
    topology = {"status": "geometry_candidate", "x_edges": [0, 70, 200]}
    result = regional.compose(source, [region], 0.5, 0.1, {"a": topology})
    assert result["state"]["tables"][0]["row_count"] == 3
    assert result["regions"][0]["plan"]["treatment"] == "tatr_columns_physical_rows"
    bad = regional.compose(source, [region], 0.5, 0.1, {})
    assert bad["state"]["tables"] == []


def test_repeated_or_unknown_ownership_refuses() -> None:
    source, region = fixture_source(), fixture_region()
    with pytest.raises(ValueError, match="share"):
        regional.compose(source, [region, {**region, "region_id": "b"}], 0.5, 0.1)
    with pytest.raises(ValueError, match="Unknown"):
        regional.regional_source(source, {**region, "source_ids": ["unknown"]})


def test_global_slot_admission_refuses_atomically_and_retains_proposals(monkeypatch: pytest.MonkeyPatch) -> None:
    source, region = fixture_source(), fixture_region()
    monkeypatch.setattr(regional, "MAX_SLOTS", 5)
    result = regional.compose(source, [region], 0.5, 0.1)
    assert result["page_refusal"] == "whole_page_slot_admission_all_proposed_tables_refused"
    assert result["state"]["tables"] == []
    assert result["state"]["unresolved_ids"] == [w["id"] for w in source["words"]]
    assert result["regions"][0]["state"]["tables"]
    assert result["regions"][0]["effective_page_accepted"] is False
