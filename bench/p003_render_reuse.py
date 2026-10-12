"""CPU-only page-scoped render amortization; exact current JPEG crop contract."""

# ruff: noqa: EM101, TRY003, PLC0415, SLF001, PLR2004, S311, S603, EM102
from __future__ import annotations

import argparse
import base64
import io
import json
import platform
import random
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Self

from bench.silver import guard_path, sha, write_json

MAX_PAGE_PIXELS = 4095 * 4095
MAX_RESIDENT_RGB_BYTES = MAX_PAGE_PIXELS * 3
EDGES = (128, 256, 400, 512, 768, 1024, 1200)


class PageRender:
    """One authenticated resident RGB page; explicitly close before another page."""

    def __init__(
        self, record: dict[str, Any], page_result: dict[str, Any], *, max_rgb_bytes: int = MAX_RESIDENT_RGB_BYTES
    ) -> None:
        """Authenticate and render exactly one admitted source page."""
        from PIL import Image

        import pdfust

        self.image = None
        self.viewport = list(page_result["viewport"])
        data = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Frozen selector source PDF hash changed")
        with pdfust.open(stream=data) as document:
            page = document[record["page_number"]]
            if list(page.rect) != self.viewport or page.rotation != page_result["original_rotation"]:
                raise ValueError("Selector rerender geometry differs from frozen generation source")
            scale = 4095 / max(page.rect.width, page.rect.height)
            # Hayro uses ceil dimensions. Admission precedes allocating raster storage.
            import math

            predicted = math.ceil(page.rect.width * scale) * math.ceil(page.rect.height * scale) * 3
            if type(max_rgb_bytes) is not int or max_rgb_bytes < predicted:
                raise ValueError("One-page resident RGB memory admission refused")
            pixels = page.render(scale=scale, background=(255, 255, 255))
        with Image.open(io.BytesIO(pixels)) as rendered:
            if rendered.width * rendered.height * 3 > max_rgb_bytes:
                raise ValueError("Rendered page exceeds one-page resident RGB memory cap")
            self.image = rendered.convert("RGB")
        self.resident_rgb_bytes = self.image.width * self.image.height * 3
        self.pdf_sha256 = record["pdf_sha256"]
        self.page_number = record["page_number"]
        self.rotation = page_result["original_rotation"]

    def close(self) -> None:
        """Release the single retained page and forbid further crops."""
        if self.image is not None:
            self.image.close()
            self.image = None

    def crop(self, crop: dict[str, Any], edge: int) -> tuple[str, dict[str, Any]]:
        """Match candidate._rerender bytes exactly, with no chained resizing."""
        from PIL import Image

        image = self.image
        if image is None:
            raise ValueError("Resident page is closed")
        if type(edge) is not int or edge not in EDGES:
            raise ValueError("Unknown render comparison edge")
        box = crop["viewport"]
        if len(box) != 4 or not all(type(v) in (int, float) for v in box):
            raise ValueError("Invalid crop viewport")
        x0, y0, x1, y1 = self.viewport
        a, b, c, d = box
        if not x0 <= a < c <= x1 or not y0 <= b < d <= y1:
            raise ValueError("Crop must be wholly inside original page viewport")
        pixel_box = [
            (a - x0) * image.width / (x1 - x0),
            (b - y0) * image.height / (y1 - y0),
            (c - x0) * image.width / (x1 - x0),
            (d - y0) * image.height / (y1 - y0),
        ]
        ratio = edge / max(pixel_box[2] - pixel_box[0], pixel_box[3] - pixel_box[1])
        size = (
            max(1, round((pixel_box[2] - pixel_box[0]) * ratio)),
            max(1, round((pixel_box[3] - pixel_box[1]) * ratio)),
        )
        with image.transform(size, Image.Transform.EXTENT, pixel_box, resample=Image.Resampling.BICUBIC) as cropped:
            encoded = io.BytesIO()
            cropped.save(encoded, format="JPEG", quality=90)
        payload = encoded.getvalue()
        return "data:image/jpeg;base64," + base64.b64encode(payload).decode(), {
            "image_edge": edge,
            "image_size": list(size),
            "image_viewport": box,
            "image_sha256": sha(payload),
            "image_bytes": len(payload),
            "image_codec": "JPEG",
            "image_quality": 90,
            "rerendered": True,
        }


