"""Private complete-table evaluation; source conservation is a separate diagnostic."""

# Artifact dictionaries carry heterogeneous retained observations.
# ruff: noqa: PLR2004, EM101, TRY003, C901, PLR0912, TRY301
from __future__ import annotations

from collections import Counter
from typing import Any


def _value(value: str | None) -> str | None:
    return " ".join(value.split()) if value is not None else None


def _slots(table: dict[str, Any]) -> list[str | None]:
    rows, cols = table["row_count"], table["col_count"]
    values = table["values"]
    if type(rows) is not int or type(cols) is not int or not 1 <= rows * cols <= 4096:
        raise ValueError("Invalid table dimensions")
    if rows < 1 or cols < 1 or len(values) != rows or any(len(row) != cols for row in values):
        raise ValueError("Table values do not match declared dimensions")
    if any(value is not None and not isinstance(value, str) for row in values for value in row):
        raise ValueError("Invalid cell value")
    return [_value(value) for row in values for value in row]


def _spans(table: dict[str, Any]) -> list[tuple[int, int, int, int]]:
    result = []
    for span in table.get("spans", []):
        values = (span["row"], span["column"], span["row_span"], span["column_span"])
        if any(type(value) is not int for value in values):
            raise ValueError("Span coordinates must be integers")
        row, col, rows, cols = values
        if min(row, col) < 0 or min(rows, cols) < 1:
            raise ValueError("Invalid span coordinates")
        if row + rows > table["row_count"] or col + cols > table["col_count"]:
            raise ValueError("Span extends outside the declared table")
        result.append(values)
    return sorted(result)


