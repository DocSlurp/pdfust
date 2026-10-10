"""Offline natural-table evaluation, independent of inference and assembly code."""

# Frozen artifact schemas are heterogeneous; strict validation happens at entry.
# ruff: noqa: C901, PLR0912, PLR2004, EM101, TRY003, TRY301
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from html.parser import HTMLParser
from typing import Any

from bench.pipeline_scoring import _assignment

MAX_SLOTS = 4096
MAX_TABLES = 256


def normalize_text(text: str) -> str:
    """Normalize NFC and Unicode whitespace; preserve case, punctuation and math."""
    return " ".join(unicodedata.normalize("NFC", text).split())


class _AnnotationParser(HTMLParser):
    """Parse explicit table rows and cells without browser error recovery."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[tuple[str, int, int]]]] = []
        self.rows: list[list[tuple[str, int, int]]] | None = None
        self.row: list[tuple[str, int, int]] | None = None
        self.cell: list[str] | None = None
        self.span = (1, 1)
        self.inline: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            if self.rows is not None:
                self.errors.append("nested_table")
            else:
                self.rows = []
        elif tag == "tr":
            if self.rows is None or self.row is not None:
                self.errors.append("invalid_row_nesting")
            else:
                self.row = []
        elif tag in {"td", "th"}:
            if self.row is None or self.cell is not None:
                self.errors.append("invalid_cell_nesting")
                return
            self.cell = []
            attributes = dict(attrs)
            try:
                dimensions = []
                for key in ("rowspan", "colspan"):
                    value = attributes.get(key, "1")
                    if value is None or not re.fullmatch(r"[1-9][0-9]*", value):
                        raise ValueError("Invalid span")
                    size = int(value)
                    if size > MAX_SLOTS:
                        raise ValueError("Oversized span")
                    dimensions.append(size)
                self.span = (dimensions[0], dimensions[1])
            except ValueError:
                self.errors.append("invalid_span")
                self.span = (1, 1)
            self.inline = [tag]
        elif self.cell is not None:
            if tag == "br":
                self.cell.append(" ")
            elif tag not in {"img", "hr", "wbr"}:
                self.inline.append(tag)
            if tag in {"img", "script", "style"}:
                self.errors.append("unsupported_cell_content")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in {"br", "img", "hr", "wbr"}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"}:
            if self.cell is None or self.row is None or self.inline != [tag]:
                self.errors.append("incomplete_cell")
            else:
                self.row.append((normalize_text("".join(self.cell)), *self.span))
            self.cell = None
            self.inline = []
        elif tag == "tr":
            if self.row is None or self.rows is None or self.cell is not None:
                self.errors.append("incomplete_row")
            else:
                self.rows.append(self.row)
            self.row = None
        elif tag == "table":
            if self.rows is None or self.row is not None or self.cell is not None:
                self.errors.append("incomplete_table")
            else:
                self.tables.append(self.rows)
            self.rows = None
        elif self.cell is not None:
            if self.inline and self.inline[-1] == tag:
                self.inline.pop()
            elif tag not in {"br", "img", "hr", "wbr"}:
                self.errors.append("unbalanced_inline_markup")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
        elif self.row is not None and data.strip():
            self.errors.append("text_outside_cell")


def _html_table(rows: list[list[tuple[str, int, int]]]) -> dict[str, Any]:
    occupied: dict[tuple[int, int], str | None] = {}
    spans = []
    if not rows or len(rows) > MAX_SLOTS:
        raise ValueError("Empty or oversized table")
    for r, row in enumerate(rows):
        c = 0
        for text, height, width in row:
            while (r, c) in occupied:
                c += 1
            if r + height > len(rows) or (c + width) * len(rows) > MAX_SLOTS:
                raise ValueError("Span outside bounded explicit rows")
            for rr in range(r, r + height):
                for cc in range(c, c + width):
                    if (rr, cc) in occupied:
                        raise ValueError("Overlapping spans")
                    occupied[rr, cc] = text if (rr, cc) == (r, c) else None
            if height > 1 or width > 1:
                spans.append({"row": r, "column": c, "row_span": height, "column_span": width})
            c += width
    columns = max((c + 1 for _, c in occupied), default=0)
    if not columns or len(occupied) != len(rows) * columns:
        raise ValueError("Ragged or incomplete table")
    return {
        "row_count": len(rows),
        "col_count": columns,
        "values": [[occupied[r, c] for c in range(columns)] for r in range(len(rows))],
        "spans": spans,
    }


def parse_annotation_html(annotation_html: str) -> dict[str, Any]:
    """Retain original annotations and abstain on any incomplete table markup."""
    parser = _AnnotationParser()
    try:
        parser.feed(annotation_html)
        parser.close()
        if parser.rows is not None or parser.row is not None or parser.cell is not None:
            parser.errors.append("unclosed_table_markup")
        if not parser.tables:
            parser.errors.append("no_explicit_table")
        if len(parser.tables) > MAX_TABLES:
            parser.errors.append("too_many_tables")
        tables = [_html_table(rows) for rows in parser.tables] if not parser.errors else []
    except (ValueError, RecursionError) as error:
        parser.errors.append(str(error))
        tables = []
    return {
        "annotation_html": annotation_html,
        "structural_scored": not parser.errors,
        "tables": tables,
        "annotation_errors": parser.errors,
    }


def _cells(table: dict[str, Any]) -> dict[tuple[int, int, int, int], str]:
    rows, cols, values = table["row_count"], table["col_count"], table["values"]
    if type(rows) is not int or type(cols) is not int or min(rows, cols) < 1 or rows * cols > MAX_SLOTS:
        raise ValueError("Invalid table dimensions")
    if len(values) != rows or any(len(row) != cols for row in values):
        raise ValueError("Invalid rectangular matrix")
    spans: dict[tuple[int, int], tuple[int, int]] = {}
    covered = set()
    for span in table.get("spans", []):
        r, c, height, width = (span[k] for k in ("row", "column", "row_span", "column_span"))
        if any(type(v) is not int for v in (r, c, height, width)):
            raise ValueError("Invalid span types")
        if min(r, c) < 0 or min(height, width) < 1 or r + height > rows or c + width > cols:
            raise ValueError("Invalid span bounds")
        if (r, c) in spans:
            raise ValueError("Duplicate span anchor")
        spans[r, c] = (height, width)
        for rr in range(r, r + height):
            for cc in range(c, c + width):
                if (rr, cc) in covered:
                    raise ValueError("Overlapping spans")
                covered.add((rr, cc))
    anchors = set(spans)
    nonanchors = covered - anchors
    cells = {}
    for r, row in enumerate(values):
        for c, value in enumerate(row):
            if (r, c) in nonanchors:
                if value is not None:
                    raise ValueError("Covered slot must be None")
            elif not isinstance(value, str):
                raise ValueError("Uncovered cell must be a string")
            else:
                height, width = spans.get((r, c), (1, 1))
                cells[r, c, height, width] = normalize_text(value)
    return cells


def _bbox(table: dict[str, Any]) -> tuple[float, float, float, float] | None:
    value = table.get("bbox")
    if value is None:
        return None
    if len(value) != 4 or any(
        isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in value
    ):
        raise ValueError("Invalid bbox")
    if value[2] <= value[0] or value[3] <= value[1]:
        raise ValueError("Empty bbox")
    return tuple(value)


def _iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    area = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return area / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - area)


def _text_similarity(a: dict[Any, str], b: dict[Any, str]) -> float:
    # Character multiset is a matching cue only, never a correctness score.
    aa, bb = Counter("".join(a.values())), Counter("".join(b.values()))
    return 2 * sum((aa & bb).values()) / max(1, sum(aa.values()) + sum(bb.values()))


def _distance(a: str, b: str) -> int:
    """Exact Levenshtein distance with linear scratch memory."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char in enumerate(a, 1):
        current = [i]
        for j, other in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (char != other)))
        previous = current
    return previous[-1]


