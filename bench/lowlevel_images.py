"""L006 retained-crop image factors with bounded target-local source packets."""

# ruff: noqa: PLR2004
from __future__ import annotations

import argparse
import base64
import io
import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import __version__ as pillow_version

from bench.lowlevel_compact import compact, encoded
from bench.lowlevel_control_freeze import begin, finish, sources, verify_control
from bench.lowlevel_evidence import MODELS as SOURCE_MODELS
from bench.lowlevel_evidence import request as original_request
from bench.lowlevel_packets import _digest, _file, _write
from bench.lowlevel_prompts import transform
from bench.silver import guard_path

EXPERIMENT = "L006"
MODELS = (
    "perplexity/pplx-decider-v1.1-27b",
    "openai/gpt-6-luna-decisions",
    "cloudflare/clef-flash",
    "cloudflare/clef",
)
RICH_MODELS = MODELS[:2]
SIZES = (64, 128, 256, 400, 500, 512)
MODES = ("rgb", "gray", "lowbit")
MAX_BODY_BYTES = 200_000
MAX_FOCUS_TEXT_BYTES = 1800


def arms(kind: str) -> tuple[str, ...]:
    """Declare the complete size/color-factor grid for one evidence scope."""
    if kind not in ("focus", "rich"):
        message = "L006 kind must be focus or rich"
        raise ValueError(message)
    return tuple(f"{kind}-{mode}-{size}" for mode in MODES for size in SIZES)


def image_variant(observation: dict[str, Any], *, edge: int, mode: str) -> dict[str, Any]:
    """Downsample retained crop512; preserve transforms and encode only PNG.

    RGB/gray resizing and two-bit quantization are deliberate pixel-information
    changes. PNG encoding is lossless; this is not a claim of lossless resizing.
    """
    if edge not in SIZES or mode not in MODES:
        message = "L006 image variant is unadmitted"
        raise ValueError(message)
    source = observation["images"]["crop512"]
    raw = base64.b64decode(source["png_base64"], validate=True)
    if _digest(raw) != source["sha256"]:
        message = "L006 retained source crop hash differs"
        raise ValueError(message)
    with Image.open(io.BytesIO(raw)) as original:
        if (
            original.format != "PNG"
            or max(original.size) != 512
            or original.width * original.height > 512 * 512
            or list(original.size) != source["pixels"]
        ):
            message = "L006 retained crop is not the admitted 512-edge PNG"
            raise ValueError(message)
        rgba = original.convert("RGBA")
        rgb = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")
    ratio = edge / max(rgb.size)
    resized = rgb.resize(
        (max(1, round(rgb.width * ratio)), max(1, round(rgb.height * ratio))), Image.Resampling.LANCZOS
    )
    bitmap = resized if mode == "rgb" else resized.convert("L")
    if mode == "lowbit":
        bitmap = bitmap.point([(value * 3 + 127) // 255 for value in range(256)]).convert("P")
        bitmap.putpalette([channel for index in range(256) for channel in [min(index, 3) * 85] * 3])
    output = io.BytesIO()
    if mode == "lowbit":
        bitmap.save(output, format="PNG", optimize=True, bits=2)
    else:
        bitmap.save(output, format="PNG", optimize=True)
    png = output.getvalue()
    return {
        "pixels": list(bitmap.size),
        "bbox": deepcopy(source["bbox"]),
        "png_base64": base64.b64encode(png).decode(),
        "sha256": _digest(png),
        "source_crop_sha256": source["sha256"],
        "source_pixels": source["pixels"],
        "resampling": "Pillow LANCZOS from retained crop512, after white compositing",
        "mode": mode,
        "png_bit_depth": png[24],
        "quantization": "four grayscale levels 0/85/170/255; two-bit palette PNG" if mode == "lowbit" else None,
    }


def non_image_bytes(body: dict[str, Any]) -> int:
    """Count all serialized source text and question criteria, excluding data URLs."""
    text_only = deepcopy(body)
    text_only["state"] = [
        part for part in body["state"] if not isinstance(part, dict) or part.get("type") != "image_url"
    ]
    return len(encoded(text_only))


def _body(observation: dict[str, Any], model: str, arm: str, image: dict[str, Any]) -> dict[str, Any]:
    kind = arm.split("-", 1)[0]
    source = transform(original_request([observation], SOURCE_MODELS[0], "canonical"), [observation], "both")
    projected = source["state"]["observations"]["q0"]
    question = source["questions"]["q0"]
    if kind == "rich":
        state = compact(projected)
    else:
        state = {
            "task": projected["task"],
            "target_boxes": projected["target_boxes"],
            "chunks": projected["chunks"],
            "nearby_words": [],
        }
    image_info = {
        "image_bbox": image["bbox"],
        "image_pixels": image["pixels"],
        "image_mode": image["mode"],
        "png_bit_depth": image["png_bit_depth"],
    }

    def assemble() -> dict[str, Any]:
        return {
            "model": model,
            "state": [
                json.dumps({"observations": {"q0": state}, **image_info}, separators=(",", ":")),
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image["png_base64"]}},
            ],
            "questions": {"q0": deepcopy(question)},
        }

    body = assemble()
    if kind == "focus":

        def budget(candidate: dict[str, Any]) -> int:
            conservative = deepcopy(candidate)
            conservative["model"] = max(MODELS, key=len)
            state_text = json.loads(conservative["state"][0])
            state_text["image_pixels"] = [512, 512]
            state_text["image_mode"] = "lowbit"
            conservative["state"][0] = json.dumps(state_text, separators=(",", ":"))
            return non_image_bytes(conservative)

        if budget(body) > MAX_FOCUS_TEXT_BYTES:
            message = "L006 essential source chunks/questions exceed focus text budget"
            raise ValueError(message)
        boxes = projected["target_boxes"]
        center_x = sum(box[0] + box[2] for box in boxes) / 4
        top = min(box[1] for box in boxes)
        # Source-only deterministic proximity, with geometry tie-breakers. Targets
        # already appear verbatim as chunks; nearby source words are optional.
        nearby = sorted(
            observation["words"],
            key=lambda word: (
                abs(word["bbox"][3] - top) + abs((word["bbox"][0] + word["bbox"][2]) / 2 - center_x) * 0.1,
                word["bbox"],
                word["text"],
            ),
        )
        for word in nearby[:8]:
            state["nearby_words"].append(deepcopy(word))
            candidate = assemble()
            if budget(candidate) <= MAX_FOCUS_TEXT_BYTES:
                body = candidate
            else:
                state["nearby_words"].pop()
    if len(encoded(body)) > MAX_BODY_BYTES:
        message = "L006 complete image body exceeds byte admission"
        raise ValueError(message)
    return body


