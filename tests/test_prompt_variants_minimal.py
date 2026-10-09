"""Check that generic prompt alternatives preserve every frozen source field."""

from __future__ import annotations

from copy import deepcopy

import pytest
from bench.prompt_variants_minimal import transform, variants


def body() -> dict:
    return {
        "model": "admitted-model",
        "state": ["literal source", {"type": "image_url", "image_url": {"url": "opaque pixels"}}],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "original generic task",
                "criteria": {"rolling": "retained candidate", "not_table": "prose", "unresolved": "unknown"},
            },
            "q1": {"type": "noul", "instructions": "unchanged"},
        },
        "opaque_ids": ["w0", "candidate0"],
    }


def test_five_unique_generic_variants_are_fresh_and_source_independent() -> None:
    registry = variants()
    assert len(registry) == 5
    assert len({variant["name"] for variant in registry}) == 5
    assert all(set(variant) == {"name", "rationale", "instructions"} for variant in registry)
    assert all(variant["name"].startswith("minimal-") for variant in registry)
    registry[0]["instructions"] = "mutated caller value"
    assert variants()[0]["instructions"] != registry[0]["instructions"]


def test_transform_changes_only_q0_generic_instruction_and_deep_copies() -> None:
    original = body()
    before = deepcopy(original)
    for variant in variants():
        transformed = transform(original, variant)
        assert transformed["questions"]["q0"]["instructions"] == variant["instructions"]
        transformed["questions"]["q0"]["instructions"] = before["questions"]["q0"]["instructions"]
        assert transformed == before
        assert original == before
        assert transformed["state"] is not original["state"]
        assert transformed["questions"]["q0"]["criteria"] is not original["questions"]["q0"]["criteria"]


def test_private_metadata_cannot_interpolate_into_generic_instruction() -> None:
    first, second = body(), body()
    first["scorer_only"] = {"labels": "private-a", "expected": True}
    second["scorer_only"] = {"labels": "private-b", "expected": False}
    for variant in variants():
        one, two = transform(first, variant), transform(second, variant)
        assert one["questions"] == two["questions"]
        assert "private-" not in one["questions"]["q0"]["instructions"]


def test_missing_or_wrong_question_is_rejected() -> None:
    with pytest.raises(ValueError, match="q0 choice"):
        transform({"questions": {}}, variants()[0])
    changed = body()
    changed["questions"]["q0"]["type"] = "noul"
    with pytest.raises(ValueError, match="q0 choice"):
        transform(changed, variants()[0])
