"""Frozen source-only CPU table-routing screen over every authored DEV page.

Only scorer code sees authored references. Routing has no manifest, family, ID,
producer, reference, or target argument. This is an experiment, not an API default.
"""

# Artifacts retain heterogeneous public extraction observations.
# ruff: noqa: EM101, TRY003, PLC0415, ISC004, E501
from __future__ import annotations

import argparse
import json
import os
import platform
import time
import warnings
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

from bench.silver import canonical, guard_path, load_manifest, sha, verify_input, write_json
from bench.silver_structure import observed_table, prepare_targets, process_peak_rss, score_page

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ("none", "vector", "raw-text", "vector-veto", "vector-paint")
RULES = {
    "version": 1,
    "routes": ROUTES,
    "minimum_rows": 3,
    "minimum_columns": 2,
    "maximum_cell_tokens": 8,
    "maximum_cell_characters": 72,
    "minimum_numeric_columns_per_row": 2,
    "minimum_numeric_rows": 2,
    "paint_horizontal_support": 2,
    "paint_span_fraction": 0.7,
    "paint_tolerance_points": 2.0,
    "overlap_policy": "any positive-area overlap with retained vector table rejects text candidate",
    "priority": "retain complete vector tables unchanged before considering text candidates",
}


def overlaps(a: list[float], b: list[float]) -> bool:
    """Reject positive-area overlap, preserving retained grid ownership."""
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def compact_numeric(table: dict[str, Any]) -> bool:
    """Require compact cells and repeated multi-column numeric data, with prose veto."""
    if table["row_count"] < RULES["minimum_rows"] or table["col_count"] < RULES["minimum_columns"]:
        return False
    values = [value for row in table["values"] for value in row if value]
    if any(
        len(value.split()) > RULES["maximum_cell_tokens"]
        or len(value) > RULES["maximum_cell_characters"]
        or value.rstrip().endswith((".", "!", "?"))
        for value in values
    ):
        return False
    numeric_rows = sum(
        sum(any(char.isdecimal() for char in value) for value in row if value)
        >= RULES["minimum_numeric_columns_per_row"]
        for row in table["values"]
    )
    return numeric_rows >= RULES["minimum_numeric_rows"]


def paint_support(table: dict[str, Any], drawings: list[dict[str, Any]]) -> bool:
    """Require distinct long horizontal stroke positions within the candidate box."""
    x0, y0, x1, y1 = table["bbox"]
    tolerance = RULES["paint_tolerance_points"]
    positions = set()
    for drawing in drawings:
        if drawing["type"] not in ("s", "fs"):
            continue
        for item in drawing["items"]:
            if item[0] != "l":
                continue
            a, b = item[1:]
            if (
                abs(a.y - b.y) <= tolerance
                and y0 - tolerance <= a.y <= y1 + tolerance
                and min(a.x, b.x) >= x0 - tolerance
                and max(a.x, b.x) <= x1 + tolerance
                and abs(a.x - b.x) >= (x1 - x0) * RULES["paint_span_fraction"]
            ):
                positions.add(round(a.y / tolerance))
    return len(positions) >= RULES["paint_horizontal_support"]