def score_page(target: dict[str, Any], observed: list[dict[str, Any]], *, status: str = "ok") -> dict[str, Any]:
    """Score complete matrices, geometry, cell topology, and text independently."""
    base: dict[str, Any] = {"structural_scored": False, "error": status != "ok"}
    if not target.get("structural_scored", True):
        return base
    gold = target.get("tables", [])
    try:
        if len(gold) > MAX_TABLES:
            raise ValueError("Too many reference tables")
        expected = [_cells(t) for t in gold]
        gold_boxes = [_bbox(t) for t in gold]
    except (KeyError, TypeError, ValueError):
        return {**base, "annotation_errors": ["invalid_reference_matrix"]}
    malformed = False
    try:
        if len(observed) > MAX_TABLES:
            raise ValueError("Too many predicted tables")
        predicted = observed if status == "ok" else []
        actual = [_cells(t) for t in predicted]
        boxes = [_bbox(t) for t in predicted]
    except (KeyError, TypeError, ValueError):
        malformed = True
        predicted, actual, boxes = [], [], []
    weights: list[list[int]] = []
    methods: dict[tuple[int, int], str] = {}
    for i, cells in enumerate(expected):
        weights.append([])
        for j, other in enumerate(actual):
            gold_box, predicted_box = gold_boxes[i], boxes[j]
            if gold_box is not None and predicted_box is not None:
                cue = _iou(gold_box, predicted_box)
                admitted, method = cue >= 0.1, "geometry"
            elif len(gold) == len(predicted) == 1:
                cue, admitted, method = 1.0, True, "single_table"
            else:
                cue = _text_similarity(cells, other)
                admitted, method = cue >= 0.2, "text_assisted"
            topology = len(cells.keys() & other.keys()) / max(1, len(cells.keys() | other.keys()))
            # Geometry dominates; content breaks ties only without geometry.
            weight = 1 + round(cue * 1_000_000) + round(topology * 1000) if admitted else 0
            weights[-1].append(weight)
            methods[i, j] = method
    pairs = _assignment(weights)
    matched_g, matched_p = {i for i, _ in pairs}, {j for _, j in pairs}
    counts = {
        "expected_tables": len(gold),
        "detected_tables": len(predicted),
        "matched_tables": len(pairs),
        "missing_tables": len(gold) - len(pairs),
        "false_positive_tables": len(predicted) - len(pairs),
        "expected_cells": sum(map(len, expected)),
        "predicted_cells": sum(map(len, actual)),
        "correct_structure_cells": 0,
        "correct_text_cells": 0,
        "complete_tables": 0,
        "exact_table_spans": 0,
        "exact_table_cells": 0,
        "exact_rows": 0,
        "exact_columns": 0,
        "text_edit_distance": 0,
        "reference_characters": sum(len(v) for t in expected for v in t.values()),
        "predicted_characters": sum(len(v) for t in actual for v in t.values()),
        "geometry_matches": 0,
        "geometry_iou_sum": 0.0,
        "geometry_expected_tables": sum(b is not None for b in gold_boxes),
    }
    details = []
    for i, j in pairs:
        a, b = expected[i], actual[j]
        same_structure = a.keys() == b.keys()
        same_text = same_structure and a == b
        counts["correct_structure_cells"] += len(a.keys() & b.keys())
        counts["complete_tables"] += int(same_text)
        counts["exact_table_spans"] += int(same_structure)
        counts["exact_rows"] += int(gold[i]["row_count"] == predicted[j]["row_count"])
        counts["exact_columns"] += int(gold[i]["col_count"] == predicted[j]["col_count"])
        # Text-only correspondence uses anchor position regardless of spans.
        aa, bb = {(k[0], k[1]): v for k, v in a.items()}, {(k[0], k[1]): v for k, v in b.items()}
        counts["correct_text_cells"] += sum(aa[k] == bb[k] for k in aa.keys() & bb.keys())
        counts["exact_table_cells"] += int(aa == bb)
        counts["text_edit_distance"] += sum(_distance(aa.get(k, ""), bb.get(k, "")) for k in aa.keys() | bb.keys())
        gold_box, predicted_box = gold_boxes[i], boxes[j]
        if methods[i, j] == "geometry" and gold_box is not None and predicted_box is not None:
            overlap = _iou(gold_box, predicted_box)
            counts["geometry_matches"] += 1
            counts["geometry_iou_sum"] += overlap
        else:
            overlap = None
        details.append({"target": i, "prediction": j, "matching_method": methods[i, j], "iou": overlap})
    counts["text_edit_distance"] += sum(
        len(v) for i, t in enumerate(expected) if i not in matched_g for v in t.values()
    )
    counts["text_edit_distance"] += sum(len(v) for j, t in enumerate(actual) if j not in matched_p for v in t.values())
    successful = status == "ok" and not malformed
    return {
        "structural_scored": True,
        "error": not successful,
        "malformed": malformed,
        **counts,
        "negative_page": not gold,
        "positive_page": bool(gold),
        "false_positive_page": bool(not gold and predicted),
        "presence_correct": successful and bool(gold) == bool(predicted),
        "exact_page": successful and counts["complete_tables"] == len(gold) and len(pairs) == len(predicted),
        "table_denominator": len(gold) + len(predicted) - len(pairs),
        "penalized_cells": counts["expected_cells"] + counts["predicted_cells"] - counts["correct_structure_cells"],
        "matches": details,
    }


