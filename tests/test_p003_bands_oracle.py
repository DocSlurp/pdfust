"""Frozen band oracle preserves atomic rejection and bounded complete enumeration."""

from typing import Any

import pytest
from bench import p003_bands_oracle as oracle


def test_enumeration_rejects_atomic_failure_without_partial_output(monkeypatch: pytest.MonkeyPatch) -> None:
    page = {
        "id": "p",
        "page_viewport": [100, 100],
        "crops": [
            {"viewport": [50, 100], "alternatives": [{"canonical_json": '{"v":0}'}, {"canonical_json": '{"v":1}'}]},
            {"viewport": [50, 100], "alternatives": [{"canonical_json": '{"v":2}'}]},
        ],
    }
    attempted = []

    def compose(states: list[dict[str, Any]], _viewports: list[list[int]], _page: list[int]) -> dict[str, Any]:
        attempted.append([s["v"] for s in states])
        if states[0]["v"] == 1:
            raise ValueError
        return {"tables": []}

    monkeypatch.setattr(oracle.bands, "compose", compose)
    outcomes = oracle.enumerate_page(page)
    assert attempted == [[0, 2], [1, 2]]
    assert [indexes for indexes, _ in outcomes] == [(0, 0)]


def test_composition_bound_refuses_before_assembly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oracle.pools, "MAX_COMPOSITIONS", 1)
    page = {"crops": [{"alternatives": [{}, {}]}]}
    with pytest.raises(ValueError, match="bound exceeded"):
        oracle.enumerate_page(page)
