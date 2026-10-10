"""Experimental source-only accounting around native and image-transcribed tables.

Composition never claims source identity for replacement text. No inference,
reference loading, source mutation, or default library behavior is implemented.
"""

# Bounded experimental JSON states are intentionally heterogeneous.
# ruff: noqa: EM101, EM102, TRY003, TRY004, TRY301, PLR2004, C901, PLR0912
from __future__ import annotations

import html
from collections import Counter
from copy import deepcopy
from typing import Any

from bench.pipeline_assembly import _clean_table, _native, _owned
from bench.pipeline_regions import _source, validate_composed
from bench.pipeline_vision_transcription import PROVENANCE, _viewport
from bench.pipeline_vision_transcription import markdown as vision_markdown

MAX_TABLES = 32
MAX_SLOTS = 4096
RULES_V1 = {
    "version": 1,
    "native_geometry": "Full retained vector grid bounds; never owned text bounds",
    "replacement": "Supersede only fully contained words; keep crossing and outside words",
    "overlap": "Positive-area overlap refuses the whole page; touching edges allowed",
    "ordering": "Retained word order; table anchor at first owned/superseded word, geometry fallback",
    "failure": "Validated native baseline is diagnostic only; no complete hybrid output",
    "limits": {"tables": MAX_TABLES, "aggregate_slots": MAX_SLOTS, "words": 65536, "source_characters": 4194304},
}

RULES = {
    **RULES_V1,
    "version": 2,
    "renderer_version": 2,
    "ordering": (
        "Retained source anchors first; unowned tables use next geometric source anchor; "
        "ties use display y/x then insertion order"
    ),
}


def _contains(outer: list[float], inner: list[float]) -> bool:
    return all(outer[i] <= inner[i] for i in (0, 1)) and all(inner[i] <= outer[i] for i in (2, 3))


def _overlap(a: list[float], b: list[float]) -> bool:
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def _native_html(table: dict[str, Any]) -> str:
    """Match the existing native baseline renderer, with escaped literal values."""
    spans = {(s["row"], s["column"]): s for s in table["spans"]}
    text = ["<table>"]
    for r, row in enumerate(table["values"]):
        text.append("<tr>")
        for c, value in enumerate(row):
            if value is None:
                continue
            span = spans.get((r, c), {"row_span": 1, "column_span": 1})
            attrs = f' rowspan="{span["row_span"]}" colspan="{span["column_span"]}"'
            text.append(f"<td{attrs}>{html.escape(value)}</td>")
        text.append("</tr>")
    text.append("</table>")
    return "\n".join(text)


def _render_v1(
    source: dict[str, Any], tables: list[dict[str, Any]], prose: list[str], superseded: dict[int, list[str]]
) -> str:
    lookup = {w["id"]: w for w in source["words"]}
    order = {ident: i for i, ident in enumerate(lookup)}
    entries: list[tuple[int, str]] = []
    for index, table in enumerate(tables):
        if table["text_provenance"] == PROVENANCE:
            markup = vision_markdown({"tables": [table], "text_provenance": PROVENANCE, "source_conserved": False})
            ids = superseded[index]
            fallback = next(
                (
                    i
                    for i, w in enumerate(source["words"])
                    if (w["bbox"][1], w["bbox"][0]) >= (table["bbox"][1], table["bbox"][0])
                ),
                len(order),
            )
        else:
            markup = _native_html(table)
            ids = _owned([table])
            fallback = len(order)
        entries.append((min((order[i] for i in ids), default=fallback), markup))
    lines: dict[tuple[Any, ...], list[str]] = {}
    for ident in prose:
        word = lookup[ident]
        line = tuple(word.get("line", [round(word["bbox"][1], 1)]))
        lines.setdefault(line, []).append(ident)
    entries.extend(
        (min(order[i] for i in ids), "<p>" + html.escape(" ".join(lookup[i]["text"] for i in ids)) + "</p>")
        for ids in lines.values()
    )
    return "\n\n".join(text for _, text in sorted(entries)) + "\n"


