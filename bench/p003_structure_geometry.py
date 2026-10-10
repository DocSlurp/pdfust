"""CPU-only Table Transformer geometry; inference never reads references or text."""

# ruff: noqa: EM101, TRY003, PLR2004, C901, PLC0415
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import resource
import threading
import time
from itertools import pairwise
from pathlib import Path
from typing import Any

THRESHOLDS = (0.3, 0.5, 0.7)
LABELS = (
    "table",
    "table column",
    "table row",
    "table column header",
    "table projected row header",
    "table spanning cell",
)


def digest(data: bytes) -> str:
    """Hash exact archived bytes."""
    return hashlib.sha256(data).hexdigest()


def encode(value: object) -> bytes:
    """Canonical finite JSON for frozen geometry."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def project(queries: list[dict[str, Any]], bounds: list[float], labels: list[str], threshold: float) -> dict[str, Any]:
    """Clip foreground objects to the source viewport, retaining raw query identity."""
    if (
        threshold not in THRESHOLDS
        or len(bounds) != 4
        or any(not math.isfinite(v) for v in bounds)
        or bounds[0] >= bounds[2]
        or bounds[1] >= bounds[3]
    ):
        raise ValueError("Invalid fixed geometry policy or viewport")
    if len(queries) > 125 or tuple(labels) != LABELS:
        raise ValueError("Unexpected model query or label contract")
    x0, y0, x1, y1 = bounds
    objects, excluded = [], []
    for index, query in enumerate(queries):
        probabilities, box = query["probabilities"], query["box_cxcywh"]
        if (
            len(probabilities) != 7
            or len(box) != 4
            or any(not math.isfinite(v) for v in probabilities + box)
            or any(v < 0 or v > 1 for v in probabilities)
            or abs(sum(probabilities) - 1) > 1e-5
            or box[2] < 0
            or box[3] < 0
        ):
            raise ValueError("Invalid finite model output")
        label = max(range(6), key=lambda k: probabilities[k])
        score = probabilities[label]
        if score < threshold:
            continue
        cx, cy, w, h = box
        original = [
            x0 + (cx - w / 2) * (x1 - x0),
            y0 + (cy - h / 2) * (y1 - y0),
            x0 + (cx + w / 2) * (x1 - x0),
            y0 + (cy + h / 2) * (y1 - y0),
        ]
        clipped = [max(x0, original[0]), max(y0, original[1]), min(x1, original[2]), min(y1, original[3])]
        if clipped[0] >= clipped[2] or clipped[1] >= clipped[3]:
            excluded.append({"query": index, "reason": "outside_or_empty_viewport"})
            continue
        objects.append(
            {
                "query": index,
                "label": labels[label],
                "score": score,
                "bbox": clipped,
                "raw_page_bbox": original,
                "clipped": clipped != original,
            }
        )
    return {"threshold": threshold, "objects": objects, "excluded": excluded}


def topology(view: dict[str, Any]) -> dict[str, Any]:
    """Derive bounded ordered bands and nonoverlapping rectangular span anchors."""
    objects = view["objects"]
    table = sorted((o for o in objects if o["label"] == "table"), key=lambda o: (-o["score"], o["query"]))
    if not table:
        return {"status": "no_table_object", "tables": []}
    box = table[0]["bbox"]
    discarded = []

    def bands(label: str, axis: int) -> list[dict[str, Any]]:
        retained: list[dict[str, Any]] = []
        for obj in sorted((o for o in objects if o["label"] == label), key=lambda o: (-o["score"], o["query"])):
            b = obj["bbox"]
            center = (b[axis] + b[axis + 2]) / 2
            if not box[axis] < center < box[axis + 2]:
                discarded.append({"query": obj["query"], "reason": "band_center_outside_table"})
                continue
            duplicate = False
            for other in retained:
                a = other["bbox"]
                overlap = max(0, min(a[axis + 2], b[axis + 2]) - max(a[axis], b[axis]))
                if overlap / min(a[axis + 2] - a[axis], b[axis + 2] - b[axis]) >= 0.8:
                    duplicate = True
                    break
            if duplicate:
                discarded.append({"query": obj["query"], "reason": "axis_overlap_suppressed"})
            else:
                retained.append(obj)
        return sorted(retained, key=lambda o: ((o["bbox"][axis] + o["bbox"][axis + 2]) / 2, o["query"]))

    rows, cols = bands("table row", 1), bands("table column", 0)
    if not rows or not cols or len(rows) * len(cols) > 4096:
        return {"status": "shape_refused", "row_count": len(rows), "column_count": len(cols), "discarded": discarded}

    def edges(items: list[dict[str, Any]], axis: int) -> list[float]:
        centers = [(o["bbox"][axis] + o["bbox"][axis + 2]) / 2 for o in items]
        return [box[axis], *[(a + b) / 2 for a, b in pairwise(centers)], box[axis + 2]]

    xs, ys = edges(cols, 0), edges(rows, 1)
    anchors: list[dict[str, Any]] = []
    occupied: set[tuple[int, int]] = set()
    conflicts: list[dict[str, Any]] = []
    spans = sorted((o for o in objects if o["label"] == "table spanning cell"), key=lambda o: (-o["score"], o["query"]))
    for span in spans:
        sb = span["bbox"]
        slots = set()
        for r in range(len(rows)):
            for c in range(len(cols)):
                area = (xs[c + 1] - xs[c]) * (ys[r + 1] - ys[r])
                overlap = max(0, min(xs[c + 1], sb[2]) - max(xs[c], sb[0])) * max(
                    0, min(ys[r + 1], sb[3]) - max(ys[r], sb[1])
                )
                if overlap / area >= 0.5:
                    slots.add((r, c))
        if len(slots) < 2:
            discarded.append({"query": span["query"], "reason": "span_does_not_cover_multiple_slots"})
            continue
        r0, c0 = min(r for r, _ in slots), min(c for _, c in slots)
        r1, c1 = max(r for r, _ in slots) + 1, max(c for _, c in slots) + 1
        rectangle = {(r, c) for r in range(r0, r1) for c in range(c0, c1)}
        if rectangle != slots or occupied & slots:
            conflicts.append({"query": span["query"], "reason": "nonrectangular_or_conflicting_span"})
            continue
        occupied |= slots
        anchors.append(
            {
                "row": r0,
                "column": c0,
                "row_span": r1 - r0,
                "column_span": c1 - c0,
                "bbox": [xs[c0], ys[r0], xs[c1], ys[r1]],
                "query": span["query"],
            }
        )
    if conflicts:
        return {"status": "span_conflict", "conflicts": conflicts, "discarded": discarded}
    anchors.extend(
        {
            "row": r,
            "column": c,
            "row_span": 1,
            "column_span": 1,
            "bbox": [xs[c], ys[r], xs[c + 1], ys[r + 1]],
            "query": None,
        }
        for r in range(len(rows))
        for c in range(len(cols))
        if (r, c) not in occupied
    )
    return {
        "status": "geometry_candidate",
        "bbox": box,
        "row_count": len(rows),
        "column_count": len(cols),
        "x_edges": xs,
        "y_edges": ys,
        "anchors": sorted(anchors, key=lambda a: (a["row"], a["column"])),
        "row_objects": rows,
        "column_objects": cols,
        "discarded": discarded,
        "policy": "axis overlap NMS 0.8; center-midpoint bands; span slot overlap 0.5; no source text assignment",
    }


def infer(manifest: Path, model_directory: Path, output: Path, threads: int = 2) -> dict[str, Any]:
    """Load local safetensors and run one CPU model call per frozen source crop."""
    if threads not in (1, 2, 4):
        raise ValueError("Thread policy must be 1, 2 or 4")
    os.environ.update(
        {
            "CUDA_VISIBLE_DEVICES": "",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
            "OMP_NUM_THREADS": str(threads),
            "MKL_NUM_THREADS": str(threads),
        }
    )
    import psutil  # type: ignore[import-untyped]
    import torch  # type: ignore[import-not-found]
    from PIL import Image
    from transformers import AutoImageProcessor, TableTransformerForObjectDetection  # type: ignore[import-not-found]

    started, cpu = time.perf_counter(), time.process_time()
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(mode=True)
    prepared = json.loads(manifest.read_bytes())
    if prepared["code_sha256"][Path(__file__).name] != digest(Path(__file__).read_bytes()):
        raise ValueError("Inference helper differs from source-freeze code")
    provenance = json.loads((model_directory / "provenance.json").read_bytes())
    for item in provenance["files"]:
        if digest((model_directory / item["name"]).read_bytes()) != item["sha256"]:
            raise ValueError("Pinned model bytes changed")
    process = psutil.Process()
    samples: list[dict[str, Any]] = []
    stop = threading.Event()

    def sample() -> None:
        while not stop.is_set():
            times = process.cpu_times()
            samples.append(
                {
                    "seconds": time.perf_counter() - started,
                    "rss_bytes": process.memory_info().rss,
                    "cpu_seconds": times.user + times.system,
                    "native_threads": process.num_threads(),
                }
            )
            stop.wait(0.1)

    worker = threading.Thread(target=sample, daemon=True)
    worker.start()
    output.mkdir(parents=True, exist_ok=True)
    load_started = time.perf_counter()
    processor = AutoImageProcessor.from_pretrained(model_directory, local_files_only=True, use_fast=False)
    checkpoint_size = dict(processor.size)
    if checkpoint_size != {"longest_edge": 800}:
        raise ValueError("Unexpected pinned processor size contract")
    # Transformers 4.57 requires both keys. Equal shortest/max sizes implement
    # the checkpoint's longest-edge bound without expanding its image budget.
    processor.size = {"shortest_edge": 800, "longest_edge": 800}
    model = (
        TableTransformerForObjectDetection.from_pretrained(model_directory, local_files_only=True, use_safetensors=True)
        .to("cpu")
        .eval()
    )
    load_seconds = time.perf_counter() - load_started
    if torch.version.cuda is not None or any(p.device.type != "cpu" for p in model.parameters()):
        raise ValueError("CPU-only build/device required")
    labels = [model.config.id2label[i] for i in range(6)]
    pages = []
    for page in prepared["pages"]:
        if digest((manifest.parent / page["source_path"]).read_bytes()) != page["source_sha256"]:
            raise ValueError("Frozen source ownership bytes changed")
        results = []
        for crop in page["crops"]:
            data = (manifest.parent / crop["image_path"]).read_bytes()
            if digest(data) != crop["image_sha256"]:
                raise ValueError("Frozen source image changed")
            began, began_cpu = time.perf_counter(), time.process_time()
            with Image.open(manifest.parent / crop["image_path"]) as image:
                inputs = processor(images=image.convert("RGB"), return_tensors="pt")
            with torch.inference_mode():
                predicted = model(**inputs)
                probabilities = predicted.logits.softmax(-1)[0].tolist()
                boxes = predicted.pred_boxes[0].tolist()
            queries = [{"probabilities": p, "box_cxcywh": b} for p, b in zip(probabilities, boxes, strict=True)]
            views = []
            for threshold in THRESHOLDS:
                view = project(queries, crop["bbox"], labels, threshold)
                views.append({**view, "topology": topology(view)})
            result = {
                "crop": crop,
                "raw_logits": predicted.logits[0].tolist(),
                "queries": queries,
                "input_tensor_shape": list(inputs["pixel_values"].shape),
                "views": views,
                "wall_seconds": time.perf_counter() - began,
                "cpu_seconds": time.process_time() - began_cpu,
            }
            name = f"{page['id']}-{crop['region_id']}-geometry.json"
            (output / name).write_bytes(encode(result))
            results.append(
                {
                    "path": name,
                    "sha256": digest(encode(result)),
                    "wall_seconds": result["wall_seconds"],
                    "cpu_seconds": result["cpu_seconds"],
                    "topology_statuses": [v["topology"]["status"] for v in views],
                }
            )
        pages.append({"id": page["id"], "status": "completed" if results else "no_detector_proposal", "crops": results})
    stop.set()
    worker.join()
    report = {
        "source_manifest_sha256": digest(manifest.read_bytes()),
        "model": provenance,
        "pages": pages,
        "labels": labels,
        "thresholds": list(THRESHOLDS),
        "device": "cpu",
        "threads": threads,
        "interop_threads": 1,
        "query_count": model.config.num_queries,
        "checkpoint_processor_size": checkpoint_size,
        "effective_processor_size": processor.size,
        "processor_compatibility": "4.57 requires both resize keys; equal values retain longest edge 800",
        "references_read": False,
        "source_text_model_input": False,
        "conditional_scope": "retained ordinal detector crops only",
        "versions": {n: importlib.metadata.version(n) for n in ("torch", "torchvision", "transformers", "Pillow")},
        "code_sha256": digest(Path(__file__).read_bytes()),
        "resources": {
            "model_load_seconds": load_seconds,
            "wall_seconds": time.perf_counter() - started,
            "self_cpu_seconds": time.process_time() - cpu,
            "sampled_peak_rss_bytes": max((s["rss_bytes"] for s in samples), default=None),
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": "single CPU inference process; psutil RSS every100ms; no subprocesses; contended",
        },
    }
    (output / "resources.json").write_bytes(encode(samples))
    (output / "report.json").write_bytes(encode(report))
    (output / "frozen-helper.py").write_bytes(Path(__file__).read_bytes())
    return report


def main() -> None:
    """Run offline local CPU inference on an independently prepared crop manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, choices=(1, 2, 4), default=2)
    args = parser.parse_args()
    report = infer(args.manifest, args.model_directory, args.output, args.threads)
    print(json.dumps({"pages": len(report["pages"]), "resources": report["resources"]}, indent=2))


if __name__ == "__main__":
    main()
