"""Independent adversarial checks for the bounded content-only wrap diagnostic."""

from __future__ import annotations

import pytest
from bench.p003_wrap_content import compare_wrap_content


def _assert_conserved(result: dict) -> None:
    assert result["supported"], result.get("unsupported_reason")
    counts = result["counts"]
    assert counts["matched"] + counts["substituted"] + counts["missing"] == counts["reference_units"]
    assert counts["matched"] + counts["substituted"] + counts["extra"] == counts["prediction_units"]
    assert 0 <= result["precision"] <= 1
    assert 0 <= result["recall"] <= 1


def _assert_symmetric(reference: list[list[str]], prediction: list[list[str]]) -> dict:
    forward = compare_wrap_content(reference, prediction)
    reverse = compare_wrap_content(prediction, reference)
    _assert_conserved(forward)
    _assert_conserved(reverse)
    left, right = forward["counts"], reverse["counts"]
    for key in ("matched", "substituted"):
        assert left[key] == right[key]
    assert left["missing"] == right["extra"]
    assert left["extra"] == right["missing"]
    assert left["reference_units"] == right["prediction_units"]
    assert left["prediction_units"] == right["reference_units"]
    assert forward["precision"] == reverse["recall"]
    assert forward["recall"] == reverse["precision"]
    assert forward["content_recovered_with_row_order"] == reverse["content_recovered_with_row_order"]
    return forward


def test_three_row_exact_wrap_has_single_unrepeated_anchor() -> None:
    reference = [["Blue long coat", "42.00"]]
    prediction = [["Blue", "42.00"], ["long", ""], ["coat", ""]]
    result = _assert_symmetric(reference, prediction)
    assert result["content_recovered_with_row_order"]
    assert result["counts"]["matched"] == len("Blue long coat") + len("42.00")


@pytest.mark.parametrize(
    "prediction",
    [
        [["Blue", "42.00"], ["long", "42.00"], ["coat", ""]],
        [["Blue", "42.00"], ["coat", ""]],
        [["Blue", "42.00"], ["long", ""], ["long coat", ""]],
        [["Blue", ""], ["long", "42.00"], ["coat", "42.00"]],
        [["Blue long coat", "42.00"], ["Blue long coat", "42.00"]],
    ],
)
def test_duplicate_or_missing_fragments_are_not_recovered(prediction: list[list[str]]) -> None:
    result = _assert_symmetric([["Blue long coat", "42.00"]], prediction)
    assert not result["content_recovered_with_row_order"]
    assert sum(result["counts"][key] for key in ("substituted", "missing", "extra")) > 0


def test_swapped_amounts_cannot_be_borrowed_from_neighboring_rows() -> None:
    reference = [["Blue long coat", "42.00"], ["Red warm coat", "84.00"]]
    prediction = [["Blue", "84.00"], ["long coat", ""], ["Red", "42.00"], ["warm coat", ""]]
    assert not _assert_symmetric(reference, prediction)["content_recovered_with_row_order"]


def test_blank_padding_axes_are_content_only() -> None:
    reference = [["Blue coat", "42.00"], ["Red coat", "84.00"]]
    prediction = [["", "", ""], ["Blue coat", "", "42.00"], ["", "", ""], ["Red coat", "", "84.00"]]
    result = _assert_symmetric(reference, prediction)
    assert result["content_recovered_with_row_order"]
    assert result["schema_correctness"] is None


@pytest.mark.parametrize(
    ("reference", "prediction"),
    [
        ([["A", "$1 000"]], [["A", "$1000"]]),
        ([["A", "1.00"]], [["A", "100"]]),
        ([["Coat", "42"]], [["coat", "42"]]),
        ([["Ａ", "42"]], [["A", "42"]]),
    ],
)
def test_content_normalization_preserves_numeric_case_and_compatibility_distinctions(
    reference: list[list[str]], prediction: list[list[str]]
) -> None:
    assert not _assert_symmetric(reference, prediction)["content_recovered_with_row_order"]


def test_content_normalization_accepts_only_nfc_and_whitespace_equivalence() -> None:
    assert _assert_symmetric([["Cafe\u0301 coat", "42"]], [["Café\tcoat", "42"]])["content_recovered_with_row_order"]


def test_split_columns_without_any_singleton_anchor_cannot_join() -> None:
    reference = [["Blue coat", "Warm lining"]]
    prediction = [["Blue", "Warm"], ["coat", "lining"]]
    assert not _assert_symmetric(reference, prediction)["content_recovered_with_row_order"]


def test_exact_text_in_swapped_columns_is_not_complete() -> None:
    reference = [["Blue long coat", "42.00"]]
    prediction = [["42.00", "Blue"], ["", "long coat"]]
    assert not _assert_symmetric(reference, prediction)["content_recovered_with_row_order"]
