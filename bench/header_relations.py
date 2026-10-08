"""CPU-only, source-preserving header inference experiment; no public API changes.

Run ``.venv/bin/python -m bench.header_relations``. Gold bands and anchor edges
come from fixture declarations, never inferred text. No fitting or model runtime.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import statistics
import time
from dataclasses import asdict, dataclass
from functools import partial
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pylopdf
from bench.feature_cases import ROOT, page_pdf, text_op
from pylopdf import pylopdf_core

if TYPE_CHECKING:
    from pylopdf._spatial import SpatialTable

# Long report prose stays in a single string for reproducible Markdown.
# ruff: noqa: E501

_MIN_BODY_SUPPORT = 3
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts/headers"
REPORT = ROOT / "bench/results/header-relations.md"


@dataclass(frozen=True)
class Decision:
    """A band hypothesis or abstention with retained alternatives."""

    header_rows: int | None
    row_header_columns: int
    reason: str
    candidates: tuple[int, ...] = ()


@dataclass(frozen=True)
class Edge:
    """One relationship between existing source cells."""

    kind: str
    source_id: int
    target_id: int
    column: int


def lexical_type(text: str) -> str:
    """Classify bounded fixture lexical forms without changing text."""
    text = text.strip()
    if not text:
        return "empty"
    if re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", text):
        return "date"
    if re.fullmatch(r"[$+-]?[\d,]+(?:\.\d+)?%?", text):
        return "number"
    if re.fullmatch(r"\([^()]{1,12}\)|%|kg|USD|ms|mm", text):
        return "unit"
    return "text"


def infer_bands(table: SpatialTable) -> Decision:
    """Conservative lexical contrasts and merged-span constraints, not truth."""
    by_id = {cell.id: cell for cell in table.cells}
    rows = [
        [by_id[index] for index in table.slots[r * table.col_count : (r + 1) * table.col_count]]
        for r in range(table.row_count)
    ]
    if table.row_count < _MIN_BODY_SUPPORT:
        return Decision(None, 0, "insufficient body support")
    if all(lexical_type(cell.text) in {"number", "date", "empty"} for cell in table.cells):
        return Decision(None, 0, "numeric/date header and headerless grid indistinguishable", (0, 1))
    candidates = []
    for band in range(1, min(4, table.row_count - 1)):
        if any(cell.row < band < cell.row + cell.row_span for cell in table.cells):
            continue
        if any(lexical_type(cell.text) not in {"text", "unit", "empty"} for row in rows[:band] for cell in row):
            continue
        # A unit-only row or merged top parent can justify another header level.
        if band > 1 and not (
            any(cell.row < band - 1 and cell.column_span > 1 for cell in table.cells)
            or all(lexical_type(c.text) == "unit" for c in rows[band - 1][1:])
        ):
            continue
        body = rows[band:]
        typed_columns = sum(
            all(lexical_type(row[c].text) in {"number", "date"} for row in body) for c in range(table.col_count)
        )
        if typed_columns >= max(1, table.col_count - 1):
            candidates.append(band)
    if len(candidates) != 1:
        return Decision(None, 0, "ambiguous or unsupported header band", tuple(candidates))
    band = candidates[0]
    # Row scope is only declared for recognized stubs; other textual columns
    # remain ordinary data. This narrow vocabulary is an experimental policy.
    stub = rows[band - 1][0].text.strip().casefold()
    row_headers = int(
        stub in {"metric", "category", "item"}
        and all(lexical_type(row[0].text) == "text" for row in rows[band:])
        and all(row[0].column_span == 1 for row in rows[band:])
    )
    return Decision(band, row_headers, "unique span/type contrast", tuple(candidates))


def strict_bands(table: SpatialTable, *, declared: tuple[int, int] | None = None) -> Decision:
    """Require caller role evidence; feature-only heuristics cannot prove scope."""
    if declared is None:
        return Decision(None, 0, "independent role evidence required")
    headers, rows = declared
    table.records(header_rows=headers, row_header_columns=rows)
    return Decision(headers, rows, "explicit caller role declaration")


def first_row(table: SpatialTable) -> Decision:
    """Use the first row whenever it does not cut a merged cell."""
    try:
        table.records(header_rows=1)
    except pylopdf.PdfError:
        return Decision(None, 0, "first row cuts merged cell")
    return Decision(1, 0, "first-row baseline")


def graph(table: SpatialTable, decision: Decision) -> tuple[Edge, ...]:
    """Materialize unchanged source-cell IDs, including ancestry and row scope."""
    if decision.header_rows is None:
        return ()
    edges = set()
    for row in table.records(header_rows=decision.header_rows, row_header_columns=decision.row_header_columns):
        for field in row:
            for parent, child in pairwise(field.headers):
                edges.add(Edge("ancestor", parent.id, child.id, field.column))
            for header in field.headers:
                edges.add(Edge("column", header.id, field.cell.id, field.column))
            for header in field.row_headers:
                edges.add(Edge("row", header.id, field.cell.id, field.column))
    return tuple(sorted(edges, key=lambda edge: (edge.kind, edge.source_id, edge.target_id, edge.column)))


@dataclass(frozen=True)
class Fixture:
    """An independently declared logical table and intended header scope."""

    family: str
    cells: tuple[tuple[int, int, int, int, str], ...]
    rows: int
    columns: int
    header_rows: int
    row_headers: int = 0


def fixtures() -> list[Fixture]:
    """Declare structural families and semantic control cases independently."""
    result = []

    def add(
        name: str,
        matrix: list[list[str]],
        headers: int,
        row_headers: int = 0,
        merges: tuple[tuple[int, int, int, int], ...] = (),
    ) -> None:
        covered: set[tuple[int, int]] = set()
        cells = []
        spans = {(r, c): (rs, cs) for r, c, rs, cs in merges}
        for r, row in enumerate(matrix):
            for c, value in enumerate(row):
                if (r, c) in covered:
                    continue
                rs, cs = spans.get((r, c), (1, 1))
                covered.update((rr, cc) for rr in range(r, r + rs) for cc in range(c, c + cs))
                cells.append((r, c, rs, cs, value))
        result.append(Fixture(name, tuple(cells), len(matrix), len(matrix[0]), headers, row_headers))

    add("simple", [["Name", "Revenue", "Cost"], ["Oak", "100", "60"], ["Elm", "110", "65"]], 1)
    add(
        "hierarchy",
        [["Name", "Finance", ""], ["", "Revenue", "Cost"], ["Oak", "100", "60"], ["Elm", "110", "65"]],
        2,
        merges=((0, 0, 2, 1), (0, 1, 1, 2)),
    )
    add(
        "repeated-labels",
        [
            ["Name", "East", "", "West", ""],
            ["", "Count", "Rate", "Count", "Rate"],
            ["Oak", "10", "20", "30", "40"],
            ["Elm", "11", "21", "31", "41"],
        ],
        2,
        merges=((0, 0, 2, 1), (0, 1, 1, 2), (0, 3, 1, 2)),
    )
    add(
        "units",
        [["Name", "Mass", "Time"], ["", "kg", "ms"], ["Oak", "10", "20"], ["Elm", "11", "21"]],
        2,
        merges=((0, 0, 2, 1),),
    )
    add("numeric-headers", [["2023", "2024", "2025"], ["10", "20", "30"], ["11", "21", "31"]], 1)
    add("date-headers", [["2023-01-01", "2024-01-01"], ["10", "20"], ["11", "21"]], 1)
    add("headerless-numeric", [["10", "20", "30"], ["11", "21", "31"], ["12", "22", "32"]], 0)
    add("mixed-prose", [["Oak", "Pending", "10"], ["Elm", "Paid", "20"], ["Ash", "Pending", "30"]], 0)
    add("row-headings", [["Metric", "East", "West"], ["Revenue", "10", "20"], ["Cost", "11", "21"]], 1, 1)
    add("all-text-headers", [["Name", "Status"], ["Oak", "Pending"], ["Elm", "Paid"]], 1)
    add("headerless-mixed", [["Oak", "10", "20"], ["Elm", "11", "21"], ["Ash", "12", "22"]], 0)
    add("headerless-type-shift", [["Oak", "North", "West"], ["Elm", "11", "21"], ["Ash", "12", "22"]], 0)
    add("type-shift-declared-header", [["Oak", "North", "West"], ["Elm", "11", "21"], ["Ash", "12", "22"]], 1)
    add(
        "three-level",
        [
            ["Name", "Finance", ""],
            ["", "Actual", "Forecast"],
            ["", "USD", "USD"],
            ["Oak", "10", "20"],
            ["Elm", "11", "21"],
        ],
        3,
        merges=((0, 0, 3, 1), (0, 1, 1, 2)),
    )
    return result


def _coalesce_rules(ops: list[str]) -> list[str]:
    """Join adjacent collinear segments without changing painted geometry."""
    groups: dict[tuple[bool, float], list[tuple[float, float]]] = {}
    for op in ops:
        parts = op.split()
        x0, y0, x1, y1 = map(float, (parts[0], parts[1], parts[3], parts[4]))
        horizontal = y0 == y1
        key = (horizontal, y0 if horizontal else x0)
        groups.setdefault(key, []).append((x0, x1) if horizontal else (min(y0, y1), max(y0, y1)))
    ops = []
    for (horizontal, axis), spans in groups.items():
        merged: list[tuple[float, float]] = []
        for start, end in sorted(spans):
            if merged and start == merged[-1][1]:
                merged[-1] = (merged[-1][0], end)
            else:
                merged.append((start, end))
        for start, end in merged:
            ops.append(f"{start} {axis} m {end} {axis} l S" if horizontal else f"{axis} {start} m {axis} {end} l S")
    return ops


def fixture_pdf(fixture: Fixture, scale: float = 1, rotation: int = 0, *, coalesce: bool = True) -> bytes:
    """Generate ruled PDF cells from declared spans and display placement."""
    left, top, width, height = 40, 740, 105 * scale, 30 * scale
    anchor = {
        (rr, cc): (r, c) for r, c, rs, cs, _ in fixture.cells for rr in range(r, r + rs) for cc in range(c, c + cs)
    }
    ops = []
    for r in range(fixture.rows + 1):
        for c in range(fixture.columns):
            if r in (0, fixture.rows) or anchor[r - 1, c] != anchor[r, c]:
                x, y = left + c * width, top - r * height
                ops.append(f"{x} {y} m {x + width} {y} l S")
    for c in range(fixture.columns + 1):
        for r in range(fixture.rows):
            if c in (0, fixture.columns) or anchor[r, c - 1] != anchor[r, c]:
                x, y = left + c * width, top - r * height
                ops.append(f"{x} {y} m {x} {y - height} l S")
    if coalesce:
        ops = _coalesce_rules(ops)
    ops.extend(
        text_op(value, left + c * width + 4, top - r * height - 19 * scale, size=8 * scale)
        for r, c, _, _, value in fixture.cells
        if value
    )
    return page_pdf("\n".join(ops), extra_page=f"/Rotate {rotation}")


def gold_edges(fixture: Fixture) -> set[tuple[str, tuple[int, int], tuple[int, int], int]]:
    """Derive expected edges from declared cell containment and header scope."""
    # Declared spatial containment produces gold independently of records().
    edges = set()
    for r in range(fixture.header_rows, fixture.rows):
        for c in range(fixture.row_headers, fixture.columns):
            value = next((rr, cc) for rr, cc, rs, cs, _ in fixture.cells if rr <= r < rr + rs and cc <= c < cc + cs)
            headers = [
                (rr, cc) for rr, cc, rs, cs, _ in fixture.cells if rr < fixture.header_rows and cc <= c < cc + cs
            ]
            for header in headers:
                edges.add(("column", header, value, c))
            for parent, child in pairwise(headers):
                edges.add(("ancestor", parent, child, c))
            for rr, cc, rs, _, _ in fixture.cells:
                if rr <= r < rr + rs and cc < fixture.row_headers:
                    edges.add(("row", (rr, cc), value, c))
    return edges


def normalized_edges(table: SpatialTable, edges: tuple[Edge, ...]) -> set[tuple]:
    """Translate retained source IDs into independently checkable anchors."""
    anchors = {cell.id: (cell.row, cell.column) for cell in table.cells}
    return {(e.kind, anchors[e.source_id], anchors[e.target_id], e.column) for e in edges}


def _encoding_audit() -> list[dict[str, Any]]:
    """Retain same-pixel fragmented and coalesced three-level grids."""
    encodings: list[dict[str, Any]] = []
    three_level = next(f for f in fixtures() if f.family == "three-level")
    for scale in (0.8, 1.0):
        for rotation in (0, 90, 180, 270):
            forms = []
            for coalesce in (False, True):
                data = fixture_pdf(three_level, scale, rotation, coalesce=coalesce)
                path = ARTIFACTS / f"encoding-three-level-{scale}-{rotation}-{coalesce}.pdf"
                path.write_bytes(data)
                with pylopdf.open(stream=data) as doc:
                    layout = doc[0].get_layout()
                    pixels = doc[0].get_pixmap().samples
                forms.append(
                    {
                        "coalesced": coalesce,
                        "tables": len(layout.tables),
                        "pixel_sha256": hashlib.sha256(pixels).hexdigest(),
                        "input_sha256": hashlib.sha256(data).hexdigest(),
                    }
                )
            encodings.append({"scale": scale, "rotation": rotation, "forms": forms})
    return encodings


def run() -> None:  # noqa: C901 - experiment orchestration and report aggregation.
    """Preserve generated inputs and decisions, then write a compact report."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS.parent / ".gitignore").write_text("*\n", encoding="utf-8")
    results: list[dict[str, Any]] = []
    times: dict[str, list[float]] = {"first_row": [], "constraints": [], "strict_unhinted": [], "strict_declared": []}
    for fixture in fixtures():
        for scale in (0.8, 1.0):
            for rotation in (0, 90, 180, 270):
                name = f"{fixture.family}-{scale}-{rotation}"
                data = fixture_pdf(fixture, scale, rotation)
                (ARTIFACTS / f"{name}.pdf").write_bytes(data)
                start = time.perf_counter_ns()
                with pylopdf.open(stream=data) as doc:
                    layout = doc[0].get_layout()
                extraction_ms = (time.perf_counter_ns() - start) / 1e6
                gold = gold_edges(fixture)
                row: dict[str, Any] = {
                    "name": name,
                    "family": fixture.family,
                    "gold_band": [fixture.header_rows, fixture.row_headers],
                    "input_sha256": hashlib.sha256(data).hexdigest(),
                    "source_cells": [[asdict(c) for c in t.cells] for t in layout.tables],
                    "table_count": len(layout.tables),
                    "gold_edges": len(gold),
                    "extraction_ms": extraction_ms,
                    "methods": {},
                }
                for method, infer in (
                    ("first_row", first_row),
                    ("constraints", infer_bands),
                    ("strict_unhinted", strict_bands),
                    ("strict_declared", partial(strict_bands, declared=(fixture.header_rows, fixture.row_headers))),
                ):
                    predicted = set()
                    decision = Decision(None, 0, "table absent or multiple tables")
                    edges: tuple[Edge, ...] = ()
                    if len(layout.tables) == 1:
                        table = layout.tables[0]
                        # Check all extracted anchor text/spans against declarations, not just table count.
                        row["exact_cells"] = {
                            (c.row, c.column, c.row_span, c.column_span, c.text) for c in table.cells
                        } == set(fixture.cells)
                        start = time.perf_counter_ns()
                        decision = infer(table)
                        edges = graph(table, decision)
                        times[method].append((time.perf_counter_ns() - start) / 1e3)
                        predicted = normalized_edges(table, edges)
                    row["methods"][method] = {
                        "decision": asdict(decision),
                        "edges": [asdict(e) for e in edges],
                        "by_kind": {
                            kind: {
                                key: sum(e[0] == kind for e in group)
                                for key, group in (
                                    ("tp", predicted & gold),
                                    ("fp", predicted - gold),
                                    ("fn", gold - predicted),
                                )
                            }
                            for kind in ("column", "ancestor", "row")
                        },
                        "tp": len(predicted & gold),
                        "fp": len(predicted - gold),
                        "fn": len(gold - predicted),
                        "correct_band": (decision.header_rows, decision.row_header_columns)
                        == (fixture.header_rows, fixture.row_headers),
                    }
                results.append(row)
    corpus: list[dict[str, Any]] = []
    for name in ("senate-expenditures.pdf", "nics-background-checks-2015-11.pdf", "f1040.pdf"):
        with pylopdf.open(ROOT / "tests/assets/real_world" / name) as doc:
            layout = doc[0].get_layout()
        corpus.append(
            {
                "file": name,
                "tables": [
                    {
                        "rows": t.row_count,
                        "columns": t.col_count,
                        "decision": asdict(infer_bands(t)),
                        "cells": [asdict(c) for c in t.cells],
                    }
                    for t in layout.tables
                ],
            }
        )
    encodings = _encoding_audit()
    (ARTIFACTS / "decisions.json").write_text(
        json.dumps(
            {
                "environment": {
                    "python": platform.python_version(),
                    "platform": platform.platform(),
                    "pylopdf": pylopdf.__version__,
                    "native_sha256": hashlib.sha256(Path(pylopdf_core.__file__).read_bytes()).hexdigest(),
                    "extract_source_sha256": hashlib.sha256((ROOT / "rust/src/extract.rs").read_bytes()).hexdigest(),
                },
                "synthetic": results,
                "encoding_audit": encodings,
                "corpus": corpus,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    lines = [
        "# Experimental CPU header relationships",
        "",
        "Reproduce: `.venv/bin/python -m bench.header_relations`.",
        "",
        f"Loaded native extension SHA-256: `{hashlib.sha256(Path(pylopdf_core.__file__).read_bytes()).hexdigest()}`. Full Python/platform/library and Rust source provenance is retained in decisions.json.",
        "",
        "112 generated PDFs: 14 structural/semantic families × two scales × four right-angle rotations. No training, GPU, network, or inference service. Gold bands and edges are fixture declarations; text and spans are checked independently. Variants share templates and are not independent documents or held-out production accuracy.",
        "",
        "| Method | Correct bands | Abstained | Edge TP / FP / FN | Precision | Recall | Median inference + graph µs |",
        "| --- | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for method, timings in times.items():
        values = [r["methods"][method] for r in results]
        tp, fp, fn = (sum(v[key] for v in values) for key in ("tp", "fp", "fn"))
        precision = f"{tp / (tp + fp):.3f}" if tp + fp else "n/a"
        lines.append(
            f"| {method} | {sum(v['correct_band'] for v in values)}/112 | {sum(v['decision']['header_rows'] is None for v in values)} | {tp} / {fp} / {fn} | {precision} | {tp / max(1, tp + fn):.3f} | {statistics.median(timings):.1f} |"
        )
    lines += [
        "",
        "Strict-unhinted accepts no semantic edges without role evidence. Strict-declared is schema-assisted: fixture declarations are explicitly supplied as caller bands, so its numbers measure source relationship materialization, not header prediction accuracy. Headerless declarations accept a zero-header band. This coverage/false-edge tradeoff cannot be solved by score threshold tuning alone.",
        "",
        "| Method / edge kind | TP | FP | FN |",
        "| --- | ---: | ---: | ---: |",
    ]
    for method in times:
        for kind in ("column", "ancestor", "row"):
            counts = [sum(r["methods"][method]["by_kind"][kind][key] for r in results) for key in ("tp", "fp", "fn")]
            lines.append(f"| {method} / {kind} | {counts[0]} | {counts[1]} | {counts[2]} |")
    pairs = [r for r in results if r["family"] in {"headerless-type-shift", "type-shift-declared-header"}]
    if len({r["input_sha256"] for r in pairs}) != len(pairs) // 2:
        msg = "paired fixtures must have identical bytes"
        raise RuntimeError(msg)
    lines += [
        "",
        "Identifiability control: eight paired PDFs have identical bytes, words, cell boxes and geometry but different independently declared application roles (first row data versus header). Constraints make the same prediction on both, and therefore cannot be correct for both. Strict-unhinted abstains on both; explicit caller roles distinguish them. Input SHA-256 hashes and declarations are retained.",
    ]
    lines += [
        "",
        f"Exact extracted cells/spans: {sum(r.get('exact_cells', False) for r in results)}/112. Opening + first layout median: {statistics.median(r['extraction_ms'] for r in results):.3f} ms. Inference timings exclude extraction, use one local pass, and are not robust throughput measurements.",
        "",
        "Edges distinguish column-header/value, header ancestry, and row-header/value relationships; IDs refer only to retained snapshot cells. Merged headers and repeated labels retain separate IDs. No new cell text or geometry is synthesized. Abstention retains the complete original table.",
        "",
        "| Family | Constraint correct band | Constraint abstentions | Edge TP / FP / FN |",
        "| --- | ---: | ---: | --- |",
    ]
    for fixture in fixtures():
        values = [r["methods"]["constraints"] for r in results if r["family"] == fixture.family]
        counts = [sum(v[key] for v in values) for key in ("tp", "fp", "fn")]
        lines.append(
            f"| {fixture.family} | {sum(v['correct_band'] for v in values)}/8 | {sum(v['decision']['header_rows'] is None for v in values)}/8 | {' / '.join(map(str, counts))} |"
        )
    lines += [
        "",
        "Segmented/coalesced rule encoding audit after the connectivity fix: eight scale/rotation pairs produce identical RGBA pixel SHA-256 hashes. Both segmented and coalesced forms detect 8/8 native tables. Before the fix, segmented forms detected 0/8 and coalesced forms 8/8; pre-fix decisions and pixel hashes are retained in phase2-before-connectivity.json/md. This verifies representation invariance for these cases, not a header semantics improvement. Root cause: the middle left-border segment had no perpendicular intersection; joining touching/overlapping collinear fragments restores its component membership without changing any rule geometry.",
    ]
    lines += [
        "",
        "Numeric/year/date headers and headerless numeric data are observationally ambiguous under these rules; the method abstains. All-text headers lack type contrast. The original fragmented-rule three-level fixture yielded no table in eight variants. The outer left border was split at rows without an intersecting horizontal rule; the middle collinear segment became disconnected under the extractor’s perpendicular-intersection component grouping (rust/src/extract.rs). Coalescing contiguous collinear rules changes only drawing segmentation and restores the 5×3 table. Current semantic fixtures coalesce rules; the separate post-fix encoding audit and Python regressions test both representations. The first unconditional connectivity patch regressed Form 1040 by merging independent form-rule networks. The final repair preserves every accepted perpendicular grid, skips repair unions involving those roots, and admits repaired candidates only outside retained table bboxes. Existing Form 1040 regressions and parallel-decoration snapshot checks guard this restriction. The original segmentation failure is fixed by connecting parallel interval neighbors within the existing snap tolerance, while preserving all original segments. The original 104-case results are preserved in phase1.md/json, so the improved denominator is not silently compared as the same corpus. A headerless table whose first data row is textual but whose following rows contain numbers falsely looks like a header: this is the key known accepted error, not cured by source IDs. Row scope uses a narrow stub vocabulary and does not prove semantic scope. Text-only inputs, missing cells, and broad domain lexicons need independent evaluation.",
        "",
        "Corpus first-page audit (unscored for semantic edges):",
    ]
    for item in corpus:
        lines.append(
            f"- {item['file']}: {len(item['tables'])} native tables; "
            + "; ".join(f"{t['rows']}×{t['columns']}: {t['decision']['reason']}" for t in item["tables"])
        )
    lines += [
        "",
        "The existing corpus references check values, not independently annotated header ancestry. Senate has a ruled header with an unruled body; NICS has a large merged header. A header-only native grid does not supply full-document value relationships. No corpus edge accuracy is claimed. Existing structure-findings.md and spatial-latest.md already document these gaps; this run adds semantic edge scoring instead of repeating model experiments.",
        "",
        "Next experiments: annotate source-ID column scopes for complete Senate/NICS regions; evaluate independent unseen document families; add typography and separator evidence to distinguish a first data row; compare explicit application schema hints versus conservative abstention. Keep evidence and source text when header semantics remain ambiguous.",
        "",
        "Complete decisions, source cells, and generated PDFs remain in ignored `pdf-master-artifacts/headers/`. This is a benchmark prototype, not a default API policy.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    run()
