"""Bounded wrap-aware content recovery; independent of row-schema correctness."""

from __future__ import annotations

from typing import Any

from bench.p003_content_alignment import LIMITS as BASE_LIMITS
from bench.p003_content_alignment import Edits, Unsupported, _coverage, _join, _table

# ruff: noqa: ANN401, EM101, TRY003, TRY300
VERSION = "p003-wrap-content-v1"
LIMITS = {key: value for key, value in BASE_LIMITS.items() if key != "adjacent_group"}
LIMITS["adjacent_rows"] = 3
COUNT_KEYS = ("matched", "substituted", "missing", "extra", "reference_units", "prediction_units")


class WrapEdits(Edits):
    """Use the independently declared wrap-comparison work budget."""

    def charge(self, work: int) -> None:
        """Refuse the whole result when its cumulative work budget is exhausted."""
        self.work += work
        if self.work > LIMITS["edit_work"]:
            raise Unsupported("Cumulative edit-work limit exceeded")


def _prepare(value: Any) -> dict[str, Any]:
    matrix = _table(value)
    rows = [i for i, row in enumerate(matrix) if any(row)]
    columns = [j for j in range(len(matrix[0])) if any(row[j] for row in matrix)]
    return {
        "matrix": [[matrix[i][j] for j in columns] for i in rows],
        "row_map": rows,
        "column_map": columns,
        "blank_inventory": {
            "rows": [i for i, row in enumerate(matrix) if not any(row)],
            "columns": [j for j in range(len(matrix[0])) if j not in columns],
            "cells": [[i, j] for i, row in enumerate(matrix) for j, text in enumerate(row) if not text],
        },
        "literal_characters": sum(len(text) for row in matrix for text in row),
    }


def _texts(table: dict[str, Any], start: int, size: int) -> list[str]:
    return [_join([row[j] for row in table["matrix"][start : start + size]]) for j in range(len(table["column_map"]))]


def _wrap_allowed(a: dict[str, Any], b: dict[str, Any], i: int, j: int, left: int, right: int) -> bool:  # noqa: PLR0913, PLR0917
    """Admit only exact joins with one unambiguous anchor inside this block."""
    multi, start, size = (a, i, left) if left > 1 else (b, j, right)
    original = multi["row_map"][start : start + size]
    if original != list(range(original[0], original[0] + size)):
        return False
    joined = _texts(a, i, left)
    if joined != _texts(b, j, right):
        return False
    return any(
        sum(bool(row[column]) for row in a["matrix"][i : i + left]) == 1
        and sum(bool(row[column]) for row in b["matrix"][j : j + right]) == 1
        and bool(joined[column])
        for column in range(len(a["column_map"]))
    )


def _align(a: dict[str, Any], b: dict[str, Any], edits: WrapEdits) -> list[tuple[int, int, int, int]]:
    n, m = len(a["matrix"]), len(b["matrix"])
    # Each transition consumes its literal rows exactly once; gaps cannot reuse
    # fragments. Score ties prefer retained characters, then fewer gaps/wraps.
    states: dict[tuple[int, int], tuple[int, int, int, int]] = {(0, 0): (0, 0, 0, 0)}
    previous: dict[tuple[int, int], tuple[int, int, int, int]] = {}
    for i in range(n + 1):
        for j in range(m + 1):
            score = states[i, j]
            for left, right in ((1, 1), (1, 0), (0, 1), (1, 2), (2, 1), (1, 3), (3, 1)):
                if max(left, right) > LIMITS["adjacent_rows"] or i + left > n or j + right > m:
                    continue
                if max(left, right) > 1 and not _wrap_allowed(a, b, i, j, left, right):
                    continue
                lhs, rhs = _texts(a, i, left), _texts(b, j, right)
                receipts = [edits.text(x, y) for x, y in zip(lhs, rhs, strict=True)]
                next_score = (
                    score[0] + sum(r["edit_cost"] for r in receipts),
                    score[1] - sum(r["matched"] for r in receipts),
                    score[2] + (left == 0 or right == 0),
                    score[3] + (max(left, right) > 1),
                )
                target = (i + left, j + right)
                if target not in states or next_score < states[target]:
                    states[target] = next_score
                    previous[target] = (i, j, left, right)
    path = []
    position = (n, m)
    while position != (0, 0):
        step = previous[position]
        path.append(step)
        position = step[:2]
    return list(reversed(path))


