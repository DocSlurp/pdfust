"""Offline token-pricing fallback and original accounting preservation tests."""

# JSON fixtures and mock provider usage intentionally retain heterogeneous values.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench.reprice_model_rates import aggregate, cohort, load, reprice, request_cost

PRICE = {"input": 1e-7, "output": 0.0}


def entry(index: int = 1, cost: float = 0, *, status: str = "provider-reported USD") -> dict[str, Any]:
    """Create a minimal retained request accounting observation."""
    return {"index": index, "accounted_usd": cost, "cost_status": status, "case_count": 1}


@pytest.mark.parametrize("reported", [0, None])
def test_zero_and_missing_fallback(reported: float | None) -> None:
    usage = {"input_tokens": 1000, "output_tokens": 0, "cost": reported}
    accounting = entry()
    if reported is None:
        accounting["accounted_usd"] = None
    result = request_cost(accounting, usage, PRICE)
    assert result["effective_usd"] == pytest.approx(0.0001)
    assert result["basis"] == "catalog estimate"
    assert result["reported_usd"] == reported


@pytest.mark.parametrize("usage", [{"cost": 0.002}, {"cost": 0}])
def test_positive_provider_cost_wins(usage: dict[str, Any]) -> None:
    result = request_cost(entry(cost=0.002), usage, PRICE)
    assert result["effective_usd"] == 0.002
    assert result["basis"] == "provider-reported USD"


def test_missing_tokens_unknown_and_reservations_not_spend() -> None:
    result = request_cost(entry(cost=0.3, status="reserved unknown charge"), {}, PRICE)
    assert result["effective_usd"] is None
    assert result["ledger_accounted_usd"] == 0.3


def test_native_and_chat_token_fields() -> None:
    result = request_cost(entry(), {"prompt_tokens": 10, "completion_tokens": 20}, {"input": 0.01, "output": 0.02})
    assert result["effective_usd"] == pytest.approx(0.5)


def test_index_dedup_and_unknown_not_partial_rate() -> None:
    request = {"entry": entry(), "usage": {"input_tokens": 1000, "output_tokens": 0, "cost": 0}}
    result = aggregate([request, request], PRICE)
    assert result["admitted_page_inputs"] == 1
    assert result["pages_per_usd"] == pytest.approx(10_000)
    assert aggregate([request, {"entry": entry(2)}], PRICE)["pages_per_usd"] is None


def test_relationship_cohort_only_reused_smoke(tmp_path: Path) -> None:
    model = "model/example"
    rows = [
        {**entry(i), "tag": f"{model}@resolved-b1/batch/{i:03d}", "response_file": "response.json"}
        for i in range(1, 96)
    ]
    rows += [
        {**entry(100), "tag": f"{model}@resolved/smoke/000", "response_file": "response.json"},
        {**entry(101), "tag": f"{model}@resolved/tagtest/000", "response_file": "response.json"},
        {**entry(102), "tag": f"controls/{model}@resolved-b1/batch/000", "response_file": "response.json"},
    ]
    (tmp_path / "response.json").write_text(json.dumps({"usage": {"input_tokens": 10, "output_tokens": 0}}))
    selected = cohort(tmp_path, model, "Relationships resolved-b1", rows)
    assert len(selected) == 96
    assert {r["entry"]["index"] for r in selected}.isdisjoint({101, 102})


