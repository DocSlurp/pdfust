"""Independent natural-table annotation and complete-output evaluation checks."""

from copy import deepcopy
from typing import Any

import pytest
from bench.generalization_scoring import (
    audit_model_body,
    normalize_text,
    parse_annotation_html,
    score_dataset,
    score_page,
)


def table(
    values: list[list[str | None]],
    *,
    spans: list[dict[str, int]] | None = None,
    bbox: list[int] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "row_count": len(values),
        "col_count": len(values[0]),
        "values": values,
        "spans": spans or [],
    }
    if bbox is not None:
        result["bbox"] = bbox
    return result


def test_html_span_and_inline_math() -> None:
    html = (
        r'<table><tr><th rowspan="2">A &amp; B</th><td><i>x</i><sup>2</sup> + \(\alpha\)</td></tr>'
        "<tr><td></td></tr></table>"
    )
    result = parse_annotation_html(html)
    assert result["structural_scored"]
    assert result["annotation_html"] == html
    assert result["tables"][0]["values"] == [["A & B", r"x2 + \(\alpha\)"], [None, ""]]
    assert result["tables"][0]["spans"] == [{"row": 0, "column": 0, "row_span": 2, "column_span": 1}]


@pytest.mark.parametrize(
    "html",
    [
        '<table><tr><td rowspan="0">A</td></tr></table>',
        '<table><tr><td rowspan="2">A</td></tr></table>',
        "<table><tr><td>A</td><td>B</td></tr><tr><td>C</td></tr></table>",
        "<table><tr><td>A",
        "<table><tr><td><table><tr><td>A</td></tr></table></td></tr></table>",
        '<table><tr><td><img src="equation.png"></td></tr></table>',
        "<table><tr><td><b>A</td></tr></table>",
        "no table",
    ],
)
def test_invalid_annotation_abstains(html: str) -> None:
    parsed = parse_annotation_html(html)
    assert not parsed["structural_scored"]
    assert parsed["annotation_errors"]
    assert parsed["annotation_html"] == html
    assert parsed["tables"] == []


def test_colspan_and_multiple_tables() -> None:
    parsed = parse_annotation_html(
        '<table><tr><td colspan="2">A</td></tr><tr><td>B</td><td>C</td></tr></table><table><tr><td>D</td></tr></table>'
    )
    assert parsed["structural_scored"]
    assert len(parsed["tables"]) == 2
    assert parsed["tables"][0]["values"] == [["A", None], ["B", "C"]]


def test_ocr_errors_do_not_erase_structure_or_geometry() -> None:
    target = table([["Invoice", "100"]], bbox=[0, 0, 100, 20])
    prediction = table([["lnvoice", "l00"]], bbox=[0, 0, 100, 20])
    score = score_page({"tables": [target]}, [prediction])
    assert score["exact_table_spans"] == 1
    assert score["correct_structure_cells"] == 2
    assert score["geometry_iou_sum"] == 1
    assert score["text_edit_distance"] == 2
    assert score["complete_tables"] == 0


def test_row_column_error_and_missing_extra_cells() -> None:
    score = score_page({"tables": [table([["A", "B"]])]}, [table([["A"], ["B"], ["C"]])])
    assert score["exact_rows"] == score["exact_columns"] == 0
    assert score["expected_cells"] == 2
    assert score["predicted_cells"] == 3
    assert score["correct_structure_cells"] == 1
    assert score["text_edit_distance"] == 3
    assert score["penalized_cells"] == 4


def test_duplicate_tables_are_one_to_one_and_extra_charged() -> None:
    item = table([["A", "B"]])
    score = score_page({"tables": [item]}, [item, deepcopy(item)])
    assert score["complete_tables"] == 1
    assert score["false_positive_tables"] == 1
    assert score["table_denominator"] == 2
    assert score["text_edit_distance"] == 2
    assert not score["exact_page"]
    duplicate_gold = score_page({"tables": [item, deepcopy(item)]}, [item])
    assert duplicate_gold["missing_tables"] == 1


def test_geometry_pairs_tables_independently_of_text_and_order() -> None:
    a = table([["AAAA"]], bbox=[0, 0, 10, 10])
    b = table([["BBBB"]], bbox=[20, 0, 30, 10])
    pa = table([["????"]], bbox=[0, 0, 10, 10])
    pb = table([["!!!!"]], bbox=[20, 0, 30, 10])
    score = score_page({"tables": [a, b]}, [pb, pa])
    assert score["exact_table_spans"] == 2
    assert {(m["target"], m["prediction"]) for m in score["matches"]} == {(0, 1), (1, 0)}
    assert score["text_edit_distance"] == 8


