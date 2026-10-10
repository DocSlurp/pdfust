"""Deterministic source-owned placement into a frozen uniform-grid hypothesis.

Overlap and distance scores are geometry heuristics, never model probabilities.
No image analysis or literal transcription is performed.
"""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004
from __future__ import annotations

import json
import math
from copy import deepcopy
from typing import Any

from bench import p003_spatial_bands as bands
from bench import p003_topology_chunks as chunks
from bench import p003_topology_ownership as ownership

MIN_OVERLAP = 0.8
MIN_MARGIN = 0.15
DISTANCE_WEIGHT = 0.05


def _intersection(a: list[float], b: list[float]) -> float:
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def place(plan: ownership.Plan, *, band_mode: str = "uniform") -> dict[str, Any]:
    """Rank every anchor and atomically retain one literal-word owner or abstain."""
    if band_mode not in {"uniform", "source"}:
        raise ValueError("Unknown geometric band mode")
    packet = chunks.packet(plan) if json.loads(plan.packet_json).get("version") == 2 else ownership._packet(plan)
    source, tables = packet["source"], deepcopy(packet["topology"]["canonical"])
    anchors = []
    band_receipts = []
    for t, table in enumerate(tables):
        merged = {(s["row"], s["column"]): s for s in table["spans"]}
        table["spans"] = [
            deepcopy(merged.get((r, c), {"row": r, "column": c, "row_span": 1, "column_span": 1}))
            for r, values in enumerate(table["values"])
            for c, value in enumerate(values)
            if value is not None
        ]
        table["cells"] = [{"source_ids": [], "role": "unknown"} for _ in table["cells"]]
        x0, y0, x1, y1 = table["bbox"]
        width, height = (x1 - x0) / table["col_count"], (y1 - y0) / table["row_count"]
        edges = (
            bands.derive(source["words"], table)
            if band_mode == "source"
            else {
                "x_edges": [x0 + i * width for i in range(table["col_count"] + 1)],
                "y_edges": [y0 + i * height for i in range(table["row_count"] + 1)],
            }
        )
        if band_mode == "source":
            band_receipts.append(edges)
        for span in table["spans"]:
            r, c = span["row"], span["column"]
            box = [
                edges["x_edges"][c],
                edges["y_edges"][r],
                edges["x_edges"][c + span["column_span"]],
                edges["y_edges"][r + span["row_span"]],
            ]
            anchors.append((f"t{t}r{r}c{c}", t, r * table["col_count"] + c, box))
    unresolved, outside, assignments = [], [], []
    for word in source["words"]:
        box = word["bbox"]
        area = (box[2] - box[0]) * (box[3] - box[1])
        ranked = []
        for alias, t, slot, bounds in anchors:
            overlap = _intersection(box, bounds) / area
            distance = math.hypot(
                ((box[0] + box[2]) - (bounds[0] + bounds[2])) / (2 * (bounds[2] - bounds[0])),
                ((box[1] + box[3]) - (bounds[1] + bounds[3])) / (2 * (bounds[3] - bounds[1])),
            )
            score = overlap - DISTANCE_WEIGHT * distance
            ranked.append((score, alias, t, slot, overlap))
        ranked.sort(key=lambda a: (-a[0], a[1]))
        best = ranked[0] if ranked else None
        margin = best[0] - ranked[1][0] if len(ranked) > 1 else (1.0 if best else 0.0)
        intersects = any(_intersection(box, table["bbox"]) > 0 for table in tables)
        contained = any(
            box[0] >= t["bbox"][0] and box[1] >= t["bbox"][1] and box[2] <= t["bbox"][2] and box[3] <= t["bbox"][3]
            for t in tables
        )
        choice = "outside" if not intersects else "unresolved"
        if best and contained and best[4] >= MIN_OVERLAP and margin >= MIN_MARGIN:
            choice = best[1]
            tables[best[2]]["cells"][best[3]]["source_ids"].append(word["id"])
        elif choice == "outside":
            outside.append(word["id"])
        else:
            unresolved.append(word["id"])
        assignments.append(
            {
                "source_id": word["id"],
                "choice": choice,
                "best_score": best[0] if best else None,
                "best_overlap_fraction": best[4] if best else None,
                "margin": margin,
                "anchor_scores": [
                    {"anchor": a, "score": score, "overlap_fraction": overlap} for score, a, _, _, overlap in ranked
                ],
            }
        )
    lookup = {w["id"]: w for w in source["words"]}
    tables = [{**ownership._clean_table(t, lookup), "bbox": t["bbox"]} for t in tables]
    remaining = set(outside + unresolved)
    state = {
        "id": "c0",
        "tables": tables,
        "unresolved_ids": [w["id"] for w in source["words"] if w["id"] in remaining],
        "mechanism": "p003_topology_uniform_geometry",
    }
    ownership.validate(source, state)
    return {
        "state": state,
        "snapshot_sha256": plan.sha256,
        "source_conserved": True,
        "text_provenance": "literal-source-words",
        "outside_ids": outside,
        "abstained_ids": unresolved,
        "assignments": assignments,
        "geometry_policy": {
            "grid": "uniform subdivision of frozen topology bbox"
            if band_mode == "uniform"
            else "source inferred row bands and column gutters",
            **({"band_mode": "source", "bands": band_receipts} if band_mode == "source" else {}),
            "min_overlap": MIN_OVERLAP,
            "min_margin": MIN_MARGIN,
            "distance_weight": DISTANCE_WEIGHT,
            "scores_are_probabilities": False,
            "quality_verified": False,
        },
        "missing_source_text_recoverable": False,
    }
