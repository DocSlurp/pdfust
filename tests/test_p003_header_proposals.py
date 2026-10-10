"""Complete literal header alternatives without default parser repair."""

from __future__ import annotations

from copy import deepcopy

import pytest
from bench import p003_header_proposals as headers
from bench import pipeline_vision_transcription as strict
from bench.silver import canonical


def response(tables: list[dict]) -> dict:
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": canonical({"answers": {"q0": {"tables": tables}}}).decode()},
            }
        ]
    }


def table(k: int = 1, columns: int = 4, index: int = 0) -> dict:
    return {
        "bbox": [index * 200, 0, index * 200 + 180, 900],
        "matrix": [
            [f"Header {i}" for i in range(k)],
            [f"Body {i}" for i in range(columns)],
            [f"Exact math {i} x^2" for i in range(columns)],
        ],
        "mergedspans": [],
    }


def page(tables: list[dict]) -> dict:
    return {
        "id": "page",
        "status": "error",
        "error": "original rectangularity failure",
        "viewport": [0, 0, 100, 100],
        "transcription_regions": [
            {
                "index": 0,
                "request_index": 0,
                "status": "error",
                "viewport": [0, 0, 100, 100],
                "transcription_response": response(tables),
            }
        ],
    }


def test_complete_four_table_alternatives_preserve_every_literal_and_box() -> None:
    tables = [table(1, 4, 0), table(1, 4, 1), table(1, 3, 2), table(3, 4, 3)]
    original = page(tables)
    before = deepcopy(original)
    with pytest.raises(ValueError, match="rectangular"):
        strict.parse(original["transcription_regions"][0]["transcription_response"], original["viewport"])
    plan = headers.freeze_page(original)
    assert original == before
    assert plan["original_page_status"] == "error"
    assert plan["original_page"] == before
    assert plan["status"] == "header_proposals"
    assert len(plan["complete_page_alternatives"]) == 135
    assert plan["source_conserved"] is False
    menus = plan["crop_plans"][0]["table_menus"]
    assert [len(menu) for menu in menus] == [3, 3, 3, 5]
    for raw, menu in zip(tables, menus, strict=True):
        for item in menu:
            assert item["table"]["bbox"] == raw["bbox"]
            assert item["table"]["matrix"][1:] == raw["matrix"][1:]
            assert [item["table"]["matrix"][0][i] for i in item["header_anchors"]] == raw["matrix"][0]
            assert item["inferred_header_structure"] is True
    for proposal in plan["complete_page_alternatives"]:
        assert len(proposal["state"]["tables"]) == 4
        strict.markdown(proposal["state"])
    with pytest.raises(ValueError, match="rectangular"):
        strict.parse(original["transcription_regions"][0]["transcription_response"], original["viewport"])


@pytest.mark.parametrize("mutation", ["body", "merges", "bbox", "unknown", "truncated", "duplicate_json", "nonstrings"])
def test_other_malformation_refuses_complete_page_without_salvage(mutation: str) -> None:
    raw = table()
    if mutation == "body":
        raw["matrix"][2].pop()
    elif mutation == "merges":
        raw["mergedspans"] = [[0, 0, 1, 2]]
    elif mutation == "bbox":
        raw["bbox"][0] = -1
    elif mutation == "unknown":
        raw["extra"] = "not permitted"
    elif mutation == "nonstrings":
        raw["matrix"][1][0] = 5
    original = page([raw])
    if mutation == "truncated":
        original["transcription_regions"][0]["transcription_response"]["choices"][0]["finish_reason"] = "length"
    elif mutation == "duplicate_json":
        original["transcription_regions"][0]["transcription_response"]["choices"][0]["message"]["content"] = (
            '{"answers":{},"answers":{}}'
        )
    plan = headers.freeze_page(original)
    assert plan["status"] == "refused"
    assert plan["complete_page_alternatives"] == []
    assert plan["primary_predicted_tables"] == []


def test_caps_refuse_complete_inventory_not_partial_and_valid_original_control() -> None:
    with pytest.raises(ValueError, match="cap"):
        headers.table_alternatives(table(5, 12), [0, 0, 100, 100])
    capped_tables = [table(1, 4) for _ in range(6)]
    for i, raw in enumerate(capped_tables):
        raw["bbox"] = [i * 150, 0, i * 150 + 140, 900]
    capped = headers.freeze_page(page(capped_tables))
    assert capped["status"] == "refused"
    assert "cap" in capped["reason"]
    valid = table(4, 4)
    original = page([valid])
    original["status"] = "ok"
    original["transcription_regions"][0]["status"] = "ok"
    plan = headers.freeze_page(original)
    assert plan["status"] == "unchanged_valid"
    assert len(plan["complete_page_alternatives"]) == 1
    assert plan["complete_page_alternatives"][0]["state"] == strict.parse(response([valid]), original["viewport"])
    assert headers.freeze_page(original, input_refusal="missing request")["complete_page_alternatives"] == []
    original["status"] = "error"
    refused = headers.freeze_page(original)
    assert refused["status"] == "refused"
    assert "unrelated rescue" in refused["reason"]
