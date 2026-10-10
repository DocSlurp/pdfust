"""Whole literal bands respect independent compatibility and merged-span boundaries."""

import json
from copy import deepcopy

import pytest
from bench import p003_candidate_bands as bands
from bench import pipeline_vision_transcription as adapter


def state(rows: list[list[str]], *, box: list[int] | None = None, spans: list[list[int]] | None = None) -> dict:
    content = {
        "answers": {"q0": {"tables": [{"bbox": box or [0, 0, 1000, 1000], "matrix": rows, "mergedspans": spans or []}]}}
    }
    response = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(content)}}]}
    return adapter.parse(response, [0, 0, 100, 100])


def test_complete_rows_only_and_all_combinations_small_menu() -> None:
    a = state([["name", "value"], ["a", "1"], ["b", "2"]])
    b = state([["name", "value"], ["a corrected", "11"], ["b corrected", "22"]])
    frozen = bands.freeze([0, 0, 100, 100], [a, b])
    alternatives = bands.alternatives(frozen)
    assert len(alternatives) == 4
    assert len(frozen["differing_bands"]) == 2
    for alternative in alternatives:
        table = json.loads(alternative["canonical_json"])["tables"][0]
        assert table["values"][0] == a["tables"][0]["values"][0]
        for row in (1, 2):
            assert table["values"][row] in [a["tables"][0]["values"][row], b["tables"][0]["values"][row]]
    assert not frozen["policy"]["row_index_alignment_physically_verified"]


def test_merged_vertical_span_is_indivisible() -> None:
    a = state([["h", "n"], ["a", "1"], ["", "2"]], spans=[[1, 0, 2, 1]])
    b = state([["h", "n"], ["B", "10"], ["", "20"]], spans=[[1, 0, 2, 1]])
    frozen = bands.freeze([0, 0, 100, 100], [a, b])
    assert [[x["start_row"], x["stop_row"]] for x in frozen["differing_bands"]] == [[1, 3]]
    assert len(bands.alternatives(frozen)) == 2


def test_header_dimensions_and_span_disagreement_keep_whole_controls() -> None:
    a = state([["h", "n"], ["a", "1"], ["b", "2"]])
    b = state([["different", "n"], ["a", "3"], ["b", "4"]])
    frozen = bands.freeze([0, 0, 100, 100], [a, b])
    assert not frozen["matching"]
    assert len(bands.alternatives(frozen)) == 2
    changed = deepcopy(frozen)
    changed["threshold"] = 0.8
    with pytest.raises(ValueError, match="changed"):
        bands.alternatives(changed)


def test_iou_treatment_keeps_original_baseline_geometry_explicit() -> None:
    a = state([["h", "n"], ["a", "1"], ["b", "2"]])
    b = state([["h", "n"], ["B", "3"], ["c", "4"]], box=[10, 0, 990, 1000])
    exact = bands.freeze([0, 0, 100, 100], [a, b], threshold=1.0)
    assert not exact["matching"]
    relaxed = bands.freeze([0, 0, 100, 100], [a, b], threshold=0.95)
    assert relaxed["matching"] == [[0, 0]]
    for item in bands.alternatives(relaxed):
        state_bytes = json.loads(item["canonical_json"])
        if any("band_choices" in p for p in item["provenance"]):
            assert state_bytes["tables"][0]["bbox"] == a["tables"][0]["bbox"]


def test_large_band_menus_use_frozen_bounded_patterns_and_invalid_state_refused() -> None:
    a = state([["h", "n"], *[[str(i), "A"] for i in range(9)]])
    b = state([["h", "n"], *[[str(i), "B"] for i in range(9)]])
    frozen = bands.freeze([0, 0, 100, 100], [a, b])
    assert len(frozen["patterns"]) < 2**9
    assert frozen["patterns"] == sorted(frozen["patterns"])
    broken = deepcopy(b)
    broken["tables"][0]["values"][1] = ["malformed"]
    with pytest.raises(ValueError, match="dimensions"):
        bands.freeze([0, 0, 100, 100], [a, broken])


def test_complete_pattern_capacity_retains_only_controls_and_atomic_overlap_refusal() -> None:
    a = state([["h", "n"], *[[str(i), "A"] for i in range(70)]])
    b = state([["h", "n"], *[[str(i), "B"] for i in range(70)]])
    frozen = bands.freeze([0, 0, 100, 100], [a, b])
    assert frozen["status"] == "capacity_retained_controls"
    assert frozen["patterns"] == []
    assert len(bands.alternatives(frozen)) == 2
    with pytest.raises(ValueError, match="overlap"):
        bands.compose([a, b], [[0, 0, 100, 100]] * 2, [0, 0, 100, 100])
