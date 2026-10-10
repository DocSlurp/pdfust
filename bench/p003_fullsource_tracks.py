"""Source-only global gutter controls without detector crop ownership or binary search caps."""

# ruff: noqa: EM101, TRY003, PLR2004, SLF001
from __future__ import annotations

import math
from collections import defaultdict
from statistics import median
from typing import Any

from bench import p003_segment_topology as segments
from bench.pipeline_repair import _sources, validate
from bench.silver import canonical, sha

GAPS = (0.5, 1.0, 1.5)
SUPPORTS = (0.1, 0.25, 0.5)
MAX_LINES = 256
MAX_COLUMNS = 32


def physical(source: dict[str, Any]) -> dict[str, Any]:
    """Retain every source word; disclose geometry excluded from row grouping."""
    _sources(source)
    if len(canonical(source)) > 2 * 1024 * 1024:
        raise ValueError("Complete source admission exceeded")
    bounds = source["page_size"]
    if len(bounds) != 4 or any(not math.isfinite(v) for v in bounds):
        raise ValueError("Expected finite display viewport")
    eligible = [w for w in source["words"] if segments._inside(w["bbox"], bounds)]
    return {
        "source_sha256": sha(canonical(source)), "bbox": bounds,
        "lines": segments._lines(eligible),
        "eligible_ids": [w["id"] for w in eligible],
        "excluded_ids": [w["id"] for w in source["words"] if not segments._inside(w["bbox"], bounds)],
        "source_word_count": len(source["words"]),
        "references_read": False,
    }


def gutter_intervals(gaps: list[tuple[float, float, str]], minimum: int) -> list[dict[str, Any]]:
    """Sweep positive gap intervals, counting distinct supporting physical lines."""
    events: dict[float, list[tuple[str, int]]] = defaultdict(list)
    for left, right, line in gaps:
        if left < right:
            events[left].append((line, 1))
            events[right].append((line, -1))
    active: dict[str, int] = {}
    intervals = []
    previous = None
    for x in sorted(events):
        if previous is not None and x > previous and len(active) >= minimum:
            intervals.append({"left": previous, "right": x, "support": sorted(active)})
        for line, change in events[x]:
            active[line] = active.get(line, 0) + change
            if active[line] == 0:
                del active[line]
        previous = x
    return intervals


def prepare(source: dict[str, Any], frozen: dict[str, Any], gap_em: float, support_fraction: float) -> dict[str, Any]:
    """Freeze one global-track hypothesis using all eligible page words, without model answers."""
    if gap_em not in GAPS or support_fraction not in SUPPORTS or frozen["source_sha256"] != sha(canonical(source)):
        raise ValueError("Unadmitted profile or changed complete source")
    lookup = _sources(source)
    lines = frozen["lines"]
    plan = {
        **frozen, "gap_em": gap_em, "support_fraction": support_fraction,
        "column_proposals": [], "row_proposals": [], "status": "no_candidate_refusal",
        "policy": "All-page global gaps, physical rows, no inferred wraps or semantic table admission",
        "max_columns": MAX_COLUMNS, "max_lines": MAX_LINES, "source_conserved": True,
    }
    if not lines or len(lines) > MAX_LINES:
        return {**plan, "refusal": "empty_or_physical_row_admission"}
    heights = [line["median_word_height"] for line in lines]
    height = median(heights)
    gaps = []
    for line in lines:
        words = sorted((lookup[i] for i in line["source_ids"]), key=lambda w: (w["bbox"][0], w["id"]))
        right = words[0]["bbox"][2]
        for word in words[1:]:
            left = word["bbox"][0]
            if left - right > gap_em * line["median_word_height"]:
                gaps.append((right, left, line["id"]))
            right = max(right, word["bbox"][2])
    minimum = max(2, math.ceil(len(lines) * support_fraction))
    intervals = gutter_intervals(gaps, minimum)
    ranked = sorted(intervals, key=lambda v: (-len(v["support"]), -(v["right"] - v["left"]), v["left"]))
    chosen = []
    excluded = []
    for interval in ranked:
        x = (interval["left"] + interval["right"]) / 2
        # Adjacent sweep slabs from one continuous gap are alternatives, not extra columns.
        if any(
            abs(x - item["x"]) < 0.5 * height
            or max(interval["left"], item["left"]) <= min(interval["right"], item["right"])
            for item in chosen
        ):
            excluded.append(interval)
        else:
            chosen.append({**interval, "x": x, "id": f"c{len(chosen)}"})
    plan.update(raw_gap_count=len(gaps), supported_intervals=intervals, excluded_alternative_intervals=excluded,
                minimum_support_lines=minimum, column_proposals=chosen)
    if not chosen:
        return {**plan, "refusal": "no_supported_column_separator"}
    if len(chosen) + 1 > MAX_COLUMNS or len(lines) * (len(chosen) + 1) > 4096:
        return {**plan, "refusal": "complete_grid_admission_no_truncation"}
    return {**plan, "status": "prepared"}


def decode(source: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Reuse strict whole-word ownership; crossing words remain explicitly unresolved."""
    state = segments.decode(source, plan, [item["id"] for item in plan["column_proposals"]])
    validate(source, state)
    return state
