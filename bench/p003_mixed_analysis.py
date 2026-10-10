"""Secondary admission and page-sensitivity diagnostics for verified P003 mixed runs."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

DENSE_IDS = frozenset({"p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"})


def ranking_admission(report: dict[str, Any]) -> dict[str, Any]:
    """Distinguish genuine duplicate pools from historical pending-status mislabeling."""
    pages = Counter(p.get("ranking_status") for p in report["results"])
    regions = [r for p in report["results"] for r in p.get("ranking_regions", [])]
    region_statuses = Counter(r["ranking_status"] for r in regions)
    duplicates = sum(len(r["pool"]["candidates"]) == 1 for r in regions)
    mislabeled = sum(
        r["ranking_status"] == "not_applicable_duplicates" and len(r["pool"]["candidates"]) > 1 for r in regions
    )
    errors = [e for p in report["results"] for e in p.get("ranking_errors", [])]
    return {
        "page_status_counts": dict(pages),
        "region_status_counts": dict(region_statuses),
        "genuine_duplicate_pools": duplicates,
        "distinct_pools_mislabeled_duplicates": mislabeled,
        "returned_calls": sum(len(p.get("ranking_calls", [])) for p in report["results"]),
        "ledger_attempts": report["incremental_ranking"]["ledger_attempts"],
        "evidence_capacity_refusals": sum(e["error_type"] == "EvidenceCapacityError" for e in errors),
        "input_admission_refusals": sum(
            e.get("detail") == "Request exceeds frozen model/input admission" for e in errors
        ),
        "other_error_types": dict(Counter(e["error_type"] for e in errors if e.get("detail") is None)),
        "scope": "Archived status observations; distinct pending pools are not interpreted as duplicate-only admission",
    }


def page_sensitivity(run: dict[str, Any], excluded: frozenset[str] = DENSE_IDS) -> dict[str, Any]:
    """Keep all other pages, failures and negatives in a predeclared secondary denominator."""
    pages = [p for p in run["page_scores"] if p["id"] not in excluded]
    positives = [p for p in pages if p["positive_page"]]
    dense = [p for p in run["page_scores"] if p["id"] in excluded]
    totals = {
        key: sum(p[key] for p in pages)
        for key in (
            "strict_exact_cells",
            "expected_cells",
            "expected_tables",
            "complete_tables",
            "missing_tables",
            "false_positive_tables",
            "false_positive_page",
            "error",
            "negative_page",
        )
    }
    return {
        "retained_pages": len(pages),
        "positive_pages": len(positives),
        "totals": totals,
        "positive_macro_strict_recall": statistics.mean(
            p["strict_exact_cells"] / p["expected_cells"] for p in positives
        )
        if positives
        else None,
        "positive_macro_complete_recall": statistics.mean(
            p["complete_tables"] / p["expected_tables"] for p in positives
        )
        if positives
        else None,
        "dense_strict_cells": sum(p["strict_exact_cells"] for p in dense),
        "dense_expected_cells": sum(p["expected_cells"] for p in dense),
        "excluded_ids": sorted(excluded),
        "scope": "Secondary predeclared dense-page sensitivity; full original denominator remains primary",
    }
