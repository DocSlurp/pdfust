"""Keep reporter accounting categories separate without filling unknown charges."""

from bench.p003_progress_checkpoint import money


def test_reporter_money_separates_reported_estimated_and_reserved() -> None:
    """A reservation remains exposure and cannot become billed spend."""
    costs = money(
        [
            {"cost_status": "provider-reported USD", "accounted_usd": 2.0},
            {"cost_status": "catalog estimate", "accounted_usd": 0.1, "provider_reported_usd": 0},
            {"cost_status": "reserved", "accounted_usd": 0.3},
        ]
    )
    assert costs["ledger_classified_reported_usd"] == "2.0"
    assert costs["catalog_estimated_usd"] == "0.1"
    assert costs["unresolved_reserved_usd"] == "0.3"
    assert costs["known_accounted_usd"] == "2.4"


def test_reporter_unknown_charge_prevents_complete_budget_total() -> None:
    """Missing charge observations stay unknown rather than becoming zero."""
    costs = money([{"cost_status": "provider-reported USD"}])
    assert costs["unknown_amount_entries"] == 1
    assert costs["wave_remaining_usd"] is None
    assert costs["cumulative_remaining_usd"] is None
