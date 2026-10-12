"""Authored pairing, intended ownership and candidate-completeness scoring checks."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from bench.borderless_challenge import generate_cases, score
from bench.silver import sha

import pdfust


def test_fixed_companion_cohort_and_clean_wrap_intervention() -> None:
    cases = generate_cases()
    assert len(cases) == 28
    assert len({sha(case["pdf"]) for case in cases}) == 28
    assert sum(case["target"]["kind"] == "borderless" for case in cases) == 12
    assert sum(case["target"]["kind"] == "prose" for case in cases) == 12
    assert sum(case["target"]["kind"] == "ruled-control" for case in cases) == 4
    for setting in range(6):
        paired = [
            case for case in cases if case["target"]["kind"] == "borderless" and case["target"]["setting"] == setting
        ]
        assert paired[0]["target"]["tables"] == paired[1]["target"]["tables"]
        assert not paired[0]["target"]["wrap"]
        assert paired[1]["target"]["wrap"]
        assert paired[0]["pdf"] != paired[1]["pdf"]


def test_visible_text_has_no_fixture_class_or_scoring_labels() -> None:
    for case in generate_cases():
        with pdfust.open(stream=case["pdf"]) as document:
            text = document[0].get_text().lower()
        assert "quarterly observations" in text
        assert not any(label in text for label in ("borderless", "prose", "control", "target", "case-"))


def example() -> tuple[dict[str, Any], dict[str, Any]]:
    target = generate_cases()[0]["target"]
    return target, deepcopy(target["tables"][0])


def test_exact_cells_ownership_and_whitespace_only_normalization() -> None:
    target, table = example()
    table["values"][1][0] = "North\ndepot"
    result = score(target, [table])
    assert result["exact_page"]
    assert result["exact_spans"]
    assert result["owned_values"] == 12
    assert result["owned_words"] == 15


def test_wrong_row_or_column_ownership_fails_even_with_complete_words() -> None:
    target, table = example()
    table["values"][1][1], table["values"][2][1] = table["values"][2][1], table["values"][1][1]
    result = score(target, [table])
    assert not result["exact_cells"]
    assert result["owned_values"] == 10
    assert result["owned_words"] == 13
    assert result["exact_spans"]


def test_duplicate_candidate_invalidates_unique_ownership() -> None:
    target, table = example()
    result = score(target, [table, deepcopy(table)])
    assert not result["exact_page"]
    assert result["owned_values"] == 0
    assert result["owned_words"] == 0


def test_shape_mismatch_and_missing_wrap_line_fail_exactness() -> None:
    target, table = example()
    table["values"][1][0] = "North"
    assert not score(target, [table])["exact_cells"]
    assert score(target, [table])["owned_words"] == 14
    table["row_count"] = 5
    assert score(target, [table])["owned_words"] == 0


def test_merged_control_requires_span_and_covered_none_slot() -> None:
    target = generate_cases()[-1]["target"]
    table = deepcopy(target["tables"][0])
    assert score(target, [table])["exact_page"]
    table["spans"][0]["column_span"] = 1
    assert score(target, [table])["exact_cells"]
    assert not score(target, [table])["exact_spans"]
    table["values"][0][1] = ""
    assert not score(target, [table])["exact_cells"]


def test_numeric_prose_reference_targets_zero_tables() -> None:
    target = generate_cases()[1]["target"]
    assert score(target, [])["exact_page"]
    _, table = example()
    assert score(target, [table])["false_positive_page"]
