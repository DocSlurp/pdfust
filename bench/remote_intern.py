"""Local-only adapter for the pinned Intern-Decision-4B reference runtime.

Bootstrap Python >=3.12, torch==2.9.1, torchvision==0.24.1,
transformers==5.14.1 and Pillow>=10.0.0 in an isolated remote environment.
The coordinator downloads the complete pinned snapshot. This adapter never
fetches models, installs dependencies, reads credentials or calls a provider.
"""

# ruff: noqa: ANN401 - imported third-party runtime is deliberately lazy and optional.
from __future__ import annotations

import hashlib
import importlib.util
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

MODEL_ID = "internlm/Intern-Decision-4B"
MODEL_REVISION = "0e5e6aa7d6d750e2b1504ba11a8136cb58aeb3cd"
INFERENCE_SHA256 = "c904e2c67ca0775621a22375ee373d2ba30b52117cda870c6c9ef74143b29863"
REQUIREMENTS = ("torch==2.9.1", "torchvision==0.24.1", "transformers==5.14.1", "Pillow>=10.0.0")
MAX_LENGTH = 8192
MAX_RUNTIME_BYTES = 1_000_000
MAX_QUESTIONS = 16
MAX_IMAGES = 8


def _runtime(directory: Path) -> Any:
    source = directory / "inference.py"
    if source.stat().st_size > MAX_RUNTIME_BYTES or hashlib.sha256(source.read_bytes()).hexdigest() != INFERENCE_SHA256:
        message = "Intern reference runtime differs from pinned source"
        raise ValueError(message)
    name = "_jev_remote_intern_" + MODEL_REVISION
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        message = "Intern reference runtime cannot be imported"
        raise ValueError(message)
    module = importlib.util.module_from_spec(spec)
    # Dataclass definitions require their module to exist during execution.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def load(model_dir: str | Path, device: str = "cuda") -> Any:
    """Load the already staged pinned snapshot with native calibration intact."""
    directory = Path(model_dir).resolve(strict=True)
    runtime = _runtime(directory)
    return runtime.DecisionEngine(
        checkpoint=str(directory),
        device=device,
        backend="hf",
        dtype="bfloat16",
        attn_implementation="sdpa",
        max_length=MAX_LENGTH,
        media_root=str(directory),
    )


def native_request(  # noqa: C901, PLR0912 - explicit canonical transport and admission checks.
    body: dict[str, Any], image_paths: list[str | Path]
) -> dict[str, Any]:
    """Project canonical evidence without changing questions or literal text parts.

    A singleton multimodal text part remains the exact string. Multiple text
    parts remain an ordered list of the exact strings; native JSON serialization
    supplies their boundaries. Staged paths correspond to inline images in
    encounter order. Transport model IDs never select another loaded checkpoint.
    """
    if not isinstance(body, dict) or "state" not in body or not isinstance(body.get("questions"), dict):
        message = "Intern adapter requires canonical state and named questions"
        raise ValueError(message)
    if not body["questions"] or len(body["questions"]) > MAX_QUESTIONS:
        message = "Intern adapter admits 1–16 named questions"
        raise ValueError(message)
    state = body["state"]
    images = 0
    if isinstance(state, list):
        texts = []
        for part in state:
            if isinstance(part, str):
                texts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
            elif isinstance(part, dict) and part.get("type") == "image_url":
                images += 1
            else:
                message = "Intern adapter encountered unsupported multimodal state part"
                raise ValueError(message)
        if not texts:
            message = "Intern adapter requires source text alongside canonical images"
            raise ValueError(message)
        state = texts[0] if len(texts) == 1 else texts
    if "images" in body:
        if images or not isinstance(body["images"], list):
            message = "Intern image transports must not be ambiguous"
            raise ValueError(message)
        images = len(body["images"])
    if images != len(image_paths) or images > MAX_IMAGES:
        message = "Intern staged image count differs from canonical order or exceeds eight"
        raise ValueError(message)
    paths = [str(Path(path).resolve(strict=True)) for path in image_paths]
    if any(not Path(path).is_file() for path in paths):
        message = "Intern staged images must be local files"
        raise ValueError(message)
    result = {"state": deepcopy(state), "questions": deepcopy(body["questions"])}
    if paths:
        result["images"] = paths
    return result


def predict(engine: Any, body: dict[str, Any], image_paths: list[str | Path]) -> dict[str, Any]:
    """Return native answers/usage plus measured adapter wall time, without estimates."""
    request = native_request(body, image_paths)
    started = time.perf_counter()
    native = engine.predict(request)
    elapsed = time.perf_counter() - started
    if not isinstance(native, dict) or not isinstance(native.get("answers"), dict):
        message = "Intern runtime returned no named answer mapping"
        raise TypeError(message)
    if set(native["answers"]) != set(request["questions"]):
        message = "Intern runtime answer inventory differs from requested fields"
        raise ValueError(message)
    response = deepcopy(native)
    response["runtime_elapsed_seconds"] = elapsed
    response["adapter"] = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "runtime_source_sha256": INFERENCE_SHA256,
        "usage_semantics": "native output_tokens count scored fields, not generated tokens",
    }
    return response