def request(observations: list[dict[str, Any]], model: str, arm: str) -> dict[str, Any]:
    """Build matched source criteria plus a deterministic retained-crop variant."""
    if len(observations) != 1:
        message = "L006 accepts singleton observations only"
        raise ValueError(message)
    kind, mode, size = arm.split("-")
    if arm not in arms(kind) or model not in (MODELS if kind == "focus" else RICH_MODELS):
        message = "L006 model or arm is unadmitted"
        raise ValueError(message)
    return _body(observations[0], model, arm, image_variant(observations[0], edge=int(size), mode=mode))


def prepare(parent: Path, directory: Path, *, kind: str = "focus", catalog: Path | None = None) -> dict[str, Any]:
    """Select pixel representatives before labels; freeze all image factors."""
    declared_arms = arms(kind)
    models = MODELS if kind == "focus" else RICH_MODELS
    parent, original, observations = sources(parent)
    parent_hash = _digest(_file(parent, "manifest.json").read_bytes())
    representatives: dict[str, dict[str, Any]] = {}
    for page in sorted(original["pages"], key=lambda page: page["id"]):
        representatives.setdefault(observations[page["id"]]["pixel_sha256"], page)
    pages = sorted(representatives.values(), key=lambda page: page["id"])
    pricing_path = _file(parent, "catalog-prices.json") if catalog is None else guard_path(catalog).resolve()
    pricing = pricing_path.read_bytes()
    if not all(model in json.loads(pricing).get("prices", {}) for model in models):
        message = "L006 catalog lacks declared model rates; pass the complete retained --catalog"
        raise ValueError(message)
    directory = begin(parent, directory, pages)
    _file(directory, "catalog-prices.json").write_bytes(pricing)
    records: list[dict[str, Any]] = []
    for page in pages:
        observation = observations[page["id"]]
        for arm in declared_arms:
            _, mode, edge = arm.split("-")
            image = image_variant(observation, edge=int(edge), mode=mode)
            for model in models:
                body = _body(observation, model, arm, image)
                name = f"request-{len(records):04d}.json"
                records.append(
                    {
                        "request": name,
                        "sha256": _write(_file(directory, name), body),
                        "model": model,
                        "arm": arm,
                        "page_ids": [page["id"]],
                        "body_bytes": len(encoded(body)),
                        "non_image_bytes": non_image_bytes(body),
                        "source_crop_sha256": image["source_crop_sha256"],
                        "image_sha256": image["sha256"],
                        "pixels": image["pixels"],
                    }
                )
    random.Random(17446).shuffle(records)  # noqa: S311 - fixed source-factor schedule.
    manifest = {
        "schema": 1,
        "experiment": EXPERIMENT,
        "kind": kind,
        "parent_directory": str(parent),
        "parent_manifest_sha256": parent_hash,
        "models": list(models),
        "arms": list(declared_arms),
        "pages": pages,
        "records": records,
        "catalog_sha256": _digest(pricing),
        "catalog_source": str(pricing_path),
        "selection": (
            "One lexicographically smallest source ID per complete white-composited "
            "page pixel_sha256; no target labels read"
        ),
        "request_settings": {
            "max_body_bytes": MAX_BODY_BYTES,
            "batch_size": 1,
            "max_focus_text_bytes": MAX_FOCUS_TEXT_BYTES,
            "schedule_seed": 17446,
        },
        "image_provenance": {
            "base": "retained crop512 PNG",
            "sizes": list(SIZES),
            "modes": list(MODES),
            "resampling": "LANCZOS",
            "pillow": pillow_version,
            "native_render_claim": False,
            "lowbit": "four grayscale levels; palette PNG bits=2",
        },
        "prompt_factor": "resolved singleton criteria; focus source projection or rich compactcanonical",
        "scope": (
            "Target-local focus input shared by all four OpenRouter image models; "
            "optional rich comparison only PPLX/Luna. Gateway models excluded."
        ),
        "code_sha256": {
            f"bench/{name}": _digest(Path(__file__).with_name(name).read_bytes())
            for name in (
                "lowlevel_images.py",
                "lowlevel_control_freeze.py",
                "lowlevel_compact.py",
                "lowlevel_prompts.py",
            )
        },
    }
    return finish(parent, directory, manifest, selected=True)


