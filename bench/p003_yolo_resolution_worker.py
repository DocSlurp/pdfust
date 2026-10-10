"""Offline local CPU worker for independently frozen YOLO resolution arms."""

# ruff: noqa: EM101, TRY003, PLC0415, E501, C901, PLR0912, PLR2004, TRY301
from __future__ import annotations

import argparse
import contextlib
import json
import os
import resource
import sys
import threading
import time
from pathlib import Path
from typing import Any, Self

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench import p003_yolo_resolution as protocol


def rss() -> int:
    """Own Linux process resident memory; no credential/GPU inspection."""
    return int(Path("/proc/self/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")


class Measure:
    """Sample own worker RSS every100ms plus endpoints; CPU is process-wide."""

    def __enter__(self) -> Self:
        """Start independent CPU/RSS measurement scope."""
        self.wall, self.cpu = time.perf_counter(), time.process_time()
        self.samples = [rss()]
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)
        self.thread.start()
        return self

    def sample(self) -> None:
        """Collect bounded own-process RSS until the exact scope closes."""
        while not self.stop.wait(0.1):
            self.samples.append(rss())

    def __exit__(self, *_args: object) -> None:
        """Close the sampler and record exact scope metrics."""
        self.stop.set()
        self.thread.join()
        self.samples.append(rss())
        self.result = {
            "wall_seconds": time.perf_counter() - self.wall,
            "cpu_seconds": time.process_time() - self.cpu,
            "peak_sampled_rss_bytes": max(self.samples),
            "current_rss_bytes": self.samples[-1],
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Worker process_time CPU; /proc/self/statm RSS100ms plus endpoints; getrusage lifetime peak; excludes parent",
            "sampling_interval_seconds": 0.1,
            "sample_count": len(self.samples),
        }


