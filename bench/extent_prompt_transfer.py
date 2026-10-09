"""Freeze existing generic evidence prompts onto an unchanged expanded union menu."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.prompt_variants_evidence import transform
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss

ROOT = Path("/home/dan/code/oss/pylopdf")
PARENT = Path(
    "/home/dan/code/oss/pdf-master-designs/bench/results/pdf-master-artifacts/rolling-topology-v1/realism-v2/union-semantic-image512-extent-v1"
)
OUTPUT = ROOT / "bench/results/pdf-master-artifacts/decisions/extent-prompt-transfer-v1"
NAMES = ("E002_cross_cell_relations", "E003_reading_order")
VERIFIER = ROOT / "bench/rolling_topology_run.py"


def sha(path: Path) -> str:
    """Hash complete retained bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory: Path) -> dict[str, Any]:
    """Use the existing topology runner's source/body verifier without client construction."""
    spec = importlib.util.spec_from_file_location("extent_transfer_verifier", VERIFIER)
    if spec is None or spec.loader is None:
        message = "Existing topology verifier cannot be loaded"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest, _sources = module.verify(directory)
    return manifest


def transfer_body(body: dict[str, Any], name: str) -> dict[str, Any]:
    """Enforce that only q0 instructions change, including nested source and pixels."""
    modified = transform(body, name)
    restored = deepcopy(modified)
    restored["questions"]["q0"]["instructions"] = body["questions"]["q0"]["instructions"]
    if restored != body:
        message = "Prompt transfer changed fields outside q0 instructions"
        raise ValueError(message)
    return modified


def freeze(parent: Path, output: Path) -> dict[str, Any]:
    """Freeze both complete prompt variants without target reads or hosted execution."""
    parent, output = guard_path(parent), guard_path(output)
    if (output / "manifest.json").exists():
        message = "Transfer already frozen; retain it or choose a new directory"
        raise ValueError(message)
    began, cpu = time.perf_counter(), time.process_time()
    manifest = verify(parent)
    output.mkdir(parents=True, exist_ok=True)
    variants = []
    for name in NAMES:
        directory = output / name
        directory.mkdir()
        derived = deepcopy(manifest)
        records = []
        for record in manifest["records"]:
            copied = deepcopy(record)
            if record["route"] == "hosted_admission":
                path = parent / record["request"]
                if sha(path) != record["sha256"]:
                    message = "Parent body changed after initial verification"
                    raise ValueError(message)
                original = json.loads(path.read_text())
                body = transfer_body(original, name)
                target = directory / record["request"]
                target.write_text(json.dumps(body, separators=(",", ":")))
                copied.update(
                    sha256=sha(target),
                    bytes=target.stat().st_size,
                    parent_request=str(path),
                    parent_request_sha256=record["sha256"],
                    prompt_variant=name,
                )
            records.append(copied)
        derived.update(
            records=records,
            prompt_variant=name,
            parent_manifest_sha256=sha(parent / "manifest.json"),
            parent_directory=str(parent),
            transform_scope="questions.q0.instructions only",
            registry_sha256=sha(Path(__file__).with_name("prompt_variants_evidence.py")),
        )
        (directory / "manifest.json").write_text(json.dumps(derived, indent=2))
        verify(directory)
        variants.append(
            {
                "name": name,
                "directory": str(directory),
                "manifest_sha256": sha(directory / "manifest.json"),
                "prepared_calls": sum(r["route"] == "hosted_admission" for r in records),
            }
        )
    rss, tool = process_peak_rss()
    summary = {
        "schema": 1,
        "parent_directory": str(parent),
        "parent_manifest_sha256": sha(parent / "manifest.json"),
        "variants": variants,
        "paid_calls": 0,
        "reference_access": "none",
        "verifier_sha256": sha(VERIFIER),
        "preparation": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss,
            "measurement": tool + "; SELF process CPU; single CPU process; no children or periodic sampling",
        },
    }
    (output / "manifest.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    """Prepare only; root owns opt-in execution of the per-variant topology manifests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=PARENT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(freeze(args.parent, args.output), indent=2))


if __name__ == "__main__":
    main()