def verify(directory: Path) -> dict[str, Any]:
    """Reconstruct every PNG/body, source representative and focus byte bound."""
    manifest = json.loads(_file(guard_path(directory).resolve(), "manifest.json").read_bytes())
    kind = manifest["kind"]
    result = verify_control(
        directory,
        experiment=EXPERIMENT,
        models=MODELS if kind == "focus" else RICH_MODELS,
        arms=arms(kind),
        builder=request,
        max_bytes=MAX_BODY_BYTES,
        selected=True,
    )
    _, original, observations = sources(Path(result["parent_directory"]))
    representatives: dict[str, dict[str, Any]] = {}
    for page in sorted(original["pages"], key=lambda page: page["id"]):
        representatives.setdefault(observations[page["id"]]["pixel_sha256"], page)
    if result["pages"] != sorted(representatives.values(), key=lambda page: page["id"]):
        message = "L006 representative inventory differs from source-only selection"
        raise ValueError(message)
    for record in result["records"]:
        body = json.loads(_file(directory, record["request"]).read_bytes())
        if non_image_bytes(body) != record["non_image_bytes"] or (
            kind == "focus" and record["non_image_bytes"] > MAX_FOCUS_TEXT_BYTES
        ):
            message = "L006 focus byte count differs from frozen complete text"
            raise ValueError(message)
        image = base64.b64decode(body["state"][1]["image_url"]["url"].split(",", 1)[1], validate=True)
        if _digest(image) != record["image_sha256"]:
            message = "L006 image hash differs from frozen image"
            raise ValueError(message)
        source = observations[record["page_ids"][0]]["images"]["crop512"]
        with Image.open(io.BytesIO(image)) as raster:
            if source["sha256"] != record["source_crop_sha256"] or list(raster.size) != record["pixels"]:
                message = "L006 image source transform metadata differs"
                raise ValueError(message)
    return result


def main() -> None:
    """Prepare or verify image factors without provider calls or credentials."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--kind", choices=("focus", "rich"), default="focus")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        manifest = verify(args.directory)
    else:
        if args.parent is None:
            parser.error("--parent is required")
        manifest = prepare(args.parent, args.directory, kind=args.kind, catalog=args.catalog)
    print(
        json.dumps(
            {
                "experiment": EXPERIMENT,
                "kind": manifest["kind"],
                "pages": len(manifest["pages"]),
                "requests": len(manifest["records"]),
            }
        )
    )


if __name__ == "__main__":
    main()
