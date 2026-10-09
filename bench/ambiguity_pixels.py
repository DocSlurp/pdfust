"""Bounded source-only pixel diagnostics for a supplied two-line candidate.

Thresholds are prospective engineering choices, not calibrated probabilities.
Visible separators do not alone prove row identity; pixel-only choice abstains.
No reference, answer, label, dataset or provider client is read by this module.
"""

# ruff: noqa: C901, PLR2004 - bounded pixel/geometry arities.
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

from PIL import Image

SCHEMA = "source-ambiguity-pixels-v1"
EDGE = 640
MAX_IMAGE_PIXELS = 1_048_576
MAX_PAGE_RENDER_PIXELS = 16_000_000
MAX_SOURCE_BYTES = 64 * 1024 * 1024
POLICY: dict[str, Any] = {
    "schema": SCHEMA,
    "render_longest_edge": EDGE,
    "candidate_corridor": "between selector centers; ink-edge gap remains a separate diagnostic",
    "dark_channel_max": 120,
    "white_channel_min": 239,
    "rule_coverage_min": 0.85,
    "rule_thickness_max_em": 0.20,
    "crossing_coverage_min": 0.85,
    "fill_color_delta_min": 24,
    "fill_uniform_fraction_min": 0.85,
    "fill_color_tolerance": 12,
    "border_contact_min": 0.15,
    "minimum_scale_pixels": 4,
    "semantic_policy": "Always unresolved; gap, rule, fill and inset edges do not alone establish row identity.",
}


def _fail(message: str) -> None:
    raise ValueError(message)


def _safe(path: Path) -> Path:
    path = path.resolve()
    parts = path.parts
    if "heldout-silver" in parts or "silver-heldout-v1" in parts:
        _fail("Protected corpus is outside DEV pixel experiment")
    return path


def _box(value: list[float]) -> list[float]:
    if len(value) != 4 or any(
        isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) or abs(x) > 1e9 for x in value
    ):
        _fail("Pixel geometry requires four finite coordinates")
    if value[2] - value[0] < 1e-6 or value[3] - value[1] < 1e-6:
        _fail("Pixel geometry requires positive area")
    return [float(x) for x in value]


def _runs(flags: list[bool]) -> list[tuple[int, int]]:
    result = []
    start = None
    for index, flag in enumerate([*flags, False]):
        if flag and start is None:
            start = index
        elif not flag and start is not None:
            result.append((start, index))
            start = None
    return result


