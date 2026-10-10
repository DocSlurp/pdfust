"""Source-only row bands and persistent whitespace gutters for frozen topology.

These are geometric hypotheses, not calibrated probabilities. The expected row
and column counts come from the declared topology; no text labels or references
are read. Insufficient support explicitly falls back to uniform divisions.
"""

# Geometry records use the existing heterogeneous source snapshot contract.
# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import math
import statistics
from itertools import pairwise
from typing import Any

BIN_COUNT = 512
MAX_WORDS = 4096
MAX_LINES = 512
MIN_CLEAR_FRACTION = 0.65


def _uniform(start: float, stop: float, count: int) -> list[float]:
    return [start + (stop - start) * i / count for i in range(count + 1)]


def _lines(words: list[dict[str, Any]], height: float) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    ordered = sorted(words, key=lambda w: ((w["bbox"][1] + w["bbox"][3]) / 2, w["bbox"][0], w["id"]))
    for word in ordered:
        box = word["bbox"]
        center = (box[1] + box[3]) / 2
        if not lines or center - lines[-1]["center"] > 0.45 * height:
            lines.append({"center": center, "words": [], "top": box[1], "bottom": box[3]})
        line = lines[-1]
        line["words"].append(word)
        line["center"] += (center - line["center"]) / len(line["words"])
        line["top"], line["bottom"] = min(line["top"], box[1]), max(line["bottom"], box[3])
    if len(lines) > MAX_LINES:
        raise ValueError("Spatial physical-line inventory exceeds admission")
    return lines


def _rows(lines: list[dict[str, Any]], bounds: list[float], count: int) -> dict[str, Any]:
    if len(lines) < count:
        return {"edges": _uniform(bounds[1], bounds[3], count), "method": "uniform_insufficient_physical_lines"}
    gaps = [
        {"after": i, "clearance": lines[i + 1]["top"] - line["bottom"],
         "leading": lines[i + 1]["center"] - line["center"]}
        for i, line in enumerate(lines[:-1])
    ]
    cuts = sorted(sorted(gaps, key=lambda g: (-g["clearance"], -g["leading"], g["after"]))[:count - 1],
                  key=lambda g: g["after"])
    positions = [0, *(g["after"] + 1 for g in cuts), len(lines)]
    edges = [bounds[1], *[
        max(bounds[1], min(bounds[3], (lines[g["after"]]["bottom"] + lines[g["after"] + 1]["top"]) / 2))
        for g in cuts
    ], bounds[3]]
    if any(a >= b for a, b in pairwise(edges)):
        return {"edges": _uniform(bounds[1], bounds[3], count), "method": "uniform_degenerate_row_edges"}
    return {"edges": edges, "method": "largest_physical_line_clearances", "selected_gaps": cuts,
            "physical_lines_per_row": [b - a for a, b in pairwise(positions)]}


def _columns(  # noqa: C901, PLR0912 - bounded projection and explicit fallback.
    lines: list[dict[str, Any]], bounds: list[float], count: int, height: float,
) -> dict[str, Any]:
    if count == 1:
        return {"edges": [bounds[0], bounds[2]], "method": "single_column"}
    width = bounds[2] - bounds[0]
    occupied = [0] * BIN_COUNT
    for line in lines:
        mask = [False] * BIN_COUNT
        for word in line["words"]:
            box = word["bbox"]
            start = max(0, min(BIN_COUNT, math.floor((box[0] - bounds[0]) / width * BIN_COUNT)))
            stop = max(0, min(BIN_COUNT, math.ceil((box[2] - bounds[0]) / width * BIN_COUNT)))
            for i in range(start, stop):
                mask[i] = True
        for i, used in enumerate(mask):
            occupied[i] += used
    clear = [1 - value / max(1, len(lines)) for value in occupied]
    candidates = []
    cursor = 0
    while cursor < BIN_COUNT:
        if clear[cursor] < MIN_CLEAR_FRACTION:
            cursor += 1
            continue
        start = cursor
        while cursor < BIN_COUNT and clear[cursor] >= MIN_CLEAR_FRACTION:
            cursor += 1
        stop = cursor
        # Exterior margins are not separators, even when very wide.
        if start == 0 or stop == BIN_COUNT:
            continue
        gap_width = (stop - start) / BIN_COUNT * width
        if gap_width < 0.25 * height:
            continue
        x = bounds[0] + (start + stop) / (2 * BIN_COUNT) * width
        bilateral = sum(
            any(w["bbox"][2] <= x for w in line["words"])
            and any(w["bbox"][0] >= x for w in line["words"])
            for line in lines
        ) / max(1, len(lines))
        if bilateral < 0.25:
            continue
        support = statistics.mean(clear[start:stop])
        candidates.append({"x": x, "width": gap_width, "clear_fraction": support,
                           "bilateral_line_fraction": bilateral,
                           "score": support * bilateral * min(3, gap_width / height)})
    ranked = sorted(candidates, key=lambda c: (-c["score"], c["x"]))
    selected: list[dict[str, float]] = []
    minimum_width = width / (8 * count)
    for candidate in ranked:
        if all(abs(candidate["x"] - prior["x"]) >= minimum_width for prior in selected):
            selected.append(candidate)
        if len(selected) == count - 1:
            break
    if len(selected) != count - 1:
        return {"edges": _uniform(bounds[0], bounds[2], count), "method": "uniform_insufficient_gutters",
                "candidate_gutters": candidates}
    return {"edges": [bounds[0], *sorted(c["x"] for c in selected), bounds[2]],
            "method": "persistent_source_whitespace", "selected_gutters": selected,
            "candidate_gutters": candidates, "projection_bins": BIN_COUNT}


def derive(words: list[dict[str, Any]], table: dict[str, Any]) -> dict[str, Any]:
    """Infer variable-width bands from literal word boxes and declared dimensions."""
    bounds = table["bbox"]
    if (len(bounds) != 4 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                                or not math.isfinite(v) for v in bounds)
            or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]):
        raise ValueError("Spatial table bounds must be finite with positive extent")
    rows, columns = table["row_count"], table["col_count"]
    if type(rows) is not int or type(columns) is not int or not 1 <= rows <= 128 or not 1 <= columns <= 32:
        raise ValueError("Spatial topology dimensions exceed admission")
    if len(words) > MAX_WORDS:
        raise ValueError("Spatial word inventory exceeds admission")
    retained = []
    for word in words:
        box = word["bbox"]
        if (len(box) != 4 or any(not isinstance(v, (int, float)) or isinstance(v, bool)
                                or not math.isfinite(v) for v in box)
                or box[0] >= box[2] or box[1] >= box[3]):
            raise ValueError("Spatial source boxes must have finite positive extent")
        if bounds[0] <= (box[0] + box[2]) / 2 <= bounds[2] and bounds[1] <= (box[1] + box[3]) / 2 <= bounds[3]:
            retained.append(word)
    height = statistics.median(w["bbox"][3] - w["bbox"][1] for w in retained) if retained else 1.0
    lines = _lines(retained, height)
    row_bands, column_bands = _rows(lines, bounds, rows), _columns(lines, bounds, columns, height)
    return {"x_edges": column_bands.pop("edges"), "y_edges": row_bands.pop("edges"),
            "rows": row_bands, "columns": column_bands, "source_words_used": len(retained),
            "physical_line_count": len(lines), "scores_are_probabilities": False,
            "reference_labels_used": False}
