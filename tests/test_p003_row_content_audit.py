"""Literal conditional record projection does not credit immutable context."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from bench.decision_rows import materialize_assignments, project_input
from bench.p003_row_content_audit import body_table, compare_body


def source() -> dict[str, Any]:
    return project_input(
        {
            "words": [
                {"id": i, "text": text, "bbox": [i * 10, 0, i * 10 + 8, 8]}
                for i, text in enumerate(["Name", "USD", "Alpha", "Beta", "120"])
            ],
            "headers": [{"id": "h0", "source_ids": [0]}, {"id": "h1", "source_ids": [1]}],
            "rows": [{"id": "r0", "bbox": [0, 0, 100, 20]}, {"id": "r1", "bbox": [0, 10, 100, 20]}],
            "columns": [
                {"id": "c0", "bbox": [0, 0, 50, 20], "role": "row_key", "header_path": [[0]]},
                {"id": "c1", "bbox": [50, 0, 100, 20], "role": "value", "header_path": [[1]]},
            ],
            "fragments": [
                {"id": "a", "source_ids": [2]},
                {"id": "b", "source_ids": [3]},
                {"id": "v", "source_ids": [4]},
            ],
        }
    )


def test_projection_keeps_join_split_and_omissions_distinct() -> None:
    spec = source()
    joined = materialize_assignments(spec, {"a": ["r0", "c0"], "b": ["r0", "c0"], "v": ["r0", "c1"]})
    split = materialize_assignments(spec, {"a": ["r0", "c0"], "b": ["r1", "c0"], "v": ["r0", "c1"]})
    assert body_table(spec, joined) == {"row_count": 1, "col_count": 2, "values": [["Alpha Beta", "120"]], "spans": []}
    assert body_table(spec, split) == {
        "row_count": 2,
        "col_count": 2,
        "values": [["Alpha", "120"], ["Beta", ""]],
        "spans": [],
    }
    omitted = materialize_assignments(spec, dict.fromkeys(["a", "b", "v"]))
    assert body_table(spec, omitted) is None
    assert compare_body(body_table(spec, joined), None)["counts"]["missing"] == 13


def test_wrong_row_does_not_become_content_complete() -> None:
    reference = {"row_count": 2, "col_count": 2, "values": [["A", "1"], ["B", "2"]], "spans": []}
    predicted = {**reference, "values": [["B", "2"], ["A", "1"]]}
    assert not compare_body(reference, predicted)["content_recovered_with_row_order"]


def test_projection_rejects_duplicate_record_ownership() -> None:
    spec = source()
    assembly = materialize_assignments(spec, {"a": ["r0", "c0"], "b": ["r0", "c0"], "v": ["r0", "c1"]})
    corrupted = deepcopy(assembly)
    corrupted["records"].append(corrupted["records"][0])
    with pytest.raises(ValueError, match="duplicate or omit"):
        body_table(spec, corrupted)


def test_headers_cannot_be_reused_as_body() -> None:
    spec = source()
    assembly = materialize_assignments(spec, {"a": ["r0", "c0"], "b": ["r0", "c0"], "v": ["r0", "c1"]})
    assembly["records"][0]["row_key_ids"].append(0)
    with pytest.raises(ValueError, match="source identity"):
        body_table(spec, assembly)
