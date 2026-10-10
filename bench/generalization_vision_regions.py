"""Opt-in source-only CPU detector crops for strict image-only transcription.

No OCR, source word IDs, references, repairs or inference occur during proposal
selection. Provider transport is delegated to the coordinated metered caller.
"""

# ruff: noqa: ANN401, PLC0415, EM101, TRY003, SLF001, PLR2004, TRY301
from __future__ import annotations

import base64
import io
import math
import time
from pathlib import Path
from typing import Any

from bench import generalization_vision_run as vision
from bench import pipeline_vision_transcription as adapter
from bench.pipeline_frontier import MODELS
from bench.silver import guard_path, sha, write_json

MAX_REGIONS = 32
MAX_PAGE_SLOTS = 4096
DETECTOR_EDGE = 1536
RENDER_EDGE = 4096
CROP_EDGE = 1024
CROP_EDGES = (400, 512, 768, 1024, 2048)
JPEG_QUALITY = 90
JPEG_QUALITIES = (50, 70, 90)
DETECTOR_CONFIDENCE = 0.25
TRANSCRIPTION_REPRESENTATIONS = ("legacy", "matrix_strict", "atomic_cells")



def transcription_request(
    model: str, url: str, viewport: list[float], max_tokens: int = adapter.MAX_TOKENS,
    *, representation: str = "legacy",
) -> dict[str, Any]:
    """Rebuild actual strict request content without changing legacy body bytes."""
    if representation not in TRANSCRIPTION_REPRESENTATIONS:
        raise ValueError("Unknown transcription representation")
    body = adapter.request(model, url, viewport, max_tokens=max_tokens)
    if representation != "legacy":
        from bench.p003_transcription_design import prompt_variant

        variant = prompt_variant(representation)
        body["messages"][0]["content"] = variant["instructions"]
        body["response_format"]["json_schema"] = {
            "name": "pdf_vision_" + representation, "strict": True, "schema": variant["schema"],
        }
    return body


def transcription_parse(
    response: dict[str, Any], viewport: list[float], *, representation: str = "legacy",
) -> dict[str, Any]:
    """Select only the explicitly frozen strict parser; never apply repair."""
    if representation not in TRANSCRIPTION_REPRESENTATIONS:
        raise ValueError("Unknown transcription representation")
    if representation == "atomic_cells":
        from bench.p003_transcription_design import parse_atomic

        return parse_atomic(response, viewport)
    return adapter.parse(response, viewport)

def _contained(value: Any, viewport: list[float]) -> list[float]:
    box = list(adapter._viewport(value))
    page = adapter._viewport(viewport)
    if box[0] < page[0] or box[1] < page[1] or box[2] > page[2] or box[3] > page[3]:
        raise ValueError("Crop viewport lies outside the original page")
    return box


def proposals(detection: dict[str, Any], viewport: list[float]) -> list[dict[str, Any]]:
    """Select only fixed-confidence Table detections in retained detector order."""
    if detection.get("device") != "cpu" or detection.get("type") != "result":
        raise ValueError("Crop transcription requires complete CPU detector output")
    if list(detection.get("viewport", [])) != viewport:
        raise ValueError("Detector viewport differs from original page")
    boxes = detection.get("boxes")
    if not isinstance(boxes, list) or len(boxes) > 1024:
        raise ValueError("Detector box inventory exceeds admission")
    retained: list[dict[str, Any]] = []
    for box in boxes:
        label, confidence = box["label"], box["confidence"]
        if (
            not isinstance(label, str)
            or isinstance(confidence, bool)
            or not isinstance(confidence, (float, int))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
        ):
            raise ValueError("Invalid source detector class or confidence")
        bounds = _contained(box["bbox"], viewport)
        if label == "Table" and confidence >= DETECTOR_CONFIDENCE:
            retained.append(
                {
                    "index": len(retained),
                    "request_index": len(retained),
                    "viewport": bounds,
                    "detector_box": dict(box),
                    "status": "not_requested",
                }
            )
    if len(retained) > MAX_REGIONS:
        raise ValueError("Complete table proposal inventory exceeds 32 regions; no subset selection")
    return retained


