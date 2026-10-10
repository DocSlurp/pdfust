"""Matched CPU YOLO input-resolution experiment over one frozen DEV source raster per page."""

# ruff: noqa: EM101, TRY003, PLR2004, PLC0415, E501, ANN401, TRY301, S603
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import subprocess
import time
from pathlib import Path
from typing import Any

SIZES = (640, 1024, 1280)
SOURCE_EDGE = 1536
MAX_PIXELS = 4_000_000
MAX_BOXES = 1024
MODEL = Path(
    "/home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt"
)
MODEL_PYTHON = Path("/home/dan/.cache/pylopdf-structure-bench/bin/python")
CODE_FILES = ("p003_yolo_resolution.py", "p003_yolo_resolution_worker.py")


def encode(value: Any) -> bytes:
    """Canonical finite JSON bytes for archived identities."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(path: Path) -> str:
    """Hash bounded local artifacts without copying complete model weights."""
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            result.update(chunk)
    return result.hexdigest()


def write(path: Path, value: Any) -> None:
    """Write canonical source-only experiment receipts."""
    path.write_bytes(encode(value))


def configuration(size: int) -> dict[str, Any]:
    """Match the existing detector contract, changing only imgsz and declared CPU thread bound."""
    if type(size) is not int or size not in SIZES:
        raise ValueError("Unsupported frozen resolution arm")
    return {
        "device": "cpu",
        "imgsz": size,
        "batch": 1,
        "conf": 0.25,
        "quantize": "fp32",
        "verbose": False,
        "max_det": MAX_BOXES + 1,
    }


def project(boxes: list[dict[str, Any]], viewport: list[float], image_size: list[int]) -> list[dict[str, Any]]:
    """Retain every returned class and map actual source pixels into exact display viewport."""
    if (
        len(boxes) > MAX_BOXES
        or len(viewport) != 4
        or any(type(v) not in (int, float) or not math.isfinite(v) for v in viewport)
        or viewport[2] <= viewport[0]
        or viewport[3] <= viewport[1]
        or len(image_size) != 2
        or any(type(v) is not int or v <= 0 for v in image_size)
        or math.prod(image_size) > MAX_PIXELS
    ):
        raise ValueError("Invalid complete detector geometry admission")
    result = []
    for box in boxes:
        coords = box["pixel_bbox"]
        conf = box["confidence"]
        if (
            type(box["class_id"]) is not int
            or box["class_id"] < 0
            or not isinstance(box["label"], str)
            or type(conf) not in (int, float)
            or not math.isfinite(conf)
            or not 0 <= conf <= 1
            or len(coords) != 4
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in coords)
            or coords[0] < 0
            or coords[1] < 0
            or coords[2] > image_size[0]
            or coords[3] > image_size[1]
            or coords[2] <= coords[0]
            or coords[3] <= coords[1]
        ):
            raise ValueError("Detector returned invalid or out-of-frame box; no clipping repair")
        sx, sy = (viewport[2] - viewport[0]) / image_size[0], (viewport[3] - viewport[1]) / image_size[1]
        result.append(
            {
                **box,
                "global_bbox": [
                    viewport[0] + coords[0] * sx,
                    viewport[1] + coords[1] * sy,
                    viewport[0] + coords[2] * sx,
                    viewport[1] + coords[3] * sy,
                ],
            }
        )
    return result


def prepare(baseline: Path, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Authenticate all16 ordinal sources and finish code/model/input freezing before CPU inference."""
    from PIL import Image

    import pylopdf
    from bench.p003_gate_run import authenticate
    from bench.silver import guard_path

    baseline, trusted_code, output = [guard_path(p) for p in (baseline, trusted_code, output)]
    if output.exists():
        raise FileExistsError("Resolution experiment requires a new output directory")
    began, cpu = time.perf_counter(), time.process_time()
    frozen, _ = authenticate(baseline, json.loads(trusted_code.read_bytes()))
    if len(frozen["records"]) != 16 or not MODEL.is_file() or not MODEL_PYTHON.is_file():
        raise ValueError("Complete intended16 and pinned existing model environment required")
    output.mkdir(parents=True)
    for name in ("code", "inputs", "sources", "results", "trust"):
        (output / name).mkdir()
    code = {}
    for name in CODE_FILES:
        data = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(data)
        code[name] = hashlib.sha256(data).hexdigest()
    (output / "trust" / "source.json").write_bytes(trusted_code.read_bytes())
    pages = []
    for record in frozen["records"]:
        ident = record["id"]
        entry: dict[str, Any] = {"id": ident, "record": record, "status": "error", "intended_sizes": list(SIZES)}
        try:
            original_path = baseline / f"{ident}-result.json"
            original = json.loads(original_path.read_bytes())
            source = original["source"]
            source_path = output / "sources" / f"{ident}.json"
            write(source_path, source)
            raw = guard_path(Path(record["pdf_path"])).read_bytes()
            if hashlib.sha256(raw).hexdigest() != record["pdf_sha256"]:
                raise ValueError("Source PDF bytes differ from authenticated original")
            with pylopdf.open(stream=raw) as document:
                page = document[record["page_number"]]
                viewport = list(page.rect)
                if (
                    viewport != source["page_size"]
                    or page.rotation != original["original_rotation"]
                    or original["effective_rotation"] != original["original_rotation"]
                ):
                    raise ValueError("Retained source display geometry/rotation differs; no normalization")
                scale = SOURCE_EDGE / max(viewport[2] - viewport[0], viewport[3] - viewport[1])
                pixels = page.render(scale=scale, background=(255, 255, 255))
            import io

            with Image.open(io.BytesIO(pixels)) as rendered:
                if math.prod(rendered.size) > MAX_PIXELS or max(rendered.size) > SOURCE_EDGE + 1:
                    raise ValueError("Whole source raster exceeds fixed pixel admission")
                image = rendered.convert("RGB")
                image_path = output / "inputs" / f"{ident}.png"
                image.save(image_path, format="PNG", compress_level=6, optimize=False)
                image_size = list(image.size)
            entry.update(
                status="ready",
                source_path=str(source_path.relative_to(output)),
                source_sha256=digest(source_path),
                baseline_result_sha256=digest(original_path),
                image_path=str(image_path.relative_to(output)),
                image_sha256=digest(image_path),
                image_bytes=image_path.stat().st_size,
                image_size=image_size,
                viewport=viewport,
                original_rotation=original["original_rotation"],
                effective_rotation=original["effective_rotation"],
                source_word_count=len(source["words"]),
            )
        except (ValueError, KeyError, OSError, RuntimeError) as error:
            entry.update(
                error_type=type(error).__name__,
                reason="Source preparation failed; preserve all3 intended arms, no retry",
            )
        pages.append(entry)
    manifest = {
        "schema": 1,
        "processor": "p003_yolo_resolution",
        "records": frozen["records"],
        "pages": pages,
        "code_sha256": code,
        "model_path": str(MODEL),
        "model_sha256": digest(MODEL),
        "model_bytes": MODEL.stat().st_size,
        "model_revision": MODEL.parent.name,
        "model_python": str(MODEL_PYTHON),
        "sizes": list(SIZES),
        "configurations": {str(s): configuration(s) for s in SIZES},
        "source_edge": SOURCE_EDGE,
        "max_pixels": MAX_PIXELS,
        "cpu_threads": 2,
        "interop_threads": 1,
        "baseline": str(baseline),
        "external_trusted_code": str(trusted_code),
        "external_trusted_code_sha256": digest(trusted_code),
        "baseline_frozen_sha256": digest(baseline / "frozen.json"),
        "baseline_report_sha256": digest(baseline / "report.json"),
        "references_read": False,
        "fresh_confirmation_accessed": False,
        "hosted_calls": 0,
        "preparation_resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Parent process_time/perf_counter; getrusage lifetime peak includes imports; preparation timer excludes imports",
            "process_scope": "Parent preparation only, no model worker; no RSS sampling",
            "sampling_interval_seconds": None,
        },
    }
    write(output / "frozen.json", manifest)
    return manifest


