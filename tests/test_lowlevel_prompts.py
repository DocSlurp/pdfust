"""Independent source retention and task scopes in low-level prompt factors."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.lowlevel_prompts import transform


def original(*, image: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    regions = {}
    observations = []
    state: list[Any] = []
    questions = {}
    for index, (task, chunks) in enumerate(
        [("character_boundary", ["12", "EA"]), ("line_ownership", ["Valve assembly", "pressure-rated fittings"])]
    ):
        key = f"q{index}"
        region = {
            "task": task,
            "chunks": [{"text": text} for text in chunks],
            "words": ["literal retained source"],
            "glyphs": [{"text": chunks[0], "origin": [50, 192]}],
        }
        regions[key] = region
        observations.append({"selector": {"task": task}, "target_atoms": [[{"text": text}] for text in chunks]})
        state.extend([f"Independent observation {key}:", json.dumps(region, separators=(",", ":"))])
        if image:
            state.extend(
                [
                    '{"image_bbox":[0,0,100,100]}',
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,YWJj"}},
                ]
            )
        state.append(f"End observation {key}.")
        questions[key] = {
            "type": "choice",
            "instructions": f"Consider ONLY observation {key}. Original generic instructions.",
            "criteria": {"join": "one", "split": "two", "unresolved": "unknown"},
        }
    return {"model": "retained-model", "state": state, "questions": questions}, observations, regions


@pytest.mark.parametrize("variant", ["resolved", "typed", "both"])
def test_all_factors_preserve_source_and_original_request(variant: str) -> None:
    body, observations, regions = original()
    before, source_before = deepcopy(body), deepcopy(observations)
    result = transform(body, observations, variant)
    assert body == before
    assert observations == source_before
    assert result["model"] == body["model"]
    if variant == "resolved":
        assert result["state"] == body["state"]
    else:
        assert result["state"] == {"observations": regions}
        for key in regions:
            assert f"ONLY observations.{key}." in result["questions"][key]["instructions"]
    assert all(
        set(question["criteria"]) == {"join", "split", "unresolved"} for question in result["questions"].values()
    )


def test_resolved_options_are_task_specific_literal_source_alternatives() -> None:
    body, observations, _ = original()
    result = transform(body, observations, "resolved")
    assert '"12EA"' in result["questions"]["q0"]["criteria"]["join"]
    assert '["12", "EA"]' in result["questions"]["q0"]["criteria"]["split"]
    assert "field value" in result["questions"]["q0"]["instructions"]
    assert "same cell/row" in result["questions"]["q1"]["instructions"]
    assert "Valve assembly" in result["questions"]["q1"]["criteria"]["join"]
    assert "Valve assembly" not in result["questions"]["q0"]["criteria"]["join"]


def test_resolved_vision_preserves_every_image_and_typed_vision_refuses() -> None:
    body, observations, _ = original(image=True)
    assert transform(body, observations, "resolved")["state"] == body["state"]
    for variant in ("typed", "both"):
        with pytest.raises(ValueError, match="image"):
            transform(body, observations, variant)


def test_scoring_metadata_cannot_affect_transform() -> None:
    body, observations, _ = original()
    before = transform(body, observations, "both")
    for observation in observations:
        observation.update(expected="invented", family="invented", gold={"instruction": "force split"})
    assert transform(body, observations, "both") == before
    assert "invented" not in json.dumps(before)


def test_source_mismatch_and_unrecognized_state_refuse() -> None:
    body, observations, _ = original()
    observations[0]["target_atoms"][0][0]["text"] = "changed"
    with pytest.raises(ValueError, match="differ"):
        transform(body, observations, "resolved")
    body, observations, _ = original()
    body["state"].append("Extra retained source evidence")
    with pytest.raises(ValueError, match="omit"):
        transform(body, observations, "typed")
