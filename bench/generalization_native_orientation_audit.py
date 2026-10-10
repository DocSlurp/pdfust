"""Offline logical-native correction diagnostic; retained model responses stay fixed."""

# Explicit experimental artifacts contain heterogeneous canonical JSON.
# ruff: noqa: ANN401, EM101, TRY003, PLR2004, C901
from __future__ import annotations

import argparse
import json
import resource
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import pylopdf
from bench import pipeline_native_orientation as orientation
from bench.generalization_scoring import score_dataset
from bench.silver import guard_path, sha, write_json

RUNS = ("full276-hybrid-haiku-1024", "full276-hybrid-sonnet-1024")


def replay(root: Path, run_name: str) -> dict[str, Any]:
    """Recompose all 276 pages, preserving failed pages and every model table."""
    if run_name not in RUNS:
        raise ValueError("Unsupported retained control")
    root = guard_path(root)
    start, cpu = time.perf_counter(), time.process_time()
    inputs: dict[str, str] = {}

    def load(path: Path) -> Any:
        data = path.read_bytes()
        inputs[str(path)] = sha(data)
        return json.loads(data)

    manifest = load(root / "corpus-r2/manifest.json")
    run = root / run_name
    report = load(run / "report.json")
    verified = load(run / "verified-evaluation.json")
    if verified["report_sha256"] != inputs[str(run / "report.json")]:
        raise ValueError("Verified baseline report identity changed")
    if verified["manifest_sha256"] != inputs[str(root / "corpus-r2/manifest.json")]:
        raise ValueError("Verified baseline manifest identity changed")
    records = {p["id"]: p for p in manifest["pages"]}
    results = report["results"]
    if len(records) != 276 or len(results) != 276 or {p["id"] for p in results} != set(records):
        raise ValueError("Replay requires complete unique 276-page coverage")
    corrected, diagnostics = [], []
    for previous in results:
        if previous["status"] != "ok":
            corrected.append(deepcopy(previous))
            continue
        record = records[previous["id"]]
        path = Path(record["pdf_path"])
        data = path.read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Original frozen PDF identity changed")
        inputs[str(path)] = sha(data)
        with pylopdf.open(stream=data) as document:
            evidence = orientation.evidence(document[record["page_number"]], previous["native_boxes"])
        vision = load(run / "vision" / f"{record['id']}-structure.json")
        composed = orientation.compose(previous["source"], previous["native_state"], vision, evidence)
        count = len(previous["native_boxes"])
        if (
            composed["status"] != "ok"
            or composed["source_ledger"] != previous["source_ledger"]
            or composed["tables"][count:] != previous["tables"][count:]
            or [t["bbox"] for t in composed["tables"][:count]] != previous["native_boxes"]
        ):
            raise ValueError("Logical correction changed a required physical invariant")
        corrected.append({**previous, "composition": composed, "tables": composed["tables"],
                          "native_orientation_evidence": evidence})
        diagnostics.append({"id": record["id"], "family": record["family"], "cohort": record["cohort"],
                            "directions": [t["direction"] for t in evidence["tables"]],
                            "changed": composed["tables"] != previous["tables"]})
    # Reference access follows the committed source-only projection, never its choice.
    targets = load(root / "corpus-r2/private-targets.json")["pages"]
    baseline = score_dataset(targets, results)
    logical = score_dataset(targets, corrected)
    groups = {}
    for family in sorted({p["family"] for p in manifest["pages"]}):
        ids = {p["id"] for p in manifest["pages"] if p["family"] == family}
        selected = [t for t in targets if t["id"] in ids]
        groups[family] = {
            "baseline": score_dataset(selected, [p for p in results if p["id"] in ids])["totals"],
            "logical": score_dataset(selected, [p for p in corrected if p["id"] in ids])["totals"],
        }
    for input_path, digest in inputs.items():
        if sha(Path(input_path).read_bytes()) != digest:
            raise ValueError("Audit input changed during replay")
    dependencies = [Path(orientation.__file__), Path(__file__).with_name("generalization_scoring.py"),
                    Path(__file__).with_name("pipeline_hybrid_composition.py")]
    return {
        "diagnostic": "Offline retained-response logical-native correction; no fresh inference or productivity claim",
        "run": run_name, "spec": orientation.SPEC, "baseline": baseline, "logical": logical,
        "groups": groups, "diagnostics": diagnostics, "predictions": corrected,
        "input_sha256": inputs, "dependency_sha256": {str(p): sha(p.read_bytes()) for p in dependencies},
        "resources": {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu,
                      "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      "scope": ("Single Linux CPU process; replay wall/CPU exclude imports; "
                                "getrusage lifetime RSS includes imports")},
        "original_costs_unchanged": {key: report.get(key) for key in
                                     ("provider_reported_usd", "effective_usd", "accounted_usd", "calls")},
    }


def main() -> None:
    """Expose explicit retained controls without inference or artifact traversal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--run", choices=RUNS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = guard_path(args.output)
    if output.exists():
        raise FileExistsError("Audit output must be new; preserve retained evidence")
    result = replay(args.artifact_root, args.run)
    write_json(output, result)
    print(json.dumps({"baseline": result["baseline"]["totals"], "logical": result["logical"]["totals"],
                      "resources": result["resources"]}, indent=2))


if __name__ == "__main__":
    main()
