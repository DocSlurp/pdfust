"""Synthetic source-word occupancy diagrams for matched whole-crop selectors."""

# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import base64
import io
import json
import math
from copy import deepcopy
from typing import Any

from PIL import Image, ImageDraw

from bench import p003_candidate_choice as chooser
from bench.pipeline_repair import _sources
from bench.silver import canonical, sha

EDGES = (128, 400, 512)
STYLES = ("filled", "outline")
NOTICE = (
    "The attached image is a synthetic geometry-only diagram of retained source-word bounding rectangles. "
    "It contains no original source pixels, word glyphs, table rules, detector structures, candidate layouts "
    "or candidate aliases. Every rectangle has the same neutral appearance. White canvas means no drawn "
    "retained word bbox; it is not proof of blank PDF space. Do not infer literal text or table semantics "
    "from occupancy alone. Use unresolved when the supplied alternatives and word geometry cannot resolve differences."
)


def diagram(
    source: dict[str, Any], source_ids: list[str], viewport: list[float], edge: int, style: str
) -> tuple[str, dict[str, Any]]:
    """Render complete owned word geometry without glyphs or candidate-derived pixels."""
    lookup = _sources(source)
    if (
        len(canonical(source)) > 2 * 1024 * 1024
        or len(source_ids) != len(set(source_ids))
        or set(source_ids) - set(lookup)
        or edge not in EDGES
        or style not in STYLES
        or len(viewport) != 4
        or any(not math.isfinite(v) for v in viewport)
        or viewport[0] >= viewport[2]
        or viewport[1] >= viewport[3]
    ):
        raise ValueError("Invalid complete geometry diagram contract")
    x0, y0, x1, y1 = viewport
    ratio = edge / max(x1 - x0, y1 - y0)
    width, height = max(1, round((x1 - x0) * ratio)), max(1, round((y1 - y0) * ratio))
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    owned = set(source_ids)
    mappings = []
    for word in source["words"]:
        if word["id"] not in owned:
            continue
        b = word["bbox"]
        clipped = [max(x0, b[0]), max(y0, b[1]), min(x1, b[2]), min(y1, b[3])]
        item: dict[str, Any] = {"source_id": word["id"], "global_bbox": b, "clipped_global_bbox": clipped}
        if clipped[0] >= clipped[2] or clipped[1] >= clipped[3]:
            item.update(status="not_drawable", reason="no_positive_bbox_intersection", pixel_bbox=None)
            item["clipped_global_bbox"] = None
        else:
            # Inclusive Pillow rectangles use explicit outward integer coverage, clipped to the canvas.
            pixels = [
                max(0, min(width - 1, math.floor((clipped[0] - x0) * width / (x1 - x0)))),
                max(0, min(height - 1, math.floor((clipped[1] - y0) * height / (y1 - y0)))),
                max(0, min(width - 1, math.ceil((clipped[2] - x0) * width / (x1 - x0)) - 1)),
                max(0, min(height - 1, math.ceil((clipped[3] - y0) * height / (y1 - y0)) - 1)),
            ]
            pixels[2], pixels[3] = max(pixels[0], pixels[2]), max(pixels[1], pixels[3])
            draw.rectangle(
                pixels,
                fill=(96, 96, 96) if style == "filled" else None,
                outline=(96, 96, 96) if style == "outline" else None,
                width=1,
            )
            item.update(status="drawn", pixel_bbox=pixels, bbox_clipped=clipped != b)
        mappings.append(item)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=6, optimize=False)
    encoded = buffer.getvalue()
    metadata = {
        "image_evidence_kind": "synthetic_source_word_geometry_only",
        "source_pixels_supplied": False,
        "source_sha256": sha(canonical(source)),
        "owned_source_ids_sha256": sha(canonical(source_ids)),
        "source_ids": source_ids,
        "source_id_pixel_mapping": mappings,
        "owned_word_count": len(source_ids),
        "drawn_word_count": sum(m["status"] == "drawn" for m in mappings),
        "not_drawable_owned_word_count": sum(m["status"] != "drawn" for m in mappings),
        "owned_word_geometry_omitted_count": 0,
        "other_page_words_omitted_count": len(source["words"]) - len(source_ids),
        "source_word_text_in_image": False,
        "candidate_dependent_marks": False,
        "image_viewport": viewport,
        "image_edge": edge,
        "image_size": [width, height],
        "image_style": style,
        "outline_width_pixels": 1 if style == "outline" else None,
        "foreground_rgb": [96, 96, 96],
        "background_rgb": [255, 255, 255],
        "image_codec": "PNG",
        "png_sample_bit_depth": 8,
        "png_color_type": 2,
        "png_compression_level": 6,
        "image_bytes": len(encoded),
        "image_sha256": sha(encoded),
        "rasterization": "global display-point geometry; outward integer coverage; no resampling or source raster",
        "notice": NOTICE,
    }
    return "data:image/png;base64," + base64.b64encode(encoded).decode(), metadata


def request(pool: chooser.Pool, model: str, url: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Preserve alternatives/criteria while explicitly changing the image-evidence treatment."""
    original = chooser.request(pool, model, url)
    body = deepcopy(original)
    evidence = json.loads(body["state"][0])
    evidence["image_evidence_kind"] = "synthetic_source_word_geometry_only"
    evidence["image_evidence_notice"] = NOTICE
    text = chooser.canonical_json(evidence)
    metadata = {
        "candidate_pool_sha256": pool.snapshot_sha256,
        "original_comparison_sha256": sha(original["state"][0].encode()),
        "evidence_sha256": sha(text),
        "evidence_utf8_bytes": len(text),
        "candidate_choices_unchanged": True,
        "alias_seed_unchanged": True,
        "criteria_unchanged": True,
        "instruction_treatment_changed": True,
        "pure_pixel_causal_control": False,
        "evidence_omitted_bytes": 0,
        "max_evidence_bytes": chooser.MAX_COMPARISON_BYTES,
    }
    if len(text) > chooser.MAX_COMPARISON_BYTES:
        return None, {
            **metadata,
            "status": "no_question_refusal",
            "reason": "complete_comparison_and_notice_exceed128KiB",
        }
    body["state"][0] = text.decode()
    body["questions"]["q0"]["instructions"] = (
        NOTICE
        + " "
        + chooser.SYSTEM.replace(
            "against the attached source crop", "using the attached synthetic source-word geometry diagram"
        )
    )
    return body, {**metadata, "status": "prepared"}
