"""Bounded CPU-only table recovery study with frozen evidence gates.

Run ``.venv/bin/python -m bench.geometry_cascade --repeats 3``. This experiment
does not modify pdfust, call a model, or use fixture names/reference cells to
route extraction. Development and heldout transformations are reported apart;
the latter are stress tests of related templates, not independent producers.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import json
import platform
import re
import statistics
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfust
from bench.feature_cases import ROOT, FeatureCase, page_pdf, text_op
from bench.structure_cases import RECORD_REFERENCES, StructureCase, build_structure_cases
from bench.structure_core import (
    geometry_tables,
    markdown_tables,
    render_tables,
    score_records,
    score_tables,
    source_agreement,
    validate_patch,
)
from bench.structure_native import header_guided_records

ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts/geometry"
REPORT = ROOT / "bench/results/geometry-cascade.md"
MAX_WORDS = 8192
MAX_TABLES = 32
MAX_CELLS = 4096
MAX_REPEATS = 20
MIN_ROWS = 3
MIN_COLUMNS = 2
MIN_NUMERIC_ROWS = 2
MAX_KEY_WORDS = 2
METHODS = ("native", "text", "geometry", "header", "cascade")
NUMERIC = re.compile(r"[-+$]?[\d,]+(?:\.\d+)?%?\Z")


@dataclass(frozen=True)
class Case:
    """Carry an input and evaluation-only labels separately from routing."""

    case: StructureCase
    split: str
    family: str


def derivative(style: str, *, rotation: int = 0, reverse: bool = False) -> StructureCase:  # noqa: C901, PLR0912
    """Create author-specified cells with interchangeable content encodings."""
    matrix: tuple[tuple[str, ...], ...] = (
        ("Item", "Description", "Amount"),
        ("Alpha", "First line continuation" if style == "partial" else "First", "42.00"),
        ("Beta", "Second line continuation" if style == "partial" else "Second", "7.00"),
        ("Gamma", "Short", "16.00"),
    )
    if style == "missing":
        matrix = (matrix[0], matrix[1], ("Beta", "", "7.00"), ("Gamma", "Short", ""))
    if style in {"prose", "numeric-prose"}:
        matrix = (
            ("A quiet morning", "Across the valley", "Clouds were gathering"),
            ("Birds were singing", "Beyond the river", "Trees moved gently"),
            ("The path curved", "Toward the hill", "Rain arrived slowly"),
            ("Light returned", "After the storm", "The sky cleared"),
        )
        if style == "numeric-prose":
            matrix = tuple((*row[:2], str(1900 + index)) for index, row in enumerate(matrix))
    ops: list[str] = []
    for index, row in enumerate(matrix):
        y = 680 - index * 50
        for x, cell in zip((50, 230, 480), row, strict=True):
            if " continuation" in cell:
                ops.extend((text_op(cell.removesuffix(" continuation"), x, y), text_op("continuation", x, y - 16)))
            elif cell:
                ops.append(text_op(cell, x, y))
    if reverse:
        ops.reverse()
    rules = []
    xs: tuple[int, ...] = (40, 220, 460, 570)
    ys: tuple[int, ...] = (700, 650, 600, 550, 500)
    if style == "partial":
        ys = (700, 675, 650)
    if style not in {"prose", "numeric-prose", "missing", "borderless"}:
        segments = [(40, y, 570, y) for y in ys] + [(x, min(ys), x, max(ys)) for x in xs]
        if style == "dashed":
            rules.append("[3 3] 0 d")
        for x0, y0, x1, y1 in segments:
            if style == "filled":
                rules.append(f"{x0} {y0} {max(0.25, x1 - x0)} {max(0.25, y1 - y0)} re f")
            elif style == "broken":
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                dx, dy = (1 if x1 != x0 else 0), (1 if y1 != y0 else 0)
                rules.extend((f"{x0} {y0} m {mx - dx} {my - dy} l S", f"{mx + dx} {my + dy} m {x1} {y1} l S"))
            else:
                rules.append(f"{x0} {y0} m {x1} {y1} l S")
    name = f"cascade-{style}-r{rotation}-{'reverse' if reverse else 'forward'}"
    data = page_pdf("\n".join([*rules, *ops]), extra_page=f"/Rotate {rotation}")
    gold = () if style in {"prose", "numeric-prose"} else (matrix,)
    return StructureCase(FeatureCase(name, data, ("tables", style), "Author-specified transformation."), gold)


def cases() -> list[Case]:
    """Freeze the split before evaluation; never optimize on heldout outcomes."""
    result = [Case(case, "existing", "existing-study") for case in build_structure_cases()]
    result.extend(
        Case(derivative(style), "development", style) for style in ("solid", "borderless", "partial", "prose")
    )
    # Shared templates deliberately expose encoding/ordering generalization only.
    result.extend(
        Case(derivative(style, reverse=True), "heldout", style)
        for style in ("broken", "dashed", "filled", "partial", "missing", "prose", "numeric-prose")
    )
    for rotation in (90, 180, 270):
        result.extend(
            Case(derivative(style, rotation=rotation, reverse=True), "heldout", style)
            for style in ("solid", "partial", "missing")
        )
    result.extend(
        Case(header_control(style), "development-round2", "header-control") for style in ("prose", "footnote")
    )
    return result


def header_control(style: str) -> StructureCase:
    """Place prose or a footnote below a complete two-row vector header."""
    rules = [f"40 {y} m 570 {y} l S" for y in (700, 675, 650)]
    rules.extend(f"{x} 650 m {x} 700 l S" for x in (40, 220, 460, 570))
    ops = [text_op(value, x, 680) for x, value in zip((50, 230, 480), ("Item", "Description", "Amount"), strict=True)]
    matrix: tuple[tuple[str, ...], ...] = (("Item", "Description", "Amount"), ("", "", ""))
    if style == "prose":
        for index in range(3):
            ops.extend(
                text_op(value, x, 630 - index * 40)
                for x, value in zip(
                    (50, 230, 480), ("Quiet morning", "Across the valley", "Clouds gathered"), strict=True
                )
            )
    else:
        rows = (("Alpha", "First", "42.00"), ("Beta", "Second", "7.00"), ("Gamma", "Short", "16.00"))
        for index, row in enumerate(rows):
            ops.extend(text_op(value, x, 630 - index * 50) for x, value in zip((50, 230, 480), row, strict=True))
        # Small leading deliberately prevents a gap-only stop from protecting prose.
        ops.append(text_op("Note: descriptive prose belongs outside the records.", 50, 514))
        matrix = (matrix[0], *rows)
    return StructureCase(
        FeatureCase(
            f"cascade-header-{style}",
            page_pdf("\n".join([*rules, *ops])),
            ("tables", "header control"),
            "Round-two development control.",
        ),
        (matrix,),
    )


def logical_orientation(page: pdfust.Page) -> int:
    """Derive axes from interpreted baseline direction, not Rotate metadata."""
    directions: Counter[tuple[int, int]] = Counter()
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            directions[round(line["dir"][0]), round(line["dir"][1])] += sum(len(span["text"]) for span in line["spans"])
    direction = directions.most_common(1)[0][0] if directions else (1, 0)
    return {(1, 0): 0, (0, 1): 90, (-1, 0): 180, (0, -1): 270}.get(direction, 0)


def logical_box(page: pdfust.Page, box: tuple[float, ...], orientation: int) -> tuple[float, ...]:
    """Transform word and vector boxes with the same baseline-derived axes."""
    x0, y0, x1, y1 = box
    width, height = page.rect.width, page.rect.height
    return {
        0: (x0, y0, x1, y1),
        90: (y0, width - x1, y1, width - x0),
        180: (width - x1, height - y1, width - x0, height - y0),
        270: (height - y1, x0, height - y0, x1),
    }[orientation]


def positioned_words(page: pdfust.Page) -> list[dict[str, Any]]:
    """Normalize right-angle baseline direction without using page labels."""
    orientation = logical_orientation(page)
    raw = page.get_text("words")
    if len(raw) > MAX_WORDS:
        msg = "geometry study word admission exceeded"
        raise ValueError(msg)
    words = []
    for index, word in enumerate(raw):
        logical = logical_box(page, tuple(word[:4]), orientation)
        words.append({"id": f"w{index}", "text": word[4], "bbox": list(word[:4]), "logical_bbox": list(logical)})
    return words


def bounded(matrices: list[list[list[str]]]) -> list[list[list[str]]]:
    """Refuse a complete result above fixed benchmark materialization limits."""
    if len(matrices) > MAX_TABLES or sum(len(row) for table in matrices for row in table) > MAX_CELLS:
        msg = "geometry study table admission exceeded"
        raise ValueError(msg)
    return matrices


def geometry(words: list[dict[str, Any]]) -> tuple[list[list[list[str]]], set[str]]:
    """Reuse source-ID geometry and reject duplicate/unknown ownership."""
    if len(words) > MAX_WORDS:
        msg = "geometry study word admission exceeded"
        raise ValueError(msg)
    patches = geometry_tables(words, wrapped=True)
    if len(patches) > MAX_TABLES or sum(len(row) for table in patches for row in table) > MAX_CELLS:
        msg = "geometry study candidate admission exceeded"
        raise ValueError(msg)
    return validate_patch({"tables": [{"rows": table} for table in patches]}, words)


def numeric_evidence(matrix: list[list[str]]) -> bool:
    """Require repeated short keyed records and numerical value columns.

    This is a deliberately narrow evidence gate, not a table classifier. Numeric
    prose can still satisfy it; the heldout numeric prose control measures that.
    """
    if len(matrix) < MIN_ROWS or len(matrix[0]) < MIN_COLUMNS:
        return False
    body = matrix[1:]
    short_keys = sum(bool(row[0]) and len(row[0].split()) <= MAX_KEY_WORDS for row in body)
    numeric = sum(any(NUMERIC.fullmatch(cell.strip()) for cell in row[1:] if cell) for row in body)
    return numeric >= MIN_NUMERIC_ROWS and short_keys >= max(MIN_NUMERIC_ROWS, len(body) * 0.75)


def clustered_axis(values: list[float]) -> list[float]:
    """Merge one-point vector coordinate noise without changing cell ownership."""
    result: list[float] = []
    for value in sorted(values):
        if not result or value - result[-1] > 1:
            result.append(value)
    return result


def strict_header_records(  # noqa: C901, PLR0912
    page: pdfust.Page,
    words: list[dict[str, Any]],
) -> tuple[list[list[list[str]]], set[str], list[dict[str, Any]]]:
    """Stop body extension at unsupported rows and preserve each header ID once.

    This round-two proposal uses Senate as development evidence. A numeric last
    column can start an anonymous payroll row; descriptive continuation after
    such a row cannot consume the amount column. Unsupported rows end extension,
    leaving all following source words as prose. Vector boxes follow the same
    baseline-derived logical transform as source words, retaining their IDs.
    """
    matrices: list[list[list[str]]] = []
    used: set[str] = set()
    diagnostics: list[dict[str, Any]] = []
    orientation = logical_orientation(page)
    for table in page.find_tables():
        vector_cells = [
            logical_box(page, (cell.x0, cell.y0, cell.x1, cell.y1), orientation)
            for cell in table.cells
            if cell is not None
        ]
        bbox = logical_box(page, (table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1), orientation)
        xaxis = clustered_axis([coordinate for cell in vector_cells for coordinate in (cell[0], cell[2])])
        yaxis = clustered_axis([coordinate for cell in vector_cells for coordinate in (cell[1], cell[3])])
        rows, columns = len(yaxis) - 1, len(xaxis) - 1
        detail: dict[str, Any] = {
            "rows": rows,
            "columns": columns,
            "orientation": orientation,
            "physical_rows": table.row_count,
            "physical_columns": table.col_count,
        }
        diagnostics.append(detail)
        if rows > MIN_ROWS or columns < MIN_ROWS:
            detail["stop"] = "not-short-wide-header"
            continue
        lefts = xaxis[:-1]
        selected = [
            word
            for word in words
            if bbox[0] <= (word["logical_bbox"][0] + word["logical_bbox"][2]) / 2 <= bbox[2]
            and bbox[1] <= (word["logical_bbox"][1] + word["logical_bbox"][3]) / 2
        ]
        headers: list[list[str]] = [[] for _ in lefts]
        body = []
        for word in selected:
            center_x = (word["logical_bbox"][0] + word["logical_bbox"][2]) / 2
            center_y = (word["logical_bbox"][1] + word["logical_bbox"][3]) / 2
            if center_y > bbox[3]:
                body.append(word)
                continue
            # A merged header remains at its native anchor rather than being duplicated.
            anchor = next(
                (
                    min(range(len(lefts)), key=lambda column: abs(lefts[column] - cell[0]))
                    for cell in sorted(vector_cells, key=lambda box: (box[1], box[0]))
                    if cell[0] <= center_x <= cell[2] and cell[1] <= center_y <= cell[3]
                ),
                None,
            )
            if anchor is not None:
                headers[anchor].append(word["id"])
        if not body:
            detail["stop"] = "no-body-words"
            continue
        height = statistics.median(word["logical_bbox"][3] - word["logical_bbox"][1] for word in body)
        physical: list[list[dict[str, Any]]] = []
        for word in sorted(body, key=lambda item: (item["logical_bbox"][1], item["logical_bbox"][0])):
            if not physical or abs(word["logical_bbox"][1] - physical[-1][0]["logical_bbox"][1]) > height * 0.45:
                physical.append([])
            physical[-1].append(word)
        records: list[list[list[str]]] = []
        previous_y = None
        numeric_rows = 0
        source = {word["id"]: word["text"] for word in words}
        detail["stop"] = "end-of-source"
        for line in physical:
            y = line[0]["logical_bbox"][1]
            if previous_y is not None and y - previous_y > height * 5:
                detail["stop"] = "body-gap"
                break
            cells: list[list[str]] = [[] for _ in lefts]
            for word in sorted(line, key=lambda item: item["logical_bbox"][0]):
                center = (word["logical_bbox"][0] + word["logical_bbox"][2]) / 2
                cells[max(0, sum(center >= left for left in lefts) - 1)].append(word["id"])
            numeric_last = bool(cells[-1]) and bool(NUMERIC.fullmatch(" ".join(source[index] for index in cells[-1])))
            occupied = sum(bool(cell) for cell in cells)
            if numeric_last and occupied >= MIN_COLUMNS:
                records.append(cells)
                numeric_rows += 1
            elif records and not cells[0] and previous_y is not None and y - previous_y <= height * 2:
                # Overflowing descriptive continuation is source-backed; amount stays scalar.
                if cells[-1]:
                    cells[-2].extend(cells[-1])
                    cells[-1] = []
                for column, ids in enumerate(cells):
                    records[-1][column].extend(ids)
            else:
                detail["stop"] = "unsupported-record-or-prose"
                detail["stopped_word_ids"] = [word["id"] for word in line]
                break
            previous_y = y
        detail["numeric_rows"] = numeric_rows
        if numeric_rows < MIN_NUMERIC_ROWS:
            detail["admission"] = "insufficient-numeric-records"
            continue
        patch = [headers, *records]
        matrix, consumed = validate_patch({"tables": [{"rows": patch}]}, words)
        if consumed & used:
            detail["admission"] = "overlapping-source-ownership"
            continue
        used.update(consumed)
        matrices.extend(matrix)
        detail["admission"] = "accepted"
        detail["source_ids"] = sorted(consumed)
        detail["header_ids"] = [index for cell in headers for index in cell]
    return bounded(matrices), used, diagnostics


def cascade(
    page: pdfust.Page,
    words: list[dict[str, Any]],
) -> tuple[list[list[list[str]]], str, set[str], list[dict[str, Any]]]:
    """Route native grids, vector header extension, then numeric geometry.

    Short vector tables can trigger baseline-normalized header extension;
    numerical geometry uses its independently frozen evidence gate.
    """
    native = list(page.find_tables())
    if native:
        guided, consumed, diagnostics = strict_header_records(page, words)
        if guided and len(guided) == len(native):
            return bounded(guided), "strict-vector-header", consumed, diagnostics
        matrices = markdown_tables(page.to_markdown())
        return bounded(matrices), "native-grid", covered_ids(page, words), diagnostics
    matrices, consumed = geometry(words)
    accepted = [table for table in matrices if numeric_evidence(table)]
    if len(accepted) != len(matrices):
        # Rebuild source ownership only for accepted table IDs, without token matching.
        patches = geometry_tables(words, wrapped=True)
        consumed = {
            word_id
            for patch, matrix in zip(patches, matrices, strict=True)
            if numeric_evidence(matrix)
            for row in patch
            for cell in row
            for word_id in cell
        }
    return bounded(accepted), "numeric-geometry" if accepted else "abstain", consumed, []


def covered_ids(page: pdfust.Page, words: list[dict[str, Any]], *, extend: bool = False) -> set[str]:
    """Retain all source words outside selected vector extents as ordinary text."""
    boxes = [table.bbox for table in page.find_tables()]
    return {
        word["id"]
        for word in words
        for box in boxes
        if box.x0 <= (word["bbox"][0] + word["bbox"][2]) / 2 <= box.x1
        and box.y0 <= (word["bbox"][1] + word["bbox"][3]) / 2
        and (extend or (word["bbox"][1] + word["bbox"][3]) / 2 <= box.y1)
    }


def extract(page: pdfust.Page, method: str) -> dict[str, Any]:
    """Return complete tables, retained text, routing evidence and source loss."""
    if method == "native":
        output = page.to_markdown()
        tables = bounded(markdown_tables(output))
        route = "native-grid"
    elif method == "text":
        output = page.to_markdown(table_strategy="text")
        tables = bounded(markdown_tables(output))
        route = "native-text-strategy"
    else:
        words = positioned_words(page)
        if method == "geometry":
            tables, consumed = geometry(words)
            route = "unconditional-geometry"
        elif method == "cascade":
            tables, route, consumed, diagnostics = cascade(page, words)
        elif method == "header":
            tables = bounded(header_guided_records(page, words))
            consumed = covered_ids(page, words, extend=True) if tables else set()
            route = "existing-header-helper" if tables else "abstain"
        else:
            msg = f"unknown method: {method}"
            raise ValueError(msg)
        remainder = " ".join(word["text"] for word in words if word["id"] not in consumed)
        output = render_tables(tables) + "\n\n<p>" + html.escape(remainder) + "</p>"
    result: dict[str, Any] = {"tables": tables, "markdown": output, "route": route}
    if method == "cascade":
        result["header_diagnostics"] = diagnostics
    elif method == "header":
        result["header_diagnostics"] = [
            {
                "stop": "end-of-page-without-record-evidence-gate",
                "header_policy": "merged labels expanded across columns",
            }
        ]
    return result


def run(*, repeats: int = 3) -> dict[str, Any]:
    """Time opening plus extraction on fresh documents, saving every result."""
    if not 1 <= repeats <= MAX_REPEATS:
        msg = "repeats must be between 1 and 20"
        raise ValueError(msg)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    results = []
    for entry in cases():
        feature = entry.case.feature
        directory = ARTIFACTS / feature.name
        directory.mkdir(exist_ok=True)
        (directory / "input.pdf").write_bytes(feature.data)
        (directory / "labels.json").write_text(
            json.dumps(
                {
                    "tables": entry.case.tables,
                    "spans": entry.case.spans,
                    "source": feature.source,
                    "notes": feature.notes,
                    "split": entry.split,
                    "family": entry.family,
                },
                indent=2,
            )
            + "\n"
        )
        with pdfust.open(stream=feature.data) as document:
            words = positioned_words(document[0])
        for method in METHODS:
            elapsed = []
            result: dict[str, Any] = {
                "name": feature.name,
                "method": method,
                "split": entry.split,
                "family": entry.family,
                "sha256": hashlib.sha256(feature.data).hexdigest(),
            }
            try:
                for _ in range(repeats):
                    start = time.perf_counter()
                    with pdfust.open(stream=feature.data) as document:
                        output = extract(document[0], method)
                    elapsed.append((time.perf_counter() - start) * 1000)
                result.update(
                    output=output,
                    milliseconds=elapsed,
                    median_ms=statistics.median(elapsed),
                    score=score_tables(output["tables"], entry.case.tables),
                    source=source_agreement(output["markdown"], words),
                    records=score_records(output["tables"], RECORD_REFERENCES.get(feature.name, {})),
                )
            except Exception as error:
                result["error"] = f"{type(error).__name__}: {error}"
            (directory / f"{method}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            results.append(result)
    extension_path = importlib.import_module("pdfust.pdfust_core").__file__
    if extension_path is None:
        msg = "native extension path is unavailable for provenance"
        raise ValueError(msg)
    report = {
        "python": platform.python_version(),
        "pdfust": pdfust.__version__,
        "repeats": repeats,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "platform": platform.platform(),
        "native_extension_sha256": hashlib.sha256(Path(extension_path).read_bytes()).hexdigest(),
        "limits": {"words": MAX_WORDS, "tables": MAX_TABLES, "cells": MAX_CELLS},
        "results": results,
    }
    (ARTIFACTS / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    write_report(report)
    return report


def write_report(report: dict[str, Any]) -> None:
    """Publish wins, losses, partial corpus labels and bounded timing scope."""
    lines = [
        "# CPU geometry cascade study",
        "",
        "Run `.venv/bin/python -m bench.geometry_cascade --repeats 3`.",
        "",
        f"Python {report['python']}; pdfust {report['pdfust']}; {report['repeats']} fresh-document repeats.",
        "",
        (
            f"Native extension SHA-256: `{report['native_extension_sha256']}`. "
            "Repository base revision: `7008b627bb01fcec4c12f80308967b511e4e2422`; "
            "the extension hash identifies the actual loaded build, including local rebuilds."
        ),
        "",
        (
            "CPU only. No model calls, OCR, cached detector boxes, network inference, or training. "
            "Timings include PDF opening and complete extraction/Markdown assembly, exclude fixture construction, "
            "label scoring and artifact writes. Source comparison runs outside timing. "
            "Per-page geometry admission: 8,192 source words, 32 tables, 4,096 cells; native API limits also apply."
        ),
        "",
        (
            "Round one froze a numeric evidence gate before benchmarking. Round two corrects full-grid native "
            "scoring through Page.to_markdown's existing logical rotation normalization and proposes a stricter "
            "vector-header handoff using Senate and two new development controls. Geometry's numerical gate "
            "is unchanged. No reference cells, fixture names or content-operator order shortcuts enter extraction. "
            "Existing inputs are observations; "
            "solid/borderless/partial/prose forward inputs are development; encoding changes, reverse content "
            "operators, missing cells, numeric prose and rotations are heldout transformations. Templates are "
            "related across splits: this does not demonstrate independent-document generalization."
        ),
        "",
        (
            "The heldout transformation outcomes were inspected after round one. Subsequent scores on them are "
            "regression observations, not a fresh untouched test. The original report and complete results are "
            "preserved locally as round1-before-normalization.{md,json}. Header control inputs are explicitly "
            "development-round2; no threshold was tuned against the heldout transformations. "
            "Round-two pre-normalization results are preserved as round2-before-logical-header.{md,json}. "
            "The final run uses the locally rebuilt native collinear-rule connectivity fix. Prior round "
            "artifacts predate that rebuild and lack an extension hash; they cannot isolate its timing effect."
        ),
        "",
        (
            "The header baseline reuses header_guided_records without an evidence gate. It extends to page end "
            "and expands merged header labels. The revised handoff admits at least two numeric-last-column "
            "records, permits anonymous salary records, stops at unsupported prose/gaps, preserves source IDs "
            "once, and keeps description continuation out of scalar amount cells. Round three transforms "
            "word and vector boxes through the same interpreted baseline direction, handling rotated headers. "
            "A merged parent label remains at its anchor once; that is not complete header semantics."
        ),
        "",
        (
            "| Split | Method | Exact labeled pages | Correct cells | Relationship recall | "
            "False table pages / negatives; excess tables | Median ms | Missing / extra source tokens |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for split in ("existing", "development", "heldout", "development-round2"):
        for method in METHODS:
            rows = [r for r in report["results"] if r["split"] == split and r["method"] == method and "score" in r]
            gold = [r for r in rows if r["score"]["gold_available"]]
            positives = [r for r in gold if r["score"]["expected_tables"]]
            negatives = [r for r in gold if not r["score"]["expected_tables"]]
            correct = sum(r["score"]["correct_cells"] for r in positives)
            cells = sum(r["score"]["total_cells"] for r in positives)
            matches = sum(r["score"]["relationship_matches"] for r in positives)
            edges = sum(r["score"]["relationship_expected"] for r in positives)
            false = sum(bool(r["score"]["tables"]) for r in negatives)
            excess = sum(max(0, r["score"]["tables"] - r["score"]["expected_tables"]) for r in gold)
            missing = sum(r["source"]["missing_tokens"] for r in rows)
            extra = sum(r["source"]["extra_tokens"] for r in rows)
            ms = statistics.median(r["median_ms"] for r in rows) if rows else 0
            lines.append(
                f"| {split} | {method} | {sum(r['score']['exact'] for r in gold)}/{len(gold)} | "
                f"{correct}/{cells} | {matches}/{edges} | {false}/{len(negatives)}; {excess} | "
                f"{ms:.3f} | {missing}/{extra} |"
            )
    lines.extend(
        [
            "",
            "## Complete derivative results",
            "",
            "| Input | Split | Native exact | Text exact | Geometry exact | Header exact | Cascade exact / route |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    names = dict.fromkeys(r["name"] for r in report["results"] if r["split"] != "existing")
    for name in names:
        rows = [r for r in report["results"] if r["name"] == name]
        status = {r["method"]: str(r.get("score", {}).get("exact", "error")) for r in rows}
        route = rows[-1].get("output", {}).get("route", "error")
        lines.append(
            f"| {name} | {rows[0]['split']} | {status['native']} | {status['text']} | "
            f"{status['geometry']} | {status['header']} | {status['cascade']} / {route} |"
        )
    lines.extend(
        [
            "",
            "## Corpus spot checks",
            "",
            (
                "Senate and NICS use existing visual record annotations only; full matrices have no gold. "
                "The fractions below are annotated cells, not document accuracy."
            ),
            "",
            "| Input | Method | Spot-check cells | Open + extract ms | Missing / extra source tokens |",
            "|---|---|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {row['name']} | {row['method']} | {row['records']['correct']}/{row['records']['total']} | "
        f"{row['median_ms']:.3f} | {row['source']['missing_tokens']}/{row['source']['extra_tokens']} |"
        for row in report["results"]
        if row["name"] in RECORD_REFERENCES and "score" in row
    )
    lines.extend(
        [
            "",
            "## Header stop and retention evidence",
            "",
            "| Input | Method | Admission | Stop | Header IDs retained once |",
            "|---|---|---|---|---:|",
        ]
    )
    for row in report["results"]:
        if row["name"] not in {"corpus-senate-expenditures", "cascade-header-prose", "cascade-header-footnote"}:
            continue
        for detail in row.get("output", {}).get("header_diagnostics", []):
            header_ids = detail.get("header_ids", [])
            once = str(len(header_ids) == len(set(header_ids))) if header_ids else "n/a"
            lines.append(
                f"| {row['name']} | {row['method']} | {detail.get('admission', 'ungated')} | "
                f"{detail.get('stop', 'n/a')} | {once} |"
            )
    errors = [r for r in report["results"] if "error" in r]
    lines.extend(
        [
            "",
            f"Errors: {len(errors)}.",
            "",
            (
                "Exact cells preserve empty slots; relationship recall counts horizontal/vertical neighboring "
                "cell values, including empties. Missing/extra tokens compare output with the extracted text "
                "layer, not OCR gold. Geometry preserves unassigned words outside tables; source agreement "
                "does not establish correct ordering. Scanned inputs remain unavailable to geometry."
            ),
            "",
            (
                "Extra tokens on native merged tables can reflect intentional merged-cell expansion, not new "
                "source facts. The stricter header path retains labels once instead. Timing differences include "
                "different output work; these are complete-path measurements rather than interpreter-only costs."
            ),
            "",
            (
                "False-positive page counts use gold no-table controls. Excess table counts additionally include "
                "extra candidates on labeled pages with a real table, such as prose below a vector header. "
                "Unassigned source is HTML-escaped to preserve literal angle brackets and Markdown punctuation."
            ),
            "",
            (
                "Next tests: independently labeled partial-rule reports; numerical multicolumn prose with "
                "short keys; multiple tables beside prose; wrapped descriptions with blank record keys; "
                "merged headers under right-angle rotations; dashed/broken rules with irregular joins; "
                "duplicate and overlapping source words. The stricter handoff assumes one dominant right-angle "
                "baseline; mixed directions, vertical writing and unrelated document families need separate "
                "abstention and correctness evaluation before promoting this cascade."
            ),
            "",
            (
                "Complete inputs, per-method output, hashes, timings and errors are local under "
                "`bench/results/pdf-master-artifacts/geometry/`. No general fastest-method claim follows "
                "from this small synthetic study."
            ),
        ]
    )
    lines.extend(f"- {row['name']} / {row['method']}: {row['error']}" for row in errors)
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Run the bounded CPU study without dependency or model installation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    arguments = parser.parse_args()
    run(repeats=arguments.repeats)
    print(REPORT)


if __name__ == "__main__":
    main()
