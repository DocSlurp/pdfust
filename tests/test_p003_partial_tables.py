"""Partial experiments retain literal valid fragments without repairing tables."""

import json
from copy import deepcopy

import pytest
from bench import p003_partial_tables as partial


def response(tables: list[dict]) -> dict:
    """Create a complete wire response without transport or model calls."""
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps({"answers": {"q0": {"tables": tables}}}),
                },
            }
        ]
    }


@pytest.mark.parametrize("representation", ["legacy", "matrix_strict"])
def test_valid_table_survives_invalid_peer_without_clamping_or_padding(representation: str) -> None:
    good = {"bbox": [0, 0, 400, 1000], "matrix": [["A", "B"]], "mergedspans": []}
    bad_box = {**good, "bbox": [500, 0, 1010, 1000]}
    ragged = {**good, "matrix": [["a", "b"], ["c"]]}
    raw = response([good, bad_box, ragged])
    original = deepcopy(raw)
    result = partial.recover(
        [
            {
                "index": 0,
                "request_index": 0,
                "viewport": [0, 0, 100, 100],
                "transcription_response": raw,
                "transcription_representation": representation,
            }
        ],
        [0, 0, 100, 100],
    )
    assert raw == original
    assert result["state"]["tables"][0]["values"] == [["A", "B"]]
    assert result["retained_table_ids"] == [[0, 0]]
    assert len(result["rejected"]) == 2
    assert result["full_page_success"] is False


def test_all_members_of_overlap_conflict_drop_and_truncation_never_salvages() -> None:
    table = {"bbox": [0, 0, 1000, 1000], "matrix": [["literal"]], "mergedspans": []}
    raw = response([table, table])
    result = partial.recover(
        [{"index": 0, "request_index": 0, "viewport": [0, 0, 100, 100], "transcription_response": raw}],
        [0, 0, 100, 100],
    )
    assert result["state"]["tables"] == []
    assert [r["reason"] for r in result["rejected"]] == ["overlap_ownership_conflict"] * 2
    raw["choices"][0]["finish_reason"] = "length"
    with pytest.raises(ValueError, match="truncated"):
        partial.response_tables(raw, [0, 0, 100, 100])


def test_duplicate_json_key_refuses_complete_response() -> None:
    raw = response([])
    raw["choices"][0]["message"]["content"] = '{"answers":{"q0":{"tables":[],"tables":[]}}}'
    with pytest.raises(ValueError, match="Duplicate"):
        partial.response_tables(raw, [0, 0, 100, 100])
