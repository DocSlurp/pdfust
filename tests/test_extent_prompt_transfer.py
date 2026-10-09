"""Expanded-union prompt transfer changes no source, menu, image or model fields."""

from copy import deepcopy
from typing import Any

import pytest
from bench.extent_prompt_transfer import NAMES, transfer_body
from bench.prompt_variants_evidence import variants


@pytest.mark.parametrize("name", NAMES)
def test_prompt_transfer_changes_only_q0_instructions(name: str) -> None:
    """Every nested observation and candidate declaration stays byte-for-byte equivalent."""
    body: dict[str, Any] = {
        "model": "declared-model",
        "state": ["literal source with candidate IDs", {"image_url": {"url": "same-pixels", "detail": "high"}}],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "parent instructions",
                "criteria": {"c0": "candidate", "not_table": "prose", "unresolved": "uncertain"},
            }
        },
        "future_field": {"nested": [1, 2, 3]},
    }
    original = deepcopy(body)
    result = transfer_body(body, name)
    assert result["questions"]["q0"]["instructions"] == next(v["instructions"] for v in variants() if v["name"] == name)
    assert result != original
    result["questions"]["q0"]["instructions"] = original["questions"]["q0"]["instructions"]
    assert result == original
    assert body == original
    result["state"][1]["image_url"]["url"] = "changed-copy"
    assert body == original


def test_unknown_transfer_variant_is_refused() -> None:
    """The freezer uses an existing registry prompt rather than constructing target-specific text."""
    with pytest.raises(ValueError, match="Unknown evidence"):
        transfer_body({"questions": {"q0": {"instructions": "parent"}}}, "not-a-registry-prompt")