def _render_v2(
    source: dict[str, Any], tables: list[dict[str, Any]], prose: list[str], superseded: dict[int, list[str]]
) -> str:
    lookup = {w["id"]: w for w in source["words"]}
    order = {ident: i for i, ident in enumerate(lookup)}
    # Geometry is a display-space fallback, not inferred logical reading order.
    entries: list[tuple[int, float, float, int, str]] = []
    for index, table in enumerate(tables):
        if table["text_provenance"] == PROVENANCE:
            markup = vision_markdown({"tables": [table], "text_provenance": PROVENANCE, "source_conserved": False})
            ids = superseded[index]

        else:
            markup = _native_html(table)
            ids = _owned([table])
        fallback = next(
            (
                i
                for i, w in enumerate(source["words"])
                if (w["bbox"][1], w["bbox"][0]) >= (table["bbox"][1], table["bbox"][0])
            ),
            len(order),
        )
        entries.append(
            (min((order[i] for i in ids), default=fallback), table["bbox"][1], table["bbox"][0], len(entries), markup)
        )
    lines: dict[tuple[Any, ...], list[str]] = {}
    for ident in prose:
        word = lookup[ident]
        line = tuple(word.get("line", [round(word["bbox"][1], 1)]))
        lines.setdefault(line, []).append(ident)
    for ids in lines.values():
        y, x = min((lookup[i]["bbox"][1], lookup[i]["bbox"][0]) for i in ids)
        markup = "<p>" + html.escape(" ".join(lookup[i]["text"] for i in ids)) + "</p>"
        entries.append((min(order[i] for i in ids), y, x, len(entries), markup))
    return "\n\n".join(entry[-1] for entry in sorted(entries, key=lambda entry: entry[:4])) + "\n"


def _render(
    source: dict[str, Any],
    tables: list[dict[str, Any]],
    prose: list[str],
    superseded: dict[int, list[str]],
    render_version: int,
) -> str:
    renderer = _render_v1 if render_version == 1 else _render_v2
    return renderer(source, tables, prose, superseded)


def _baseline(
    source: dict[str, Any], state: dict[str, Any], viewport: list[float], render_version: int = 2
) -> dict[str, Any]:
    vectors = source.get("vector_candidates", [])
    if not isinstance(vectors, list) or len(vectors) > MAX_TABLES:
        raise ValueError("Native grid inventory admission exceeded")
    if any(type(v.get(k)) is not int or v[k] < 1 for v in vectors for k in ("row_count", "col_count")):
        raise ValueError("Invalid native grid dimensions")
    if sum(v["row_count"] * v["col_count"] for v in vectors) > MAX_SLOTS:
        raise ValueError("Aggregate native slot admission exceeded")
    validate_composed(source, state)
    lookup = {w["id"]: w for w in source["words"]}
    expected = [_clean_table(t, lookup) for t in _native(source, source["words"])]
    if [_clean_table(t, lookup) for t in state["tables"]] != expected:
        raise ValueError("Native state differs from retained native grid ownership")
    tables = []
    for table, vector in zip(expected, vectors, strict=True):
        cells = [list(_viewport(b)) for b in vector["cells"] if b is not None]
        if not cells:
            raise ValueError("Native grid has no retained physical geometry")
        bounds = [
            min(b[0] for b in cells),
            min(b[1] for b in cells),
            max(b[2] for b in cells),
            max(b[3] for b in cells),
        ]
        if "bbox" in vector:
            bbox = list(_viewport(vector["bbox"]))
            if not _contains(bbox, bounds):
                raise ValueError("Native physical bounds exclude retained grid geometry")
        else:
            bbox = bounds
        if not _contains(viewport, bbox):
            raise ValueError("Native grid outside page viewport")
        tables.append({**deepcopy(table), "bbox": bbox, "text_provenance": "native-source", "source_conserved": True})
    native_owners = {ident: i for i, t in enumerate(tables) for ident in _owned([t])}
    prose = list(state["unresolved_ids"])
    ledger = [
        {
            "id": w["id"],
            "owner": "native" if w["id"] in native_owners else "prose",
            "table_index": native_owners.get(w["id"]),
        }
        for w in source["words"]
    ]
    return {
        "tables": tables,
        "unresolved_ids": prose,
        "superseded_ids": [],
        "source_ledger": ledger,
        "source_conserved": True,
        "source_inventory_complete": True,
        "accounting_complete": True,
        "markdown": _render(source, tables, prose, {}, render_version),
    }


