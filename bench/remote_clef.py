"""Opt-in local Clef adapter; importing this module loads no model or credentials.

Reference cards test torch==2.11.0 and transformers==5.10.2, plus Pillow,
safetensors and huggingface_hub. Freeze the latter dependency versions in the
remote environment manifest. Bootstrap/download/staging belongs to the worker:
download RELEASES at their exact revisions, then call load with a local folder.
Both releases are Apache-2.0. Reference helper/code and weights are external;
this adapter does not copy them or enable models in default PDF extraction.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

RELEASES = {
    "Cloudflare/clef": "ed3eed331870db2eff4b0db01237128ede8a00ce",
    "Cloudflare/clef-flash": "fde727a287004204b7518dcc983fe64379776712",
}
HELPER_SHA256 = "0e304cf7c6500e8bb59bef7e2afd2c6373f82596dfb3b57d1aa93c175e2dc3a3"
MAX_LENGTH = 16384
MAX_BODY_BYTES = 2 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_IMAGES = 16
BOOTSTRAP_TESTED = ("torch==2.11.0", "transformers==5.10.2")


@dataclass(frozen=True)
class Engine:
    """Keep the supplied runtime, processor and reference helper together."""

    model: Any
    processor: Any
    helper: Any


def load(model_dir: str | Path, device: str = "cuda") -> Engine:
    """Load only an existing local release with the pinned reference helper.

    The worker must separately verify staged weight hashes and release revision.
    Hub IDs/nonexistent directories are refused, preventing implicit downloads.
    """
    directory = Path(model_dir).resolve(strict=True)
    if not directory.is_dir():
        message = "model_dir must be an existing local release directory"
        raise ValueError(message)
    source = directory / "joint_schema_model.py"
    if hashlib.sha256(source.read_bytes()).hexdigest() != HELPER_SHA256:
        message = "Clef helper differs from the pinned release"
        raise ValueError(message)
    name = "_jev_remote_clef_" + HELPER_SHA256
    helper = sys.modules.get(name)
    if helper is None:
        spec = importlib.util.spec_from_file_location(name, source)
        if spec is None or spec.loader is None:
            message = "cannot import the staged Clef helper"
            raise ValueError(message)
        helper = importlib.util.module_from_spec(spec)
        sys.modules[name] = helper
        try:
            spec.loader.exec_module(helper)
        except BaseException:
            sys.modules.pop(name, None)
            raise
    model, processor = helper.load_release_model(directory, device=device, local_files_only=True)
    return Engine(model, processor, helper)


def _is_image(part: object) -> bool:
    """Recognize the two frozen SystemOne image representations."""
    return isinstance(part, dict) and (
        (set(part) == {"image"} and isinstance(part["image"], str))
        or (
            set(part) == {"type", "image_url"}
            and part["type"] == "image_url"
            and isinstance(part["image_url"], dict)
            and isinstance(part["image_url"].get("url"), str)
        )
    )


def _request(body: dict[str, Any], image_paths: Sequence[str | Path]) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Translate the pilot's one literal text plus images without rewriting text."""
    if len(json.dumps(body, ensure_ascii=False).encode("utf-8")) > MAX_BODY_BYTES:
        message = "request exceeds the remote adapter byte bound"
        raise ValueError(message)
    if set(body) - {"model", "state", "questions", "images", "media_kwargs"}:
        message = "unsupported request fields; evidence cannot be silently dropped"
        raise ValueError(message)
    if not isinstance(body.get("model"), str) or "state" not in body:
        message = "model and source state are required"
        raise ValueError(message)
    if not isinstance(body.get("questions"), dict) or not body["questions"]:
        message = "source questions must be a nonempty mapping"
        raise ValueError(message)
    request = deepcopy(body)
    state = body["state"]
    embedded_count = 0
    if isinstance(state, list):
        embedded_count = sum(_is_image(part) for part in state)
        if embedded_count:
            texts = [part for part in state if not _is_image(part)]
            if len(texts) != 1 or not isinstance(texts[0], str):
                message = "pilot multimodal state requires exactly one literal text segment"
                raise ValueError(message)
            request["state"] = texts[0]
    top_images = body.get("images") or []
    if not isinstance(top_images, list):
        message = "images must be a list"
        raise TypeError(message)
    if embedded_count and top_images:
        message = "embedded and top-level images cannot be mixed"
        raise ValueError(message)
    image_count = embedded_count or len(top_images)
    if image_count != len(image_paths) or image_count > MAX_IMAGES:
        message = "local image paths must match the source images in order"
        raise ValueError(message)
    # No URL/data-URI fetches: frozen image bytes are staged by the worker.
    if image_count:
        from PIL import Image  # noqa: PLC0415 -- optional remote-image dependency

        images = []
        for image_path in image_paths:
            with Image.open(image_path) as image:
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    message = "image exceeds the adapter pixel bound"
                    raise ValueError(message)
                image.load()
                images.append(image.copy())
        request["images"] = images
    else:
        request.pop("images", None)
    return request


def predict(engine: Engine, body: dict[str, Any], image_paths: Sequence[str | Path]) -> dict[str, Any]:
    """Return native answers/usage after complete-input token admission.

    The pinned helper silently slices state at max_length. First encoding with
    a larger temporary bound measures the complete text/schema/image input;
    overlength is refused before any model call. No probabilities or usage are
    invented, and source text/questions are not modified using references.
    """
    request = _request(body, image_paths)
    encoded = engine.helper.encode_record(
        engine.processor.tokenizer, request, max_length=1_000_000_000, processor=engine.processor
    )
    if len(encoded.input_ids) > MAX_LENGTH:
        message = f"complete source input exceeds Clef limit of {MAX_LENGTH} tokens"
        raise ValueError(message)
    response = engine.helper.systemone(engine.model, engine.processor, request, max_length=MAX_LENGTH)
    if not isinstance(response, dict) or set(response.get("answers", {})) != set(body["questions"]):
        message = "native response does not cover the source questions"
        raise ValueError(message)
    return response