def run(directory: Path) -> dict[str, Any]:
    """Launch one owned local CPU worker after source freeze; never signal other campaign processes."""
    directory = directory.resolve()
    manifest = json.loads((directory / "frozen.json").read_bytes())
    if (directory / "report.json").exists():
        raise FileExistsError("No implicit repeat or overwrite of inference result")
    for name, digest_value in manifest["code_sha256"].items():
        if digest(Path(__file__).with_name(name)) != digest_value or digest(directory / "code" / name) != digest_value:
            raise ValueError("Source-frozen code differs from current worker")
    environment = os.environ.copy()
    environment.update(
        CUDA_VISIBLE_DEVICES="",
        YOLO_OFFLINE="true",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        OMP_NUM_THREADS="2",
        MKL_NUM_THREADS="2",
        OPENBLAS_NUM_THREADS="2",
    )
    with (directory / "worker.stdout").open("wb") as stdout, (directory / "worker.stderr").open("wb") as stderr:
        completed = subprocess.run(
            [
                manifest["model_python"],
                str(Path(__file__).with_name("p003_yolo_resolution_worker.py")),
                "--manifest",
                str(directory / "frozen.json"),
            ],
            env=environment,
            stdout=stdout,
            stderr=stderr,
            check=False,
            timeout=600,
        )
    if completed.returncode != 0 or not (directory / "report.json").exists():
        raise RuntimeError("Owned CPU worker failed; retain artifacts, no retry")
    return json.loads((directory / "report.json").read_bytes())


def main() -> None:
    """Explicit source-only preparation and opt-in local CPU inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-cpu", action="store_true")
    args = parser.parse_args()
    manifest = prepare(args.baseline, args.trusted_code, args.output)
    if args.run_cpu:
        report = run(args.output)
        print(json.dumps({k: v for k, v in report.items() if k != "pages"}, indent=2))
    else:
        print(
            json.dumps(
                {
                    "page_count": len(manifest["pages"]),
                    "ready_pages": sum(p["status"] == "ready" for p in manifest["pages"]),
                }
            )
        )


if __name__ == "__main__":
    main()
