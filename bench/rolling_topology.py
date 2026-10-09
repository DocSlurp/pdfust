"""T001–T003 source-only seed-band column corridors and short-table hypotheses."""

# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import time
from collections import Counter
from copy import deepcopy
from itertools import pairwise
from pathlib import Path
from statistics import median
from typing import Any, TypedDict

from bench.decision_evidence_designs import fragments
from bench.rolling_rows import numeric, project
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss


class Config(TypedDict):
    """Declared source-only topology proposal policy."""

    name: str
    merge: str
    seed_limit: int
    maximum_columns: int
    stop_gap_multiple: float
    wrap_gap_heights: float


_CONFIGS: tuple[Config, ...] = (
    {
        "name": "T001-seed-physical",
        "merge": "none",
        "seed_limit": 3,
        "maximum_columns": 8,
        "stop_gap_multiple": 2.5,
        "wrap_gap_heights": 1.8,
    },
    {
        "name": "T002-seed-sparse",
        "merge": "sparse",
        "seed_limit": 3,
        "maximum_columns": 8,
        "stop_gap_multiple": 2.5,
        "wrap_gap_heights": 1.8,
    },
    {
        "name": "T003-seed-numeric-boundary",
        "merge": "numeric",
        "seed_limit": 3,
        "maximum_columns": 8,
        "stop_gap_multiple": 2.5,
        "wrap_gap_heights": 1.8,
    },
)


def configs() -> list[Config]:
    """Return immutable-in-intent policies for freezing before private scoring."""
    return deepcopy(list(_CONFIGS))


def _identity(table: dict[str, Any]) -> str:
    return json.dumps({k: table[k] for k in ("row_count", "col_count", "values", "spans", "cells")}, sort_keys=True)


