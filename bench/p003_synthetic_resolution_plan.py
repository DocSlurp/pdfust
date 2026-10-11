"""Freeze 25 source-only resolution arms and optionally prepare all 600 native requests."""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from bench import p003_synthetic_resolution as images
from bench import p003_synthetic_resolution_run as runner
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, PLR0913, PLR2004
SHORT = {
    "perplexity/pplx-decider-v1.1-27b": "pplx",
    "openai/gpt-6-luna-decisions": "lunadec",
    "cloudflare/clef-flash": "clefflash",
    "cloudflare/clef": "clef",
    "cloudflare/clef-omni": "clefomni",
}


def arms(source: Path, source_map: Path, pool: Path, pool_map: Path) -> list[dict[str, Any]]:
    """Use fixed resolution-first breadth ordering without model outcomes or labels."""
    return [
        {
            "name": f"synth-{SHORT[model]}-resolution-crop{edge}-r0-c3",
            "kind": "synthetic_resolution",
            "args": [
                "--source",
                str(source.resolve()),
                "--source-map",
                str(source_map.resolve()),
                "--images",
                str(pool.resolve()),
                "--image-map",
                str(pool_map.resolve()),
                "--model",
                model,
                "--image-edge",
                str(edge),
            ],
            "model": model,
            "image_edge": edge,
            "question_count": 24,
        }
        for edge in images.EDGES
        for model in images.MODELS
    ]


def build(
    source: Path, source_map: Path, pool: Path, pool_map: Path, output: Path, *, prepare_requests: bool = False
) -> dict[str, Any]:
    """Freeze complete explicit arms; preparation has no client or gold option."""
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New plan/preflight directory required")
    began, cpu = time.perf_counter(), time.process_time()
    rows = arms(source, source_map, pool, pool_map)
    with runner.adapter(source, source_map, pool, pool_map) as prepared:
        output.mkdir(parents=True)
        write_json(output / "plan.json", rows)
        receipts = []
        for arm in rows:
            config = runner.legacy.configuration(arm["model"], image_edge=arm["image_edge"])
            config["run_id"] = arm["name"]
            if prepare_requests:
                result = runner.legacy.prepare(source, source_map, output / arm["name"], config)
                if len(result["requests"]) != 24:
                    raise ValueError("Complete intended request inventory required")
                receipts.append(
                    {
                        "name": arm["name"],
                        "frozen_sha256": sha((output / arm["name"] / "frozen.json").read_bytes()),
                        "ready": sum(r["question_status"] == "ready" for r in result["requests"]),
                        "requests": [
                            {k: v for k, v in r.items() if k not in ("canonical", "wire", "encoded")}
                            for r in result["requests"]
                        ],
                    }
                )
        frozen = {
            "version": images.VERSION,
            "plan_sha256": sha((output / "plan.json").read_bytes()),
            "image_pool_sha256": sha((pool / "frozen.json").read_bytes()),
            "image_map_sha256": sha(pool_map.read_bytes()),
            "source_frozen_sha256": prepared["context"]["frozen_sha256"],
            "source_map_sha256": prepared["context"]["map_sha256"],
            "runtime_code_files": list(runner.CODE_FILES),
            "arm_count": 25,
            "intended_questions": 600,
            "retained_controls_not_repurchased": [128, 512],
            "new_api_calls": 0,
            "gold_read": False,
            "prepared_requests": prepare_requests,
            "arm_receipts": receipts,
            "resources": {
                "wall_seconds": time.perf_counter() - began,
                "cpu_seconds": time.process_time() - cpu,
                "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            },
        }
        write_json(output / "frozen.json", frozen)
        return frozen


def main() -> None:
    """Create a new immutable plan, with explicit optional source-only request preflight."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "source-map", "images", "image-map", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--prepare-requests", action="store_true")
    args = parser.parse_args()
    frozen = build(
        args.source, args.source_map, args.images, args.image_map, args.output, prepare_requests=args.prepare_requests
    )
    print(
        json.dumps(
            {
                "arm_count": frozen["arm_count"],
                "prepared_requests": frozen["prepared_requests"],
                "resources": frozen["resources"],
                "hosted_calls": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
