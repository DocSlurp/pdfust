"""Freeze all-page source-gutter controls before independent reference scoring."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_fullsource_tracks as tracks
from bench.p003_gate_run import authenticate
from bench.pipeline_run import Resources
from bench.silver import canonical, guard_path, sha, write_json

CODE_FILES = (
    "p003_fullsource_tracks.py", "p003_fullsource_tracks_prepare.py", "p003_segment_topology.py",
    "pipeline_assembly.py", "pipeline_repair.py", "silver.py",
)


def prepare(baseline: Path, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Authenticate source records, freeze nine profiles, and retain every refusal."""
    baseline, trusted_code, output = (guard_path(p) for p in (baseline, trusted_code, output))
    if output.exists():
        raise ValueError("Refuse existing experimental output")
    with Resources() as resources:
        original, _ = authenticate(baseline, json.loads(trusted_code.read_bytes()))
        output.mkdir(parents=True)
        (output / "code").mkdir()
        (output / "pages").mkdir()
        code = {}
        for name in CODE_FILES:
            data = Path(__file__).with_name(name).read_bytes()
            (output / "code" / name).write_bytes(data)
            code[name] = sha(data)
        (output / "source-trusted-code.json").write_bytes(trusted_code.read_bytes())
        frozen = {
            "schema": 1, "processor": "p003_fullsource_tracks", "records": original["records"],
            "baseline": str(baseline), "baseline_frozen_sha256": sha((baseline / "frozen.json").read_bytes()),
            "external_source_code_path": str(trusted_code),
            "external_source_code_sha256": sha(trusted_code.read_bytes()), "code_sha256": code,
            "profiles": [{"gap_em": gap, "support_fraction": support}
                         for gap in tracks.GAPS for support in tracks.SUPPORTS],
            "references_read": False, "inference_calls": 0, "fresh_confirmation_accessed": False,
            "scope": "Full-page literal source; physical rows and global gap tracks; no semantic admission",
            "page_sha256": {},
        }
        pages = []
        for record in original["records"]:
            result_path = baseline / f"{record['id']}-result.json"
            result = json.loads(result_path.read_bytes())
            source = result["source"]
            physical = tracks.physical(source)
            variants = []
            for profile in frozen["profiles"]:
                plan = tracks.prepare(source, physical, **profile)
                state = tracks.decode(source, plan)
                variants.append({"profile": profile, "plan": plan, "state": state,
                                 "state_sha256": sha(canonical(state))})
            page = {"id": record["id"], "record": record, "source": source, "physical": physical,
                    "baseline_result_sha256": sha(result_path.read_bytes()), "variants": variants}
            path = output / "pages" / f"{record['id']}.json"
            write_json(path, page)
            frozen["page_sha256"][record["id"]] = sha(path.read_bytes())
            pages.append({"id": record["id"], "source_words": len(source["words"]),
                          "physical_lines": len(physical["lines"]),
                          "geometry_excluded_words": len(physical["excluded_ids"]),
                          "variants": [{"profile": v["profile"], "status": v["plan"]["status"],
                                        "refusal": v["plan"].get("refusal"),
                                        "tables": len(v["state"]["tables"]),
                                        "unresolved_words": len(v["state"]["unresolved_ids"])} for v in variants]})
        write_json(output / "frozen.json", frozen)
    report = {
        "pages": pages, "intended_pages": len(pages), "variant_count": len(pages) * len(frozen["profiles"]),
        "status_counts": dict(Counter(v["status"] for p in pages for v in p["variants"])),
        "refusal_counts": dict(Counter(v["refusal"] for p in pages for v in p["variants"] if v["refusal"])),
        "frozen_sha256": sha((output / "frozen.json").read_bytes()), "resources": resources.summary(),
        "thread_environment": {name: os.environ.get(name) for name in
                               ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "references_read": False, "inference_calls": 0, "scores": None,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Prepare explicit source-only controls with no hosted client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--trusted-code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = prepare(args.baseline, args.trusted_code, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != "pages"}, indent=2))


if __name__ == "__main__":
    main()