def sanitize_vectors(source: dict[str, Any]) -> dict[str, Any]:
    """Project complete words and physical native geometry; discard annotations."""
    clean = _source(source)
    vectors = source.get("vector_candidates", [])
    if not isinstance(vectors, list) or len(vectors) > MAX_TABLES:
        raise ValueError("Native grid inventory admission exceeded")
    if any(type(v.get(k)) is not int or v[k] < 1 for v in vectors for k in ("row_count", "col_count")):
        raise ValueError("Invalid native grid dimensions")
    if sum(v["row_count"] * v["col_count"] for v in vectors) > MAX_SLOTS:
        raise ValueError("Aggregate native slot admission exceeded")
    if any(not isinstance(v.get(k), list) or len(v[k]) > MAX_SLOTS for v in vectors for k in ("cells", "spans")):
        raise ValueError("Native geometry inventory admission exceeded")
    clean["vector_candidates"] = []
    for vector in vectors:
        projected = {k: deepcopy(vector[k]) for k in ("row_count", "col_count", "cells", "spans")}
        if "bbox" in vector:
            projected["bbox"] = list(_viewport(vector["bbox"]))
        projected["spans"] = [
            {k: span[k] for k in ("row", "column", "row_span", "column_span")} for span in projected["spans"]
        ]
        clean["vector_candidates"].append(projected)
    for original, word in zip(source["words"], clean["words"], strict=True):
        if "line" in original:
            line = original["line"]
            if not isinstance(line, (list, tuple)) or any(not isinstance(v, (str, int, float)) for v in line):
                raise ValueError("Invalid retained source line identity")
            word["line"] = list(line)
    return clean


def native_boxes(source: dict[str, Any], native_state: dict[str, Any]) -> list[list[float]]:
    """Return verified full physical native boxes, ignoring runtime text bounds."""
    clean = sanitize_vectors(source)
    size = clean["page_size"]
    viewport = list(_viewport([0, 0, *size] if len(size) == 2 else size))
    return [deepcopy(t["bbox"]) for t in _baseline(clean, native_state, viewport)["tables"]]


