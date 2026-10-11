"""Wrap recovery preserves literal membership, column order and bounded evidence."""

from __future__ import annotations

import pytest
from bench.p003_wrap_content import LIMITS, VERSION, compare_wrap_content


@pytest.mark.parametrize(
    "pieces", [["Deferred revenue", "contract adjustments"], ["Deferred", "revenue contract", "adjustments"]]
)
def test_exact_two_and_three_line_wrap(pieces: list[str]) -> None:
    reference = [["Deferred revenue contract adjustments", "340"]]
    prediction = [[piece, "340" if i == 0 else ""] for i, piece in enumerate(pieces)]
    result = compare_wrap_content(reference, prediction)
    assert result["version"] == VERSION
    assert result["supported"]
    assert result["content_recovered_with_row_order"]
    assert result["precision"] == result["recall"] == 1
    assert result["row_alignment"][0]["prediction_rows"] == list(range(len(pieces)))
    assert result["row_alignment"][0]["kind"] == "wrap"
    assert result["coverage"]["prediction_join_separator_units"] == len(pieces) - 1
    assert result["schema_correctness"] is None


@pytest.mark.parametrize(
    "prediction",
    [
        [["Deferred revenue", "341"], ["contract adjustments", ""]],
        [["Deferred revenue", "340"], ["contract adjustments", "340"]],
        [["Deferred revenue", "340"]],
        [["Deferred revenue", "340"], ["contract adjustments", ""], ["contract adjustments", ""]],
    ],
)
def test_wrong_amount_missing_and_duplicate_are_not_complete(prediction: list[list[str]]) -> None:
    result = compare_wrap_content([["Deferred revenue contract adjustments", "340"]], prediction)
    assert result["supported"]
    assert not result["content_recovered_with_row_order"]
    assert sum(result["counts"][key] for key in ("missing", "extra", "substituted")) > 0


def test_swaps_and_missing_rows_keep_order() -> None:
    ref = [["Alpha", "10"], ["Beta", "20"], ["Gamma", "30"]]
    for prediction in ([ref[1], ref[0], ref[2]], [ref[0], ref[2]], [["Alpha", "20"], ["Beta", "10"], ref[2]]):
        result = compare_wrap_content(ref, prediction)
        assert result["supported"]
        assert not result["content_recovered_with_row_order"]


def test_blank_padding_has_original_maps_and_inventory() -> None:
    result = compare_wrap_content([["", "", ""], ["", "Alpha", "10"], ["", "", ""]], [["Alpha", "10", ""]])
    assert result["content_recovered_with_row_order"]
    assert result["coordinate_maps"]["reference"] == {"row_map": [1], "column_map": [1, 2]}
    assert result["blank_inventory"]["reference"]["rows"] == [0, 2]
    cell = result["row_alignment"][0]["cells"][0]
    assert result["row_alignment"][0]["reference_rows"] == [1]
    assert cell["reference_columns"] == [1]
    assert cell["prediction_columns"] == [0]


def test_all_blank_is_vacuous_content_recovery() -> None:
    result = compare_wrap_content([["", ""], ["", ""]], [[""]])
    assert result["supported"]
    assert result["content_recovered_with_row_order"]
    assert result["precision"] == result["recall"] == 1
    assert result["row_alignment"] == []
    assert result["counts"]["reference_units"] == 0
    assert result["blank_inventory"]["reference"]["cells"] == [[0, 0], [0, 1], [1, 0], [1, 1]]


def test_repeated_anchors_are_block_local() -> None:
    ref = [["Alpha beta", "10"], ["Gamma delta", "10"]]
    pred = [["Alpha", "10"], ["beta", ""], ["Gamma", "10"], ["delta", ""]]
    result = compare_wrap_content(ref, pred)
    assert result["content_recovered_with_row_order"]
    assert [row["kind"] for row in result["row_alignment"]] == ["wrap", "wrap"]


@pytest.mark.parametrize(
    ("ref", "pred"),
    [
        ([["Alpha beta", "10"]], [["Alpha", "10"], ["beta", ""]]),
        ([["Alpha", "10"], ["missing", "20"]], [["Alpha", "11"]]),
        ([["", "Alpha", "10"]], [["Alpha", "10"], ["", ""]]),
    ],
)
def test_canonical_orientation_symmetry_and_conservation(ref: list, pred: list) -> None:
    forward, reverse = compare_wrap_content(ref, pred), compare_wrap_content(pred, ref)
    assert forward["supported"] == reverse["supported"]
    assert forward["precision"] == reverse["recall"]
    assert forward["recall"] == reverse["precision"]
    counts = forward["counts"]
    assert counts["matched"] + counts["substituted"] + counts["missing"] == counts["reference_units"]
    assert counts["matched"] + counts["substituted"] + counts["extra"] == counts["prediction_units"]
    for side in ("reference", "prediction"):
        consumed = [index for row in forward["row_alignment"] for index in row[side + "_rows"]]
        assert consumed == forward["coordinate_maps"][side]["row_map"]


def test_no_many_to_many_pooling_or_over_limit_wrap() -> None:
    assert not compare_wrap_content([["Alpha beta", "10"], ["gamma", ""]], [["Alpha", "10"], ["beta gamma", ""]])[
        "content_recovered_with_row_order"
    ]
    assert not compare_wrap_content(
        [["one two three four", "10"]], [["one", "10"], ["two", ""], ["three", ""], ["four", ""]]
    )["content_recovered_with_row_order"]
    assert not compare_wrap_content([["Alpha beta"]], [["Alpha"], ["beta"]])["content_recovered_with_row_order"]


def test_schema_and_resources_refuse_with_null_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    unequal = compare_wrap_content([["Alpha", "10"]], [["Alpha 10"]])
    assert not unequal["supported"]
    assert "column" in unequal["unsupported_reason"]
    over = compare_wrap_content([["X" * (LIMITS["cell_characters"] + 1)]], [["X"]])
    assert not over["supported"]
    monkeypatch.setitem(LIMITS, "edit_work", 1)
    refusal = compare_wrap_content([["Alpha", "10"]], [["Alpha", "10"]])
    assert not refusal["supported"]
    assert "work" in refusal["unsupported_reason"]
    assert refusal["precision"] is refusal["recall"] is refusal["counts"] is None
    assert refusal["row_alignment"] is None


@pytest.mark.parametrize("reverse", [False, True])
def test_blank_spacer_is_content_padding_with_explicit_wrap_witness(*, reverse: bool) -> None:
    reference = [["Deferred tail", "340"]]
    prediction = [["Deferred", "340"], ["", ""], ["tail", ""]]
    result = compare_wrap_content(prediction, reference) if reverse else compare_wrap_content(reference, prediction)
    side = "reference" if reverse else "prediction"
    assert result["content_recovered_with_row_order"]
    assert result["precision"] == result["recall"] == 1
    assert result["coordinate_maps"][side]["row_map"] == [0, 2]
    assert result["blank_inventory"][side]["rows"] == [1]
    assert result["row_alignment"][0][side + "_rows"] == [0, 2]
    assert result["row_alignment"][0]["crossed_blank_rows"][side] == [1]
