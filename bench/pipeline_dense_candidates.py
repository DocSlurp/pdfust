"""Bounded raster-rule geometry proposals; table semantics remain undecided."""

# ruff: noqa: ANN401, EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

import math
from collections import defaultdict
from copy import deepcopy
from statistics import median
from typing import Any

from bench.pipeline_assembly import native_state, validate

MAX_PIXELS = 4_194_304
MAX_RULES = 512
MAX_SLOTS = 4096


def _lines(
    mask: Any, axis: int, minimum: int, *, max_gap: int = 0, thickness_ratio: float = 0.008
) -> list[tuple[float, float, float]]:
    """Find long contiguous dark runs and collapse thin adjacent stroke bands."""
    import numpy as np

    rows = mask if axis == 0 else mask.T
    groups: list[list[tuple[int, int, int]]] = []
    for position, row in enumerate(rows):
        edges = np.flatnonzero(np.diff(np.concatenate(([False], row, [False]))))
        runs: list[tuple[int, int]] = []
        for start, stop in zip(edges[::2], edges[1::2], strict=True):
            if runs and start - runs[-1][1] <= max_gap:
                runs[-1] = (runs[-1][0], int(stop))
            else:
                runs.append((int(start), int(stop)))
        for start, stop in runs:
            if stop - start < minimum:
                continue
            hit = next(
                (
                    g
                    for g in reversed(groups)
                    if position - g[-1][0] <= 1
                    and min(stop, g[-1][2]) - max(start, g[-1][1]) >= 0.8 * min(stop - start, g[-1][2] - g[-1][1])
                ),
                None,
            )
            if hit is None:
                groups.append([(position, int(start), int(stop))])
                if len(groups) > MAX_RULES:
                    raise ValueError("Raster rule inventory exceeds admission")
            else:
                hit.append((position, int(start), int(stop)))
    # Filled bars and logo/background rectangles are not thin rule evidence.
    thickness = max(3, round(min(mask.shape) * thickness_ratio))
    return [
        (median(p for p, _, _ in group), median(s for _, s, _ in group), median(e - 1 for _, _, e in group))
        for group in groups
        if group[-1][0] - group[0][0] + 1 <= thickness
    ]


def _coordinates(values: list[float], tolerance: float) -> list[float]:
    groups: list[list[float]] = []
    for value in sorted(values):
        if not groups or value - groups[-1][0] > tolerance:
            groups.append([])
        groups[-1].append(value)
    return [median(group) for group in groups]


def _covered(  # noqa: PLR0913, PLR0917
    lines: list[tuple[float, float, float]],
    coordinate: float,
    start: float,
    stop: float,
    tolerance: float,
    endpoint_tolerance: float | None = None,
) -> bool:
    endpoint = tolerance if endpoint_tolerance is None else endpoint_tolerance
    edge = start
    for _, left, right in sorted(
        (line for line in lines if abs(line[0] - coordinate) <= tolerance), key=lambda v: v[1]
    ):
        if left > edge + endpoint:
            return False
        edge = max(edge, right)
        if edge >= stop - endpoint:
            return True
    return False


