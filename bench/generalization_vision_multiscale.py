"""Opt-in fixed whole/2x2 CPU proposals for unchanged strict crop transcription."""

# Retained experiment dictionaries contain heterogeneous JSON evidence.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, PLR2004, C901, PLR0912, TRY301
from __future__ import annotations

import argparse
import io
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import generalization_vision_regions as regions
from bench import generalization_vision_run as vision
from bench.pipeline_layout_detector import MAX_BOXES, _box
from bench.pipeline_layout_fusion import THRESHOLDS, fuse
from bench.pipeline_layout_tiles import tile_windows
from bench.silver import guard_path, sha, write_json

RULES = {
    "version": 1,
    "source_render_edge_cap": 3072,
    "render_scale_numerator": 3071,
    "whole_side": 1536,
    "grid": 2,
    "overlap": 0.12,
    "fusion": "larger_containment",
    "fusion_thresholds": dict(THRESHOLDS),
    "boundary_margin_fraction": 0.02,
    "maximum_calls": 5,
    "preliminary_nms": False,
    "crop_path": "Unchanged vision_regions: original PDF, 4096 render cap, JPEG90/1024 crops",
}
CALL_IDS = ("whole", "g2-t0", "g2-t1", "g2-t2", "g2-t3")


def _windows(size: list[int], viewport: list[float]) -> list[tuple[list[int], list[float]]]:
    if not isinstance(size, list) or len(size) != 2 or any(type(v) is not int or v < 3 for v in size):
        raise ValueError("Multiscale image dimensions must be admitted integers")
    width, height = size
    _box(viewport)
    windows = [[0, 0, width, height], *tile_windows(width, height, 2, overlap=0.12)]
    return [
        (
            window,
            [
                viewport[0] + window[0] / width * (viewport[2] - viewport[0]),
                viewport[1] + window[1] / height * (viewport[3] - viewport[1]),
                viewport[0] + window[2] / width * (viewport[2] - viewport[0]),
                viewport[1] + window[3] / height * (viewport[3] - viewport[1]),
            ],
        )
        for window in windows
    ]


def replay(raw_calls: list[dict[str, Any]], viewport: list[float], full_image_size: list[int]) -> dict[str, Any]:
    """Map every fixed raw CPU call exactly, then fuse all proposals without NMS."""
    expected = _windows(full_image_size, viewport)
    if not isinstance(raw_calls, list) or len(raw_calls) != 5:
        raise ValueError("Multiscale replay requires all five raw responses")
    calls, boxes = [], []
    for index, (raw, (window, display)) in enumerate(zip(raw_calls, expected, strict=True)):
        if raw.get("call_id") != CALL_IDS[index] or raw.get("status") != "ok":
            raise ValueError("Multiscale raw call order or success is invalid")
        if raw.get("tile_pixel_bbox") != window or raw.get("viewport") != display:
            raise ValueError("Raw detector source window or viewport changed")
        result = deepcopy(raw["result"])
        if result.get("type") != "result" or result.get("device") != "cpu" or result.get("viewport") != display:
            raise ValueError("Multiscale requires complete CPU detector responses")
        size = result.get("image_size")
        if not isinstance(size, list) or len(size) != 2 or any(type(v) is not int or v < 1 for v in size):
            raise ValueError("Invalid detector response image dimensions")
        if raw.get("image", {}).get("image_size") != size:
            raise ValueError("Detector response dimensions differ from submitted raster")
        if index and size != [window[2] - window[0], window[3] - window[1]]:
            raise ValueError("Tile raster dimensions differ from exact source window")
        if not index and (
            max(size) != min(1536, max(full_image_size))
            or abs(size[0] / size[1] - full_image_size[0] / full_image_size[1]) > 2 / min(size)
        ):
            raise ValueError("Whole detector raster differs from fixed aspect-preserving thumbnail")
        proposals = result.get("boxes")
        if not isinstance(proposals, list) or len(proposals) > MAX_BOXES:
            raise ValueError("Raw detector proposal admission exceeded")
        for box in proposals:
            pixel = _box(box["pixel_bbox"])
            if pixel[0] < 0 or pixel[1] < 0 or pixel[2] > size[0] or pixel[3] > size[1]:
                raise ValueError("Pixel proposal exceeds submitted raster")
            normalized = [pixel[0] / size[0], pixel[1] / size[1], pixel[2] / size[0], pixel[3] / size[1]]
            mapped = [
                display[0] + normalized[0] * (display[2] - display[0]),
                display[1] + normalized[1] * (display[3] - display[1]),
                display[0] + normalized[2] * (display[2] - display[0]),
                display[1] + normalized[3] * (display[3] - display[1]),
            ]
            if box.get("normalized_bbox") != normalized or box.get("bbox") != mapped:
                raise ValueError("Retained detector mapping differs from exact pixel-to-display transform")
            risk = bool(
                index
                and (
                    (window[0] > 0 and normalized[0] <= 0.02)
                    or (window[1] > 0 and normalized[1] <= 0.02)
                    or (window[2] < full_image_size[0] and normalized[2] >= 0.98)
                    or (window[3] < full_image_size[1] and normalized[3] >= 0.98)
                )
            )
            box.update(call_id=CALL_IDS[index], tile_viewport=display, tile_boundary_risk=risk)
            boxes.append(box)
        result.update(call_id=CALL_IDS[index], tile_pixel_bbox=window, tile_viewport=display)
        calls.append(result)
    fusion = fuse(boxes, viewport, arm="larger_containment")
    return {
        "type": "result",
        "device": "cpu",
        "viewport": list(viewport),
        "boxes": fusion["boxes"],
        "calls": calls,
        "fusion": fusion,
        "configuration": deepcopy(RULES),
        "raw_box_count": len(boxes),
    }


