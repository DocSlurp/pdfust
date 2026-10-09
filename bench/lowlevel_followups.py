"""Freeze L002 prompt/transport/batching factors from source-only L001 snapshots."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import json
import random
import shutil
import time
from pathlib import Path
from typing import Any

from bench.lowlevel_evidence import IMAGE_MODELS, MODELS, digest, request, verify, write
from bench.lowlevel_prompts import transform
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss

CONFIGS = (
    *((arm, variant, 3) for variant in ("resolved", "typed", "both") for arm in ("minimal", "canonical", "vectors")),
    ("crop512", "resolved", 3),
    *((arm, "original", 1) for arm in ("minimal", "vectors", "crop512")),
)


def prepare(parent: Path, directory: Path) -> dict[str, Any]:
    """Select the shortest encoding per full-page raster hash, never by score."""
    parent, directory = guard_path(parent), guard_path(directory)
    original = verify(parent)
    if directory.exists():
        raise ValueError("Preserve prior prompt freezes; choose a new directory")
    start, cpu = time.perf_counter(), time.process_time()
    choices: dict[str, list[dict[str, Any]]] = {}
    observations = {}
    for page in original["pages"]:
        obs = json.loads((parent / page["observation_file"]).read_bytes())
        observations[page["id"]] = obs
        choices.setdefault(obs["pixel_sha256"], []).append(page)
    pages = sorted(
        (
            min(group, key=lambda p: ((parent / p["source_file"]).stat().st_size, p["source_sha256"]))
            for group in choices.values()
        ),
        key=lambda p: p["id"],
    )
    directory.mkdir(parents=True)
    for page in pages:
        for key in ("source_file", "observation_file"):
            shutil.copyfile(parent / page[key], directory / page[key])
    records: list[dict[str, Any]] = []
    arms = []
    for arm, variant, batch_size in CONFIGS:
        label = arm + "@" + ("singleton" if variant == "original" else variant)
        arms.append(label)
        for model in IMAGE_MODELS if arm.startswith("crop") else MODELS:
            for offset in range(0, len(pages), batch_size):
                ids = [p["id"] for p in pages[offset : offset + batch_size]]
                selected = [observations[ident] for ident in ids]
                body = request(selected, model, arm)
                if variant != "original":
                    body = transform(body, selected, variant)
                filename = f"request-{len(records):04d}.json"
                records.append(
                    {
                        "request": filename,
                        "sha256": write(directory / filename, body),
                        "model": model,
                        "arm": label,
                        "base_arm": arm,
                        "prompt_variant": variant,
                        "page_ids": ids,
                    }
                )
    random.Random(22617).shuffle(records)  # noqa: S311 - fixed experimental schedule.
    shutil.copyfile(parent / "catalog-prices.json", directory / "catalog-prices.json")
    rss, method = process_peak_rss()
    manifest = {
        "schema": 1,
        "models": list(MODELS),
        "arms": arms,
        "records": records,
        "pages": pages,
        "catalog_sha256": original["catalog_sha256"],
        "parent_directory": str(parent.resolve()),
        "parent_manifest_sha256": digest((parent / "manifest.json").read_bytes()),
        "selection": "Shortest source PDF per identical full-page RGB raster hash; SHA tie-break; no targets/results",
        "encoding_comparison": False,
        "code_sha256": {
            name: digest(Path(name).read_bytes())
            for name in ("bench/lowlevel_followups.py", "bench/lowlevel_prompts.py", "bench/lowlevel_evidence.py")
        },
        "preparation": {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss,
            "measurement": method + "; sequential CPU; lifetime RSS; reuses frozen source extraction, no new rendering",
        },
    }
    # Gold selection occurs strictly after the complete source-only request freeze.
    targets = json.loads((parent / "private-targets.json").read_bytes())
    if digest((parent / "private-targets.json").read_bytes()) != original["targets_sha256"]:
        raise ValueError("Parent targets changed after freeze")
    retained = {p["id"] for p in pages}
    manifest["targets_sha256"] = write(directory / "private-targets.json", [t for t in targets if t["id"] in retained])
    write(directory / "manifest.json", manifest)
    verify(directory)
    return manifest


def main() -> None:
    """Prepare prompt factors offline; inference uses the existing metered runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.parent, args.directory)
    print(
        json.dumps(
            {"pages": len(result["pages"]), "requests": len(result["records"]), "preparation": result["preparation"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