def _compose_legacy(regions: list[dict[str, Any]], viewport: list[float]) -> dict[str, Any]:
    """Reparse every raw response and compose atomic ordered disjoint tables."""
    adapter._viewport(viewport)
    if not isinstance(regions, list) or len(regions) > MAX_REGIONS:
        raise ValueError("Region inventory admission exceeded")
    tables: list[dict[str, Any]] = []
    slots = 0
    for index, region in enumerate(regions):
        if (
            type(region.get("index")) is not int
            or region["index"] != index
            or type(region.get("request_index")) is not int
            or region["request_index"] != index
            or region.get("status") != "ok"
        ):
            raise ValueError("Region order, request uniqueness or success status is invalid")
        bounds = _contained(region["viewport"], viewport)
        parsed = adapter.parse(region["transcription_response"], bounds)
        for table in parsed["tables"]:
            slots += table["row_count"] * table["col_count"]
            if slots > MAX_PAGE_SLOTS:
                raise ValueError("Complete crop transcription exceeds 4096 slots")
            box = table["bbox"]
            for prior in tables:
                other = prior["bbox"]
                if min(box[2], other[2]) > max(box[0], other[0]) and min(box[3], other[3]) > max(box[1], other[1]):
                    raise ValueError("Returned crop tables overlap; ownership is unverified")
            tables.append(table)
    return {"tables": tables, "text_provenance": adapter.PROVENANCE, "source_conserved": False}


def compose(  # noqa: C901 - explicit strict treatment dispatch and atomic composition.
    regions: list[dict[str, Any]], viewport: list[float], *, representation: str = "legacy",
) -> dict[str, Any]:
    """Reparse every raw response and compose atomic ordered disjoint tables."""
    if representation == "legacy":
        if any(r.get("transcription_representation", "legacy") != "legacy" for r in regions):
            raise ValueError("Region representation differs from frozen composition treatment")
        return _compose_legacy(regions, viewport)
    adapter._viewport(viewport)
    if representation not in TRANSCRIPTION_REPRESENTATIONS:
        raise ValueError("Unknown transcription representation")
    if not isinstance(regions, list) or len(regions) > MAX_REGIONS:
        raise ValueError("Region inventory admission exceeded")
    tables: list[dict[str, Any]] = []
    slots = 0
    for index, region in enumerate(regions):
        if (
            type(region.get("index")) is not int
            or region["index"] != index
            or type(region.get("request_index")) is not int
            or region["request_index"] != index
            or region.get("status") != "ok"
        ):
            raise ValueError("Region order, request uniqueness or success status is invalid")
        bounds = _contained(region["viewport"], viewport)
        if region.get("transcription_representation", "legacy") != representation:
            raise ValueError("Region representation differs from frozen composition treatment")
        parsed = transcription_parse(region["transcription_response"], bounds, representation=representation)
        for table in parsed["tables"]:
            slots += table["row_count"] * table["col_count"]
            if slots > MAX_PAGE_SLOTS:
                raise ValueError("Complete crop transcription exceeds 4096 slots")
            box = table["bbox"]
            for prior in tables:
                other = prior["bbox"]
                if min(box[2], other[2]) > max(box[0], other[0]) and min(box[3], other[3]) > max(box[1], other[1]):
                    raise ValueError("Returned crop tables overlap; ownership is unverified")
            tables.append(table)
    return {"tables": tables, "text_provenance": adapter.PROVENANCE, "source_conserved": False}