class MultiscaleDetector:
    """One-page wrapper preserving raw detection before any geometry fusion."""

    def __init__(self, detector: Any, source_image: bytes, viewport: list[float]) -> None:
        """Bind one unchanged source raster and an initialized persistent CPU detector."""
        self.detector, self.source_image, self.viewport = detector, source_image, viewport
        self.raw_calls: list[dict[str, Any]] = []
        self.called = False
        self.fused: dict[str, Any] | None = None
        self.received_base_image: dict[str, Any] | None = None

    def detect(self, image_bytes: bytes, *, viewport: list[float]) -> dict[str, Any]:
        """Replace only proposal acquisition; the crop transcription caller is unchanged."""
        from PIL import Image

        if self.called or viewport != self.viewport:
            raise ValueError("Multiscale wrapper requires one matching original page viewport")
        self.called = True
        self.received_base_image = {"sha256": sha(image_bytes), "bytes": len(image_bytes), "used_for_inference": False}
        with Image.open(io.BytesIO(self.source_image)) as original:
            raster = original.convert("RGB")
            size = list(raster.size)
            for index, (window, display) in enumerate(_windows(size, viewport)):
                image = raster.copy() if not index else raster.crop((window[0], window[1], window[2], window[3]))
                if not index:
                    image.thumbnail((1536, 1536))
                stream = io.BytesIO()
                image.save(stream, format="PNG")
                payload = stream.getvalue()
                call: dict[str, Any] = {
                    "call_id": CALL_IDS[index],
                    "status": "requesting",
                    "tile_pixel_bbox": window,
                    "viewport": display,
                    "image": {"sha256": sha(payload), "bytes": len(payload), "image_size": list(image.size)},
                }
                self.raw_calls.append(call)
                try:
                    call["result"] = deepcopy(self.detector.detect(payload, viewport=display))
                    call["status"] = "ok"
                except Exception as error:
                    call.update(status="error", error_type=type(error).__name__)
                    raise
        self.fused = replay(self.raw_calls, viewport, size)
        return self.fused


