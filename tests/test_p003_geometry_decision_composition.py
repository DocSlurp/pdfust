"""Composition decisions depend only on fixed same-model/vector outcomes."""

from __future__ import annotations

from copy import deepcopy

import pytest
from bench.p003_geometry_decision_composition import POLICIES, compose


def fixtures(vchoice: str, mchoice: str) -> tuple[dict, dict]:
    vector = {
        "id": "opaque",
        "kind": "cell",
        "treatment": "direct_vector",
        "choice": vchoice,
        "status": "abstained" if vchoice == "unresolved" else "classified",
    }
    model = {
        "id": "opaque",
        "kind": "cell",
        "status": "valid_abstention" if mchoice == "unresolved" else "valid_nonabstaining",
        "receipt": {"choice": mchoice, "raw_probabilities": [{"choice": mchoice, "probability": 1.0}]},
        "original_status": "malformed_response",
        "response_sha256": "a" * 64,
    }
    return vector, model


@pytest.mark.parametrize(
    ("v", "m", "choices"),
    [
        ("same", "same", ("same", "same", "same")),
        ("same", "separate", ("same", "unresolved", "unresolved")),
        ("unresolved", "separate", ("separate", "unresolved", "separate")),
        ("same", "unresolved", ("same", "unresolved", "same")),
        ("unresolved", "unresolved", ("unresolved", "unresolved", "unresolved")),
    ],
)
def test_all_three_fixed_policies(v: str, m: str, choices: tuple) -> None:
    vector, model = fixtures(v, m)
    before = deepcopy((vector, model))
    for policy, choice in zip(POLICIES, choices, strict=True):
        result = compose(vector, model, policy)
        assert result["choice"] == choice
        assert result["decisive_conflict"] == (v != "unresolved" and m not in ("unresolved", v))
        assert result["raw_model_receipt"] == model["receipt"]
        assert result["probability"] is None
        assert result["original_model_status"] == "malformed_response"
    assert (vector, model) == before


def test_errors_preserved_and_vector_first_does_not_replace_vector_failure() -> None:
    vector, model = fixtures("unresolved", "same")
    vector["status"] = "source_refused"
    result = compose(vector, model, "vector_first")
    assert result["choice"] == "unresolved"
    assert result["component_error"]
    either = compose(vector, model, "either_evidence_conflicts_abstain")
    assert either["choice"] == "same"
    assert either["component_error"]
    vector, model = fixtures("same", "unresolved")
    model["status"] = "transport_error"
    assert compose(vector, model, "vector_first")["component_error"]
    assert compose(vector, model, "agreement_only")["choice"] == "unresolved"


def test_identity_and_treatment_mismatch_refused() -> None:
    vector, model = fixtures("same", "same")
    model["id"] = "different"
    with pytest.raises(ValueError, match="identities"):
        compose(vector, model, POLICIES[0])
    model["id"] = vector["id"]
    vector["treatment"] = "bbox_physical_proxy"
    with pytest.raises(ValueError, match="direct-vector"):
        compose(vector, model, POLICIES[0])


def test_invalid_decisive_payloads_do_not_become_abstentions() -> None:
    vector, model = fixtures("same", "same")
    model["receipt"]["choice"] = "unknown"
    with pytest.raises(ValueError, match="model choice"):
        compose(vector, model, POLICIES[0])
    model["receipt"]["choice"] = "same"
    vector["choice"] = "unknown"
    with pytest.raises(ValueError, match="vector choice"):
        compose(vector, model, POLICIES[0])
