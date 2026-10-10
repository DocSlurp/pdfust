"""Bounded source-segment topology alternatives, without generated text or labels."""

# Experimental evidence uses explicit heterogeneous JSON records.
# ruff: noqa: EM101, TRY003, PLR2004, C901
from __future__ import annotations

import math
from bisect import bisect_right
from itertools import pairwise
from statistics import median
from typing import Any

from bench.pipeline_assembly import _clean_table
from bench.pipeline_repair import _sources, validate
from bench.silver import canonical, sha

POLICY: dict[str, Any] = {
    "version": 1,
    "max_source_words": 4096,
    "max_source_bytes": 2 * 1024 * 1024,
    "max_physical_lines": 256,
    "max_raw_segment_gaps": 2048,
    "line_center_drift_smaller_height": 0.35,
    "line_vertical_overlap_smaller_height": 0.5,
    "segment_gap_median_word_heights": 1.5,
    "column_support_physical_lines": 2,
    "column_edge_separation_median_word_heights": 0.5,
    "row_join_max_gap_word_heights": 1.5,
    "row_join_min_horizontal_overlap_smaller_width": 0.5,
    "max_column_boundaries": 4,
    "max_row_boundaries": 4,
    "max_disputed_boundaries": 8,
    "max_states_per_crop": 256,
    "max_table_slots": 4096,
    "word_assignment": "whole bbox inside one active column; source-order literal IDs; crossing/outside unresolved",
    "topology_language": "global column split toggles and adjacent physical-row joins; rectangular atomic cells",
}


def _box(words: list[dict[str, Any]]) -> list[float]:
    return [
        min(w["bbox"][0] for w in words),
        min(w["bbox"][1] for w in words),
        max(w["bbox"][2] for w in words),
        max(w["bbox"][3] for w in words),
    ]


def _inside(box: list[float], bounds: list[float]) -> bool:
    return bounds[0] <= box[0] < box[2] <= bounds[2] and bounds[1] <= box[1] < box[3] <= bounds[3]


def _lines(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {w["id"]: i for i, w in enumerate(words)}
    groups: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda w: ((w["bbox"][1] + w["bbox"][3]) / 2, order[w["id"]])):
        b = word["bbox"]
        height, cy = b[3] - b[1], (b[1] + b[3]) / 2
        matches = [
            j
            for j, group in enumerate(groups)
            if all(
                abs(cy - (o["bbox"][1] + o["bbox"][3]) / 2) <= 0.35 * min(height, o["bbox"][3] - o["bbox"][1])
                and min(b[3], o["bbox"][3]) - max(b[1], o["bbox"][1]) >= 0.5 * min(height, o["bbox"][3] - o["bbox"][1])
                for o in group
            )
        ]
        if len(matches) == 1:
            groups[matches[0]].append(word)
        else:
            groups.append([word])
    result = []
    for index, group in enumerate(groups):
        group.sort(key=lambda w: order[w["id"]])
        height = median(w["bbox"][3] - w["bbox"][1] for w in group)
        parts: list[list[dict[str, Any]]] = []
        for word in sorted(group, key=lambda w: (w["bbox"][0], order[w["id"]])):
            if parts and word["bbox"][0] - max(o["bbox"][2] for o in parts[-1]) <= 1.5 * height:
                parts[-1].append(word)
            else:
                parts.append([word])
        result.append(
            {
                "id": f"l{index}",
                "bbox": _box(group),
                "median_word_height": height,
                "source_ids": [w["id"] for w in group],
                "segments": [
                    {
                        "id": f"l{index}s{k}",
                        "bbox": _box(part),
                        "source_ids": [w["id"] for w in sorted(part, key=lambda w: order[w["id"]])],
                    }
                    for k, part in enumerate(parts)
                ],
            }
        )
    return result


