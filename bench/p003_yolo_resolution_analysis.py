"""Independent source/image/projection audit and DEV bbox acquisition metrics, without model reruns."""

# ruff: noqa: EM101, TRY003, C901, PLR0912
from __future__ import annotations

import io
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

import pdfust
from bench import p003_yolo_resolution as detector
from bench.generalization_report import load_corpus
from bench.generalization_scoring import _iou
from bench.p003_availability_analysis import characters, read
from bench.p003_gate_run import authenticate
from bench.pipeline_scoring import _assignment
from bench.silver import guard_path, sha

IOU_THRESHOLDS = (0.1, 0.3, 0.5, 0.7)
CPU_THREADS = 2
CONFIDENCE = 0.25


def predictor_arguments(size: int) -> dict[str, Any]:
    """Require matched retained predictor defaults, with only nominal size changed."""
    return {
        "agnostic_nms": False,
        "augment": False,
        "batch": 1,
        "conf": CONFIDENCE,
        "device": "cpu",
        "half": None,
        "imgsz": size,
        "iou": 0.7,
        "max_det": 1025,
        "quantize": 32,
        "rect": True,
    }


def box_counts(expected: list[list[float]], predicted: list[list[float]], threshold: float) -> dict[str, Any]:
    """Match cardinality first, then IoU, without text or table-shape matching cues."""
    weights = []
    ious = []
    for a in expected:
        values = [_iou(tuple(a), tuple(b)) for b in predicted]
        ious.append(values)
        weights.append([1_000_000 + int(v * 100_000) if v >= threshold else 0 for v in values])
    pairs = [(i, j) for i, j in _assignment(weights) if weights[i][j] > 0] if expected and predicted else []
    return {
        "expected": len(expected),
        "predicted": len(predicted),
        "matched": len(pairs),
        "missed": len(expected) - len(pairs),
        "extra": len(predicted) - len(pairs),
        "iou_sum": sum(ious[i][j] for i, j in pairs),
        "negative_page": int(not expected),
        "negative_fp_page": int(not expected and bool(predicted)),
    }