def _compare(a: dict[str, Any], b: dict[str, Any], edits: WrapEdits) -> dict[str, Any]:
    if len(a["column_map"]) != len(b["column_map"]):
        raise Unsupported("Unequal nonblank column counts are unsupported")
    totals = dict.fromkeys(COUNT_KEYS, 0)
    witness = []
    for i, j, left, right in _align(a, b, edits):
        cells = []
        for column, (x, y) in enumerate(zip(_texts(a, i, left), _texts(b, j, right), strict=True)):
            receipt = edits.text(x, y, witness=True)
            for key in totals:
                totals[key] += receipt[key]
            cells.append(
                {
                    "reference_columns": [a["column_map"][column]] if left else [],
                    "prediction_columns": [b["column_map"][column]] if right else [],
                    "reference_text": x,
                    "prediction_text": y,
                    "join_provenance": {
                        "reference_cells": left,
                        "prediction_cells": right,
                        "separator": "one space between nonempty literals",
                    },
                    **receipt,
                }
            )
        witness.append(
            {
                "reference_rows": a["row_map"][i : i + left],
                "prediction_rows": b["row_map"][j : j + right],
                "kind": "wrap" if max(left, right) > 1 else "paired" if left and right else "gap",
                "cells": cells,
            }
        )
    p, r = totals["prediction_units"], totals["reference_units"]
    complete = not any(totals[key] for key in ("substituted", "missing", "extra"))
    return {
        "supported": True,
        "unsupported_reason": None,
        "counts": totals,
        "precision": totals["matched"] / p if p else float(not r),
        "recall": totals["matched"] / r if r else float(not p),
        "content_recovered_with_row_order": complete,
        "row_alignment": witness,
        "coverage": {
            "reference_literal_characters": a["literal_characters"],
            "prediction_literal_characters": b["literal_characters"],
            "reference_join_separator_units": r - a["literal_characters"],
            "prediction_join_separator_units": p - b["literal_characters"],
        },
    }


def _transpose(result: dict[str, Any]) -> None:
    for counts in [result["counts"], *(cell for row in result["row_alignment"] for cell in row["cells"])]:
        counts["missing"], counts["extra"] = counts["extra"], counts["missing"]
        counts["reference_units"], counts["prediction_units"] = counts["prediction_units"], counts["reference_units"]
    result["precision"], result["recall"] = result["recall"], result["precision"]
    for row in result["row_alignment"]:
        row["reference_rows"], row["prediction_rows"] = row["prediction_rows"], row["reference_rows"]
        for cell in row["cells"]:
            for suffix in ("columns", "text"):
                cell["reference_" + suffix], cell["prediction_" + suffix] = (
                    cell["prediction_" + suffix],
                    cell["reference_" + suffix],
                )
            provenance = cell["join_provenance"]
            provenance["reference_cells"], provenance["prediction_cells"] = (
                provenance["prediction_cells"],
                provenance["reference_cells"],
            )
            for op in cell["character_witness"]:
                op["reference_index"], op["prediction_index"] = op["prediction_index"], op["reference_index"]
                if op["operation"] in ("missing", "extra"):
                    op["operation"] = "extra" if op["operation"] == "missing" else "missing"
    coverage = result["coverage"]
    for suffix in ("literal_characters", "join_separator_units"):
        coverage["reference_" + suffix], coverage["prediction_" + suffix] = (
            coverage["prediction_" + suffix],
            coverage["reference_" + suffix],
        )


def compare_wrap_content(reference: Any, prediction: Any) -> dict[str, Any]:
    """Measure ordered content recovery with exact anchored continuation joins.

    This metric cannot establish semantic row identity, header relationships, or
    schema correctness. Entirely blank rows/columns are inventoried but unscored.
    """
    edits = WrapEdits()
    base = {
        "version": VERSION,
        "limits": dict(LIMITS),
        "normalization": "NFC and whitespace runs to one space; case/punctuation/numeric boundaries retained",
        "algorithm": "Monotone per-column character alignment with exact anchored 1:N/N:1 wraps up to three rows",
        "orientation_policy": "Lexicographic normalized nonblank matrices; chosen before alignment",
        "schema_correctness": None,
        "unit": "Normalized Unicode characters including retained spaces and declared wrap join separators",
        "input_coverage": {"reference": _coverage(reference), "prediction": _coverage(prediction)},
    }
    try:
        a, b = _prepare(reference), _prepare(prediction)
        base["coordinate_maps"] = {
            "reference": {k: a[k] for k in ("row_map", "column_map")},
            "prediction": {k: b[k] for k in ("row_map", "column_map")},
        }
        base["blank_inventory"] = {"reference": a["blank_inventory"], "prediction": b["blank_inventory"]}
        reverse = tuple(map(tuple, b["matrix"])) < tuple(map(tuple, a["matrix"]))
        result = _compare(b, a, edits) if reverse else _compare(a, b, edits)
        if reverse:
            _transpose(result)
        return {**base, **result, "edit_work": edits.work, "caller_reference_was_internal_first": not reverse}
    except Unsupported as error:
        return {
            **base,
            "supported": False,
            "unsupported_reason": str(error),
            "counts": None,
            "precision": None,
            "recall": None,
            "content_recovered_with_row_order": None,
            "row_alignment": None,
            "edit_work": edits.work,
        }