def process(record: dict[str, Any], config: dict[str, Any], output: Path, client: Any) -> dict[str, Any]:
    """Retain all proposals and strict crop costs, rejecting partial output atomically."""
    from PIL import Image

    import pylopdf

    began, cpu = time.perf_counter(), time.process_time()
    output.mkdir(parents=True, exist_ok=True)
    for path in (output / f"{record['id']}-structure.json", output / f"{record['id']}.md"):
        path.unlink(missing_ok=True)
    result: dict[str, Any] = {
        "id": record["id"],
        "status": "error",
        "tables": [],
        "calls": [],
        "unresolved_ids": [],
        "route": "vision_transcription_regions",
        "processor": "vision_multiscale",
        "source_conserved": False,
        "text_provenance": "model-transcribed",
        "output_scope": "table_only",
        "output_atomic": True,
        "coverage": "unverified",
    }
    wrapper = None
    stage = "config"
    try:
        if (
            config.get("campaign", "P002") != "P002"
            or config.get("layout_detector") != "yolo"
            or config.get("_layout_detector") is None
            or config.get("detector_tiles", "2x2") != "2x2"
            or config.get("detector_fusion", "larger_containment") != "larger_containment"
            or config.get("image_edge", 1024) != 1024
            or config.get("jpeg_quality", 90) != 90
        ):
            raise ValueError("Multiscale requires fixed P002 CPU YOLO 2x2/larger_containment and JPEG90/1024")
        stage = "source_render"
        data = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Frozen PDF changed")
        with pylopdf.open(stream=data) as document:
            page = document[record["page_number"]]
            viewport = list(page.rect)
            scale = 3071 / max(page.rect.width, page.rect.height)
            pixels = page.render(scale=scale, background=(255, 255, 255))
            with Image.open(io.BytesIO(pixels)) as image:
                size = list(image.size)
            if max(size) > 3072:
                raise ValueError("Multiscale source raster exceeds fixed render cap")
            source_metadata = {
                "sha256": sha(pixels),
                "bytes": len(pixels),
                "image_size": size,
                "viewport": viewport,
                "render_scale": scale,
                "original_rotation": page.rotation,
                "rotation_normalized": False,
            }
        wrapper = MultiscaleDetector(config["_layout_detector"], pixels, viewport)
        stage = "vision_regions"
        result["multiscale_image"] = source_metadata
        result = regions.process(record, {**config, "_layout_detector": wrapper}, output, client)
        result["multiscale_image"] = source_metadata
    except Exception as error:
        result.update(status="error", tables=[], error_stage=stage, error_type=type(error).__name__)
        if isinstance(error, ValueError):
            result["error"] = str(error)[:500]
    if result.get("status") != "ok":
        for path in (output / f"{record['id']}-structure.json", output / f"{record['id']}.md"):
            path.unlink(missing_ok=True)
    result.update(processor="vision_multiscale", multiscale_rules=deepcopy(RULES))
    if wrapper is not None:
        result.update(
            multiscale_raw_calls=wrapper.raw_calls, multiscale_received_base_image=wrapper.received_base_image
        )
    result.update(wall_seconds=time.perf_counter() - began, cpu_seconds=time.process_time() - cpu)
    write_json(output / f"{record['id']}-result.json", result)
    return result


def main() -> None:
    """Expose only run inputs and model budget; proposal/crop settings stay frozen."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generation-model", "--model", choices=vision.MODELS, default=vision.MODELS[1])
    parser.add_argument(
        "--generation-tokens", "--tokens", type=int, choices=(4096, 8192, 16384, 32768, 65536), default=16384
    )
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    config = {
        "run_id": args.output.name,
        "processor": "vision_multiscale",
        "campaign": "P002",
        "policy": "gated",
        "layout_detector": "yolo",
        "detector_tiles": "2x2",
        "detector_fusion": "larger_containment",
        "image_edge": 1024,
        "jpeg_quality": 90,
        "generation_model": args.generation_model,
        "model": args.generation_model,
        "generation_tokens": args.generation_tokens,
        "pilot": args.pilot,
        "order_seed": 20261010,
        "normalize_rotation": False,
        "rotation_mode": "preserve",
        "ocr_empty": False,
        "output_scope": "table_only",
    }
    report = vision.baseline.run(args.manifest, args.output, config)
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
