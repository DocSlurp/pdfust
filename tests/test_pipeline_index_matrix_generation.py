"""Ordinal identity must preserve literal source ownership and strict topology."""

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest
from bench import pipeline_matrix_generation as ids
from bench.pipeline_index_matrix_generation import freeze, parse, request
from test_pipeline_generation import MODELS, response, source


def ordinal() -> dict:
    return {"matrix": [[[0], []], [[1], [2]]], "spans": [[0, 0, 1, 2]]}


def unicode_source() -> dict:
    data = source()
    for word, identifier, text in zip(
        data["words"], ["r:w零", "opaque-β", "0007", "尾注"], ["地域", "North α", "12", "Footnote"], strict=True
    ):
        word["id"], word["text"] = identifier, text
    return data


def test_roundtrip_matches_strict_id_matrix_and_preserves_prose() -> None:
    data = unicode_source()
    frozen = freeze(data)
    raw = ordinal()
    expanded = deepcopy(raw)
    for row in expanded["matrix"]:
        for cell in row:
            cell[:] = [data["words"][index]["id"] for index in cell]
    actual = parse(frozen, response([raw]))
    expected = ids.parse(data, response([expanded]))
    actual["mechanism"] = expected["mechanism"]
    assert actual == expected
    assert actual["unresolved_ids"] == ["尾注"]


@pytest.mark.parametrize("format_name", ["objects", "arrays", "quarter"])
def test_evidence_changes_only_identity(format_name: str) -> None:
    data = unicode_source()
    expected = json.loads(ids.request(data, MODELS[0], evidence_format=format_name)["messages"][1]["content"])
    body = request(freeze(data), MODELS[0], evidence_format=format_name, max_tokens=16384)
    packet = json.loads(body["messages"][1]["content"])
    if format_name == "objects":
        for index, word in enumerate(expected["words"]):
            del word["id"]
            word["index"] = index
    else:
        expected["word_fields"][0] = "index"
        for index, word in enumerate(expected["words"]):
            word[0] = index
    assert packet == expected
    assert not any(word["id"] in json.dumps(body, ensure_ascii=False) for word in data["words"])
    entry = body["response_format"]["json_schema"]["schema"]["properties"]["answers"]["properties"]["q0"]["properties"][
        "tables"
    ]["items"]
    assert entry["properties"]["matrix"]["items"]["items"]["items"] == {"type": "integer", "minimum": 0, "maximum": 3}
    assert body["max_tokens"] == 16384


def test_snapshot_is_immutable_and_caller_mutation_cannot_reindex() -> None:
    data = unicode_source()
    frozen = freeze(data)
    before = request(frozen, MODELS[0])
    data["words"].reverse()
    data["words"][0]["text"] = "changed"
    exported = frozen.source()
    exported["words"].clear()
    assert request(frozen, MODELS[0]) == before
    assert parse(frozen, response([ordinal()]))["unresolved_ids"] == ["尾注"]
    with pytest.raises(FrozenInstanceError):
        frozen.words = ()  # type: ignore[misc]


@pytest.mark.parametrize("index", [True, False, 1.0, "1", -1, 4, None, {}, []])
def test_invalid_index_types_and_ranges_are_rejected(index: object) -> None:
    raw = {"matrix": [[[index]]], "spans": []}
    with pytest.raises(ValueError, match="in-range integer"):
        parse(source(), response([raw]))


@pytest.mark.parametrize(
    "raw",
    [
        {"matrix": [[[0, 0]]], "spans": []},
        {"matrix": [[[0], [0]]], "spans": []},
        {"matrix": [[[0], [1]]], "spans": [[0, 0, 1, 2]]},
        {"matrix": [[[0]]], "spans": [[0, 0, 1, 1]]},
        {"matrix": [[[0], []]], "spans": [[0, 0, 1, 2], [0, 0, 1, 2]]},
        {"matrix": [[[0]], []], "spans": []},
    ],
)
def test_duplicate_and_topology_refusals_are_atomic(raw: dict) -> None:
    with pytest.raises(ValueError, match=r".+"):
        parse(source(), response([raw]))


def test_cross_table_duplicate_is_rejected_and_raw_response_preserved() -> None:
    raw = response([ordinal(), ordinal()])
    before = deepcopy(raw)
    with pytest.raises(ValueError, match="Duplicate"):
        parse(source(), raw)
    assert raw == before


@pytest.mark.parametrize("finish", ["length", "content_filter", "tool_calls", None])
def test_abnormal_finishes_are_rejected(finish: str | None) -> None:
    with pytest.raises(ValueError, match="normal finish"):
        parse(source(), response([ordinal()], finish))  # type: ignore[arg-type]


def test_refusal_duplicate_keys_and_nonfinite_are_rejected() -> None:
    raw = response([])
    raw["choices"][0]["message"]["refusal"] = "refused"
    with pytest.raises(ValueError, match=r".+"):
        parse(source(), raw)
    for content in ['{"answers":{"q0":{"tables":[],"tables":[]}}}', '{"answers":{"q0":{"tables":NaN}}}']:
        raw = response([])
        raw["choices"][0]["message"]["content"] = content
        with pytest.raises(ValueError, match=r".+"):
            parse(source(), raw)


def test_empty_source_and_output_token_boundary() -> None:
    empty = {"page_size": [600, 800], "words": []}
    assert parse(empty, response([]))["unresolved_ids"] == []
    body = request(empty, MODELS[0])
    cell = body["response_format"]["json_schema"]["schema"]["properties"]["answers"]["properties"]["q0"]["properties"][
        "tables"
    ]["items"]["properties"]["matrix"]["items"]["items"]
    assert cell["maxItems"] == 0
    with pytest.raises(ValueError, match=r".+"):
        parse(empty, response([{"matrix": [[[0]]], "spans": []}]))
    with pytest.raises(ValueError, match=r".+"):
        request(source(), MODELS[0], max_tokens=16385)


def test_order_inside_cell_and_optional_image_are_preserved() -> None:
    data = unicode_source()
    frozen = freeze(data)
    raw = {"matrix": [[[2, 0, 1]]], "spans": []}
    state = parse(frozen, response([raw]))
    assert state["tables"][0]["values"] == [["12 地域 North α"]]
    body = request(frozen, MODELS[0], "data:image/png;base64,YQ==", [0, 0, 600, 800], 512)
    content = body["messages"][1]["content"]
    assert content[1]["image_url"]["url"] == "data:image/png;base64,YQ=="
    assert json.loads(content[0]["text"])["viewport"] == [0, 0, 600, 800]


def test_complete_source_and_cumulative_slots_are_admitted_without_truncation() -> None:
    data = source()
    data["words"].append(deepcopy(data["words"][0]))
    with pytest.raises(ValueError, match=r".+"):
        freeze(data)
    empty: dict = {"matrix": [[[] for _ in range(64)] for _ in range(64)], "spans": []}
    with pytest.raises(ValueError, match="cumulative slot"):
        parse(source(), response([empty, empty]))
