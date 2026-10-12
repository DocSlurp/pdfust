"""Source-only overlapping CPU detector tiles with explicit boundary abstention."""

# Explicit experimental protocols retain heterogeneous source dictionaries.
# ruff: noqa: ANN401, EM101, TRY003, TRY301, PLR2004, PLR0913, PLC0415
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
from typing import Any

from bench.pipeline_layout_detector import MAX_BOXES, MAX_PIXELS, LayoutDetector, _box, _Measure, detector_regions

MAX_FULL_SIDE = 3072
MAX_CALLS = 14


def tile_windows(width: int, height: int, grid: int, *, overlap: float = 0.12) -> list[list[int]]:
    """Cover the full source raster with deterministic overlapping rectangular tiles."""
    if any(type(v) is not int or v < 1 for v in (width, height, grid)) or grid not in (2, 3):
        raise ValueError("Tile dimensions must be positive integers and grid must be two or three")
    if max(width, height) > MAX_FULL_SIDE or not math.isfinite(overlap) or not 0 <= overlap <= 0.5:
        raise ValueError("Full raster or tile overlap exceeds admission")
    windows = []
    for row in range(grid):
        for column in range(grid):
            xpad, ypad = width * overlap / grid / 2, height * overlap / grid / 2
            box = [
                max(0, math.floor(column * width / grid - xpad)),
                max(0, math.floor(row * height / grid - ypad)),
                min(width, math.ceil((column + 1) * width / grid + xpad)),
                min(height, math.ceil((row + 1) * height / grid + ypad)),
            ]
            if (box[2] - box[0]) * (box[3] - box[1]) > MAX_PIXELS:
                raise ValueError("Complete tile exceeds detector pixel admission")
            windows.append(box)
    return windows


def _iou(a: list[float], b: list[float]) -> float:
    width, height = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = width * height
    return intersection / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection)


def class_nms(boxes: list[dict[str, Any]], *, threshold: float = 0.5) -> list[dict[str, Any]]:
    """Retain confidence-ranked class-aware proposals; preserve all raw boxes separately."""
    if len(boxes) > MAX_CALLS * MAX_BOXES or not math.isfinite(threshold) or not 0 < threshold <= 1:
        raise ValueError("Invalid multiscale proposal admission or NMS threshold")
    for box in boxes:
        _box(box["bbox"])
        confidence = box["confidence"]
        if not isinstance(box["label"], str) or type(confidence) not in (int, float):
            raise ValueError("Invalid multiscale label or confidence")
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Invalid multiscale confidence")
    ordered = sorted(enumerate(boxes), key=lambda item: (-item[1]["confidence"], item[0]))
    retained: list[dict[str, Any]] = []
    for _, box in ordered:
        if not any(
            box["label"].casefold() == old["label"].casefold() and _iou(box["bbox"], old["bbox"]) > threshold
            for old in retained
        ):
            retained.append(dict(box))
            if len(retained) > MAX_BOXES:
                raise ValueError("Complete multiscale proposals exceed detector admission")
    return retained


def multiscale(
    detector: LayoutDetector,
    image: bytes,
    *,
    viewport: list[float],
    grids: tuple[int, ...] = (2, 3),
    overlap: float = 0.12,
    whole_side: int = 1024,
) -> dict[str, Any]:
    """Run whole-page and fixed source tiles without reference-informed cropping."""
    from PIL import Image

    display = _box(viewport)
    if grids not in ((2,), (3,), (2, 3)) or type(whole_side) is not int or not 1 <= whole_side <= 1600:
        raise ValueError("Invalid fixed multiscale configuration")
    with _Measure() as parent_measurement, Image.open(io.BytesIO(image)) as original:
        width, height = original.size
        if min(width, height) < 3 or max(width, height) > MAX_FULL_SIDE:
            raise ValueError("Full source raster exceeds multiscale admission")
        original.load()
        rgba = original.convert("RGBA")
        raster = Image.new("RGB", original.size, "white")
        raster.paste(rgba, mask=rgba.getchannel("A"))
        whole = raster.copy()
        whole.thumbnail((whole_side, whole_side))
        body = io.BytesIO()
        whole.save(body, format="PNG")
        result = detector.detect(body.getvalue(), viewport=display)
        result.update(call_id="whole", tile_pixel_bbox=[0, 0, width, height], tile_viewport=display)
        for box in result["boxes"]:
            box.update(call_id="whole", tile_viewport=display, tile_boundary_risk=False)
        calls = [result]
        for grid in grids:
            for index, window in enumerate(tile_windows(width, height, grid, overlap=overlap)):
                tile_viewport = [
                    display[0] + window[0] / width * (display[2] - display[0]),
                    display[1] + window[1] / height * (display[3] - display[1]),
                    display[0] + window[2] / width * (display[2] - display[0]),
                    display[1] + window[3] / height * (display[3] - display[1]),
                ]
                body = io.BytesIO()
                raster.crop((window[0], window[1], window[2], window[3])).save(body, format="PNG")
                result = detector.detect(body.getvalue(), viewport=tile_viewport)
                call_id = f"g{grid}-t{index}"
                result.update(call_id=call_id, tile_pixel_bbox=window, tile_viewport=tile_viewport)
                for box in result["boxes"]:
                    normalized = box["normalized_bbox"]
                    # Page exterior is complete source context; interior tile edges are not.
                    risk = (window[0] > 0 and normalized[0] <= 0.02) or (window[1] > 0 and normalized[1] <= 0.02)
                    risk |= (window[2] < width and normalized[2] >= 0.98) or (
                        window[3] < height and normalized[3] >= 0.98
                    )
                    box.update(call_id=call_id, tile_viewport=tile_viewport, tile_boundary_risk=bool(risk))
                calls.append(result)
        raw_boxes = [box for call in calls for box in call["boxes"]]
        selected = class_nms(raw_boxes)
    return {
        "configuration": {
            "grids": list(grids),
            "overlap": overlap,
            "whole_side": whole_side,
            "nms_iou": 0.5,
            "boundary_margin_fraction": 0.02,
            "full_image_size": [width, height],
        },
        "calls": calls,
        "boxes": selected,
        "raw_box_count": len(raw_boxes),
        "parent_metrics": parent_measurement.result,
        "semantic_status": "Source-only multiscale proposals; NMS is not table topology reconstruction",
    }