def _crop(
    image: Any,
    viewport: list[float],
    bounds: list[float],
    crop_edge: int = CROP_EDGE,
    jpeg_quality: int = JPEG_QUALITY,
) -> tuple[str, dict[str, Any]]:
    from PIL import Image

    if type(crop_edge) is not int or crop_edge not in CROP_EDGES:
        raise ValueError("Crop image edge is outside the fixed comparison settings")
    if type(jpeg_quality) is not int or jpeg_quality not in JPEG_QUALITIES:
        raise ValueError("Crop JPEG quality is outside the fixed comparison settings")
    box = _contained(bounds, viewport)
    width, height = image.size
    scale_x, scale_y = width / (viewport[2] - viewport[0]), height / (viewport[3] - viewport[1])
    pixel_box = [
        (box[0] - viewport[0]) * scale_x,
        (box[1] - viewport[1]) * scale_y,
        (box[2] - viewport[0]) * scale_x,
        (box[3] - viewport[1]) * scale_y,
    ]
    # EXTENT retains the exact continuous crop viewport instead of relabeling a
    # floor/ceil-expanded raster as the narrower detector box.
    target_width, target_height = pixel_box[2] - pixel_box[0], pixel_box[3] - pixel_box[1]
    ratio = crop_edge / max(target_width, target_height)
    target = (max(1, round(target_width * ratio)), max(1, round(target_height * ratio)))
    cropped = image.transform(target, Image.Transform.EXTENT, pixel_box, resample=Image.Resampling.BICUBIC)
    stream = io.BytesIO()
    cropped.save(stream, format="JPEG", quality=jpeg_quality)
    data = stream.getvalue()
    metadata = {
        "image_codec": "JPEG",
        "image_mode": "RGB",
        "image_quality": jpeg_quality,
        "image_edge": crop_edge,
        "image_size": list(target),
        "image_viewport": box,
        "image_sha256": sha(data),
        "image_bytes": len(data),
        "whole_page": False,
        "body_limit_adaptation": False,
        "continuous_crop": True,
    }
    return "data:image/jpeg;base64," + base64.b64encode(data).decode(), metadata