def route_tables(
    route: str,
    vector: list[dict[str, Any]],
    text: list[dict[str, Any]],
    drawings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Route exclusively from native observed geometry, cell text and paint."""
    if route == "none":
        return []
    if route == "vector":
        return vector[:]
    if route == "raw-text":
        return text[:]
    if route not in ("vector-veto", "vector-paint"):
        raise ValueError("Unknown frozen route")
    retained = vector[:]
    for table in text:
        if any(overlaps(table["bbox"], old["bbox"]) for old in retained) or not compact_numeric(table):
            continue
        if route == "vector-paint" and not paint_support(table, drawings):
            continue
        retained.append(table)
    return retained


def totals(rows: list[dict[str, Any]], targets: dict[str, Any]) -> dict[str, Any]:
    """Keep failures in the full denominator and ownership targets fixed."""
    result = {}
    for route in ROUTES:
        selected = [row for row in rows if row["route"] == route]
        scores = [row["scores"] for row in selected if row["status"] == "ok"]
        result[route] = {
            "pages": len(targets["pages"]),
            "errors": len(targets["pages"]) - len(scores),
            **{
                key: sum(score[key] for score in scores)
                for key in (
                    "exact_page",
                    "false_positive_page",
                    "false_positive_tables",
                    "correct_owned_values",
                    "correct_cell_slots",
                    "detected_tables",
                )
            },
            "exact_cells": sum(score["exact_cells"] is True for score in scores),
            "exact_spans": sum(score["exact_spans"] is True for score in scores),
        }
    return result


def run(directory: Path, summary_path: Path = ROOT / "bench/results/corpus-routes.md") -> dict[str, Any]:
    """Freeze route configuration before targets, then retain complete observed evidence."""
    import pylopdf

    directory = guard_path(directory)
    runs = directory / "corpus-route-runs"
    runs.mkdir(exist_ok=True)
    output = Path(mkdtemp(prefix=time.strftime("%Y%m%dT%H%M%S-", time.gmtime()), dir=runs))
    write_json(output / "frozen-rules.json", RULES)
    runner_hash = sha(Path(__file__).read_bytes())
    write_json(output / "freeze.json", {"rules_sha256": sha(canonical(RULES)), "runner_sha256": runner_hash})
    targets = prepare_targets(directory)
    target_map = {(page["id"], page["page_number"]): page for page in targets["pages"]}
    manifest = load_manifest(directory)
    rows = []
    start, cpu = time.perf_counter(), time.process_time()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for record in manifest["cases"]:
            with pylopdf.open(verify_input(directory, record)) as document:
                for number, page in enumerate(document):
                    began, began_cpu = time.perf_counter(), time.process_time()
                    try:
                        vector = [observed_table(table) for table in page.find_tables().tables]
                        text = [observed_table(table) for table in page.find_tables(strategy="text").tables]
                        drawings = page.get_drawings()
                        evidence_ms = 1000 * (time.perf_counter() - began)
                        evidence_cpu_ms = 1000 * (time.process_time() - began_cpu)
                        for route in ROUTES:
                            selected = route_tables(route, vector, text, drawings)
                            # Reference lookup happens only after source-only routing.
                            target = target_map[(record["id"], number)]
                            rows.append(
                                {
                                    "id": record["id"],
                                    "page_number": number,
                                    "family": target["family"],
                                    "route": route,
                                    "status": "ok",
                                    "observed": selected,
                                    "scores": score_page(target, selected),
                                    "shared_evidence_wall_ms": evidence_ms,
                                    "shared_evidence_cpu_ms": evidence_cpu_ms,
                                }
                            )
                    except Exception as exc:
                        rows.extend(
                            {
                                "id": record["id"],
                                "page_number": number,
                                "route": route,
                                "status": "error",
                                "error": str(exc),
                            }
                            for route in ROUTES
                        )
    wall, cpu_seconds = time.perf_counter() - start, time.process_time() - cpu
    peak, tool = process_peak_rss()
    summary = {
        "dataset_sha256": targets["dataset_sha256"],
        "documents": len(manifest["cases"]),
        "pages": len(targets["pages"]),
        "rules": RULES,
        "runner_sha256": runner_hash,
        "totals": totals(rows, targets),
        "run_directory": str(output),
        "warnings": sorted({str(w.message) for w in caught}),
        "resources": {
            "wall_seconds": wall,
            "cpu_seconds": cpu_seconds,
            "cpu_utilization_pct": 100 * cpu_seconds / wall,
            "peak_rss_bytes": peak,
            "tool": "perf_counter/process_time; " + tool,
            "sampling": "cumulative counters and OS high-water mark, no periodic sampling",
            "scope": "single current executable; sequential source verification, load, both detections, paint, routing, scoring; RSS includes target preparation/imports",
            "workers": 1,
            "logical_cpus": os.cpu_count(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "gpu": "unused",
            "remote_inference": "none",
        },
    }
    write_json(output / "summary.json", summary)
    write_json(output / "targets.json", targets)
    with (output / "pages.jsonl").open("w") as handle:
        for row in rows:
            handle.write(canonical(row).decode() + "\n")
    report = [
        "# DEV corpus source-only routing screen",
        "",
        f"{summary['documents']} documents / {summary['pages']} physical pages; fixed all-page denominator. "
        "Authored silver references are not independently reviewed gold. Scoring covers exact table cells, "
        "merged topology, unique intended-cell ownership and non-table false positives; no anchor metric.",
        "",
        "| Route | Exact pages / 125 | Exact cells / 10 | Exact spans / 10 | Owned / 140 | Non-table FP / 115 | Unmatched tables | Errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in summary["totals"].items():
        report.append(
            f"| {name} | {result['exact_page']}/125 | {result['exact_cells']}/10 | "
            f"{result['exact_spans']}/10 | {result['correct_owned_values']}/140 | "
            f"{result['false_positive_page']}/115 | {result['false_positive_tables']} | {result['errors']} |"
        )
    report += [
        "",
        "Rules were written to a hashed freeze artifact before preparing scorer targets. The router accepts "
        "only native vector/text table observations and native drawings, never IDs, families, producer groups or references. "
        "`none` is the minimal baseline; `vector` preserves the extraction default; `raw-text` exposes ambiguity. "
        "The two conditional routes preserve vectors, reject overlapping candidates, veto cells over 8 tokens/72 characters "
        "and sentence endings, and require two rows with digits in at least two cells. `vector-paint` additionally requires "
        "two distinct horizontal stroke positions spanning at least 70% of candidate width within a 2-point tolerance.",
        "",
        "False-positive pages by family (diagnostic grouping only; never routing inputs):",
    ]
    for route in ROUTES:
        families = {}
        for row in rows:
            if row["route"] == route and row["status"] == "ok" and row["scores"]["false_positive_page"]:
                families[row["family"]] = families.get(row["family"], 0) + 1
        report.append(f"- `{route}`: {json.dumps(families, sort_keys=True)}")
    report += [
        "",
        "The vector baseline already reaches the authored table ceiling. Conditional routes cannot establish "
        "borderless recall on this cohort: there are no positive authored borderless references. Gains over raw text "
        "are rejection gains; preserving 10 vector grids is not evidence of general layout improvement. Numeric content "
        "and compact cells can still appear in prose, forms or mathematical matrices. Next hypothesis: add independently "
        "reviewed borderless tables and aligned numeric-prose negatives to DEV, then test row/column ownership and prose "
        "reading order before expanding admission. No core default was changed.",
        "",
        f"One sequential CPU run: {wall:.3f}s wall, {cpu_seconds:.3f}s CPU, {100 * cpu_seconds / wall:.1f}% of one core, "
        f"peak current-exec RSS {peak} bytes. Measurement: {summary['resources']}. Evidence is shared across routes, "
        "so these are quality screens, not independent route performance comparisons. No provider charges.",
        "",
        f"Dataset SHA-256 `{targets['dataset_sha256']}`; rules SHA-256 `{sha(canonical(RULES))}`; "
        f"runner SHA-256 `{runner_hash}`. Complete observations, per-page errors and scores, frozen rules and authored "
        f"targets remain in ignored `{output}`.",
        "",
    ]
    summary_path.write_text("\n".join(report))
    return summary


def main() -> None:
    """Run the frozen DEV screen with an explicit dataset path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.directory), indent=2))


if __name__ == "__main__":
    main()