def score_dataset(targets: list[dict[str, Any]] | dict[str, Any], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Accept P001 report rows or final states; all manifest pages remain counted."""
    pages = targets["pages"] if isinstance(targets, dict) else targets
    ids = [p["id"] for p in pages]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate target page ID")
    by_id = {}
    for prediction in predictions:
        if prediction["id"] in by_id or prediction["id"] not in ids:
            raise ValueError("Duplicate or unknown prediction page ID")
        by_id[prediction["id"]] = prediction
    scores = []
    for page in pages:
        prediction = by_id.get(page["id"], {})
        tables = prediction.get("tables", prediction.get("observed", prediction.get("state", {}).get("tables", [])))
        status = prediction.get("status", "ok" if prediction else "missing")
        scores.append({"id": page["id"], **score_page(page, tables, status=status)})
    scored = [s for s in scores if s["structural_scored"]]
    totals: dict[str, Any] = {
        "pages": len(pages),
        "scored_pages": len(scored),
        "diagnostic_pages": len(pages) - len(scored),
        "all_page_errors": sum(s["error"] for s in scores),
    }
    if scored:
        for key, value in scored[0].items():
            if key not in {"structural_scored", "id"} and isinstance(value, (int, float)):
                totals[key] = sum(s[key] for s in scored)
    return {"totals": totals, "pages": scores}


def audit_model_body(body: dict[str, Any] | list[Any]) -> dict[str, Any]:
    """Report explicit private-reference fields in a serialized inference body.

    This is a schema-level audit, not proof against semantic leakage. A body may
    legitimately include source words also present in reference cells.
    """
    forbidden = {
        "annotation_html",
        "annotation_errors",
        "annotation_path",
        "gold",
        "gold_tables",
        "private_targets",
        "reference",
        "reference_tables",
        "structural_scored",
        "targets",
        "expected_values",
        "expected_tables",
        "answer",
        "ground_truth",
    }
    violations = []
    stack: list[tuple[str, Any]] = [("$", body)]
    while stack:
        path, node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                child = f"{path}.{key}"
                if str(key).lower().replace("-", "_") in forbidden:
                    violations.append(child)
                stack.append((child, value))
        elif isinstance(node, list):
            stack.extend((f"{path}[{i}]", value) for i, value in enumerate(node))
    return {"explicit_reference_fields_absent": not violations, "violations": sorted(violations)}
