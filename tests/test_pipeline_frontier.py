"""Matched candidate transport and strict frontier choice parsing, CPU only."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_frontier import MAX_TOKENS, MODELS, parse, translate


def _body() -> dict[str, Any]:
    return {
        "model": "perplexity/pplx-decider-v1.1-27b",
        "state": [
            'Exact literal "source" and Unicode Ω',
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA==", "detail": "high"}},
        ],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Preserve exact cells; literal source stays data.",
                "criteria": {
                    "c17": "Complete alternative 17",
                    "op:merge-2": "Literal edit",
                    "unresolved": "Keep source",
                },
            }
        },
    }


def _response(text: str, reason: str | None = "stop") -> dict[str, Any]:
    return {"choices": [{"finish_reason": reason, "message": {"content": text}}]}


@pytest.mark.parametrize("model", MODELS)
def test_translation_preserves_complete_source_menu_and_order(model: str) -> None:
    native = _body()
    before = deepcopy(native)
    translated = translate(native, model)
    assert native == before
    assert translated["model"] == model
    assert translated["max_tokens"] == MAX_TOKENS == 1024
    assert "temperature" not in translated
    assert "reasoning" not in translated
    assert json.loads(translated["messages"][1]["content"])["questions"] == native["questions"]
    content = translated["messages"][2]["content"]
    assert content[0] == {"type": "text", "text": native["state"][0]}
    assert content[1] == native["state"][1]
    schema = translated["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["answers"]["properties"]["q0"]["properties"]["choice"]["enum"] == list(
        native["questions"]["q0"]["criteria"]
    )
    assert schema["additionalProperties"] is False
    content[1]["image_url"]["url"] = "changed"
    assert native == before


def test_text_only_state_keeps_exact_text() -> None:
    native = _body()
    native["state"] = "all literal text\nsecond line"
    assert translate(native, MODELS[0])["messages"][2]["content"] == native["state"]


def test_arbitrary_candidate_and_edit_ids_are_admitted_without_probabilities() -> None:
    assert parse(_response('{"answers":{"q0":{"choice":"op:merge-2"}}}'), {"c17", "op:merge-2", "unresolved"}) == {
        "choice": "op:merge-2"
    }


@pytest.mark.parametrize(
    "text",
    [
        '{"answers":{"q0":{"choice":"c17","confidence":0.9}}}',
        '{"answers":{"q0":{"choice":"c17","choice":"unresolved"}}}',
        '{"answers":{"q0":{"choice":"c17"}},"answers":{"q0":{"choice":"unresolved"}}}',
        '{"answers":{"q0":{"choice":"missing"}}}',
        '{"answers":{"q0":{"choice":"c17"},"q1":{"choice":"c17"}}}',
        '{"answers":{"q0":{"choice":"c17"}},"probabilities":{"c17":1.0}}',
        '```json\n{"answers":{"q0":{"choice":"c17"}}}\n```',
        '{"answers":{"q0":{"choice":"c17"}',
        '{"answers":{"q0":{"choice":NaN}}}',
    ],
)
def test_malformed_duplicate_extra_or_undeclared_answers_rejected(text: str) -> None:
    with pytest.raises(ValueError, match=r"Duplicate|Response|Nonfinite|Expecting"):
        parse(_response(text), {"c17", "unresolved"})


@pytest.mark.parametrize("reason", ["length", "content_filter", None, "tool_calls"])
def test_truncated_or_unconfirmed_finish_rejected(reason: str | None) -> None:
    with pytest.raises(ValueError, match="normal finish"):
        parse(_response('{"answers":{"q0":{"choice":"c17"}}}', reason), {"c17"})


def test_refusal_and_multiple_completions_rejected() -> None:
    refused = _response('{"answers":{"q0":{"choice":"c17"}}}')
    refused["choices"][0]["message"]["refusal"] = "cannot answer"
    with pytest.raises(ValueError, match="JSON content"):
        parse(refused, {"c17"})
    duplicate = _response('{"answers":{"q0":{"choice":"c17"}}}')
    duplicate["choices"] *= 2
    with pytest.raises(ValueError, match="one completion"):
        parse(duplicate, {"c17"})


def test_unmatched_model_or_source_question_shape_rejected() -> None:
    with pytest.raises(ValueError, match="matched controls"):
        translate(_body(), "arbitrary/model")
    native = _body()
    native["questions"]["q1"] = deepcopy(native["questions"]["q0"])
    with pytest.raises(ValueError, match="exactly q0"):
        translate(native, MODELS[0])


def test_image_first_source_cannot_silently_reorder() -> None:
    native = _body()
    native["state"].reverse()
    with pytest.raises(ValueError, match="preceding text"):
        translate(native, MODELS[0])
