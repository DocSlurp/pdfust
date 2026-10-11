"""Tolerant content near misses preserve row membership and numeric boundaries."""

from __future__ import annotations

import random

import pytest
from bench.p003_content_alignment import LIMITS, compare_content


def test_rank_name_shared_split_and_blank_header() -> None:
    reference = [["No.", "Record", "Points"], ["1. Hingham", "6-0-0", "2"], ["2. Harbor", "5-1-0", "3"]]
    prediction = [["No.", "", "Record", "Points"], ["1.", "Hingham", "6-0-0", "2"], ["2.", "Harbor", "5-1-0", "3"]]
    result = compare_content(reference, prediction)
    assert result["supported"] is True
    assert result["content_recovered_with_row_order"] is True
    assert result["precision"] == result["recall"] == 1
    assert result["schema_correctness"] is None
    assert result["shared_column_path"][0] == {"reference_columns": [0, 1], "prediction_columns": [0, 2]}
    assert result["row_alignment"][1]["cells"][0]["join_provenance"]["prediction_cells"] == 2


@pytest.mark.parametrize("prediction", ["Hingham", "North"])
def test_prefix_and_suffix_partial_recovery(prediction: str) -> None:
    result = compare_content([["Hingham North"]], [[prediction]])
    assert result["counts"]["matched"] == len(prediction)
    assert result["counts"]["missing"] == len("Hingham North") - len(prediction)
    assert result["precision"] == 1
    assert 0 < result["recall"] < 1
    assert result["content_recovered_with_row_order"] is False


def test_extra_middle_cell_keeps_later_cells_and_penalizes_extra() -> None:
    result = compare_content(
        [["Alpha", "12", "$40.00"], ["Beta", "25", "$60.00"]],
        [["Alpha", "junk", "12", "$40.00"], ["Beta", "junk", "25", "$60.00"]],
    )
    assert result["counts"]["matched"] == len("Alpha12$40.00Beta25$60.00")
    assert result["counts"]["extra"] == 8
    assert result["recall"] == 1
    assert result["precision"] < 1
    assert result["row_alignment"][0]["cells"][-1]["reference_text"] == "$40.00"


def test_missing_row_does_not_shift_later_credit() -> None:
    result = compare_content([["Alpha", "10"], ["Missing", "20"], ["Gamma", "30"]], [["Alpha", "10"], ["Gamma", "30"]])
    assert [(r["reference_row"], r["prediction_row"]) for r in result["row_alignment"]] == [(0, 0), (1, None), (2, 1)]
    assert result["counts"]["matched"] == len("Alpha10Gamma30")
    assert result["counts"]["missing"] > 0
    assert result["row_sequence_preserved"] is False


@pytest.mark.parametrize(
    ("reference", "prediction"),
    [
        ([["A", "10"], ["B", "20"]], [["A", "20"], ["B", "10"]]),
        ([["Alpha", "Beta"]], [["Beta", "Alpha"]]),
        ([["1 23"]], [["12 3"]]),
        ([["$1.20", "2026-10-11"]], [["$120", "2026-11-10"]]),
        ([["1", "23"]], [["12", "3"]]),
    ],
)
def test_wrong_row_permutations_numeric_and_date_boundaries_not_complete(reference: list, prediction: list) -> None:
    result = compare_content(reference, prediction)
    assert result["supported"]
    assert result["content_recovered_with_row_order"] is False
    assert result["counts"]["substituted"] + result["counts"]["missing"] + result["counts"]["extra"] > 0


def test_duplicate_blank_rows_and_blank_columns_have_explicit_structural_diagnostics() -> None:
    rows = compare_content([["A"], [""], ["B"]], [["A"], [""], [""], ["B"]])
    assert rows["counts"]["missing"] == rows["counts"]["extra"] == 0
    assert rows["content_recovered_with_row_order"] is False
    assert rows["blank_rows_preserved"] is False
    columns = compare_content([["A", "B"]], [["A", "", "B"]])
    assert columns["precision"] == columns["recall"] == 1
    assert columns["schema_correctness"] is None
    assert columns["blank_cell_gap_count"] > 0


def test_nfc_and_wrapping_normalized_without_case_or_punctuation_erasure() -> None:
    exact = compare_content([["Café\nNorth"]], [["Cafe\u0301  North"]])
    assert exact["content_recovered_with_row_order"]
    wrong = compare_content([["Café, North"]], [["café North"]])
    assert not wrong["content_recovered_with_row_order"]