class Monitor:
    """Current process CPU and 100 ms sampled RSS, including native renderer threads."""

    def __enter__(self) -> Self:
        """Start the isolated resource interval."""
        import psutil

        self.process = psutil.Process()
        self.peak = self.process.memory_info().rss
        self.stop = threading.Event()
        self.start, self.cpu = time.perf_counter(), time.process_time()

        def sample() -> None:
            while not self.stop.wait(0.1):
                self.peak = max(self.peak, self.process.memory_info().rss)

        self.thread = threading.Thread(target=sample, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        """Stop sampling and retain complete interval metrics."""
        self.wall = time.perf_counter() - self.start
        self.cpu_seconds = time.process_time() - self.cpu
        self.peak = max(self.peak, self.process.memory_info().rss)
        self.stop.set()
        self.thread.join()

    def metrics(self) -> dict[str, Any]:
        """Export measured local resource values."""
        return {
            "wall_seconds": self.wall,
            "cpu_seconds": self.cpu_seconds,
            "peak_sampled_rss_bytes": self.peak,
            "measurement": "process_time CPU; psutil current-process RSS every 100ms; includes native threads",
            "scope": "local preprocessing only; no inference or pipeline extraction",
        }


def worker(job: dict[str, Any]) -> dict[str, Any]:
    """Measure one isolated page arm and retain exact output digests."""
    from bench import p003_candidate_run as candidate

    rows, setup = [], None
    with Monitor() as total:
        resident = None
        try:
            if job["arm"] == "reuse":
                with Monitor() as phase:
                    resident = PageRender(job["record"], job["page"])
                setup = phase.metrics()
            with Monitor() as warm:
                for crop in job["crops"]:
                    for edge in job["edges"]:
                        url, metadata = (
                            resident.crop(crop, edge)
                            if resident is not None
                            else candidate._rerender(job["record"], job["page"], crop, edge)
                        )
                        from PIL import Image

                        payload = base64.b64decode(url.split(",", 1)[1])
                        with Image.open(io.BytesIO(payload)) as decoded:
                            decoded_hash = sha(decoded.convert("RGB").tobytes())
                        rows.append(
                            {
                                "crop_index": crop["index"],
                                "edge": edge,
                                "metadata": metadata,
                                "encoded_sha256": sha(payload),
                                "decoded_rgb_sha256": decoded_hash,
                            }
                        )
        finally:
            if resident is not None:
                resident.close()
    return {
        "arm": job["arm"],
        "id": job["record"]["id"],
        "setup": setup,
        "warm_operations": warm.metrics(),
        "total": total.metrics(),
        "outputs": rows,
    }


def run(
    baseline: Path, trusted: Path, output: Path, *, repeats: int = 2, edges: tuple[int, ...] = EDGES
) -> dict[str, Any]:
    """Authenticate DEV inventory and run fixed matched fresh-process arms."""
    from bench import p003_candidate_run as candidate

    baseline, output = guard_path(baseline), guard_path(output)
    frozen, report, _ = candidate.authenticate(baseline, candidate._read(guard_path(trusted)))
    if len(frozen["records"]) != 16 or repeats not in (1, 2) or not edges or not set(edges) <= set(EDGES):
        raise ValueError("Render reuse targets the explicit natural16 DEV crop inventory")
    output.mkdir(parents=True, exist_ok=False)
    write_json(
        output / "frozen.json",
        {
            "baseline": str(baseline),
            "baseline_frozen_sha256": sha((baseline / "frozen.json").read_bytes()),
            "trusted_code": candidate._read(trusted),
            "records": frozen["records"],
            "manifest_sha256": frozen["manifest_sha256"],
            "edges": edges,
            "repeats": repeats,
            "seed": 3001,
            "code_sha256": sha(Path(__file__).read_bytes()),
            "baseline_renderer_sha256": sha(Path(candidate.__file__).read_bytes()),
            "python": sys.version,
            "platform": platform.platform(),
            "logical_cpus": __import__("os").cpu_count(),
            "memory_cap_scope": (
                "single resident RGB page only; transient renderer/PNG/JPEG storage measured separately"
            ),
            "acceptance": (
                "all exact encoded bytes and decoded pixels plus metadata identical; "
                ">=10% total CPU reduction; no API claim"
            ),
        },
    )
    pages = {p["id"]: p for p in report["results"]}
    measurements, equality = [], []
    rng = random.Random(3001)
    for repeat in range(repeats):
        for record in frozen["records"]:
            page = pages[record["id"]]
            crops = page.get("transcription_regions", [])
            if page["status"] != "ok" or not crops:
                continue
            arms = ["cold", "reuse"]
            rng.shuffle(arms)
            pair = {}
            for arm in arms:
                stem = f"r{repeat}-{record['id']}-{arm}"
                job = {"arm": arm, "record": record, "page": page, "crops": crops, "edges": edges}
                write_json(output / f"{stem}-job.json", job)
                command = [
                    sys.executable,
                    "-m",
                    "bench.p003_render_reuse",
                    "--worker",
                    str(output / f"{stem}-job.json"),
                ]
                began = time.perf_counter()
                process = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
                (output / f"{stem}.stdout").write_text(process.stdout)
                (output / f"{stem}.stderr").write_text(process.stderr)
                if process.returncode:
                    raise RuntimeError(f"Render worker failed: {stem}; full stderr retained")
                result = json.loads(process.stdout)
                result.update(repeat=repeat, order=arms, subprocess_wall_seconds=time.perf_counter() - began)
                write_json(output / f"{stem}-result.json", result)
                measurements.append(result)
                pair[arm] = result["outputs"]
            equality.append(
                {
                    "repeat": repeat,
                    "id": record["id"],
                    "exact_outputs_equal": pair["cold"] == pair["reuse"],
                    "crop_edge_count": len(pair["cold"]),
                }
            )
            print(
                f"repeat {repeat}: {record['id']} {len(pair['cold'])} "
                f"crops/edges equal={pair['cold'] == pair['reuse']}",
                file=sys.stderr,
            )
    summary = {
        "measurements": measurements,
        "equality": equality,
        "all_equal": all(r["exact_outputs_equal"] for r in equality),
        "no_api_calls": True,
        "pages_per_minute": None,
        "scope": "local JPEG preprocessing amortization",
        "cache": "one resident page per fresh child process; OS filesystem caches not reset; no provider cache",
        "baseline_errors": [{"id": p["id"], "status": p["status"]} for p in report["results"] if p["status"] != "ok"],
    }
    write_json(output / "report.json", summary)
    return summary


def main() -> None:
    """Run only explicit CPU DEV preflight and subprocess measurements."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--trusted-code", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repeats", type=int, choices=(1, 2), default=2)
    parser.add_argument("--edges", type=int, nargs="+", choices=EDGES, default=list(EDGES))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.loads(guard_path(args.worker).read_bytes()))))
    elif all((args.baseline, args.trusted_code, args.output)):
        run(args.baseline, args.trusted_code, args.output, repeats=args.repeats, edges=tuple(args.edges))
    else:
        parser.error("Specify baseline, independent trusted-code map and fresh output")


if __name__ == "__main__":
    main()