def verify(
    directory: Path, trusted_code: dict[str, str], source_trusted_code: dict[str, str]
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Authenticate and regenerate all source rasters, then reproject all retained raw boxes before targets."""
    directory = guard_path(directory)
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    if frozen["code_sha256"] != trusted_code:
        raise ValueError("YOLO independent code authority differs")
    for name, digest in trusted_code.items():
        if Path(name).name != name or sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("YOLO archive differs from independent source code")
        if name == "p003_yolo_resolution.py" and sha(Path(detector.__file__).read_bytes()) != digest:
            raise ValueError("Current pure YOLO projection differs from authenticated source")
    configs = {str(size): detector.configuration(size) for size in detector.SIZES}
    if (
        frozen["processor"] != "p003_yolo_resolution"
        or frozen["references_read"] is not False
        or frozen["fresh_confirmation_accessed"] is not False
        or frozen["hosted_calls"] != 0
        or frozen["sizes"] != list(detector.SIZES)
        or frozen["configurations"] != configs
        or report["source_manifest_sha256"] != sha((directory / "frozen.json").read_bytes())
        or report["code_sha256"] != trusted_code
        or report["configuration"] != configs
        or report["cpu_threads"] != CPU_THREADS
        or report["interop_threads"] != 1
        or report["local_gpu_used"] is not False
        or detector.digest(guard_path(Path(frozen["model_path"]))) != frozen["model_sha256"]
        or report["model_sha256"] != frozen["model_sha256"]
        or frozen["source_edge"] != detector.SOURCE_EDGE
        or frozen["max_pixels"] != detector.MAX_PIXELS
        or report["device"] != "cpu"
    ):
        raise ValueError("YOLO source-only model/configuration protocol differs")
    baseline = guard_path(Path(frozen["baseline"]))
    sf, sr = authenticate(baseline, source_trusted_code)
    if (
        sf["records"] != frozen["records"]
        or sha((baseline / "frozen.json").read_bytes()) != frozen["baseline_frozen_sha256"]
        or sha((baseline / "report.json").read_bytes()) != frozen["baseline_report_sha256"]
        or read(directory / "trust/source.json") != source_trusted_code
        or sha((directory / "trust/source.json").read_bytes()) != frozen["external_trusted_code_sha256"]
        or [p["id"] for p in frozen["pages"]] != [r["id"] for r in frozen["records"]]
        or [p["id"] for p in report["pages"]] != [r["id"] for r in frozen["records"]]
    ):
        raise ValueError("YOLO source inventory/provenance differs")
    original = {p["id"]: p for p in sr["results"]}
    pages = []
    for frame, row in zip(frozen["pages"], report["pages"], strict=True):
        if frame["status"] != "ready":
            raise ValueError("Unsupported incomplete source raster freeze; preserve separately")
        record = frame["record"]
        source = read(directory / frame["source_path"])
        raw = guard_path(Path(record["pdf_path"])).read_bytes()
        if (
            sha(raw) != record["pdf_sha256"]
            or source != original[frame["id"]]["source"]
            or sha((directory / frame["source_path"]).read_bytes()) != frame["source_sha256"]
            or sha((baseline / f"{frame['id']}-result.json").read_bytes()) != frame["baseline_result_sha256"]
        ):
            raise ValueError("YOLO source/PDF identity changed")
        with pdfust.open(stream=raw) as doc:
            page = doc[record["page_number"]]
            viewport = list(page.rect)
            if (
                viewport != frame["viewport"]
                or viewport != source["page_size"]
                or page.rotation != frame["original_rotation"]
            ):
                raise ValueError("YOLO source display geometry differs")
            pixels = page.render(
                scale=detector.SOURCE_EDGE / max(page.rect.width, page.rect.height), background=(255, 255, 255)
            )
        with Image.open(io.BytesIO(pixels)) as image:
            out = io.BytesIO()
            image.convert("RGB").save(out, format="PNG", compress_level=6, optimize=False)
            if list(image.size) != frame["image_size"] or sha(out.getvalue()) != frame["image_sha256"]:
                raise ValueError("YOLO frozen pixels differ from actual original PDF")
        if sha((directory / frame["image_path"]).read_bytes()) != frame["image_sha256"]:
            raise ValueError("YOLO retained raster bytes changed")
        if [x["imgsz"] for x in row["results"]] != list(detector.SIZES):
            raise ValueError("YOLO resolution arm missing or reordered")
        results = []
        for result in row["results"]:
            value = read(directory / result["path"])
            if sha((directory / result["path"]).read_bytes()) != result["sha256"]:
                raise ValueError("YOLO raw result changed")
            if (
                value["id"] != frame["id"]
                or value["imgsz"] != result["imgsz"]
                or value["status"] != result["status"]
                or value["configuration"] != detector.configuration(value["imgsz"])
                or value["model_sha256"] != frozen["model_sha256"]
                or value["image_sha256"] != frame["image_sha256"]
                or value["source_sha256"] != frame["source_sha256"]
                or value["viewport"] != frame["viewport"]
                or value["image_size"] != frame["image_size"]
                or value["no_retry"] is not True
                or value["local_gpu_used"] is not False
                or value["device"] != "cpu"
                or value["effective_predictor_arguments"] != predictor_arguments(value["imgsz"])
            ):
                raise ValueError("YOLO result input/model/configuration identity differs")
            if value["status"] != "completed":
                raise ValueError("Unsupported incomplete detector result; preserve as separate failed arm")
            projected = detector.project(value["raw_boxes"], frame["viewport"], frame["image_size"])
            if (
                value["boxes"] != projected
                or value["torch_intra_threads"] != CPU_THREADS
                or value["torch_interop_threads"] != 1
                or any(b["confidence"] < CONFIDENCE for b in projected)
                or result["box_count"] != len(projected)
                or result["metrics"] != value["metrics"]
                or result["table_box_count"] != sum(b["label"].lower() == "table" for b in projected)
            ):
                raise ValueError("YOLO raw box projection/thread/count differs")
            results.append(value)
        pages.append({"id": frame["id"], "source": source, "results": results})
    return frozen, report, pages


def analyze(
    directory: Path, corpus: Path, *, trusted_code: dict[str, str], source_trusted_code: dict[str, str]
) -> dict[str, Any]:
    """Compare each frozen resolution independently; text counts are character necessities, never cells."""
    _, report, pages = verify(directory, trusted_code, source_trusted_code)
    manifest, targets = load_corpus(guard_path(corpus))
    refs = {p["id"]: p for p in targets["pages"]}
    if set(refs) != {p["id"] for p in pages}:
        raise ValueError("YOLO acquisition must score exact complete intended DEV cohort")
    arms = []
    for index, size in enumerate(detector.SIZES):
        rows = []
        for page in pages:
            result = page["results"][index]
            boxes = [b["global_bbox"] for b in result["boxes"] if b["label"].lower() == "table"]
            expected = [t["bbox"] for t in refs[page["id"]]["tables"]]
            words = [
                w
                for w in page["source"]["words"]
                if any(
                    b[0] <= (w["bbox"][0] + w["bbox"][2]) / 2 <= b[2]
                    and b[1] <= (w["bbox"][1] + w["bbox"][3]) / 2 <= b[3]
                    for b in boxes
                )
            ]
            available = sum((characters(w["text"]) for w in words), Counter())
            required = sum(
                (
                    characters(v)
                    for t in refs[page["id"]]["tables"]
                    for row in t["values"]
                    for v in row
                    if v is not None
                ),
                Counter(),
            )
            rows.append(
                {
                    "id": page["id"],
                    "bbox": {str(t): box_counts(expected, boxes, t) for t in IOU_THRESHOLDS},
                    "source_words_center_union": len(words),
                    "reference_nonspace_characters": required.total(),
                    "aggregate_available_reference_characters": (required & available).total(),
                    "aggregate_missing_reference_characters": (required - available).total(),
                    "metrics": result["metrics"],
                }
            )
        arms.append(
            {
                "imgsz": size,
                "pages": rows,
                "bbox_totals": {
                    str(t): dict(sum((Counter(r["bbox"][str(t)]) for r in rows), Counter())) for t in IOU_THRESHOLDS
                },
                "source_character_totals": {
                    k: sum(r[k] for r in rows)
                    for k in (
                        "source_words_center_union",
                        "reference_nonspace_characters",
                        "aggregate_available_reference_characters",
                        "aggregate_missing_reference_characters",
                    )
                },
                "resources": {
                    "wall_seconds": sum(r["metrics"]["wall_seconds"] for r in rows),
                    "cpu_seconds": sum(r["metrics"]["cpu_seconds"] for r in rows),
                    "peak_sampled_rss_bytes": max(r["metrics"]["peak_sampled_rss_bytes"] for r in rows),
                },
            }
        )
    return {
        "scope": "Independent retained YOLO source/pixels/projection audit; "
        "bbox acquisition and optimistic character necessities only",
        "frozen_sha256": sha((guard_path(directory) / "frozen.json").read_bytes()),
        "dataset_sha256": manifest["dataset_sha256"],
        "intended_pages": len(pages),
        "arms": arms,
        "iou_thresholds_predeclared": IOU_THRESHOLDS,
        "initialization": report["initialization"],
        "warmups": report["warmups"],
        "model_rerun": False,
        "new_api_calls": 0,
        "limitations": "Raw confidence-filtered post-NMS outputs are retained, not regenerated logits; "
        "character union ignores order/geometry/complete-word feasibility and is not cell quality; "
        "source costs separate",
    }
