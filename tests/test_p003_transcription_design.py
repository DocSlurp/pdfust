"""Strict representation and tiny repair invariants; no inference or corpus access."""

from __future__ import annotations

import copy
import json
import math
from typing import Any

import pytest
from bench import p003_transcription_design as design
from bench import pipeline_vision_transcription as adapter


def envelope(tables: list[dict[str, Any]]) -> dict[str, Any]:
    return {"choices": [{"finish_reason": "stop", "message": {
        "content": json.dumps({"answers": {"q0": {"tables": tables}}}),
    }}]}


def matrix_table() -> dict[str, Any]:
    return {"bbox": [0, 0, 1000, 1000], "matrix": [["header", ""], ["x", "x"]],
            "mergedspans": [[0, 0, 1, 2]]}


def atomic_table() -> dict[str, Any]:
    return {"bbox": [0, 0, 1000, 1000], "row_count": 2, "col_count": 2, "cells": [
        {"row": 0, "column": 0, "row_span": 1, "column_span": 2, "text": "header"},
        {"row": 1, "column": 0, "row_span": 1, "column_span": 1, "text": "x"},
        {"row": 1, "column": 1, "row_span": 1, "column_span": 1, "text": "x"},
    ]}


def test_atomic_matches_strict_matrix_without_continuation_records() -> None:
    response = envelope([atomic_table()])
    before = copy.deepcopy(response)
    parsed = design.parse_atomic(response, [10, 20, 110, 220])
    assert parsed == adapter.parse(envelope([matrix_table()]), [10, 20, 110, 220])
    assert parsed["tables"][0]["values"] == [["header", None], ["x", "x"]]
    assert parsed["source_conserved"] is False
    assert response == before


@pytest.mark.parametrize("mutation", ["gap", "overlap", "bounds", "nonliteral", "dimension", "extra"])
def test_atomic_refuses_ambiguous_partition(mutation: str) -> None:
    table = atomic_table()
    if mutation == "gap":
        table["cells"].pop()
    elif mutation == "overlap":
        table["cells"][1]["row"] = 0
    elif mutation == "bounds":
        table["cells"][0]["column_span"] = 3
    elif mutation == "nonliteral":
        table["cells"][0]["text"] = None
    elif mutation == "dimension":
        table["row_count"] = True
    else:
        table["invented"] = "bad"
    with pytest.raises(ValueError, match=r"gaps|overlap|outside|literal|dimensions|keys"):
        design.parse_atomic(envelope([table]), [0, 0, 1, 1])


def test_atomic_unordered_anchors_and_explicit_empty_cells() -> None:
    table = atomic_table()
    table["cells"] = list(reversed(table["cells"]))
    table["cells"][0]["text"] = ""
    parsed = design.parse_atomic(envelope([table]), [0, 0, 1, 1])
    assert parsed["tables"][0]["values"][1] == ["x", ""]


def test_atomic_all_tables_atomic_and_aggregate_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    bad = atomic_table()
    bad["cells"].pop()
    with pytest.raises(ValueError, match="gaps"):
        design.parse_atomic(envelope([atomic_table(), bad]), [0, 0, 1, 1])
    monkeypatch.setattr(adapter, "MAX_TOTAL_SLOTS", 4)
    with pytest.raises(ValueError, match="slot admission"):
        design.parse_atomic(envelope([atomic_table(), atomic_table()]), [0, 0, 1, 1])


@pytest.mark.parametrize("representation", ["atomic_cells", "matrix_strict", "topology"])
def test_prompt_variants_are_provider_independent_and_strict(representation: str) -> None:
    variant = design.prompt_variant(representation)
    assert "model" not in variant
    assert "normalized 0..1000" in variant["instructions"]
    assert variant["schema"]["additionalProperties"] is False
    assert variant["source_conserved"] is False
    assert variant["runtime_integration"] is False


def test_no_repair_changes_on_already_valid_response() -> None:
    result = envelope([matrix_table()])
    before = copy.deepcopy(result)
    repaired = design.repair(result, [0, 0, 1, 1])
    assert repaired["parsed"] == adapter.parse(result, [0, 0, 1, 1])
    assert repaired["edits"] == []
    assert repaired["quality_validated"] is False
    assert result == before


def test_redundant_spans_have_exact_identity_interpretation() -> None:
    table = matrix_table()
    table["mergedspans"].extend([[0, 0, 1, 2], [1, 0, 1, 1]])
    result = design.repair(envelope([table]), [0, 0, 1, 1])
    assert result["parsed"] == adapter.parse(envelope([matrix_table()]), [0, 0, 1, 1])
    assert [e["operation"] for e in result["edits"]] == [
        "remove_exact_duplicate_span", "remove_unit_identity_span",
    ]


def test_only_one_ulp_normalized_endpoint_excursions() -> None:
    table = matrix_table()
    table["bbox"] = [math.nextafter(0, -math.inf), 0, math.nextafter(1000, math.inf), 1000]
    result = design.repair(envelope([table]), [0, 0, 1, 1])
    assert result["parsed"] == adapter.parse(envelope([matrix_table()]), [0, 0, 1, 1])
    assert len(result["edits"]) == 2
    table["bbox"][2] = math.nextafter(table["bbox"][2], math.inf)
    with pytest.raises(ValueError, match="outside normalized"):
        design.repair(envelope([table]), [0, 0, 1, 1])


@pytest.mark.parametrize("mechanism", ["bbox", "ragged", "covered", "span", "overlap", "unit"])
def test_substantive_failures_never_repaired(mechanism: str) -> None:
    table = matrix_table()
    if mechanism == "bbox":
        table["bbox"][2] = 1010
    elif mechanism == "ragged":
        table["matrix"][1].pop()
    elif mechanism == "covered":
        table["matrix"][0][1] = "header"
    elif mechanism == "span":
        table["mergedspans"][0][3] = 3
    elif mechanism == "overlap":
        table["mergedspans"].append([0, 0, 2, 1])
    else:
        table["mergedspans"].append([5, 0, 1, 1])
    with pytest.raises(ValueError, match=r"outside|rectangular|Covered|bounds|Overlapping|slots"):
        design.repair(envelope([table]), [0, 0, 1, 1])


@pytest.mark.parametrize("parser", [design.repair, design.parse_atomic])
@pytest.mark.parametrize("finish", ["length", "content_filter", None])
def test_abnormal_completions_never_repaired(parser: Any, finish: str | None) -> None:  # noqa: ANN401
    response = envelope([])
    response["choices"][0]["finish_reason"] = finish
    with pytest.raises(ValueError, match="finish normally"):
        parser(response, [0, 0, 1, 1])


@pytest.mark.parametrize("parser", [design.repair, design.parse_atomic])
def test_duplicate_json_keys_refused(parser: Any) -> None:  # noqa: ANN401
    result = envelope([])
    result["choices"][0]["message"]["content"] = '{"answers":{},"answers":{}}'
    with pytest.raises(ValueError, match="Duplicate"):
        parser(result, [0, 0, 1, 1])
