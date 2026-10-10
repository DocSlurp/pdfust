"""Synthetic frozen salvage gates; no references, transport or credentials."""

import json
from copy import deepcopy

import pytest
from bench.pipeline_vision_partial import salvage


def table(text: str | int = "literal", bbox: list[int] | None = None) -> dict:
    return {"bbox": bbox or [0, 0, 200, 200], "matrix": [[text]], "mergedspans": []}


def descriptor(tables: list[dict], *, finish: str = "stop", content: str | None = None) -> dict:
    return {
        "viewport": [10, 20, 110, 120],
        "response": {
            "choices": [
                {
                    "finish_reason": finish,
                    "message": {
                        "content": content
                        if content is not None
                        else json.dumps({"answers": {"q0": {"tables": tables}}})
                    },
                }
            ]
        },
    }


def test_invalid_table_is_quarantined_whole_with_literal_valid_neighbor() -> None:
    raw = descriptor([table("keep", [0, 0, 200, 200]), table(7, [500, 500, 700, 700])])
    before = deepcopy(raw)
    result = salvage([raw], [0, 0, 200, 200])
    assert result["status"] == "partial"
    assert result["complete_page"] is result["source_conserved"] is False
    assert result["tables"][0]["values"] == [["keep"]]
    assert result["tables"][0]["bbox"] == [10, 20, 30, 40]
    assert result["quarantined"][0]["table_index"] == 1
    assert raw == before


def test_transitive_overlap_quarantines_entire_component_not_greedy_winner() -> None:
    raw = descriptor(
        [
            table("A", [0, 0, 400, 400]),
            table("B", [300, 0, 700, 400]),
            table("C", [600, 0, 1000, 400]),
            table("isolated", [0, 600, 200, 800]),
        ]
    )
    result = salvage([raw], [0, 0, 200, 200])
    assert [t["values"] for t in result["tables"]] == [[["isolated"]]]
    assert len(result["overlap_components"][0]) == 3


def test_overlap_is_global_across_crop_viewports_and_touching_edges_allowed() -> None:
    a = descriptor([table("A", [0, 0, 500, 500])])
    b = descriptor([table("B", [0, 0, 500, 500])])
    b["viewport"] = [40, 20, 140, 120]
    assert salvage([a, b], [0, 0, 200, 200])["tables"] == []
    b["viewport"] = [60, 20, 160, 120]
    assert len(salvage([a, b], [0, 0, 200, 200])["tables"]) == 2


@pytest.mark.parametrize("finish", ["length", "content_filter", "error"])
def test_abnormal_finish_cannot_salvage_complete_looking_prefix(finish: str) -> None:
    result = salvage([descriptor([table()], finish=finish)], [0, 0, 200, 200])
    assert result["tables"] == []
    assert result["quarantined"][0]["code"] == "response_ineligible"


@pytest.mark.parametrize(
    "content", ['{"answers":', '{"answers":{"q0":{"tables":[]}},"answers":{}}', '{"answers":{"q0":{"tables":[NaN]}}}']
)
def test_malformed_duplicate_or_nonfinite_outer_json_refuses_response(content: str) -> None:
    assert salvage([descriptor([], content=content)], [0, 0, 200, 200])["tables"] == []


def test_refusal_and_outside_crop_are_ineligible_without_clipping() -> None:
    raw = descriptor([table()])
    raw["response"]["choices"][0]["message"]["refusal"] = "refused"
    assert salvage([raw], [0, 0, 200, 200])["tables"] == []
    raw = descriptor([table()])
    raw["viewport"] = [-1, 0, 100, 100]
    assert salvage([raw], [0, 0, 200, 200])["tables"] == []


def test_aggregate_slot_refusal_never_selects_a_convenient_subset() -> None:
    a, b = table("", [0, 0, 400, 400]), table("", [600, 600, 1000, 1000])
    for raw in (a, b):
        raw["matrix"] = [[""] * 64 for _ in range(64)]
    result = salvage([descriptor([a, b])], [0, 0, 200, 200])
    assert result["validated_table_count"] == 2
    assert result["tables"] == []
    assert [q["code"] for q in result["quarantined"]] == ["aggregate_admission", "aggregate_admission"]


def test_end_turn_and_empty_inventory_still_label_partial_not_complete() -> None:
    result = salvage([descriptor([], finish="end_turn")], [0, 0, 200, 200])
    assert result["status"] == "partial"
    assert result["complete_page"] is False
    assert result["quarantined"] == []
