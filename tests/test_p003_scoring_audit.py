"""Secondary scoring keeps full scope and cannot silently forgive changed input evidence."""

from __future__ import annotations

from pathlib import Path

import pytest
from bench.p003_report import strict_scores
from bench.p003_scoring_audit import admit, dual_scores, pinned
from bench.silver import sha


def table(values: list[list[str | None]], x: int = 0) -> dict:
    return {
        "row_count": len(values),
        "col_count": len(values[0]),
        "values": values,
        "spans": [],
        "bbox": [x, 0, x + 10, 10],
    }


def measure(reference: list[dict], prediction: list[dict], status: str = "ok") -> dict:
    targets = [{"id": "page", "tables": reference}]
    predictions = [{"id": "page", "tables": prediction, "status": status}]
    return dual_scores(targets, predictions, strict_scores(targets, predictions))


def test_alternative_granularity_preserves_strict_score_and_counts_new_acceptance() -> None:
    ref = table([["No.", "Rec."], ["1. Hingham", "6-0-0"]])
    pred = table([["No.", "", "Rec."], ["1.", "Hingham", "6-0-0"]])
    result = measure([ref], [pred])
    assert result["counts"]["strict_complete_tables"] == 0
    assert result["counts"]["strict_or_equivalent_tables"] == 1
    assert result["counts"]["different_column_equivalent_tables"] == 1
    assert result["full_content_precision"] == result["full_content_recall"] == 1
    assert result["primary_scores_changed"] is False


def test_blank_padding_content_cannot_become_schema_acceptance() -> None:
    result = measure([table([["A", "B"]])], [table([["A", "", "B"]])])
    assert result["counts"]["content_recovered_tables"] == 1
    assert result["counts"]["strict_or_equivalent_tables"] == 0


def test_missing_and_extra_tables_keep_false_positive_and_omission_penalties() -> None:
    result = measure([table([["lost"]], 0)], [table([["invented"]], 20)])
    assert result["counts"]["missing_tables"] == result["counts"]["extra_tables"] == 1
    assert result["counts"]["missing"] == 4
    assert result["counts"]["extra"] == 8
    assert result["full_content_precision"] == result["full_content_recall"] == 0


def test_error_page_keeps_all_reference_loss_and_gives_no_partial_output_credit() -> None:
    ref = table([["actual"]])
    result = measure([ref], [ref], "error")
    assert result["counts"]["error_pages"] == 1
    assert result["counts"]["missing"] == len("actual")
    assert result["full_content_recall"] == 0


def test_unsupported_merge_still_keeps_strict_acceptance_and_unknown_content_scope() -> None:
    merged = table([["Group", None]])
    merged["spans"] = [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}]
    result = measure([merged], [merged])
    assert result["counts"]["strict_complete_tables"] == 1
    assert result["counts"]["strict_or_equivalent_tables"] == 1
    assert result["counts"]["content_unsupported_pairs"] == 1
    assert result["full_content_precision"] is result["full_content_recall"] is None


def test_changed_report_refused_before_any_evaluation_or_reference_read(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text('{"results": []}')
    with pytest.raises(ValueError, match="Pinned audit artifact changed"):
        admit({"report": str(path), "report_sha256": "0" * 64})
    assert pinned(str(path), sha(path.read_bytes())) == {"results": []}


def test_diagnostic_pages_remain_counted_without_fabricated_quality() -> None:
    targets = [{"id": "diagnostic", "structural_scored": False}]
    predictions = [{"id": "diagnostic", "tables": [], "status": "ok"}]
    result = dual_scores(targets, predictions, strict_scores(targets, predictions))
    assert result["counts"]["pages"] == result["counts"]["diagnostic_pages"] == 1
    assert result["pages"] == [{"id": "diagnostic", "structural_scored": False, "error": False}]
