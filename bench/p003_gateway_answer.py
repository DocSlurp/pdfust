"""Normalize the native Gateway question-name echo without changing a decision."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def normalize(result: dict[str, Any], *, model: str, question_ids: set[str]) -> dict[str, Any]:
    """Remove only an exact native d1 name echo; retain all decision values."""
    if model != "liquid/d1" or result.get("model") != model:
        message = "Native Gateway normalization requires the exact requested d1 model"
        raise ValueError(message)
    answers = result.get("answers")
    if not isinstance(answers, dict) or set(answers) != question_ids:
        message = "Native Gateway answer identities differ from the frozen request"
        raise ValueError(message)
    normalized = deepcopy(result)
    for identifier, answer in normalized["answers"].items():
        if not isinstance(answer, dict) or answer.get("name") != identifier:
            message = "Native Gateway name must exactly echo its enclosing question identifier"
            raise ValueError(message)
        del answer["name"]
    return normalized
