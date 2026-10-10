"""Offline optimistic complete-cell inventory bound; never inference evidence."""

# Frozen evaluation dictionaries have heterogeneous schemas.
# ruff: noqa: EM101, TRY003
from __future__ import annotations

from collections import Counter
from typing import Any

from bench.generalization_scoring import MAX_TABLES, _cells

SPEC = {
    "version": 1,
    "normalization": "Authoritative NFC plus collapsed Unicode whitespace; preserve case and punctuation",
    "unit": "Complete anchor-cell string, excluding merged covered slots",
    "matching": "Page-wide multiset intersection across all admitted tables; consume each duplicate once",
    "ignored": ["table identity", "row", "column", "span dimensions", "geometry"],
    "empty": "Report normalized empty anchors and their intersection separately",
    "failure": "Non-ok predictions contribute zero anchors, including retained successful prefixes",
    "purpose": "Optimistic offline placement-free bound; never primary score, inference evidence or routing",
}


def inventory(tables: list[dict[str, Any]]) -> Counter[str]:
    """Count validated complete normalized anchors without splitting or joining text."""
    if len(tables) > MAX_TABLES:
        raise ValueError("Too many tables")
    return Counter(value for table in tables for value in _cells(table).values())


def compare(target: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    """Consume page-wide duplicate strings once; retain separate empty-anchor counts."""
    expected = inventory(target.get("tables", []))
    admitted = prediction.get("status") == "ok"
    actual = inventory(prediction.get("tables", [])) if admitted else Counter()
    matches = expected & actual
    return {
        "id": target["id"],
        "admitted": admitted,
        "expected_nonempty": sum(expected.values()) - expected[""],
        "predicted_nonempty": sum(actual.values()) - actual[""],
        "matched_nonempty": sum(matches.values()) - matches[""],
        "expected_empty": expected[""],
        "predicted_empty": actual[""],
        "matched_empty": matches[""],
        "optimistic_total": sum(matches.values()),
    }
