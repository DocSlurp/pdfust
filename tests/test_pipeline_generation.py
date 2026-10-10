"""Offline contracts for source-ID-only generative assembly."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_assembly import validate
from bench.pipeline_generation import MAX_RESPONSE_CHARACTERS, MODELS, parse, request


def source() -> dict:
    """Include forbidden metadata to verify explicit source-only projection."""
    return {
        "page_size": [600, 800],
        "family": "secret-family",
        "filename": "secret-file.pdf",
        "annotation_html": "secret-answer",
        "words": [
            {"id": "w0", "text": "Site", "bbox": [10, 10, 30, 20], "gold": "secret-cell"},
            {"id": "w1", "text": "North", "bbox": [10, 30, 40, 40]},
            {"id": "w2", "text": "12", "bbox": [50, 30, 60, 40]},
            {"id": "w3", "text": "Footnote", "bbox": [10, 200, 60, 210]},
        ],
    }


def cell(row: int, column: int, ids: list[Any], row_span: int = 1, column_span: int = 1) -> dict:
    """Build a declared anchor independent of literal text."""
    return {"row": row, "column": column, "row_span": row_span, "column_span": column_span, "source_ids": ids}


def response(tables: object, finish: str = "stop") -> dict:
    """Return an ordinary complete chat transport envelope."""
    return {
        "choices": [
            {"finish_reason": finish, "message": {"content": json.dumps({"answers": {"q0": {"tables": tables}}})}}
        ]
    }


def table() -> dict:
    """Declare a merged header and two data anchors."""
    return {
        "rows": 2,
        "columns": 2,
        "cells": [cell(0, 0, ["w0"], column_span=2), cell(1, 0, ["w1"]), cell(1, 1, ["w2"])],
    }


@pytest.mark.parametrize("model", MODELS)
def test_request_uses_client_schema_and_strips_metadata(model: str) -> None:
    body = request(source(), model)
    schema = body["response_format"]["json_schema"]["schema"]["properties"]["answers"]["properties"]["q0"]
    assert set(schema["properties"]) == {"tables"}
    assert "secret-" not in json.dumps(body)
    assert body["max_tokens"] == 4096
    evidence = json.loads(body["messages"][1]["content"])
    assert len(evidence["words"]) == 4
    assert evidence["words"][0] == {"id": "w0", "text": "Site", "bbox": [10, 10, 30, 20]}
    assert "OCR text is fixed" in body["messages"][0]["content"]


def test_image_evidence_has_literal_text_first_and_explicit_viewport() -> None:
    body = request(source(), MODELS[0], "data:image/png;base64,YQ==", [0, 0, 600, 800], 2048)
    blocks = body["messages"][1]["content"]
    assert [block["type"] for block in blocks] == ["text", "image_url"]
    assert json.loads(blocks[0]["text"])["viewport"] == [0, 0, 600, 800]
    assert len(json.loads(blocks[0]["text"])["words"]) == 4


def test_complete_state_derives_values_and_preserves_prose() -> None:
    state = parse(source(), response([table()]))
    assert state["tables"][0]["values"] == [["Site", None], ["North", "12"]]
    assert state["unresolved_ids"] == ["w3"]
    validate(source(), state)


def test_omitted_slots_become_empty_anchors_without_losing_tokens() -> None:
    state = parse(source(), response([{"rows": 2, "columns": 2, "cells": [cell(0, 0, ["w1", "w2"])]}]))
    assert state["tables"][0]["values"] == [["North 12", ""], ["", ""]]
    assert len(state["tables"][0]["spans"]) == 4
    assert state["unresolved_ids"] == ["w0", "w3"]
    assert parse(source(), response([]))["unresolved_ids"] == ["w0", "w1", "w2", "w3"]


@pytest.mark.parametrize(
    "invalid",
    [
        {"rows": True, "columns": 2, "cells": []},
        {"rows": 0, "columns": 2, "cells": []},
        {"rows": 2.0, "columns": 2, "cells": []},
        {"rows": 4096, "columns": 2, "cells": []},
        {"rows": 2, "columns": 2, "cells": "wrong"},
        {"rows": 2, "columns": 2, "cells": [cell(0, 0, ["unknown"])]},
        {"rows": 2, "columns": 2, "cells": [cell(0, 0, ["w0", "w0"])]},
        {"rows": 2, "columns": 2, "cells": [cell(0, 0, [False])]},
        {"rows": 2, "columns": 2, "cells": [cell(0, 0, ["w0"], row_span=3)]},
        {"rows": 2, "columns": 2, "cells": [cell(0, 0, ["w0"], column_span=2), cell(0, 1, ["w1"])]},
        {"rows": 2, "columns": 2, "cells": [cell(0, 0, ["w0"]), cell(0, 0, ["w1"])]},
        {"rows": 2, "columns": 2, "cells": [{**cell(0, 0, ["w0"]), "text": "invention"}]},
    ],
)
def test_invalid_topology_and_ownership_reject_whole_response(invalid: dict) -> None:
    with pytest.raises(ValueError, match=r".+"):
        parse(source(), response([invalid]))


def test_duplicate_ownership_across_tables_is_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        parse(source(), response([table(), table()]))


@pytest.mark.parametrize("finish", ["length", "content_filter", "tool_calls", None])
def test_abnormal_finish_rejected(finish: str) -> None:
    with pytest.raises(ValueError, match="truncated"):
        parse(source(), response([], finish))


@pytest.mark.parametrize(
    "content",
    [
        "{",
        "[]",
        '{"answers":{"q0":{"tables":[],"text":"bad"}}}',
        '{"answers":{"q0":{"tables":[],"tables":[]}}}',
        '{"answers":{"q0":{"tables":NaN}}}',
    ],
)
def test_malformed_extra_or_duplicate_json_rejected(content: str) -> None:
    result = response([])
    result["choices"][0]["message"]["content"] = content
    with pytest.raises(ValueError, match=r".+"):
        parse(source(), result)


def test_refusal_and_response_size_are_rejected() -> None:
    result = response([])
    result["choices"][0]["message"]["refusal"] = "refused"
    with pytest.raises(ValueError, match=r".+"):
        parse(source(), result)
    result["choices"][0]["message"] = {"content": " " * (MAX_RESPONSE_CHARACTERS + 1)}
    with pytest.raises(ValueError, match="exceeds"):
        parse(source(), result)


def test_request_bounds_and_invalid_source_rejected() -> None:
    for kwargs in (
        {"model": "unknown"},
        {"max_tokens": True},
        {"viewport": [0, 0]},
        {"url": "https://example.com/filename.png"},
    ):
        with pytest.raises(ValueError, match=r".+"):
            request(source(), **({"model": MODELS[0]} | kwargs))
    broken = deepcopy(source())
    broken["words"][1]["id"] = "w0"
    with pytest.raises(ValueError, match="Duplicate"):
        request(broken, MODELS[0])
