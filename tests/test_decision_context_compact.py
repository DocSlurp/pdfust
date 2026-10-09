"""Compact request evidence, option semantics and geometry checks."""

import json

from bench.decision_context_cases import context_cases, evidence_modes
from bench.decision_context_compact import local_state, make_request


def test_raw_compact_omits_gold_and_derived_facts() -> None:
    case = context_cases()[0]
    request = make_request(evidence_modes(case, "native"), "dev-model")
    serialized = json.dumps(request)
    assert len(json.dumps(request["state"]).encode()) < 4000
    assert len(serialized.encode()) < 5000
    assert "gold" not in serialized
    assert "assemblies" not in serialized
    assert "derived_geometry" not in serialized
    assert case["evidence"]["candidates"]["tail"] == request["state"]["source_spans"]["tail"]["ids"]
    assert set(request["questions"]) == {"q0"}
    assert "TWO entries" in request["questions"]["q0"]["criteria"]["B"]


def test_identical_current_observations_cannot_encode_paired_answer() -> None:
    cases = context_cases()
    for offset in (0, 10, 20):
        for index in (0, 2):
            left = make_request(evidence_modes(cases[offset + index], "current"), "dev", derived=True)
            right = make_request(evidence_modes(cases[offset + index + 1], "current"), "dev", derived=True)
            assert left == right
            assert not left["state"]["derived_geometry"]["separator_between_description_centers"]
            assert not left["state"]["derived_geometry"]["fill_membership_by_description_center"]


def test_derived_facts_are_geometry_observations_not_gold() -> None:
    cases = context_cases()
    joined, split = [local_state(evidence_modes(case, "native"), derived=True) for case in cases[:2]]
    assert not joined["derived_geometry"]["separator_between_description_centers"]
    assert split["derived_geometry"]["separator_between_description_centers"]
    fills = [local_state(evidence_modes(case, "native"), derived=True) for case in cases[2:4]]
    assert any(
        item["lead_center_inside"] and item["tail_center_inside"]
        for item in fills[0]["derived_geometry"]["fill_membership_by_description_center"]
    )
    assert any(
        item["lead_center_inside"] and not item["tail_center_inside"]
        for item in fills[1]["derived_geometry"]["fill_membership_by_description_center"]
    )


def test_reversal_changes_order_only() -> None:
    evidence = evidence_modes(context_cases()[0], "native")
    forward = make_request(evidence, "dev")
    reverse = make_request(evidence, "dev", reverse=True)
    assert forward == reverse
    assert list(forward["questions"]["q0"]["criteria"]) == ["A", "B", "unresolved"]
    assert list(reverse["questions"]["q0"]["criteria"]) == ["B", "A", "unresolved"]
