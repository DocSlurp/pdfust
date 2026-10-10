"""Source-only table-local continuation hypotheses over frozen TATR columns."""
# ruff: noqa: EM101, TRY003, PLR2004, SLF001, C901, PLR0912, PLR0913, PLR0917 - explicit bounded geometry protocol.
from __future__ import annotations

import json
import math
from bisect import bisect_right
from itertools import pairwise
from statistics import median
from typing import Any

from bench import p003_segment_topology as physical
from bench.pipeline_assembly import _clean_table
from bench.pipeline_repair import MAX_PACKET_BYTES, MAX_SLOTS, _sources, validate

RATIOS = (0.75, 1.0, 1.25)
KEY_COLUMNS = (1, 2)
PROFILES = tuple((ratio, key) for ratio in RATIOS for key in KEY_COLUMNS)
POLICY = {"ratios": RATIOS, "key_columns": KEY_COLUMNS, "tatr_threshold": 0.5,
          "maximum_physical_lines": 1024, "maximum_columns": 32,
          "leading": "median positive adjacent physical-line center gaps, floored at median word height",
          "continuation": "empty key columns, occupied columns subset of preceding anchored row, bounded center gap",
          "barrier": "source horizontal stroke across >=80% region width between physical line centers",
          "contradictions": "refuse join; retain independent physical row without claiming logical correctness",
          "literal_policy": "whole source IDs, fixed column crossings/outside unresolved, no generated strings",
          "merged_cells_inferred": False}


def horizontal_rules(drawings: list[dict]) -> list[list[float]]:
    """Preserve source horizontal strokes only, without inventing missing dividers."""
    rules = []
    for drawing in drawings:
        if drawing.get("type") not in {"s", "fs"}:
            continue
        for item in drawing.get("items", []):
            if item[0] == "l":
                a, b = item[1:]
                if abs(a[1] - b[1]) <= 0.1 and abs(a[0] - b[0]) > 1:
                    rules.append([min(a[0], b[0]), (a[1] + b[1]) / 2, max(a[0], b[0])])
    return rules


def region(  # noqa: PLR0911 - explicit complete-evidence refusal branches.
           source: dict[str, Any], proposal: dict[str, Any], topology: dict[str, Any],
           rules: list[list[float]], ratio: float, key_count: int) -> dict[str, Any]:
    """Freeze every adjacent-row decision and decode complete source-owned cells."""
    lookup = _sources(source)
    ids = proposal["source_ids"]
    if len(ids) != len(set(ids)) or set(ids) - set(lookup):
        raise ValueError("Unique known regional source IDs required")
    owned = set(ids)
    bounds = proposal["bbox"]
    if (len(bounds) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in bounds)
            or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]):
        raise ValueError("Finite positive regional bounds required")
    words = [w for w in source["words"] if w["id"] in owned and physical._inside(w["bbox"], bounds)]
    lines = physical._lines(words)
    receipt = {"region_id": proposal["region_id"], "physical_lines": lines, "decisions": [],
               "owned_source_ids": ids, "status": "refused", "table": None}
    xs = topology.get("x_edges", [])
    if topology.get("status") != "geometry_candidate" or not 3 <= len(xs) <= 33:
        return {**receipt, "refusal": "missing_or_unadmitted_frozen_columns"}
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in xs):
        return {**receipt, "refusal": "nonfinite_or_invalid_frozen_column_endpoint"}
    if any(not bounds[0] < x < bounds[2] for x in xs[1:-1]) or any(a >= b for a, b in pairwise(xs)):
        return {**receipt, "refusal": "column_tracks_outside_region_or_nonmonotone"}
    # Region geometry declares the outer bounds; only internal TATR tracks are preserved.
    xs = [bounds[0], *xs[1:-1], bounds[2]]
    if not lines or len(lines) > POLICY["maximum_physical_lines"]:
        return {**receipt, "refusal": "empty_or_physical_line_admission"}
    centers = [(line["bbox"][1] + line["bbox"][3]) / 2 for line in lines]
    height = median(line["median_word_height"] for line in lines)
    leading = max(height, median([b - a for a, b in pairwise(centers) if b > a]) if len(lines) > 1 else height)
    columns = len(xs) - 1
    keys = set(range(min(key_count, columns)))
    mapped = []
    for line in lines:
        slots: dict[int, list[str]] = {}
        for ident in line["source_ids"]:
            word = lookup[ident]
            b = word["bbox"]
            col = min(columns - 1, max(0, bisect_right(xs, (b[0] + b[2]) / 2) - 1))
            if xs[col] <= b[0] < b[2] <= xs[col + 1]:
                slots.setdefault(col, []).append(ident)
        mapped.append(slots)
    if not any(mapped):
        return {**receipt, "refusal": "no_whole_word_assignments_to_frozen_columns"}
    groups: list[dict[int, list[str]]] = []
    for index, slots in enumerate(mapped):
        occupied = set(slots)
        previous = set(groups[-1]) if groups else set()
        gap = centers[index] - centers[index - 1] if index else None
        barrier = index > 0 and any(centers[index - 1] < y < centers[index]
                                   and right - left >= 0.8 * (bounds[2] - bounds[0])
                                   and left <= bounds[0] + 0.1 * (bounds[2] - bounds[0])
                                   and right >= bounds[2] - 0.1 * (bounds[2] - bounds[0])
                                   for left, y, right in rules)
        empty_key = not bool(occupied & keys)
        anchored = bool(previous & keys)
        compatible = bool(occupied) and occupied <= previous
        join = bool(index and not barrier and empty_key and anchored and compatible and gap <= ratio * leading)
        if join:
            for col, values in slots.items():
                groups[-1].setdefault(col, []).extend(values)
        else:
            groups.append({col: list(values) for col, values in slots.items()})
        receipt["decisions"].append({"physical_line_id": lines[index]["id"], "join_previous": join,
                                     "logical_row": len(groups) - 1, "center_gap": gap,
                                     "normalized_gap": gap / leading if gap is not None else None,
                                     "horizontal_rule_barrier": barrier, "key_empty": empty_key,
                                     "previous_row_key_present": anchored, "columns_compatible": compatible,
                                     "occupied_columns": sorted(occupied), "previous_row_columns": sorted(previous)})
    if len(groups) * columns > MAX_SLOTS:
        return {**receipt, "refusal": "complete_rectangular_grid_admission"}
    table = {"bbox": bounds, "row_count": len(groups), "col_count": columns,
             "cells": [{"source_ids": group.get(col, []), "role": "unknown"}
                       for group in groups for col in range(columns)],
             "spans": [{"row": row, "column": col, "row_span": 1, "column_span": 1}
                       for row in range(len(groups)) for col in range(columns)]}
    # Preserve source order within each cell; do not invent semantic/lexical ordering.
    order = {w["id"]: i for i, w in enumerate(source["words"])}
    for cell in table["cells"]:
        cell["source_ids"].sort(key=order.__getitem__)
    table = {**_clean_table(table, lookup), "bbox": bounds}
    used = {i for cell in table["cells"] for i in cell["source_ids"]}
    return {**receipt, "status": "decoded", "table": table, "leading": leading, "word_height": height,
            "column_edges": xs, "unresolved_owned_ids": [i for i in ids if i not in used],
            "joined_line_count": sum(d["join_previous"] for d in receipt["decisions"])}