def worker(manifest_path: Path) -> dict[str, Any]:
    """Validate frozen inputs before loading a pinned existing model; retain all48 attempted arms."""
    os.environ.update(
        CUDA_VISIBLE_DEVICES="",
        YOLO_OFFLINE="true",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        OMP_NUM_THREADS="2",
        MKL_NUM_THREADS="2",
        OPENBLAS_NUM_THREADS="2",
    )
    manifest = json.loads(manifest_path.read_bytes())
    directory = manifest_path.parent
    for name, digest_value in manifest["code_sha256"].items():
        if (
            protocol.digest(Path(__file__).with_name(name)) != digest_value
            or protocol.digest(directory / "code" / name) != digest_value
        ):
            raise ValueError("Worker code differs from source freeze")
    model_path = Path(manifest["model_path"])
    if protocol.digest(model_path) != manifest["model_sha256"] or tuple(manifest["sizes"]) != protocol.SIZES:
        raise ValueError("Pinned model or treatment inventory changed")
    for page in manifest["pages"]:
        if page["status"] == "ready" and (
            protocol.digest(directory / page["image_path"]) != page["image_sha256"]
            or protocol.digest(directory / page["source_path"]) != page["source_sha256"]
        ):
            raise ValueError("Frozen complete source/pixel bytes changed before inference")
    with Measure() as initialization, contextlib.redirect_stdout(sys.stderr):
        import torch  # type: ignore[import-not-found]
        import ultralytics  # type: ignore[import-not-found]
        import ultralytics.utils  # type: ignore[import-not-found]
        import ultralytics.utils.torch_utils  # type: ignore[import-not-found]
        from PIL import Image
        from ultralytics import YOLO  # type: ignore[import-not-found]

        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        # select_device(cpu) otherwise resets the bound from its imported constant.
        ultralytics.utils.NUM_THREADS = 2
        ultralytics.utils.torch_utils.NUM_THREADS = 2
        model = YOLO(str(model_path))
        warmups = []
        for size in protocol.SIZES:
            began, cpu = time.perf_counter(), time.process_time()
            model.predict(Image.new("RGB", (128, 128), "white"), **protocol.configuration(size))
            if torch.get_num_threads() != 2:
                raise ValueError("Detector changed CPU thread bound during initialization")
            warmups.append(
                {"imgsz": size, "wall_seconds": time.perf_counter() - began, "cpu_seconds": time.process_time() - cpu}
            )
        if any(parameter.device.type != "cpu" for parameter in model.model.parameters()):
            raise ValueError("Model parameters are not CPU-only")
    versions = {
        "python": sys.version.split()[0],
        "torch": str(torch.__version__),
        "torch_cuda_build": torch.version.cuda,
        "ultralytics": ultralytics.__version__,
        "Pillow": Image.__version__,
    }
    pages = []
    for page in manifest["pages"]:
        results = []
        for size in protocol.SIZES:
            entry: dict[str, Any] = {
                "id": page["id"],
                "imgsz": size,
                "status": "error",
                "configuration": protocol.configuration(size),
                "model_sha256": manifest["model_sha256"],
                "image_sha256": page.get("image_sha256"),
                "source_sha256": page.get("source_sha256"),
                "image_size": page.get("image_size"),
                "viewport": page.get("viewport"),
                "original_rotation": page.get("original_rotation"),
                "effective_rotation": page.get("effective_rotation"),
                "no_retry": True,
                "local_gpu_used": False,
                "device": "cpu",
                "boxes": [],
            }
            if page["status"] != "ready":
                entry.update(
                    error_type=page.get("error_type", "SourcePreparationError"),
                    reason="No frozen admitted source image",
                )
            else:
                with Measure() as measurement:
                    try:
                        image_path = directory / page["image_path"]
                        if protocol.digest(image_path) != page["image_sha256"]:
                            raise ValueError("Frozen image changed during inference")
                        with Image.open(image_path) as original:
                            if (
                                list(original.size) != page["image_size"]
                                or original.width * original.height > protocol.MAX_PIXELS
                            ):
                                raise ValueError("Decoded image exceeds frozen admission")
                            image = original.convert("RGB")
                        with contextlib.redirect_stdout(sys.stderr), torch.inference_mode():
                            prediction = model.predict(image, **protocol.configuration(size))[0]
                        if torch.get_num_threads() != 2 or len(prediction.boxes) > protocol.MAX_BOXES:
                            raise ValueError("CPU thread or complete box admission exceeded")
                        raw = [
                            {
                                "class_id": int(label),
                                "label": model.names[int(label)],
                                "confidence": float(conf),
                                "pixel_bbox": [float(v) for v in coords],
                            }
                            for label, conf, coords in zip(
                                prediction.boxes.cls.cpu().tolist(),
                                prediction.boxes.conf.cpu().tolist(),
                                prediction.boxes.xyxy.cpu().tolist(),
                                strict=True,
                            )
                        ]
                        entry["raw_boxes"] = raw
                        entry.update(
                            status="completed",
                            boxes=protocol.project(raw, page["viewport"], page["image_size"]),
                            raw_boxes=raw,
                            predictor_speed=prediction.speed,
                            effective_predictor_arguments={
                                k: getattr(model.predictor.args, k, None)
                                for k in (
                                    "imgsz",
                                    "conf",
                                    "iou",
                                    "agnostic_nms",
                                    "max_det",
                                    "rect",
                                    "half",
                                    "augment",
                                    "batch",
                                    "device",
                                    "quantize",
                                )
                            },
                            torch_intra_threads=torch.get_num_threads(),
                            torch_interop_threads=torch.get_num_interop_threads(),
                        )
                    except Exception as error:
                        entry.update(
                            error_type=type(error).__name__, reason="Bounded detector arm failed; no repair/retry"
                        )
                entry["metrics"] = measurement.result
            result_path = directory / "results" / f"{page['id']}-{size}.json"
            protocol.write(result_path, entry)
            results.append(
                {
                    "imgsz": size,
                    "path": str(result_path.relative_to(directory)),
                    "sha256": protocol.digest(result_path),
                    "status": entry["status"],
                    "box_count": len(entry["boxes"]),
                    "table_box_count": sum(b["label"].lower() == "table" for b in entry["boxes"]),
                    "metrics": entry.get("metrics"),
                    "error_type": entry.get("error_type"),
                }
            )
        pages.append({"id": page["id"], "source_status": page["status"], "results": results})
    report = {
        "processor": "p003_yolo_resolution",
        "source_manifest_sha256": protocol.digest(manifest_path),
        "code_sha256": manifest["code_sha256"],
        "pages": pages,
        "page_count": len(pages),
        "prediction_arm_count": sum(len(p["results"]) for p in pages),
        "initialization": initialization.result,
        "warmups": warmups,
        "versions": versions,
        "model_sha256": manifest["model_sha256"],
        "model_revision": manifest["model_revision"],
        "device": "cpu",
        "cpu_threads": 2,
        "interop_threads": 1,
        "local_gpu_used": False,
        "references_read": False,
        "fresh_confirmation_accessed": False,
        "hosted_calls": 0,
        "raw_output_scope": "Complete YOLO confidence-filtered class-aware post-NMS boxes, not pre-NMS logits; no extra experiment NMS",
        "configuration": manifest["configurations"],
        "prediction_order": "frozen page order then imgsz640/1024/1280; shared warm model; potentially contended",
        "model_license": "AGPL-3.0",
        "worker_pid": os.getpid(),
        "cpu_build_caveat": "CUDA-capable Torch build; CUDA visibility disabled, explicit cpu prediction and CPU parameter check; no GPU query/inference",
    }
    protocol.write(directory / "report.json", report)
    return report


def main() -> None:
    """Read only explicit frozen DEV inputs, then write fresh local geometry artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = worker(args.manifest)
    except Exception as error:
        manifest = json.loads(args.manifest.read_bytes())
        pages = []
        for page in manifest["pages"]:
            results = []
            for size in protocol.SIZES:
                entry = {
                    "id": page["id"],
                    "imgsz": size,
                    "status": "error",
                    "error_type": type(error).__name__,
                    "reason": "Worker preflight/initialization failed; no retry",
                    "boxes": [],
                    "no_retry": True,
                    "image_sha256": page.get("image_sha256"),
                    "model_sha256": manifest["model_sha256"],
                }
                path = args.manifest.parent / "results" / f"{page['id']}-{size}.json"
                if not path.exists():
                    protocol.write(path, entry)
                results.append(
                    {
                        "imgsz": size,
                        "path": str(path.relative_to(args.manifest.parent)),
                        "sha256": protocol.digest(path),
                        "status": json.loads(path.read_bytes())["status"],
                    }
                )
            pages.append({"id": page["id"], "results": results})
        report = {
            "processor": "p003_yolo_resolution",
            "status": "worker_failure",
            "error_type": type(error).__name__,
            "page_count": len(pages),
            "prediction_arm_count": sum(len(p["results"]) for p in pages),
            "pages": pages,
            "source_manifest_sha256": protocol.digest(args.manifest),
            "references_read": False,
            "local_gpu_used": False,
            "hosted_calls": 0,
            "initialization_resources": "unmeasured due worker failure",
        }
        protocol.write(args.manifest.parent / "report.json", report)
    print(json.dumps({"page_count": report["page_count"], "prediction_arm_count": report["prediction_arm_count"]}))


if __name__ == "__main__":
    main()