def analyze(
    image: Image.Image,
    target_boxes: list[list[float]],
    *,
    image_bbox: list[float],
    font_scale: float | None = None,
) -> dict[str, Any]:
    """Measure source pixels in display-coordinate ROI, without interpreting text.

    Image bbox must describe actual rendered coverage. No resizing is performed.
    Font scale, when supplied, is measured outside this module; otherwise median
    target-box height is an explicitly labeled geometry surrogate.
    """
    bbox = _box(image_bbox)
    if len(target_boxes) != 2 or image.width * image.height > MAX_IMAGE_PIXELS or min(image.size) < 2:
        _fail("Pixel candidate/image exceeds admission")
    boxes = sorted((_box(box) for box in target_boxes), key=lambda box: box[1] + box[3])
    if any(box[0] < bbox[0] or box[1] < bbox[1] or box[2] > bbox[2] or box[3] > bbox[3] for box in boxes):
        _fail("Target selectors must be inside actual image coverage")
    if font_scale is not None and (
        isinstance(font_scale, bool) or not math.isfinite(font_scale) or font_scale <= 0 or font_scale > 1e6
    ):
        _fail("Font scale must be finite and positive")
    scale = font_scale if font_scale is not None else float(median(box[3] - box[1] for box in boxes))
    sx, sy = image.width / (bbox[2] - bbox[0]), image.height / (bbox[3] - bbox[1])
    font_px = scale * sy
    x0 = max(0, math.floor((min(box[0] for box in boxes) - bbox[0]) * sx))
    x1 = min(image.width, math.ceil((max(box[2] for box in boxes) - bbox[0]) * sx))
    upper, lower = (boxes[0][1] + boxes[0][3]) / 2, (boxes[1][1] + boxes[1][3]) / 2
    gap_top, gap_bottom = boxes[0][3], boxes[1][1]
    overlapping = gap_bottom <= gap_top
    corridor_top, corridor_bottom = upper, lower
    if corridor_bottom <= corridor_top or x1 - x0 < 2:
        return {
            "schema": SCHEMA,
            "features": {"available": False, "normalization_scale": scale},
            "qualifiers": {
                "supports": {"join": [], "split": []},
                "choice": "unresolved",
                "visible_boundary_support": [],
                "alternatives": [],
                "insufficiency": ["no_measurable_horizontal_candidate_corridor"],
            },
            "scope": {
                "image_bbox": bbox,
                "target_boxes": boxes,
                "actual_pixels": list(image.size),
                "boundary_corridor": None,
            },
            "policy_sha256": hashlib.sha256(json.dumps(POLICY, sort_keys=True).encode()).hexdigest(),
        }
    boundary = (corridor_top + corridor_bottom) / 2
    center = min(image.height - 1, max(0, round((boundary - bbox[1]) * sy)))
    radius = max(1, round(font_px * 0.75))
    y0, y1 = max(0, center - radius), min(image.height, center + radius + 1)
    rgba = image.convert("RGBA")
    rgb = Image.alpha_composite(Image.new("RGBA", image.size, "white"), rgba).convert("RGB")
    pixels: Any = rgb.load()
    width = x1 - x0
    rows = [[pixels[x, y] for x in range(x0, x1)] for y in range(y0, y1)]
    dark = [[max(pixel) <= POLICY["dark_channel_max"] for pixel in row] for row in rows]
    white = [sum(min(pixel) >= POLICY["white_channel_min"] for pixel in row) / width for row in rows]
    dark_fraction = [sum(row) / width for row in dark]
    row_colors = [tuple(float(median(pixel[c] for pixel in row)) for c in range(3)) for row in rows]
    uniform = [
        sum(max(abs(pixel[c] - color[c]) for c in range(3)) <= POLICY["fill_color_tolerance"] for pixel in row) / width
        for row, color in zip(rows, row_colors, strict=True)
    ]
    c0 = max(y0, math.floor((corridor_top - bbox[1]) * sy)) - y0
    c1 = min(y1, math.ceil((corridor_bottom - bbox[1]) * sy)) - y0
    corridor = range(max(0, c0), max(c0 + 1, min(len(rows), c1)))
    corridor_indices = [index for index in corridor if index < len(rows)]
    rule_runs = _runs(
        [
            index in corridor_indices and value >= POLICY["rule_coverage_min"]
            for index, value in enumerate(dark_fraction)
        ]
    )
    thin_rules = [(a, b) for a, b in rule_runs if b - a <= max(1, POLICY["rule_thickness_max_em"] * font_px)]
    crossing_runs = _runs(
        [sum(row[x] for row in dark) / len(rows) >= POLICY["crossing_coverage_min"] for x in range(width)]
    )
    narrow_crossings = [(a, b) for a, b in crossing_runs if b - a <= max(1, font_px * 0.20)]
    above = [index for index in range(len(rows)) if y0 + index < center - max(1, round(font_px * 0.15))]
    below = [index for index in range(len(rows)) if y0 + index > center + max(1, round(font_px * 0.15))]
    color_delta, fill_edge = None, False
    if above and below:
        colors = [
            tuple(float(median(row_colors[index][c] for index in side)) for c in range(3)) for side in (above, below)
        ]
        color_delta = max(abs(a - b) for a, b in zip(*colors, strict=True))
        fill_edge = color_delta >= POLICY["fill_color_delta_min"] and all(
            median(uniform[index] for index in side) >= POLICY["fill_uniform_fraction_min"] for side in (above, below)
        )
    # Compare the corridor with actual selector bands, not adjacent blank padding.
    selector_white: list[float] = []
    for box in boxes:
        start = max(0, math.floor((box[1] - bbox[1]) * sy))
        end = min(image.height, math.ceil((box[3] - bbox[1]) * sy))
        selector_white.extend(
            sum(min(pixels[x, y]) >= POLICY["white_channel_min"] for x in range(x0, x1)) / width
            for y in range(start, end)
        )
    within = selector_white
    valley = max((white[index] for index in corridor_indices), default=None)
    edge_fractions = {
        "top": sum(max(pixels[x, 0]) <= POLICY["dark_channel_max"] for x in range(image.width)) / image.width,
        "bottom": sum(max(pixels[x, image.height - 1]) <= POLICY["dark_channel_max"] for x in range(image.width))
        / image.width,
        "left": sum(max(pixels[0, y]) <= POLICY["dark_channel_max"] for y in range(image.height)) / image.height,
        "right": sum(max(pixels[image.width - 1, y]) <= POLICY["dark_channel_max"] for y in range(image.height))
        / image.height,
    }
    insufficient = ["pixel_features_do_not_establish_cell_identity"]
    if font_scale is None:
        insufficient.append("font_scale_unmeasured_selector_height_surrogate")
    if overlapping:
        insufficient.append("overlapping_target_boxes")
    if font_px < POLICY["minimum_scale_pixels"]:
        insufficient.append("small_scale_aliasing")
    if any(value >= POLICY["border_contact_min"] for value in edge_fractions.values()):
        insufficient.append("dark_border_contact_possible_clipped_object")
    visible = []
    if thin_rules:
        visible.append("thin_horizontal_dark_separator")
    if fill_edge:
        visible.append("broad_color_transition")
    features = {
        "available": True,
        "normalization_scale": scale,
        "normalization_source": "font_scale" if font_scale is not None else "selector_height",
        "scale_pixels": font_px,
        "baseline_gap_em": (lower - upper) / scale,
        "selector_ink_gap_em": (gap_bottom - gap_top) / scale,
        "horizontal_whitespace_valley": valley,
        "within_target_band_whitespace": float(median(within)) if within else None,
        "valley_contrast": valley - float(median(within)) if valley is not None and within else None,
        "horizontal_rule_coverage": max((dark_fraction[index] for index in corridor_indices), default=None),
        "thin_horizontal_rule_count": len(thin_rules),
        "vertical_crossing_count": len(narrow_crossings),
        "broad_color_delta": color_delta,
        "broad_color_transition": fill_edge,
        "dark_border_contact": edge_fractions,
    }
    return {
        "schema": SCHEMA,
        "features": features,
        "qualifiers": {
            "supports": {"join": [], "split": []},
            "choice": "unresolved",
            "visible_boundary_support": visible,
            "alternatives": ["cell boundary", "within-cell decoration"],
            "insufficiency": insufficient,
        },
        "scope": {
            "image_bbox": bbox,
            "target_boxes": boxes,
            "boundary_corridor": [
                min(box[0] for box in boxes),
                corridor_top,
                max(box[2] for box in boxes),
                corridor_bottom,
            ],
            "analyzed_pixel_window": [x0, y0, x1, y1],
            "actual_pixels": list(image.size),
        },
        "policy_sha256": hashlib.sha256(json.dumps(POLICY, sort_keys=True).encode()).hexdigest(),
    }


