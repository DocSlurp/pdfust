"""Presence gate must remove candidate suggestions and preserve literal source."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.source_table_gate import CRITERIA, VISIBLE_KEYS, gate_body, variants


def admission_body() -> dict[str, Any]:
    """Return a request with source evidence and deliberately suggestive candidate fields."""
    visible = {
        "coordinates": "display points",
        "page_size": [0, 0, 600, 800],
        "source_words": [{"id": "word0", "text": "literal  OCR!", "bbox": [1, 2, 3, 4]}],
        "image_mapping": {"pixels": [384, 512]},
        "candidate_tables": {"rolling": {"values": [["invented suggestion"]]}},
        "header_policy": "candidate policy",
        "future_hypothesis": "must disappear",
    }
    return {
        "model": "test-model",
        "state": [json.dumps(visible), {"image_url": {"url": "same-pixels"}}],
        "questions": {"q0": {"instructions": "candidate-selection", "criteria": {"rolling": "accept"}}},
    }


@pytest.mark.parametrize("variant", variants(), ids=lambda v: v["name"])
def test_gate_has_only_source_evidence(variant: dict[str, str]) -> None:
    """Both prompts see identical pixels/regions and no reconstruction hypotheses."""
    original = admission_body()
    saved = deepcopy(original)
    body = gate_body(original, variant)
    visible = json.loads(body["state"][0])
    assert set(visible) == VISIBLE_KEYS
    assert visible["source_words"] == json.loads(original["state"][0])["source_words"]
    assert body["state"][1:] == original["state"][1:]
    assert body["model"] == original["model"]
    assert body["questions"]["q0"]["criteria"] == CRITERIA
    assert body["questions"]["q0"]["instructions"] == variant["instructions"]
    assert original == saved


def test_partial_source_is_refused() -> None:
    """Missing source geometry cannot be silently reconstructed from candidates."""
    body = admission_body()
    visible = json.loads(body["state"][0])
    del visible["source_words"]
    body["state"][0] = json.dumps(visible)
    with pytest.raises(ValueError, match="Complete source"):
        gate_body(body, variants()[0])


def test_nonimage_body_is_refused() -> None:
    """Require the same original whole-page image evidence."""
    body = admission_body()
    body["state"] = {}
    with pytest.raises(ValueError, match="whole-page image"):
        gate_body(body, variants()[0])


def test_missing_pixels_are_refused() -> None:
    """An image mapping without actual pixels cannot masquerade as an image arm."""
    body = admission_body()
    body["state"] = body["state"][:1]
    with pytest.raises(ValueError, match="whole-page image"):
        gate_body(body, variants()[0])
