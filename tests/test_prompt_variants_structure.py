"""Instruction-only prompt variants preserve every source and choice field."""

from __future__ import annotations

from copy import deepcopy

import pytest
from bench.prompt_variants_structure import transform, variants


def body(*, image: bool = False) -> dict:
    source = {
        "words": [{"id": "w0", "text": "Observed source", "bbox": [1, 2, 3, 4]}],
        "candidate_tables": {"rolling": {"cells": [{"source_ids": ["w0"]}]}},
    }
    state = (
        [source, {"type": "image_url", "image_url": {"url": "data:image/png;base64,UNCHANGED"}}] if image else source
    )
    return {
        "model": "test-model",
        "state": state,
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Original frozen prompt",
                "criteria": {
                    "rolling": "Complete existing candidate",
                    "not_table": "Non-table",
                    "unresolved": "Abstain",
                },
            }
        },
    }


@pytest.mark.parametrize("variant", variants(), ids=lambda v: v["name"])
@pytest.mark.parametrize("image", [False, True])
def test_only_q0_instruction_changes_and_copies_are_independent(variant: dict, *, image: bool) -> None:
    original = body(image=image)
    before = deepcopy(original)
    changed = transform(original, variant)
    assert original == before
    assert changed["questions"]["q0"]["instructions"] == variant["instructions"]
    restored = deepcopy(changed)
    restored["questions"]["q0"]["instructions"] = before["questions"]["q0"]["instructions"]
    assert restored == before
    assert changed["state"] is not original["state"]
    assert changed["questions"]["q0"]["criteria"] is not original["questions"]["q0"]["criteria"]


def test_variant_cannot_smuggle_metadata_or_case_specific_instructions() -> None:
    variant = variants()[0]
    variant["instructions"] += " SECRET_EXPECTED_ANSWER"
    with pytest.raises(ValueError, match="registered"):
        transform(body(), variant)


def test_transform_does_not_project_case_metadata_into_instructions() -> None:
    original = body()
    original["private_metadata"] = "SECRET_EXPECTED_ANSWER"
    variant = variants()[0]
    changed = transform(original, variant)
    assert changed["questions"]["q0"]["instructions"] == variant["instructions"]
    assert "SECRET_EXPECTED_ANSWER" not in changed["questions"]["q0"]["instructions"]
    assert changed["private_metadata"] == original["private_metadata"]


@pytest.mark.parametrize("mutation", ["extra_question", "missing_abstain", "wrong_type"])
def test_incompatible_menu_is_rejected(mutation: str) -> None:
    original = body()
    if mutation == "extra_question":
        original["questions"]["q1"] = deepcopy(original["questions"]["q0"])
    elif mutation == "missing_abstain":
        del original["questions"]["q0"]["criteria"]["unresolved"]
    else:
        original["questions"]["q0"]["type"] = "nouls"
    with pytest.raises(ValueError, match=r"require|retain"):
        transform(original, variants()[0])
