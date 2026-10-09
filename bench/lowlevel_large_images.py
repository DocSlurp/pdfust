"""CPU-only L015/L016 fresh source-crop rendering; no provider calls."""

# ruff: noqa: PLR2004, PLR0913, C901
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import random
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from PIL import Image
from PIL import __version__ as pillow_version

import pylopdf
from bench.decision_gateway_vision import translate, validate_wire
from bench.lowlevel_control_freeze import begin, encoded_body, finish
from bench.lowlevel_images import MODELS, non_image_bytes
from bench.lowlevel_packets import _digest, _file
from bench.silver import guard_path

SIZES = (512, 768, 1024)
MODES = ("rgb", "gray", "lowbit")
ARMS = tuple(f"fresh-{mode}-{edge}" for mode in MODES for edge in SIZES)
GATEWAY_MODELS = ("liquid/d1",)
BODY_CAP = 200_000
TEXT_CAP = 1800
RASTER_PIXELS = 32_000_000


def raster(source: Path, bbox: list[float], edge: int) -> tuple[Image.Image, dict[str, Any]]:
    """Render at source resolution sufficient for the requested crop, never upscale PNGs."""
    if edge not in SIZES or len(bbox) != 4 or not all(math.isfinite(v) for v in bbox):
        msg = "Unadmitted crop or size"
        raise ValueError(msg)
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if min(width, height) <= 0:
        msg = "Empty crop"
        raise ValueError(msg)
    # One extra source pixel avoids outward clip rounding requiring an upscale.
    scale = (edge + 2) / max(width, height)
    with pylopdf.Document(source) as document:
        page = document[0]
        rect = page.rect
        if math.ceil(rect.width * scale) * math.ceil(rect.height * scale) > RASTER_PIXELS:
            msg = "Fresh render exceeds bounded full-page pixel admission"
            raise ValueError(msg)
        pix = page.get_pixmap(scale=scale, clip=bbox)
        rgba = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    rgb = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")
    target = (max(1, round(width / max(width, height) * edge)), max(1, round(height / max(width, height) * edge)))
    if rgb.width < target[0] or rgb.height < target[1]:
        msg = "Fresh crop would require upscaling"
        raise ValueError(msg)
    rendered = list(rgb.size)
    rgb = rgb.resize(target, Image.Resampling.LANCZOS)
    return rgb, {
        "bbox": bbox,
        "render_scale": scale,
        "render_pixels": rendered,
        "render_display_bbox": [
            math.floor(bbox[0] * scale) / scale,
            math.floor(bbox[1] * scale) / scale,
            math.ceil(bbox[2] * scale) / scale,
            math.ceil(bbox[3] * scale) / scale,
        ],
        "requested_edge": edge,
        "width": target[0],
        "height": target[1],
        "source": "fresh source PDF page 0 crop; outward pixel clipping before downsample",
        "pixels": list(target),
        "pixel_area": target[0] * target[1],
        "resampling": "fresh hayro crop at (edge+2)/longest bbox edge; Pillow LANCZOS downsample",
    }