def tile_regions(page: dict[str, Any], boxes: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    """Partition every source ID once and abstain on tile boundaries or capacity cuts."""
    plan = detector_regions(page, boxes, **kwargs)
    for region in plan["regions"]:
        if "detector" not in region:
            continue
        proposal = boxes[region["detector"]["index"]]
        tile = proposal["tile_viewport"]
        words_cross_tile = any(
            word["bbox"][0] < tile[0]
            or word["bbox"][1] < tile[1]
            or word["bbox"][2] > tile[2]
            or word["bbox"][3] > tile[3]
            for word in region["source"]["words"]
        )
        region["detector"].update(
            call_id=proposal["call_id"],
            tile_viewport=tile,
            tile_boundary_risk=proposal["tile_boundary_risk"],
            source_words_cross_tile=words_cross_tile,
        )
        if proposal["tile_boundary_risk"] or words_cross_tile:
            region.update(context_complete=False, boundary="detector_tile_boundary")
    return plan


def baseline(manifest_path: Path, sources_directory: Path, output: Path) -> dict[str, Any]:
    """Retain a fixed-screen whole/2x2/3x3 CPU comparison with cached source ownership."""
    import pdfust
    from bench.silver import guard_path, sha, write_json

    manifest = json.loads(guard_path(manifest_path).read_bytes())
    if manifest.get("split") != "DEV":
        raise ValueError("Multiscale diagnostic requires explicit DEV sources")
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    with LayoutDetector() as detector:
        initialization = detector.initialization
        for record in manifest["pages"]:
            row: dict[str, Any] = {"id": record["id"], "status": "error"}
            with _Measure() as parent_measurement:
                try:
                    data = guard_path(Path(record["pdf_path"])).read_bytes()
                    if sha(data) != record["pdf_sha256"]:
                        raise ValueError("Frozen source PDF changed")
                    cached = json.loads(guard_path(sources_directory / f"{record['id']}-result.json").read_bytes())
                    if cached["id"] != record["id"]:
                        raise ValueError("Cached source ID does not match frozen page")
                    with pdfust.open(stream=data) as document:
                        page = document[record["page_number"]]
                        if page.rotation:
                            page.set_rotation(0)
                        pixels = page.get_pixmap(
                            scale=(MAX_FULL_SIDE - 1) / max(page.rect.width, page.rect.height),
                            background=(255, 255, 255),
                        ).tobytes()
                        result = multiscale(detector, pixels, viewport=list(page.rect))
                    comparisons = {}
                    for arm, grids in (
                        ("whole", []),
                        ("whole_2x2", [2]),
                        ("whole_3x3", [3]),
                        ("whole_2x2_3x3", [2, 3]),
                    ):
                        calls = [
                            call
                            for call in result["calls"]
                            if call["call_id"] == "whole"
                            or any(call["call_id"].startswith(f"g{grid}-") for grid in grids)
                        ]
                        boxes = class_nms([box for call in calls for box in call["boxes"]])
                        plan = tile_regions(cached["source"], boxes)
                        comparisons[arm] = {
                            "boxes": boxes,
                            "partition": {k: v for k, v in plan.items() if k != "words"},
                            "worker_wall_seconds": sum(call["metrics"]["wall_seconds"] for call in calls),
                            "worker_cpu_seconds": sum(call["metrics"]["cpu_seconds"] for call in calls),
                            "worker_peak_sampled_rss_bytes": max(
                                call["metrics"]["peak_sampled_rss_bytes"] for call in calls
                            ),
                        }
                    row.update(
                        status="ok",
                        detection=result,
                        comparisons=comparisons,
                        source_words=len(cached["source"]["words"]),
                        cached_source_sha256=sha(json.dumps(cached["source"], sort_keys=True).encode()),
                    )
                except Exception as error:
                    row["error_type"] = type(error).__name__
            row["parent_metrics"] = parent_measurement.result
            rows.append(row)
            write_json(output / f"{record['id']}-tiles.json", row)
    report = {
        "schema": 1,
        "source_only": True,
        "manifest_sha256": sha(manifest_path.read_bytes()),
        "initialization": initialization,
        "predictions": rows,
        "measurement_scope": "One serial CPU worker; arm times reuse retained whole/tile calls, not independent runs. "
        "Cached source ownership excludes original OCR/extraction; not complete-pipeline timing.",
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run an explicit fixed-source DEV diagnostic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sources-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline(args.manifest, args.sources_directory, args.output)


if __name__ == "__main__":
    main()