def test_unrelated_multitable_matrices_do_not_match_by_shape() -> None:
    score = score_page({"tables": [table([["AAA"]]), table([["BBB"]])]}, [table([["ZZZ"]])])
    assert score["matched_tables"] == 0
    assert score["missing_tables"] == 2
    assert score["false_positive_tables"] == 1


@pytest.mark.parametrize("mutation", ["overlap", "covered_value", "orphan_none", "duplicate_anchor", "bad_type"])
def test_malformed_predictions_charge_complete_failure(mutation: str) -> None:
    t = table([["A", None], ["B", "C"]], spans=[{"row": 0, "column": 0, "row_span": 1, "column_span": 2}])
    bad = deepcopy(t)
    if mutation == "overlap":
        bad["spans"].append({"row": 0, "column": 1, "row_span": 1, "column_span": 1})
    elif mutation == "covered_value":
        bad["values"][0][1] = "hidden"
    elif mutation == "orphan_none":
        bad["spans"] = []
    elif mutation == "duplicate_anchor":
        bad["spans"] *= 2
    else:
        bad["spans"][0]["row_span"] = True
    score = score_page({"tables": [t]}, [bad])
    assert score["error"]
    assert score["malformed"]
    assert score["expected_cells"] == 3
    assert score["missing_tables"] == 1
    assert score["correct_structure_cells"] == 0


def test_missing_errors_diagnostics_negative_pages_all_retained() -> None:
    targets = {
        "pages": [
            {"id": "missing", "tables": [table([["A"]])]},
            {"id": "failed", "tables": [table([["BC"]])]},
            {"id": "negative", "tables": []},
            {"id": "diagnostic", "structural_scored": False},
        ]
    }
    result = score_dataset(
        targets,
        [
            {"id": "failed", "status": "error", "tables": [table([["BC"]])]},
            {"id": "negative", "status": "ok", "tables": [table([["extra"]])]},
        ],
    )
    totals = result["totals"]
    assert totals["pages"] == 4
    assert totals["scored_pages"] == 3
    assert totals["diagnostic_pages"] == 1
    assert totals["all_page_errors"] == 3
    assert totals["expected_cells"] == 2
    assert totals["correct_text_cells"] == 0
    assert totals["text_edit_distance"] == 8
    assert totals["table_denominator"] == 3
    assert totals["false_positive_page"] == 1


def test_text_normalization_is_conservative() -> None:
    assert normalize_text("e\u0301\u00a0 A\n B") == "é A B"
    assert normalize_text(r"\frac{1}{2}") != "1/2"
    assert normalize_text("O") != normalize_text("0")
    assert normalize_text("a-") != normalize_text("a")


def test_p001_state_adapter_and_invalid_ids() -> None:
    target = {"id": "p", "tables": [table([["A"]])]}
    assert score_dataset([target], [{"id": "p", "state": {"tables": [table([["A"]])]}}])["totals"]["exact_page"] == 1
    with pytest.raises(ValueError, match="Duplicate or unknown"):
        score_dataset([target], [{"id": "other"}])
    with pytest.raises(ValueError, match="Duplicate or unknown"):
        score_dataset([target], [{"id": "p"}, {"id": "p"}])


def test_model_body_audit_checks_nested_fields_without_text_overlap_claims() -> None:
    assert audit_model_body({"messages": [{"source_words": [{"text": "Invoice"}]}]})["explicit_reference_fields_absent"]
    audit = audit_model_body({"messages": [{"data": {"annotation_html": "private"}}]})
    assert not audit["explicit_reference_fields_absent"]
    assert audit["violations"] == ["$.messages[0].data.annotation_html"]


def test_span_error_can_preserve_text_edit_distance() -> None:
    target = table([["A", None]], spans=[{"row": 0, "column": 0, "row_span": 1, "column_span": 2}])
    prediction = table([["A", ""]])
    score = score_page({"tables": [target]}, [prediction])
    assert score["exact_table_spans"] == 0
    assert score["complete_tables"] == 0
    assert score["text_edit_distance"] == 0
    assert score["correct_text_cells"] == 1


def test_identical_text_cannot_override_disjoint_geometry() -> None:
    score = score_page(
        {"tables": [table([["A"]], bbox=[0, 0, 10, 10])]},
        [table([["A"]], bbox=[20, 0, 30, 10])],
    )
    assert score["matched_tables"] == 0
    assert score["missing_tables"] == 1
    assert score["false_positive_tables"] == 1