def freeze(source: dict[str, Any], source_ids: list[str], bounds: list[float]) -> dict[str, Any]:
    """Freeze complete physical groups and at most eight source-only structural boundaries."""
    lookup = _sources(source)
    if len(canonical(source)) > POLICY["max_source_bytes"]:
        raise ValueError("Complete source byte admission exceeded")
    if (
        len(source_ids) != len(set(source_ids))
        or set(source_ids) - set(lookup)
        or len(bounds) != 4
        or any(not math.isfinite(v) for v in bounds)
        or bounds[0] >= bounds[2]
        or bounds[1] >= bounds[3]
    ):
        raise ValueError("Invalid complete crop ownership or geometry")
    owned = set(source_ids)
    words = [w for w in source["words"] if w["id"] in owned]
    eligible = [w for w in words if _inside(w["bbox"], bounds)]
    excluded = [
        {"source_id": w["id"], "reason": "outside_or_nonpositive_crop_geometry"}
        for w in words
        if not _inside(w["bbox"], bounds)
    ]
    lines = _lines(eligible)
    gaps = [
        {"line_id": line["id"], "interval": [a["bbox"][2], b["bbox"][0]], "segments": [a["id"], b["id"]]}
        for line in lines
        for a, b in pairwise(line["segments"])
    ]
    plan: dict[str, Any] = {
        "version": 1,
        "policy": POLICY,
        "source_sha256": sha(canonical(source)),
        "bbox": bounds,
        "source_ids": [w["id"] for w in words],
        "owned_word_count": len(words),
        "other_page_words_omitted_count": len(source["words"]) - len(words),
        "owned_words_omitted_count": 0,
        "literal_words": [[w["id"], w["text"], *w["bbox"]] for w in words],
        "words_excluded_from_assignment": excluded,
        "lines": lines,
        "column_proposals": [],
        "row_proposals": [],
        "proposal_refusals": [],
        "context": "Complete crop-owned source only; no pixels, generated text or other-page literal context.",
        "raw_segment_gap_count": len(gaps),
        "references_read": False,
    }
    if not eligible or len(lines) > 256 or len(gaps) > 2048:
        plan.update(status="no_candidate_refusal", refusal="empty_or_physical_inventory_admission")
        return plan
    height = median(w["bbox"][3] - w["bbox"][1] for w in eligible)
    probes = []
    for gap in gaps:
        x = sum(gap["interval"]) / 2
        support = sorted({g["line_id"] for g in gaps if g["interval"][0] < x < g["interval"][1]})
        if len(support) >= 2:
            probes.append({"x": x, "support_line_ids": support, "gap_width": gap["interval"][1] - gap["interval"][0]})
    probes.sort(key=lambda p: (-len(p["support_line_ids"]), -p["gap_width"], p["x"]))
    for probe in probes:
        reason = None
        if any(abs(probe["x"] - p["x"]) < 0.5 * height for p in plan["column_proposals"]):
            reason = "near_existing_column_boundary"
        elif len(plan["column_proposals"]) == 4:
            reason = "column_boundary_cap"
        if reason:
            plan["proposal_refusals"].append({"kind": "column_split", "reason": reason, **probe})
        else:
            plan["column_proposals"].append({"id": f"c{len(plan['column_proposals'])}", **probe})
    joins = []
    for j, (a, b) in enumerate(pairwise(lines)):
        gap = b["bbox"][1] - a["bbox"][3]
        smaller_height = min(a["median_word_height"], b["median_word_height"])
        overlap = max(0.0, min(a["bbox"][2], b["bbox"][2]) - max(a["bbox"][0], b["bbox"][0]))
        smaller_width = min(a["bbox"][2] - a["bbox"][0], b["bbox"][2] - b["bbox"][0])
        if 0 <= gap <= 1.5 * smaller_height and overlap >= 0.5 * smaller_width:
            joins.append(
                {"after_line_index": j, "line_ids": [a["id"], b["id"]], "normalized_vertical_gap": gap / smaller_height}
            )
    joins.sort(key=lambda p: (p["normalized_vertical_gap"], p["after_line_index"]))
    plan["row_proposals"] = [{"id": f"r{j}", **p} for j, p in enumerate(joins[:4])]
    plan["proposal_refusals"].extend({"kind": "row_join", "reason": "row_boundary_cap", **p} for p in joins[4:])
    plan.update(
        status="prepared",
        boundary_count=len(plan["column_proposals"]) + len(plan["row_proposals"]),
        proposal_space="All binary combinations; no scores or semantic labels.",
    )
    return plan