def variant(rgb: Image.Image, mode: str) -> bytes:
    """Encode independent RGB8, gray8 or four-level two-bit PNG treatments."""
    if mode not in MODES:
        msg = "Unadmitted color treatment"
        raise ValueError(msg)
    bitmap = rgb if mode == "rgb" else rgb.convert("L")
    if mode == "lowbit":
        bitmap = bitmap.point([(value * 3 + 127) // 255 for value in range(256)]).convert("P")
        bitmap.putpalette([channel for i in range(256) for channel in [min(i, 3) * 85] * 3])
    output = io.BytesIO()
    bitmap.save(output, format="PNG", optimize=True, **({"bits": 2} if mode == "lowbit" else {}))
    return output.getvalue()


def body(
    template: dict[str, Any], model: str, png: bytes, image: dict[str, Any], mode: str, *, gateway: bool = False
) -> dict[str, Any]:
    """Preserve source criteria and translate only the provider image transport."""
    result = deepcopy(template)
    result["model"] = model
    state = json.loads(result["state"][0])
    state.update(image_bbox=image["bbox"], image_pixels=image["pixels"], image_mode=mode, png_bit_depth=png[24])
    text = json.dumps(state, separators=(",", ":"))
    image_part: dict[str, Any] = {
        "type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}
    }
    result["state"] = [text, image_part]
    if non_image_bytes(result) > TEXT_CAP:
        msg = "Fresh image source text exceeds 1800 bytes"
        raise ValueError(msg)
    if gateway:
        result.update(state=text, images=[image_part["image_url"]["url"]])
        result = translate(result)
        validate_wire(result, BODY_CAP)
        text_only = deepcopy(result)
        text_only["input"][0]["content"] = text_only["input"][0]["content"][:1]
        if len(encoded_body(text_only)) > TEXT_CAP:
            msg = "Native wire source text exceeds 1800 bytes"
            raise ValueError(msg)
    if len(encoded_body(result)) > BODY_CAP:
        msg = "Fresh image request exceeds body admission"
        raise ValueError(msg)
    return result


def text_bytes(request: dict[str, Any]) -> int:
    """Count serialized actual-wire text and questions after removing image parts."""
    if "input" not in request:
        return non_image_bytes(request)
    packet = deepcopy(request)
    packet["input"][0]["content"] = packet["input"][0]["content"][:1]
    return len(encoded_body(packet))


def source_templates(parent: Path, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Reuse exact historical focus chunks/questions; bound optional words once globally."""
    templates = {}
    for page in manifest["pages"]:
        records = [
            r
            for r in manifest["records"]
            if r["page_ids"] == [page["id"]] and r["arm"] == "focus-rgb-512" and r["model"] == MODELS[0]
        ]
        if len(records) != 1:
            msg = "Parent lacks unique historical focus packet"
            raise ValueError(msg)
        record = records[0]
        raw = _file(parent, record["request"]).read_bytes()
        if _digest(raw) != record["sha256"]:
            msg = "Parent source request changed"
            raise ValueError(msg)
        template = json.loads(raw)
        state = json.loads(template["state"][0])
        state.update(image_pixels=[1024, 1024], image_mode="lowbit", png_bit_depth=2)
        template["state"] = [json.dumps(state, separators=(",", ":"))]
        template["model"] = max((*MODELS, *GATEWAY_MODELS), key=len)
        while non_image_bytes(template) > TEXT_CAP:
            words = state["observations"]["q0"]["nearby_words"]
            if not words:
                msg = "Essential source chunks/questions exceed text admission"
                raise ValueError(msg)
            words.pop()
            template["state"][0] = json.dumps(state, separators=(",", ":"))
        templates[page["id"]] = template
    return templates


def prepare(
    parent: Path,
    directory: Path,
    *,
    gateway: bool = False,
    catalog: Path | None = None,
    image_freeze: Path | None = None,
) -> dict[str, Any]:
    """Freeze all complete source requests before the common helper copies scorer targets."""
    if gateway and image_freeze is None:
        msg = "L016 requires verified L015 image_freeze for exact matched pixels"
        raise ValueError(msg)
    started, cpu = time.perf_counter(), time.process_time()
    parent = guard_path(parent).resolve()
    original_raw = _file(parent, "manifest.json").read_bytes()
    original = json.loads(original_raw)
    if original.get("experiment") != "L006" or original.get("kind") != "focus" or len(original["pages"]) != 24:
        msg = "Requires exact 24-source L006 focus freeze"
        raise ValueError(msg)
    templates = source_templates(parent, original)
    retained_images = {}
    image_manifest = None
    if image_freeze is not None:
        image_freeze = guard_path(image_freeze).resolve()
        image_manifest = verify(image_freeze)
        if image_manifest["experiment"] != "L015" or image_manifest["parent_manifest_sha256"] != _digest(original_raw):
            msg = "Matched images must come from L015 with the exact same source parent"
            raise ValueError(msg)
        retained_images = {(image["id"], image["arm"]): image for image in image_manifest["images"]}
    models = GATEWAY_MODELS if gateway else MODELS
    catalog_raw = guard_path(catalog).read_bytes() if catalog else _file(parent, "catalog-prices.json").read_bytes()
    if not all(model in json.loads(catalog_raw)["prices"] for model in models):
        msg = "Frozen catalog must cover every model"
        raise ValueError(msg)
    directory = begin(parent, directory, original["pages"])
    _file(directory, "catalog-prices.json").write_bytes(catalog_raw)
    records: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    exact: dict[str, str] = {}
    projection_edits = []
    for page in original["pages"]:
        obs = json.loads(_file(directory, page["observation_file"]).read_bytes())
        bbox = obs["images"]["crop512"]["bbox"]
        prior_record = next(
            r
            for r in original["records"]
            if r["page_ids"] == [page["id"]] and r["model"] == MODELS[0] and r["arm"] == "focus-rgb-512"
        )
        prior = json.loads(_file(parent, prior_record["request"]).read_bytes())
        prior_words = json.loads(prior["state"][0])["observations"]["q0"]["nearby_words"]
        kept = json.loads(templates[page["id"]]["state"][0])["observations"]["q0"]["nearby_words"]
        projection_edits.append(
            {
                "id": page["id"],
                "nearby_words_removed": prior_words[len(kept) :],
                "removed_count": len(prior_words) - len(kept),
            }
        )
        for edge in SIZES:
            rgb, metadata = (None, {}) if retained_images else raster(_file(directory, page["source_file"]), bbox, edge)
            for mode in MODES:
                if retained_images:
                    metadata = deepcopy(retained_images[(page["id"], f"fresh-{mode}-{edge}")])
                    png = _file(cast("Path", image_freeze), metadata["file"]).read_bytes()
                else:
                    png = variant(cast("Image.Image", rgb), mode)
                name = f"image-{page['id']}-{mode}-{edge}.png"
                _file(directory, name).write_bytes(png)
                info = {
                    **metadata,
                    "id": page["id"],
                    "arm": f"fresh-{mode}-{edge}",
                    "file": name,
                    "sha256": _digest(png),
                    "png_bytes": len(png),
                    "png_bit_depth": png[24],
                    "mode": mode,
                    "source_file": page["source_file"],
                    "source_sha256": page["source_sha256"],
                    "historical_crop_sha256": obs["images"]["crop512"]["sha256"],
                }
                images.append(info)
                for model in models:
                    request = body(templates[page["id"]], model, png, metadata, mode, gateway=gateway)
                    raw = encoded_body(request)
                    digest = _digest(raw)
                    filename = exact.get(digest, f"request-{len(exact):04d}.json")
                    alias = digest in exact
                    if not alias:
                        _file(directory, filename).write_bytes(raw)
                        exact[digest] = filename
                    records.append(
                        {
                            "request": filename,
                            "sha256": digest,
                            "model": model,
                            "arm": info["arm"],
                            "page_ids": [page["id"]],
                            "body_bytes": len(raw),
                            "exact_body_alias": alias,
                            "image_file": name,
                            "image_sha256": info["sha256"],
                            "pixels": info["pixels"],
                            "pixel_area": info["pixel_area"],
                            "png_bytes": len(png),
                            "width": info["width"],
                            "height": info["height"],
                            "non_image_bytes": text_bytes(request),
                        }
                    )
    random.Random(17516).shuffle(records)  # noqa: S311 - reproducible source schedule.
    manifest = {
        "schema": 1,
        "experiment": "L016" if gateway else "L015",
        "kind": "fresh-focus",
        "gateway": "vercel" if gateway else "openrouter",
        "protocol": "openai-decisions" if gateway else "typesafe",
        "matched_image_directory": str(image_freeze) if image_freeze else None,
        "matched_image_manifest_sha256": _digest(_file(image_freeze, "manifest.json").read_bytes())
        if image_freeze
        else None,
        "models": list(models),
        "arms": list(ARMS),
        "parent_directory": str(parent),
        "parent_manifest_sha256": _digest(original_raw),
        "pages": original["pages"],
        "records": records,
        "images": images,
        "projection_edits": projection_edits,
        "unique_requests": len(exact),
        "catalog_sha256": _digest(catalog_raw),
        "request_settings": {
            "max_body_bytes": BODY_CAP,
            "max_focus_text_bytes": TEXT_CAP,
            "batch_size": 1,
            "max_raster_pixels": RASTER_PIXELS,
        },
        "code_sha256": {"bench/lowlevel_large_images.py": _digest(Path(__file__).read_bytes())},
        "pillow_version": pillow_version,
        "preparation": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": int(
                next(
                    line.split()[1]
                    for line in Path("/proc/self/status").read_text().splitlines()
                    if line.startswith("VmHWM:")
                )
            )
            * 1024,
            "scope": "serial current process counters and Linux VmHWM, no sampling/provider/GPU",
        },
        "scope": (
            "Conditional source-only selectors; fresh512 is a new matched control, not identical historical pixels. "
            "Projection changes prevent an isolated historical L006 comparison. No provider-internal pixel assumptions."
        ),
    }
    return finish(parent, directory, manifest)


def verify(directory: Path) -> dict[str, Any]:  # noqa: PLR0912 - verify every frozen source and native-wire admission.
    """Verify frozen source, raster provenance, complete inventory and exact source bodies."""
    directory = guard_path(directory).resolve()
    manifest = json.loads(_file(directory, "manifest.json").read_bytes())
    gateway = manifest["experiment"] == "L016"
    models = GATEWAY_MODELS if gateway else MODELS
    if gateway and manifest.get("protocol") != "openai-decisions":
        msg = "Native Gateway protocol provenance changed"
        raise ValueError(msg)
    if gateway:
        matched = guard_path(Path(manifest["matched_image_directory"])).resolve()
        if _digest(_file(matched, "manifest.json").read_bytes()) != manifest["matched_image_manifest_sha256"]:
            msg = "Matched L015 image freeze changed"
            raise ValueError(msg)
    if (
        manifest["experiment"] not in ("L015", "L016")
        or manifest["models"] != list(models)
        or manifest["arms"] != list(ARMS)
    ):
        msg = "Fresh image inventory changed"
        raise ValueError(msg)
    parent = guard_path(Path(manifest["parent_directory"])).resolve()
    parent_raw = _file(parent, "manifest.json").read_bytes()
    if _digest(parent_raw) != manifest["parent_manifest_sha256"]:
        msg = "Parent manifest changed"
        raise ValueError(msg)
    original = json.loads(parent_raw)
    if manifest["pages"] != original["pages"]:
        msg = "Source inventory changed"
        raise ValueError(msg)
    templates = source_templates(parent, original)
    if _digest(_file(directory, "catalog-prices.json").read_bytes()) != manifest["catalog_sha256"]:
        msg = "Catalog changed"
        raise ValueError(msg)
    for page in manifest["pages"]:
        for key, hashkey in (("source_file", "source_sha256"), ("observation_file", "observation_sha256")):
            if _digest(_file(directory, page[key]).read_bytes()) != page[hashkey]:
                msg = "Copied source changed"
                raise ValueError(msg)
    images = {(im["id"], im["arm"]): im for im in manifest["images"]}
    seen = set()
    for record in manifest["records"]:
        ident = record["page_ids"][0]
        record_key = (ident, record["model"], record["arm"])
        if record_key in seen or record["model"] not in models:
            msg = "Duplicate or unadmitted request"
            raise ValueError(msg)
        seen.add(record_key)
        info = images[(ident, record["arm"])]
        png = _file(directory, info["file"]).read_bytes()
        raw = _file(directory, record["request"]).read_bytes()
        reconstructed = body(templates[ident], record["model"], png, info, info["mode"], gateway=gateway)
        if gateway:
            validate_wire(reconstructed, BODY_CAP)
            if _file(matched, info["file"]).read_bytes() != png:
                msg = "L016 pixels differ from matched L015"
                raise ValueError(msg)
        if (
            len(raw) != record["body_bytes"]
            or len(png) != info["png_bytes"]
            or png[24] != info["png_bit_depth"]
            or _digest(png) != info["sha256"]
            or record["image_sha256"] != info["sha256"]
            or _digest(raw) != record["sha256"]
            or raw != encoded_body(reconstructed)
        ):
            msg = "Frozen image or request changed"
            raise ValueError(msg)
        with Image.open(io.BytesIO(png)) as bitmap:
            if list(bitmap.size) != info["pixels"] or bitmap.width * bitmap.height != info["pixel_area"]:
                msg = "Actual image dimensions changed"
                raise ValueError(msg)
    expected = {(p["id"], m, a) for p in manifest["pages"] for m in models for a in ARMS}
    if seen != expected or len(images) != len(manifest["pages"]) * len(ARMS):
        msg = "Incomplete fresh image matrix"
        raise ValueError(msg)
    return manifest


def main() -> None:
    """Prepare or verify an offline source freeze."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--gateway", action="store_true")
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--image-freeze", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify(args.directory)
        if args.verify
        else prepare(
            args.parent, args.directory, gateway=args.gateway, catalog=args.catalog, image_freeze=args.image_freeze
        )
    )
    print(
        json.dumps(
            {
                "experiment": result["experiment"],
                "records": len(result["records"]),
                "unique_requests": result["unique_requests"],
            }
        )
    )


if __name__ == "__main__":
    main()
