"""Difference projection exposes every exact dispute without changing winners."""
# ruff: noqa: SLF001

import base64
import json
from copy import deepcopy
from typing import Any

import pytest
from bench import p003_candidate_choice as chooser
from bench import p003_candidate_diff as diff
from bench import p003_candidate_run as runner
from bench.pipeline_vision_transcription import parse

URL = "data:image/png;base64," + base64.b64encode(b"offline").decode()
VIEW = [0, 0, 100, 100]


def candidate(matrix: list[list[str]], merged: list[list[int]] | None = None) -> dict[str, Any]:
    payload = {
        "answers": {"q0": {"tables": [{"bbox": [0, 0, 1000, 1000], "matrix": matrix, "mergedspans": merged or []}]}}
    }
    return parse({"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}]}, VIEW)


def pool(a: dict[str, Any], b: dict[str, Any]) -> chooser.Pool:
    return chooser.freeze_pool(VIEW, [a, b], seed=71)


def test_every_difference_literal_headers_and_common_omission() -> None:
    a = candidate([["Name", "Value"], ["SHARED-COMMON-TEXT", "literal"], ["x", ""]])
    b = candidate([["Name", "Value"], ["SHARED-COMMON-TEXT", "literal "], ["y", ""]])
    frozen = pool(a, b)
    evidence = diff.comparison(frozen)
    assert [(t, r, c) for t, r, c, _ in evidence["differing_slots"]] == [(0, 1, 1), (0, 2, 0)]
    assert "SHARED-COMMON-TEXT" not in json.dumps(evidence)
    assert {v["value"] for v in evidence["differing_slots"][0][3].values()} == {"literal", "literal "}
    assert list(evidence["first_row_context"].values()) == [[["Name", "Value"]], [["Name", "Value"]]]
    assert "input_indexes" not in json.dumps(evidence)
    assert "snapshot_sha256" not in json.dumps(evidence)


def test_absent_table_row_column_and_merged_slots_are_distinct() -> None:
    a = candidate([["Header", ""], ["x", ""]], [[0, 0, 1, 2]])
    b = candidate([["Header"], ["x"], ["extra"]])
    frozen = pool(a, b)
    evidence = diff.comparison(frozen)
    entries = {(t, r, c): list(slots.values()) for t, r, c, slots in evidence["differing_slots"]}
    assert {json.dumps(v, sort_keys=True) for v in entries[(0, 0, 1)]} == {
        '{"present": false}',
        '{"present": true, "value": null}',
    }
    assert {json.dumps(v, sort_keys=True) for v in entries[(0, 1, 1)]} == {
        '{"present": false}',
        '{"present": true, "value": ""}',
    }
    assert (0, 2, 0) in entries
    b = deepcopy(b)
    b["tables"] = []
    empty = diff.comparison(pool(a, b))
    assert len(empty["differing_slots"]) == 4


def test_geometry_only_dispute_and_exact_selected_original() -> None:
    a, b = candidate([["H"], ["same"]]), candidate([["H"], ["same"]])
    b["tables"][0]["bbox"] = [0, 0, 90, 100]
    frozen = pool(a, b)
    body = diff.request(frozen, "model", URL)
    assert json.loads(body["state"][0])["differing_slots"] == []
    assert len({json.dumps(v) for v in json.loads(body["state"][0])["table_summaries"].values()}) == 2
    answer = {
        "answers": {"q0": {"type": "choice", "choice": "A", "probabilities": {"A": 0.7, "B": 0.2, "unresolved": 0.1}}}
    }
    selected, _ = chooser.select(frozen, chooser.parse(frozen, answer))
    assert selected == frozen.candidates[0].canonical_bytes
    answer["answers"]["q0"]["choice"] = "unresolved"
    answer["answers"]["q0"]["probabilities"] = {"A": 0.1, "B": 0.2, "unresolved": 0.7}
    assert chooser.select(frozen, chooser.parse(frozen, answer))[0] is None


def test_cap_never_truncates_and_default_body_is_unchanged() -> None:
    frozen = pool(candidate([["H"], ["first"]]), candidate([["H"], ["second"]]))
    body = diff.request(frozen, "model", URL)
    count = len(body["state"][0].encode())
    assert diff.request(frozen, "model", URL, max_bytes=count) == body
    with pytest.raises(diff.EvidenceCapacityError):
        diff.request(frozen, "model", URL, max_bytes=count - 1)
    assert runner._body(frozen, "model", URL, 512) == chooser.request(frozen, "model", URL)
    control = runner._body(frozen, "model", URL, 0, evidence_mode="differences")
    assert isinstance(control["state"], str)
    assert "difference projection" in control["questions"]["q0"]["instructions"]
    assert "text-only control" in control["questions"]["q0"]["instructions"]


@pytest.mark.parametrize("cap", [False, 0, -1, 131073, 1.5])
def test_invalid_cap(cap: float) -> None:
    frozen = pool(candidate([["H"], ["a"]]), candidate([["H"], ["b"]]))
    with pytest.raises(ValueError, match="cap"):
        diff.comparison(frozen, max_bytes=cap)
