"""Keep reporter accounting categories separate without filling unknown charges."""

from pathlib import Path

from bench.p003_progress_checkpoint import money, queue_summary


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


def test_unknown_cost_basis_does_not_become_reliable_budget() -> None:
    """An exposed ledger placeholder stays separate from a supported subtotal."""
    costs = money([{"cost_status": "unknown", "accounted_usd": 5.0}])
    assert costs["exposed_ledger_conservative_usd"] == "5.0"
    assert costs["known_accounted_usd"] == "0"
    assert costs["unknown_basis_entries"] == 1
    assert costs["wave_remaining_usd"] is None


def test_synthetic_questions_do_not_become_pdf_pages(tmp_path: Path) -> None:
    """Operational question counters preserve their own denominator and launch state."""
    queue = {
        "frozen_order": [1, 2],
        "arms": [
            {
                "name": "a",
                "kind": "synthetic_relations",
                "status": "completed",
                "intended_questions": 24,
                "attempted_questions": 24,
                "valid_returned_questions": 0,
                "question_status_counts": {"malformed_response": 24},
            },
            {"name": "b", "status": "starting"},
        ],
    }
    result = queue_summary(queue, tmp_path / "synthetic/status.json")
    assert "attempted_pdf_pages" not in result
    assert result["synthetic_question_counts"]["attempted_questions"] == 24
    assert result["question_status_counts"] == {"malformed_response": 24}
    assert result["starting_jobs"] == 1
