"""Geometry evaluation keeps empty pages and every frozen treatment in the denominator."""

from copy import deepcopy
from typing import Any

import pytest
from bench.p003_structure_evaluation import placement_inventory


def complete_report() -> dict[str, Any]:
    return {
        "rows": [
            {"id": identifier, "threshold": threshold, "policy": policy, "tables": 0}
            for identifier in ("positive", "negative")
            for threshold in (0.3, 0.5)
            for policy in ("center", "overlap_margin")
        ]
    }


def test_complete_inventory_retains_empty_negative_page() -> None:
    report = complete_report()
    rows = placement_inventory(report, ["positive", "negative"], [0.3, 0.5], ["center", "overlap_margin"])
    assert len(rows) == 8
    assert rows[("negative", 0.5, "center")]["tables"] == 0


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "different_policy", "unknown_page"])
def test_inventory_rejects_changing_denominator(mutation: str) -> None:
    report = deepcopy(complete_report())
    if mutation == "missing":
        report["rows"].pop()
    elif mutation == "duplicate":
        report["rows"].append(deepcopy(report["rows"][0]))
    elif mutation == "different_policy":
        report["rows"][0]["policy"] = "posthoc_best"
    else:
        report["rows"][0]["id"] = "different-page"
    with pytest.raises(ValueError, match="inventory"):
        placement_inventory(report, ["positive", "negative"], [0.3, 0.5], ["center", "overlap_margin"])