def extract(
    source_pdf: Path,
    target_boxes: list[list[float]],
    *,
    page_index: int = 0,
    scope_bbox: list[float] | None = None,
    font_scale: float | None = None,
) -> dict[str, Any]:
    """Fresh-render a bounded source ROI; retain PDF/crop/render provenance."""
    import pylopdf  # noqa: PLC0415

    source_pdf = _safe(source_pdf)
    if (
        source_pdf.stat().st_size > MAX_SOURCE_BYTES
        or isinstance(page_index, bool)
        or not isinstance(page_index, int)
        or page_index < 0
    ):
        _fail("Source PDF/page exceeds admission")
    if len(target_boxes) != 2:
        _fail("Pixel extractor requires two selectors")
    boxes = [_box(box) for box in target_boxes]
    with pylopdf.Document(source_pdf, limits=pylopdf.DocumentLimits.web()) as document:
        page = document[page_index]
        rect = page.rect
        bbox = (
            _box(scope_bbox)
            if scope_bbox is not None
            else [
                min(box[0] for box in boxes),
                min(box[1] for box in boxes),
                max(box[2] for box in boxes),
                max(box[3] for box in boxes),
            ]
        )
        if bbox[0] < rect.x0 or bbox[1] < rect.y0 or bbox[2] > rect.x1 or bbox[3] > rect.y1:
            _fail("ROI must be inside display page")
        scale = EDGE / max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        if math.ceil(rect.width * scale) * math.ceil(rect.height * scale) > MAX_PAGE_RENDER_PIXELS:
            _fail("Underlying full-page render exceeds admission")
        pix = page.get_pixmap(scale=scale, clip=bbox)
        image = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
        actual_bbox = [
            math.floor(bbox[0] * scale) / scale,
            math.floor(bbox[1] * scale) / scale,
            math.ceil(bbox[2] * scale) / scale,
            math.ceil(bbox[3] * scale) / scale,
        ]
    result = analyze(image, boxes, image_bbox=actual_bbox, font_scale=font_scale)
    result["scope"].update(page_index=page_index, scope_bbox=bbox, render_scale=scale)
    with source_pdf.open("rb") as stream:
        source_bytes = stream.read(MAX_SOURCE_BYTES + 1)
    if len(source_bytes) > MAX_SOURCE_BYTES:
        _fail("Source PDF grew beyond admission")
    result["provenance"] = {
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "rgba_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
        "pylopdf_version": pylopdf.__version__,
        "policy": POLICY,
    }
    return result


def main() -> None:
    """Freeze one source-only descriptor without opening references."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--target-boxes", required=True, help="JSON array of two display-coordinate boxes")
    parser.add_argument("--scope-bbox", help="JSON display-coordinate ROI")
    parser.add_argument("--font-scale", type=float)
    parser.add_argument("--page-index", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = extract(
        args.pdf,
        json.loads(args.target_boxes),
        page_index=args.page_index,
        scope_bbox=json.loads(args.scope_bbox) if args.scope_bbox else None,
        font_scale=args.font_scale,
    )
    output = _safe(args.output)
    with output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, allow_nan=False, sort_keys=True)


if __name__ == "__main__":
    main()
