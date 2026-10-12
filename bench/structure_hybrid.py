"""Combine native tables, source-backed region recovery, and missing-text OCR."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pdfust
from bench.structure_core import geometry_tables, markdown_tables, render_tables, validate_patch
from bench.structure_native import header_guided_records, header_word_ids

if TYPE_CHECKING:
    from pathlib import Path

_MAX_HEADER_CHARS = 120


def contains(box: list[float], word: dict[str, Any], *, logical: bool = False) -> bool:
    """Assign a word by its centroid in one explicitly selected coordinate space."""
    bounds = word["logical_bbox" if logical else "bbox"]
    return box[0] <= (bounds[0] + bounds[2]) / 2 <= box[2] and box[1] <= (bounds[1] + bounds[3]) / 2 <= box[3]


def native_spans(table: pdfust.Table) -> list[list[int]]:
    """Recover rectangular spans from accepted native cell boxes and divider coordinates."""
    cells = [cell for cell in table.cells if cell is not None]
    xs = sorted({value for cell in cells for value in (cell.x0, cell.x1)})
    ys = sorted({value for cell in cells for value in (cell.y0, cell.y1)})
    if len(xs) != table.col_count + 1 or len(ys) != table.row_count + 1:
        return []
    spans = []
    for index, cell in enumerate(table.cells):
        if cell is None:
            continue
        rowspan = sum(cell.y0 - 0.01 <= y < cell.y1 - 0.01 for y in ys)
        colspan = sum(cell.x0 - 0.01 <= x < cell.x1 - 0.01 for x in xs)
        if rowspan > 1 or colspan > 1:
            spans.append([index // table.col_count, index % table.col_count, rowspan, colspan])
    return spans


def recover(bundle: dict[str, Any], directory: Path, ocr: pdfust.OcrEngine, *, bullets: bool) -> dict[str, Any]:
    """Reuse verified layout predictions; prefer vector evidence before inferred rows."""
    from bench.structure import REPORT  # noqa: PLC0415 - avoid the runner import cycle.

    prior = next(
        result
        for result in json.loads(REPORT.read_text())["results"]
        if result["case"] == bundle["name"] and result["adapter"] == "yolo-normalized-geometry-wrapped"
    )
    if prior["sha256"] != bundle["sha256"] or "error" in prior:
        msg = "hybrid recovery requires matching successful normalized YOLO provenance"
        raise ValueError(msg)
    detections = json.loads((directory / "yolo-normalized-geometry-wrapped-detections.json").read_text())
    words = bundle["words"]
    recognized = []
    matrices = []
    spans: list[list[list[int]]] = []
    covered: set[str] = set()
    choices = []
    retained_headers: set[str] = set()
    with pdfust.open(directory / "input.pdf") as document:
        page = document[0]
        if not words:
            recognized = page.apply_ocr(dpi=150, engine=ocr)
            words = [
                {"id": f"p0w{i}", "text": word[4], "bbox": list(word[:4]), "logical_bbox": list(word[:4])}
                for i, word in enumerate(page.get_text("words"))
            ]
            choices.append("missing-text OCR at 150 dpi; no automatic scan orientation")
        tables = page.find_tables()
        guided = header_guided_records(page, words)
        if guided:
            matrices.extend(guided)
            spans.extend([] for _ in guided)
            choices.append("native header-guided records")
            for table in tables:
                box = [table.bbox.x0, table.bbox.y0, table.bbox.x1, page.rect.y1]
                covered.update(word["id"] for word in words if contains(box, word))
        else:
            for table in tables:
                matrix = markdown_tables(table.to_markdown())[0]
                unresolved = max(map(len, matrix[0])) > _MAX_HEADER_CHARS
                if unresolved:
                    retained_headers.update(header_word_ids(table, words))
                    matrix = [[value or "" for value in row] for row in table.extract() if any(row)]
                    matrix[0] = [f"Column {column + 1}" for column in range(table.col_count)]
                matrices.append(matrix)
                spans.append([] if unresolved else native_spans(table))
                choices.append("native vector cells with neutral labels" if unresolved else "native vector cells")
                box = [table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1]
                covered.update(word["id"] for word in words if contains(box, word))
    for region in detections:
        if region["label"].lower() != "table":
            continue
        selected = [
            word for word in words if word["id"] not in covered and contains(region["bbox"], word, logical=True)
        ]
        payload = {"tables": [{"rows": table} for table in geometry_tables(selected, wrapped=True)]}
        inferred, used = validate_patch(payload, words)
        matrices.extend(inferred)
        spans.extend([] for _ in inferred)
        covered.update(used)
        if inferred:
            choices.append("normalized YOLO-gated physical rows with wrapped continuations")
    covered.difference_update(retained_headers)
    return {
        "markdown": render_tables(matrices, bullets=bullets, spans=spans)
        + "\n\n"
        + " ".join(word["text"] for word in words if word["id"] not in covered),
        "tables": matrices,
        "choices": choices,
        "recognized_words": len(recognized),
        "source_ids_covered": len(covered),
        "source_ids_total": len(words),
        "source_header_ids_retained": len(retained_headers),
        "detection_cost": "reuses normalized YOLO detections; excludes detector inference",
        "header_policy": "native header or neutral vector labels; inferred first row is unverified",
    }
