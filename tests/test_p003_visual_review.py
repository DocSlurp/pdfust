"""Pin strict diagnostic verdicts without granting credit for semantic similarity."""

import pytest
from bench.generalization_scoring import score_page
from bench.p003_visual_review import (
    column_partition_audit,
    detector_inference_size,
    differences,
    lexical_tokens,
    measured_wrap,
    verdicts,
)


def test_diagnostic_marks_preserve_span_and_exact_text_requirements() -> None:
    """Equal visible text cannot make a different merged topology green."""
    gold = {
        "row_count": 1,
        "col_count": 2,
        "values": [["A", None]],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}],
    }
    prediction = {"row_count": 1, "col_count": 2, "values": [["A", ""]], "spans": []}
    target = {"tables": [gold]}
    score = score_page(target, [prediction])
    marks = verdicts(target, [prediction], score)
    assert marks["input_tables"] == {0: "failure"}
    assert set(marks["output_cells"][0].values()) == {"failure"}


def test_diagnostic_marks_normalize_nfc_but_keep_percent_spacing_strict() -> None:
    """Typography explanations preserve the primary scorer's exact verdict."""
    gold = {"row_count": 1, "col_count": 3, "values": [["café", "10%", "O₂"]], "spans": []}
    prediction = {"row_count": 1, "col_count": 3, "values": [["cafe\u0301", "10 %", "O2"]], "spans": []}
    target = {"tables": [gold]}
    score = score_page(target, [prediction])
    marks = verdicts(target, [prediction], score)
    assert marks["output_cells"][0][0, 0, 1, 1] == "success"
    assert marks["output_cells"][0][0, 1, 1, 1] == "failure"
    assert marks["output_cells"][0][0, 2, 1, 1] == "failure"
    assert {row["reason"] for row in differences(target, [prediction], score)} == {
        "whitespace-only strict mismatch",
        "subscript-versus-baseline digit",
    }


def test_unmatched_predictions_cannot_receive_green() -> None:
    """An extra output on a negative page receives no fabricated source mask."""
    prediction = {"row_count": 1, "col_count": 1, "values": [["A"]], "spans": []}
    target = {"tables": []}
    marks = verdicts(target, [prediction], score_page(target, [prediction]))
    assert marks["input_tables"] == {}
    assert marks["output_cells"] == {0: {(0, 0, 1, 1): "failure"}}


def test_extra_prediction_diagnostics_use_only_retained_geometry() -> None:
    """An unmatched predicted region uses its actual box and remains red."""
    prediction = {"row_count": 1, "col_count": 1, "values": [["A"]], "spans": [], "bbox": [1, 2, 3, 4]}
    target = {"tables": []}
    score = score_page(target, [prediction])
    marks = verdicts(target, [prediction], score)
    assert marks["extra_prediction_boxes"] == {0: [1, 2, 3, 4]}
    assert differences(target, [prediction], score)[0]["reason"] == "extra unmatched predicted table"


def test_fixed_partition_preserves_headers_and_digit_boundaries() -> None:
    """Alternative granularity needs a single partition and cannot concatenate digits."""
    assert lexical_tokens("1 23") != lexical_tokens("12 3")
    gold = {"col_count": 3, "row_count": 2, "values": [["Rank Team", "Record", "Previous"], ["1.Hingham", "12-3", "2"]]}
    actual = {
        "col_count": 4,
        "row_count": 2,
        "values": [["Rank", "Team", "Record", "Previous"], ["1.", "Hingham", "12-3", "2"]],
    }
    audit = column_partition_audit(gold, actual)
    assert audit["verified"]
    assert audit["prediction_column_groups"] == [[0, 1], [2], [3]]
    actual["values"][0][1] = "Wrong header"
    assert not column_partition_audit(gold, actual)["verified"]


def test_numeric_output_does_not_gain_visual_digit_breaks() -> None:
    """Font-measured wrapping keeps a price intact and retains every character."""
    assert measured_wrap("540.50", 100) == ["540.50"]
    text = "A long table label with multiple words"
    assert "".join(measured_wrap(text, 100)) == text


def test_detector_caption_uses_actual_worker_configuration() -> None:
    """Missing legacy frozen fields must not conceal known worker inference size."""
    report = {"layout_detector_initialization": {"configuration": {"imgsz": 640}}}
    assert detector_inference_size({"config": {}}, report) == 640
    with pytest.raises(ValueError, match="inference sizes differ"):
        detector_inference_size({"config": {"detector_inference_size": 1024}}, report)
