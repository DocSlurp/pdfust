"""Freeze source-only row-band alternatives before independent DEV oracle scoring."""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004, C901, PLR0912
from __future__ import annotations

import argparse
import itertools
import json
import resource
import shutil
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_candidate_bands as bands
from bench import p003_candidate_choice, pipeline_vision_transcription
from bench import p003_candidate_regions_run as source
from bench import p003_candidate_run as candidate
from bench.silver import guard_path, sha, write_json

MAX_PAGE_COMPOSITIONS = 16384


def run(
    inputs: list[Path], maps: list[Path], output: Path, *, reviewed_parser_sha256: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Finish all three frozen geometry treatments before reference-free feasibility enumeration."""
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    if len(inputs) != 2 or len(maps) != 2:
        raise ValueError("Row-band controls require two explicit independent baseline/trust pairs")
    output = guard_path(output)
    if output.exists():
        raise ValueError("Row-band output must be fresh")
    source.run(inputs, maps, output / "source-admission", reviewed_parser_sha256=reviewed_parser_sha256)
    baseline = candidate._read(output / "source-admission/frozen.json")
    code = {}
    (output / "code").mkdir()
    for path in (
        Path(__file__),
        Path(bands.__file__),
        Path(p003_candidate_choice.__file__),
        Path(pipeline_vision_transcription.__file__),
    ):
        shutil.copyfile(path, output / "code" / path.name)
        code[path.name] = sha(path.read_bytes())
    inventories = {}
    for threshold in bands.THRESHOLDS:
        label = f"iou-{threshold:.2f}"
        directory = output / label
        directory.mkdir()
        inventory = {}
        for record in baseline["records"]:
            page = candidate._read(output / f"source-admission/{record['id']}-valid-region-pools.json")
            crops = []
            for crop in page["crops"]:
                valid = [a for a in crop["attempts"] if a["valid"]]
                states = [json.loads(a["canonical_json"]) for a in valid]
                if len(valid) == 2:
                    plan = bands.freeze(crop["viewport"], states, threshold=threshold)
                    alternatives = bands.alternatives(plan)
                else:
                    plan = None
                    alternatives = [
                        {
                            "canonical_json": a["canonical_json"],
                            "sha256": a["state_sha256"],
                            "provenance": [{"whole_original": a["baseline_index"]}],
                        }
                        for a in valid
                    ]
                crops.append(
                    {
                        "index": crop["index"],
                        "viewport": crop["viewport"],
                        "image_sha256": crop["image_sha256"],
                        "valid_baseline_indexes": crop["valid_baseline_indexes"],
                        "plan": plan,
                        "status": plan["status"] if plan else "fewer_than_two_valid_controls",
                        "alternatives": alternatives,
                    }
                )
            prepared = {
                "id": record["id"],
                "page_viewport": page["page_metadata"]["viewport"],
                "threshold": threshold,
                "source_admission_sha256": page["snapshot_sha256"],
                "crops": crops,
                "quality_scored": False,
            }
            write_json(directory / f"{record['id']}-bands.json", prepared)
            inventory[record["id"]] = sha((directory / f"{record['id']}-bands.json").read_bytes())
        inventories[label] = inventory
    write_json(
        output / "frozen.json",
        {
            "processor": "p003_compatible_candidate_bands_offline",
            "code_sha256": code,
            "source_admission_frozen_sha256": sha((output / "source-admission/frozen.json").read_bytes()),
            "records": baseline["records"],
            "manifest_sha256": baseline["manifest_sha256"],
            "thresholds": bands.THRESHOLDS,
            "prepared_inventory_sha256": inventories,
            "quality_references_used_in_freeze": False,
            "source_conserved": False,
        },
    )
    summary = {}
    for label in inventories:
        reports = []
        for record in baseline["records"]:
            page = candidate._read(output / label / f"{record['id']}-bands.json")
            alternatives = [c["alternatives"] for c in page["crops"]]
            combinations = 1
            for choices in alternatives:
                combinations *= len(choices)
            failures, successful = Counter(), 0
            if combinations <= MAX_PAGE_COMPOSITIONS:
                for variants in itertools.product(*alternatives):
                    try:
                        bands.compose(
                            [json.loads(v["canonical_json"]) for v in variants],
                            [c["viewport"] for c in page["crops"]],
                            page["page_viewport"],
                        )
                    except ValueError as error:
                        failures[str(error)] += 1
                    else:
                        successful += 1
            reports.append(
                {
                    "id": record["id"],
                    "complete_compositions": combinations,
                    "feasible_compositions": successful if combinations <= MAX_PAGE_COMPOSITIONS else None,
                    "status": "enumerated" if combinations <= MAX_PAGE_COMPOSITIONS else "capacity_not_enumerated",
                    "composition_failures": dict(failures),
                    "crop_statuses": dict(Counter(c["status"] for c in page["crops"])),
                    "differing_indivisible_bands": sum(
                        len(c["plan"]["differing_bands"]) for c in page["crops"] if c["plan"]
                    ),
                    "alternative_count": sum(len(c["alternatives"]) for c in page["crops"]),
                }
            )
        summary[label] = reports
    report = {
        "results": summary,
        "scope": "offline exact literal candidate row bands and atomic composition opportunity",
        "quality_scored": False,
        "local_metrics": {
            "wall_seconds": time.perf_counter() - wall_start,
            "cpu_seconds": time.process_time() - cpu_start,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "measurement": "process_time CPU; getrusage process lifetime peak RSS on Linux; no subprocesses",
            "scope": "offline source authentication, band freeze and exact composition enumeration",
        },
        "no_api_calls": True,
        "source_conserved": False,
        "pages_per_minute": None,
        "pages_per_dollar": None,
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run only source-only preparation of explicit DEV baseline controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, action="append", required=True)
    parser.add_argument("--trusted-code", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewed-parser-sha256", action="append", default=[])
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.baseline, args.trusted_code, args.output, reviewed_parser_sha256=tuple(args.reviewed_parser_sha256)
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
