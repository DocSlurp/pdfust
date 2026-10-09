"""Complete-page accounting for independently authored pipeline references."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.pipeline_corpus import _table, build
from bench.pipeline_scoring import conservation, score_dataset, score_page


def target(*tables: dict[str, Any]) -> dict[str, Any]:
    return {"id": "opaque", "tables": list(tables), "structural_scored": True}


def test_complete_merged_table_and_covered_slots() -> None:
    table = _table([["Merged", "Merged"], ["a", "b"]], ((0, 0, 1, 2),))
    score = score_page(target(table), [deepcopy(table)])
    assert score["exact_page"]
    assert score["correct_cell_slots"] == 4
    assert score["complete_tables"] == 1
    absent = score_page(target(table), [])
    assert absent["correct_cell_slots"] == 0
    assert absent["cell_slots"] == 4
    assert absent["missing_tables"] == 1


def test_wrapped_whitespace_normalization_retains_values() -> None:
    table = _table([["North depot", "42"], ["West", "7"]])
    prediction = deepcopy(table)
    prediction["values"][0][0] = "North\n depot"
    assert score_page(target(table), [prediction])["exact_page"]
    prediction["values"][0][0] = "North"
    score = score_page(target(table), [prediction])
    assert not score["exact_page"]
    assert score["correct_cell_slots"] == 3


def test_extra_duplicate_table_penalizes_page_table_and_cells() -> None:
    table = _table([["a", "b"], ["c", "d"]])
    score = score_page(target(table), [table, table])
    assert not score["exact_page"]
    assert score["complete_tables"] == 1
    assert score["false_positive_tables"] == 1
    assert score["table_denominator"] == 2
    assert score["penalized_cell_slots"] == 8


def test_multiple_tables_match_one_to_one_in_any_order() -> None:
    first = _table([["a", "b"], ["c", "d"]])
    second = _table([["e", "f"], ["g", "h"]])
    assert score_page(target(first, second), [second, first])["exact_page"]
    score = score_page(target(first, second), [first])
    assert score["complete_tables"] == 1
    assert score["missing_tables"] == 1
    assert score["cell_slots"] == 8


def test_span_error_prevents_complete_table() -> None:
    table = _table([["a", "b"], ["c", "d"]])
    observed = deepcopy(table)
    observed["spans"][0]["column_span"] = 2
    score = score_page(target(table), [observed])
    assert score["exact_table_cells"] == 1
    assert score["exact_table_spans"] == 0
    assert not score["exact_page"]


def test_negative_errors_and_missing_outputs_stay_in_denominator() -> None:
    positive = target(_table([["a", "b"], ["c", "d"]]))
    negative = {**target(), "id": "negative"}
    diagnostic = {**target(), "id": "natural", "structural_scored": False}
    result = score_dataset([positive, negative, diagnostic], [{"id": "negative", "status": "error"}])
    assert result["totals"]["scored_pages"] == 2
    assert result["totals"]["error"] == 2
    assert result["totals"]["exact_page"] == 0
    assert result["totals"]["cell_slots"] == 4
    assert result["totals"]["diagnostic_pages"] == 1


def test_negative_false_positive_accounting() -> None:
    table = _table([["a", "b"], ["c", "d"]])
    score = score_page(target(), [table])
    assert score["false_positive_page"]
    assert score["false_positive_tables"] == 1
    assert score["penalized_cell_slots"] == 4
    assert score_page(target(), [])["exact_page"]


def test_malformed_matrix_cannot_receive_partial_credit() -> None:
    table = _table([["a", "b"], ["c", "d"]])
    malformed = deepcopy(table)
    malformed["values"].pop()
    score = score_page(target(table), [table, malformed])
    assert score["error"]
    assert score["malformed"]
    assert score["correct_cell_slots"] == 0
    assert score["cell_slots"] == 4


def test_duplicate_and_unknown_output_ids_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        score_dataset([target()], [{"id": "opaque"}, {"id": "opaque"}])
    with pytest.raises(ValueError, match="outside"):
        score_dataset([target()], [{"id": "new"}])


def test_conservation_separates_missing_duplicate_and_unknown() -> None:
    score = conservation(["w0", "w1", "w2"], ["w0", "w0", "w1", "invented"])
    assert score == {
        "source_count": 3,
        "assigned_count": 4,
        "missing_count": 1,
        "duplicate_count": 1,
        "unknown_count": 1,
        "exact_conservation": False,
    }
    assert conservation(["w0", "w1"], ["w1", "w0"])["exact_conservation"]


def test_corpus_freezes_complete_cohort_and_balanced_pilot(tmp_path: Path) -> None:
    manifest = build(tmp_path / "corpus")
    private = json.loads((tmp_path / "corpus/private-targets.json").read_text())["pages"]
    assert len(manifest["pages"]) == 181
    assert len({page["id"] for page in manifest["pages"]}) == 181
    assert sum(page["structural_scored"] for page in private) == 168
    targets = {page["id"]: page for page in private}
    pilot = [page for page in manifest["pages"] if page["pilot"]]
    assert len(pilot) == 32
    assert sum(bool(targets[page["id"]]["tables"]) for page in pilot) == 16
    assert all(Path(page["pdf_path"]).is_absolute() for page in manifest["pages"])
    assert all("tables" not in page for page in manifest["pages"])
    assert build(tmp_path / "other")["dataset_sha256"] == manifest["dataset_sha256"]
