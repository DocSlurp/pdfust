"""Summarize matched cohorts without dropping unsuccessful model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def summarize(rows: list[dict[str, Any]], references: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Keep attempted failures in denominators; separate unsupported artifact replays."""
    totals: dict[str, Any] = {
        "attempted": len(rows),
        "unsupported": 0,
        "errors": 0,
        "truncated": 0,
        "positive_correct": 0,
        "positive_total": 0,
        "negative_correct": 0,
        "negative_total": 0,
        "cells_correct": 0,
        "cells_total": 0,
        "relations_correct": 0,
        "relations_total": 0,
        "relations_observed": 0,
        "records_correct": 0,
        "records_total": 0,
    }
    for row in rows:
        error = row.get("error", "")
        if row["adapter"].startswith("retained-") and (
            "identical single-page input" in error or error == "StopIteration: "
        ):
            totals["unsupported"] += 1
            continue
        totals["errors"] += bool(error)
        totals["truncated"] += bool(row.get("output", {}).get("truncated")) or any(
            generation.get("truncated") for generation in row.get("failed_generations", [])
        )
        reference = references[row["case"]]
        gold = reference.get("score", {})
        score = row.get("score", {})
        if gold.get("gold_available"):
            category = "positive" if gold["expected_tables"] else "negative"
            totals[category + "_total"] += 1
            totals[category + "_correct"] += bool(score.get("exact")) and not error
            totals["cells_total"] += gold.get("total_cells", 0)
            totals["cells_correct"] += score.get("correct_cells", 0) if not error else 0
            totals["relations_total"] += gold.get("relationship_expected", 0)
            totals["relations_correct"] += score.get("relationship_matches", 0) if not error else 0
            totals["relations_observed"] += score.get("relationship_observed", 0) if not error else 0
        totals["records_total"] += reference.get("record_checks", {}).get("total", 0)
        totals["records_correct"] += row.get("record_checks", {}).get("correct", 0) if not error else 0
    return totals


def fraction(correct: int, total: int) -> str:
    """Distinguish an untested cohort from a failed cohort."""
    return f"{correct}/{total}" if total else "—"


def main() -> None:
    """Write a compact comparison from immutable outputs and current scored reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=Path("bench/results/structure-latest.json"))
    parser.add_argument("--report", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, default=Path("bench/results/structure-comparison.md"))
    args = parser.parse_args()
    baseline = json.loads(args.reference.read_text())
    references = {row["case"]: row for row in baseline["results"] if row["adapter"] == "pdfust"}
    lines = [
        "# Structured recovery comparison",
        "",
        "These are exploratory results on the preserved study inputs, not held-out production accuracy.",
        "Each adapter's denominators describe its attempted cohort. Failed calls remain in the denominators.",
        "Unsupported retained Docling/Marker replays are listed separately and excluded from quality totals.",
        "Positive grids, negative controls, and visual corpus spot checks are separate measurements.",
        "Cell and relationship totals count the reference grid; spot checks do not cover a complete corpus page.",
        "See STRUCTURE_BENCHMARKS.md for timing, source-agreement, training, and provenance limitations.",
        "Truncated counts are lower bounds: older failed calls can lack generation metadata in the report.",
        "",
    ]
    for path in args.report:
        report_bytes = path.read_bytes()
        report = json.loads(report_bytes)
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in report["results"]:
            groups[row["adapter"]].append(row)
        lines += [
            f"## {path.stem}",
            "",
            f"Source report run: {report['metadata'].get('started_at', 'see detailed report')}",
            f"Snapshot SHA-256: `{hashlib.sha256(report_bytes).hexdigest()}`.",
            "",
            (
                "| Adapter | Calls | Unsupported | Positive exact | Negative exact | Cells | Relation recall "
                "| Precision | Corpus cells | Errors | Truncated |"
            ),
            "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |",
        ]
        for adapter, rows in groups.items():
            totals = summarize(rows, references)
            counts = [
                fraction(totals[key + "_correct"], totals[key + "_total"])
                for key in ("positive", "negative", "cells", "relations")
            ]
            counts += [
                fraction(totals["relations_correct"], totals["relations_observed"]),
                fraction(totals["records_correct"], totals["records_total"]),
            ]
            lines.append(
                f"| {adapter} | {totals['attempted']} | {totals['unsupported']} | "
                + " | ".join(counts)
                + f" | {totals['errors']} | {totals['truncated']} |"
            )
        lines.append("")
    args.output.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
