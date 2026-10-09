"""Prospective source-only divider baseline for selected DEV description lines.

Selector box centers approximate line locations; interpreted paths do not prove
clip-resolved visibility. This experiment never infers semantics from text.
"""

# Geometry tuple arities are literal throughout this small bounded baseline.
# ruff: noqa: PLR2004
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

MAX_PATHS = 4096
MAX_COMMANDS = 16384
TOLERANCE = 0.25
POLICY = "divider-v1: split on full-width center-corridor stroke; join on enclosing closed rectangle; otherwise defer"


def _number(value: Any) -> float:  # noqa: ANN401 - validate external geometry.
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or abs(value) > 1_000_000_000
        or not math.isfinite(value)
    ):
        message = "Geometry must contain finite numbers"
        raise ValueError(message)
    return float(value)


def _point(value: Sequence[float]) -> tuple[float, float]:
    if len(value) != 2:
        message = "Point must have two coordinates"
        raise ValueError(message)
    return _number(value[0]), _number(value[1])


def _box(value: Sequence[float]) -> tuple[float, float, float, float]:
    if len(value) != 4:
        message = "Box must have four coordinates"
        raise ValueError(message)
    x0, y0, x1, y1 = map(_number, value)
    if x0 >= x1 or y0 >= y1:
        message = "Target boxes must have positive dimensions"
        raise ValueError(message)
    return x0, y0, x1, y1


def _rectangle(
    lines: list[tuple[tuple[float, float], tuple[float, float]]],
) -> tuple[float, float, float, float] | None:
    if len(lines) != 4:
        return None
    points = [point for line in lines for point in line]
    x0, y0 = min(p[0] for p in points), min(p[1] for p in points)
    x1, y1 = max(p[0] for p in points), max(p[1] for p in points)
    if x1 - x0 <= TOLERANCE or y1 - y0 <= TOLERANCE:
        return None
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    edges = set()
    for start, end in lines:
        matched = [
            [
                i
                for i, corner in enumerate(corners)
                if max(abs(point[0] - corner[0]), abs(point[1] - corner[1])) <= TOLERANCE
            ]
            for point in (start, end)
        ]
        if any(len(candidates) != 1 for candidates in matched):
            return None
        left, right = matched[0][0], matched[1][0]
        if (left - right) % 4 not in (1, 3):
            return None
        edges.add(tuple(sorted((left, right))))
    if len(edges) != 4:
        return None
    return x0, y0, x1, y1


def grouping(drawings: Sequence[Mapping[str, Any]], target_boxes: Sequence[Sequence[float]], *, task: str) -> str:  # noqa: C901, PLR0912 - explicit bounded source checks.
    """Return a grouping from strokes and loose target regions, or defer.

    Full-width means covering the union horizontal extent. Between lines means
    strictly between vertical box centers, not outside every selector pixel.
    Character-boundary requests abstain regardless of headers or target text.
    """
    if len(drawings) > MAX_PATHS or len(target_boxes) != 2:
        message = "Geometry input exceeds admission or has invalid target arity"
        raise ValueError(message)
    boxes = sorted((_box(box) for box in target_boxes), key=lambda box: box[1] + box[3])
    commands = sum(len(drawing.get("items", ())) for drawing in drawings)
    if commands > MAX_COMMANDS:
        message = "Geometry commands exceed admission"
        raise ValueError(message)
    segments = []
    rectangles = []
    for drawing in drawings:
        items = drawing.get("items", ())
        lines = []
        only_lines = True
        for item in items:
            if not item or item[0] != "l" or len(item) != 3:
                only_lines = False
                continue
            start, end = _point(item[1]), _point(item[2])
            lines.append((start, end))
        if drawing.get("type") not in ("s", "fs") or drawing.get("color") is None:
            continue
        if _number(drawing.get("width", 0)) < 0:
            message = "Stroke width cannot be negative"
            raise ValueError(message)
        segments.extend(lines)
        if only_lines and drawing.get("close_path") is True:
            rectangle = _rectangle(lines)
            if rectangle is not None:
                rectangles.append(rectangle)
    if task == "character_boundary":
        return "unresolved"
    if task != "line_ownership":
        message = "Unknown geometry task"
        raise ValueError(message)
    x0, x1 = min(box[0] for box in boxes), max(box[2] for box in boxes)
    centers = [(box[1] + box[3]) / 2 for box in boxes]
    if centers[1] - centers[0] <= TOLERANCE:
        return "unresolved"
    internal = False
    for start, end in segments:
        if abs(start[1] - end[1]) <= TOLERANCE:
            y = (start[1] + end[1]) / 2
            left, right = sorted((start[0], end[0]))
            if centers[0] + TOLERANCE < y < centers[1] - TOLERANCE:
                if left <= x0 + TOLERANCE and right >= x1 - TOLERANCE:
                    return "split"
                internal |= right > x0 and left < x1
        elif abs(start[0] - end[0]) <= TOLERANCE:
            x = (start[0] + end[0]) / 2
            low, high = sorted((start[1], end[1]))
            internal |= x0 + TOLERANCE < x < x1 - TOLERANCE and low < centers[1] and high > centers[0]
    if internal:
        return "unresolved"
    y0, y1 = min(box[1] for box in boxes), max(box[3] for box in boxes)
    if any(left <= x0 and top <= y0 and right >= x1 and bottom >= y1 for left, top, right, bottom in rectangles):
        return "join"
    return "unresolved"
