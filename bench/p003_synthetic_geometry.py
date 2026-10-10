"""Label-free geometric relationship qualifiers; no synthetic generator imports."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from PIL import Image

# ruff: noqa: PLR2004, TRY003, EM101, C901 - bounded geometric protocol thresholds and refusals.

LIMIT = 256
POLICY = {
    "axis_tolerance_points": 1.0,
    "raster_dark_threshold": 96,
    "raster_min_run_pixels": 12,
    "raster_min_run_fraction": 0.10,
    "raster_min_aspect": 12.0,
    "maximum_segments": LIMIT,
    "maximum_rectangles": 4096,
    "positive_wrap": "abstain: enclosure and spacing do not prove logical continuation",
    "physical_row_proxy": "separate bbox treatment only; not proof of logical row membership",
}


def box(value: Any) -> list[float]:  # noqa: ANN401
    """Reject nonfinite or inverted source boxes rather than changing coordinates."""
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("Four finite coordinates required")
    result = [float(v) for v in value]
    if any(not math.isfinite(v) for v in result) or result[2] <= result[0] or result[3] <= result[1]:
        raise ValueError("Positive finite source box required")
    return result


def vector_segments(drawings: list[dict]) -> list[list[float]]:
    """Retain axis-aligned source strokes; filled/decorative shapes do not become rules."""
    lines = []
    for drawing in drawings:
        if drawing.get("type") not in {"s", "fs"}:
            continue
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue
            x0, y0 = map(float, item[1])
            x1, y1 = map(float, item[2])
            if not all(math.isfinite(v) for v in (x0, y0, x1, y1)):
                raise ValueError("Nonfinite drawing")
            if abs(y1 - y0) <= 0.1 and abs(x1 - x0) > 1:
                lines.append([min(x0, x1), (y0 + y1) / 2, max(x0, x1), (y0 + y1) / 2])
            elif abs(x1 - x0) <= 0.1 and abs(y1 - y0) > 1:
                lines.append([(x0 + x1) / 2, min(y0, y1), (x0 + x1) / 2, max(y0, y1)])
    if len(lines) > LIMIT:
        raise ValueError("Complete rule evidence exceeds segment cap")
    return sorted(lines)


def raster_segments(image: Image.Image, viewport: list[float]) -> list[list[float]]:
    """Extract long dark thin runs independently of vector rules and source strings."""
    viewport = box(viewport)
    dark = np.asarray(image.convert("L")) <= POLICY["raster_dark_threshold"]
    lines = []
    for vertical in (False, True):
        data = dark.T if vertical else dark
        minimum = max(POLICY["raster_min_run_pixels"], math.ceil(data.shape[1] * 0.10))
        runs = []
        for index, row in enumerate(data):
            changes = np.diff(np.r_[False, row, False].astype(np.int8))
            for start, end in zip(np.where(changes == 1)[0], np.where(changes == -1)[0], strict=True):
                if end - start >= minimum:
                    runs.append([index, index + 1, int(start), int(end)])
        grouped = []
        for run in runs:
            match = next((g for g in reversed(grouped) if g[1] == run[0]
                          and abs(g[2] - run[2]) <= 1 and abs(g[3] - run[3]) <= 1), None)
            if match is None:
                grouped.append(run)
            else:
                match[1] = run[1]
                match[2] = min(match[2], run[2])
                match[3] = max(match[3], run[3])
        for first, last, start, end in grouped:
            if (end - start) / (last - first) < POLICY["raster_min_aspect"]:
                continue
            center = (first + last) / 2
            pixels = [center, start, center, end] if vertical else [start, center, end, center]
            lines.append([viewport[axis % 2] + value / image.size[axis % 2]
                          * (viewport[axis % 2 + 2] - viewport[axis % 2])
                          for axis, value in enumerate(pixels)])
    if len(lines) > LIMIT:
        raise ValueError("Complete raster rule evidence exceeds segment cap")
    return sorted(lines)


def _cover(lines: list[list[float]], axis: int, position: float, lo: float, hi: float) -> bool:
    tolerance = POLICY["axis_tolerance_points"]
    intervals = sorted((line[1 - axis], line[3 - axis]) for line in lines
                       if abs(line[axis] - line[axis + 2]) < 0.01 and abs(line[axis] - position) <= tolerance)
    reached = lo
    for start, end in intervals:
        if start > reached + tolerance:
            break
        reached = max(end, reached)
    return reached >= hi - tolerance


def enclosure(word: list[float], lines: list[list[float]]) -> list[float] | None:
    """Find a complete minimal rectangle with no complete interior rule divider."""
    xs = sorted({line[0] for line in lines if line[0] == line[2]})
    ys = sorted({line[1] for line in lines if line[1] == line[3]})
    candidates = []
    examined = 0
    for left in (x for x in xs if x <= word[0]):
        for right in (x for x in xs if x >= word[2]):
            for top in (y for y in ys if y <= word[1]):
                for bottom in (y for y in ys if y >= word[3]):
                    examined += 1
                    if examined > POLICY["maximum_rectangles"]:
                        raise ValueError("Enclosure search cap exceeded; no partial proposal")
                    if not (_cover(lines, 0, left, top, bottom) and _cover(lines, 0, right, top, bottom)
                            and _cover(lines, 1, top, left, right) and _cover(lines, 1, bottom, left, right)):
                        continue
                    if any(_cover(lines, 0, x, top, bottom) for x in xs if left + 1 < x < right - 1):
                        continue
                    if any(_cover(lines, 1, y, left, right) for y in ys if top + 1 < y < bottom - 1):
                        continue
                    candidates.append([left, top, right, bottom])
    if not candidates:
        return None
    candidates.sort(key=lambda r: ((r[2] - r[0]) * (r[3] - r[1]), r))
    smallest = candidates[0]
    if any(abs((r[2] - r[0]) * (r[3] - r[1]) - (smallest[2] - smallest[0])
               * (smallest[3] - smallest[1])) <= 1 and r != smallest for r in candidates[1:]):
        return None
    return smallest


def classify(record: dict, lines: list[list[float]], *, physical_proxy: bool = False) -> dict:
    """Emit geometry choices without using case IDs, literal text, families, or labels."""
    words = record["source"]["words"]
    by_id = {word["id"]: box(word["bbox"]) for word in words}
    if len(by_id) != len(words) or len(record["pair_source_ids"]) != 2:
        raise ValueError("Unique exact source pair required")
    first, second = [by_id[i] for i in record["pair_source_ids"]]
    kind = record["kind"]
    if kind not in {"cell", "row", "wrap"}:
        raise ValueError("Unknown relation kind")
    a, b = enclosure(first, lines), enclosure(second, lines)
    vertical_overlap = max(0, min(first[3], second[3]) - max(first[1], second[1]))
    overlap_ratio = vertical_overlap / min(first[3] - first[1], second[3] - second[1])
    horizontal_separator = any(
        line[1] == line[3]
        and min(first[3], second[3]) < line[1] < max(first[1], second[1])
        and line[0] <= min(first[0], second[0]) and line[2] >= max(first[2], second[2])
        for line in lines
    )
    vertical_separator = any(
        line[0] == line[2]
        and min(first[2], second[2]) < line[0] < max(first[0], second[0])
        and line[1] <= min(first[1], second[1]) and line[3] >= max(first[3], second[3])
        for line in lines
    )
    choice, reason = "unresolved", "Geometry does not establish requested logical relationship"
    if (horizontal_separator or vertical_separator) and kind in {"cell", "wrap"}:
        choice, reason = "separate", "Complete axis separator spans both source boxes"
    elif horizontal_separator and kind == "row":
        choice, reason = "separate", "Complete horizontal separator spans both source boxes"
    elif kind == "cell" and a is not None and b is not None:
        choice = "same_cell" if a == b else "different_cell"
        reason = "Complete minimal rule enclosures"
    elif kind == "row" and a is not None and b is not None:
        if abs(a[1] - b[1]) <= 1 and abs(a[3] - b[3]) <= 1:
            choice, reason = "same_row", "Complete cells share upper and lower row boundaries"
        elif min(a[3], b[3]) <= max(a[1], b[1]) + 1:
            choice, reason = "different_row", "Complete cells occupy disjoint row bands"
    elif kind == "row" and physical_proxy:
        if overlap_ratio >= 0.8:
            choice, reason = "same_row", "Physical-row proxy only; not logical membership proof"
        elif overlap_ratio == 0:
            choice, reason = "different_row", "Different physical baselines; wrapped logical rows remain ambiguous"
    elif kind == "wrap" and a is not None and b is not None and a != b:
        choice, reason = "not_wrap", "Distinct complete rule enclosures prohibit same-cell continuation"
    claim = choice
    choice = "same" if choice in {"same_cell", "same_row"} else (
        "separate" if choice in {"separate", "different_cell", "different_row", "not_wrap"} else "unresolved"
    )
    return {"choice": choice, "geometric_claim": claim, "abstained": choice == "unresolved", "reason": reason,
            "kind": kind, "pair_source_ids": record["pair_source_ids"], "pair_boxes": [first, second],
            "enclosures": [a, b], "vertical_overlap_ratio": overlap_ratio,
            "horizontal_separator": horizontal_separator, "vertical_separator": vertical_separator,
            "physical_proxy": physical_proxy, "rule_segments": lines,
            "probability": None, "correctness_measured": False}
