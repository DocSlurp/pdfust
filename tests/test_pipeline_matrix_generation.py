"""Compact syntax must preserve the anchor parser's source and topology gates."""

import json
from copy import deepcopy

import pytest
from bench.pipeline_generation import parse as anchor_parse
from bench.pipeline_matrix_generation import parse, request
from test_pipeline_generation import MODELS, response, source, table


def matrix() -> dict:
    return {"matrix": [[["w0"], []], [["w1"], ["w2"]]], "spans": [[0, 0, 1, 2]]}


def test_matrix_matches_anchor_state_and_keeps_unassigned_prose() -> None:
    state = parse(source(), response([matrix()]))
    expected = anchor_parse(source(), response([table()]))
    state["mechanism"] = expected["mechanism"]
    assert state == expected


def test_matrix_evidence_is_complete_and_source_only() -> None:
    body = request(source(), MODELS[0], max_tokens=8192, viewport=[0, 0, 600, 800])
    assert "secret-" not in json.dumps(body)
    assert json.loads(body["messages"][1]["content"])["words"][0]["text"] == "Site"
    schema = body["response_format"]["json_schema"]["schema"]
    entry = schema["properties"]["answers"]["properties"]["q0"]["properties"]["tables"]["items"]
    assert set(entry["properties"]) == {"matrix", "spans"}
    assert body["max_tokens"] == 8192


@pytest.mark.parametrize(
    "raw",
    [
        {"matrix": [], "spans": []},
        {"matrix": [[[]], []], "spans": []},
        {"matrix": [[["unknown"]]], "spans": []},
        {"matrix": [[["w0", "w0"]]], "spans": []},
        {"matrix": [[["w0"], ["w0"]]], "spans": []},
        {"matrix": [[["w0"], ["w1"]]], "spans": [[0, 0, 1, 2]]},
        {"matrix": [[["w0"]]], "spans": [[0, 0, 1, 1]]},
        {"matrix": [[["w0"]]], "spans": [[True, 0, 1, 2]]},
        {"matrix": [[["w0"]]], "spans": [[0, 0, 1, 2]]},
        {"matrix": [[["w0"], []]], "spans": [[0, 0, 1, 2], [0, 0, 1, 2]]},
        {"matrix": [["w0"]], "spans": []},
        {"matrix": [[["w0"]]], "spans": [], "text": "invented"},
    ],
)
def test_invalid_matrices_fail_as_a_whole(raw: dict) -> None:
    with pytest.raises(ValueError, match=r".+"):
        parse(source(), response([raw]))


def test_empty_slots_are_not_missing_and_cross_table_ids_cannot_repeat() -> None:
    raw = {"matrix": [[["w0"], []], [[], []]], "spans": []}
    state = parse(source(), response([raw]))
    assert state["tables"][0]["values"] == [["Site", ""], ["", ""]]
    assert len(state["tables"][0]["spans"]) == 4
    with pytest.raises(ValueError, match="Duplicate"):
        parse(source(), response([raw, deepcopy(raw)]))


def test_truncation_and_duplicate_json_keys_are_not_repaired() -> None:
    with pytest.raises(ValueError, match="truncated"):
        parse(source(), response([matrix()], "length"))
    result = response([])
    result["choices"][0]["message"]["content"] = '{"answers":{"q0":{"tables":[],"tables":[]}}}'
    with pytest.raises(ValueError, match="Duplicate"):
        parse(source(), result)
