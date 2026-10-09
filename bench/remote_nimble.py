"""Research-only local Bespoke-Nimble-9B-v3 native text decision adapter.

Coordinator stages the pinned adapter at model_dir, its base under model_dir/base,
and the publisher's code/nimble tree under model_dir/reference/nimble. Explicit
base_model_dir/reference_dir keywords support other staging layouts. No downloads
or dependency installation occur here. Images are refused, including unstaged
canonical image parts; geometry/text-only ablations must be frozen separately.

Publisher tested Torch2.8, Transformers5.17.0, PEFT0.21.0,
flash-linear-attention0.5.2, causal-conv1d1.7.0 and decision-index commit87d4650.
Freeze actual compatible Blackwell packages separately. CC-BY-NC4.0 declaration;
this adapter supplies no legal conclusion about downstream use.
"""

# ruff: noqa: ANN401 - optional publisher runtime is lazily imported.
from __future__ import annotations

import hashlib
import importlib
import json
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

MODEL_ID = "bespokelabs/Bespoke-Nimble-9B-v3"
MODEL_REVISION = "8e927b9b4afdbb14479fac10a7364d1a695be208"
BASE_MODEL_ID = "Qwen/Qwen3.5-9B"
BASE_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
REFERENCE_REPOSITORY = "bespokelabs/bespoke-nimble-9b-v3-decision-index"
REFERENCE_REVISION = "654b124d3508a7da0d849405744bde80c4bb1a1b"
SOURCE_SHA256 = {
    "decision_index_engine.py": "689e31a4b7ce2a04c9d5d9ec4f2e88a291b718ebf4e66e55a6a782f29f8f2ea1",
    "extended_schema.py": "fb51ac3d51922bb93caa207a34493d6addaa22c9ec1c26df594ba9d46f7a2285",
    "parallel_schema.py": "a0a0f94d0f65e972bc20d088678ad3d595ff1c42b9c0d78f96034526303f63fc",
}
MAX_TOKENS = 32768
MAX_BODY_BYTES = 2 * 1024 * 1024
MAX_QUESTIONS = 16
MAX_CHOICES = 255


def _reference(directory: Path) -> Any:
    package = directory / "nimble" / "evaluation"
    for name, digest in SOURCE_SHA256.items():
        source = package / name
        if source.stat().st_size > MAX_BODY_BYTES or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            message = "Nimble v3 publisher source differs from pinned reference"
            raise ValueError(message)
    for source in (directory / "nimble" / "__init__.py", package / "__init__.py"):
        if source.read_bytes():
            message = "Nimble reference package initializers must match empty pinned files"
            raise ValueError(message)
    name = "nimble.evaluation.decision_index_engine"
    existing = sys.modules.get(name)
    if existing is not None and Path(existing.__file__).resolve() != package / "decision_index_engine.py":
        message = "Another Nimble runtime is already imported"
        raise ValueError(message)
    sys.path.insert(0, str(directory))
    try:
        runtime = importlib.import_module(name)
    finally:
        sys.path.remove(str(directory))
    if Path(runtime.__file__).resolve() != package / "decision_index_engine.py":
        message = "Nimble reference resolved outside staged source"
        raise ValueError(message)
    return runtime


def load(
    model_dir: str | Path,
    device: str = "cuda",
    *,
    base_model_dir: str | Path | None = None,
    reference_dir: str | Path | None = None,
) -> Any:
    """Load staged base+adapter through the unmodified pinned native scorer."""
    if device != "cuda":
        message = "Nimble v3 published native scorer requires BF16 CUDA"
        raise ValueError(message)
    directory = Path(model_dir).resolve(strict=True)
    base = Path(base_model_dir).resolve(strict=True) if base_model_dir else (directory / "base").resolve(strict=True)
    reference = (
        Path(reference_dir).resolve(strict=True) if reference_dir else (directory / "reference").resolve(strict=True)
    )
    if not all(path.is_dir() for path in (directory, base, reference)):
        message = "Nimble adapter, base and reference must be staged local directories"
        raise ValueError(message)
    contract_path = directory / "schema_config.json"
    if contract_path.stat().st_size > MAX_BODY_BYTES:
        message = "Nimble schema contract exceeds admission"
        raise ValueError(message)
    contract = json.loads(contract_path.read_bytes())
    if (
        contract.get("model") != BASE_MODEL_ID
        or contract.get("revision") != BASE_REVISION
        or contract.get("task") != "schema_candidate_classification_v2"
        or contract.get("prompt_source_sha256")
        != {name: SOURCE_SHA256[name] for name in ("parallel_schema.py", "extended_schema.py")}
    ):
        message = "Nimble v3 base or prompt contract differs from pinned release"
        raise ValueError(message)
    runtime = _reference(reference)
    return runtime.NimbleEngine(
        adapter=str(directory),
        model=str(base),
        revision=BASE_REVISION,
        max_tokens=MAX_TOKENS,
        batch_tokens=65536,
        shared_prefix=True,
        cache_tokens=131072,
    )


