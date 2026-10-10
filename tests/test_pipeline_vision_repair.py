"""Conservative repair rules independent of any retained response or gold labels."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_vision_repair import repair


def response(matrix: list, spans: list | None = None, bbox: list | None = None) -> dict[str, Any]:
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "answers": {
                                "q0": {
                                    "tables": [
                                        {
                                            "bbox": [10, 10, 900, 900] if bbox is None else bbox,
                                            "matrix": matrix,
                                            "mergedspans": [] if spans is None else spans,
                                        }
                                    ]
                                }
                            }
                        }
                    )
                },
            }
        ]
    }


def test_valid_output_is_unchanged_and_raw_envelope_preserved() -> None:
    raw = response([["A", "B"], ["C", "D"]])
    before = deepcopy(raw)
    result = repair(raw, [0, 0, 600, 800])
    assert raw == before
    assert not result["repaired"]
    assert result["edits"] == []
    assert result["parsed"]["tables"][0]["values"] == [["A", "B"], ["C", "D"]]


def test_only_explicit_merged_continuation_null_becomes_blank() -> None:
    result = repair(response([["Merged", None], ["A", "B"]], [[0, 0, 1, 2]]), [0, 0, 600, 800])
    assert result["parsed"]["tables"][0]["values"] == [["Merged", None], ["A", "B"]]
    assert result["edits"][0]["operation"] == "covered_null_to_blank"
    with pytest.raises(ValueError, match="non-string"):
        repair(response([[None, "B"]]), [0, 0, 600, 800])


def test_ragged_rows_pad_only_suffix_and_record_every_invented_blank() -> None:
    result = repair(response([["A", "B", "C"], ["D"], ["E", "F"]]), [0, 0, 600, 800])
    assert result["parsed"]["tables"][0]["values"] == [["A", "B", "C"], ["D", "", ""], ["E", "F", ""]]
    assert len(result["edits"]) == 3
    assert all(edit["invented_blank_slot"] for edit in result["edits"])


def test_bbox_clips_without_rescaling_and_retains_original() -> None:
    result = repair(response([["Literal"]], bbox=[-50, 20, 1100, 980]), [0, 0, 600, 800])
    assert result["parsed"]["tables"][0]["bbox"] == [0, 16, 600, 784]
    edit = result["edits"][0]
    assert edit["original"] == [-50, 20, 1100, 980]
    assert edit["geometry_clipped"]
    assert not edit["rescaled"]


@pytest.mark.parametrize("bbox", [[1001, 20, 1100, 900], [50, 20, 40, 900], [0, 0, float("nan"), 900]])
def test_invalid_or_disjoint_geometry_is_refused(bbox: list) -> None:
    with pytest.raises(ValueError, match="."):
        repair(response([["A"]], bbox=bbox), [0, 0, 600, 800])


@pytest.mark.parametrize("spans", [[[0, 0, 1, 3]], [[0, 0, 1, 2], [0, 1, 1, 2]], [[0, 0, 1, 1]], [[1, 1, 1, 2]]])
def test_invalid_spans_and_missing_anchors_are_refused(spans: list) -> None:
    with pytest.raises(ValueError, match="."):
        repair(response([["A", ""], ["B"]], spans), [0, 0, 600, 800])


@pytest.mark.parametrize("matrix", [[["A", 3]], [["A"], []], [["Anchor", "Nonempty"]]])
def test_ambiguous_types_empty_rows_or_deleting_nonempty_values_are_refused(matrix: list) -> None:
    spans = [[0, 0, 1, 2]] if matrix == [["Anchor", "Nonempty"]] else []
    with pytest.raises(ValueError, match="."):
        repair(response(matrix, spans), [0, 0, 600, 800])


@pytest.mark.parametrize("reason", ["length", "content_filter", "refused", None])
def test_non_normal_outputs_are_never_repaired(reason: str | None) -> None:
    raw = response([["A"], ["B", "C"]])
    raw["choices"][0]["finish_reason"] = reason
    with pytest.raises(ValueError, match="non-normal"):
        repair(raw, [0, 0, 600, 800])


def test_refusal_and_malformed_or_duplicate_json_are_refused() -> None:
    raw = response([["A"]])
    raw["choices"][0]["message"]["refusal"] = "refusal"
    with pytest.raises(ValueError, match="."):
        repair(raw, [0, 0, 600, 800])
    for content in ('{"answers":', '{"answers":{},"answers":{}}'):
        raw = response([["A"]])
        raw["choices"][0]["message"]["content"] = content
        with pytest.raises(ValueError, match="."):
            repair(raw, [0, 0, 600, 800])


def test_overlapping_in_range_spans_are_refused_without_moving_literal_values() -> None:
    raw = response([["A", "", ""]], [[0, 0, 1, 2], [0, 1, 1, 2]])
    before = deepcopy(raw)
    with pytest.raises(ValueError, match="Overlapping"):
        repair(raw, [0, 0, 600, 800])
    assert raw == before


def test_padding_explicit_covered_suffix_preserves_merge_anchor() -> None:
    result = repair(response([["A", "B"], ["Merged"]], [[1, 0, 1, 2]]), [0, 0, 600, 800])
    assert result["parsed"]["tables"][0]["values"] == [["A", "B"], ["Merged", None]]
    assert result["edits"][0]["covered_by_span"]
