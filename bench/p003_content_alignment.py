"""Bounded table content alignment; independent of source geometry and strict scoring."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLR2004, ANN401, N818
VERSION = "p003-content-alignment-v2"
LIMITS = {
    "rows": 128,
    "columns": 24,
    "slots": 2048,
    "characters": 16384,
    "cell_characters": 1024,
    "edit_work": 8000000,
    "adjacent_group": 2,
}


class Unsupported(ValueError):
    """An explicit resource/schema refusal, never a zero-quality verdict."""


def _coverage(value: Any) -> dict[str, Any]:
    """Retain bounded declared coverage even when merged topology is unsupported."""
    if isinstance(value, dict):
        rows, cols = value.get("row_count"), value.get("col_count")
        spans = value.get("spans", [])
    else:
        rows = len(value) if isinstance(value, list) else None
        cols = len(value[0]) if rows and isinstance(value[0], list) else None
        spans = []
    merged = None
    if isinstance(spans, list) and len(spans) <= LIMITS["slots"]:
        merged = sum(isinstance(s, dict) and (s.get("row_span") != 1 or s.get("column_span") != 1) for s in spans)
    return {
        "declared_rows": rows if type(rows) is int else None,
        "declared_columns": cols if type(cols) is int else None,
        "declared_slots": rows * cols if type(rows) is int and type(cols) is int else None,
        "non_unit_span_records": merged,
    }


def _table(value: Any) -> list[list[str]]:
    if isinstance(value, dict):
        rows, columns = value.get("row_count"), value.get("col_count")
        matrix, spans = value.get("values"), value.get("spans", [])
        if type(rows) is not int or type(columns) is not int:
            raise Unsupported("Canonical integer row_count and col_count required")
        if not isinstance(spans, list) or len(spans) > LIMITS["slots"]:
            raise Unsupported("Explicit span list required")
        for span in spans:
            if not isinstance(span, dict):
                raise Unsupported("Invalid span record")
            if span.get("row_span") != 1 or span.get("column_span") != 1:
                raise Unsupported("Merged or non-unit spans are unsupported in version 1")
            if any(type(span.get(k)) is not int for k in ("row", "column", "row_span", "column_span")):
                raise Unsupported("Invalid span coordinates")
            if not (0 <= span["row"] < rows and 0 <= span["column"] < columns):
                raise Unsupported("Span outside table")
        if len({(s["row"], s["column"]) for s in spans}) != len(spans):
            raise Unsupported("Duplicate span anchor")
    else:
        matrix = value
        rows = len(matrix) if isinstance(matrix, list) else 0
        columns = len(matrix[0]) if rows and isinstance(matrix[0], list) else 0
    if not isinstance(matrix, list) or not 1 <= rows <= LIMITS["rows"] or not 1 <= columns <= LIMITS["columns"]:
        raise Unsupported("Invalid or over-limit table dimensions")
    if rows * columns > LIMITS["slots"] or len(matrix) != rows:
        raise Unsupported("Invalid or over-limit table slots")
    result = []
    for row in matrix:
        if not isinstance(row, list) or len(row) != columns or any(not isinstance(v, str) for v in row):
            raise Unsupported("Rectangular literal string matrix required; covered None slots unsupported")
        if any(len(v) > LIMITS["cell_characters"] for v in row):
            raise Unsupported("Raw cell character limit exceeded")
        normalized = [" ".join(unicodedata.normalize("NFC", v).split()) for v in row]
        if any(len(v) > LIMITS["cell_characters"] for v in normalized):
            raise Unsupported("Cell character limit exceeded")
        result.append(normalized)
    if sum(len(v) for row in result for v in row) > LIMITS["characters"]:
        raise Unsupported("Table character limit exceeded")
    return result


def _join(values: list[str]) -> str:
    # A single visible boundary is added between nonempty adjacent cells. Internal
    # numeric/date/currency spacing and punctuation are retained, never stripped.
    return " ".join(v for v in values if v)


class Edits:
    """Bound cumulative dynamic-programming work, including repeated row comparisons."""

    def __init__(self) -> None:
        """Start one comparison budget and bounded text-pair cache."""
        self.work = 0
        self.cache: dict[tuple[str, str], dict[str, Any]] = {}

    def charge(self, work: int) -> None:
        """Refuse before allocating or executing an over-limit edit matrix."""
        self.work += work
        if self.work > LIMITS["edit_work"]:
            raise Unsupported("Cumulative edit-work limit exceeded")

    def text(self, a: str, b: str, *, witness: bool = False) -> dict[str, Any]:
        """Count exact, substituted, missing and extra characters with optional traceback."""
        key = (a, b)
        if not witness and key in self.cache:
            return self.cache[key]
        self.charge((len(a) + 1) * (len(b) + 1))
        # Tuple fields are cost, negative exact matches, substitutions, deletions,
        # insertions. Tie breaks maximize retained content, then prefer fewer edits.
        prior = [(j, 0, 0, 0, j) for j in range(len(b) + 1)]
        directions = bytearray((len(a) + 1) * (len(b) + 1)) if witness else None
        width = len(b) + 1
        for i, left in enumerate(a, 1):
            current = [(i, 0, 0, i, 0)]
            for j, right in enumerate(b, 1):
                diagonal = prior[j - 1]
                if left == right:
                    diagonal = (diagonal[0], diagonal[1] - 1, *diagonal[2:])
                else:
                    diagonal = (diagonal[0] + 1, diagonal[1], diagonal[2] + 1, diagonal[3], diagonal[4])
                deleted = prior[j]
                deleted = (deleted[0] + 1, deleted[1], deleted[2], deleted[3] + 1, deleted[4])
                inserted = current[j - 1]
                inserted = (inserted[0] + 1, inserted[1], inserted[2], inserted[3], inserted[4] + 1)
                best, operation = min((diagonal, 0), (deleted, 1), (inserted, 2))
                current.append(best)
                if directions is not None:
                    directions[i * width + j] = operation
            prior = current
        cost, negative_matches, substituted, missing, extra = prior[-1]
        result: dict[str, Any] = {
            "edit_cost": cost,
            "matched": -negative_matches,
            "substituted": substituted,
            "missing": missing,
            "extra": extra,
            "reference_units": len(a),
            "prediction_units": len(b),
        }
        if directions is not None:
            i, j = len(a), len(b)
            operations: list[dict[str, Any]] = []
            while i or j:
                operation = 1 if j == 0 else 2 if i == 0 else directions[i * width + j]
                if operation == 0:
                    operations.append(
                        {
                            "operation": "equal" if a[i - 1] == b[j - 1] else "substitute",
                            "reference_index": i - 1,
                            "prediction_index": j - 1,
                        }
                    )
                    i, j = i - 1, j - 1
                elif operation == 1:
                    operations.append({"operation": "missing", "reference_index": i - 1, "prediction_index": None})
                    i -= 1
                else:
                    operations.append({"operation": "extra", "reference_index": None, "prediction_index": j - 1})
                    j -= 1
            result["character_witness"] = list(reversed(operations))
        else:
            self.cache[key] = result
        return result


def _align(rows: int, columns: int, cost: Any, ref_gap: Any, pred_gap: Any) -> list[tuple[int | None, int | None]]:
    """One-to-one monotone row alignment; no row fragments can be borrowed elsewhere."""
    prior = [0]
    for j in range(columns):
        prior.append(prior[-1] + pred_gap(j))
    directions = bytearray((rows + 1) * (columns + 1))
    width = columns + 1
    for i in range(1, rows + 1):
        current = [prior[0] + ref_gap(i - 1)]
        for j in range(1, columns + 1):
            best, operation = min(
                (prior[j - 1] + cost(i - 1, j - 1), 0),
                (prior[j] + ref_gap(i - 1), 1),
                (current[j - 1] + pred_gap(j - 1), 2),
            )
            current.append(best)
            directions[i * width + j] = operation
        prior = current
    i, j = rows, columns
    pairs: list[tuple[int | None, int | None]] = []
    while i or j:
        op = 1 if j == 0 else 2 if i == 0 else directions[i * width + j]
        if op == 0:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif op == 1:
            pairs.append((i - 1, None))
            i -= 1
        else:
            pairs.append((None, j - 1))
            j -= 1
    return list(reversed(pairs))


def _token_cost(a: list[str], b: list[str], edits: Edits) -> int:
    edits.charge((len(a) + 1) * (len(b) + 1))
    prior = list(range(len(b) + 1))
    for i, token in enumerate(a, 1):
        current = [i]
        for j, other in enumerate(b, 1):
            current.append(min(prior[j - 1] + (token != other), prior[j] + 1, current[-1] + 1))
        prior = current
    return prior[-1]


def _columns(
    ref: list[list[str]], pred: list[list[str]], pairs: list[tuple[int | None, int | None]], edits: Edits
) -> list[tuple[int, int, int, int]]:
    """Select one shared monotone column path across every initially matched row."""
    matched = [(a, b) for a, b in pairs if a is not None and b is not None]
    if not matched:
        raise Unsupported("No initial row correspondence; shared column path unavailable")
    n, m = len(ref[0]), len(pred[0])
    states: dict[tuple[int, int], tuple[tuple[int, int, int], list[tuple[int, int, int, int]]]] = {
        (0, 0): ((0, 0, 0), [])
    }
    for i in range(n + 1):
        for j in range(m + 1):
            if (i, j) not in states:
                continue
            previous, path = states[i, j]
            for left, right in ((1, 1), (1, 2), (2, 1), (1, 0), (0, 1)):
                if i + left > n or j + right > m:
                    continue
                loss = sum(
                    edits.text(_join(ref[a][i : i + left]), _join(pred[b][j : j + right]))["edit_cost"]
                    for a, b in matched
                )
                score = (previous[0] + loss, previous[1] + (left + right > 2), previous[2] + (left == 0 or right == 0))
                target = (i + left, j + right)
                if target not in states or score < states[target][0]:
                    states[target] = (score, [*path, (i, i + left, j, j + right)])
    return states[n, m][1]


def _compare_oriented(reference: Any, prediction: Any) -> dict[str, Any]:
    """Return separately versioned content precision/recall and auditable monotone witnesses."""
    base: dict[str, Any] = {
        "version": VERSION,
        "limits": dict(LIMITS),
        "algorithm": "Two-pass heuristic: lexical row alignment, shared column path, final row alignment",
        "normalization": "NFC and whitespace runs to one space; case/punctuation/numeric boundaries retained",
        "schema_correctness": None,
        "header_label_acceptance": "Separate source-aware metric required",
        "input_coverage": {"reference": _coverage(reference), "prediction": _coverage(prediction)},
    }
    edits = Edits()
    try:
        ref, pred = _table(reference), _table(prediction)
        ref_tokens = [re.findall(r"\w+|[^\w\s]", _join(row)) for row in ref]
        pred_tokens = [re.findall(r"\w+|[^\w\s]", _join(row)) for row in pred]
        initial = _align(
            len(ref),
            len(pred),
            lambda i, j: _token_cost(ref_tokens[i], pred_tokens[j], edits),
            lambda i: len(ref_tokens[i]) + 1,
            lambda j: len(pred_tokens[j]) + 1,
        )
        path = _columns(ref, pred, initial, edits)

        def loss(i: int, j: int) -> int:
            return sum(edits.text(_join(ref[i][a:b]), _join(pred[j][c:d]))["edit_cost"] for a, b, c, d in path)

        pairs = _align(
            len(ref),
            len(pred),
            loss,
            lambda i: sum(len(v) for v in ref[i]) + 1,
            lambda j: sum(len(v) for v in pred[j]) + 1,
        )
        totals = dict.fromkeys(("matched", "substituted", "missing", "extra", "reference_units", "prediction_units"), 0)
        witness = []
        blank_gaps = 0
        for i, j in pairs:
            cells = []
            groups = path if i is not None and j is not None else [(0, len(ref[0]), 0, len(pred[0]))]
            for a, b, c, d in groups:
                left = _join(ref[i][a:b]) if i is not None else ""
                right = _join(pred[j][c:d]) if j is not None else ""
                receipt = edits.text(left, right, witness=True)
                for key in totals:
                    totals[key] += receipt[key]
                if i is not None and j is not None and ((a == b or c == d) and not left and not right):
                    blank_gaps += 1
                cells.append(
                    {
                        "reference_columns": [a, b] if i is not None else None,
                        "prediction_columns": [c, d] if j is not None else None,
                        "reference_text": left,
                        "prediction_text": right,
                        "join_provenance": {
                            "reference_cells": b - a,
                            "prediction_cells": d - c,
                            "separator": "one space between nonempty literals",
                        },
                        **receipt,
                    }
                )
            witness.append({"reference_row": i, "prediction_row": j, "cells": cells})
        denominator_p, denominator_r = totals["prediction_units"], totals["reference_units"]
        content_complete = not any(totals[k] for k in ("substituted", "missing", "extra"))
        rows_preserved = all(i is not None and j is not None for i, j in pairs)
        return {
            **base,
            "supported": True,
            "unsupported_reason": None,
            "counts": totals,
            "precision": totals["matched"] / denominator_p if denominator_p else (1.0 if not denominator_r else 0.0),
            "recall": totals["matched"] / denominator_r if denominator_r else (1.0 if not denominator_p else 0.0),
            "content_recovered_with_row_order": content_complete and rows_preserved,
            "row_sequence_preserved": rows_preserved,
            "blank_cell_gap_count": blank_gaps,
            "blank_rows_preserved": rows_preserved,
            "shared_column_path": [{"reference_columns": [a, b], "prediction_columns": [c, d]} for a, b, c, d in path],
            "row_alignment": witness,
            "edit_work": edits.work,
            "unit": "Normalized Unicode characters including retained spaces and declared join separators",
            "coverage": {
                "reference_rows": len(ref),
                "prediction_rows": len(pred),
                "reference_cells": sum(map(len, ref)),
                "prediction_cells": sum(map(len, pred)),
                "reference_literal_characters": sum(len(v) for row in ref for v in row),
                "prediction_literal_characters": sum(len(v) for row in pred for v in row),
                "reference_join_separator_units": totals["reference_units"] - sum(len(v) for row in ref for v in row),
                "prediction_join_separator_units": totals["prediction_units"]
                - sum(len(v) for row in pred for v in row),
            },
        }
    except Unsupported as error:
        return {
            **base,
            "supported": False,
            "unsupported_reason": str(error),
            "counts": None,
            "precision": None,
            "recall": None,
            "content_recovered_with_row_order": None,
            "edit_work": edits.work,
        }


def _transpose_counts(counts: dict[str, Any]) -> dict[str, Any]:
    return {
        **counts,
        "missing": counts["extra"],
        "extra": counts["missing"],
        "reference_units": counts["prediction_units"],
        "prediction_units": counts["reference_units"],
    }


def _transpose(result: dict[str, Any]) -> dict[str, Any]:
    """Map all directional content evidence back to caller roles."""
    if not result["supported"]:
        return result
    result["counts"] = _transpose_counts(result["counts"])
    result["precision"], result["recall"] = result["recall"], result["precision"]
    coverage = result["coverage"]
    result["coverage"] = {
        (
            "prediction_" + key.removeprefix("reference_")
            if key.startswith("reference_")
            else "reference_" + key.removeprefix("prediction_")
        ): value
        for key, value in coverage.items()
    }
    for step in result["shared_column_path"]:
        step["reference_columns"], step["prediction_columns"] = step["prediction_columns"], step["reference_columns"]
    for row in result["row_alignment"]:
        row["reference_row"], row["prediction_row"] = row["prediction_row"], row["reference_row"]
        for cell in row["cells"]:
            for suffix in ("columns", "text"):
                a, b = "reference_" + suffix, "prediction_" + suffix
                cell[a], cell[b] = cell[b], cell[a]
            counts = _transpose_counts(cell)
            for key in ("missing", "extra", "reference_units", "prediction_units"):
                cell[key] = counts[key]
            provenance = cell["join_provenance"]
            provenance["reference_cells"], provenance["prediction_cells"] = (
                provenance["prediction_cells"],
                provenance["reference_cells"],
            )
            for operation in cell["character_witness"]:
                operation["reference_index"], operation["prediction_index"] = (
                    operation["prediction_index"],
                    operation["reference_index"],
                )
                if operation["operation"] in ("missing", "extra"):
                    operation["operation"] = "extra" if operation["operation"] == "missing" else "missing"
    return result


def compare_content(reference: Any, prediction: Any) -> dict[str, Any]:
    """Align in a preselected canonical orientation, then restore caller reference/prediction roles."""
    try:
        # Validate the original span/value contracts before discarding structural
        # wrappers. A genuine merge must never become an unmerged matrix silently.
        ref, pred = _table(reference), _table(prediction)
    except Unsupported:
        return _compare_oriented(reference, prediction)
    reverse = tuple(map(tuple, pred)) < tuple(map(tuple, ref))
    result = _compare_oriented(pred, ref) if reverse else _compare_oriented(ref, pred)
    if reverse:
        result = _transpose(result)
    result["input_coverage"] = {"reference": _coverage(reference), "prediction": _coverage(prediction)}
    result["orientation_policy"] = (
        "Lexicographically ordered tuples of NFC/whitespace-normalized literal rows; selected before alignment"
    )
    result["caller_reference_was_internal_first"] = not reverse
    return result
