"""Source-pixel CPU layout proposals with a persistent, separately metered worker."""

# Explicit experimental protocols use heterogeneous source dictionaries.
# ruff: noqa: C901, PLR0912, PLR2004, EM101, TRY003, TRY301, PLC0415, ANN401
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import io
import json
import math
import os
import resource
import selectors
import subprocess
import sys
import threading
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Self

# Same pinned local assets as bench.gpu_comparison; no download fallback.
MODEL = Path(
    "/home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/"
    "49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt"
)
MODEL_PYTHON = Path("/home/dan/.cache/pylopdf-structure-bench/bin/python")
MAX_PIXELS = 4_000_000
MAX_BODY_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_BOXES = 1024
CPU_THREADS = 4


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _box(value: Any) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("Invalid detector display box")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
        raise ValueError("Nonfinite detector display box")
    if value[2] <= value[0] or value[3] <= value[1]:
        raise ValueError("Detector display box needs positive extent")
    return list(value)


def _rss() -> int:
    # Own-process Linux RSS only; neither credentials nor GPU state are queried.
    resident = int(Path("/proc/self/statm").read_text().split()[1])
    return resident * os.sysconf("SC_PAGE_SIZE")


class _Measure:
    def __enter__(self) -> Self:
        self.wall, self.cpu = time.perf_counter(), time.process_time()
        self.samples = [_rss()]
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)
        self.thread.start()
        return self

    def _sample(self) -> None:
        while not self.stop.wait(0.1):
            self.samples.append(_rss())

    def __exit__(self, *_args: object) -> None:
        self.stop.set()
        self.thread.join()
        self.samples.append(_rss())
        self.result = {
            "wall_seconds": time.perf_counter() - self.wall,
            "cpu_seconds": time.process_time() - self.cpu,
            "peak_sampled_rss_bytes": max(self.samples),
            "current_rss_bytes": self.samples[-1],
            "worker_lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; "
            "getrusage lifetime peak RSS; no parent or subprocess usage included",
        }


