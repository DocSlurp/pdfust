"""Span-aware anchor-row content diagnostics around the frozen v2 content metric."""

from __future__ import annotations

from typing import Any

from bench.generalization_scoring import _cells
from bench.p003_content_alignment import LIMITS, VERSION, compare_content

# ruff: noqa: EM101, TRY003, ANN401, C901, PLR0912, TRY004
ADAPTER_VERSION = "p003-span-content-v1"
POLICY = (
    "Validate original complete span matrices; preserve each anchor literal once in its anchor row; "
    "only legitimate covered None slots become empty placeholders. Span extents and header semantics "
    "are separate from content recovery. No merged text expansion or de-duplication."
)


def _project(table: Any) -> tuple[list[list[str]], dict[str, Any]]:
    """Validate before projection and retain literal, normalized and geometric anchor receipts."""
    if not isinstance(table, dict):
        raise ValueError("Canonical table dictionary required")
    rows, cols = table.get("row_count"), table.get("col_count")
    if (
        type(rows) is not int
        or type(cols) is not int
        or not 1 <= rows <= LIMITS["rows"]
        or not 1 <= cols <= LIMITS["columns"]
        or rows * cols > LIMITS["slots"]
    ):
        raise ValueError("Invalid or over-limit canonical dimensions")
    matrix, spans = table.get("values"), table.get("spans", [])
    if not isinstance(matrix, list) or len(matrix) != rows:
        raise ValueError("Complete original matrix required")
    if not isinstance(spans, list) or len(spans) > rows * cols:
        raise ValueError("Bounded original span list required")
    for row in matrix:
        if not isinstance(row, list) or len(row) != cols:
            raise ValueError("Rectangular original matrix required")
        for value in row:
            if value is not None and (not isinstance(value, str) or len(value) > LIMITS["cell_characters"]):
                raise ValueError("Invalid or over-limit raw anchor literal")
    cells = _cells(table)
    projected = [["" for _ in range(cols)] for _ in range(rows)]
    anchors, covered_slots = [], []
    for (r, c, height, width), normalized in sorted(cells.items()):
        literal = matrix[r][c]
        projected[r][c] = literal
        covered = [[rr, cc] for rr in range(r, r + height) for cc in range(c, c + width) if (rr, cc) != (r, c)]
        covered_slots.extend(covered)
        anchors.append(
            {
                "row": r,
                "column": c,
                "row_span": height,
                "column_span": width,
                "literal": literal,
                "normalized_literal": normalized,
                "covered_slots": covered,
            }
        )
    # _cells already rejects uncovered None and text in covered slots. Check that
    # this projection did not silently replace any independent empty/text anchor.
    covered_set = {tuple(slot) for slot in covered_slots}
    for r, row in enumerate(matrix):
        for c, literal in enumerate(row):
            if literal is None and (r, c) not in covered_set:
                raise ValueError("None is not covered by a valid span")
            if literal is not None and projected[r][c] != literal:
                raise ValueError("Projection would discard or copy an anchor literal")
    return projected, {
        "row_count": rows,
        "col_count": cols,
        "slot_count": rows * cols,
        "anchor_count": len(anchors),
        "merged_anchor_count": sum(a["row_span"] > 1 or a["column_span"] > 1 for a in anchors),
        "covered_slot_count": len(covered_slots),
        "covered_slots": sorted(covered_slots),
        "original_span_records": [{k: s[k] for k in ("row", "column", "row_span", "column_span")} for s in spans],
        "anchors": anchors,
        "literal_characters": sum(len(a["literal"]) for a in anchors),
        "normalized_literal_characters": sum(len(a["normalized_literal"]) for a in anchors),
        "row_interpretation": (
            "Merged cell text belongs once to its top-left anchor row, not every row crossed by its extent"
        ),
    }


def _topology(receipt: dict[str, Any]) -> tuple[Any, ...]:
    return (
        receipt["row_count"],
        receipt["col_count"],
        tuple((a["row"], a["column"], a["row_span"], a["column_span"]) for a in receipt["anchors"]),
    )


def compare_table_content(reference: Any, prediction: Any) -> dict[str, Any]:
    """Return v2 content counts with validated span receipts, never a schema acceptance."""
    receipts: dict[str, Any] = {"reference": None, "prediction": None}
    projected: dict[str, list[list[str]]] = {}
    for name, value in (("reference", reference), ("prediction", prediction)):
        try:
            projected[name], receipts[name] = _project(value)
        except (ValueError, KeyError, TypeError) as error:
            return {
                "version": VERSION,
                "adapter_version": ADAPTER_VERSION,
                "adapter_policy": POLICY,
                "supported": False,
                "unsupported_reason": f"{name} span validation/admission: {error}",
                "counts": None,
                "precision": None,
                "recall": None,
                "content_recovered_with_row_order": None,
                "schema_correctness": None,
                "span_topology_equal": None,
                "span_coverage": receipts,
                "edit_work": 0,
                "limits": dict(LIMITS),
                "header_label_acceptance": "Separate source-aware metric required",
            }
    result = compare_content(projected["reference"], projected["prediction"])
    return {
        **result,
        "adapter_version": ADAPTER_VERSION,
        "adapter_policy": POLICY,
        "span_topology_equal": _topology(receipts["reference"]) == _topology(receipts["prediction"]),
        "span_coverage": receipts,
        "schema_correctness": None,
        "span_acceptance": "No schema acceptance inferred, even with equal topology and complete anchor-row content",
        "original_covered_slots_expanded": False,
        "original_anchor_literals_deduplicated": False,
    }
