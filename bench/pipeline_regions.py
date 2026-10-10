"""Source-only bounded region proposals and exact complete-page composition.

Coordinates and IDs stay in the original display space. Regions suggest work
units, never table semantics; capacity cuts explicitly report topology risk.
"""

# ruff: noqa: ANN401, EM101, TRY003, TRY004, PLR2004
from __future__ import annotations

import math
from collections import Counter
from copy import deepcopy
from itertools import pairwise
from statistics import median
from typing import Any

from bench.pipeline_assembly import _clean_table, _native, _owned, validate

MAX_PAGE_WORDS = 65_536
MAX_PAGE_CHARACTERS = 4 * 1024 * 1024
MAX_REGIONS = 1024


def _box(value: Any) -> list[float]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 4
        or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value)
        or value[0] > value[2]
        or value[1] > value[3]
    ):
        raise ValueError("Invalid display geometry")
    return list(value)


def _source(page: dict[str, Any]) -> dict[str, Any]:
    size = page["page_size"]
    if not isinstance(size, (list, tuple)) or len(size) not in (2, 4):
        raise ValueError("Invalid page size")
    bounds = _box([0, 0, *size] if len(size) == 2 else size)
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValueError("Page must have positive extent")
    words = page["words"]
    if not isinstance(words, list) or len(words) > MAX_PAGE_WORDS:
        raise ValueError("Complete page word admission exceeded")
    clean = []
    for word in words:
        if not isinstance(word["id"], str) or not isinstance(word["text"], str):
            raise ValueError("Invalid literal source word")
        clean.append({"id": word["id"], "text": word["text"], "bbox": _box(word["bbox"])})
    if len({w["id"] for w in clean}) != len(clean):
        raise ValueError("Duplicate global source IDs")
    if _characters(clean) > MAX_PAGE_CHARACTERS:
        raise ValueError("Complete page character admission exceeded")
    return {"page_size": list(size), "words": clean}


def _characters(words: list[dict[str, Any]]) -> int:
    return sum(len(w["id"]) + len(w["text"]) for w in words)


def _bounds(words: list[dict[str, Any]]) -> list[float]:
    return [
        min(w["bbox"][0] for w in words),
        min(w["bbox"][1] for w in words),
        max(w["bbox"][2] for w in words),
        max(w["bbox"][3] for w in words),
    ]