def _native_candidate(page: dict[str, Any], words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retain source vector topology and map source centers without private references."""
    result: list[dict[str, Any]] = []
    for index, table in enumerate(page.get("vector_candidates", [])):
        cells: list[dict[str, Any]] = [{"source_ids": [], "role": "unknown"} for _ in table["cells"]]
        for word in words:
            x, y = ((word["bbox"][i] + word["bbox"][i + 2]) / 2 for i in (0, 1))
            hits = [
                i
                for i, box in enumerate(table["cells"])
                if box is not None and box[0] <= x <= box[2] and box[1] <= y <= box[3]
            ]
            if len(hits) == 1:
                cells[hits[0]]["source_ids"].append(word["id"])
        owned = [i for cell in cells for i in cell["source_ids"]]
        result.append(
            {
                "name": f"native-vector-{index}",
                "row_count": table["row_count"],
                "col_count": table["col_count"],
                "values": deepcopy(table["values"]),
                "spans": deepcopy(table["spans"]),
                "cells": cells,
                "unresolved_ids": [w["id"] for w in words if w["id"] not in set(owned)],
                "status": "source-native grid prior; no new merged-cell inference",
            }
        )
    return result


def propose(page: dict[str, Any], config: Config) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Propose complete source-owned tables from seed corridors, never admitting a table automatically."""
    if config not in _CONFIGS:
        raise ValueError("Topology configuration must match a frozen declared policy")
    words = project(page)["words"]
    lookup = {w["id"]: w for w in words}
    parts = fragments(words)
    by_band: dict[int, list[dict[str, Any]]] = {}
    for part in parts:
        by_band.setdefault(part["band"], []).append(part)
    seeds = [(band, items) for band, items in by_band.items() if 2 <= len(items) <= config["maximum_columns"]][
        : config["seed_limit"]
    ]
    candidates = _native_candidate(page, words)
    for seed_band, seed_parts in seeds:
        anchors = sorted(p["bbox"][0] for p in seed_parts)
        if len(set(anchors)) != len(anchors):
            continue
        height = median(max(1, p["bbox"][3] - p["bbox"][1]) for p in seed_parts)
        full_tops = [
            min(p["bbox"][1] for p in items) for band, items in by_band.items() if band >= seed_band and len(items) >= 2
        ]
        differences = [b - a for a, b in pairwise(full_tops) if b > a]
        typical_gap = median(differences) if differences else height * 4
        numeric_columns: set[int] = set()
        admitted: list[tuple[int, list[list[str]], float, float]] = []
        previous_bottom = None
        for band, items in by_band.items():
            if band < seed_band:
                continue
            top = min(p["bbox"][1] for p in items)
            bottom = max(p["bbox"][3] for p in items)
            if previous_bottom is not None and top - previous_bottom > max(
                height * 3, typical_gap * config["stop_gap_multiple"]
            ):
                break
            if (
                len(items) == 1
                and band > seed_band
                and items[0]["bbox"][2] - items[0]["bbox"][0] > (anchors[-1] - anchors[0]) * 0.9
            ):
                break
            cells: list[list[str]] = [[] for _ in anchors]
            for part in items:
                for source_id in part["source_ids"]:
                    word = lookup[source_id]
                    x = word["bbox"][0]
                    if x < anchors[0] - height * 0.5:
                        continue
                    column = max(0, bisect.bisect_right(anchors, x + 0.05) - 1)
                    cells[column].append(source_id)
                    if numeric(word["text"]):
                        numeric_columns.add(column)
            if any(cells):
                admitted.append((band, cells, top, bottom))
                previous_bottom = bottom
        if len(admitted) < 2:
            continue
        rows: list[list[list[str]]] = []
        physical_bands: list[list[int]] = []
        previous_bottom = None
        for band, cells, top, bottom in admitted:
            occupied = {c for c, ids in enumerate(cells) if ids}
            close = previous_bottom is not None and 0 <= top - previous_bottom <= height * config["wrap_gap_heights"]
            numeric_here = any(any(numeric(lookup[i]["text"]) for i in ids) for ids in cells)
            sparse = len(occupied) < len(anchors)
            join = bool(rows) and close and sparse and config["merge"] != "none"
            if config["merge"] == "sparse":
                join = join and not bool(occupied & numeric_columns)
            elif config["merge"] == "numeric":
                join = join and not numeric_here
            if not join:
                rows.append([[] for _ in anchors])
                physical_bands.append([])
            physical_bands[-1].append(band)
            for column, ids in enumerate(cells):
                rows[-1][column].extend(ids)
            previous_bottom = bottom
        cell_list = [{"source_ids": ids, "role": "unknown"} for row in rows for ids in row]
        owned = [i for cell in cell_list for i in cell["source_ids"]]
        table = {
            "name": f"{config['name']}-seed-{seed_band}",
            "row_count": len(rows),
            "col_count": len(anchors),
            "values": [[" ".join(lookup[i]["text"] for i in ids) for ids in row] for row in rows],
            "spans": [
                {"row": r, "column": c, "row_span": 1, "column_span": 1}
                for r in range(len(rows))
                for c in range(len(anchors))
            ],
            "cells": cell_list,
            "unresolved_ids": [w["id"] for w in words if w["id"] not in set(owned)],
            "column_corridor_starts": anchors,
            "physical_bands": physical_bands,
            "header_role": "unknown; seed band is a geometry hypothesis, not an assumed header",
            "status": "unaccepted complete candidate; no source words invented",
        }
        if not any(_identity(table) == _identity(old) for old in candidates):
            candidates.append(table)
    for candidate in candidates:
        owned = [i for cell in candidate["cells"] for i in cell["source_ids"]]
        if Counter(owned + candidate["unresolved_ids"]) != Counter(w["id"] for w in words):
            raise ValueError("Topology candidate violates exact source conservation")
    return {
        "config": config["name"],
        "candidates": candidates,
        "source_word_ids": [w["id"] for w in words],
        "candidate_only": True,
    }


def freeze(sources: list[Path], output: Path) -> dict[str, Any]:
    """Freeze every declared config and complete cohort candidate bytes before private scoring."""
    output = guard_path(output)
    if output.exists():
        raise ValueError("Topology output already exists; preserve the original freeze")
    output.mkdir(parents=True)
    policies = configs()
    (output / "configs.json").write_text(json.dumps(policies, sort_keys=True, indent=2))
    start, cpu = time.perf_counter(), time.process_time()
    cohorts = []
    for source_path in sources:
        raw = guard_path(source_path).read_bytes()
        pages = json.loads(raw)["pages"]
        cohorts.append(
            {
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "source_path": str(source_path.resolve()),
                "pages": [{"id": p["id"], "alternatives": [propose(p, config) for config in policies]} for p in pages],
            }
        )
    rss, measurement = process_peak_rss()
    payload = {
        "schema": 1,
        "configs": policies,
        "cohorts": cohorts,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"perf_counter/process_time; {measurement}; process lifetime; sequential CPU; no sampling",
    }
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    (output / "candidates.json").write_bytes(data)
    return {
        "output": str(output),
        "sha256": hashlib.sha256(data).hexdigest(),
        "cohort_pages": [len(c["pages"]) for c in cohorts],
    }


def main() -> None:
    """Prepare candidates without targets, credentials or inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.sources, args.output), indent=2))


if __name__ == "__main__":
    main()