def test_reprice_only_cost_cells_idempotently(tmp_path: Path) -> None:
    (tmp_path / "langfuse").mkdir()
    (tmp_path / "langfuse/catalog-prices.json").write_text(json.dumps({"fetched_at": 1, "prices": {"m": PRICE}}))
    ledger = {"requests": [{**entry(), "tag": "m@resolved-b1/batch/001", "response_file": "response.json"}]}
    original = json.dumps(ledger)
    (tmp_path / "ledger.json").write_text(original)
    (tmp_path / "response.json").write_text(
        json.dumps({"usage": {"input_tokens": 1000, "output_tokens": 0, "cost": 0}})
    )
    report = tmp_path / "report.md"
    report.write_text(
        "| m | Relationships resolved-b1 | $0 reported | 200.2 | 31/36 (86.1%) |\n"
        "| paid | Relationships resolved-b1 | 99 | 101 | unchanged |\n"
    )
    first = reprice(tmp_path, report)
    contents = report.read_text()
    assert "| ~10,000 | 200.2 | 31/36 (86.1%) |" in contents
    assert "| paid | Relationships resolved-b1 | 99 | 101 | unchanged |" in contents
    assert (tmp_path / "ledger.json").read_text() == original
    second = reprice(tmp_path, report)
    assert report.read_text() == contents
    assert first == second


def test_refuse_heldout_before_read(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Held-out"):
        load(tmp_path / "heldout-silver" / "never-created.json")


def test_published_cache_read_and_write_rates() -> None:
    usage = {
        "input_tokens": 1000,
        "output_tokens": 20,
        "cost": 0,
        "input_tokens_details": {"cached_tokens": 600, "cache_write_tokens": 100},
    }
    price = {"input": 1e-6, "output": 2e-6, "input_cache_read": 2e-7, "input_cache_write": 1.2e-6}
    result = request_cost(entry(), usage, price)
    assert result["effective_usd"] == pytest.approx(0.00058)
    assert result["estimated_components_usd"]["uncached_input"] == pytest.approx(0.0003)
    assert result["cache_read_counter_present"]
    assert result["cache_write_counter_present"]
    assert result["cache_assumption"] is None
    assert result["reported_usd"] == 0


def test_cache_read_missing_published_rate_is_unknown() -> None:
    usage = {
        "prompt_tokens": 1000,
        "completion_tokens": 0,
        "cost": 0,
        "prompt_tokens_details": {"cached_tokens": 500, "cache_write_tokens": 0},
    }
    result = request_cost(entry(), usage, PRICE)
    assert result["effective_usd"] is None
    assert result["missing_price_keys"] == ["input_cache_read"]
    assert result["known_components_usd"]["uncached_input"] == pytest.approx(0.00005)


def test_absent_cache_counters_are_explicitly_unverified() -> None:
    result = request_cost(entry(), {"input_tokens": 100, "output_tokens": 0}, PRICE)
    assert result["effective_usd"] == pytest.approx(0.00001)
    assert not result["cache_read_counter_present"]
    assert not result["cache_write_counter_present"]
    assert "unverified" in result["cache_assumption"]
    assert result["cache_status"] == "unreported"


@pytest.mark.parametrize(("read", "write"), [(101, 0), (60, 50), (-1, 0), (True, 0)])
def test_invalid_cache_counts_do_not_create_estimates(read: int, write: int) -> None:
    usage = {
        "input_tokens": 100,
        "output_tokens": 0,
        "cost": 0,
        "input_tokens_details": {"cached_tokens": read, "cache_write_tokens": write},
    }
    result = request_cost(entry(), usage, {**PRICE, "input_cache_read": 0, "input_cache_write": 0})
    assert result["effective_usd"] is None
    assert not result["cache_counters_valid"]
    assert result["basis"] == "unknown: invalid cache usage"
    # Invalid cache detail cannot override a separately observed positive actual charge.
    usage["cost"] = 0.001
    assert request_cost(entry(), usage, PRICE)["effective_usd"] == 0.001


def test_known_ledger_provider_zero_preserved_separately_from_estimate() -> None:
    accounting = {**entry(cost=0.0001, status="catalog estimate"), "provider_reported_usd": 0}
    result = request_cost(accounting, {"input_tokens": 1000, "output_tokens": 0}, PRICE)
    assert result["reported_usd"] == 0
    assert result["effective_usd"] == pytest.approx(0.0001)
    assert result["ledger_cost_status"] == "catalog estimate"