def _assignment(weights: list[list[int]]) -> list[tuple[int, int]]:
    """Maximum-weight one-to-one assignment using square Hungarian potentials."""
    rows, cols = len(weights), len(weights[0]) if weights else 0
    size = max(rows, cols)
    if not size:
        return []
    u: list[float] = [0] * (size + 1)
    v: list[float] = [0] * (size + 1)
    p, way = [0] * (size + 1), [0] * (size + 1)
    for i in range(1, size + 1):
        p[0], j0 = i, 0
        minimum, used = [float("inf")] * (size + 1), [False] * (size + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], float("inf"), 0
            for j in range(1, size + 1):
                if not used[j]:
                    weight = weights[i0 - 1][j - 1] if i0 <= rows and j <= cols else 0
                    cost = -weight - u[i0] - v[j]
                    if cost < minimum[j]:
                        minimum[j], way[j] = cost, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(size + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    return [
        (p[j] - 1, j - 1)
        for j in range(1, size + 1)
        if 1 <= p[j] <= rows and j <= cols and weights[p[j] - 1][j - 1] > 0
    ]


def score_page(target: dict[str, Any], observed: list[dict[str, Any]], *, status: str = "ok") -> dict[str, Any]:
    """Charge missing/extra tables and errors, matching complete matrices one-to-one.

    Cell recall denominator includes every expected slot. A separate penalized
    denominator also charges slots of unmatched predicted tables. No absent
    predicted cell can earn credit for an expected covered None slot.
    """
    if not target.get("structural_scored", True):
        return {"structural_scored": False, "error": status != "ok"}
    gold = target["tables"]
    expected = [_slots(table) for table in gold]
    malformed = False
    try:
        actual = [_slots(table) for table in observed] if status == "ok" else []
        if len(actual) > 256:
            raise ValueError("Too many returned tables")
        # Missing span keys and invalid types invalidate complete structural output.
        for table in observed if status == "ok" else []:
            _spans(table)
    except (KeyError, TypeError, ValueError):
        malformed = True
        actual = []
    successful = status == "ok" and not malformed
    predicted = observed if successful else []
    weights = []
    priority = 1 + sum(map(len, expected)) + len(gold)
    for index, table in enumerate(gold):
        row = []
        for other_index, other in enumerate(predicted):
            shape = (table["row_count"], table["col_count"]) == (other["row_count"], other["col_count"])
            correct = sum(a == b for a, b in zip(expected[index], actual[other_index], strict=False)) if shape else 0
            exact = shape and expected[index] == actual[other_index] and _spans(table) == _spans(other)
            row.append(int(shape) + correct + int(exact) * priority)
        weights.append(row)
    pairs = _assignment(weights)
    matched_predictions = {j for _, j in pairs}
    correct_cells, exact_cells, exact_spans, complete = 0, 0, 0, 0
    for i, j in pairs:
        shape = (gold[i]["row_count"], gold[i]["col_count"]) == (predicted[j]["row_count"], predicted[j]["col_count"])
        cells = shape and expected[i] == actual[j]
        spans = shape and _spans(gold[i]) == _spans(predicted[j])
        correct_cells += sum(a == b for a, b in zip(expected[i], actual[j], strict=False)) if shape else 0
        exact_cells += int(cells)
        exact_spans += int(spans)
        complete += int(cells and spans)
    extras = len(predicted) - len(matched_predictions)
    slots = sum(map(len, expected))
    return {
        "structural_scored": True,
        "error": not successful,
        "malformed": malformed,
        "expected_tables": len(gold),
        "detected_tables": len(predicted),
        "matched_tables": len(pairs),
        "missing_tables": len(gold) - len(pairs),
        "false_positive_tables": extras,
        "false_positive_page": bool(not gold and predicted),
        "negative_page": not gold,
        "positive_page": bool(gold),
        "exact_page": successful and complete == len(gold) and extras == 0,
        "complete_tables": complete,
        "exact_table_cells": exact_cells,
        "exact_table_spans": exact_spans,
        "correct_cell_slots": correct_cells,
        "cell_slots": slots,
        "penalized_cell_slots": slots + sum(len(actual[j]) for j in range(len(actual)) if j not in matched_predictions),
        "table_denominator": len(gold) + extras,
    }


def score_dataset(targets: list[dict[str, Any]] | dict[str, Any], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep every expected page in denominators, including absent/error outputs."""
    pages = targets["pages"] if isinstance(targets, dict) else targets
    prediction_map = {}
    for prediction in predictions:
        if prediction["id"] in prediction_map:
            raise ValueError("Duplicate predicted page ID")
        prediction_map[prediction["id"]] = prediction
    target_ids = [page["id"] for page in pages]
    if len(target_ids) != len(set(target_ids)):
        raise ValueError("Duplicate reference page ID")
    unknown = set(prediction_map) - set(target_ids)
    if unknown:
        raise ValueError("Predicted page IDs are outside the frozen manifest")
    scores = []
    for page in pages:
        prediction = prediction_map.get(page["id"], {})
        observed = prediction.get("tables", prediction.get("observed", []))
        scores.append({"id": page["id"], **score_page(page, observed, status=prediction.get("status", "missing"))})
    scored = [row for row in scores if row["structural_scored"]]
    totals = {"pages": len(pages), "scored_pages": len(scored), "diagnostic_pages": len(pages) - len(scored)}
    for key in (
        "error",
        "malformed",
        "expected_tables",
        "detected_tables",
        "matched_tables",
        "missing_tables",
        "false_positive_tables",
        "false_positive_page",
        "negative_page",
        "positive_page",
        "exact_page",
        "complete_tables",
        "exact_table_cells",
        "exact_table_spans",
        "correct_cell_slots",
        "cell_slots",
        "penalized_cell_slots",
        "table_denominator",
    ):
        totals[key] = sum(row[key] for row in scored)
    return {"totals": totals, "pages": scores}


def conservation(source_ids: list[str], assigned_ids: list[str]) -> dict[str, Any]:
    """Measure full-output source identity coverage, never semantic correctness."""
    source, assigned = Counter(source_ids), Counter(assigned_ids)
    known = set(source)
    return {
        "source_count": len(source_ids),
        "assigned_count": len(assigned_ids),
        "missing_count": sum((source - assigned).values()),
        "duplicate_count": sum(max(0, count - source[item]) for item, count in assigned.items() if item in known),
        "unknown_count": sum(count for item, count in assigned.items() if item not in known),
        "exact_conservation": source == assigned,
    }
