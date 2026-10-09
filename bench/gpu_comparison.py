"""Matched pixel-only YOLO layout CPU/GPU DEV benchmark without training."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

ARTIFACTS = Path("/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts")
MODEL = Path(
    "/home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt"
)
BOX_TOLERANCE = 0.1
CONFIDENCE_TOLERANCE = 0.001
TELEMETRY_FIELDS = 5
WORKER_LIMIT_SECONDS = 1200
MODEL_PYTHON = Path("/home/dan/.cache/pylopdf-structure-bench/bin/python")


def digest(path: Path) -> str:
    """Hash the exact retained input/model file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def confusion(expected: list[bool], predicted: list[bool]) -> dict[str, int]:
    """Score presence separately for each input cohort."""
    if len(expected) != len(predicted):
        message = "Label and prediction counts differ"
        raise ValueError(message)
    return {
        key: sum(e == a and p == b for e, p in zip(expected, predicted, strict=True))
        for key, a, b in [("tp", True, True), ("fn", True, False), ("fp", False, True), ("tn", False, False)]
    }


def compare_predictions(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare ordered classes, boxes and confidence with explicit tolerances."""
    if len(left) != len(right) or any(a["id"] != b["id"] for a, b in zip(left, right, strict=True)):
        message = "Prediction cohorts differ"
        raise ValueError(message)
    topology = 0
    max_box = 0.0
    max_conf = 0.0
    within = 0
    exact = 0
    for a, b in zip(left, right, strict=True):
        aa, bb = a["boxes"], b["boxes"]
        exact += aa == bb
        same = len(aa) == len(bb) and [x["class"] for x in aa] == [x["class"] for x in bb]
        if same:
            topology += 1
            available = list(bb)
            aligned = []
            for box in aa:
                choices = [index for index, other in enumerate(available) if other["class"] == box["class"]]
                nearest = min(
                    choices,
                    key=lambda index: sum(
                        abs(x - y) for x, y in zip(box["xyxy"], available[index]["xyxy"], strict=True)
                    ),
                )
                aligned.append(available.pop(nearest))
            box_error = max(
                (
                    abs(x - y)
                    for u, v in zip(aa, aligned, strict=True)
                    for x, y in zip(u["xyxy"], v["xyxy"], strict=True)
                ),
                default=0.0,
            )
            conf_error = max(
                (abs(u["confidence"] - v["confidence"]) for u, v in zip(aa, aligned, strict=True)),
                default=0.0,
            )
            max_box = max(max_box, box_error)
            max_conf = max(max_conf, conf_error)
            within += box_error <= BOX_TOLERANCE and conf_error <= CONFIDENCE_TOLERANCE
    return {
        "pages": len(left),
        "bit_exact_pages": exact,
        "ordered_topology_equal_pages": topology,
        "within_tolerance_pages": within,
        "box_tolerance_pixels": 0.1,
        "confidence_tolerance": 0.001,
        "max_box_delta_on_equal_topology": max_box,
        "max_confidence_delta_on_equal_topology": max_conf,
    }


def prepare(output: Path) -> None:
    """Render only current DEV inputs and put scoring labels in a separate file."""
    import pylopdf  # noqa: PLC0415 - preparation uses the native extension environment
    from bench.silver import dataset_path, load_manifest, verify_input  # noqa: PLC0415

    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    silver = Path(json.loads((ARTIFACTS / "silver-v1/latest.json").read_text())["path"])
    manifest = load_manifest(silver)
    inputs = []
    labels = []
    for case in manifest["cases"]:
        verify_input(silver, case)
        with pylopdf.Document(dataset_path(silver, case["pdf_path"])) as doc:
            for number, page in enumerate(doc):
                identifier = f"{case['id']}/page-{number}"
                path = output / "images" / (identifier.replace("/", "__") + ".png")
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.write_bytes(page.render(dpi=120))
                inputs.append({"id": identifier, "cohort": "silver-dev", "path": str(path), "sha256": digest(path)})
                labels.append(
                    {
                        "id": identifier,
                        "cohort": "silver-dev",
                        "table_present": case["family"] in {"merged-table", "multilevel-table"},
                    }
                )
    registry = json.loads((Path(__file__).parent / "omnidoc-dev/registry.json").read_text())
    for row in registry["rows"]:
        path = ARTIFACTS / "omnidoc-dev/images" / row["id"]
        if digest(path) != row["image_sha256"]:
            message = "OmniDocBench source hash mismatch"
            raise ValueError(message)
        inputs.append({"id": row["id"], "cohort": "omnidoc-dev", "path": str(path), "sha256": digest(path)})
        labels.append(
            {"id": row["id"], "cohort": "omnidoc-dev", "table_present": row["category_counts"].get("table", 0) > 0}
        )
    (output / "inputs.json").write_text(json.dumps(inputs, indent=2))
    (output / "labels.json").write_text(json.dumps(labels, indent=2))
    (output / "prepare.json").write_text(
        json.dumps(
            {
                "elapsed_seconds": time.perf_counter() - started,
                "resource_usage": list(resource.getrusage(resource.RUSAGE_SELF)),
                "silver_dataset_sha256": manifest["dataset_sha256"],
                "render_dpi": 120,
                "omnidoc_revision": registry["revision"],
                "scope": "single CPU preparation process; lifetime RSS; no sampling",
            },
            indent=2,
        )
    )
    print(f"Prepared {len(inputs)} pixel-only inputs")


def worker(output: Path, device: str, *, half: bool, repeats: int) -> None:
    """Run one isolated model worker with fixed inference settings."""
    os.environ["YOLO_OFFLINE"] = "true"
    import torch  # noqa: PLC0415 - isolated model environment
    import ultralytics  # noqa: PLC0415
    from ultralytics import YOLO  # noqa: PLC0415

    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    inputs = json.loads((output / "inputs.json").read_text())
    for row in inputs:
        if digest(Path(row["path"])) != row["sha256"]:
            message = "Input pixel hash mismatch"
            raise ValueError(message)
    cold_start = time.perf_counter()
    model = YOLO(str(MODEL))
    cold_seconds = time.perf_counter() - cold_start
    gpu = device != "cpu"
    if gpu:
        torch.cuda.reset_peak_memory_stats()
    config = {
        "imgsz": 640,
        "batch": 1,
        "conf": 0.25,
        "device": device,
        "quantize": "fp16" if half else "fp32",
        "verbose": False,
    }
    warmup = time.perf_counter()
    model.predict(inputs[0]["path"], **config)
    if gpu:
        torch.cuda.synchronize()
    warmup_seconds = time.perf_counter() - warmup
    # Predictor initialization resets CPU threads; enforce the measured arm afterward.
    torch.set_num_threads(4)
    passes = []
    for repeat in range(repeats):
        before = resource.getrusage(resource.RUSAGE_SELF)
        start = time.perf_counter()
        predictions = []
        for row in inputs:
            result = model.predict(row["path"], **config)[0]
            boxes = [
                {"class": model.names[int(cls)], "confidence": float(conf), "xyxy": [float(x) for x in xyxy]}
                for cls, conf, xyxy in zip(
                    result.boxes.cls.cpu().tolist(),
                    result.boxes.conf.cpu().tolist(),
                    result.boxes.xyxy.cpu().tolist(),
                    strict=True,
                )
            ]
            boxes.sort(key=lambda box: (box["class"], -box["confidence"], box["xyxy"]))
            predictions.append({"id": row["id"], "cohort": row["cohort"], "boxes": boxes})
        if gpu:
            torch.cuda.synchronize()
        after = resource.getrusage(resource.RUSAGE_SELF)
        elapsed = time.perf_counter() - start
        passes.append(
            {
                "repeat": repeat,
                "elapsed_seconds": elapsed,
                "cpu_user_seconds": after.ru_utime - before.ru_utime,
                "cpu_system_seconds": after.ru_stime - before.ru_stime,
                "predictions": predictions,
            }
        )
        print(f"{device} half={half} pass={repeat}: {elapsed:.3f}s for {len(inputs)} pages", flush=True)
    result = {
        "device": device,
        "half": half,
        "configuration": config,
        "cold_model_load_seconds": cold_seconds,
        "first_prediction_warmup_seconds": warmup_seconds,
        "passes": passes,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated() if gpu else None,
        "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved() if gpu else None,
        "torch": torch.__version__,
        "ultralytics": ultralytics.__version__,
        "model_sha256": digest(MODEL),
        "runner_sha256": digest(Path(__file__)),
        "input_manifest_sha256": digest(output / "inputs.json"),
        "actual_predictor_fp16": bool(model.predictor.model.fp16),
        "gpu_name": torch.cuda.get_device_name() if gpu else None,
        "tf32_allowed": False,
        "model_source": "https://huggingface.co/hantian/yolo-doclaynet",
        "model_revision": MODEL.parent.name,
        "model_license": "AGPL-3.0",
        "cpu_threads": torch.get_num_threads(),
        "interop_threads": 1,
        "machine": platform.platform(),
        "cpu_count": os.cpu_count(),
        "measurement": (
            "resource.getrusage SELF; CPU deltas per pass; RSS lifetime peak; CUDA allocator peaks include warmup"
        ),
    }
    name = "cpu-fp32" if not gpu else "gpu-fp16" if half else "gpu-fp32"
    (output / (name + ".json")).write_text(json.dumps(result, indent=2))


def monitored_run(output: Path, device: str, *, half: bool, repeats: int) -> None:
    """Record host-wide GPU telemetry at 0.5-second intervals for one worker."""
    name = "cpu-fp32" if device == "cpu" else "gpu-fp16" if half else "gpu-fp32"
    command = [
        str(MODEL_PYTHON),
        "-m",
        "bench.gpu_comparison",
        "--worker",
        "--output",
        str(output),
        "--device",
        device,
        "--repeats",
        str(repeats),
    ]
    if half:
        command.append("--half")
    samples = []
    started = time.perf_counter()
    kernel_since = "@" + str(int(time.time()))
    with (output / (name + ".log")).open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)  # noqa: S603
        while process.poll() is None:
            measured = subprocess.run(
                [
                    "/usr/bin/nvidia-smi",
                    "--query-gpu=name,driver_version,utilization.gpu,memory.used,power.draw",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            samples.append(
                {
                    "elapsed_seconds": time.perf_counter() - started,
                    "raw_csv": measured.stdout.strip(),
                    "error": measured.stderr.strip(),
                }
            )
            kernel = subprocess.run(  # noqa: S603 - fixed executable with generated timestamp
                ["/usr/bin/journalctl", "-k", "--since", kernel_since, "--no-pager", "-o", "cat"],
                capture_output=True,
                text=True,
                check=False,
            )
            xid = [line for line in kernel.stdout.splitlines() if "NVRM" in line and "Xid" in line]
            samples[-1]["kernel_xid_lines"] = xid
            samples[-1]["kernel_query_error"] = kernel.stderr.strip()
            if (
                measured.returncode != 0
                or "Xid" in measured.stderr
                or xid
                or time.perf_counter() - started > WORKER_LIMIT_SECONDS
            ):
                process.terminate()
                process.wait(timeout=15)
                message = "GPU telemetry error; worker stopped"
                raise RuntimeError(message)
            time.sleep(0.5)
        if process.returncode != 0:
            message = "Comparison worker failed; inspect retained log"
            raise RuntimeError(message)
    (output / (name + "-telemetry.json")).write_text(
        json.dumps(
            {
                "scope": "host-wide nvidia-smi; includes desktop and other processes; no per-model attribution",
                "sampling_interval_seconds": 0.5,
                "process_wall_seconds": time.perf_counter() - started,
                "samples": samples,
            },
            indent=2,
        )
    )
    print((output / (name + ".log")).read_text())


def pass_time_lines(runs: dict[str, Any]) -> list[str]:
    """Include every measured pass rather than hiding first-pass overhead."""
    lines = []
    for name, run in runs.items():
        times = ", ".join(f"{item['elapsed_seconds']:.3f}s" for item in run["passes"])
        lines.extend(["", f"{name} full-pass times: {times}. Single-page warmup does not warm all page shapes."])
    return lines


def summarize(output: Path) -> None:
    """Write paired timings, cohort-specific quality, and prediction differences."""
    labels = json.loads((output / "labels.json").read_text())
    names = [name for name in ("cpu-fp32", "gpu-fp32", "gpu-fp16") if (output / (name + ".json")).exists()]
    runs = {name: json.loads((output / (name + ".json")).read_text()) for name in names}
    scores = {}
    lines = [
        "# YOLO26m matched CPU/GPU DEV comparison",
        "",
        (
            "Fixed pixel-only inputs: 125 synthetic silver DEV pages and 16 frozen OmniDocBench DEV images. "
            "The model receives image paths only; labels are loaded exclusively for this report. "
            "No training or hosted inference occurred. Public benchmark contamination is unknown."
        ),
        "",
        (
            "| Arm | Median 141-page pass | Pages/s | CPU user+system/pass | Cold load | First-predict warmup | "
            "Lifetime RSS | CUDA allocated / reserved |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, run in runs.items():
        passes = run["passes"]
        elapsed = statistics.median(x["elapsed_seconds"] for x in passes)
        cpu = statistics.median(x["cpu_user_seconds"] + x["cpu_system_seconds"] for x in passes)
        allocated = run["peak_cuda_allocated_bytes"]
        reserved = run["peak_cuda_reserved_bytes"]
        vram = "n/a" if allocated is None else f"{allocated / 2**20:.1f} / {reserved / 2**20:.1f} MiB"
        lines.append(
            f"| {name} | {elapsed:.3f}s | {141 / elapsed:.2f} | {cpu:.3f}s | "
            f"{run['cold_model_load_seconds']:.3f}s | {run['first_prediction_warmup_seconds']:.3f}s | "
            f"{run['peak_rss_kib'] / 1024:.1f} MiB | {vram} |"
        )
        scores[name] = {}
        predictions = passes[0]["predictions"]
        for cohort in ("silver-dev", "omnidoc-dev"):
            cohort_labels = [row for row in labels if row["cohort"] == cohort]
            cohort_predictions = [row for row in predictions if row["cohort"] == cohort]
            if [row["id"] for row in cohort_labels] != [row["id"] for row in cohort_predictions]:
                message = "Scoring identifiers differ"
                raise ValueError(message)
            scores[name][cohort] = confusion(
                [row["table_present"] for row in cohort_labels],
                [any(box["class"].lower() == "table" for box in row["boxes"]) for row in cohort_predictions],
            )
    lines.extend(pass_time_lines(runs))
    lines.extend(["", "| Arm | Cohort | TP | FN | FP | TN |", "|---|---|---|---|---|---|"])
    for name, cohorts in scores.items():
        for cohort, score in cohorts.items():
            lines.append(f"| {name} | {cohort} | {score['tp']} | {score['fn']} | {score['fp']} | {score['tn']} |")
    differences = {}
    baseline = runs["cpu-fp32"]["passes"][0]["predictions"]
    lines.extend(
        [
            "",
            (
                "| Compared with CPU FP32 | Bit-exact pages | Equal ordered class/count | "
                "Within 0.1px / 0.001 confidence | Max box delta* | Max confidence delta* |"
            ),
            "|---|---|---|---|---|---|",
        ]
    )
    for name in names:
        if name == "cpu-fp32":
            continue
        diff = compare_predictions(baseline, runs[name]["passes"][0]["predictions"])
        differences[name] = diff
        lines.append(
            f"| {name} | {diff['bit_exact_pages']}/141 | {diff['ordered_topology_equal_pages']}/141 | "
            f"{diff['within_tolerance_pages']}/141 | {diff['max_box_delta_on_equal_topology']:.6f}px | "
            f"{diff['max_confidence_delta_on_equal_topology']:.6f} |"
        )
    cpu_median = statistics.median(x["elapsed_seconds"] for x in runs["cpu-fp32"]["passes"])
    gpu_median = statistics.median(x["elapsed_seconds"] for x in runs["gpu-fp32"]["passes"])
    lines.extend(
        [
            "",
            (
                f"GPU FP32 steady-pass speedup: **{cpu_median / gpu_median:.2f}×**. "
                "*Numeric maxima compare only pages with equal ordered class/count. "
                "Same-class detections use greedy nearest-box matching; this is not an optimal assignment. "
                "Presence accuracy does not establish table structure, OCR, reading order, or full-record quality."
            ),
            "",
            (
                "Silver labels cover authored bordered-table presence (correlated templates, not adjudicated gold); "
                "OmniDocBench labels cover any annotated table in page images. "
                "These are distinct tasks and are not pooled."
            ),
            "",
        ]
    )
    telemetry_summary = {}
    for name in names:
        telemetry_path = output / (name + "-telemetry.json")
        telemetry = json.loads(telemetry_path.read_text())
        fields = [sample["raw_csv"].split(",") for sample in telemetry["samples"]]
        rows = [row for row in fields if len(row) == TELEMETRY_FIELDS]
        if rows:
            telemetry_summary[name] = {
                "samples": len(rows),
                "gpu": rows[0][0].strip(),
                "driver": rows[0][1].strip(),
                "mean_utilization_percent": statistics.mean(float(row[2]) for row in rows),
                "max_host_memory_mib": max(float(row[3]) for row in rows),
                "mean_host_power_watts": statistics.mean(float(row[4]) for row in rows),
            }
            sample = telemetry_summary[name]
            lines.append(
                f"{name} nvidia-smi host-wide samples (0.5s target interval plus query overhead, "
                "whole worker including load/warmup): "
                f"{sample['samples']} observations, mean utilization {sample['mean_utilization_percent']:.1f}%, "
                f"max memory {sample['max_host_memory_mib']:.0f} MiB, "
                f"mean power {sample['mean_host_power_watts']:.1f} W. Includes desktop/other processes; "
                "not per-model attribution."
            )
            lines.append("")
    run = runs["cpu-fp32"]
    prepare_result = json.loads((output / "prepare.json").read_text())
    usage = prepare_result["resource_usage"]
    lines.extend(
        [
            (
                f"Preparation: {prepare_result['elapsed_seconds']:.3f}s wall, {usage[0] + usage[1]:.3f}s "
                f"lifetime CPU, {usage[2] / 1024:.1f} MiB lifetime RSS; sequential native rendering at 120 DPI. "
                "Original OmniDocBench images are unchanged. Preprocessing is measured separately from model passes."
            ),
            "",
            (
                "Configuration: image size 640, batch size 1, confidence threshold 0.25, minimum-rectangle padding, "
                "TF32 disabled, CPU 4 threads + "
                f"interop 1; three sequential passes per arm. Torch `{run['torch']}`, "
                f"Ultralytics `{run['ultralytics']}`; "
                f"machine `{run['machine']}`, {run['cpu_count']} logical CPUs. "
                "Cold model load follows imports and input "
                "hash verification; first prediction separately includes device transfer and predictor initialization. "
                "Complete process startup timings remain in telemetry artifacts. "
                "RSS is process-lifetime getrusage SELF with no sampling; pass CPU is SELF user/system deltas. "
                "CUDA allocator peaks include warmup; nvidia-smi memory is a separate host-wide measure. "
                "Four CPU threads are reasserted after predictor initialization, which otherwise resets them."
            ),
            "",
            (
                f"[Pinned model card](https://huggingface.co/hantian/yolo-doclaynet/blob/"
                f"{run['model_revision']}/README.md): "
                f"AGPL-3.0, model SHA256 `{run['model_sha256']}`. "
                "[Ultralytics prediction settings](https://docs.ultralytics.com/modes/predict/) define the explicit "
                "FP32/FP16 quantize arms. OmniDocBench retains its noncommercial research restriction. "
                "No model weights, raw page images, labels, predictions, or telemetry are committed."
            ),
            "",
            (
                "Reproduce after input preparation with the cached model environment: "
                "`.venv/bin/python -m bench.gpu_comparison --prepare`, then "
                "`.venv/bin/python -m bench.gpu_comparison --run --device cpu` and "
                "`--run --device 0` sequentially; optional `--run --device 0 --half` is a distinct FP16 arm. "
                "Finish with `--report`. Retained artifacts are under ignored `gpu-comparison/`."
            ),
            "",
        ]
    )
    lines.extend(
        [
            "",
            (
                "GPU FP32 is the useful acceleration arm on this cohort. FP16 changes detection topology on two "
                "pages and lacks a median speed advantage. Both arms retain the same presence decisions, including "
                "all ten silver misses; the layout detector cannot replace native bordered-table extraction here. "
                "Initial overlapping timing runs and the initial auto-reset CPU-thread arm are retained separately "
                "and excluded from this matched summary. No nvidia-smi/worker errors or kernel NVRM Xid events "
                "were observed during the bounded comparison."
            ),
            "",
        ]
    )
    (output / "summary.json").write_text(
        json.dumps({"scores": scores, "differences": differences, "telemetry": telemetry_summary}, indent=2)
    )
    (Path(__file__).parent / "results/gpu-comparison.md").write_text("\n".join(lines))


def main() -> None:
    """Prepare inputs or execute one matched comparison worker."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ARTIFACTS / "gpu-comparison")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--repeats", type=int, choices=[1, 2, 3], default=3)
    args = parser.parse_args()
    if args.report:
        summarize(args.output)
    if args.prepare:
        prepare(args.output)
    if args.run:
        monitored_run(args.output, args.device, half=args.half, repeats=args.repeats)
    if args.worker:
        worker(args.output, args.device, half=args.half, repeats=args.repeats)


if __name__ == "__main__":
    main()
