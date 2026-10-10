"""Source-only alternatives for tables interrupted by capacity work boundaries."""

# ruff: noqa: C901, PLR0911, EM101, TRY003, PLR2004
from __future__ import annotations

from copy import deepcopy
from statistics import median
from typing import Any

from bench.pipeline_assembly import _clean_table
from bench.pipeline_regions import _geometric_parts, compose, validate_composed


def _owned(table: dict[str, Any]) -> list[str]:
    return [i for c in table["cells"] for i in c["source_ids"]]


def _bounds(ids: list[str], lookup: dict[str, dict[str, Any]]) -> list[float] | None:
    if not ids:
        return None
    boxes = [lookup[i]["bbox"] for i in ids]
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def _profile(table: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    columns = table["col_count"]
    if columns < 2 or table["row_count"] < 2:
        return None
    samples: list[list[list[float]]] = [[] for _ in range(columns)]
    spans = {(s["row"], s["column"]): s for s in table["spans"]}
    rows = []
    signatures = []
    for row in range(table["row_count"]):
        ids = []
        occupied = set()
        for column in range(columns):
            cell = table["cells"][row * columns + column]
            ids.extend(cell["source_ids"])
            box = _bounds(cell["source_ids"], lookup)
            if box is not None:
                occupied.add(column)
                span = spans.get((row, column))
                if span and span["row_span"] == span["column_span"] == 1:
                    samples[column].append(box)
        box = _bounds(ids, lookup)
        if box is None:
            return None
        rows.append(box)
        signatures.append(occupied)
    if any(len(sample) < 2 for sample in samples):
        return None
    profiles = [(median(b[0] for b in sample), median(b[2] for b in sample)) for sample in samples]
    return {"columns": profiles, "rows": rows, "signatures": signatures}


def _compatible(a: dict[str, Any], b: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> bool:
    if a["col_count"] != b["col_count"]:
        return False
    pa, pb = _profile(a, lookup), _profile(b, lookup)
    if pa is None or pb is None:
        return False
    ids = _owned(a) + _owned(b)
    height = median(max(1, lookup[i]["bbox"][3] - lookup[i]["bbox"][1]) for i in ids)
    # Each column must independently retain a repeated left or right edge.
    if any(
        min(abs(x[0] - y[0]), abs(x[1] - y[1])) > 0.75 * height
        for x, y in zip(pa["columns"], pb["columns"], strict=True)
    ):
        return False
    if any(
        x[1] >= y[0] for profile in (pa, pb) for x, y in zip(profile["columns"], profile["columns"][1:], strict=False)
    ):
        return False
    # Internal logical rows must progress downward; do not join rotated tables.
    if any(
        following[1] <= previous[1]
        for p in (pa, pb)
        for previous, following in zip(p["rows"], p["rows"][1:], strict=False)
    ):
        return False
    gaps = [
        following[1] - previous[3]
        for p in (pa, pb)
        for previous, following in zip(p["rows"], p["rows"][1:], strict=False)
        if following[1] > previous[3]
    ]
    gap = pb["rows"][0][1] - pa["rows"][-1][3]
    if gap < -0.5 * height or gap > max(3 * height, 2 * median(gaps) if gaps else 0):
        return False
    signatures_a, signatures_b = pa["signatures"][-3:], pb["signatures"][:3]
    return any(len(x & y) >= 2 and len(x & y) / len(x | y) >= 0.6 for x in signatures_a for y in signatures_b)


def _same_header(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        a["values"][0] == b["values"][0]
        and any(v for v in a["values"][0])
        and all(span["row_span"] == 1 for table in (a, b) for span in table["spans"] if span["row"] == 0)
    )


def _joined(
    a: dict[str, Any], b: dict[str, Any], lookup: dict[str, dict[str, Any]], *, drop_header: bool
) -> tuple[dict[str, Any], list[str]]:
    columns = a["col_count"]
    skipped = 1 if drop_header else 0
    offset = a["row_count"] - skipped
    removed = [i for c in b["cells"][:columns] for i in c["source_ids"]] if skipped else []
    merged = {
        "row_count": a["row_count"] + b["row_count"] - skipped,
        "col_count": columns,
        "cells": deepcopy(a["cells"] + b["cells"][skipped * columns :]),
        "spans": deepcopy(a["spans"]) + [{**s, "row": s["row"] + offset} for s in b["spans"] if s["row"] >= skipped],
    }
    return _clean_table(merged, lookup), removed


def propose(
    plan: dict[str, Any], region_states: dict[str, dict[str, Any]], *, max_alternatives: int = 24
) -> list[dict[str, Any]]:
    """Propose single-boundary stitches beside an unchanged complete baseline.

    Inputs contain one already validated table assembly per region. Both regions
    must be consecutive complete-row capacity chunks of one source-derived block.
    Repeated-header removal moves its literal IDs to unresolved ownership; keep
    is always proposed separately. No edit is applied automatically.
    """
    if isinstance(max_alternatives, bool) or not isinstance(max_alternatives, int) or not 1 <= max_alternatives <= 24:
        raise ValueError("Invalid stitch alternative admission")
    baseline = compose(plan, region_states)
    baseline["id"] = "c0"
    outputs = [baseline]
    lookup = {w["id"]: w for w in plan["words"]}
    native_ids = {i for r in plan["regions"] if r["kind"] == "native" for i in r["source_ids"]}
    parts = _geometric_parts([w for w in plan["words"] if w["id"] not in native_ids])
    blocks = {w["id"]: index for index, (words, _) in enumerate(parts) for w in words}
    offsets = {}
    offset = 0
    for region in plan["regions"]:
        offsets[region["id"]] = offset
        offset += len(region_states[region["id"]]["tables"])
    for first, second in zip(plan["regions"], plan["regions"][1:], strict=False):
        if any(r["boundary"] != "capacity_rows" for r in (first, second)):
            continue
        if len({blocks[i] for r in (first, second) for i in r["source_ids"]}) != 1:
            continue
        for ai, a in enumerate(region_states[first["id"]]["tables"]):
            for bi, b in enumerate(region_states[second["id"]]["tables"]):
                if not _compatible(a, b, lookup) or (a["row_count"] + b["row_count"]) * a["col_count"] > 4096:
                    continue
                for drop in (False, True) if _same_header(a, b) else (False,):
                    if len(outputs) >= max_alternatives:
                        raise ValueError("Complete stitch alternative inventory exceeds admission")
                    joined, removed = _joined(a, b, lookup, drop_header=drop)
                    index_a, index_b = offsets[first["id"]] + ai, offsets[second["id"]] + bi
                    tables = [
                        joined if index == index_a else deepcopy(table)
                        for index, table in enumerate(baseline["tables"])
                        if index != index_b
                    ]
                    unresolved = set(baseline["unresolved_ids"] + removed)
                    state = {
                        "id": f"c{len(outputs)}",
                        "tables": tables,
                        "unresolved_ids": [w["id"] for w in plan["words"] if w["id"] in unresolved],
                        "mechanism": "capacity_stitch_drop_header" if drop else "capacity_stitch_keep_header",
                        "stitched_regions": [first["id"], second["id"]],
                        "repeated_header_unresolved_ids": removed,
                    }
                    validate_composed(plan, state)
                    outputs.append(state)
    return outputs
