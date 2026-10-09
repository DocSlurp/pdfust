"""Documented Gateway Decisions wire protocol for explicitly verified d1 vision.

Official contract: https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions
Translation is pure and separate from transmission. Freeze the native wire bytes
before calling this client so ledger hashes match request artifacts exactly.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from typing import Any, NoReturn

from bench import decision_hosted as hosted
from bench.decision_gateway import GatewayDecisionClient, _validate, normalize_response

ENDPOINT = "https://ai-gateway.vercel.sh/v1/decisions"
MODEL = "liquid/d1"
MAX_CHOICES = 255
PROBABILITY_TOLERANCE = 1e-6


def _fail(reason: str) -> NoReturn:
    raise ValueError("Gateway vision: " + reason)


def translate(body: dict[str, Any]) -> dict[str, Any]:
    """Preserve literal state/images/questions in the documented native wire shape."""
    _validate(body, hosted.MAX_IMAGE_BODY_BYTES)
    if body["model"] != MODEL or not isinstance(body["state"], str):
        _fail("only d1 with literal string state is admitted")
    content = [{"type": "input_text", "text": body["state"]}]
    content.extend({"type": "input_image", "image_url": image, "detail": "high"} for image in body.get("images", []))
    questions = []
    for name, question in body["questions"].items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(question, dict)
            or set(question) != {"type", "instructions", "criteria"}
            or question["type"] != "choice"
            or not isinstance(question["criteria"], dict)
            or not 1 <= len(question["criteria"]) <= MAX_CHOICES
            or any(not isinstance(option, str) for option in question["criteria"])
        ):
            _fail("expected named Choice instructions and string-keyed criteria")
        questions.append(
            {
                "name": name,
                "type": "choice",
                "instructions": deepcopy(question["instructions"]),
                "choices": [
                    {"value": option, "description": deepcopy(description)}
                    for option, description in question["criteria"].items()
                ],
            }
        )
    wire = {"model": MODEL, "input": [{"role": "user", "content": content}], "questions": questions}
    if "providerOptions" in body:
        wire["providerOptions"] = deepcopy(body["providerOptions"])
    return wire


def validate_wire(body: dict[str, Any], max_body_bytes: int) -> bytes:  # noqa: C901, PLR0912
    """Require actual native wire bytes; never translate implicitly during a call."""
    if not isinstance(body, dict) or set(body) - {"model", "input", "questions", "providerOptions"}:
        _fail("unexpected native wire fields")
    messages = body.get("input")
    if not isinstance(messages, list) or len(messages) != 1:
        _fail("expected one native user message")
    message = messages[0]
    if not isinstance(message, dict) or set(message) != {"role", "content"} or message["role"] != "user":
        _fail("expected native user content")
    content = message["content"]
    if (
        not isinstance(content, list)
        or not content
        or not isinstance(content[0], dict)
        or content[0].get("type") != "input_text"
    ):
        _fail("expected literal text followed by images")
    if set(content[0]) != {"type", "text"}:
        _fail("text part changed")
    images = []
    for part in content[1:]:
        if not isinstance(part, dict) or set(part) != {"type", "image_url", "detail"}:
            _fail("image part changed")
        if part["type"] != "input_image" or part["detail"] != "high":
            _fail("expected frozen high-detail image part")
        images.append(part["image_url"])
    questions = body.get("questions")
    if not isinstance(questions, list) or not questions:
        _fail("expected native question array")
    canonical: dict[str, Any] = {"model": body.get("model"), "state": content[0]["text"], "questions": {}}
    if images:
        canonical["images"] = images
    if "providerOptions" in body:
        canonical["providerOptions"] = body["providerOptions"]
    for question in questions:
        if not isinstance(question, dict) or set(question) != {"name", "type", "instructions", "choices"}:
            _fail("native question fields changed")
        name = question["name"]
        choices = question["choices"]
        if not isinstance(name, str) or name in canonical["questions"] or not isinstance(choices, list):
            _fail("duplicate name or malformed choices")
        criteria = {}
        for option in choices:
            if not isinstance(option, dict) or set(option) != {"value", "description"}:
                _fail("choice fields changed")
            value = option["value"]
            if not isinstance(value, str) or value in criteria:
                _fail("duplicate or nonstring choice")
            criteria[value] = option["description"]
        canonical["questions"][name] = {
            "type": question["type"],
            "instructions": question["instructions"],
            "criteria": criteria,
        }
    # Round trip rejects lossy translation, fallbacks, unknown keys and model aliases.
    if translate(canonical) != body:
        _fail("native wire does not preserve the exact canonical contract")
    if type(max_body_bytes) is not int or not 1 <= max_body_bytes <= hosted.MAX_IMAGE_BODY_BYTES:
        _fail("byte admission exceeds shared ceiling")
    encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) > max_body_bytes:
        _fail("native wire exceeds frozen byte admission")
    return encoded


def normalize_answers(raw: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
    """Map documented named answer/probability arrays into strict Choice dictionaries."""
    result = normalize_response(raw)
    answers = raw.get("answers")
    if not isinstance(answers, list) or len(answers) != len(body["questions"]):
        _fail("answer inventory changed")
    expected = {question["name"]: {option["value"] for option in question["choices"]} for question in body["questions"]}
    normalized = {}
    for answer in answers:
        if not isinstance(answer, dict):
            _fail("answer is not an object")
        name = answer.get("name")
        if not isinstance(name, str) or name not in expected or name in normalized or answer.get("type") != "choice":
            _fail("refused, duplicate or unexpected named answer")
        rows = answer.get("probabilities")
        if not isinstance(rows, list):
            _fail("native probability array missing")
        probabilities = {}
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"value", "probability"}:
                _fail("malformed probability row")
            value, probability = row["value"], row["probability"]
            if (
                not isinstance(value, str)
                or value not in expected[name]
                or value in probabilities
                or isinstance(probability, bool)
                or not isinstance(probability, (int, float))
                or not math.isfinite(probability)
                or not 0 <= probability <= 1
            ):
                _fail("invalid probability option/value")
            probabilities[value] = probability
        if set(probabilities) != expected[name] or abs(sum(probabilities.values()) - 1) > PROBABILITY_TOLERANCE:
            _fail("probability inventory or sum changed")
        choice = answer.get("choice")
        if (
            not isinstance(choice, str)
            or choice not in probabilities
            or probabilities[choice] != max(probabilities.values())
        ):
            _fail("selected choice is not a maximal native probability")
        normalized[name] = {**answer, "probabilities": probabilities}
    result["answers"] = normalized
    return result


class GatewayVisionDecisionClient(GatewayDecisionClient):
    """Share the budget ledger while isolating the documented native image route."""

    endpoint = ENDPOINT

    def _encode(self, body: dict[str, Any], max_body_bytes: int) -> bytes:
        """Admit actual frozen native wire; caller must translate before freezing."""
        return validate_wire(body, max_body_bytes)

    def _normalize(self, raw: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        """Preserve usage/provider metadata and map only documented native answers."""
        return normalize_answers(raw, body)
