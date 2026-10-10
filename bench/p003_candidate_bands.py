"""Frozen compatible whole-row-band alternatives from two valid crop candidates.

Generated row index agreement is a hypothesis, not verified physical row
alignment. Whole original crop candidates remain independent controls.
"""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004
from __future__ import annotations

import itertools
from copy import deepcopy
from hashlib import sha256
from typing import Any

from bench import p003_candidate_choice as choice
from bench import pipeline_vision_transcription as adapter

THRESHOLDS = (1.0, 0.95, 0.8)
MAX_ALTERNATIVES = 256
MAX_EXHAUSTIVE_BANDS = 8


def _iou(a: list[float], b: list[float]) -> float:
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return intersection / (area_a + area_b - intersection)


def _spans(table: dict[str, Any]) -> list[tuple[int, int, int, int]]:
    return sorted((s["row"], s["column"], s["row_span"], s["column_span"]) for s in table["spans"])


def _compatible(a: dict[str, Any], b: dict[str, Any], threshold: float) -> bool:
    geometry = a["bbox"] == b["bbox"] if threshold == 1 else _iou(a["bbox"], b["bbox"]) >= threshold
    return (
        geometry
        and a["row_count"] == b["row_count"]
        and a["col_count"] == b["col_count"]
        and a["values"][0] == b["values"][0]
        and _spans(a) == _spans(b)
    )


def _bands(table: dict[str, Any]) -> list[list[int]]:
    cuts = set(range(1, table["row_count"]))
    for span in table["spans"]:
        cuts.difference_update(range(span["row"] + 1, span["row"] + span["row_span"]))
    edges = [0, *sorted(cuts), table["row_count"]]
    return [[a, b] for a, b in itertools.pairwise(edges)]


def _patterns(count: int) -> list[tuple[int, ...]]:
    # Full enumeration is predeclared only for <=8 differing indivisible bands.
    if count <= MAX_EXHAUSTIVE_BANDS:
        return list(itertools.product((0, 1), repeat=count))
    variants = {(0,) * count, (1,) * count, tuple(i % 2 for i in range(count)), tuple(1 - i % 2 for i in range(count))}
    for position in range(count):
        variants.add(tuple(int(i == position) for i in range(count)))
        variants.add(tuple(int(i != position) for i in range(count)))
    for cut in range(1, count):
        variants.add((0,) * cut + (1,) * (count - cut))
        variants.add((1,) * cut + (0,) * (count - cut))
    return sorted(variants)


def freeze(viewport: list[float], states: list[dict[str, Any]], *, threshold: float = 1.0) -> dict[str, Any]:
    """Predeclare all literal candidate bands and bounded patterns without scoring."""
    if len(states) != 2 or type(threshold) not in (int, float) or threshold not in THRESHOLDS:
        raise ValueError("Compatible band treatment requires exactly two states and a frozen threshold")
    bounds = choice._viewport(viewport)
    for state in states:
        choice._validate(bounds, state)
    a, b = (s["tables"] for s in states)
    candidates = {i: [j for j, table in enumerate(b) if _compatible(t, table, threshold)] for i, t in enumerate(a)}
    used = [indexes[0] for indexes in candidates.values() if len(indexes) == 1]
    ambiguous = any(len(indexes) > 1 for indexes in candidates.values()) or len(set(used)) != len(used)
    matches = [] if ambiguous else [[i, indexes[0]] for i, indexes in candidates.items() if len(indexes) == 1]
    bands = []
    for i, j in matches:
        for start, stop in _bands(a[i]):
            if a[i]["values"][start:stop] != b[j]["values"][start:stop]:
                bands.append(
                    {
                        "table_a": i,
                        "table_b": j,
                        "start_row": start,
                        "stop_row": stop,
                        "bbox_iou": _iou(a[i]["bbox"], b[j]["bbox"]),
                        "values_a": deepcopy(a[i]["values"][start:stop]),
                        "values_b": deepcopy(b[j]["values"][start:stop]),
                    }
                )
    patterns = _patterns(len(bands))
    capacity = len(patterns) > MAX_ALTERNATIVES
    plan = {
        "version": 1,
        "viewport": list(bounds),
        "states": deepcopy(states),
        "threshold": threshold,
        "matching": matches,
        "ambiguous_matching": ambiguous,
        "differing_bands": bands,
        "patterns": [] if capacity else [list(p) for p in patterns],
        "status": "capacity_retained_controls"
        if capacity
        else "ambiguous_retained_controls"
        if ambiguous
        else "compatible_band_choices"
        if bands
        else "no_compatible_differences",
        "policy": {
            "max_composite_patterns": MAX_ALTERNATIVES,
            "max_original_controls": 2,
            "max_exhaustive_bands": MAX_EXHAUSTIVE_BANDS,
            "large_menu": "whole patterns + every one-band exchange + every prefix split + parity patterns; no ranking",
            "header": "identical literal first row",
            "span_cuts": "never cut a vertical merged span",
            "geometry": "original baseline zero bbox for every composite table",
            "row_index_alignment_physically_verified": False,
            "source_conserved": False,
            "whole_original_controls_retained": True,
        },
    }
    plan["snapshot_sha256"] = sha256(choice.canonical_json(plan)).hexdigest()
    return plan


def alternatives(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return exact original controls plus complete literal row-band composites."""
    if freeze(plan["viewport"], plan["states"], threshold=plan["threshold"]) != plan:
        raise ValueError("Frozen compatible-band admission or pattern inventory changed")
    unique = {}
    for origin, state in enumerate(plan["states"]):
        encoded = choice.canonical_json(state)
        unique.setdefault(encoded, {"canonical_json": encoded.decode(), "provenance": []})["provenance"].append(
            {"whole_original": origin}
        )
    for pattern in plan["patterns"]:
        state = deepcopy(plan["states"][0])
        for selection, band in zip(pattern, plan["differing_bands"], strict=True):
            if selection:
                table = state["tables"][band["table_a"]]
                table["values"][band["start_row"] : band["stop_row"]] = deepcopy(band["values_b"])
        choice._validate(tuple(plan["viewport"]), state)
        encoded = choice.canonical_json(state)
        unique.setdefault(encoded, {"canonical_json": encoded.decode(), "provenance": []})["provenance"].append(
            {"band_choices": pattern}
        )
    return [{**v, "sha256": sha256(k).hexdigest()} for k, v in unique.items()]


def compose(states: list[dict[str, Any]], viewports: list[list[float]], page_viewport: list[float]) -> dict[str, Any]:
    """Validate whole literal crop states and assemble one atomic nonoverlapping page."""
    if len(states) != len(viewports):
        raise ValueError("Complete crop state inventory differs")
    page = choice._viewport(page_viewport)
    tables = []
    slots = 0
    for state, viewport in zip(states, viewports, strict=True):
        bounds = choice._viewport(viewport)
        if bounds[0] < page[0] or bounds[1] < page[1] or bounds[2] > page[2] or bounds[3] > page[3]:
            raise ValueError("Crop viewport exceeds page geometry")
        choice._validate(bounds, state)
        for table in state["tables"]:
            slots += table["row_count"] * table["col_count"]
            if slots > 4096:
                raise ValueError("Complete composed page exceeds source pipeline slot cap")
            box = table["bbox"]
            for prior in tables:
                other = prior["bbox"]
                if min(box[2], other[2]) > max(box[0], other[0]) and min(box[3], other[3]) > max(box[1], other[1]):
                    raise ValueError("Complete crop alternatives overlap on page")
            tables.append(deepcopy(table))
    return {"tables": tables, "text_provenance": adapter.PROVENANCE, "source_conserved": False}
