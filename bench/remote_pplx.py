"""Pinned native PPLX decision adapter; importing this module performs no inference.

Bootstrap an isolated Python 3.12+ environment with the pinned model repository's
requirements.txt. Keep SDPA, the noncausal hook, separate readout, and supplied
calibration. Stock causal chat/vLLM loaders are not equivalent. CUDA wheel/driver
and Blackwell kernel compatibility must be checked on the actual remote host.
The coordinator owns downloads, device checks, budgets and resource measurement.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import math
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

MODEL = "perplexity-ai/pplx-decider-v1.1-27b"
HOSTED_MODEL = "perplexity/pplx-decider-v1.1-27b"
REVISION = "6195aa55a72ae21e503c8a60198f7b390d42adb5"
BASE_REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
PINNED_FILES = {
    "source/src/autojev/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "source/src/autojev/model.py": "02940963e9fba5736b8f625f860812f31de2e6658a49606fbed49fd7215c20f9",
    "source/src/autojev/types.py": "250ba2eea1cd9bc5501bc76ba76b2f4a1d6c692a7fb1bba4b01affff38cb81ca",
    "requirements.txt": "60ce3c0ba6ec117b114e2ec1641baef7f50cb68020fc9bf46653a86e885e32e8",
    "decision_config.json": "68d4a4c704a0c42837f749b0287bd80f70d186ed3be4dc6a90802e78223925e8",
}
MAX_BODY_BYTES = 200_000
MAX_QUESTIONS = 128
MAX_IMAGES = 128
MAX_OPTIONS = 255
PROBABILITY_TOLERANCE = 1e-5


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


@dataclass(frozen=True)
class Engine:
    """Native model plus the publisher's answer formatter and load provenance."""

    model: Any
    answer: Callable[..., dict[str, Any]]
    metadata: dict[str, Any]


def load(model_dir: str | Path, device: str = "cuda") -> Engine:
    """Load local pinned files with the supplied DecisionModel, without downloads."""
    directory = Path(model_dir).resolve(strict=True)
    hashes = {}
    for relative, expected in PINNED_FILES.items():
        digest = hashlib.sha256((directory / relative).read_bytes()).hexdigest()
        if digest != expected:
            _fail(f"PPLX pinned runtime/config hash mismatch: {relative}")
        hashes[relative] = digest
    config = json.loads((directory / "decision_config.json").read_text())
    if (
        config.get("attention_mode") != "noncausal_full_attention"
        or config.get("revision") != BASE_REVISION
        or config.get("pooling") != "last"
        or config.get("base_model") != "Qwen/Qwen3.8-27B"
    ):
        _fail("PPLX checkpoint attention/base/pooling contract changed")
    origin = (directory / "source/src/autojev/model.py").resolve()
    existing = sys.modules.get("autojev.model")
    if existing is not None and Path(existing.__file__ or "").resolve() != origin:
        _fail("A different autojev model is already imported; use an isolated worker")
    package = sys.modules.get("autojev")
    if package is not None:
        paths = {Path(path).resolve() for path in getattr(package, "__path__", [])}
        if (directory / "source/src/autojev").resolve() not in paths:
            _fail("A different autojev package is already imported; use an isolated worker")
    source = str(directory / "source/src")
    sys.path.insert(0, source)
    try:
        native = importlib.import_module("autojev.model")
    finally:
        sys.path.remove(source)
    if Path(native.__file__ or "").resolve() != origin:
        _fail("PPLX imported runtime is not the pinned local source")
    # Native constructor reads the separate readout and saved calibration; its
    # own loader selects SDPA and installs the saved noncausal attention hook.
    model = native.DecisionModel(directory, device=device)
    if model.attention_mode != config["attention_mode"] or model.temperature != config["temperature"]:
        _fail("PPLX native attention/calibration did not match the checkpoint")
    return Engine(
        model,
        native.answer,
        {
            "model": MODEL,
            "revision": REVISION,
            "base_revision": BASE_REVISION,
            "runtime_sha256": hashes,
            "device": device,
            "attention_mode": model.attention_mode,
            "temperature": model.temperature,
            "calibration": "native predict applies saved temperature once; adapter adds none",
            "native_batch_size": 1,
            "max_combined_tokens_per_question": 8192,
            "image_processor_min_pixels": 65_536,
            "image_processor_max_pixels": 4_194_304,
        },
    )


