"""Denominator and provenance checks for offline composition scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench import p003_geometry_composition_eval as evaluation
from bench import p003_geometry_decision_composition as composition


def fixtures() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = [
        {"id": str(i), "kind": ("cell", "row", "wrap")[i // 8], "status": "abstained", "choice": "unresolved"}
        for i in range(24)
    ]
    gold = {str(i): {"expected_choice": "same", "evidence_limitation": i >= 18} for i in range(24)}
    return rows, gold


def test_full_denominators_and_indeterminate_abstentions() -> None:
    rows, gold = fixtures()
    rows[0].update(status="classified", choice="same")
    rows[1].update(status="transport_error")
    scores = evaluation.summary(rows, gold)
    assert scores["all_24"]["intended_count"] == 24
    assert scores["all_24"]["author_label_matches"] == 1
    assert scores["all_24"]["classified"] == 1
    assert scores["all_24"]["abstained"] == 22
    assert scores["visually_cued_18"]["intended_count"] == 18
    assert scores["indeterminate_6"]["abstained"] == 6
    assert all(s["intended_count"] == 8 for s in scores["per_kind"].values())


@pytest.mark.parametrize("change", ["missing", "duplicate"])
def test_missing_or_duplicate_cases_rejected(change: str) -> None:
    rows, gold = fixtures()
    rows = rows[:-1] if change == "missing" else [*rows[:-1], rows[0]]
    with pytest.raises(ValueError, match="Complete unique"):
        evaluation.summary(rows, gold)


def test_conflict_policies_do_not_invent_probabilities() -> None:
    vector = {"id": "0", "kind": "cell", "treatment": "direct_vector", "status": "classified", "choice": "same"}
    model = {"id": "0", "kind": "cell", "status": "valid_nonabstaining", "receipt": {"choice": "separate"}}
    assert composition.compose(vector, model, "vector_first")["selected_component"] == "vector"
    for policy in ("agreement_only", "either_evidence_conflicts_abstain"):
        row = composition.compose(vector, model, policy)
        assert row["decisive_conflict"]
        assert row["status"] == "abstained"
        assert row["probability"] is None


def test_external_authority_checked_before_any_replay(tmp_path: Path) -> None:
    authority = tmp_path / "authority.json"
    authority.write_text(json.dumps({}))
    with pytest.raises(ValueError, match="authority"):
        evaluation.verify(tmp_path, authority, "wrong", "wrong")
