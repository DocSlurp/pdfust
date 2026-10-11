"""Counterfactual scoring must preserve complete denominators and immutable preparation."""

import json
from pathlib import Path

import pytest
from bench import p003_resolution_composition_eval as evaluation
from bench.silver import sha


def test_external_authority_refused_before_source_access(tmp_path: Path) -> None:
    """Artifact content cannot authenticate its own helper or preparation."""
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "frozen.json").write_text("{}")
    authority = tmp_path / "authority.json"
    authority.write_text("{}")
    with pytest.raises(ValueError, match="Separately approved"):
        evaluation.prepare_context(prepared, authority, "0" * 64, "0" * 64, tmp_path / "absent-map", "0" * 64)


def test_wrong_preparation_refused_before_response_access(tmp_path: Path) -> None:
    """A changed control cannot inherit a materialized policy receipt."""
    (tmp_path / "frozen.json").write_text(json.dumps({"prepared_sha256": "wrong", "policy_count": 3}))
    with pytest.raises(ValueError, match="approved complete"):
        evaluation.verify_arm(tmp_path, {"prepared_sha256": "approved"})


def test_changed_results_refused_before_raw_replay(tmp_path: Path) -> None:
    """A caller must not manufacture a selected policy output."""
    (tmp_path / "results.json").write_text("[]")
    (tmp_path / "frozen.json").write_text(
        json.dumps(
            {
                "prepared_sha256": "approved",
                "policy_count": 3,
                "gold_read": False,
                "new_api_calls": 0,
                "case_receipts": 72,
                "results_sha256": sha(b"changed"),
            }
        )
    )
    with pytest.raises(ValueError, match="artifact changed"):
        evaluation.verify_arm(tmp_path, {"prepared_sha256": "approved"})


def test_full_denominator_and_single_original_charge() -> None:
    """Unresolved cases receive no label credit and costs are not multiplied by policies."""
    gold = {str(i): {"expected_choice": "same", "evidence_limitation": i >= 18} for i in range(24)}
    rows = [
        {
            "id": str(i),
            "kind": ("cell", "row", "wrap")[i // 8],
            "choice": "same" if i < 2 else "unresolved",
            "status": "classified" if i < 2 else "abstained",
        }
        for i in range(24)
    ]
    verified = {
        "input_arm": "test",
        "model": "test",
        "image_edge": 400,
        "actual_charges_once": {"effective_usd": 0.01},
        "results": [{"name": str(i), "policy": str(i), "rows": rows} for i in range(3)],
    }
    result = evaluation.score(verified, gold)
    assert result["actual_charges_once"] == {"effective_usd": 0.01}
    assert result["fresh_throughput"] is None
    assert result["hypothetical_cost_saving_usd"] is None
    assert len(result["policies"]) == 3
    for policy in result["policies"]:
        assert policy["scores"]["all_24"]["intended_count"] == 24
        assert policy["scores"]["all_24"]["author_label_matches"] == 2
        assert policy["scores"]["indeterminate_6"]["abstained"] == 6
    verified["results"][0]["rows"] = rows[:23]
    with pytest.raises(ValueError, match="24-case denominator"):
        evaluation.score(verified, gold)
