"""T005 separately frozen source-only local-gap extent alternatives."""

# ruff: noqa: EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from copy import deepcopy
from itertools import pairwise
from pathlib import Path
from statistics import median
from typing import Any, TypedDict

from bench.rolling_topology import configs as topology_configs
from bench.rolling_topology import propose as topology_propose
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss


class Config(TypedDict):
    """Independent extent policy over unchanged T003 source groupings."""

    name: str
    statistic: str
    cap_heights: float | None


_CONFIGS: tuple[Config, ...] = (
    {"name": "T005-minimum-local", "statistic": "minimum", "cap_heights": None},
    {"name": "T005-lower-quartile", "statistic": "lower_quartile", "cap_heights": None},
    {"name": "T005-first-two-capped", "statistic": "first_two", "cap_heights": 6.0},
)


def configs() -> list[Config]:
    """Return predeclared independent configs; original topology policies remain untouched."""
    return deepcopy(list(_CONFIGS))


def propose(page: dict[str, Any], policy: Config) -> dict[str, Any]:  # noqa: C901
    """Trim only detached trailing logical rows; retain original complete hypotheses separately."""
    if policy not in _CONFIGS:
        raise ValueError("Extent policy differs from the frozen declaration")
    result = topology_propose(page, topology_configs()[2])
    words = {w["id"]: w for w in page["words"]}
    candidates = []
    for original in result["candidates"]:
        table = deepcopy(original)
        if "physical_bands" not in table:
            candidates.append(table)
            continue
        columns = table["col_count"]
        rows = [table["cells"][i * columns : (i + 1) * columns] for i in range(table["row_count"])]
        boxes = [[words[i]["bbox"] for cell in row for i in cell["source_ids"]] for row in rows]
        height = median(max(1, box[3] - box[1]) for row in boxes for box in row)
        tops = [min(b[1] for b in row) for row in boxes]
        bottoms = [max(b[3] for b in row) for row in boxes]
        gaps = [b - a for a, b in pairwise(tops) if b > a]
        if not gaps:
            candidates.append(table)
            continue
        if policy["statistic"] == "minimum":
            typical = min(gaps)
        elif policy["statistic"] == "lower_quartile":
            typical = sorted(gaps)[max(0, math.ceil(len(gaps) / 4) - 1)]
        else:
            typical = median(gaps[:2])
        if policy["cap_heights"] is not None:
            typical = min(typical, height * policy["cap_heights"])
        limit = max(height * 3, typical * 2.5)
        cutoff = next((i for i in range(1, len(rows)) if tops[i] - bottoms[i - 1] > limit), len(rows))
        if cutoff < 2:
            continue
        table["row_count"] = cutoff
        table["values"] = table["values"][:cutoff]
        table["cells"] = table["cells"][: cutoff * columns]
        table["spans"] = [s for s in table["spans"] if s["row"] < cutoff]
        table["physical_bands"] = table["physical_bands"][:cutoff]
        owned = {i for cell in table["cells"] for i in cell["source_ids"]}
        table["unresolved_ids"] = [w["id"] for w in page["words"] if w["id"] not in owned]
        table["name"] = f"{policy['name']}-{len(candidates)}"
        table["status"] = "unaccepted local-gap extent hypothesis"
        candidates.append(table)
    for table in candidates:
        inventory = [i for c in table["cells"] for i in c["source_ids"]] + table["unresolved_ids"]
        if Counter(inventory) != Counter(words.keys()):
            raise ValueError("Extent candidate violated source conservation")
    return {"config": policy["name"], "candidates": candidates, "candidate_only": True}


def freeze(sources: list[Path], output: Path) -> dict[str, Any]:
    """Freeze all candidate bytes before evaluator reference access."""
    output = guard_path(output)
    if output.exists():
        raise ValueError("Preserve existing extent freeze")
    output.mkdir(parents=True)
    start, cpu = time.perf_counter(), time.process_time()
    cohorts = []
    for path in sources:
        raw = guard_path(path).read_bytes()
        cohorts.append(
            {
                "source_path": str(path.resolve()),
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "pages": [
                    {"id": p["id"], "alternatives": [propose(p, c) for c in configs()]}
                    for p in json.loads(raw)["pages"]
                ],
            }
        )
    rss, method = process_peak_rss()
    payload = {
        "configs": configs(),
        "cohorts": cohorts,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": method,
    }
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    (output / "candidates.json").write_bytes(data)
    return {"sha256": hashlib.sha256(data).hexdigest(), "output": str(output)}