def raster_vectors(image: Any, display_bbox: list[float], *, method: str = "baseline") -> list[dict[str, Any]]:  # noqa: C901, PLR0912
    """Propose physical raster grids in unchanged display coordinates.

    `image` is a PIL RGB/gray image corresponding exactly to `display_bbox`.
    Both dimensions must be at least 16 pixels and total pixels at most 2**22.
    Full outer edges are required; missing internal dividers imply rectangular
    merged cells. Pixels are evidence only: no word text or references are read.
    `baseline` retains the original fixed threshold. `contrast` estimates scan
    background/polarity. `gap` keeps the fixed threshold and closes small axis-aligned gaps;
    `repair` combines contrast with gap repair and
    admits strokes up to two percent of the smaller raster dimension. Repair
    is a separate hypothesis, never automatic semantic table acceptance.
    """
    import numpy as np

    if len(display_bbox) != 4 or any(
        isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in display_bbox
    ):
        raise ValueError("Invalid raster display bounds")
    x0, y0, x1, y1 = display_bbox
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Raster display bounds must have positive extent")
    width, height = image.size
    if min(width, height) < 16 or width * height > MAX_PIXELS:
        raise ValueError("Raster pixel admission exceeded")
    if method not in {"baseline", "contrast", "gap", "repair"}:
        raise ValueError("Unknown raster rule method")
    gray = np.asarray(image.convert("L"))
    if method in {"baseline", "gap"}:
        mask = gray < 160
    else:
        # The majority intensity estimates scan background without depending on
        # document identities. Preserve a minimum 24-level luminance contrast.
        background = float(np.median(gray))
        mask = gray > background + 24 if background < 128 else gray < background - 24
    gap = min(8, max(2, round(min(width, height) * 0.006))) if method in {"gap", "repair"} else 0
    thickness = 0.02 if method in {"gap", "repair"} else 0.008
    horizontal = _lines(mask, 0, max(20, round(width * 0.06)), max_gap=gap, thickness_ratio=thickness)
    vertical = _lines(mask, 1, max(20, round(height * 0.06)), max_gap=gap, thickness_ratio=thickness)
    if len(horizontal) + len(vertical) > MAX_RULES:
        raise ValueError("Raster rule inventory exceeds admission")
    count = len(horizontal) + len(vertical)
    parents = list(range(count))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    tolerance = max(2.0, min(width, height) * 0.003)
    endpoint = (
        max(tolerance, round(min(width, height) * thickness) / 2 + 1) if method in {"gap", "repair"} else tolerance
    )
    for hi, (y, left, right) in enumerate(horizontal):
        for vi, (x, top, bottom) in enumerate(vertical):
            if left - endpoint <= x <= right + endpoint and top - endpoint <= y <= bottom + endpoint:
                parents[find(hi)] = find(len(horizontal) + vi)
    components: dict[int, tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]] = defaultdict(
        lambda: ([], [])
    )
    for index, line in enumerate(horizontal):
        components[find(index)][0].append(line)
    for index, line in enumerate(vertical):
        components[find(len(horizontal) + index)][1].append(line)
    vectors = []
    for hs, vs in components.values():
        ys = _coordinates([line[0] for line in hs], tolerance)
        xs = _coordinates([line[0] for line in vs], tolerance)
        if len(xs) < 2 or len(ys) < 2 or (len(xs) == 2 and len(ys) == 2):
            continue  # A lone decorative rectangle offers no internal partition.
        # Reject a partial grid whose attached lines continue beyond the
        # proposed outer rectangle instead of silently shrinking its extent.
        if any(left < xs[0] - endpoint or right > xs[-1] + endpoint for _, left, right in hs) or any(
            top < ys[0] - endpoint or bottom > ys[-1] + endpoint for _, top, bottom in vs
        ):
            continue
        rows, columns = len(ys) - 1, len(xs) - 1
        if rows * columns > MAX_SLOTS:
            raise ValueError("Raster grid slots exceed admission")
        if not all(_covered(hs, y, xs[0], xs[-1], tolerance, endpoint) for y in (ys[0], ys[-1])) or not all(
            _covered(vs, x, ys[0], ys[-1], tolerance, endpoint) for x in (xs[0], xs[-1])
        ):
            continue
        cell_parents = list(range(rows * columns))

        def cell_find(index: int, cell_parents: list[int] = cell_parents) -> int:
            while cell_parents[index] != index:
                cell_parents[index] = cell_parents[cell_parents[index]]
                index = cell_parents[index]
            return index

        for row in range(rows):
            for column in range(columns):
                slot = row * columns + column
                if column + 1 < columns and not _covered(vs, xs[column + 1], ys[row], ys[row + 1], tolerance, endpoint):
                    cell_parents[cell_find(slot)] = cell_find(slot + 1)
                if row + 1 < rows and not _covered(hs, ys[row + 1], xs[column], xs[column + 1], tolerance, endpoint):
                    cell_parents[cell_find(slot)] = cell_find(slot + columns)
        groups: dict[int, list[int]] = defaultdict(list)
        for slot in range(rows * columns):
            groups[cell_find(slot)].append(slot)
        boxes: list[list[float] | None] = [None] * (rows * columns)
        spans = []
        valid = True
        for slots in groups.values():
            r0, r1 = min(s // columns for s in slots), max(s // columns for s in slots)
            c0, c1 = min(s % columns for s in slots), max(s % columns for s in slots)
            if len(slots) != (r1 - r0 + 1) * (c1 - c0 + 1):
                valid = False
                break
            boxes[r0 * columns + c0] = [
                x0 + xs[c0] / width * (x1 - x0),
                y0 + ys[r0] / height * (y1 - y0),
                x0 + xs[c1 + 1] / width * (x1 - x0),
                y0 + ys[r1 + 1] / height * (y1 - y0),
            ]
            spans.append({"row": r0, "column": c0, "row_span": r1 - r0 + 1, "column_span": c1 - c0 + 1})
        if valid:
            vectors.append(
                {
                    "row_count": rows,
                    "col_count": columns,
                    "cells": boxes,
                    "spans": spans,
                    "bbox": [
                        x0 + xs[0] / width * (x1 - x0),
                        y0 + ys[0] / height * (y1 - y0),
                        x0 + xs[-1] / width * (x1 - x0),
                        y0 + ys[-1] / height * (y1 - y0),
                    ],
                }
            )
    return vectors


def propose(
    image: Any, display_bbox: list[float], page: dict[str, Any], *, method: str = "baseline"
) -> list[dict[str, Any]]:
    """Return baseline and raster-grid hypotheses with exact source conservation."""
    baseline = native_state(page)
    baseline["id"] = "c0"
    vectors = raster_vectors(image, display_bbox, method=method)
    existing = page.get("vector_candidates", [])

    def box(vector: dict[str, Any]) -> list[float]:
        cells = [b for b in vector["cells"] if b is not None]
        return [min(b[0] for b in cells), min(b[1] for b in cells), max(b[2] for b in cells), max(b[3] for b in cells)]

    additions = [
        v
        for v in vectors
        if not any(
            min(v["bbox"][2], box(old)[2]) > max(v["bbox"][0], box(old)[0])
            and min(v["bbox"][3], box(old)[3]) > max(v["bbox"][1], box(old)[1])
            for old in existing
        )
    ]
    if not additions:
        return [baseline]
    augmented = {**page, "vector_candidates": [*deepcopy(existing), *additions]}
    candidate = native_state(augmented)
    candidate.update(
        id="c1", mechanism="raster_rules", description="Physical raster grids; semantic table admission unknown."
    )
    validate(page, candidate)
    return [baseline, candidate]
