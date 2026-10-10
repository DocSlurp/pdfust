"""Optional complete-page column alternatives from source-only consensus geometry.

Hypothesis declared in pipeline-gap-analysis.md before implementation: retain seed
columns through sparse rows and place content by whitespace separators instead of
strict lower-bound seed starts. Geometry proposals remain unaccepted candidates.
"""

# Benchmark dictionaries retain heterogeneous source/assembly records.
# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import bisect
import json
from itertools import pairwise
from statistics import median
from typing import Any

from bench.decision_evidence_designs import fragments
from bench.pipeline_assembly import MAX_ALTERNATIVES, MAX_TABLE_SLOTS, _regions, _source, native_state, validate
from bench.rolling_rows import numeric

MAX_SEEDS = 3
MAX_COLUMNS = 8
MIN_PHYSICAL_ROWS = 3
WRAP_GAP_EM = 1.8
STOP_GAP_EM = 3.0
STOP_GAP_MULTIPLE = 2.5


def _table(  # noqa: C901, PLR0912
    region: dict[str, Any], seed_band: int, seed: list[dict[str, Any]], *, mode: str, rolling: bool
) -> dict[str, Any] | None:
    words = region["words"]
    lookup = {w["id"]: w for w in words}
    height = median(max(1, w["bbox"][3] - w["bbox"][1]) for w in words)
    seed = sorted(seed, key=lambda p: (p["bbox"][0], p["id"]))
    if any(b["bbox"][0] <= a["bbox"][2] for a, b in pairwise(seed)):
        return None
    centers = [(p["bbox"][0] + p["bbox"][2]) / 2 for p in seed]
    separators = [(a["bbox"][2] + b["bbox"][0]) / 2 for a, b in pairwise(seed)]
    left = seed[0]["bbox"][0] - max(height, (centers[1] - centers[0]) / 2)
    right = seed[-1]["bbox"][2] + max(height, (centers[-1] - centers[-2]) / 2)
    bands: dict[int, list[dict[str, Any]]] = {}
    for part in fragments(words):
        bands.setdefault(part["band"], []).append(part)
    bounds = [
        (band, min(p["bbox"][1] for p in ps), max(p["bbox"][3] for p in ps))
        for band, ps in bands.items()
        if band >= seed_band
    ]
    gaps = [b[1] - a[2] for a, b in pairwise(bounds) if b[1] > a[2]]
    typical = median(gaps) if gaps else height
    active = []
    previous_bottom = None
    for band, top, bottom in bounds:
        if previous_bottom is not None and top - previous_bottom > max(
            STOP_GAP_EM * height, STOP_GAP_MULTIPLE * typical
        ):
            break
        parts = bands[band]
        if band > seed_band and len(parts) == 1 and parts[0]["bbox"][2] - parts[0]["bbox"][0] > (right - left) * 0.9:
            break
        active.append((band, top, bottom, parts))
        previous_bottom = bottom
    if len(active) < MIN_PHYSICAL_ROWS:
        return None
    # Every sampled fragment has one column vote; sparse columns retain their seed.
    samples: list[list[list[float]]] = [[] for _ in seed]
    for _, _, _, parts in active:
        for part in parts:
            x = (part["bbox"][0] + part["bbox"][2]) / 2
            if left <= x <= right:
                samples[bisect.bisect_right(separators, x)].append(part["bbox"])
    consensus_left = [
        median(b[0] for b in group) if group else p["bbox"][0] for group, p in zip(samples, seed, strict=True)
    ]
    consensus_right = [
        median(b[2] for b in group) if group else p["bbox"][2] for group, p in zip(samples, seed, strict=True)
    ]
    if mode == "edges":
        proposed = [(consensus_right[c] + consensus_left[c + 1]) / 2 for c in range(len(seed) - 1)]
    else:
        consensus_centers = [(a + b) / 2 for a, b in zip(consensus_left, consensus_right, strict=True)]
        proposed = [(a + b) / 2 for a, b in pairwise(consensus_centers)]
    # Preserve source seed order and keep each separator strictly between seed centers.
    separators = [x if centers[c] < x < centers[c + 1] else separators[c] for c, x in enumerate(proposed)]
    physical = []
    numeric_columns: set[int] = set()
    for band, top, bottom, parts in active:
        cells: list[list[str]] = [[] for _ in seed]
        for part in sorted(parts, key=lambda p: (p["bbox"][0], p["id"])):
            for ident in part["source_ids"]:
                word = lookup[ident]
                x = (word["bbox"][0] + word["bbox"][2]) / 2
                if left <= x <= right:
                    column = bisect.bisect_right(separators, x)
                    cells[column].append(ident)
                    if numeric(word["text"]):
                        numeric_columns.add(column)
        if any(cells):
            physical.append((band, top, bottom, cells))
    if (
        len(physical) < MIN_PHYSICAL_ROWS
        or sum(sum(bool(ids) for ids in cells) >= 2 for _, _, _, cells in physical) < 2
    ):
        return None
    rows: list[list[list[str]]] = []
    previous_bottom = None
    for _, top, bottom, cells in physical:
        occupied = {c for c, ids in enumerate(cells) if ids}
        close = previous_bottom is not None and 0 <= top - previous_bottom <= WRAP_GAP_EM * height
        join = (
            rolling
            and bool(rows)
            and close
            and len(occupied) < len(seed)
            and 0 not in occupied
            and not occupied & numeric_columns
        )
        if not join:
            rows.append([[] for _ in seed])
        for column, ids in enumerate(cells):
            rows[-1][column].extend(ids)
        previous_bottom = bottom
    if len(rows) * len(seed) > MAX_TABLE_SLOTS:
        return None
    return {
        "row_count": len(rows),
        "col_count": len(seed),
        "values": [[" ".join(lookup[i]["text"] for i in ids) for ids in row] for row in rows],
        "cells": [{"source_ids": ids, "role": "unknown"} for row in rows for ids in row],
        "spans": [
            {"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(len(rows)) for c in range(len(seed))
        ],
    }


def propose(page: dict[str, Any], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:  # noqa: C901
    """Append complete consensus alternatives, preserving the existing cN prefix."""
    source = _source(page)
    for index, candidate in enumerate(existing):
        validate(source, candidate)
        if candidate["id"] != f"c{index}":
            raise ValueError("Existing candidate IDs must be consecutive")
    native = native_state(page)
    native_ids = {i for t in native["tables"] for cell in t["cells"] for i in cell["source_ids"]}
    residual = {"page_size": source["page_size"], "words": [w for w in source["words"] if w["id"] not in native_ids]}
    output = list(existing)

    def identity(candidate: dict[str, Any]) -> str:
        return json.dumps([candidate["tables"], candidate["unresolved_ids"]], sort_keys=True)

    identities = {identity(c) for c in existing}
    regions = _regions(residual)
    for mode in ("edges", "centers"):
        for rolling in (False, True):
            tables = list(native["tables"])
            added = False
            for region in regions:
                by_band: dict[int, list[dict[str, Any]]] = {}
                for part in fragments(region["words"]):
                    by_band.setdefault(part["band"], []).append(part)
                seeds = [(band, ps) for band, ps in by_band.items() if 2 <= len(ps) <= MAX_COLUMNS][:MAX_SEEDS]
                hypotheses = [_table(region, band, ps, mode=mode, rolling=rolling) for band, ps in seeds]
                admitted = [t for t in hypotheses if t is not None]
                if admitted:
                    tables.append(max(admitted, key=lambda t: sum(len(c["source_ids"]) for c in t["cells"])))
                    added = True
            if not added:
                continue
            owned = {i for t in tables for cell in t["cells"] for i in cell["source_ids"]}
            row_policy = "rolling" if rolling else "physical"
            candidate = {
                "id": f"c{len(output)}",
                "tables": tables,
                "unresolved_ids": [w["id"] for w in source["words"] if w["id"] not in owned],
                "mechanism": f"column_consensus_{row_policy}",
                "description": (
                    f"Seed columns retained through sparse rows; consensus {mode} separators and {row_policy} rows."
                ),
            }
            validate(source, candidate)
            key = identity(candidate)
            if key not in identities:
                if len(output) >= MAX_ALTERNATIVES:
                    raise ValueError("Combined complete alternatives exceed admission; no truncation")
                identities.add(key)
                output.append(candidate)
    return output
