"""Opt-in logical native table projection without changing physical source evidence."""

# Canonical experimental table dictionaries intentionally retain heterogeneous fields.
# ruff: noqa: ANN401, EM101, TRY003, SLF001, PLC0415, PLR2004
from __future__ import annotations

import math
from collections import Counter
from copy import deepcopy
from typing import Any

from bench import pipeline_hybrid_composition as hybrid
from bench.pipeline_assembly import _clean_table, _owned
from bench.pipeline_regions import _box

DIRECTIONS = ("right", "down", "left", "up")
SPEC = {
    "version": 1,
    "direction": "Core Markdown character-weighted actual table baselines; page fallback if absent",
    "projection": "Reindex native slots/spans and source-ID order into logical inline/block axes",
    "preserved": "Physical source words, native child state, table bboxes, exclusions, model tables and source ledger",
    "scope": "Post-composition only; no image transform, source text rewrite, OCR or inference",
}


def evidence(page: Any, boxes: list[list[float]]) -> dict[str, Any]:
    """Retain bounded native baseline evidence using the core Markdown direction rule."""
    from pdfust import _markdown

    layout = page.get_text("dict")
    lines = [line for block in layout["blocks"] for line in block.get("lines", [])]
    if len(lines) > 65536:
        raise ValueError("Native baseline line admission exceeded")
    retained: list[dict[str, Any]] = []
    for line in lines:
        direction = list(line["dir"])
        if len(direction) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in direction):
            raise ValueError("Invalid native baseline direction")
        retained.append(
            {
                "bbox": _box(line["bbox"]),
                "direction": direction,
                "weight": max(1, len(_markdown._line_text(line))),
                "axis": _markdown._line_orientation(line),
            }
        )
    if sum(line["weight"] for line in retained) > 4194304:
        raise ValueError("Native baseline character admission exceeded")
    result = []
    for index, box in enumerate(boxes):
        bounds = (box[0], box[1], box[2], box[3])
        inside = [i for i, line in enumerate(lines) if _markdown._line_inside_bbox(line, bounds)]
        selected = inside or list(range(len(lines)))
        votes: Counter[str] = Counter()
        for i in selected:
            votes[retained[i]["axis"]] += retained[i]["weight"]
        chosen = _markdown.table_orientation(layout, bounds)
        if chosen != (votes.most_common(1)[0][0] if votes else "right"):
            raise ValueError("Core native orientation evidence differs from votes")
        result.append(
            {
                "index": index,
                "bbox": list(box),
                "direction": chosen,
                "scope": "table" if inside else "page_fallback" if lines else "no_native_lines",
                "votes": dict(votes),
                "line_indices": selected,
            }
        )
    return {
        "spec": deepcopy(SPEC),
        "viewport": list(page.rect),
        "original_rotation": page.rotation,
        "baseline_lines": retained,
        "tables": result,
    }


def _slot(row: int, column: int, rows: int, columns: int, direction: str) -> tuple[int, int]:
    if direction == "down":
        return columns - 1 - column, row
    if direction == "left":
        return rows - 1 - row, columns - 1 - column
    if direction == "up":
        return column, rows - 1 - row
    return row, column


def _word_key(word: dict[str, Any], direction: str) -> tuple[float, float, str]:
    x0, y0, x1, y1 = word["bbox"]
    if direction == "down":
        return -x1, y0, word["id"]
    if direction == "left":
        return -y1, -x1, word["id"]
    if direction == "up":
        return x0, -y1, word["id"]
    return y0, x0, word["id"]


def _orient(table: dict[str, Any], source: dict[str, Any], direction: str) -> dict[str, Any]:
    rows, columns = table["row_count"], table["col_count"]
    new_rows, new_columns = (columns, rows) if direction in {"down", "up"} else (rows, columns)
    cells = [{"source_ids": [], "role": "unknown"} for _ in range(rows * columns)]
    lookup = {word["id"]: word for word in source["words"]}
    spans = []
    for span in table["spans"]:
        row, column, rs, cs = (span[k] for k in ("row", "column", "row_span", "column_span"))
        mapped = [
            _slot(r, c, rows, columns, direction) for r in range(row, row + rs) for c in range(column, column + cs)
        ]
        rr, cc = min(r for r, _ in mapped), min(c for _, c in mapped)
        height, width = max(r for r, _ in mapped) - rr + 1, max(c for _, c in mapped) - cc + 1
        ids = table["cells"][row * columns + column]["source_ids"]
        cells[rr * new_columns + cc]["source_ids"] = sorted(ids, key=lambda ident: _word_key(lookup[ident], direction))
        spans.append({"row": rr, "column": cc, "row_span": height, "column_span": width})
    projected = {
        "row_count": new_rows,
        "col_count": new_columns,
        "cells": cells,
        "spans": sorted(spans, key=lambda span: (span["row"], span["column"])),
    }
    clean = _clean_table(projected, lookup)
    if Counter(_owned([clean])) != Counter(_owned([table])):
        raise ValueError("Logical projection changed native source ownership")
    return {**table, **clean}


def compose(
    source: dict[str, Any], native_state: dict[str, Any], vision: dict[str, Any], orientation: dict[str, Any]
) -> dict[str, Any]:
    """Validate physical composition first, then orient only source-owned native tables."""
    composed = hybrid.compose(source, native_state, vision)
    if composed["status"] != "ok":
        return composed
    boxes = hybrid.native_boxes(source, native_state)
    size = source["page_size"]
    viewport = [0, 0, *size] if len(size) == 2 else list(size)
    entries = orientation["tables"]
    if orientation.get("spec") != SPEC or orientation.get("viewport") != viewport or len(entries) != len(boxes):
        raise ValueError("Native orientation evidence differs from physical source")
    for index, (entry, box) in enumerate(zip(entries, boxes, strict=True)):
        if entry.get("index") != index or entry.get("bbox") != box or entry.get("direction") not in DIRECTIONS:
            raise ValueError("Invalid native table orientation evidence")
        composed["tables"][index] = _orient(composed["tables"][index], source, entry["direction"])
    superseded = {
        index: [
            item["id"]
            for item in composed["source_ledger"]
            if item["owner"] == "superseded" and item["table_index"] == index
        ]
        for index in range(len(boxes), len(composed["tables"]))
    }
    composed["markdown"] = hybrid._render(source, composed["tables"], composed["unresolved_ids"], superseded, 2)
    composed["rules"] = {**composed["rules"], "native_table_orientation": deepcopy(SPEC)}
    composed["native_orientation_evidence"] = deepcopy(orientation)
    return composed
