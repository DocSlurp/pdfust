"""Freeze authenticated DEV source availability bags without reading reference cells."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, E501
from __future__ import annotations

import argparse
import json
import os
import resource
import time
from pathlib import Path
from typing import Any

from bench import p003_segment_topology as segments
from bench import p003_source_availability as availability
from bench.p003_gate_run import authenticate
from bench.silver import canonical, guard_path, sha, write_json


def prepare(baseline: Path, source_trust: Path, geometry: Path, geometry_trust: Path, output: Path) -> dict[str, Any]:
    """Replay a separate frozen geometry control, then archive source-only counts and bags."""
    started, cpu = time.perf_counter(), time.process_time()
    baseline, source_trust, geometry, geometry_trust, output = [
        guard_path(p) for p in (baseline, source_trust, geometry, geometry_trust, output)
    ]
    if output.exists() and any(output.iterdir()):
        raise ValueError("Refuse to overwrite an existing source availability freeze")
    frozen, _ = authenticate(baseline, json.loads(source_trust.read_bytes()))
    control_frozen = json.loads((geometry / "frozen.json").read_bytes())
    control_report = json.loads((geometry / "report.json").read_bytes())
    approved = json.loads(geometry_trust.read_bytes())
    if not approved or not control_frozen["code_sha256"]:
        raise ValueError("External geometry code approval is required")
    for name, digest in control_frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or approved.get(name) != digest
            or sha((geometry / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Geometry archive differs from independent code approval")
    if (
        control_frozen["records"] != frozen["records"]
        or Path(control_frozen["baseline"]) != baseline
        or control_frozen["external_trusted_code_sha256"] != sha(source_trust.read_bytes())
        or control_report["frozen_sha256"] != sha((geometry / "frozen.json").read_bytes())
    ):
        raise ValueError("Geometry and source inventories differ")
    for name in ("p003_segment_topology.py", "pipeline_assembly.py", "pipeline_repair.py", "silver.py"):
        if sha(Path(__file__).with_name(name).read_bytes()) != approved.get(name):
            raise ValueError("Current geometry reconstruction helper differs from approved code")
    controls = {p["id"]: p for p in control_report["pages"]}
    if len(controls) != len(control_report["pages"]) or set(controls) != {r["id"] for r in frozen["records"]}:
        raise ValueError("Geometry control lacks the complete intended source page inventory")
    output.mkdir(parents=True, exist_ok=True)
    for folder in ("code", "pages", "trust"):
        (output / folder).mkdir()
    code_sha256 = {}
    for name in (
        "p003_source_availability.py",
        "p003_source_availability_prepare.py",
        "generalization_scoring.py",
        "p003_segment_topology.py",
        "pipeline_assembly.py",
        "pipeline_repair.py",
        "silver.py",
    ):
        data = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(data)
        code_sha256[name] = sha(data)
    for name, path in (("source", source_trust), ("geometry", geometry_trust)):
        (output / "trust" / f"{name}.json").write_bytes(path.read_bytes())
    final_frozen = {
        "schema": 1,
        "records": frozen["records"],
        "code_sha256": code_sha256,
        "source_baseline": str(baseline),
        "source_trusted_code": str(source_trust),
        "source_trusted_code_sha256": sha(source_trust.read_bytes()),
        "source_frozen_sha256": sha((baseline / "frozen.json").read_bytes()),
        "geometry_control_directory": str(geometry),
        "geometry_trusted_code": str(geometry_trust),
        "geometry_trusted_code_sha256": sha(geometry_trust.read_bytes()),
        "geometry_frozen_sha256": sha((geometry / "frozen.json").read_bytes()),
        "geometry_report_sha256": sha((geometry / "report.json").read_bytes()),
        "normalization": "generalization_scoring.normalize_text, NFC plus Unicode whitespace collapse only",
        "subsets": ["full_page", "detector_owned_union", "geometry_control_assigned"],
        "source_bags_are_optimistic_necessity_diagnostics": True,
        "references_read": False,
        "fresh_confirmation_accessed": False,
        "inference_calls": 0,
    }
    write_json(output / "frozen.json", final_frozen)
    pages = []
    for record in frozen["records"]:
        ident = record["id"]
        original = json.loads((baseline / f"{ident}-result.json").read_bytes())
        source = original["source"]
        receipt = controls[ident]
        control_source = geometry / receipt["source_path"]
        if (
            sha(control_source.read_bytes()) != receipt["source_sha256"]
            or json.loads(control_source.read_bytes()) != source
            or receipt["baseline_result_sha256"] != sha((baseline / f"{ident}-result.json").read_bytes())
        ):
            raise ValueError("Geometry source snapshot differs from authenticated ordinal source")
        detector = [r for r in original["region_plan"]["regions"] if r["kind"] == "detector_proposal"]
        if [c["region_id"] for c in receipt["crops"]] != [r["id"] for r in detector]:
            raise ValueError("Geometry detector-crop inventory changed")
        reconstructed = []
        for crop, region in zip(receipt["crops"], detector, strict=True):
            folder = geometry / crop["folder"]
            if (
                sha((folder / "plan.json").read_bytes()) != crop["plan_sha256"]
                or sha((folder / "candidates.json").read_bytes()) != crop["candidates_sha256"]
                or crop["source_ids"] != region["source_ids"]
                or crop["bbox"] != region["bbox"]
            ):
                raise ValueError("Geometry crop or complete source ownership changed")
            plan = segments.freeze(source, region["source_ids"], region["bbox"])
            if json.loads((folder / "plan.json").read_bytes()) != plan:
                raise ValueError("Source-only segment proposal replay differs")
            candidates = segments.candidates(source, plan)
            if json.loads((folder / "candidates.json").read_bytes()) != candidates:
                raise ValueError("Geometry alternative pool replay differs")
            reconstructed.append(candidates[0]["state"])
        control = segments.compose(source, reconstructed)
        control_path = geometry / receipt["geometry_control_path"]
        if (
            sha(control_path.read_bytes()) != receipt["geometry_control_sha256"]
            or json.loads(control_path.read_bytes()) != control
        ):
            raise ValueError("Actual assigned geometry control differs from reconstructed source-only state")
        audit = availability.audit(source, original["region_plan"]["regions"], control)
        page_path = f"pages/{ident}.json"
        write_json(
            output / page_path,
            {
                "id": ident,
                "record": record,
                "source": source,
                "detector_regions": detector,
                "geometry_control": control,
                "audit": audit,
            },
        )
        pages.append(
            {
                "id": ident,
                "path": page_path,
                "sha256": sha((output / page_path).read_bytes()),
                "source_sha256": sha(canonical(source)),
                "control_sha256": sha(canonical(control)),
                "original_rotation": original["original_rotation"],
                "effective_rotation": original["effective_rotation"],
                "subsets": {
                    name: {
                        k: value["bag"][k]
                        for k in (
                            "word_count",
                            "raw_codepoint_count",
                            "normalized_codepoint_count",
                            "nonspace_codepoint_count",
                            "whitespace_token_count",
                            "duplicate_normalized_word_occurrences",
                        )
                    }
                    for name, value in audit["subsets"].items()
                },
                "detector_crop_count": len(detector),
                "detector_ownership_fraction": audit["detector_ownership_fraction"],
                "geometry_assignment_fraction": audit["geometry_assignment_fraction"],
                "detector_owned_word_appearances": audit["detector_owned_word_appearances"],
                "geometry_assigned_outside_detector_union_count": len(
                    audit["geometry_assigned_outside_detector_union_ids"]
                ),
            }
        )
    report = {
        "schema": 1,
        "pages": pages,
        "intended_page_count": len(pages),
        "frozen_sha256": sha((output / "frozen.json").read_bytes()),
        "references_read": False,
        "inference_calls": 0,
        "availability_or_ceiling_score": None,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "self_cpu_seconds": time.process_time() - cpu,
            "peak_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Serial CPU Python; source authentication, exact geometry replay and bag/overlap preparation timed; imports excluded, lifetime RSS includes imports; no sampling; native threads unmeasured; contended.",
            "thread_environment": {
                name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
            },
        },
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Prepare source-only inventory; references and scoring are deliberately absent."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--source-trusted-code", type=Path, required=True)
    parser.add_argument("--geometry-control", type=Path, required=True)
    parser.add_argument("--geometry-trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(
        args.baseline, args.source_trusted_code, args.geometry_control, args.geometry_trusted_code, args.output
    )
    print(json.dumps({"pages": report["intended_page_count"], "resources": report["resources"]}, indent=2))


if __name__ == "__main__":
    main()
