"""Source-only natural-page audit of the standalone Rust color component experiment."""

# Bounded experiment records retain heterogeneous measurements and literal geometry.
# ruff: noqa: EM101, TRY003, PLC0415
from __future__ import annotations

import argparse
import io
import json
import platform
import resource
import time
from pathlib import Path
from typing import Any

from bench.color_regions import extract_regions
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json


def audit(manifest_path: Path, output: Path, executable: Path) -> dict[str, Any]:
    """Freeze source-only inputs and retain every component or complete refusal."""
    from PIL import Image

    import pylopdf

    manifest_path, output, executable = map(guard_path, (manifest_path, output, executable))
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("split") != "DEV":
        raise ValueError("Color audit requires an explicit DEV manifest")
    fields = ("id", "pdf_path", "pdf_sha256", "page_number")
    records = [{key: row[key] for key in fields} for row in manifest["pages"]]
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parent
    frozen: dict[str, Any] = {
        "records": records, "manifest_sha256": sha(manifest_bytes),
        "executable_sha256": sha(executable.read_bytes()),
        "code_sha256": {name: sha((root / name).read_bytes()) for name in (
            "p003_color_audit.py", "color_regions.py", "color_regions.rs", "pipeline_run.py",
        )},
        "edges": [512, 1024], "thresholds": [8, 18, 36], "connectivity": 4,
        "minimum_page_area_fraction": 0.0005, "background_white": 248,
        "max_components": 65_536, "max_regions": 4096,
        "scope": "geometric proposals only; no semantic table or extraction quality claim",
        "machine": platform.platform(), "local_gpu_used": False,
    }
    write_json(output / "frozen.json", frozen)
    rows = []
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with Resources() as resources:
        for record in records:
            data = guard_path(Path(record["pdf_path"])).read_bytes()
            if sha(data) != record["pdf_sha256"]:
                raise ValueError("Frozen PDF bytes changed")
            with pylopdf.open(stream=data) as document:
                page = document[record["page_number"]]
                viewport = list(page.rect)
                for edge in frozen["edges"]:
                    start = time.perf_counter()
                    raster = page.render(scale=edge / max(page.rect.width, page.rect.height),
                                         background=(255, 255, 255))
                    with Image.open(io.BytesIO(raster)) as image:
                        rgb = image.convert("RGB")
                        width, height = rgb.size
                        pixels = rgb.tobytes()
                    render_seconds = time.perf_counter() - start
                    minimum_area = max(1, round(width * height * 0.0005))
                    for threshold in frozen["thresholds"]:
                        start, cpu = time.perf_counter(), time.process_time()
                        before = resource.getrusage(resource.RUSAGE_CHILDREN)
                        row: dict[str, Any] = {
                            "id": record["id"], "edge": edge, "threshold": threshold,
                            "viewport": viewport, "image_size": [width, height],
                            "rgb_sha256": sha(pixels), "min_area": minimum_area,
                            "render_rgb_seconds_once_per_edge": render_seconds,
                        }
                        try:
                            components = extract_regions(
                                pixels, width, height, color_distance=threshold,
                                luminance_distance=threshold, min_area=minimum_area, executable=executable,
                            )
                            row.update(status="ok", components=components, component_count=len(components))
                        except ValueError as error:
                            row.update(status="error", error=str(error)[:500])
                        after = resource.getrusage(resource.RUSAGE_CHILDREN)
                        row.update(
                            wall_seconds=time.perf_counter() - start,
                            parent_cpu_seconds=time.process_time() - cpu,
                            rust_child_cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                        )
                        rows.append(row)
            write_json(output / "results.json", {"rows": rows})
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    report = {
        "frozen": frozen, "rows": rows, "resources": resources.summary(),
        "rust_child_cpu_seconds": after.ru_utime + after.ru_stime - child_before.ru_utime - child_before.ru_stime,
        "maximum_child_peak_rss_kib": after.ru_maxrss,
        "child_measurement": (
            "Linux getrusage RUSAGE_CHILDREN CPU deltas for completed Rust children; "
            "maximum child peak RSS is process-lifetime maximum, separate from parent sampled RSS. "
            "Compile executable in a separate process before this audit; concurrency one."
        ),
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run a finite source-only sweep with a separately compiled local executable."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.manifest, args.output, args.executable)
    print(json.dumps({"page_variants": len(result["rows"]), "resources": result["resources"]}))


if __name__ == "__main__":
    main()