def _emit(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _worker(model_path: Path, image_size: int = 640) -> None:
    """Run CPU-only YOLO with inline frames and sanitized protocol errors."""
    if type(image_size) is not int or image_size not in (640, 1024, 1280):
        raise ValueError("Detector inference size must be 640, 1024 or 1280")
    os.environ.update(CUDA_VISIBLE_DEVICES="", YOLO_OFFLINE="true", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    with _Measure() as initialization, contextlib.redirect_stdout(sys.stderr):
        import torch  # type: ignore[import-not-found]
        import ultralytics  # type: ignore[import-not-found]
        from PIL import Image
        from ultralytics import YOLO  # type: ignore[import-not-found]

        if not model_path.is_file():
            raise ValueError("Pinned local detector weights unavailable")
        torch.set_num_threads(CPU_THREADS)
        torch.set_num_interop_threads(1)
        fingerprint = _hash(model_path)
        model = YOLO(str(model_path))
        configuration = {
            "device": "cpu",
            "imgsz": image_size,
            "batch": 1,
            "conf": 0.25,
            "quantize": "fp32",
            "verbose": False,
            "max_det": MAX_BOXES + 1,
        }
        # Initialization includes predictor warmup; reassert the thread limit it resets.
        model.predict(Image.new("RGB", (128, 128), "white"), **configuration)
        torch.set_num_threads(CPU_THREADS)
    versions = {
        "python": sys.version.split()[0],
        "torch": str(torch.__version__),
        "ultralytics": ultralytics.__version__,
    }
    _emit(
        {
            "type": "ready",
            "initialization": initialization.result,
            "model_sha256": fingerprint,
            "model_revision": model_path.parent.name,
            "versions": versions,
            "configuration": configuration,
            "cpu_threads": torch.get_num_threads(),
            "device": "cpu",
            "local_gpu_used": False,
            "worker_pid": os.getpid(),
            "model_license": "AGPL-3.0",
        }
    )
    while True:
        line = sys.stdin.buffer.readline(MAX_BODY_BYTES + 1)
        if not line:
            return
        if len(line) > MAX_BODY_BYTES or not line.endswith(b"\n"):
            _emit({"type": "error", "error_type": "FrameBoundaryError"})
            return
        response: dict[str, Any]
        with _Measure() as measurement:
            try:
                request = json.loads(line)
                if set(request) != {"image_base64"} or not isinstance(request["image_base64"], str):
                    raise ValueError("Only inline source pixels are admitted")
                pixels = base64.b64decode(request["image_base64"], validate=True)
                with Image.open(io.BytesIO(pixels)) as original:
                    width, height = original.size
                    if width * height > MAX_PIXELS or min(width, height) < 1:
                        raise ValueError("Decoded image exceeds frame admission")
                    original.load()
                    rgba = original.convert("RGBA")
                    image = Image.new("RGB", original.size, "white")
                    image.paste(rgba, mask=rgba.getchannel("A"))
                    with contextlib.redirect_stdout(sys.stderr):
                        result = model.predict(image, **configuration)[0]
                    torch.set_num_threads(CPU_THREADS)
                if len(result.boxes) > MAX_BOXES:
                    raise ValueError("Complete detector output exceeds box admission")
                boxes = [
                    {
                        "label": model.names[int(label)],
                        "confidence": float(confidence),
                        "pixel_bbox": [float(v) for v in coordinates],
                    }
                    for label, confidence, coordinates in zip(
                        result.boxes.cls.cpu().tolist(),
                        result.boxes.conf.cpu().tolist(),
                        result.boxes.xyxy.cpu().tolist(),
                        strict=True,
                    )
                ]
                response = {"type": "result", "image_size": [width, height], "boxes": boxes}
            except Exception as error:
                # Never serialize exception strings, frame content, paths, or stderr.
                response = {"type": "error", "error_type": type(error).__name__}
        response.update(
            metrics=measurement.result,
            model_sha256=fingerprint,
            versions=versions,
            cpu_threads=torch.get_num_threads(),
            device="cpu",
        )
        _emit(response)


class LayoutDetector:
    """One serialized CPU worker; lifecycle and accounting are independent of root."""

    def __init__(  # noqa: PLR0913 - explicit bounded worker lifecycle and inference configuration.
        self,
        *,
        model: Path = MODEL,
        python: Path = MODEL_PYTHON,
        worker_script: Path | None = None,
        initialization_timeout: float = 120,
        request_timeout: float = 120,
        image_size: int = 640,
    ) -> None:
        """Initialize one local CPU worker with bounded protocol deadlines."""
        if type(image_size) is not int or image_size not in (640, 1024, 1280):
            raise ValueError("Detector inference size must be 640, 1024 or 1280")
        if min(initialization_timeout, request_timeout) <= 0 or not all(
            math.isfinite(v) for v in (initialization_timeout, request_timeout)
        ):
            raise ValueError("Detector timeouts must be finite and positive")
        if not model.is_file() or not python.is_file():
            raise ValueError("Local detector model or environment unavailable")
        env = os.environ.copy()
        env.update(
            CUDA_VISIBLE_DEVICES="",
            YOLO_OFFLINE="true",
            HF_HUB_OFFLINE="1",
            TRANSFORMERS_OFFLINE="1",
            OMP_NUM_THREADS="4",
            MKL_NUM_THREADS="4",
        )
        self.process = subprocess.Popen(  # noqa: S603 - explicit local Python and reviewed worker source.
            [str(python), "-u", str(worker_script or Path(__file__).resolve()), "--worker", "--model", str(model),
             *(["--image-size", str(image_size)] if image_size != 640 else [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        self.lock, self.buffer = threading.Lock(), bytearray()
        self.request_timeout = request_timeout
        self.closed = False
        if self.process.stdin is None or self.process.stdout is None:
            self.close()
            raise RuntimeError("Detector worker pipes unavailable")
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        try:
            self.initialization = self._read(time.monotonic() + initialization_timeout)
            if self.initialization.get("type") != "ready" or self.initialization.get("device") != "cpu":
                raise RuntimeError("Detector CPU initialization failed")
            if image_size != 640 and self.initialization.get("configuration", {}).get("imgsz") != image_size:
                raise RuntimeError("Detector worker did not acknowledge the requested inference size")
        except BaseException:
            self.close()
            raise

    def _read(self, deadline: float) -> dict[str, Any]:
        if self.process.stdout is None:
            raise RuntimeError("Detector worker stdout unavailable")
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError("Detector worker response timed out")
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError("Detector worker exited before response")
                self.buffer.extend(chunk)
                if len(self.buffer) > MAX_RESPONSE_BYTES:
                    raise ValueError("Detector response exceeds complete output boundary")
        line, _, remaining_buffer = self.buffer.partition(b"\n")
        self.buffer = bytearray(remaining_buffer)
        value = json.loads(line)
        if not isinstance(value, dict):
            raise TypeError("Detector response must be an object")
        return value

    def _write(self, payload: bytes, deadline: float) -> None:
        if self.process.stdin is None:
            raise RuntimeError("Detector worker stdin unavailable")
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            offset = 0
            while offset < len(payload):
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError("Detector worker frame write timed out")
                offset += os.write(self.process.stdin.fileno(), payload[offset : offset + 65536])

    def detect(self, image: bytes, *, viewport: list[float]) -> dict[str, Any]:
        """Map admitted pixel proposals to one explicit global display viewport."""
        display = _box(viewport)
        if len(image) > MAX_BODY_BYTES:
            raise ValueError("Encoded detector image exceeds frame boundary")
        body = json.dumps({"image_base64": base64.b64encode(image).decode()}, separators=(",", ":")).encode() + b"\n"
        if len(body) > MAX_BODY_BYTES:
            raise ValueError("Serialized detector frame exceeds body boundary")
        with self.lock:
            if self.closed:
                raise RuntimeError("Detector worker is closed")
            try:
                deadline = time.monotonic() + self.request_timeout
                self._write(body, deadline)
                result = self._read(deadline)
                if result.get("type") != "result":
                    raise RuntimeError("Detector rejected the complete frame")
                width, height = result["image_size"]
                if (
                    type(width) is not int
                    or type(height) is not int
                    or min(width, height) < 1
                    or width * height > MAX_PIXELS
                ):
                    raise ValueError("Invalid admitted detector frame dimensions")
                if len(result["boxes"]) > MAX_BOXES:
                    raise ValueError("Too many detector boxes")
                for box in result["boxes"]:
                    coords = _box(box["pixel_bbox"])
                    confidence = box["confidence"]
                    if (
                        not isinstance(box["label"], str)
                        or isinstance(confidence, bool)
                        or not isinstance(confidence, (int, float))
                    ):
                        raise TypeError("Invalid detector label or confidence")
                    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                        raise ValueError("Invalid detector confidence")
                    if coords[0] < 0 or coords[1] < 0 or coords[2] > width or coords[3] > height:
                        raise ValueError("Detector box extends outside admitted pixels")
                    normalized = [coords[0] / width, coords[1] / height, coords[2] / width, coords[3] / height]
                    box["normalized_bbox"] = normalized
                    box["bbox"] = [
                        display[0] + normalized[0] * (display[2] - display[0]),
                        display[1] + normalized[1] * (display[3] - display[1]),
                        display[0] + normalized[2] * (display[2] - display[0]),
                        display[1] + normalized[3] * (display[3] - display[1]),
                    ]
                result["viewport"] = display
            except BaseException:
                self.close()
                raise
            else:
                return result

    def close(self) -> None:
        """Stop, kill if needed, close pipes, and always reap the child process."""
        if self.closed:
            return
        self.closed = True
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()

    def __enter__(self) -> Self:
        """Use this already initialized worker in a managed lifetime."""
        return self

    def __exit__(self, *_args: object) -> None:
        """Reap the worker at context exit."""
        self.close()


def detector_regions(
    page: dict[str, Any],
    detections: list[dict[str, Any]],
    *,
    max_words: int = 256,
    max_characters: int = 8000,
    minimum_confidence: float = 0.25,
) -> dict[str, Any]:
    """Use table boxes as proposals; preserve native grids and every word once."""
    from bench.pipeline_regions import MAX_REGIONS, split

    if not 0 <= minimum_confidence <= 1 or not math.isfinite(minimum_confidence):
        raise ValueError("Invalid detector proposal threshold")
    if len(detections) > MAX_BOXES:
        raise ValueError("Detector proposals exceed page boundary")
    baseline = split(page, max_words=max_words, max_characters=max_characters)
    native = [deepcopy(r) for r in baseline["regions"] if r["kind"] == "native"]
    native_ids = {i for r in native for i in r["source_ids"]}
    residual = [w for w in baseline["words"] if w["id"] not in native_ids]
    proposals = []
    for index, detection in enumerate(detections):
        bbox = _box(detection["bbox"])
        confidence, label = detection["confidence"], detection["label"]
        if isinstance(confidence, bool) or not isinstance(confidence, (float, int)) or not math.isfinite(confidence):
            raise ValueError("Invalid proposal confidence")
        if not 0 <= confidence <= 1 or not isinstance(label, str):
            raise ValueError("Invalid proposal label or confidence")
        if label.casefold() == "table" and confidence >= minimum_confidence:
            proposals.append((index, bbox, confidence))
    owned: dict[int, list[dict[str, Any]]] = {index: [] for index, _, _ in proposals}
    outside, conflicts = [], 0
    for word in residual:
        box = word["bbox"]
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        candidates = []
        for index, bbox, confidence in proposals:
            if bbox[0] <= cx <= bbox[2] and bbox[1] <= cy <= bbox[3]:
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                candidates.append((confidence, -area, -index, index))
        if candidates:
            conflicts += len(candidates) > 1
            owned[max(candidates)[-1]].append(word)
        else:
            outside.append(word)
    regions = list(native)
    empty = 0
    for index, bbox, confidence in proposals:
        words = owned[index]
        if not words:
            empty += 1
            continue
        if len(words) <= max_words and sum(len(w["id"]) + len(w["text"]) for w in words) <= max_characters:
            parts = [
                {
                    "source": {"page_size": baseline["page_size"], "words": deepcopy(words), "vector_candidates": []},
                    "source_ids": [w["id"] for w in words],
                    "bbox": bbox,
                    "boundary": "detector_table",
                    "context_complete": True,
                    "kind": "detector_proposal",
                }
            ]
        else:
            parts = split(
                {"page_size": baseline["page_size"], "words": words, "vector_candidates": []},
                max_words=max_words,
                max_characters=max_characters,
            )["regions"]
            for part in parts:
                part.update(boundary="detector_capacity", context_complete=False, kind="detector_proposal")
        for part in parts:
            part["detector"] = {
                "index": index,
                "confidence": confidence,
                "bbox": bbox,
                "semantic_status": "proposal_only",
            }
            regions.append(part)
    if outside:
        regions.extend(
            split(
                {"page_size": baseline["page_size"], "words": outside, "vector_candidates": []},
                max_words=max_words,
                max_characters=max_characters,
            )["regions"]
        )
    if len(regions) > MAX_REGIONS:
        raise ValueError("Detector complete region count exceeds admission")
    for i, region in enumerate(regions):
        region["id"] = f"r{i}"
    if Counter(i for r in regions for i in r["source_ids"]) != Counter(w["id"] for w in baseline["words"]):
        raise ValueError("Detector partition violates complete source ownership")
    return {
        "page_size": baseline["page_size"],
        "words": baseline["words"],
        "regions": regions,
        "coordinate_space": "display_global",
        "detector_diagnostics": {
            "table_proposals": len(proposals),
            "empty_table_proposals": empty,
            "overlapping_word_candidates": conflicts,
            "native_regions_preserved": len(native),
            "semantic_status": "Source-only proposals; not table labels or cell topology",
        },
    }


def baseline(
    manifest_path: Path, output: Path, *, sources_directory: Path | None = None, image_size: int = 640
) -> dict[str, Any]:
    """Render an explicit DEV manifest and retain detector statistics without gold."""
    import pdfust
    from bench.pipeline_run import source
    from bench.silver import guard_path, sha, write_json

    manifest = json.loads(guard_path(manifest_path).read_bytes())
    if manifest.get("split") != "DEV":
        raise ValueError("Detector baseline requires explicit DEV sources")
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=False)
    root_wall, root_cpu = time.perf_counter(), time.process_time()
    predictions = []
    with LayoutDetector(image_size=image_size) as detector:
        initialization = detector.initialization
        for record in manifest["pages"]:
            before_wall, before_cpu = time.perf_counter(), time.process_time()
            row: dict[str, Any] = {"id": record["id"], "status": "error"}
            try:
                data = guard_path(Path(record["pdf_path"])).read_bytes()
                if sha(data) != record["pdf_sha256"]:
                    raise ValueError("Frozen detector source PDF changed")
                with pdfust.open(stream=data) as document:
                    page = document[record["page_number"]]
                    if page.rotation:
                        page.set_rotation(0)
                    width, height = page.rect.width, page.rect.height
                    scale = min(1600 / max(width, height), math.sqrt(MAX_PIXELS / (width * height)))
                    pixels = page.get_pixmap(scale=scale, background=(255, 255, 255)).tobytes()
                    snapshot = (
                        source(page)
                        if sources_directory is None
                        else json.loads(guard_path(sources_directory / f"{record['id']}-result.json").read_bytes())[
                            "source"
                        ]
                    )
                    result = detector.detect(pixels, viewport=list(page.rect))
                    plan = detector_regions(snapshot, result["boxes"])
                    row.update(
                        status="ok",
                        detection=result,
                        partition={k: v for k, v in plan.items() if k != "words"},
                        source_words=len(snapshot["words"]),
                        source_scope="retained extraction/OCR snapshot"
                        if sources_directory
                        else "fresh native extraction; no OCR",
                    )
            except Exception as error:
                row["error_type"] = type(error).__name__
            row.update(
                root_wall_seconds=time.perf_counter() - before_wall, root_cpu_seconds=time.process_time() - before_cpu
            )
            predictions.append(row)
            write_json(output / f"{record['id']}-detector.json", row)
    report = {
        "schema": 1,
        "manifest_sha256": sha(manifest_path.read_bytes()),
        "source_only": True,
        "initialization": initialization,
        "predictions": predictions,
        "root_metrics": {
            "wall_seconds": time.perf_counter() - root_wall,
            "cpu_seconds": time.process_time() - root_cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": "Root preprocessing process only; excludes detector child CPU/RSS; no RSS sampling",
        },
        "worker_scope": (
            "Child initialization and each request retain CPU and sampled/lifetime RSS separately; do not sum peaks"
        ),
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Start the isolated worker or the explicitly requested source-only baseline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--model", type=Path, default=MODEL)
    parser.add_argument("--image-size", type=int, choices=(640, 1024, 1280), default=640)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--sources-directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        try:
            _worker(args.model, args.image_size)
        except Exception as error:
            _emit({"type": "error", "error_type": type(error).__name__})
    elif args.manifest is not None and args.output is not None:
        baseline(args.manifest, args.output, sources_directory=args.sources_directory, image_size=args.image_size)
    else:
        parser.error("Supply --manifest and --output for a source-only baseline")


if __name__ == "__main__":
    main()
