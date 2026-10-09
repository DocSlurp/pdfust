"""CPU-only DEV source conservation and evidence-recovery checks."""

from copy import deepcopy
from typing import Any

import pytest
from bench.decision_context_cases import context_cases, evidence_modes, native_choice
from bench.decision_records import materialize, score_records, validate_assembly


@pytest.fixture(scope="module")
def cases() -> list[dict[str, Any]]:
    return context_cases()


def test_balance_and_observable_native_oracle(cases: list[dict[str, Any]]) -> None:
    assert len(cases) == 30
    assert len({case["id"] for case in cases}) == 30
    for case in cases:
        for choice in ("A", "B", "unresolved"):
            result = materialize(case, choice)
            assert score_records(case, result)["source_conservation"]
        assert score_records(case, materialize(case, case["gold"]["choice"]))["region_exact"]
        assert native_choice(case) == case["gold"]["choice"]
        for mode in ("current", "prior", "context", "native"):
            expected = case["gold"]["mode_choices"][mode]
            assert native_choice(case, mode) == expected
            assert score_records(case, materialize(case, expected), mode)["region_exact"]


def test_paired_text_geometry_and_distinct_native_facts(cases: list[dict[str, Any]]) -> None:
    for offset in (0, 10, 20):
        for first in (0, 2):
            left, right = cases[offset + first : offset + first + 2]
            assert left["evidence"]["words"] == right["evidence"]["words"]
            assert left["evidence"]["assemblies"] == right["evidence"]["assemblies"]
            assert left["pdf_bytes"] != right["pdf_bytes"]
            assert evidence_modes(left, "current") == evidence_modes(right, "current")
            assert evidence_modes(left, "native") != evidence_modes(right, "native")


def test_modes_do_not_leak_gold_or_hidden_cue(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        evidence = evidence_modes(case, "current")
        assert "gold" not in evidence
        assert "observable" not in evidence
        assert not evidence["native_rules"]
        assert not evidence["native_fills"]
        assert not evidence["prior_rows"]
        assert not evidence["prior_row_drawings"]
        assert not evidence["surrounding_context"]
        assert case["gold"]["mode_choices"]["current"] == "unresolved"


def test_exact_records_and_cell_ownership_reject_wrong_assembly(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        if case["gold"]["choice"] == "unresolved":
            continue
        wrong = "B" if case["gold"]["choice"] == "A" else "A"
        score = score_records(case, materialize(case, wrong))
        assert not score["region_exact"]
        assert score["record_f1"] < 1


def test_invalid_omission_duplicate_and_unknown_ids(cases: list[dict[str, Any]]) -> None:
    case = cases[0]
    original = materialize(case, "A")
    for mutation in ("omit", "duplicate", "unknown", "record_unknown"):
        result = deepcopy(original)
        if mutation == "omit":
            result["cells"][0]["source_ids"].pop()
        elif mutation == "duplicate":
            result["unresolved_ids"].append(case["evidence"]["words"][0]["id"])
        elif mutation == "unknown":
            result["unresolved_ids"].append(999999)
        else:
            result["records"][0]["value_ids"].append(999999)
        with pytest.raises(ValueError, match=r"Source ownership|Unknown record source"):
            validate_assembly(case, result)
        assert not score_records(case, result)["valid"]


@pytest.mark.parametrize(
    "mutation", ["cell_text", "record_text", "nan", "record_duplicate", "cell_ref", "source_duplicate"]
)
def test_materialized_mutations_are_invalid(cases: list[dict[str, Any]], mutation: str) -> None:
    case = cases[0]
    result = materialize(case, "A")
    if mutation == "cell_text":
        result["cells"][0]["text"] = "fabricated"
    elif mutation == "record_text":
        result["records"][0]["value"] = "fabricated"
    elif mutation == "nan":
        result["cells"][0]["bbox"][0] = float("nan")
    elif mutation == "record_duplicate":
        result["records"].append(deepcopy(result["records"][0]))
    elif mutation == "cell_ref":
        result["records"][0]["cell_ids"] = ["description_header"]
    else:
        result["records"][0]["value_ids"] *= 2
    assert not score_records(case, result)["valid"]


def test_native_geometry_rule_is_translation_scale_invariant(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        shifted = deepcopy(case)
        for word in shifted["evidence"]["words"]:
            word["bbox"] = [value * 1.7 + 43 for value in word["bbox"]]
        for key in ("native_rules", "native_fills"):
            for drawing in shifted["evidence"][key]:
                drawing["bbox"] = [value * 1.7 + 43 for value in drawing["bbox"]]
        assert native_choice(shifted) == native_choice(case)
