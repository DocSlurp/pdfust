"""Experimental record fallbacks grounded in existing vector table geometry."""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING, Any

from bench.structure_core import markdown_tables

if TYPE_CHECKING:
    import pdfust

_MAX_HEADER_CHARS = 120
_MAX_HEADER_ROWS = 3
_MIN_RECORD_COLUMNS = 3


def header_word_ids(table: pdfust.Table, words: list[dict[str, Any]]) -> set[str]:
    """Keep the original words when an unresolved first grid row gains neutral labels."""
    first = next((index for index, row in enumerate(table.extract()) if any(row)), 0)
    boxes = [cell for cell in table.cells[first * table.col_count : (first + 1) * table.col_count] if cell is not None]
    return {
        word["id"]
        for word in words
        if any(
            box.x0 <= (word["bbox"][0] + word["bbox"][2]) / 2 <= box.x1
            and box.y0 <= (word["bbox"][1] + word["bbox"][3]) / 2 <= box.y1
            for box in boxes
        )
    }


def unresolved_header_ids(page: pdfust.Page, words: list[dict[str, Any]]) -> set[str]:
    """Identify displaced source text without deduplicating repeated header labels."""
    retained = set()
    for table in page.find_tables():
        rows = [row for row in table.extract() if any(row)]
        if rows and max(len(value or "") for value in rows[0]) > _MAX_HEADER_CHARS:
            retained.update(header_word_ids(table, words))
    return retained


def native_records(page: pdfust.Page) -> list[list[list[str]]]:
    """Keep detected data cells, using neutral labels for unresolved large headers."""
    matrices = []
    for table in page.find_tables():
        rows = [[value or "" for value in row] for row in table.extract()]
        rows = [row for row in rows if any(row)]
        if not rows:
            continue
        if max(map(len, rows[0])) > _MAX_HEADER_CHARS:
            rows = [[f"Column {column + 1}" for column in range(table.col_count)], *rows[1:]]
        matrices.append(rows)
    return matrices


def header_guided_records(  # noqa: C901, PLR0912
    page: pdfust.Page,
    words: list[dict[str, Any]],
) -> list[list[list[str]]]:
    """Extend a complete vector header into source-backed records below it."""
    matrices = []
    for table in page.find_tables():
        if table.row_count > _MAX_HEADER_ROWS or table.col_count < _MIN_RECORD_COLUMNS:
            continue
        # The narrowest direct cell at each column provides its left boundary.
        lefts = []
        for column in range(table.col_count):
            boxes = [table.cells[row * table.col_count + column] for row in range(table.row_count)]
            present = [box for box in boxes if box is not None]
            if not present:
                break
            lefts.append(min(box.x0 for box in present))
        if len(lefts) != table.col_count:
            continue
        header_rows = markdown_tables(table.to_markdown())[0]
        headers = [
            " ".join(dict.fromkeys(row[column] for row in header_rows if row[column]))
            for column in range(table.col_count)
        ]
        selected = [
            word
            for word in words
            if table.bbox.y1 < word["bbox"][1]
            and table.bbox.x0 <= (word["bbox"][0] + word["bbox"][2]) / 2 <= table.bbox.x1
        ]
        if not selected:
            continue
        height = statistics.median(word["bbox"][3] - word["bbox"][1] for word in selected)
        physical: list[list[dict[str, Any]]] = []
        for word in sorted(selected, key=lambda item: (item["bbox"][1], item["bbox"][0])):
            if not physical or abs(word["bbox"][1] - physical[-1][0]["bbox"][1]) > height * 0.45:
                physical.append([])
            physical[-1].append(word)
        records: list[list[list[str]]] = []
        for line in physical:
            cells: list[list[str]] = [[] for _ in lefts]
            for word in sorted(line, key=lambda item: item["bbox"][0]):
                center = (word["bbox"][0] + word["bbox"][2]) / 2
                column = max(0, sum(center >= left for left in lefts) - 1)
                cells[column].append(word["text"])
            # A line with only descriptive continuation belongs to the previous record.
            identity_columns = min(_MIN_RECORD_COLUMNS, len(cells) - 2)
            if records and not any(cells[:identity_columns]) and not cells[-1]:
                for column, cell in enumerate(cells):
                    records[-1][column].extend(cell)
            else:
                records.append(cells)
        matrices.append([headers, *[[" ".join(cell) for cell in record] for record in records]])
    return matrices
