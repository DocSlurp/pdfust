"""Source-only table fixtures; no labels, credentials, models, or corpus references."""
from __future__ import annotations

import copy

import pytest
from bench import p003_rolling_tracks as rolling

# ruff: noqa: ANN201 - deterministic small fixtures.


def fixture():
    source = {"page_size": [0, 0, 100, 100], "vector_candidates": [], "words": [
        {"id": "a", "text": "key", "bbox": [2, 2, 20, 10]},
        {"id": "b", "text": "body", "bbox": [60, 2, 80, 10]},
        {"id": "c", "text": "continuation", "bbox": [60, 14, 85, 22]},
        {"id": "d", "text": "next", "bbox": [2, 42, 20, 50]},
        {"id": "e", "text": "value", "bbox": [60, 42, 80, 50]},
        {"id": "outside", "text": "preserve", "bbox": [2, 105, 20, 115]},
    ]}
    region = {"region_id": "r", "bbox": [0, 0, 100, 100], "source_ids": ["a", "b", "c", "d", "e"]}
    topology = {"status": "geometry_candidate", "x_edges": [0, 50, 100]}
    return source, region, topology


def test_empty_key_continuation_and_second_key_policy():
    source, region, topology = fixture()
    before = copy.deepcopy(source)
    result = rolling.compose(source, [region], {"r": topology}, [], 0.75, 1)
    assert result["state"]["tables"][0]["values"] == [["key", "body continuation"], ["next", "value"]]
    assert result["regions"][0]["joined_line_count"] == 1
    assert result["state"]["unresolved_ids"] == ["outside"]
    assert source == before
    separate = rolling.compose(source, [region], {"r": topology}, [], 0.75, 2)
    assert separate["state"]["tables"][0]["row_count"] == 3
    assert separate["source_conserved"] is True


def test_source_rule_blocks_join_and_words_cannot_cross_columns():
    source, region, topology = fixture()
    source["words"].append({"id": "cross", "text": "whole", "bbox": [45, 14, 55, 22]})
    region["source_ids"].append("cross")
    result = rolling.compose(source, [region], {"r": topology}, [[0, 12, 100]], 1.25, 1)
    assert result["state"]["tables"][0]["row_count"] == 3
    assert result["regions"][0]["decisions"][1]["horizontal_rule_barrier"] is True
    assert "cross" in result["state"]["unresolved_ids"]
    assigned = [i for table in result["state"]["tables"] for cell in table["cells"] for i in cell["source_ids"]]
    assert len(assigned) == len(set(assigned))
    assert set(assigned + result["state"]["unresolved_ids"]) == {w["id"] for w in source["words"]}


def test_occupied_key_or_new_column_does_not_join():
    source, region, topology = fixture()
    source["words"][2]["bbox"] = [2, 14, 20, 22]
    result = rolling.compose(source, [region], {"r": topology}, [], 1.25, 1)
    assert result["state"]["tables"][0]["row_count"] == 3
    source["words"][2]["bbox"] = [82, 14, 90, 22]
    topology["x_edges"] = [0, 40, 80, 100]
    result = rolling.compose(source, [region], {"r": topology}, [], 1.25, 1)
    assert result["regions"][0]["decisions"][1]["columns_compatible"] is False
    assert result["state"]["tables"][0]["row_count"] == 3


def test_all_overlap_participants_refused_and_no_proposal_pages_retained():
    source, region, topology = fixture()
    other = {"region_id": "s", "bbox": [0, 0, 100, 100], "source_ids": []}
    result = rolling.compose(source, [region, other], {"r": topology, "s": topology}, [], 1.0, 1)
    assert result["state"]["tables"] == []
    assert result["conflicting_region_ids"] == ["r", "s"]
    assert len(result["state"]["unresolved_ids"]) == len(source["words"])
    result = rolling.compose(source, [], {}, [], 1.0, 1)
    assert result["state"]["tables"] == []
    assert result["source_word_count"] == 6


def test_no_invalid_topology_or_undeclared_profile_salvage():
    source, region, topology = fixture()
    topology["x_edges"] = [0, 101, 100]
    result = rolling.compose(source, [region], {"r": topology}, [], 1.0, 1)
    assert result["regions"][0]["status"] == "refused"
    assert result["state"]["tables"] == []
    with pytest.raises(ValueError, match="predeclared"):
        rolling.compose(source, [region], {"r": topology}, [], 1.1, 1)
    region["source_ids"].append("a")
    with pytest.raises(ValueError, match="Duplicate"):
        rolling.compose(source, [region], {"r": topology}, [], 1.0, 1)


@pytest.mark.parametrize("endpoint", [float("nan"), float("inf"), True, "0"])
def test_outer_endpoint_cannot_be_replaced_before_validation(endpoint: object):
    source, region, topology = fixture()
    topology["x_edges"][0] = endpoint
    result = rolling.compose(source, [region], {"r": topology}, [], 1.0, 1)
    assert result["state"]["tables"] == []
    assert result["regions"][0]["refusal"] == "nonfinite_or_invalid_frozen_column_endpoint"


def test_all_crossing_words_cannot_create_an_empty_table():
    source, region, topology = fixture()
    for word in source["words"][:-1]:
        word["bbox"][0:3:2] = [45, 55]
    result = rolling.compose(source, [region], {"r": topology}, [], 1.0, 1)
    assert result["state"]["tables"] == []
    assert result["regions"][0]["refusal"] == "no_whole_word_assignments_to_frozen_columns"
    assert len(result["state"]["unresolved_ids"]) == len(source["words"])


def test_region_slot_cap_refuses_complete_proposal(monkeypatch: pytest.MonkeyPatch):
    source, region, topology = fixture()
    monkeypatch.setattr(rolling, "MAX_SLOTS", 3)
    result = rolling.compose(source, [region], {"r": topology}, [], 0.75, 1)
    assert result["state"]["tables"] == []
    assert result["regions"][0]["refusal"] == "complete_rectangular_grid_admission"
    assert len(result["state"]["unresolved_ids"]) == len(source["words"])


def test_whole_page_slot_cap_cannot_return_one_partial_table(monkeypatch: pytest.MonkeyPatch):
    source, region, topology = fixture()
    source["page_size"][2] = 300
    words = copy.deepcopy(source["words"][:5])
    for word in words:
        word["id"] = "other-" + word["id"]
        word["bbox"][0] += 200
        word["bbox"][2] += 200
    source["words"].extend(words)
    other = {"region_id": "other", "bbox": [200, 0, 300, 100], "source_ids": [w["id"] for w in words]}
    other_topology = {"status": "geometry_candidate", "x_edges": [200, 250, 300]}
    monkeypatch.setattr(rolling, "MAX_SLOTS", 7)
    result = rolling.compose(source, [region, other], {"r": topology, "other": other_topology}, [], 0.75, 1)
    assert result["state"]["tables"] == []
    assert result["page_refusal"] == "whole_page_slots_all_tables_refused"
    assert all(not r["effective_page_accepted"] for r in result["regions"])
    assert len(result["state"]["unresolved_ids"]) == len(source["words"])
