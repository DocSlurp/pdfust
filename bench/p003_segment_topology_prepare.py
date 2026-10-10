"""Freeze all authenticated DEV ordinal crops for a bounded segment-topology oracle."""

# ruff: noqa: EM101, TRY003, E501
from __future__ import annotations

import argparse
import json
import os
import resource
import time
from pathlib import Path
from typing import Any

from bench import p003_segment_topology as segments
from bench.p003_gate_run import authenticate
from bench.silver import canonical, guard_path, sha, write_json


def prepare(baseline: Path, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Freeze complete source-only alternatives before any independent scorer reads targets."""
    started, cpu = time.perf_counter(), time.process_time()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Refuse to overwrite an existing opportunity freeze")
    baseline, trusted_code, output = guard_path(baseline), guard_path(trusted_code), guard_path(output)
    trusted_bytes = trusted_code.read_bytes()
    original_frozen, _ = authenticate(baseline, json.loads(trusted_bytes))
    output.mkdir(parents=True, exist_ok=True)
    (output / "code").mkdir()
    (output / "sources").mkdir()
    (output / "crops").mkdir()
    code_sha256 = {}
    for name in (
        "p003_segment_topology.py",
        "p003_segment_topology_prepare.py",
        "pipeline_assembly.py",
        "pipeline_repair.py",
        "silver.py",
    ):
        raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(raw)
        code_sha256[name] = sha(raw)
    (output / "source-trusted-code.json").write_bytes(trusted_bytes)
    frozen = {
        "schema": 1,
        "policy": segments.POLICY,
        "baseline": str(baseline),
        "baseline_frozen_sha256": sha((baseline / "frozen.json").read_bytes()),
        "external_trusted_code_path": str(trusted_code),
        "external_trusted_code_sha256": sha(trusted_bytes),
        "code_sha256": code_sha256,
        "records": original_frozen["records"],
        "selection": "Every retained ordinal detector_proposal on all intended DEV pages; no references or generated text used in proposals.",
        "scope": "Conditional on detector crop acquisition; source-only bounded crop topology alternatives, not a global table oracle.",
        "references_read": False,
        "inference_calls": 0,
        "fresh_confirmation_accessed": False,
    }
    write_json(output / "frozen.json", frozen)
    pages = []
    for record in original_frozen["records"]:
        original_path = baseline / f"{record['id']}-result.json"
        original = json.loads(original_path.read_bytes())
        source = original["source"]
        source_path = f"sources/{record['id']}.json"
        write_json(output / source_path, source)
        crops, controls = [], []
        for region in original["region_plan"]["regions"]:
            if region["kind"] != "detector_proposal":
                continue
            plan = segments.freeze(source, region["source_ids"], region["bbox"])
            pool = segments.candidates(source, plan)
            folder = f"crops/{record['id']}-{region['id']}"
            (output / folder).mkdir()
            write_json(output / folder / "plan.json", plan)
            write_json(output / folder / "candidates.json", pool)
            controls.append(pool[0]["state"])
            shapes = sorted({(t["row_count"], t["col_count"]) for c in pool for t in c["state"]["tables"]})
            crops.append(
                {
                    "region_id": region["id"],
                    "folder": folder,
                    "bbox": region["bbox"],
                    "source_ids": region["source_ids"],
                    "region_sha256": sha(canonical(region)),
                    "plan_sha256": sha((output / folder / "plan.json").read_bytes()),
                    "candidates_sha256": sha((output / folder / "candidates.json").read_bytes()),
                    "status": plan["status"],
                    "owned_word_count": plan["owned_word_count"],
                    "physical_line_count": len(plan["lines"]),
                    "physical_segment_count": sum(len(line["segments"]) for line in plan["lines"]),
                    "column_boundary_count": len(plan["column_proposals"]),
                    "row_boundary_count": len(plan["row_proposals"]),
                    "candidate_count": len(pool),
                    "topology_shapes": [list(shape) for shape in shapes],
                    "distinct_shape_count": len(shapes),
                    "owned_words_omitted_count": 0,
                    "other_page_words_omitted_count": plan["other_page_words_omitted_count"],
                    "proposal_refusal_count": len(plan["proposal_refusals"]),
                    "assignment_excluded_word_count": len(plan["words_excluded_from_assignment"]),
                    "complete_context_pixel_availability": False,
                }
            )
        control = segments.compose(source, controls)
        control_path = f"sources/{record['id']}-geometry-control.json"
        write_json(output / control_path, control)
        pages.append(
            {
                "id": record["id"],
                "record": record,
                "source_path": source_path,
                "source_sha256": sha((output / source_path).read_bytes()),
                "source_identity_sha256": sha(canonical(source)),
                "word_count": len(source["words"]),
                "baseline_result_sha256": sha(original_path.read_bytes()),
                "original_rotation": original["original_rotation"],
                "effective_rotation": original["effective_rotation"],
                "geometry_control_path": control_path,
                "geometry_control_sha256": sha((output / control_path).read_bytes()),
                "status": "prepared" if crops else "no_detector_crop_all_words_unresolved",
                "crops": crops,
            }
        )
    all_crops = [c for page in pages for c in page["crops"]]
    report = {
        "schema": 1,
        "pages": pages,
        "intended_page_count": len(pages),
        "crop_count": len(all_crops),
        "candidate_count": sum(c["candidate_count"] for c in all_crops),
        "crops_with_topology_changes": sum(c["distinct_shape_count"] > 1 for c in all_crops),
        "owned_word_count": sum(c["owned_word_count"] for c in all_crops),
        "full_source_word_count": sum(p["word_count"] for p in pages),
        "frozen_sha256": sha((output / "frozen.json").read_bytes()),
        "references_read": False,
        "inference_calls": 0,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "self_cpu_seconds": time.process_time() - cpu,
            "peak_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Serial Python process, no subprocesses; authentication/preparation wall and CPU exclude imports; lifetime getrusage peak RSS includes imports, no sampling; contended; native thread counts unmeasured.",
            "thread_environment": {
                name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
            },
        },
        "oracle_contract": "Independent scorer may inspect these frozen alternatives after authentication. Exact only within the declared <=8-boundary crop language and independently declared matching/composition. Missing detector regions remain unavailable; overlapping crop states are refused by compose, not oracle merged.",
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Prepare an unscored opportunity pool without clients or model inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--trusted-code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = prepare(args.baseline, args.trusted_code, args.output)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "intended_page_count",
                    "crop_count",
                    "candidate_count",
                    "crops_with_topology_changes",
                    "resources",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
