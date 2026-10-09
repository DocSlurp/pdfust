"""Lossless source packets and byte-bounded batches for opt-in DEV decisions."""

# ruff: noqa: ANN401, PLR2004
from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from bench.lowlevel_geometry import POLICY, grouping

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

MAX_ROWS = 16384
FONT_FIELDS = ("font", "font_name", "font_flags")
FORMAT = "source-array-v1"


def encoded(value: Any) -> bytes:
    """Count the complete JSON body, including question instructions."""
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _table(rows: list[dict[str, Any]], *, fonts: bool) -> dict[str, Any]:
    if len(rows) > MAX_ROWS or any(not isinstance(row, dict) for row in rows):
        message = "Source table exceeds admission or has invalid rows"
        raise ValueError(message)
    fields = list(rows[0]) if rows else []
    if any(list(row) != fields for row in rows):
        message = "Source rows have inconsistent fields"
        raise ValueError(message)
    font_fields = [key for key in fields if fonts and key in FONT_FIELDS]
    shared: list[list[Any]] = []
    indexes: dict[bytes, int] = {}
    row_indexes = []
    for row in rows:
        values = [row[key] for key in font_fields]
        signature = encoded(values)
        if signature not in indexes:
            indexes[signature] = len(shared)
            shared.append(values)
        row_indexes.append(indexes[signature])
    ordinary = [key for key in fields if key not in font_fields]
    constants = {
        key: deepcopy(rows[0][key])
        for key in ordinary
        if rows and all(encoded(row[key]) == encoded(rows[0][key]) for row in rows)
    }
    columns = [key for key in ordinary if key not in constants]
    references: dict[str, list[Any]] = {}
    reference_indexes: dict[str, dict[bytes, int]] = {}
    if not fonts and "operands" in columns:
        references["operands"] = []
        reference_indexes["operands"] = {}
        for row in rows:
            signature = encoded(row["operands"])
            if signature not in reference_indexes["operands"]:
                reference_indexes["operands"][signature] = len(references["operands"])
                references["operands"].append(deepcopy(row["operands"]))
    return {
        "format": FORMAT,
        "fields": fields,
        "columns": columns,
        "constants": constants,
        "font_fields": font_fields,
        "fonts": deepcopy(shared),
        "font_index_column": len(columns) if font_fields else None,
        "references": references,
        "rows": [
            [reference_indexes[key][encoded(row[key])] if key in references else deepcopy(row[key]) for key in columns]
            + ([font_index] if font_fields else [])
            for row, font_index in zip(rows, row_indexes, strict=True)
        ],
    }


def compact(projected_state: dict[str, Any]) -> dict[str, Any]:
    """Replace repeated source dictionary keys; preserve every value and order.

    No new quantization, glyph omission or source-order normalization occurs.
    Operator operands remain literal nested source values in their array column.
    """
    result = deepcopy(projected_state)
    for key in ("glyphs", "text_operators"):
        if key in result:
            if not isinstance(result[key], list):
                message = "Expected original source row dictionaries"
                raise ValueError(message)
            result[key] = _table(result[key], fonts=key == "glyphs")
    return result


def expand(packet: dict[str, Any]) -> dict[str, Any]:  # noqa: C901 - validate each source reference before reconstruction.
    """Restore original source dictionaries for exact round-trip verification."""
    result = deepcopy(packet)
    for key in ("glyphs", "text_operators"):
        if key not in result:
            continue
        table = result[key]
        if not isinstance(table, dict) or table.get("format") != FORMAT or len(table["rows"]) > MAX_ROWS:
            message = "Expected a bounded compact source table"
            raise ValueError(message)
        output = []
        for values in table["rows"]:
            columns, font_fields = table["columns"], table["font_fields"]
            if len(values) != len(columns) + bool(font_fields):
                message = "Compact source row has invalid arity"
                raise ValueError(message)
            row = deepcopy(table["constants"])
            for column, value in zip(columns, values[: len(columns)], strict=True):
                if column in table["references"]:
                    referenced = table["references"][column]
                    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < len(referenced):
                        message = "Compact source reference index is invalid"
                        raise ValueError(message)
                    row[column] = deepcopy(referenced[value])
                else:
                    row[column] = deepcopy(value)
            if font_fields:
                index = values[-1]
                if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(table["fonts"]):
                    message = "Compact source font index is invalid"
                    raise ValueError(message)
                row.update(zip(font_fields, table["fonts"][index], strict=True))
            if set(row) != set(table["fields"]):
                message = "Compact source fields differ from declared inventory"
                raise ValueError(message)
            output.append({field: deepcopy(row[field]) for field in table["fields"]})
        result[key] = output
    return result


def relation_hint(projected_state: dict[str, Any]) -> dict[str, Any]:
    """Add a separately labeled geometry policy result, never an expected label.

    Caller must retain source drawings. Lack of vector evidence means unresolved,
    not evidence that a divider was absent from the source page.
    """
    result = deepcopy(projected_state)
    hint = "unresolved"
    if "vector_marks" in projected_state:
        hint = grouping(projected_state["vector_marks"], projected_state["target_boxes"], task=projected_state["task"])
    result["source_geometry_hint"] = {
        "policy": POLICY,
        "choice": hint,
        "limitations": (
            "Deterministic DEV geometry heuristic; loose selector centers; "
            "no clip-resolved visibility; not model confidence or author semantics"
        ),
    }
    return result


def adaptive_requests(
    observations: Sequence[dict[str, Any]],
    builder: Callable[[list[dict[str, Any]]], dict[str, Any]],
    *,
    max_bytes: int = 32000,
    max_batch: int = 3,
) -> list[dict[str, Any]]:
    """Build largest consecutive batches below a conservative body-byte cap.

    Builder is a pure preparation function, not a provider client. A source that
    cannot fit alone refuses atomically. Bytes are not measured provider tokens.
    """
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        message = "Byte budget must be a positive integer"
        raise ValueError(message)
    if isinstance(max_batch, bool) or not isinstance(max_batch, int) or not 1 <= max_batch <= 3:
        message = "Batch budget must be between one and three"
        raise ValueError(message)
    if len(observations) > 4096:
        message = "Observation inventory exceeds admission"
        raise ValueError(message)
    output = []
    offset = 0
    while offset < len(observations):
        for count in range(min(max_batch, len(observations) - offset), 0, -1):
            body = builder(list(observations[offset : offset + count]))
            size = len(encoded(body))
            if size <= max_bytes:
                output.append({"start": offset, "stop": offset + count, "utf8_bytes": size, "body": body})
                offset += count
                break
        else:
            message = "Source singleton exceeds byte budget; no truncation permitted"
            raise ValueError(message)
    return output