def _state(body: dict[str, Any]) -> tuple[Any, list[str]]:
    state = body["state"]
    images: list[str] = []
    if isinstance(state, list):
        texts = []
        for part in state:
            if isinstance(part, str):
                if images:
                    _fail("PPLX requires text parts before images; refuse reordered evidence")
                texts.append(part)
            elif (
                isinstance(part, dict)
                and set(part) == {"type", "image_url"}
                and part["type"] == "image_url"
                and isinstance(part["image_url"], dict)
                and set(part["image_url"]) == {"url"}
                and isinstance(part["image_url"]["url"], str)
            ):
                images.append(part["image_url"]["url"])
            else:
                _fail("PPLX unsupported multimodal state part; refuse without dropping it")
        if not texts:
            _fail("PPLX multimodal state needs literal text")
        # One text part remains byte-for-byte literal. Multiple parts retain
        # their values and order as a JSON list, never guessed separators.
        state = texts[0] if len(texts) == 1 else texts
    if "images" in body:
        if images or not isinstance(body["images"], list) or any(not isinstance(i, str) for i in body["images"]):
            _fail("PPLX ambiguous or malformed duplicate image transport")
        images = body["images"]
    if len(images) > MAX_IMAGES:
        _fail("PPLX image admission exceeded")
    return deepcopy(state), images


def _images(urls: list[str], image_paths: Sequence[str | Path] | None) -> list[str | Path]:
    if image_paths is not None and (isinstance(image_paths, (str, bytes)) or len(image_paths) != len(urls)):
        _fail("PPLX staged image count differs from frozen body")
    images: list[str | Path] = []
    for index, url in enumerate(urls):
        if not url.startswith("data:image/") or ";base64," not in url:
            _fail("PPLX admits only frozen inline image data; no remote downloads")
        try:
            decoded = base64.b64decode(url.split(",", 1)[1], validate=True)
        except (ValueError, IndexError) as error:
            message = "PPLX malformed inline image"
            raise ValueError(message) from error
        if not decoded:
            _fail("PPLX empty inline image")
        if image_paths is None:
            images.append(url)
        else:
            path = Path(image_paths[index])
            if path.stat().st_size != len(decoded) or path.read_bytes() != decoded:
                _fail("PPLX staged image bytes differ from frozen source")
            images.append(path)
    return images


def _questions(body: dict[str, Any]) -> dict[str, Any]:
    questions = body.get("questions")
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        _fail("PPLX named question inventory exceeds admission")
    for name, question in questions.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(question, dict)
            or set(question) - {"type", "instructions", "criteria"}
            or question.get("type") != "choice"
            or not isinstance(question.get("criteria"), dict)
            or not 1 <= len(question["criteria"]) <= MAX_OPTIONS
            or any(not isinstance(key, str) or not key for key in question["criteria"])
        ):
            _fail("PPLX requires unchanged named Choice questions and ordered string criteria")
    return questions


def predict(engine: Engine, body: dict[str, Any], image_paths: Sequence[str | Path] | None = None) -> dict[str, Any]:
    """Ask each unchanged named Choice independently using native calibrated predict.

    No hosted token usage or calibrated correctness confidence is fabricated.
    The publisher prepends images to its prompt and interprets each question
    separately; this is not shared multi-question compute or provider parity.
    """
    if not isinstance(body, dict) or set(body) - {"model", "state", "questions", "images"}:
        _fail("PPLX unsupported source body fields")
    if body.get("model") not in {MODEL, HOSTED_MODEL} or "state" not in body:
        _fail("PPLX requires the exact declared model and state")
    encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) > MAX_BODY_BYTES:
        _fail("PPLX source body exceeds admission; no truncation")
    questions = _questions(body)
    state, urls = _state(body)
    images = _images(urls, image_paths)
    rows = [
        {"state": deepcopy(state), "question": deepcopy(question), **({"images": images.copy()} if images else {})}
        for question in questions.values()
    ]
    # Do not supply temperature or apply softmax/calibration again. Start at
    # one branch per native batch until the remote pilot measures memory.
    distributions = engine.model.predict(rows, batch_size=1)
    if not isinstance(distributions, list) or len(distributions) != len(rows):
        _fail("PPLX native answer count differs from questions")
    answers = {}
    for (name, question), probabilities in zip(questions.items(), distributions, strict=True):
        if (
            not isinstance(probabilities, (list, tuple))
            or len(probabilities) != len(question["criteria"])
            or any(
                isinstance(p, bool) or not isinstance(p, (float, int)) or not math.isfinite(p) or not 0 <= p <= 1
                for p in probabilities
            )
            or abs(sum(probabilities) - 1) > PROBABILITY_TOLERANCE
        ):
            _fail("PPLX native probability inventory/mass is invalid")
        answer = engine.answer(deepcopy(question), probabilities)
        keys = list(question["criteria"])
        selected = keys[max(range(len(keys)), key=lambda index: probabilities[index])]
        if answer.get("choice") != selected or set(answer.get("probabilities", {})) != set(keys):
            _fail("PPLX supplied answer formatter changed Choice semantics")
        answers[name] = {"type": "choice", "choice": selected, "probabilities": answer["probabilities"]}
    return {"answers": answers}