def process(record: dict[str, Any], config: dict[str, Any], output: Path, client: Any) -> dict[str, Any]:  # noqa: C901, PLR0912 - atomic staged result retention
    """Preserve all region responses/costs before strict atomic page admission."""
    from PIL import Image

    import pylopdf

    began, cpu = time.perf_counter(), time.process_time()
    result: dict[str, Any] = {
        "id": record["id"],
        "status": "error",
        "tables": [],
        "calls": [],
        "unresolved_ids": [],
        "route": "vision_transcription_regions",
        "processor": "vision_regions",
        "source_conserved": False,
        "text_provenance": adapter.PROVENANCE,
        "output_scope": "table_only",
        "output_atomic": True,
        "coverage": "unverified",
        "transcription_regions": [],
        "stages": {},
        "crop_settings": {
            "detector_edge": DETECTOR_EDGE,
            "render_edge_cap": RENDER_EDGE,
            "crop_edge": config.get("image_edge", CROP_EDGE),
            "jpeg_quality": config.get("jpeg_quality", JPEG_QUALITY),
            "class": "Table",
            "confidence": DETECTOR_CONFIDENCE,
            "maximum_regions": MAX_REGIONS,
            "maximum_slots": MAX_PAGE_SLOTS,
        },
    }
    representation = config.get("transcription_representation", "legacy")
    result["transcription_representation"] = representation
    stage = "input"
    try:
        if representation not in TRANSCRIPTION_REPRESENTATIONS:
            raise ValueError("Unknown transcription representation")
        if (
            config.get("campaign", "P002") not in {"P002", "P003"}
            or type(config.get("image_edge", CROP_EDGE)) is not int
            or config.get("image_edge", CROP_EDGE) not in CROP_EDGES
            or type(config.get("jpeg_quality", JPEG_QUALITY)) is not int
            or config.get("jpeg_quality", JPEG_QUALITY) not in JPEG_QUALITIES
        ):
            raise ValueError("Crop control requires P002 and declared fixed image edge/JPEG quality")
        detector = config.get("_layout_detector")
        if detector is None:
            raise ValueError("Crop control requires an initialized persistent CPU detector")
        data = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Frozen source PDF hash changed")
        result["pdf_sha256"] = sha(data)
        stage = "detector"
        with pylopdf.open(stream=data) as document:
            page = document[record["page_number"]]
            viewport = list(page.rect)
            result.update(viewport=viewport, original_rotation=page.rotation, rotation_normalized=False)
            detector_pixels = page.render(
                scale=DETECTOR_EDGE / max(page.rect.width, page.rect.height), background=(255, 255, 255)
            )
            result["detector_image"] = {
                "edge": DETECTOR_EDGE,
                "sha256": sha(detector_pixels),
                "bytes": len(detector_pixels),
                "viewport": viewport,
            }
            result["layout_detection"] = detector.detect(detector_pixels, viewport=viewport)
            regions = proposals(result["layout_detection"], viewport)
            for region in regions:
                region["transcription_representation"] = representation
            result["transcription_regions"] = regions
            result["proposal_count"] = len(regions)
            result["stages"]["detector_seconds"] = time.perf_counter() - began
            if regions:
                stage = "render"
                render_scale = (RENDER_EDGE - 1) / max(page.rect.width, page.rect.height)
                result["render_scale"] = render_scale
                pixels = page.render(scale=render_scale, background=(255, 255, 255))
                with Image.open(io.BytesIO(pixels)) as rendered:
                    image = rendered.convert("RGB")
                    if max(image.size) > RENDER_EDGE:
                        raise ValueError("Full-page raster exceeds fixed 4096 edge cap")
                    result["render_image_size"] = list(image.size)
                    for region in regions:
                        region["transcription_representation"] = representation
                        stage = "crop"
                        url, metadata = _crop(
                            image,
                            viewport,
                            region["viewport"],
                            config.get("image_edge", CROP_EDGE),
                            config.get("jpeg_quality", JPEG_QUALITY),
                        )
                        region["image"] = metadata
                        stage = "request"
                        body = transcription_request(
                            config.get("generation_model", MODELS[1]),
                            url,
                            region["viewport"],
                            max_tokens=config.get("generation_tokens", 16384), representation=representation,
                        )
                        region["status"] = "requesting"
                        first_call = len(result["calls"])
                        try:
                            response = vision._transcribe(
                                client, body, config, result, output, request_index=region["request_index"]
                            )
                            region["transcription_response"] = response
                            region["request"] = {**result.pop("request"),
                                "transcription_representation": representation}
                            result.pop("transcription_response", None)
                            region["call_indexes"] = list(range(first_call, len(result["calls"])))
                            stage = "parse"
                            parsed = transcription_parse(response, region["viewport"], representation=representation)
                            region.update(status="ok", tables=parsed["tables"])
                        except Exception as error:
                            region.update(status="error", error_stage=stage, error_type=type(error).__name__)
                            if "request" in result:
                                region["request"] = {**result.pop("request"),
                                    "transcription_representation": representation}
                            region["call_indexes"] = list(range(first_call, len(result["calls"])))
                            if isinstance(error, ValueError):
                                region["error"] = str(error)[:500]
                            raise
        stage = "compose"
        parsed = compose(result["transcription_regions"], result["viewport"], representation=representation)
        rendered_markdown = adapter.markdown(parsed)
        write_json(output / f"{record['id']}-structure.json", parsed)
        (output / f"{record['id']}.md").write_text(rendered_markdown)
        result.update(status="ok", tables=parsed["tables"])
    except Exception as error:
        result.update(error_type=type(error).__name__, error_stage=stage, tables=[])
        if isinstance(error, ValueError):
            result["error"] = str(error)[:500]
    result.pop("transcription_response", None)
    result.update(wall_seconds=time.perf_counter() - began, cpu_seconds=time.process_time() - cpu)
    write_json(output / f"{record['id']}-result.json", result)
    return result