def _has_images(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("type") in {"image", "image_url", "input_image"} or "png_base64" in value or value.get("images"):
            return True
        return any(_has_images(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_images(item) for item in value)
    if isinstance(value, str):
        if value.startswith("data:image/"):
            return True
        if value.lstrip().startswith(("{", "[")):
            try:
                return _has_images(json.loads(value))
            except json.JSONDecodeError:
                pass
    return False


def native_request(body: dict[str, Any], image_paths: list[str | Path]) -> dict[str, Any]:
    """Admit explicit text-only Choice bodies and preserve source/questions exactly."""
    if image_paths or body.get("images") or _has_images(body.get("state")):
        message = "Nimble v3 text-only scorer refuses image evidence; freeze a labeled text-only ablation"
        raise ValueError(message)
    if set(body) - {"model", "state", "questions", "images"} or "state" not in body:
        message = "Unsupported Nimble canonical fields cannot be silently dropped"
        raise ValueError(message)
    state = body["state"]
    if isinstance(state, list):
        if not all(isinstance(part, str) for part in state):
            message = "Nimble v3 refuses image or unsupported structured multimodal parts"
            raise ValueError(message)
        state = state[0] if len(state) == 1 else deepcopy(state)
    questions = body.get("questions")
    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        message = "Nimble adapter admits 1–16 named Choice questions"
        raise ValueError(message)
    for question in questions.values():
        if (
            not isinstance(question, dict)
            or question.get("type") != "choice"
            or not isinstance(question.get("criteria"), dict)
            or not 1 <= len(question["criteria"]) <= MAX_CHOICES
        ):
            message = "Nimble text ablation requires bounded named Choice criteria"
            raise ValueError(message)
    request = {"state": deepcopy(state), "questions": deepcopy(questions)}
    if len(json.dumps(request, allow_nan=False).encode()) > MAX_BODY_BYTES:
        message = "Nimble text evidence exceeds byte admission"
        raise ValueError(message)
    return request


def predict(engine: Any, body: dict[str, Any], image_paths: list[str | Path]) -> dict[str, Any]:
    """Keep native candidate probabilities/usage; add measured synchronized wall time."""
    request = native_request(body, image_paths)
    engine.synchronize()
    started = time.perf_counter()
    response, artifact = engine(request["state"], request["questions"])
    engine.synchronize()
    elapsed = time.perf_counter() - started
    if artifact is not None:
        message = "Unexpected Nimble native side artifact"
        raise ValueError(message)
    if not isinstance(response, dict) or not isinstance(response.get("answers"), dict):
        message = "Nimble native scorer returned no named answers"
        raise TypeError(message)
    if set(response["answers"]) != set(request["questions"]):
        message = "Nimble native answer inventory differs"
        raise ValueError(message)
    result = deepcopy(response)
    result["runtime_elapsed_seconds"] = elapsed
    result["adapter"] = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "base_revision": BASE_REVISION,
        "reference_revision": REFERENCE_REVISION,
        "evidence_scope": "geometry-text-only",
        "license_declaration": "cc-by-nc-4.0",
        "configuration": "research-only",
        "calibration": "native float64 candidate softmax; no added temperature",
        "usage_semantics": "native input_tokens sums full question prompts; prefix reuse may process fewer",
    }
    return result
