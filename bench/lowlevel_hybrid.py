"""Offline source-only divider routing over already frozen model decisions.

This measures paired decision changes, not actual cascade charges or latency.
The deterministic policy predates the model runs; no threshold is fitted here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from bench.decision_hosted import checkpoint
from bench.lowlevel_geometry import POLICY, grouping
from bench.lowlevel_run import evaluate, verify_directory
from bench.silver import guard_path, rss_bytes


def source_decision(observation: dict[str, Any]) -> str:
    """Apply only admitted drawing geometry and the supplied task selectors."""
    selector = observation["selector"]
    return grouping(observation["drawings"], selector["target"]["boxes"], task=selector["task"])


def compare(directory: Path, output: Path) -> dict[str, Any]:
    """Freeze source routing before loading outcome labels, then retain every loss."""
    directory, output = guard_path(directory), guard_path(output)
    manifest = verify_directory(directory)
    started, cpu = time.perf_counter(), time.process_time()
    routing = {
        page["id"]: source_decision(json.loads((directory / page["observation_file"]).read_bytes()))
        for page in manifest["pages"]
    }
    policy = {
        "policy": POLICY,
        "manifest_sha256": hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
        "geometry_module_sha256": hashlib.sha256(
            Path(__file__).with_name("lowlevel_geometry.py").read_bytes()
        ).hexdigest(),
        "routing": routing,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "scope": "serial saved-observation reads and geometry decisions; excludes freeze verification and scoring",
            "measurement": "perf_counter, process_time, process-lifetime VmHWM; no sampling",
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    checkpoint(output / "routing-before-scoring.json", policy)
    evaluation = evaluate(directory)
    cohorts = []
    for original in evaluation["cohorts"]:
        rows = [
            row for row in evaluation["outcomes"] if (row["model"], row["arm"]) == (original["model"], original["arm"])
        ]
        paired = [row for row in rows if row["choice"] is not None]
        records = {
            record["sha256"]: record
            for record in manifest["records"]
            if (record["model"], record["arm"]) == (original["model"], original["arm"])
        }
        hybrid = {
            row["id"]: routing[row["id"]] if routing[row["id"]] != "unresolved" else row["choice"] for row in rows
        }
        cohorts.append(
            {
                "model": original["model"],
                "arm": original["arm"],
                "inputs": len(rows),
                "paired": len(paired),
                "known_inputs": sum(row["expected"] != "unresolved" for row in rows),
                "paired_known": sum(row["expected"] != "unresolved" for row in paired),
                "direct_known_exact": sum(
                    row["expected"] != "unresolved" and row["choice"] == row["expected"] for row in paired
                ),
                "hybrid_known_exact": sum(
                    row["expected"] != "unresolved" and hybrid[row["id"]] == row["expected"] for row in paired
                ),
                "paired_ambiguous": sum(row["expected"] == "unresolved" for row in paired),
                "direct_ambiguous_abstain": sum(
                    row["expected"] == "unresolved" and row["choice"] == "unresolved" for row in paired
                ),
                "hybrid_ambiguous_abstain": sum(
                    row["expected"] == "unresolved" and hybrid[row["id"]] == "unresolved" for row in paired
                ),
                "gains": sum(
                    row["choice"] != row["expected"] and hybrid[row["id"]] == row["expected"] for row in paired
                ),
                "losses": sum(
                    row["choice"] == row["expected"] and hybrid[row["id"]] != row["expected"] for row in paired
                ),
                "source_decisive": sum(routing[row["id"]] != "unresolved" for row in rows),
                "whole_bodies_skippable": sum(
                    all(routing[ident] != "unresolved" for ident in record["page_ids"]) for record in records.values()
                ),
                "planned_bodies": len(records),
            }
        )
    result = {
        "policy": policy,
        "cohorts": cohorts,
        "scope": "offline paired replay; actual cascade cost and latency unmeasured",
    }
    checkpoint(output / "evaluation.json", result)
    lines = [
        "# Source-only geometry plus decision-model replay",
        "",
        (
            "The previously frozen divider policy handles decisive geometry; the model handles deferred regions. "
            "This offline replay measures paired decisions only. Actual cascade cost and latency are unmeasured. "
            "Missing model outcomes remain in the all-input column and are excluded from paired comparisons. "
            "Known scores inherit provisional authored references, not independent full-table validation."
        ),
        "",
        (
            "| Model | Arm | Paired/all | Known direct → hybrid / paired "
            "| Ambiguous abstain direct → hybrid / paired | Gains | Losses | Whole bodies potentially skipped/all |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| {row['model']} | {row['arm']} | {row['paired']}/{row['inputs']} "
        f"| {row['direct_known_exact']} → {row['hybrid_known_exact']} / {row['paired_known']} "
        f"| {row['direct_ambiguous_abstain']} → {row['hybrid_ambiguous_abstain']} / {row['paired_ambiguous']} "
        f"| {row['gains']} | {row['losses']} | {row['whole_bodies_skippable']}/{row['planned_bodies']} |"
        for row in cohorts
    )
    lines.extend(
        [
            "",
            (
                "Interpreted strokes do not establish clip-resolved visibility. Loose selector centers, "
                "decorative rules and enclosure assumptions remain limitations. Partial batches cannot be removed "
                "without changing the original model input; the body count includes only wholly bypassable requests."
            ),
            "",
            "Routing resources: `" + json.dumps(policy["resources"], sort_keys=True) + "`.",
            "",
        ]
    )
    (output / "report.md").write_text("\n".join(lines))
    return result


def main() -> None:
    """Run a local retained-response comparison without credentials or inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.directory, args.output)
    print(json.dumps({"cohorts": len(result["cohorts"]), "scope": result["scope"]}))


if __name__ == "__main__":
    main()
