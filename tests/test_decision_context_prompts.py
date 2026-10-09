from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.decision_context_prompts import (
    DIAGNOSTICS,
    assembly_request,
    observed_history,
    parse_assembly,
    parse_assembly_response,
    project_assembly,
)


def evidence() -> dict[str, Any]:
    return {
        "id": "secret-fixture",
        "family": "secret-family",
        "gold": "B",
        "words": [{"id": 999, "text": "Item", "bbox": [10, 50, 40, 60], "gold": "leak"}],
        "assemblies": {
            "A": {
                "cells": [{"source_ids": [999], "gold": "leak"}],
                "records": [{"row_key_ids": [999], "value_ids": [], "header_path": []}],
                "unresolved_ids": [],
            },
            "B": {"cells": [], "unresolved_ids": [999]},
        },
        "current_region": [0, 40, 100, 70],
        "prior_rows": [{"id": 888, "text": "Prior...", "bbox": [10, 10, 30, 20], "gold": "leak"}],
        "surrounding_context": [{"id": 777, "text": "Visible note", "bbox": [10, 80, 60, 90], "gold": "leak"}],
        "native_rules": [{"type": "s", "bbox": [0, 40, 100, 40], "gold": "leak"}],
    }


def answer(choice: str = "A", probabilities: object = None) -> dict[str, Any]:
    return {
        "answers": {
            "q0": {
                "type": "choice",
                "choice": choice,
                "probabilities": probabilities
                if probabilities is not None
                else {"A": 0.7, "B": 0.2, "unresolved": 0.1},
            }
        }
    }


def test_projection_excludes_fixture_and_gold_metadata() -> None:
    projected = project_assembly(evidence())
    serialized = json.dumps(projected)
    for forbidden in ("secret", "gold", "leak", "999", "888", "777", "family"):
        assert forbidden not in serialized
    assert projected["assemblies"]["A"]["records"][0]["row_key_ids"] == ["w0"]
    assert projected["surrounding_context"][0]["text"] == "Visible note"


def test_representations_keep_identical_complete_candidates() -> None:
    projections = [project_assembly(evidence(), variant) for variant in ("raw", "summary", "both")]
    assert all(item["assemblies"] == projections[0]["assemblies"] for item in projections)
    assert "observed_history" not in projections[0]
    assert "preceding_physical_rows" not in projections[1]
    assert projections[2]["observed_history"]["ellipsis_rows"] == 1


def test_order_reversal_preserves_semantic_identity_and_response() -> None:
    normal = project_assembly(evidence())
    reversed_order = project_assembly(evidence(), reverse_candidates=True)
    assert list(reversed_order["assemblies"]) == ["B", "A"]
    assert reversed_order["assemblies"] == normal["assemblies"]
    assert parse_assembly(answer(), reverse_candidates=True)["choice"] == "A"


def test_history_only_uses_preceding_observations_and_no_labeled_wraps() -> None:
    rows: list[dict[str, Any]] = [
        {"bbox": [10, index * 10, 30, index * 10 + 8], "text": "row", "wrap": True, "gold": True} for index in range(6)
    ]
    initial = observed_history(rows, 4)
    rows[4] = {"bbox": [-999, -999, 0, 0], "text": "Future..."}
    assert observed_history(rows, 4) == initial
    assert initial["aligned_close_pairs_proxy"] == 3
    assert initial["not_established_wrap_events"] is True
    rows[3]["bbox"][0] = 50
    changed = observed_history(rows, 4)
    assert changed["last_start_delta"] == 40
    assert changed["aligned_close_pairs_proxy"] == 2


def test_future_prior_word_is_filtered_out() -> None:
    data = evidence()
    data["prior_rows"].append({"id": 666, "text": "Future", "bbox": [10, 80, 20, 90]})
    assert "Future" not in json.dumps(project_assembly(data))


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "unknown"])
def test_candidate_conservation_rejects_incomplete_or_invalid_ownership(mutation: str) -> None:
    data = evidence()
    if mutation == "duplicate":
        data["assemblies"]["A"]["unresolved_ids"] = [999]
    elif mutation == "missing":
        data["assemblies"]["A"]["cells"] = []
    else:
        data["assemblies"]["A"]["cells"][0]["source_ids"] = [123]
    with pytest.raises(ValueError, match=r".+"):
        project_assembly(data)


def test_request_is_native_alpha_choice_without_label_question() -> None:
    request = assembly_request(evidence())
    assert request["questions"]["q0"]["type"] == "choice"
    assert set(request["questions"]["q0"]["criteria"]) == {"A", "B", "unresolved"}
    assert "counts alone" in request["questions"]["q0"]["instructions"]
    assert "secret" not in json.dumps(request)


@pytest.mark.parametrize("value", [True, "0.7", -0.1, 1.1, float("nan"), float("inf")])
def test_malformed_probability_refused(value: object) -> None:
    with pytest.raises(ValueError, match=r".+"):
        parse_assembly(answer(probabilities={"A": value, "B": 0.2, "unresolved": 0.1}))


@pytest.mark.parametrize("malformed", [None, [], {"A": 1}, {"A": 1, "B": 0, "unresolved": 0, "other": 0}])
def test_distribution_shape_is_strict(malformed: object) -> None:
    response = answer()
    response["answers"]["q0"]["probabilities"] = malformed
    with pytest.raises(ValueError, match=r".+"):
        parse_assembly(response)


@pytest.mark.parametrize("chosen", ["B", "unknown", [], True])
def test_choice_requires_declared_argmax(chosen: object) -> None:
    response = answer()
    response["answers"]["q0"]["choice"] = chosen
    with pytest.raises(ValueError, match=r".+"):
        parse_assembly(response)


def test_strict_keys_and_rounding_preserved() -> None:
    parsed = parse_assembly(answer(probabilities={"A": 0.81, "B": 0.13, "unresolved": 0.05}))
    assert parsed["normalization_delta"] == pytest.approx(-0.01)
    assert sum(parsed["probabilities"].values()) == pytest.approx(1)
    malformed_responses: list[dict[str, Any]] = [
        {"answers": {}},
        {"answers": {"q0": None}},
        {"answers": {"q0": {}, "extra": {}}},
    ]
    for malformed in malformed_responses:
        with pytest.raises(ValueError, match=r".+"):
            parse_assembly(malformed)


def test_diagnostic_is_separate_strict_choice() -> None:
    request = assembly_request(evidence(), diagnostics=True)
    assert set(request["questions"]["q0"]["criteria"]) == set(DIAGNOSTICS)
    probabilities = dict.fromkeys(DIAGNOSTICS, 0.0)
    probabilities["truly_ambiguous"] = 1.0
    response = answer("truly_ambiguous", probabilities)
    assert parse_assembly_response(response, 1, diagnostics=True)[0]["diagnostic"] == "truly_ambiguous"
    malformed = deepcopy(response)
    malformed["answers"]["q0"]["type"] = "enum"
    with pytest.raises(ValueError, match=r".+"):
        parse_assembly_response(malformed, 1, diagnostics=True)


def test_payload_bound_prevents_silent_evidence_truncation() -> None:
    data = evidence()
    data["words"][0]["text"] = "x" * 40_000
    with pytest.raises(ValueError, match="request bytes"):
        assembly_request(data)