def score_frozen(directory: Path, target_paths: list[Path]) -> dict[str, Any]:
    """Evaluate previously frozen variants, excluding ambiguous reference labels."""
    from bench.borderless_challenge import score
    from bench.rolling_robustness import exact_source_ownership

    raw = (guard_path(directory) / "candidates.json").read_bytes()
    frozen = json.loads(raw)
    if frozen["configs"] != configs() or len(target_paths) != len(frozen["cohorts"]):
        raise ValueError("Frozen extent identity mismatch")
    rows = []
    for index, (cohort, target_path) in enumerate(zip(frozen["cohorts"], target_paths, strict=True)):
        source_raw = guard_path(Path(cohort["source_path"])).read_bytes()
        if hashlib.sha256(source_raw).hexdigest() != cohort["source_sha256"]:
            raise ValueError("Extent source changed after freeze")
        sources = {p["id"]: p for p in json.loads(source_raw)["pages"]}
        targets = {p["id"]: p for p in json.loads(guard_path(target_path).read_bytes())}
        if set(sources) != set(targets):
            raise ValueError("Extent reference IDs mismatch")
        for page in cohort["pages"]:
            target = targets[page["id"]]
            eligible = target.get("binary_admission_eligible", True) and target["kind"] != "ambiguous"
            for alternative in page["alternatives"]:
                tables = alternative["candidates"]
                scored = [score(target, [t]) for t in tables] if eligible else []
                best = max(
                    range(len(scored)),
                    key=lambda i: (scored[i]["exact_page"], scored[i]["exact_cells"], scored[i]["owned_values"]),
                    default=None,
                )
                scores = (scored[best] if best is not None else score(target, [])) if eligible else None
                ownership = (
                    exact_source_ownership(target, sources[page["id"]], tables[best])
                    if eligible and best is not None and target.get("authored_slots")
                    else None
                )
                rows.append(
                    {
                        "cohort": index,
                        "id": page["id"],
                        "config": alternative["config"],
                        "kind": target["kind"],
                        "eligible": eligible,
                        "candidate_count": len(tables),
                        "scores": scores,
                        "ownership": ownership,
                    }
                )
    summary: dict[str, Any] = {
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "aggregates": {},
        "resources": {k: frozen[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")},
    }
    for index in range(len(frozen["cohorts"])):
        for policy in configs():
            for kind in ("borderless", "prose", "ruled-control", "ambiguous"):
                group = [
                    r for r in rows if r["cohort"] == index and r["config"] == policy["name"] and r["kind"] == kind
                ]
                eligible_rows = [r for r in group if r["eligible"]]
                summary["aggregates"][f"{index}/{policy['name']}/{kind}"] = {
                    "pages": len(group),
                    "scored_pages": len(eligible_rows),
                    "proposed_pages": sum(r["candidate_count"] > 0 for r in group),
                    **{
                        k: sum(r["scores"][k] for r in eligible_rows)
                        for k in (
                            "exact_page",
                            "exact_cells",
                            "exact_spans",
                            "owned_values",
                            "owned_words",
                            "false_positive_page",
                        )
                    },
                    "failures": [
                        r["id"] for r in eligible_rows if target_positive(r) and not r["scores"]["exact_page"]
                    ],
                }
    (directory / "private-scores.json").write_text(json.dumps({"rows": rows}, indent=2))
    (directory / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def target_positive(row: dict[str, Any]) -> bool:
    """Identify scored structural slices, never use reference kind during generation."""
    return row["kind"] in ("borderless", "ruled-control")


def main() -> None:
    """Prepare source-only candidates or score the already frozen artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="*")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--targets", type=Path, nargs="+")
    args = parser.parse_args()
    result = score_frozen(args.output, args.targets) if args.targets else freeze(args.sources, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
