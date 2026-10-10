"""Source-only projection of native tables for complete-pipeline experiments.

Retained detector anchors define ownership. Geometry cannot recover a divider
that is absent across an entire merged header band. No reference is consulted.
"""

# Retained benchmark schemas intentionally use JSON dictionaries.
# ruff: noqa: ANN401, EM101, TRY003, PLR2004, C901, PLR0912
from __future__ import annotations

import math
from typing import Any


def _box(value: Any) -> list[float]:
    coordinates = list(value)
    if len(coordinates) != 4 or any(not math.isfinite(x) for x in coordinates):
        raise ValueError("Native table geometry must be finite")
    if coordinates[0] >= coordinates[2] or coordinates[1] >= coordinates[3]:
        raise ValueError("Native table geometry must have positive area")
    return coordinates


def observed_table(table: Any) -> dict[str, Any]:
    """Project exact rectangular slot ownership, rejecting inconsistent snapshots."""
    rows, columns = table.row_count, table.col_count
    if any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in (rows, columns)):
        raise ValueError("Invalid native table dimensions")
    if rows * columns > 4096:
        raise ValueError("Native table exceeds slot admission")
    anchors = list(table._cell_anchors)  # noqa: SLF001 - detector snapshot ownership
    cells = [None if cell is None else _box(cell) for cell in table.cells]
    values = table.extract()
    if len(anchors) != rows * columns or len(cells) != rows * columns:
        raise ValueError("Native table ownership shape differs from dimensions")
    if len(values) != rows or any(len(row) != columns for row in values):
        raise ValueError("Native table value shape differs from dimensions")
    bbox = _box(table.bbox)
    owners: dict[int, list[int]] = {}
    for index, anchor in enumerate(anchors):
        if isinstance(anchor, bool) or not isinstance(anchor, int) or not 0 <= anchor < len(cells):
            raise ValueError("Invalid native cell anchor")
        if anchors[anchor] != anchor or cells[anchor] is None:
            raise ValueError("Native cell anchor must own retained geometry")
        if (index == anchor) != (cells[index] is not None):
            raise ValueError("Native continuation slot has inconsistent geometry")
        if index != anchor and values[index // columns][index % columns] is not None:
            raise ValueError("Native continuation slot has owned text")
        owners.setdefault(anchor, []).append(index)
    spans = []
    retained = []
    tolerance = 0.01
    for anchor, indexes in sorted(owners.items()):
        row, column = divmod(anchor, columns)
        last_row = max(index // columns for index in indexes)
        last_column = max(index % columns for index in indexes)
        expected = [r * columns + c for r in range(row, last_row + 1) for c in range(column, last_column + 1)]
        if indexes != expected:
            raise ValueError("Native anchor ownership must be a top-left rectangle")
        cell = cells[anchor]
        if cell is None:
            raise ValueError("Native owner geometry is missing")
        if any(cell[i] < bbox[i] - tolerance for i in (0, 1)) or any(cell[i] > bbox[i] + tolerance for i in (2, 3)):
            raise ValueError("Native cell geometry lies outside table")
        for other in retained:
            if (
                min(cell[2], other[2]) - max(cell[0], other[0]) > tolerance
                and min(cell[3], other[3]) - max(cell[1], other[1]) > tolerance
            ):
                raise ValueError("Distinct native owners overlap in display geometry")
        retained.append(cell)
        spans.append(
            {"row": row, "column": column, "row_span": last_row - row + 1, "column_span": last_column - column + 1}
        )
    return {
        "bbox": bbox,
        "row_count": rows,
        "col_count": columns,
        "values": values,
        "cells": cells,
        "spans": spans,
        "diagnostics": dict(table.diagnostics._asdict()),
    }
