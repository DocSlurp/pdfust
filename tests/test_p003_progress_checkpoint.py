"""Keep reporter accounting categories separate without filling unknown charges."""

import json
from pathlib import Path

import pytest
from bench.p003_progress_checkpoint import checkpoint, money, queue_summary


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


@pytest.mark.parametrize(
    "kind",
    ["micro", "synthetic_relations", "synthetic_shared_context", "synthetic_resolution", "synthetic_rules_resolution"],
)
def test_synthetic_questions_do_not_become_pdf_pages(tmp_path: Path, kind: str) -> None:
    """Operational question counters preserve their own denominator and launch state."""
    queue = {
        "frozen_order": [1, 2],
        "arms": [
            {
                "name": "a",
                "kind": kind,
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


def test_coordinator_publication_receipt_does_not_claim_jobs_started(tmp_path: Path) -> None:
    """A running wrapper observation preserves publication precision and unknown jobs."""
    status = tmp_path / "status.json"
    ledger = tmp_path / "ledger.json"
    receipt = tmp_path / "coordinator.json"
    status.write_text(json.dumps({"arms": [], "frozen_order": []}))
    ledger.write_text(json.dumps({"requests": []}))
    receipt.write_text(
        json.dumps(
            {
                "coordinator_last_published_utc": "2026-10-11T00:24Z",
                "publication_precision": "Approximate minute",
                "next_coordinator_publication_deadline_utc": "2026-10-11T00:29:00Z",
                "service_observations": [{"name": "shared56 wrapper", "state": "running"}],
            }
        )
    )
    report = checkpoint([status], ledger, tmp_path / "reports", ["shared56=56"], receipt)
    snapshot = json.loads(report.with_suffix(".json").read_text())
    assert snapshot["coordinator_last_published_utc"] == "2026-10-11T00:24Z"
    assert snapshot["next_coordinator_publication_deadline_utc"] == "2026-10-11T00:29:00Z"
    assert snapshot["plans"][0]["required"] == 56
    assert "Job status not observed" in report.read_text()


def test_synthetic_alias_audit_counts_preserve_original_scope(tmp_path: Path) -> None:
    """Synthetic audit receipts must not disappear behind table-evaluation naming."""
    arm = tmp_path / "synthetic" / "a"
    arm.mkdir(parents=True)
    (arm / "synthetic-alias-evaluation.json").write_text(
        json.dumps(
            {
                "original_verified": {"report_sha256": "a" * 64},
                "secondary_verified": {"report_sha256": "b" * 64, "scope": "Secondary alias replay"},
            }
        )
    )
    queue = {"frozen_order": [1], "arms": [{"name": "a", "kind": "synthetic_relations", "status": "completed"}]}
    result = queue_summary(queue, arm.parent / "status.json")
    assert result["synthetic_recorded_original_verified_jobs"] == 1
    assert result["synthetic_recorded_secondary_verified_jobs"] == 1
    assert result["synthetic_independent_alias_audits"][0]["secondary_scope"] == "Secondary alias replay"


@pytest.mark.parametrize(
    ("kind", "filename"),
    [
        ("synthetic_shared_context", "synthetic-shared-alias-evaluation.json"),
        ("synthetic_resolution", "synthetic-resolution-evaluation.json"),
        ("synthetic_rules_resolution", "synthetic-rules-resolution-evaluation.json"),
    ],
)
def test_question_audit_uses_its_own_receipt_filename(tmp_path: Path, kind: str, filename: str) -> None:
    """Question verification must not be counted as PDF table quality."""
    arm = tmp_path / "shared" / "a"
    arm.mkdir(parents=True)
    (arm / filename).write_text(
        json.dumps(
            {
                "original_verified": {"report_sha256": "a" * 64},
                "secondary_verified": {"report_sha256": "b" * 64, "scope": "Shared all24 relation questions"},
            }
        )
    )
    queue = {"frozen_order": [1], "arms": [{"name": "a", "kind": kind, "status": "completed"}]}
    result = queue_summary(queue, arm.parent / "status.json")
    assert result["synthetic_recorded_original_verified_jobs"] == 1
    assert "attempted_pdf_pages" not in result
    assert result["synthetic_independent_alias_audits"][0]["path"].endswith(filename)
