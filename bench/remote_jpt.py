"""Research-only JPT adapter using the publisher-linked llm2jev HF scorer.

JPT uses trained option-token logits from its merged Qwen3.5 LM head, not a
separate readout or generated answer. Install the pinned llm2jev HF/vision
extras in an isolated remote environment. No model imports/downloads occur
until load(); the coordinator owns NC research scope, GPUs and accounting.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import importlib.util
import json
import math
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from collections.abc import Sequence

MODELS = {
    "kirp/jpt-4b": {
        "revision": "78312f855b8bebf83ae7e9e8f05b5a0f73f519a9",
        "config_sha256": "18d14bc3e1105d9b4b164a4df4126cbc2e944d7170d030965e250f5fa44495cc",
        "temperature": 1.036,
    },
    "kirp/jpt-9b": {
        "revision": "9fda2c7f123d36c4789c46c93737e80fc3a6c9fe",
        "config_sha256": "91cd4f87224902681d6922dfd9c414f67574a7ee7d4d3cbf1a0c0ca74543df61",
        "temperature": 1.087,
    },
}
PROCESSOR_PINS = {
    "chat_template.jinja": "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715",
    "tokenizer_config.json": "792fa3f0cb88b111e54ef3134c873531008c4df471d108da17903426e308aa7b",
    "processor_config.json": "bfbc24af59a3e73a9cd0653b8d4ae758dfaec4e3e6c15dfb1c6c8ee8d5683c85",
    "preprocessor_config.json": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
}
RUNTIME_REVISION = "2b252d504972764211ef172c1155ac0fedc9c3de"
RUNTIME_PINS = {
    "__init__.py": "5c82fb6cb5bdd5fdf3a56f42907c8701871afaa0a71a734e57fc0e3e15f3ca45",
    "backends.py": "ae149a5c0bca29ee95bcc9e868a434922e87c728a247e337fb14484c193908b8",
    "prompt.py": "c16c2c9352854ada79b2464cd5a36f5a996ebf629c116d33bbca9d82a404fa29",
    "engine.py": "d309bec345ba5e1be5eec1b8790ea45666ae0d4ed7d0007f6bd2960d944eec5e",
    "scoring.py": "7b1974b59c4222e9aa1c15a416bb0ca080fbf6a55cf90e5f1417da5ae1efb807",
}
MAX_BODY_BYTES = 200_000
MAX_QUESTIONS = 64
MIN_OPTIONS = 2
MAX_OPTIONS = 255
BATCH_TENSOR_DIMS = 2
MAX_IMAGES = 128
MAX_COMBINED_TOKENS = 32_768
PROBABILITY_TOLERANCE = 1e-6


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


@dataclass(frozen=True)
class Engine:
    """Official HF scorer and model/runtime provenance for one isolated worker."""

    scorer: Any
    metadata: dict[str, Any]


def _verify(directory: Path, pins: dict[str, str]) -> None:
    for filename, expected in pins.items():
        if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != expected:
            _fail(f"JPT pinned file hash mismatch: {filename}")


def admit_tokens(_module: object, _args: object, kwargs: dict[str, Any]) -> None:
    """Bound the actual processor-produced sequence before the model forward."""
    ids = kwargs.get("input_ids")
    if ids is None or len(ids.shape) != BATCH_TENSOR_DIMS or ids.shape[-1] > MAX_COMBINED_TOKENS:
        _fail("JPT actual combined input exceeds 32768 tokens; no truncation")


def load(model_dir: str | Path, device: str = "cuda") -> Engine:
    """Load a pinned local JPT snapshot with the official reference scoring code."""
    directory = Path(model_dir).resolve(strict=True)
    config_hash = hashlib.sha256((directory / "config.json").read_bytes()).hexdigest()
    selected = [(name, config) for name, config in MODELS.items() if config["config_sha256"] == config_hash]
    if len(selected) != 1:
        _fail("JPT config does not identify a pinned 4B or 9B snapshot")
    name, config = selected[0]
    _verify(directory, PROCESSOR_PINS)
    spec = importlib.util.find_spec("llm2jev")
    if spec is None or not spec.origin:
        _fail("Install the pinned llm2jev HF/vision runtime before JPT load")
    runtime = Path(spec.origin).resolve().parent
    _verify(runtime, RUNTIME_PINS)
    module = importlib.import_module("llm2jev")
    backend_module = importlib.import_module("llm2jev.backends")
    if (
        Path(module.__file__ or "").resolve().parent != runtime
        or Path(backend_module.__file__ or "").resolve().parent != runtime
    ):
        _fail("JPT runtime import differs from verified installed files")
    backend = backend_module.HF(str(directory), device=device, dtype="bfloat16")
    # HF's processor expands images before this hook. Tensor transfer precedes
    # admission, but an over-limit sequence never reaches attention/model work.
    backend.model.register_forward_pre_hook(admit_tokens, with_kwargs=True)
    # The official scorer alone applies softmax(logits/T). workers=1 preserves
    # serial reference execution; no prefix caching or generated chat fallback.
    scorer = module.LLM2Jev(
        backend.processor or backend.tok, backend, temperature=config["temperature"], style="chat", workers=1
    )
    return Engine(
        scorer,
        {
            "model": name,
            "revision": config["revision"],
            "config_sha256": config_hash,
            "runtime_revision": RUNTIME_REVISION,
            "runtime_sha256": dict(RUNTIME_PINS),
            "temperature": config["temperature"],
            "calibration": "official llm2jev softmax applies temperature once; adapter adds none",
            "device": device,
            "dtype": "bfloat16",
            "license": "CC-BY-NC-4.0; user-authorized research/data collection",
            "max_combined_tokens_per_question": MAX_COMBINED_TOKENS,
            "native_workers": 1,
            "scoring": "trained LM-head option-token logits; no generated answer",
        },
    )


def _verify_images(urls: list[str], image_paths: Sequence[str | Path] | None) -> None:
    if image_paths is not None and (isinstance(image_paths, (str, bytes)) or len(image_paths) != len(urls)):
        _fail("JPT staged image count differs from frozen source")
    for index, url in enumerate(urls):
        if not isinstance(url, str) or not url.startswith("data:image/") or ";base64," not in url:
            _fail("JPT accepts frozen inline images only; no remote media downloads")
        try:
            decoded = base64.b64decode(url.split(",", 1)[1], validate=True)
        except (ValueError, IndexError) as error:
            message = "JPT malformed inline image"
            raise ValueError(message) from error
        if not decoded:
            _fail("JPT empty inline image")
        if image_paths is not None:
            path = Path(image_paths[index])
            if path.stat().st_size != len(decoded) or path.read_bytes() != decoded:
                _fail("JPT staged image differs from frozen bytes")


def _source_state(body: dict[str, Any], image_paths: Sequence[str | Path] | None) -> object:
    state = body["state"]
    urls: list[str] = []
    if isinstance(state, list):
        content = []
        for part in state:
            if isinstance(part, str):
                content.append({"type": "text", "text": part})
            elif (
                isinstance(part, dict)
                and set(part) == {"type", "image_url"}
                and part["type"] == "image_url"
                and isinstance(part["image_url"], dict)
                and set(part["image_url"]) == {"url"}
                and isinstance(part["image_url"]["url"], str)
            ):
                urls.append(part["image_url"]["url"])
                content.append({"type": "image", "image": urls[-1]})
            else:
                _fail("JPT unsupported multimodal state part; refuse without dropping source")
        state = [{"role": "user", "content": content}]
    elif "images" in body:
        if not isinstance(state, str) or not isinstance(body["images"], list):
            _fail("JPT separate images need literal text state")
        urls = body["images"]
        state = [{"role": "user", "content": [{"type": "text", "text": state}]}]
        state[0]["content"].extend({"type": "image", "image": url} for url in urls)
    elif isinstance(state, dict) and set(state) == {"messages"}:
        _fail("JPT chat-message state is outside this source-only adapter contract")
    if isinstance(body["state"], list) and "images" in body:
        _fail("JPT ambiguous duplicate image transport")
    if len(urls) > MAX_IMAGES:
        _fail("JPT image inventory exceeds admission")
    _verify_images(urls, image_paths)
    # Retain data URLs rather than filenames: native HF consumes the exact
    # frozen pixels and filesystem/private source names never enter the prompt.
    return deepcopy(state)


def _questions(body: dict[str, Any]) -> dict[str, Any]:
    questions = body.get("questions")
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        _fail("JPT named question inventory exceeds admission")
    for name, question in questions.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(question, dict)
            or set(question) - {"type", "instructions", "criteria"}
            or question.get("type") != "choice"
            or not isinstance(question.get("criteria"), dict)
            or not MIN_OPTIONS <= len(question["criteria"]) <= MAX_OPTIONS
            or any(not isinstance(key, str) or not key for key in question["criteria"])
        ):
            _fail("JPT requires unchanged named Choice questions and ordered string criteria")
    return questions


def predict(engine: Engine, body: dict[str, Any], image_paths: Sequence[str | Path] | None = None) -> dict[str, Any]:
    """Return native calibrated named Choice answers without invented usage/confidence."""
    if (
        not isinstance(body, dict)
        or set(body) - {"model", "state", "questions", "images"}
        or "state" not in body
        or body.get("model") != engine.metadata["model"]
    ):
        _fail("JPT body must declare its exact loaded model and source-only fields")
    if len(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()) > MAX_BODY_BYTES:
        _fail("JPT source body exceeds byte admission; no truncation")
    questions = _questions(body)
    state = _source_state(body, image_paths)
    native = engine.scorer(state, deepcopy(questions))
    if not isinstance(native, dict) or set(native) != set(questions):
        _fail("JPT native answer inventory differs from frozen questions")
    answers = {}
    for name, question in questions.items():
        answer = native[name]
        probabilities = answer.get("probabilities") if isinstance(answer, dict) else None
        if (
            not isinstance(probabilities, dict)
            or set(probabilities) != set(question["criteria"])
            or any(
                isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1
                for p in probabilities.values()
            )
            or abs(sum(probabilities.values()) - 1) > PROBABILITY_TOLERANCE
            or answer.get("type") != "choice"
            or answer.get("choice") not in probabilities
            or probabilities[answer["choice"]] != max(probabilities.values())
        ):
            _fail("JPT native Choice probabilities/selection are invalid")
        answers[name] = {"type": "choice", "choice": answer["choice"], "probabilities": deepcopy(probabilities)}
    return {"answers": answers}