def decode(source: dict[str, Any], plan: dict[str, Any], active: list[str]) -> dict[str, Any]:
    """Decode whole-source conserved rectangular states without positive-edge union guessing."""
    lookup = _sources(source)
    if sha(canonical(source)) != plan["source_sha256"]:
        raise ValueError("Frozen source changed")
    menu = {p["id"] for p in plan["column_proposals"] + plan["row_proposals"]}
    if len(active) != len(set(active)) or set(active) - menu:
        raise ValueError("Unknown or repeated topology boundary")
    if plan["status"] != "prepared":
        state = {"id": "c0", "tables": [], "unresolved_ids": [w["id"] for w in source["words"]]}
        validate(source, state)
        return state
    xs = [plan["bbox"][0], *sorted(p["x"] for p in plan["column_proposals"] if p["id"] in active), plan["bbox"][2]]
    joins = {p["after_line_index"] for p in plan["row_proposals"] if p["id"] in active}
    line_row: dict[str, int] = {}
    row = 0
    for j, line in enumerate(plan["lines"]):
        if j and j - 1 not in joins:
            row += 1
        line_row[line["id"]] = row
    rows, cols = row + 1, len(xs) - 1
    if rows * cols > 4096:
        raise ValueError("Rectangular slot admission exceeded")
    table = {
        "bbox": plan["bbox"],
        "row_count": rows,
        "col_count": cols,
        "cells": [{"source_ids": [], "role": "unknown"} for _ in range(rows * cols)],
        "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(rows) for c in range(cols)],
    }
    word_rows = {i: line_row[line["id"]] for line in plan["lines"] for i in line["source_ids"]}
    for word in source["words"]:
        if word["id"] not in word_rows:
            continue
        b = word["bbox"]
        c = min(cols - 1, bisect_right(xs, (b[0] + b[2]) / 2) - 1)
        if xs[c] <= b[0] < b[2] <= xs[c + 1]:
            table["cells"][word_rows[word["id"]] * cols + c]["source_ids"].append(word["id"])
    table = {**_clean_table(table, lookup), "bbox": table["bbox"]}
    assigned = {i for cell in table["cells"] for i in cell["source_ids"]}
    state = {
        "id": "c0",
        "tables": [table],
        "unresolved_ids": [w["id"] for w in source["words"] if w["id"] not in assigned],
    }
    validate(source, state)
    return state


def candidates(source: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Enumerate the exact bounded edit language and deduplicate identical legal states."""
    menu = [p["id"] for p in plan["column_proposals"] + plan["row_proposals"]]
    if len(menu) > 8:
        raise ValueError("Disputed boundary admission exceeded")
    control = [p["id"] for p in plan["column_proposals"]]
    masks = [sum(1 << menu.index(i) for i in control), *range(1 << len(menu))]
    result: list[dict[str, Any]] = []
    hashes: set[str] = set()
    for mask in masks:
        active = [i for j, i in enumerate(menu) if mask & (1 << j)]
        state = decode(source, plan, active)
        digest = sha(canonical(state))
        if digest in hashes:
            continue
        hashes.add(digest)
        result.append(
            {
                "id": f"s{len(result)}",
                "active_boundary_ids": active,
                "state": state,
                "state_sha256": digest,
                "geometry_control": not result,
                "topology": [{"rows": t["row_count"], "columns": t["col_count"]} for t in state["tables"]],
            }
        )
    return result


def compose(source: dict[str, Any], selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Compose crop states, refusing all conflicting tables rather than choosing an overlap winner."""
    for state in selected:
        validate(source, state)
    tables = [t for state in selected for t in state["tables"]]
    conflicts: set[int] = set()
    ownership = [{i for cell in t["cells"] for i in cell["source_ids"]} for t in tables]
    for j, a in enumerate(tables):
        for k in range(j):
            b = tables[k]
            overlap = min(a["bbox"][2], b["bbox"][2]) > max(a["bbox"][0], b["bbox"][0]) and min(
                a["bbox"][3], b["bbox"][3]
            ) > max(a["bbox"][1], b["bbox"][1])
            if overlap or ownership[j] & ownership[k]:
                conflicts.update((j, k))
    retained = [t for j, t in enumerate(tables) if j not in conflicts]
    assigned = {i for t in retained for cell in t["cells"] for i in cell["source_ids"]}
    state = {
        "id": "c0",
        "tables": retained,
        "unresolved_ids": [w["id"] for w in source["words"] if w["id"] not in assigned],
        "conflicting_table_indices": sorted(conflicts),
    }
    validate(source, state)
    return state
