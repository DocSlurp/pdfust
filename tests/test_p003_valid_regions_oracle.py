"""The valid-region oracle selects complete frozen states and preserves unavailable pages."""

from typing import Any

import pytest
from bench import p003_valid_regions_oracle as oracle
from tests.test_p003_report import table


def test_oracle_ties_choose_lowest_origin_after_declared_quality_objective() -> None:
    target = {"id": "p", "tables": [table([["A", "B"]])]}
    choices = [
        ((0,), {"id": "p", "status": "ok", "tables": [table([["A", "wrong"]])]}),
        ((1,), {"id": "p", "status": "ok", "tables": [table([["A", "B"]])]}),
        ((2,), {"id": "p", "status": "ok", "tables": [table([["A", "B"]])]}),
    ]
    result = oracle.oracle_page(target, choices)
    assert result["origins"] == [1]
    assert result["score"]["strict_exact_cells"] == 2
    assert result["maximum_complete_tables"] == 1


def test_no_complete_composition_stays_missing() -> None:
    target = {"id": "p", "tables": [table([["A"]])]}
    result = oracle.oracle_page(target, [])
    assert result["selected"]["status"] == "missing"
    assert result["compositions"] == 0


def test_compositions_exclude_invalid_and_duplicate_states_and_atomic_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    page = {
        "id": "p",
        "crops": [
            {
                "attempts": [
                    {"valid": False, "baseline_index": 0},
                    {"valid": True, "baseline_index": 1, "canonical_json": "a"},
                    {"valid": True, "baseline_index": 2, "canonical_json": "a"},
                    {"valid": True, "baseline_index": 3, "canonical_json": "b"},
                ]
            }
        ],
    }
    attempted = []

    def compose(_page: dict[str, Any], selected: dict[int, int]) -> dict[str, Any]:
        attempted.append(selected[0])
        if selected[0] == 3:
            raise ValueError  # Simulate atomic composition rejection without retaining a partial state.
        return {"state": {"tables": []}}

    monkeypatch.setattr(oracle.admission, "compose_selection", compose)
    choices = oracle.compositions(page)
    assert attempted == [1, 3]
    assert [origins for origins, _ in choices] == [(1,)]
