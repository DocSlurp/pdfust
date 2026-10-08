from __future__ import annotations

from typing import Any

import pytest
from bench.decision_choice import OPTIONS, choice_request, parse_choice
from bench.decision_hosted import JEV


def response(probabilities: dict[str, Any], choice: str = "supported") -> dict[str, Any]:
    return {
        "answers": {"q0": {"type": "choice", "choice": choice, "probabilities": probabilities, "confidence": 0.123}}
    }


def test_request_uses_explicit_questions_and_resolved_source_evidence() -> None:
    cases = [
        {
            "question": "Does the proposed value belong to the label?",
            "gold": True,
            "split": "test",
            "state": {
                "task": "assignment",
                "words": [{"id": 0, "text": "USD"}, {"id": 1, "text": "120 USD"}],
                "candidate": {"label": [0], "value": [1], "alternatives": [[1]]},
            },
        }
    ]
    body = choice_request(cases)
    assert body["model"] == JEV
    assert set(body["questions"]) == {"q0"}
    question = body["questions"]["q0"]
    assert question["type"] == "choice"
    assert set(question["criteria"]) == set(OPTIONS)
    assert "observations.q0" in question["instructions"]
    assert cases[0]["question"] in question["instructions"]
    observation = body["state"]["observations"]["q0"]
    assert observation["data"]["candidate"]["value"] == {"source_ids": [1], "text": "120 USD"}
    assert set(observation) == {"question", "data"}


def test_conditional_projection_preserves_distribution_and_raw_provenance() -> None:
    distribution = {"supported": 0.6, "contradicted": 0.2, "insufficient": 0.2}
    parsed = parse_choice(response(distribution), 1)[0]
    assert parsed["p_yes"] == pytest.approx(0.75)
    assert parsed["p_answerable"] == pytest.approx(0.8)
    assert parsed["probabilities"] == distribution
    assert parsed["raw_probabilities"] == distribution
    assert parsed["choice"] == "supported"
    assert parsed["raw_confidence"] == 0.123


def test_all_insufficient_defaults_conditional_yes_to_half() -> None:
    parsed = parse_choice(response({"supported": 0, "contradicted": 0, "insufficient": 1}, "insufficient"), 1)
    assert parsed[0]["p_yes"] == 0.5
    assert parsed[0]["p_answerable"] == 0


@pytest.mark.parametrize("chosen", ["supported", "contradicted"])
def test_argmax_ties_are_allowed(chosen: str) -> None:
    parse_choice(response({"supported": 0.5, "contradicted": 0.5, "insufficient": 0}, chosen), 1)


@pytest.mark.parametrize("value", [True, -0.1, 1.1, "0.6", float("nan"), float("inf")])
def test_invalid_probabilities_are_rejected(value: object) -> None:
    with pytest.raises(ValueError, match="finite number"):
        parse_choice(response({"supported": value, "contradicted": 0.2, "insufficient": 0.2}), 1)


@pytest.mark.parametrize(
    "distribution",
    [
        {"supported": 0.6, "contradicted": 0.2},
        {"supported": 0.6, "contradicted": 0.2, "insufficient": 0.2, "extra": 0},
    ],
)
def test_option_keys_must_match_exactly(distribution: dict[str, float]) -> None:
    with pytest.raises(ValueError, match="exactly"):
        parse_choice(response(distribution), 1)


@pytest.mark.parametrize("mass", [0.17, 0.23])
def test_distributions_outside_sum_tolerance_are_rejected(mass: float) -> None:
    with pytest.raises(ValueError, match="sum to one"):
        parse_choice(response({"supported": 0.6, "contradicted": 0.2, "insufficient": mass}), 1)


def test_distribution_rounding_within_tolerance_is_accepted() -> None:
    parse_choice(response({"supported": 0.6, "contradicted": 0.2, "insufficient": 0.1999999}), 1)


def test_admitted_rounding_is_normalized_without_losing_original_scores() -> None:
    distribution = {"supported": 0.7, "contradicted": 0.3000001, "insufficient": 0}
    parsed = parse_choice(response(distribution), 1)[0]
    assert parsed["raw_probabilities"] == distribution
    assert sum(parsed["probabilities"].values()) == pytest.approx(1)
    assert 0 <= parsed["p_answerable"] <= 1
    assert parsed["p_yes"] == pytest.approx(0.7 / 1.0000001)


@pytest.mark.parametrize("insufficient", [0.05, 0.07])
def test_provider_two_decimal_rounding_is_admitted(insufficient: float) -> None:
    distribution = {"supported": 0.81, "contradicted": 0.13, "insufficient": insufficient}
    parsed = parse_choice(response(distribution), 1)[0]
    total = sum(distribution.values())
    assert parsed["raw_probabilities"] == distribution
    assert parsed["normalization_delta"] == pytest.approx(total - 1)
    assert sum(parsed["probabilities"].values()) == pytest.approx(1)
    assert parsed["p_answerable"] == pytest.approx(0.94 / total)
    assert parsed["p_yes"] == pytest.approx(0.81 / 0.94)


@pytest.mark.parametrize("chosen", ["contradicted", "invented"])
def test_non_argmax_or_unknown_choice_is_rejected(chosen: str) -> None:
    with pytest.raises(ValueError, match="maximum"):
        parse_choice(response({"supported": 0.6, "contradicted": 0.2, "insufficient": 0.2}, chosen), 1)


def test_missing_extra_or_wrong_type_answers_are_rejected() -> None:
    valid = response({"supported": 0.6, "contradicted": 0.2, "insufficient": 0.2})
    with pytest.raises(ValueError, match="keys"):
        parse_choice(valid, 2)
    with pytest.raises(ValueError, match="keys"):
        parse_choice(valid, 0)
    valid["answers"]["q0"]["type"] = "noul"
    with pytest.raises(ValueError, match="exactly"):
        parse_choice(valid, 1)


@pytest.mark.parametrize("answers", [None, [], 1, "invalid", {"q0": None}, {"q0": []}, {"q0": 1}])
def test_malformed_answer_shapes_raise_validation_error(answers: object) -> None:
    with pytest.raises(ValueError, match="choice response"):
        parse_choice({"answers": answers}, 1)


@pytest.mark.parametrize("probabilities", [None, [], "invalid", 1])
def test_malformed_distribution_shapes_raise_validation_error(probabilities: object) -> None:
    malformed = {"answers": {"q0": {"type": "choice", "probabilities": probabilities}}}
    with pytest.raises(ValueError, match="exactly"):
        parse_choice(malformed, 1)


def test_missing_choice_raises_validation_error() -> None:
    malformed = response({"supported": 0.6, "contradicted": 0.2, "insufficient": 0.2})
    malformed["answers"]["q0"].pop("choice")
    with pytest.raises(ValueError, match="maximum"):
        parse_choice(malformed, 1)