def compose(source: dict[str, Any], proposals: list[dict[str, Any]], topologies: dict[str, dict[str, Any]],
            rules: list[list[float]], ratio: float, key_count: int) -> dict[str, Any]:
    """Refuse all overlapping participants and conserve each page source exactly once."""
    if (ratio, key_count) not in PROFILES:
        raise ValueError("Profile was not predeclared")
    _sources(source)
    if len(json.dumps(source).encode()) > MAX_PACKET_BYTES:
        raise ValueError("Complete source admission; no truncation")
    owned = [i for p in proposals for i in p["source_ids"]]
    if len(owned) != len(set(owned)):
        raise ValueError("Duplicate source ownership between regions")
    conflicts = {a["region_id"] for a in proposals for b in proposals if a is not b
                 and min(a["bbox"][2], b["bbox"][2]) > max(a["bbox"][0], b["bbox"][0])
                 and min(a["bbox"][3], b["bbox"][3]) > max(a["bbox"][1], b["bbox"][1])}
    receipts = []
    for proposal in proposals:
        r = region(source, proposal, topologies.get(proposal["region_id"], {}), rules, ratio, key_count)
        if proposal["region_id"] in conflicts:
            r.update(status="refused", refusal="overlapping_regions_all_participants", table=None)
        receipts.append(r)
    tables = [r["table"] for r in receipts if r["table"] is not None]
    page_refusal = None
    if sum(t["row_count"] * t["col_count"] for t in tables) > MAX_SLOTS:
        tables = []
        page_refusal = "whole_page_slots_all_tables_refused"
    for receipt in receipts:
        receipt["effective_page_accepted"] = receipt["table"] is not None and page_refusal is None
    used = {i for table in tables for cell in table["cells"] for i in cell["source_ids"]}
    state = {"id": "c0", "tables": tables, "unresolved_ids": [w["id"] for w in source["words"] if w["id"] not in used]}
    validate(source, state)
    return {"state": state, "regions": receipts, "page_refusal": page_refusal,
            "conflicting_region_ids": sorted(conflicts), "source_conserved": True, "references_read": False,
            "source_word_count": len(source["words"]), "assigned_word_count": len(used),
            "unresolved_word_count": len(state["unresolved_ids"])}
