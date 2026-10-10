"""Pinned CPU Table Transformer forwards on all frozen matched YOLO table crops."""

# ruff: noqa: EM101, TRY003, PLC0415, E501, C901, PLR0912, PLR2004, TRY301
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench import p003_structure_geometry as geometry
from bench import p003_yolo_resolution as detector
from bench.p003_yolo_resolution_worker import Measure


def infer(manifest_path: Path) -> dict[str, Any]:
    """One CPU forward per crop with all thresholds reused; bound errors are retained without retry."""
    os.environ.update(
        CUDA_VISIBLE_DEVICES="",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        HF_HUB_DISABLE_IMPLICIT_TOKEN="1",  # noqa: S106 - disable implicit credential lookup, not a credential.
        OMP_NUM_THREADS="2",
        MKL_NUM_THREADS="2",
        OPENBLAS_NUM_THREADS="2",
    )
    manifest = json.loads(manifest_path.read_bytes())
    directory = manifest_path.parent.parent
    output = directory / "geometry"
    if (output / "report.json").exists():
        raise FileExistsError("No implicit structure repeat")
    for name, digest_value in manifest["code_sha256"].items():
        if (
            detector.digest(Path(__file__).with_name(name)) != digest_value
            or detector.digest(directory / "code" / name) != digest_value
        ):
            raise ValueError("Frozen CPU code changed")
    model_directory = Path(manifest["model_directory"])
    for item in manifest["model"]["files"]:
        if detector.digest(model_directory / item["name"]) != item["sha256"]:
            raise ValueError("Pinned model bytes changed")
    for page in manifest["pages"]:
        if detector.digest(manifest_path.parent / page["source_path"]) != page["source_sha256"]:
            raise ValueError("Complete source bytes changed")
        for crop in page["crops"]:
            if detector.digest(manifest_path.parent / crop["image_path"]) != crop["image_sha256"]:
                raise ValueError("Frozen crop bytes changed")
    with Measure() as initialization:
        import torch  # type: ignore[import-not-found]
        from PIL import Image
        from transformers import (  # type: ignore[import-not-found]
            AutoImageProcessor,
            TableTransformerForObjectDetection,
        )

        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(mode=True)
        processor = AutoImageProcessor.from_pretrained(model_directory, local_files_only=True, use_fast=False)
        checkpoint_size = dict(processor.size)
        if checkpoint_size != {"longest_edge": 800}:
            raise ValueError("Pinned processor contract differs")
        processor.size = {"shortest_edge": 800, "longest_edge": 800}
        model = (
            TableTransformerForObjectDetection.from_pretrained(
                model_directory, local_files_only=True, use_safetensors=True
            )
            .to("cpu")
            .eval()
        )
        if torch.version.cuda is not None or any(p.device.type != "cpu" for p in model.parameters()):
            raise ValueError("CPU-only build and model required")
    labels = [model.config.id2label[i] for i in range(6)]
    pages = []
    for page in manifest["pages"]:
        results = []
        for crop in page["crops"]:
            entry: dict[str, Any] = {"crop": crop, "status": "error", "views": [], "no_retry": True}
            with Measure() as measurement:
                try:
                    path = manifest_path.parent / crop["image_path"]
                    if detector.digest(path) != crop["image_sha256"]:
                        raise ValueError("Frozen crop bytes changed during inference")
                    with Image.open(path) as image:
                        inputs = processor(images=image.convert("RGB"), return_tensors="pt")
                    with torch.inference_mode():
                        predicted = model(**inputs)
                    if torch.get_num_threads() != 2 or torch.get_num_interop_threads() != 1:
                        raise ValueError("CPU thread bound changed")
                    probabilities = predicted.logits.softmax(-1)[0].tolist()
                    boxes = predicted.pred_boxes[0].tolist()
                    queries = [{"probabilities": p, "box_cxcywh": b} for p, b in zip(probabilities, boxes, strict=True)]
                    entry.update(
                        raw_logits=predicted.logits[0].tolist(),
                        queries=queries,
                        input_tensor_shape=list(inputs["pixel_values"].shape),
                    )
                    views = []
                    for threshold in geometry.THRESHOLDS:
                        view = geometry.project(queries, crop["bbox"], labels, threshold)
                        views.append({**view, "topology": geometry.topology(view)})
                    entry.update(status="completed", views=views)
                except Exception as error:
                    entry.update(
                        error_type=type(error).__name__, reason="Bounded structure crop failed; no repair/retry"
                    )
            entry.update(
                metrics=measurement.result,
                wall_seconds=measurement.result["wall_seconds"],
                cpu_seconds=measurement.result["cpu_seconds"],
            )
            name = f"{page['id']}-{crop['region_id']}-geometry.json"
            path = output / name
            path.write_bytes(geometry.encode(entry))
            results.append(
                {
                    "path": name,
                    "sha256": detector.digest(path),
                    "status": entry["status"],
                    "acquisition_size": crop["acquisition_size"],
                    "metrics": entry["metrics"],
                    "topology_statuses": [v["topology"]["status"] for v in entry["views"]],
                }
            )
        pages.append({"id": page["id"], "status": "completed" if results else "no_proposal", "crops": results})
    report = {
        "pages": pages,
        "page_count": len(pages),
        "intended_crops": sum(len(p["crops"]) for p in pages),
        "source_manifest_sha256": detector.digest(manifest_path),
        "model": manifest["model"],
        "labels": labels,
        "thresholds": list(geometry.THRESHOLDS),
        "acquisition_sizes": manifest["acquisition_sizes"],
        "initialization": initialization.result,
        "checkpoint_processor_size": checkpoint_size,
        "effective_processor_size": processor.size,
        "versions": {n: importlib.metadata.version(n) for n in ("torch", "torchvision", "transformers", "Pillow")},
        "code_sha256": manifest["code_sha256"],
        "device": "cpu",
        "cpu_threads": 2,
        "interop_threads": 1,
        "local_gpu_used": False,
        "references_read": False,
        "source_text_model_input": False,
        "new_api_calls": 0,
        "conditional_scope": "all original19/24/37 YOLO Table proposals, same three sizes separately labeled, no crop winners",
        "prediction_order": "frozen page then640/1024/1280 then originalYOLO returnedboxorder; shared warm model; potentially contended",
    }
    (output / "report.json").write_bytes(geometry.encode(report))
    return report


def main() -> None:
    """Infer on only an explicit authenticated CPU crop manifest, with no downloads or hosted clients."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    report = infer(args.manifest)
    print(
        json.dumps(
            {
                "pages": report["page_count"],
                "crops": report["intended_crops"],
                "initialization": report["initialization"],
            }
        )
    )


if __name__ == "__main__":
    main()
