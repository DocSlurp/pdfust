"""Offline counterfactual format repair for retained image-only transcriptions.

The strict adapter remains the default. Repairs never consult references, move
literal values, infer text, rescale geometry, or repair invalid merged spans.
"""

# ruff: noqa: EM101, TRY003, TRY004, PLR2004, SLF001, C901, PLR0912
from __future__ import annotations

import hashlib
import importlib
import json
from typing import Any

VERSION = "p002-vision-format-repair-v1"


def _literal_positions(tables: list[dict[str, Any]]) -> list[tuple[int, int, int, str]]:
    return [
        (t, r, c, value)
        for t, table in enumerate(tables)
        for r, row in enumerate(table["matrix"])
        for c, value in enumerate(row)
        if isinstance(value, str) and value
    ]


def repair(result: dict[str, Any], viewport: list[float]) -> dict[str, Any]:
    """Return strict canonical output plus explicit edits, or refuse atomically."""
    adapter = importlib.import_module("bench.pipeline_vision_transcription")
    adapter._viewport(viewport)
    if not isinstance(result, dict):
        raise ValueError("Response envelope must be an object")
    choices = result.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ValueError("Response must contain one complete choice")
    completion = choices[0]
    if completion.get("finish_reason") not in ("stop", "end_turn"):
        raise ValueError("Truncated or non-normal output is never repaired")
    message = completion.get("message")
    if not isinstance(message, dict) or message.get("refusal") or not isinstance(message.get("content"), str):
        raise ValueError("Refused or non-string output is never repaired")
    content = message["content"]
    if len(content) > adapter.MAX_CONTENT_BYTES or len(content.encode("utf-8")) > adapter.MAX_CONTENT_BYTES:
        raise ValueError("Response content admission exceeded")
    try:
        payload = json.loads(content, object_pairs_hook=adapter._unique_pairs, parse_constant=adapter._invalid_constant)
    except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
        raise ValueError("Malformed JSON is never repaired") from error
    answers = adapter._exact(payload, {"answers"})["answers"]
    answer = adapter._exact(answers, {"q0"})["q0"]
    tables = adapter._exact(answer, {"tables"})["tables"]
    if not isinstance(tables, list) or len(tables) > adapter.MAX_TABLES:
        raise ValueError("Table inventory admission exceeded")
    edits = []
    original_positions = []
    total_slots = 0
    for index, table in enumerate(tables):
        adapter._exact(table, {"bbox", "matrix", "mergedspans"})
        matrix = table["matrix"]
        if (
            not isinstance(matrix, list)
            or not matrix
            or len(matrix) > adapter.MAX_SLOTS
            or any(not isinstance(row, list) or not row for row in matrix)
        ):
            raise ValueError("Ambiguous empty or invalid row is never repaired")
        original_positions.extend(
            (index, r, c, value)
            for r, row in enumerate(matrix)
            for c, value in enumerate(row)
            if isinstance(value, str) and value
        )
        rows, columns = len(matrix), max(map(len, matrix))
        total_slots += rows * columns
        if rows * columns > adapter.MAX_SLOTS or total_slots > adapter.MAX_TOTAL_SLOTS:
            raise ValueError("Padded slot admission exceeded")
        raw_spans = table["mergedspans"]
        if not isinstance(raw_spans, list) or len(raw_spans) > rows * columns:
            raise ValueError("Invalid merged span inventory")
        occupied: set[tuple[int, int]] = set()
        covered: set[tuple[int, int]] = set()
        for span in raw_spans:
            if not isinstance(span, list) or len(span) != 4 or any(type(value) is not int for value in span):
                raise ValueError("Invalid merged span types")
            row, column, height, width = span
            if (
                min(row, column) < 0
                or min(height, width) < 1
                or row + height > rows
                or column + width > columns
                or height == width == 1
            ):
                raise ValueError("Invalid merged span bounds")
            if column >= len(matrix[row]):
                raise ValueError("A missing merged anchor is ambiguous")
            slots = {(r, c) for r in range(row, row + height) for c in range(column, column + width)}
            if slots & occupied:
                raise ValueError("Overlapping or duplicate merged spans")
            occupied.update(slots)
            covered.update(slots - {(row, column)})
        for row_index, row in enumerate(matrix):
            for column, value in enumerate(row):
                if value is None and (row_index, column) in covered:
                    row[column] = ""
                    edits.append(
                        {
                            "table": index,
                            "operation": "covered_null_to_blank",
                            "row": row_index,
                            "column": column,
                            "original": None,
                            "replacement": "",
                        }
                    )
                elif not isinstance(value, str):
                    raise ValueError("Ambiguous non-string cell is never repaired")
                elif value and (row_index, column) in covered:
                    raise ValueError("Repair cannot delete a nonempty covered value")
            for column in range(len(row), columns):
                edits.append(
                    {
                        "table": index,
                        "operation": "pad_trailing_blank",
                        "row": row_index,
                        "column": column,
                        "original": "missing slot",
                        "replacement": "",
                        "invented_blank_slot": True,
                        "covered_by_span": (row_index, column) in covered,
                    }
                )
                row.append("")
        original_bbox = list(adapter._viewport(table["bbox"]))
        clipped = [
            max(0, original_bbox[0]),
            max(0, original_bbox[1]),
            min(1000, original_bbox[2]),
            min(1000, original_bbox[3]),
        ]
        if clipped[0] >= clipped[2] or clipped[1] >= clipped[3]:
            raise ValueError("Geometry without positive page intersection is never repaired")
        if clipped != original_bbox:
            edits.append(
                {
                    "table": index,
                    "operation": "clip_normalized_bbox",
                    "original": original_bbox,
                    "replacement": clipped,
                    "geometry_clipped": True,
                    "units": "protocol normalized 0..1000",
                    "rescaled": False,
                }
            )
            table["bbox"] = clipped
    if original_positions != _literal_positions(tables):
        raise ValueError("Repair changed literal text ownership")
    rewritten = {**result, "choices": [{**completion, "message": {**message, "content": json.dumps(payload)}}]}
    parsed = adapter.parse(rewritten, viewport)
    return {
        "parsed": parsed,
        "edits": edits,
        "repaired": bool(edits),
        "provenance": {
            "version": VERSION,
            "counterfactual_postprocessing": True,
            "new_provider_request": False,
            "provider_cache_hit": False,
            "reference_guided": False,
            "literal_positions_preserved": True,
            "original_content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        },
    }
