"""Matched CPU-only assembly measurements on authenticated official TATR outputs."""

# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import argparse
import cProfile
import json
import platform
import pstats
import time
from pathlib import Path
from typing import Any

from bench import p003_official_tatr as baseline
from bench.pipeline_repair import _sources, validate
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

REPORT_SHA = "a108ab555a73a305bf4e7bacd2e0524bd4ac4dae246a770e74d73ca7aae276e6"
FROZEN_SHA = "81da8260d1a0d13ab183b5cd50d22aa9b92345005fef250331f1522cd34ba195"
ORDER = ("baseline", "cached_set", "cached_set", "baseline", "baseline", "cached_set")


def cached_set(source: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep every original admission while computing assigned membership once."""
    _sources(source)
    if any(p["status"] == "postprocess_error" for p in proposals):
        tables, conflicts = [], []
    else:
        candidates = [p["table"] for p in proposals if p["table"] is not None]
        conflicts = [i for i, a in enumerate(candidates) if any(
            i != j and baseline.intersection(a["bbox"], b["bbox"]) > 0
            for j, b in enumerate(candidates))]
        tables = [t for i, t in enumerate(candidates) if i not in conflicts]
        if sum(t["row_count"] * t["col_count"] for t in tables) > 4096:
            raise ValueError("Whole-page slot admission exceeded")
    assigned = [ident for t in tables for c in t["cells"] for ident in c["source_ids"]]
    assigned_set = set(assigned)
    if len(assigned) != len(assigned_set):
        raise ValueError("Cross-table source duplication")
    state = {"id": "c0", "tables": tables,
             "unresolved_ids": [w["id"] for w in source["words"] if w["id"] not in assigned_set]}
    validate(source, state)
    return {"state": state, "conflicting_table_indices": conflicts, "source_conserved": True}


def inputs(directory: Path, authority: Path) -> list[dict[str, Any]]:
    """Admit previously independently verified outputs by external identities, never gold."""
    directory, authority = guard_path(directory), guard_path(authority)
    if sha((directory / "frozen.json").read_bytes()) != FROZEN_SHA:
        raise ValueError("Official output source freeze changed")
    raw = (directory / "report.json").read_bytes()
    if sha(raw) != REPORT_SHA:
        raise ValueError("Independently reviewed output inventory changed")
    code = json.loads(authority.read_bytes())
    frozen = json.loads((directory / "frozen.json").read_bytes())
    if code != frozen["code_sha256"] or set(code) != set(baseline.CODE_FILES):
        raise ValueError("Independent code authority differs")
    for name, digest in code.items():
        if (sha(Path(baseline.__file__).with_name(name).read_bytes()) != digest
                or sha((directory / "code" / name).read_bytes()) != digest):
            raise ValueError("Executed baseline differs from pinned code")
    rows = json.loads(raw)["rows"]
    if len(rows) != 144 or len({(r["id"], r["size"], r["threshold"]) for r in rows}) != 144:
        raise ValueError("Complete unique 144-state input required")
    records = []
    for row in rows:
        name = row["path"]
        if Path(name).name != name:
            raise ValueError("Only explicit local output files admitted")
        raw = (directory / name).read_bytes()
        if sha(raw) != row["sha256"]:
            raise ValueError("Frozen composed output changed")
        records.append(json.loads(raw))
    return records


def measure(records: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    """Time complete compositions, then verify equality outside each timed call."""
    operation = baseline.compose if variant == "baseline" else cached_set
    rows = []
    with Resources() as resources:
        for record in records:
            started, cpu = time.perf_counter(), time.process_time()
            result = operation(record["source"], record["proposals"])
            elapsed, used = time.perf_counter() - started, time.process_time() - cpu
            expected = {k: record[k] for k in ("state", "conflicting_table_indices", "source_conserved")}
            if result != expected:
                raise ValueError("Composition differs from immutable original output")
            rows.append({"id": record["id"], "size": record["size"], "threshold": record["threshold"],
                         "wall_seconds": elapsed, "cpu_seconds": used,
                         "word_count": len(record["source"]["words"]), "output_equal": True})
    return {"variant": variant, "rows": rows, "scope_resources": resources.summary(),
            "composition_wall_seconds": sum(r["wall_seconds"] for r in rows),
            "composition_cpu_seconds": sum(r["cpu_seconds"] for r in rows)}


def main() -> None:
    """Run a fixed six-pass matched screen and separately instrument both implementations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = guard_path(args.output)
    if output.exists():
        raise FileExistsError("Fresh performance output required")
    records = inputs(args.input, args.trusted_code)
    output.mkdir(parents=True)
    write_json(output / "frozen.json", {
        "source_report_sha256": REPORT_SHA, "source_frozen_sha256": FROZEN_SHA,
        "baseline_authority_sha256": sha(args.trusted_code.read_bytes()),
        "experiment_code_sha256": sha(Path(__file__).read_bytes()), "order": ORDER,
        "python": platform.python_version(), "platform": platform.platform(),
        "quality_targets_read": False, "provider_calls": 0, "gpu_used": False,
        "acceptance": "All144 outputs exactly equal; >=20% median composition CPU reduction; no removed gates",
        "scope": "Warm loaded page composition only; not detector/model/decode or full-pipeline throughput",
    })
    observations = []
    for index, variant in enumerate(ORDER):
        value = measure(records, variant)
        write_json(output / f"pass-{index}-{variant}.json", value)
        observations.append(value)
        print(json.dumps({k: v for k, v in value.items() if k != "rows"}), flush=True)
    for variant in ("baseline", "cached_set"):
        profiler = cProfile.Profile()
        profiler.runcall(measure, records, variant)
        profiler.dump_stats(str(output / f"{variant}.prof"))
        with (output / f"{variant}-profile.txt").open("w") as stream:
            pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumulative").print_stats(25)
    write_json(output / "report.json", {"observations": observations, "output_equality": True,
                                        "timing_scope": "Per-call timing excludes equality; scope resources include it",
                                        "independent_process_replicates": 1, "paired_passes": 3})


if __name__ == "__main__":
    main()
