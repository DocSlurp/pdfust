"""Authenticate source records and freeze geometry-only synthetic relationship outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import threading
import time
from collections import Counter
from pathlib import Path

import psutil
from PIL import Image

from bench import p003_synthetic_geometry as geometry

# ruff: noqa: TRY003, EM101, TRY301, C901, PLR0912, PLR2004 - bounded source-only audit.

TREATMENTS = ("bbox_physical_proxy", "direct_vector", "crop_raster128", "crop_raster512")


def digest(data: bytes) -> str:
    """Hash exact bytes, including independently supplied authorities."""
    return hashlib.sha256(data).hexdigest()


def checked(root: Path, relative: str, expected: str) -> bytes:
    """Read only explicit authenticated paths inside the source pool."""
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()) or "heldout" in str(target).lower():
        raise ValueError("Explicit source evidence path escapes permitted pool")
    data = target.read_bytes()
    if digest(data) != expected:
        raise ValueError("Source evidence digest differs")
    return data


def write(path: Path, value: object) -> None:
    """Write complete deterministic JSON, without partial evidence truncation."""
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def authenticate(pool: Path, trusted_code: Path) -> tuple[dict, list[dict]]:
    """Check external frozen/code identities without importing or executing archived generators."""
    for path in (pool, trusted_code):
        if "heldout" in str(path.resolve()).lower():
            raise ValueError("Protected source path")
    authority = json.loads(trusted_code.read_text())
    raw = checked(pool, "frozen.json", authority["source_frozen_sha256"])
    frozen = json.loads(raw)
    if frozen.get("source_only") is not True or frozen.get("intended_case_count") != 24:
        raise ValueError("Exact source-only synthetic24 pool required")
    for name, sha in frozen["code_sha256"].items():
        if authority.get(name) != sha:
            raise ValueError("Independent archived code authority differs")
        checked(pool, "code/" + name, sha)  # Bytes only; never import or decode generator source.
    records = []
    for item in frozen["records"]:
        if frozen["artifact_sha256"].get(item["path"]) != item["sha256"]:
            raise ValueError("Record and source inventory disagree")
        record = json.loads(checked(pool, item["path"], item["sha256"]))
        if record["id"] != item["id"] or record["kind"] != item["kind"]:
            raise ValueError("Source record identity differs")
        # Only extraction evidence, never counterfactual groups or authored generator plans.
        if record.get("status") == "ready":
            for image in record["images"]:
                if image["scope"] == "crop" and image["edge"] in (128, 512):
                    if frozen["artifact_sha256"].get(image["path"]) != image["sha256"]:
                        raise ValueError("Image and source inventory disagree")
                    checked(pool, image["path"], image["sha256"])
        records.append(record)
    if len(records) != 24 or len({r["id"] for r in records}) != 24:
        raise ValueError("Complete unique 24 source records required")
    return frozen, records


def run(pool: Path, trusted_code: Path, output: Path) -> dict:
    """Freeze all treatments before independent external labels or scores are consulted."""
    if output.exists():
        raise FileExistsError("Fresh output directory required")
    if "heldout" in str(output.resolve()).lower():
        raise ValueError("Protected output path")
    start, cpu = time.perf_counter(), time.process_time()
    process = psutil.Process()
    peak = [process.memory_info().rss]
    stop = threading.Event()
    def sample() -> None:
        while not stop.wait(0.1):
            peak[0] = max(peak[0], process.memory_info().rss)
    monitor = threading.Thread(target=sample, daemon=True)
    monitor.start()
    try:
        original, records = authenticate(pool, trusted_code)
        output.mkdir(parents=True)
        (output / "sources").mkdir()
        (output / "code").mkdir()
        files = ("p003_synthetic_geometry.py", "p003_synthetic_geometry_run.py")
        code = {}
        for name in files:
            data = Path(__file__).with_name(name).read_bytes()
            (output / "code" / name).write_bytes(data)
            code[name] = digest(data)
        results = []
        for record in records:
            source = {k: record.get(k) for k in ("id", "kind", "status", "pair_source_ids", "source", "drawings")}
            write(output / "sources" / (record["id"] + ".json"), source)
            for treatment in TREATMENTS:
                row = {"id": record["id"], "kind": record["kind"], "treatment": treatment}
                try:
                    if record.get("status") != "ready":
                        raise ValueError("Original source extraction refused")
                    lines = []
                    if treatment == "direct_vector":
                        lines = geometry.vector_segments(record["drawings"])
                    elif treatment.startswith("crop_raster"):
                        edge = int(treatment.removeprefix("crop_raster"))
                        image = next(i for i in record["images"] if i["scope"] == "crop" and i["edge"] == edge)
                        with Image.open(pool / image["path"]) as pixels:
                            if list(pixels.size) != image["dimensions"]:
                                raise ValueError("Authenticated image dimensions differ")
                            lines = geometry.raster_segments(pixels, image["viewport"])
                        row["image_evidence"] = image
                    row.update(geometry.classify(record, lines, physical_proxy=treatment == "bbox_physical_proxy"))
                    row["status"] = "abstained" if row["abstained"] else "classified"
                except (ValueError, KeyError, StopIteration, TypeError) as error:
                    row.update(status="source_refused", choice="unresolved", abstained=True,
                               error={"type": type(error).__name__, "message": str(error)})
                results.append(row)
        write(output / "results.json", {"results": results})
        source_inventory = {r["path"]: r["sha256"] for r in original["records"]}
        frozen = {
            "schema": 1, "processor": "p003_synthetic_geometry", "policy": geometry.POLICY,
            "treatments": TREATMENTS, "source_pool": str(pool.resolve()),
            "external_trusted_code": str(trusted_code.resolve()),
            "external_trusted_code_sha256": digest(trusted_code.read_bytes()),
            "source_frozen_sha256": digest((pool / "frozen.json").read_bytes()),
            "source_inventory": source_inventory, "code_sha256": code,
            "results_sha256": digest((output / "results.json").read_bytes()),
            "gold_read": False, "generator_imported": False, "hosted_calls": 0,
        }
        write(output / "frozen.json", frozen)
    finally:
        stop.set()
        monitor.join()
    peak[0] = max(peak[0], process.memory_info().rss)
    report = {
        "processor": "p003_synthetic_geometry", "results": results,
        "by_treatment": {name: {"case_count": 24,
                               "status_counts": dict(Counter(r["status"] for r in results if r["treatment"] == name)),
                               "choice_counts": dict(Counter(r["choice"] for r in results if r["treatment"] == name))}
                         for name in TREATMENTS},
        "metrics": {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu,
                    "sampled_peak_rss_bytes": peak[0],
                    "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    "scope": "Single CPU process including authentication and freeze; psutil RSS sampled100ms",
                    "machine_cpu_count": psutil.cpu_count(), "worker_count": 1},
        "gold_read": False, "correctness_measured": False, "source_assignments_applied": 0,
        "hosted_calls": 0, "pages_per_minute": None, "probabilities_calibrated": False,
    }
    write(output / "report.json", report)
    return report


def main() -> None:
    """Run explicitly selected source-only input pool, never hosted models."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.input, args.trusted_code, args.output)
    print(json.dumps({"by_treatment": report["by_treatment"], "metrics": report["metrics"]}, sort_keys=True))


if __name__ == "__main__":
    main()