def test_canonical_schema_merges_and_resource_refusals_are_not_quality_zero() -> None:
    table = {
        "row_count": 1,
        "col_count": 2,
        "values": [["A", "B"]],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}],
    }
    assert compare_content(table, table)["supported"]
    merged = {**table, "values": [["A", None]], "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}]}
    result = compare_content(merged, table)
    assert result["supported"] is False
    assert "Merged" in result["unsupported_reason"]
    assert result["input_coverage"]["reference"]["declared_slots"] == 2
    assert result["input_coverage"]["reference"]["non_unit_span_records"] == 1
    assert result["precision"] is result["recall"] is result["counts"] is None
    over = compare_content([["X" * (LIMITS["cell_characters"] + 1)]], [["X"]])
    assert over["supported"] is False
    assert over["edit_work"] == 0


def test_inconsistent_column_splits_cannot_change_shared_mapping_per_row() -> None:
    result = compare_content(
        [["First Last", "Score"], ["Alpha Beta", "10"], ["Gamma Delta", "20"]],
        [["First", "Last", "Score"], ["Alpha", "Beta", "10"], ["Gamma Delta", "20", ""]],
    )
    assert result["content_recovered_with_row_order"] is False
    assert len(result["shared_column_path"]) >= 2


def test_duplicates_do_not_earn_free_reuse_and_edit_budget_refuses_whole_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    duplicated = compare_content([["same"], ["same"]], [["same"]])
    assert duplicated["counts"]["matched"] == 4
    assert duplicated["counts"]["missing"] == 4
    assert duplicated["recall"] == 0.5
    monkeypatch.setitem(LIMITS, "edit_work", 10)
    refused = compare_content([["long literal"]], [["long literal"]])
    assert not refused["supported"]
    assert refused["counts"] is refused["precision"] is refused["recall"] is None
    assert "edit-work" in refused["unsupported_reason"]


def _assert_swap(reference: list, prediction: list) -> None:
    forward = compare_content(reference, prediction)
    reverse = compare_content(prediction, reference)
    assert forward["version"] == reverse["version"] == "p003-content-alignment-v2"
    assert forward["supported"] == reverse["supported"]
    assert forward["edit_work"] == reverse["edit_work"]
    assert forward["counts"]["matched"] == reverse["counts"]["matched"]
    assert forward["counts"]["substituted"] == reverse["counts"]["substituted"]
    for a, b in (
        ("missing", "extra"),
        ("extra", "missing"),
        ("reference_units", "prediction_units"),
        ("prediction_units", "reference_units"),
    ):
        assert forward["counts"][a] == reverse["counts"][b]
    assert forward["precision"] == reverse["recall"]
    assert forward["recall"] == reverse["precision"]
    assert forward["content_recovered_with_row_order"] == reverse["content_recovered_with_row_order"]
    assert forward["blank_cell_gap_count"] == reverse["blank_cell_gap_count"]
    for suffix in ("rows", "cells", "literal_characters", "join_separator_units"):
        assert forward["coverage"]["reference_" + suffix] == reverse["coverage"]["prediction_" + suffix]
        assert forward["coverage"]["prediction_" + suffix] == reverse["coverage"]["reference_" + suffix]
    assert forward["input_coverage"]["reference"] == reverse["input_coverage"]["prediction"]
    assert forward["input_coverage"]["prediction"] == reverse["input_coverage"]["reference"]
    assert len(forward["shared_column_path"]) == len(reverse["shared_column_path"])
    for a, b in zip(forward["shared_column_path"], reverse["shared_column_path"], strict=True):
        assert a["reference_columns"] == b["prediction_columns"]
        assert a["prediction_columns"] == b["reference_columns"]
    for a, b in zip(forward["row_alignment"], reverse["row_alignment"], strict=True):
        assert a["reference_row"] == b["prediction_row"]
        assert a["prediction_row"] == b["reference_row"]
        for ca, cb in zip(a["cells"], b["cells"], strict=True):
            for suffix in ("columns", "text", "units"):
                assert ca["reference_" + suffix] == cb["prediction_" + suffix]
                assert ca["prediction_" + suffix] == cb["reference_" + suffix]
            assert ca["join_provenance"]["reference_cells"] == cb["join_provenance"]["prediction_cells"]
            for wa, wb in zip(ca["character_witness"], cb["character_witness"], strict=True):
                assert wa["reference_index"] == wb["prediction_index"]
                assert wa["prediction_index"] == wb["reference_index"]
                if wa["operation"] in ("missing", "extra"):
                    assert wb["operation"] == ("extra" if wa["operation"] == "missing" else "missing")
                else:
                    assert wa["operation"] == wb["operation"]


def test_exact_review_fixture_canonical_orientation() -> None:
    a = [["BETA", "Alpha Beta"], ["20", "Alpha 20"]]
    b = [["1", "BETA"], ["ALPHA", ""], ["Alpha 20", "20 Alpha"]]
    _assert_swap(a, b)
    result = compare_content(a, b)
    assert result["counts"] == {
        "matched": 10,
        "substituted": 4,
        "missing": 10,
        "extra": 14,
        "reference_units": 24,
        "prediction_units": 28,
    }
    assert result["caller_reference_was_internal_first"] is False


def test_seeded_bounded_swap_invariance_empty_headers_gaps_unicode() -> None:
    stream = random.Random(20261011)  # noqa: S311 - reproducible bounded test fixtures
    literals = ["", "No.", "Alpha", "Beta", "1 23", "12 3", "Café", "Cafe\u0301\nNorth", "N/A", "$1.00"]
    for _ in range(80):
        columns_a, columns_b = stream.randint(1, 4), stream.randint(1, 4)
        a = [[stream.choice(literals) for _ in range(columns_a)] for _ in range(stream.randint(1, 5))]
        b = [[stream.choice(literals) for _ in range(columns_b)] for _ in range(stream.randint(1, 5))]
        _assert_swap(a, b)


def test_canonical_orientation_does_not_hide_original_merged_span() -> None:
    merged = {
        "row_count": 1,
        "col_count": 2,
        "values": [["Z", None]],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}],
    }
    for a, b in ((merged, [["A"]]), ([["A"]], merged)):
        result = compare_content(a, b)
        assert not result["supported"]
        assert result["precision"] is result["recall"] is None
        assert "Merged" in result["unsupported_reason"]