def _bands(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group nearby baselines with bounded OCR drift, without transitive chaining."""
    if not words:
        return []
    height = median(max(1, w["bbox"][3] - w["bbox"][1]) for w in words)
    bands: list[list[dict[str, Any]]] = []
    anchor = 0.0
    for word in sorted(words, key=lambda w: (w["bbox"][1], w["bbox"][0], w["id"])):
        center = (word["bbox"][1] + word["bbox"][3]) / 2
        if not bands or center - anchor > 0.5 * height:
            bands.append([])
            anchor = center
        bands[-1].append(word)
    return bands


def _geometric_parts(words: list[dict[str, Any]]) -> list[tuple[list[dict[str, Any]], str]]:  # noqa: C901
    """Prefer empty vertical bands, then one sustained wide horizontal corridor."""
    if not words:
        return []
    height = median(max(1, w["bbox"][3] - w["bbox"][1]) for w in words)
    bands = _bands(words)
    band_bounds = [(min(w["bbox"][1] for w in band), max(w["bbox"][3] for w in band)) for band in bands]
    gaps = [
        following[0] - previous[1]
        for previous, following in pairwise(band_bounds)
        if following[0] > previous[1]
    ]
    # Sparse table leading can exceed several glyph heights. Compare against
    # observed whitespace as well, so ordinary rows stay in one work unit.
    gap_threshold = max(2.5 * height, 2.5 * median(gaps)) if gaps else 2.5 * height
    groups: list[list[dict[str, Any]]] = []
    bottom = float("-inf")
    for band in bands:
        top = min(w["bbox"][1] for w in band)
        if not groups or top - bottom > gap_threshold:
            groups.append([])
        groups[-1].extend(band)
        bottom = max(bottom, *(w["bbox"][3] for w in band))
    if len(groups) > 1:
        return [(part, "vertical_gap") for group in groups for part, _ in _geometric_parts(group)]
    # Empty x intervals are supported by all retained words, not a handful of
    # unusually spaced rows. A wide title therefore blocks this split.
    ordered = sorted(words, key=lambda w: (w["bbox"][0], w["bbox"][2], w["id"]))
    width = _bounds(words)[2] - _bounds(words)[0]
    right = ordered[0]["bbox"][2]
    candidates = []
    for index, word in enumerate(ordered[1:], 1):
        gap = word["bbox"][0] - right
        if gap >= max(6 * height, 0.16 * width):
            candidates.append((gap, index))
        right = max(right, word["bbox"][2])

    def widest_internal_gap(part: list[dict[str, Any]]) -> float:
        edge = min(w["bbox"][0] for w in part)
        widest = 0.0
        for word in sorted(part, key=lambda w: w["bbox"][0]):
            widest = max(widest, word["bbox"][0] - edge)
            edge = max(edge, word["bbox"][2])
        return widest

    for gap, index in sorted(candidates, reverse=True):
        left, right_words = ordered[:index], ordered[index:]
        sides = (_bands(left), _bands(right_words))
        # A normal table has repeated comparable column gaps. Independent
        # blocks need a stronger intervening corridor and sustained width,
        # rather than one unusually wide heading on an otherwise tiny column.
        if (
            min(map(len, sides)) >= 3
            and all(median(_bounds(band)[2] - _bounds(band)[0] for band in side) >= 4 * height for side in sides)
            and gap > 1.8 * max(widest_internal_gap(left), widest_internal_gap(right_words))
        ):
            return [(left, "wide_gutter"), (right_words, "wide_gutter")]
    return [(words, "unsplit")]


def split(  # noqa: C901, PLR0912
    page: dict[str, Any], *, max_words: int = 512, max_characters: int = 8000, crop_padding: float = 4.0
) -> dict[str, Any]:
    """Partition all words exactly once; preserve native grids as atomic regions.

    Native regions may use the legacy 4096-word/16000-character source admission.
    Residual capacity chunks keep physical bands when possible, but are marked
    incomplete context because table rows can span chunks. No topology is merged
    across a capacity boundary by this module.
    """
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (max_words, max_characters)):
        raise ValueError("Region budgets must be positive integers")
    if max_words > 4096 or max_characters > 16_000:
        raise ValueError("Region budget exceeds downstream source admission")
    if (
        isinstance(crop_padding, bool)
        or not isinstance(crop_padding, (int, float))
        or not math.isfinite(crop_padding)
        or crop_padding < 0
    ):
        raise ValueError("Crop padding must be finite and nonnegative")
    source = _source(page)
    words = source["words"]
    lookup = {w["id"]: w for w in words}
    # Existing topology validation applies before any word is removed from the
    # residual. Malformed native input rejects this entire plan.
    native = _native(page, words)
    for table in native:
        _clean_table(table, lookup)
    native_ids = _owned(native)
    if len(native_ids) != len(set(native_ids)):
        raise ValueError("Overlapping native source ownership")
    vectors = page.get("vector_candidates", [])
    specs: list[tuple[list[dict[str, Any]], list[dict[str, Any]], str, str]] = []
    for vector, table in zip(vectors, native, strict=True):
        ids = set(_owned([table]))
        owned = [w for w in words if w["id"] in ids]
        if len(owned) > 4096 or _characters(owned) > 16_000:
            raise ValueError("Atomic native grid exceeds downstream admission")
        # Preserve only geometry and topology; never forward observed values.
        clean_vector = {k: deepcopy(vector[k]) for k in ("row_count", "col_count", "cells", "spans")}
        specs.append((owned, [clean_vector], "native", "atomic_native"))
    used = set(native_ids)
    residual = [w for w in words if w["id"] not in used]
    for part, reason in _geometric_parts(residual):
        if len(part) <= max_words and _characters(part) <= max_characters:
            specs.append((part, [], "residual", reason))
            continue
        chunk: list[dict[str, Any]] = []
        for band in _bands(part):
            if any(_characters([w]) > max_characters for w in band):
                raise ValueError("One source word exceeds region character budget")
            if len(band) > max_words or _characters(band) > max_characters:
                if chunk:
                    specs.append((chunk, [], "residual", "capacity_rows"))
                    chunk = []
                for word in band:
                    if chunk and (len(chunk) == max_words or _characters(chunk) + _characters([word]) > max_characters):
                        specs.append((chunk, [], "residual", "capacity_words"))
                        chunk = []
                    chunk.append(word)
                if chunk:
                    specs.append((chunk, [], "residual", "capacity_words"))
                    chunk = []
            else:
                if chunk and (
                    len(chunk) + len(band) > max_words or _characters(chunk) + _characters(band) > max_characters
                ):
                    specs.append((chunk, [], "residual", "capacity_rows"))
                    chunk = []
                chunk.extend(band)
        if chunk:
            specs.append((chunk, [], "residual", "capacity_rows"))
    if len(specs) > MAX_REGIONS:
        raise ValueError("Complete region count exceeds admission")
    regions: list[dict[str, Any]] = []
    for owned, vector, kind, boundary in specs:
        boxes = [b for v in vector for b in v["cells"] if b is not None]
        bounds = _bounds(owned) if owned else list(boxes[0]) if boxes else None
        for box in boxes:
            bounds = (
                [min(bounds[0], box[0]), min(bounds[1], box[1]), max(bounds[2], box[2]), max(bounds[3], box[3])]
                if bounds
                else list(box)
            )
        if bounds is None:
            raise ValueError("Native grid has no drawable cell geometry")
        bounds = [
            bounds[0] - crop_padding,
            bounds[1] - crop_padding,
            bounds[2] + crop_padding,
            bounds[3] + crop_padding,
        ]
        regions.append(
            {
                "id": f"r{len(regions)}",
                "kind": kind,
                "bbox": bounds,
                "source_ids": [w["id"] for w in owned],
                "boundary": boundary,
                "context_complete": not boundary.startswith("capacity_"),
                "source": {
                    "page_size": list(source["page_size"]),
                    "words": [deepcopy(lookup[w["id"]]) for w in owned],
                    "vector_candidates": vector,
                },
            }
        )
    if Counter(i for r in regions for i in r["source_ids"]) != Counter(lookup.keys()):
        raise ValueError("Region plan violates exact page source ownership")
    return {**source, "regions": regions, "coordinate_space": "display_global"}


def unresolved_region(region: dict[str, Any]) -> dict[str, Any]:
    """Explicit abstention preserves every word when a region gate cannot decide."""
    return {"id": "c0", "tables": [], "unresolved_ids": list(region["source_ids"]), "mechanism": "unresolved"}


def validate_composed(page: dict[str, Any], state: dict[str, Any]) -> None:
    """Validate aggregate conservation without legacy whole-page packet limits."""
    source = _source(page)
    lookup = {w["id"]: w for w in source["words"]}
    if Counter(_owned(state["tables"]) + state["unresolved_ids"]) != Counter(lookup.keys()):
        raise ValueError("Composed state violates exact page source ownership")
    for table in state["tables"]:
        rows, columns = table["row_count"], table["col_count"]
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in (rows, columns)):
            raise ValueError("Invalid composed table dimensions")
        if rows * columns > 4096 or len(table["cells"]) != rows * columns:
            raise ValueError("Invalid composed table slots")
        if table["values"] != _clean_table(table, lookup)["values"]:
            raise ValueError("Composed values do not derive from literal source")


def compose(plan: dict[str, Any], states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Validate every region output and return one exact, complete-page state."""
    source = _source(plan)
    regions = plan["regions"]
    if len(regions) > MAX_REGIONS or len({r["id"] for r in regions}) != len(regions):
        raise ValueError("Invalid region inventory")
    if set(states) != {r["id"] for r in regions}:
        raise ValueError("Missing or unexpected region output")
    lookup = {w["id"]: w for w in source["words"]}
    tables = []
    unresolved = []
    for region in regions:
        local = region["source"]
        if local["page_size"] != source["page_size"] or local["words"] != [lookup[i] for i in region["source_ids"]]:
            raise ValueError("Region source differs from original display source")
        state = states[region["id"]]
        validate(local, state)
        tables.extend(deepcopy(state["tables"]))
        unresolved.extend(state["unresolved_ids"])
    unresolved_set = set(unresolved)
    result = {
        "id": "composed",
        "tables": tables,
        "unresolved_ids": [w["id"] for w in source["words"] if w["id"] in unresolved_set],
        "mechanism": "bounded_regions",
        "region_ids": [r["id"] for r in regions],
    }
    # Validate the uncollapsed inventory too: duplicate unresolved IDs must not
    # disappear when restoring original source order.
    if Counter(_owned(tables) + unresolved) != Counter(lookup.keys()):
        raise ValueError("Region outputs violate aggregate exact source ownership")
    validate_composed(source, result)
    return result
