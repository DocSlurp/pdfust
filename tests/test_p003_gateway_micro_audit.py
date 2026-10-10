"""Exact native echo removal and source-pair diagnostic contracts."""

from copy import deepcopy
from typing import Any

import pytest
from bench import p003_gateway_answer as native
from bench import p003_gateway_micro_audit as audit


def response() -> dict[str, Any]:
    return {
        "model": "liquid/d1",
        "answers": {
            "q0": {
                "name": "q0",
                "type": "choice",
                "choice": "same",
                "probabilities": {"same": 0.5, "separate": 0.49, "unresolved": 0.0},
                "confidence": 0.71,
            }
        },
        "usage": {"input_tokens": 123},
    }


def test_exact_removal_retains_raw_mass_order_metadata_and_original() -> None:
    original = response()
    before = deepcopy(original)
    normalized = native.normalize(original, model="liquid/d1", question_ids={"q0"})
    delta = audit.name_only_delta(original, normalized, {"q0"})
    assert delta["removed_fields"] == ["answers.q0.name"]
    assert original == before
    expected = deepcopy(before)
    del expected["answers"]["q0"]["name"]
    assert normalized == expected
    assert list(normalized["answers"]["q0"]["probabilities"]) == ["same", "separate", "unresolved"]
    assert normalized["usage"] == before["usage"]
    normalized["usage"]["input_tokens"] = 999
    assert original["usage"]["input_tokens"] == 123


@pytest.mark.parametrize("mutation", ["wrong_model", "wrong_echo", "missing_echo", "extra_question"])
def test_reject_nonexact_identity(mutation: str) -> None:
    raw = response()
    if mutation == "wrong_model":
        raw["model"] = "another/model"
    elif mutation == "wrong_echo":
        raw["answers"]["q0"]["name"] = "q1"
    elif mutation == "missing_echo":
        del raw["answers"]["q0"]["name"]
    else:
        raw["answers"]["q1"] = deepcopy(raw["answers"]["q0"])
    with pytest.raises(ValueError, match="Native Gateway"):
        native.normalize(raw, model="liquid/d1", question_ids={"q0"})


def test_other_extra_fields_are_not_repaired_and_altered_probabilities_rejected() -> None:
    raw = response()
    raw["answers"]["q0"]["unsupported"] = 1
    normalized = native.normalize(raw, model="liquid/d1", question_ids={"q0"})
    assert normalized["answers"]["q0"]["unsupported"] == 1
    normalized["answers"]["q0"]["probabilities"]["same"] = 0.51
    with pytest.raises(ValueError, match="beyond"):
        audit.name_only_delta(raw, normalized, {"q0"})


def row(choice: str = "same", *, receipt: bool = True) -> dict[str, Any]:
    result = {
        "page_id": "p1",
        "pair_id": "q1",
        "kind": "cell",
        "source_ids": ["w0", "w1"],
        "offline_status": "valid_nonabstaining" if receipt else "transport_error",
    }
    if receipt:
        result["receipt"] = {
            "decision": {"choice": choice, "raw_probabilities": {choice: 0.6, "other": 0.39, "unresolved": 0.0}}
        }
    return result


def test_pairs_keep_failed_denominator_and_do_not_renormalize() -> None:
    result = audit.paired([row()], [row("separate")])
    assert result["choice_disagreement_count"] == 1
    assert result["rows"][0]["micro"]["raw_mass"] == pytest.approx(0.99)
    assert result["rows"][0]["micro"]["chosen_minus_runner_up"] == pytest.approx(0.21)
    failed = audit.paired([row()], [row(receipt=False)])
    assert failed["intended_pair_count"] == 1
    assert failed["valid_pair_count"] == 0
    assert failed["unpaired_or_failed_count"] == 1


def test_pair_identity_duplicates_and_ties() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        audit.paired([row(), row()], [row(), row()])
    other = row()
    other["source_ids"] = ["w1", "w0"]
    with pytest.raises(ValueError, match="inventories"):
        audit.paired([row()], [other])
    margin = audit.margins({"choice": "same", "raw_probabilities": {"same": 0.5, "separate": 0.5}})
    assert margin["argmax_tie"]
    assert margin["chosen_minus_runner_up"] == 0
