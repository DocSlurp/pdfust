"""Authenticate DEV source and prepare relation inventories without hosted calls."""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from bench import p003_pair_relations as relations
from bench.p003_gate_run import authenticate
from bench.silver import canonical, sha


def prepare(baseline: Path, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Freeze source-only edges and geometry controls for every authenticated page."""
    started, cpu = time.perf_counter(), time.process_time()
    frozen, _ = authenticate(baseline, json.loads(trusted_code.read_text()))
    output.mkdir(parents=True, exist_ok=True)
    code = output / "code"
    code.mkdir(exist_ok=True)
    code_sha256 = {}
    for name in (
        "p003_pair_relations.py", "p003_pair_prepare.py", "decision_oplog_run.py", "pipeline_repair.py", "silver.py"
    ):
        data = Path(__file__).with_name(name).read_bytes()
        (code / name).write_bytes(data)
        code_sha256[name] = sha(data)
    pages = []
    for record in frozen["records"]:
        original = json.loads((baseline / f"{record['id']}-result.json").read_text())
        if "source" not in original:
            pages.append({"id": record["id"], "status": "source_missing", "baseline_error": original.get("error")})
            continue
        source = original["source"]
        plan = relations.freeze(source)
        control = relations.decode(source, plan, relations.geometry_control(plan))
        bodies = relations.batches(source, plan, "placeholder/no-request")
        payload = {"source": source, "plan": plan, "geometry_control": control}
        (output / f"{record['id']}-prepared.json").write_bytes(canonical(payload))
        pages.append({
            "id": record["id"], "status": "prepared", "source_words": len(source["words"]),
            "groups": len(plan["groups"]), "edges": len(plan["edges"]), "omitted_pairs": plan["omitted_pairs"],
            "native_questions": len(plan["edges"]) * len(relations.AXES), "batches": len(bodies),
            "body_bytes_max": max((len(canonical(b)) for b in bodies), default=0),
            "control_cell_groups": len(control["cell_groups"]),
            "control_unresolved_words": len(control["unresolved_ids"]),
            "control_refused_merges": len(control["refused_merges"]), "plan_sha256": plan["plan_sha256"],
            "artifact_sha256": sha(canonical(payload)),
        })
    report = {
        "baseline": str(baseline), "independent_trusted_code": str(trusted_code),
        "trusted_code_sha256": sha(trusted_code.read_bytes()), "pages": pages,
        "code_sha256": code_sha256,
        "references_read": False, "hosted_calls": 0,
        "output_scope": "source-only spatial partitions; not table accuracy or a complete table prediction",
        "resources": {
            "wall_seconds": time.perf_counter() - started, "self_cpu_seconds": time.process_time() - cpu,
            "peak_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "perf_counter/process_time/getrusage; Linux lifetime peak RSS; one CPU worker; no sampling",
        },
    }
    (output / "report.json").write_bytes(canonical(report))
    return report


def main() -> None:
    """Run preparation only; this module has no client or paid request path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.baseline, args.trusted_code, args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
