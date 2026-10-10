"""Native answer metadata must never alter choices or relax decision validation."""

from copy import deepcopy
from typing import Any

import pytest
from bench.p003_gateway_answer import normalize
from bench.p003_topology_ownership import _choices


def result() -> dict[str, Any]:
    return {
        "model": "liquid/d1",
        "answers": {"q0": {"name": "q0", "type": "choice", "choice": "a", "probabilities": {"a": 0.8, "b": 0.2}}},
    }


def test_exact_echo_only_and_original_immutable() -> None:
    raw = result()
    original = deepcopy(raw)
    adjusted = normalize(raw, model="liquid/d1", question_ids={"q0"})
    assert raw == original
    assert adjusted["answers"]["q0"] == {k: v for k, v in raw["answers"]["q0"].items() if k != "name"}
    assert _choices(adjusted["answers"]["q0"], {"a": "A", "b": "B"})["choice"] == "a"


@pytest.mark.parametrize("name", [None, "q1", "Q0", 0])
def test_reject_different_echo(name: object) -> None:
    raw = result()
    raw["answers"]["q0"]["name"] = name
    with pytest.raises(ValueError, match="exactly echo"):
        normalize(raw, model="liquid/d1", question_ids={"q0"})


def test_other_extra_fields_and_invalid_probabilities_still_fail() -> None:
    for change in ({"unrecognized": True}, {"choice": "b"}, {"probabilities": {"a": 0.8}}):
        raw = result()
        raw["answers"]["q0"].update(change)
        adjusted = normalize(raw, model="liquid/d1", question_ids={"q0"})
        with pytest.raises(ValueError, match=r"Invalid typed|Probabilities must|Choice must"):
            _choices(adjusted["answers"]["q0"], {"a": "A", "b": "B"})


def test_different_model_or_question_rejected() -> None:
    with pytest.raises(ValueError, match="exact requested"):
        normalize(result(), model="another-model", question_ids={"q0"})
    with pytest.raises(ValueError, match="identities differ"):
        normalize(result(), model="liquid/d1", question_ids={"q1"})
