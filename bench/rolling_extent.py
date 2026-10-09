"""T005 separately frozen source-only local-gap extent alternatives."""

# ruff: noqa: EM101, TRY003, PLR2004
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


def main() -> None:
    """Source-only preparation; no hosted execution or reference arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.sources, args.output)))


if __name__ == "__main__":
    main()