def exclude_native_proposals(
    detection: dict[str, Any], boxes: list[list[float]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Filter whole table proposals without clipping; retained originals stay unchanged."""
    if not isinstance(detection.get("boxes"), list) or len(detection["boxes"]) > 1024 or len(boxes) > MAX_TABLES:
        raise ValueError("Detector/native inventory admission exceeded")
    checked = [list(_viewport(b)) for b in boxes]
    filtered = deepcopy(detection)
    filtered["boxes"] = []
    diagnostics = []
    for index, box in enumerate(detection["boxes"]):
        if not isinstance(box.get("label"), str):
            raise ValueError("Detector proposal label is invalid")
        bounds = list(_viewport(box["bbox"]))
        hits = (
            [i for i, native in enumerate(checked) if _overlap(bounds, native)]
            if box["label"].casefold() == "table"
            else []
        )
        if hits:
            diagnostics.append(
                {
                    "proposal_index": index,
                    "proposal": deepcopy(box),
                    "native_indices": hits,
                    "native_boxes": [deepcopy(checked[i]) for i in hits],
                    "reason": "positive_area_native_grid_overlap",
                    "coverage_uncertain": True,
                    "residual_policy": "Retain all non-native original words as prose; no partial crop synthesized",
                }
            )
        else:
            filtered["boxes"].append(deepcopy(box))
    return filtered, diagnostics


def markdown(composed: dict[str, Any]) -> str:
    """Read markup from trusted compose replay, never from an unvalidated raw artifact.

    Callers handling retained external JSON must replay compose first; this accessor
    does not attest arbitrary stored HTML or source provenance.
    """
    if (
        composed.get("status") != "ok"
        or composed.get("accounting_complete") is not True
        or not isinstance(composed.get("markdown"), str)
    ):
        raise ValueError("No complete successful hybrid Markdown output")
    return composed["markdown"]


def compose(
    source: dict[str, Any], native_state: dict[str, Any], transcription: dict[str, Any], *, render_version: int = 2
) -> dict[str, Any]:
    """Compose atomically; replacement text has provenance but never original source IDs.

    Invalid source/native state raises before any output. A rejected transcription
    returns status abstained and a native baseline artifact labeled diagnostic only.
    Strict transcription uses pipeline_vision_transcription.parse canonical output.
    Version 1 is explicit historical verification only; callers select it from a
    trusted frozen module hash, never from source or model-controlled fields.
    """
    if type(render_version) is not int or render_version not in (1, 2):
        raise ValueError("Unknown hybrid renderer version")
    clean = sanitize_vectors(source)
    size = clean["page_size"]
    viewport = list(_viewport([0, 0, *size] if len(size) == 2 else size))
    baseline = _baseline(clean, native_state, viewport, render_version)
    result = {
        "status": "ok",
        "route": "hybrid_composition",
        "viewport": viewport,
        "rules": deepcopy(RULES_V1 if render_version == 1 else RULES),
        "diagnostics": [],
    }
    try:
        # Existing renderer revalidates every canonical matrix, string, span and provenance.
        vision_markdown(transcription)
        transcribed = transcription["tables"]
        native = baseline["tables"]
        if (
            len(native) + len(transcribed) > MAX_TABLES
            or sum(t["row_count"] * t["col_count"] for t in native + transcribed) > MAX_SLOTS
        ):
            raise ValueError("Hybrid aggregate table or slot admission exceeded")
        for index, table in enumerate(transcribed):
            bounds = list(_viewport(table["bbox"]))
            if not _contains(viewport, bounds):
                raise ValueError(f"Transcribed table {index} outside page viewport")
            for ni, grid in enumerate(native):
                if _overlap(bounds, grid["bbox"]):
                    raise ValueError(f"Transcribed table {index} overlaps native grid {ni}")
            for previous, other in enumerate(transcribed[:index]):
                if _overlap(bounds, other["bbox"]):
                    raise ValueError(f"Transcribed table {index} overlaps transcribed table {previous}")
        if not transcribed:
            return {**result, **baseline}
        tables = native + deepcopy(transcribed)
        native_ids = set(_owned(native))
        superseded: dict[int, list[str]] = {len(native) + i: [] for i in range(len(transcribed))}
        replacement_owner = {}
        crossing = []
        for word in clean["words"]:
            if word["id"] in native_ids:
                continue
            for index, table in enumerate(transcribed, start=len(native)):
                if _contains(table["bbox"], word["bbox"]):
                    if word["id"] in replacement_owner:
                        raise ValueError("Word fully contained by multiple transcribed boxes")
                    superseded[index].append(word["id"])
                    replacement_owner[word["id"]] = index
                elif _overlap(table["bbox"], word["bbox"]):
                    crossing.append({"id": word["id"], "table_index": index})
        prose = [i for i in baseline["unresolved_ids"] if i not in replacement_owner]
        ledger = [
            {"id": entry["id"], "owner": "superseded", "table_index": replacement_owner[entry["id"]]}
            if entry["id"] in replacement_owner
            else deepcopy(entry)
            for entry in baseline["source_ledger"]
        ]
        if Counter(e["id"] for e in ledger) != Counter(w["id"] for w in clean["words"]):
            raise ValueError("Hybrid source ledger violates complete inventory")
        if Counter(_owned(native) + prose + list(replacement_owner)) != Counter(w["id"] for w in clean["words"]):
            raise ValueError("Hybrid source partition is incomplete or duplicated")
        return {
            **result,
            "tables": tables,
            "unresolved_ids": prose,
            "superseded_ids": [w["id"] for w in clean["words"] if w["id"] in replacement_owner],
            "source_ledger": ledger,
            "source_conserved": False,
            "source_inventory_complete": True,
            "accounting_complete": True,
            "crossing_words_retained": crossing,
            "markdown": _render(clean, tables, prose, superseded, render_version),
        }
    except (ValueError, TypeError, KeyError, IndexError) as error:
        return {
            **result,
            "status": "abstained",
            "tables": [],
            "unresolved_ids": [],
            "superseded_ids": [],
            "source_ledger": [],
            "source_conserved": False,
            "source_inventory_complete": True,
            "accounting_complete": False,
            "markdown": None,
            "diagnostics": [{"code": "page_atomic_composition_refusal", "detail": str(error)}],
            "diagnostic_baseline": {**baseline, "diagnostic_only": True},
        }
