"""Freeze source-only valid-region pools, then enumerate complete composition opportunity."""

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

from bench import p003_candidate_regions as admission
from bench import p003_candidate_run as candidate
from bench.silver import guard_path, sha, write_json

MAX_COMPOSITIONS = 16384


def run(
    inputs: list[Path],
    maps: list[Path],
    output: Path,
    *,
    seed: int = 3002,
    reviewed_parser_sha256: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Finish immutable pool preparation before separately enumerating compositions."""
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    if not 2 <= len(inputs) <= 4 or len(inputs) != len(maps):
        raise ValueError("Specify 2-4 explicit baselines with separate independent trusted maps")
    inputs = [guard_path(p) for p in inputs]
    output = guard_path(output)
    baselines = [
        candidate.authenticate(p, candidate._read(m), reviewed_parser_sha256=reviewed_parser_sha256)
        for p, m in zip(inputs, maps, strict=True)
    ]
    records = baselines[0][0]["records"]
    for frozen, _, _ in baselines:
        if frozen["records"] != records or frozen["manifest_sha256"] != baselines[0][0]["manifest_sha256"]:
            raise ValueError("Matched generation baselines require identical complete PDF inventory")
    if len(records) != 16:
        raise ValueError("This explicit offline experiment targets natural16 only")
    pages = [{p["id"]: p for p in report["results"]} for _, report, _ in baselines]
    # Authentication and all-source freeze finish before output scoring/admission enumeration.
    frozen_pages = [
        admission.freeze_page(r, [p[r["id"]] for p in pages], inputs, [b[0]["config"] for b in baselines], seed=seed)
        for r in records
    ]
    output.mkdir(parents=True, exist_ok=False)
    archived = []
    for i, (directory, trusted) in enumerate(zip(inputs, maps, strict=True)):
        destination = output / f"baseline-{i}"
        destination.mkdir()
        names = {"frozen.json", "report.json", "errors.json"}
        names.update(f"{r['id']}-result.json" for r in records)
        names.update(f"{r['id']}-structure.json" for r in records)
        names.update(f"{r['id']}.md" for r in records)
        names.update(
            f"{r['id']}-request-{c['request_index']}.json"
            for r in records
            for c in pages[i][r["id"]]["transcription_regions"]
        )
        inventory = {}
        for name in sorted(names):
            if (directory / name).exists():
                shutil.copyfile(directory / name, destination / name)
                inventory[name] = sha((destination / name).read_bytes())
        shutil.copytree(directory / "code", destination / "code")
        archived.append(
            {
                "directory": str(directory),
                "copied_directory": destination.name,
                "file_sha256": inventory,
                "independent_trusted_code": candidate._read(trusted),
                "historical_generation_report": baselines[i][1],
            }
        )
    (output / "code").mkdir()
    code = {}
    for file in (Path(admission.__file__), Path(__file__), Path(candidate.__file__)):
        shutil.copyfile(file, output / "code" / file.name)
        code[file.name] = sha(file.read_bytes())
    for page in frozen_pages:
        write_json(output / f"{page['id']}-valid-region-pools.json", page)
    frozen_inventory = {
        p["id"]: sha((output / f"{p['id']}-valid-region-pools.json").read_bytes()) for p in frozen_pages
    }
    write_json(
        output / "frozen.json",
        {
            "processor": "p003_candidate_valid_regions_offline",
            "seed": seed,
            "reviewed_parser_sha256": list(reviewed_parser_sha256),
            "records": records,
            "manifest_sha256": baselines[0][0]["manifest_sha256"],
            "code_sha256": code,
            "baseline_provenance": archived,
            "valid_region_pools_sha256": frozen_inventory,
            "quality_references_used_in_freeze": False,
            "source_conserved": False,
        },
    )
    # Only complete exact retained candidates are enumerated. No scoring/reference access occurs here.
    opportunity = []
    for page in frozen_pages:
        options = []
        for crop in page["crops"]:
            unique = {}
            for attempt in crop["attempts"]:
                if attempt["valid"]:
                    unique.setdefault(attempt["canonical_json"], attempt["baseline_index"])
            options.append(list(unique.values()))
        combinations = 1
        for choices in options:
            combinations *= len(choices)
        if combinations > MAX_COMPOSITIONS:
            raise ValueError("Complete composition opportunity exceeds explicit offline cap")
        successful, failures, first = 0, Counter(), None
        for origins in itertools.product(*options):
            try:
                composed = admission.compose_selection(page, dict(enumerate(origins)))
            except ValueError as error:
                failures[str(error)] += 1
            else:
                successful += 1
                if first is None:
                    first = composed
        entry = {
            "id": page["id"],
            "historical_page_failure_gate_blocks": page["historical_page_failure_gate_blocks"],
            "complete_crop_coverage": page["complete_crop_coverage"],
            "valid_complete_compositions": successful,
            "attempted_complete_compositions": combinations,
            "composition_failures": dict(failures),
            "crop_counts": dict(Counter(c["status"] for c in page["crops"])),
        }
        if first is not None:
            write_json(output / f"{page['id']}-first-valid-composition.json", first)
        opportunity.append(entry)
    report = {
        "scope": "offline frozen whole-crop validity and atomic composition opportunity; quality unscored",
        "page_count": len(records),
        "pages_with_valid_complete_composition": sum(p["valid_complete_compositions"] > 0 for p in opportunity),
        "historical_gate_blocked_pages": sum(p["historical_page_failure_gate_blocks"] for p in opportunity),
        "newly_available_blocked_pages": sum(
            p["historical_page_failure_gate_blocks"] and p["valid_complete_compositions"] > 0 for p in opportunity
        ),
        "quality_scored": False,
        "local_metrics": {
            "wall_seconds": time.perf_counter() - wall_start,
            "cpu_seconds": time.process_time() - cpu_start,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "measurement": "process_time CPU; getrusage process lifetime peak RSS on Linux; no subprocesses",
            "scope": "offline authentication, complete pool freeze and exact composition enumeration",
        },
        "no_api_calls": True,
        "source_conserved": False,
        "pages_per_minute": None,
        "pages_per_dollar": None,
        "results": opportunity,
        "generation_cost_scope": (
            "All original baseline reports retained, including invalid candidates/errors/calls; no generation repaid"
        ),
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Require explicit retained inputs and fresh offline output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, action="append", required=True)
    parser.add_argument("--trusted-code", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=3002)
    parser.add_argument("--reviewed-parser-sha256", action="append", default=[])
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.baseline,
                args.trusted_code,
                args.output,
                seed=args.seed,
                reviewed_parser_sha256=tuple(args.reviewed_parser_sha256),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
