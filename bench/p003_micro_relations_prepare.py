"""Source-only DEV preflight for bounded micro native relationship questions."""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004, C901
from __future__ import annotations

import argparse
import json
import resource
import shutil
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_micro_relations as micro
from bench import p003_topology_run as source
from bench.silver import guard_path, sha, write_json


def run(
    baseline: Path, trusted_code: Path, output: Path, *, model: str = "convaiinnovations/laya", max_pairs: int = 64
) -> dict[str, Any]:
    """Freeze micro and verbose inputs without any answers, references or inference."""
    start, cpu = time.perf_counter(), time.process_time()
    baseline, output = guard_path(baseline), guard_path(output)
    trusted = json.loads(guard_path(trusted_code).read_bytes())
    frozen, report = source.authenticate_source(baseline, trusted)
    if len(frozen["records"]) != 16:
        raise ValueError("Explicit preflight targets the retained ordinal natural16 source")
    prepared = []
    by_id = {p["id"]: p for p in report["results"]}
    for record in frozen["records"]:
        original = by_id[record["id"]]
        if original["status"] != "ok":
            prepared.append({"id": record["id"], "status": "baseline_failed_skipped", "original": original})
            continue
        plan = micro.freeze(original["source"], max_pairs=max_pairs)
        pairs = []
        for pair in plan["pairs"]:
            try:
                compact = micro.body(plan, pair["id"], model)
            except micro.CapacityError as error:
                pairs.append({**pair, "status": "capacity_refused", "reason": str(error)})
                continue
            verbose = micro.body(plan, pair["id"], model, mode="verbose")
            pairs.append(
                {
                    **pair,
                    "status": "prepared",
                    "micro": compact,
                    "verbose": verbose,
                    "micro_state_utf8_bytes": len(compact["state"].encode()),
                    "verbose_state_utf8_bytes": len(verbose["state"].encode()),
                    "micro_body_utf8_bytes": len(micro._dump(compact).encode()),
                    "verbose_body_utf8_bytes": len(micro._dump(verbose).encode()),
                }
            )
        prepared.append({"id": record["id"], "status": "prepared", "original": original, "plan": plan, "pairs": pairs})
    output.mkdir(parents=True, exist_ok=False)
    (output / "code").mkdir()
    code = {}
    for name in (
        Path(__file__).name,
        "p003_micro_relations.py",
        "pipeline_row_evidence.py",
        "pipeline_regions.py",
        "p003_topology_ownership.py",
    ):
        path = Path(__file__).parent / name
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    inventory = {}
    statuses, kinds = Counter(), Counter()
    sizes = {mode: [] for mode in ("micro_state", "verbose_state", "micro_body", "verbose_body")}
    for page in prepared:
        write_json(output / f"{page['id']}-micro-plan.json", {k: v for k, v in page.items() if k != "pairs"})
        inventory[f"{page['id']}-micro-plan.json"] = sha((output / f"{page['id']}-micro-plan.json").read_bytes())
        for pair in page.get("pairs", []):
            statuses[pair["status"]] += 1
            kinds[pair["kind"]] += 1
            for mode in ("micro", "verbose"):
                if mode in pair:
                    filename = f"{page['id']}-{pair['id']}-{mode}-request.json"
                    write_json(output / filename, pair[mode])
                    inventory[filename] = sha((output / filename).read_bytes())
            if pair["status"] == "prepared":
                for mode, values in sizes.items():
                    values.append(pair[f"{mode}_utf8_bytes"])
        write_json(
            output / f"{page['id']}-micro-inventory.json",
            [{k: v for k, v in p.items() if k not in {"micro", "verbose"}} for p in page.get("pairs", [])],
        )
        inventory[f"{page['id']}-micro-inventory.json"] = sha(
            (output / f"{page['id']}-micro-inventory.json").read_bytes()
        )
    write_json(
        output / "frozen.json",
        {
            "processor": "p003_micro_relations_prepare",
            "baseline": str(baseline),
            "baseline_frozen_sha256": sha((baseline / "frozen.json").read_bytes()),
            "independent_trusted_code": trusted,
            "records": frozen["records"],
            "manifest_sha256": frozen["manifest_sha256"],
            "model": model,
            "max_pairs": max_pairs,
            "max_micro_state_bytes": micro.MAX_STATE_BYTES,
            "code_sha256": code,
            "artifact_sha256": inventory,
            "no_answers_or_references": True,
        },
    )
    result = {
        "scope": "source-only compact-vs-verbose native body preflight; no inference",
        "page_count": len(prepared),
        "page_statuses": dict(Counter(p["status"] for p in prepared)),
        "question_statuses": dict(statuses),
        "question_kinds": dict(kinds),
        "sizes": {
            mode: {
                "sum": sum(values),
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "mean": sum(values) / len(values) if values else None,
            }
            for mode, values in sizes.items()
        },
        "sampled_question_count": sum(len(p.get("pairs", [])) for p in prepared),
        "full_candidate_pair_count": sum(p.get("plan", {}).get("full_candidate_pair_count", 0) for p in prepared),
        "explicitly_omitted_candidate_pairs": sum(
            p.get("plan", {}).get("omitted_candidate_pair_count", 0) for p in prepared
        ),
        "no_api_calls": True,
        "quality_unmeasured": True,
        "pages_per_minute": None,
        "metrics": {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "measurement": "process_time CPU; process lifetime peak RSS Linux getrusage; no subprocesses",
        },
    }
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Build only CPU-local inputs for explicitly declared independent model arms."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="convaiinnovations/laya")
    parser.add_argument("--max-pairs", type=int, choices=range(1, 65), default=64)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.baseline, args.trusted_code, args.output, model=args.model, max_pairs=args.max_pairs), indent=2
        )
    )


if __name__ == "__main__":
    main()
