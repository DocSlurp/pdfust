"""Source-only controllers preserve source inventory and original early endings."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from bench.decision_oplog import Atom, Session, State, apply, make_cell, operation, proposals
from bench.p003_oplog_termination import prefix, stop_decision


def trace(ending: str = "finish") -> tuple[State, list[dict[str, Any]]]:
    """Build a conserved two-word source trace with explicit receipt witnesses."""
    initial = State(
        (
            Atom("h", "Name", (0.0, 0.0, 8.0, 8.0)),
            Atom("a", "Alpha", (0.0, 20.0, 8.0, 28.0)),
            Atom("v", "120", (50.0, 20.0, 58.0, 28.0)),
        ),
        (),
        ("h", "a", "v"),
        (),
        (0.0, 0.0, 100.0, 100.0),
        256,
        2,
    )
    initial = apply(initial, operation(initial, "assign", put=(make_cell(initial, 0, 0, ("h",), "header"),)))
    session = Session(initial)
    calls = []
    for step in range(3):
        before = session.state.sha256
        menu = proposals(session.state)
        chosen = (
            next(o.id for o in menu if o.kind == "assign")
            if step < 2
            else ("abstain" if ending == "abstain" else next(o.id for o in menu if o.kind == "finish"))
        )
        session.choose(chosen, menu)
        calls.append(
            {
                "step": step,
                "before_state_sha256": before,
                "after_state_sha256": session.state.sha256,
                "stop_reason": session.stop_reason,
                "answer": {"choice": chosen},
                "entry": {"index": step, "response_file": f"response-{step}.json"},
                "request_sha256": f"request-{step}",
                "http_elapsed_ms": 100,
                "cost": {"effective_usd": 0.01, "reported_usd": 0.01},
            }
        )
    return initial, calls


def test_source_completion_remains_controller_action_with_suffix_provenance() -> None:
    initial, calls = trace()
    projected = prefix(initial, calls, "P1-source-complete", 8)
    assert projected["controller_stop"] == "controller-source-complete"
    assert projected["original_prefix_stop"] is None
    assert not projected["state"]["finished"]
    assert projected["source_complete"]
    assert projected["omitted_original_calls"] == 1
    assert projected["hypothetical_omitted_suffix"][0]["entry_index"] == 2
    assert projected["hypothetical_omitted_effective_usd"] == 0.01
    assert projected["hypothetical_omitted_http_seconds"] == 0.1
    assert projected["available_topology_operations"]["move"] > 0


def test_fixed_cap_preserves_original_earlier_abstention() -> None:
    initial, calls = trace("abstain")
    projected = prefix(initial, calls, "P3-fixed-three", 8)
    assert projected["controller_stop"] is None
    assert projected["original_prefix_stop"] == "abstained"
    assert projected["omitted_original_calls"] == 0


def test_seen_successors_requires_nonempty_menu_and_all_successors_seen() -> None:
    initial, _ = trace()
    deferred = replace(initial, deferred=initial.unassigned)
    assert stop_decision("P2-seen-successors", deferred, {deferred.sha256}, 0) is None
    successors = {apply(initial, o).sha256 for o in proposals(initial) if o.kind not in {"finish", "leave_unresolved"}}
    assert stop_decision("P2-seen-successors", initial, {initial.sha256}, 0) is None
    assert stop_decision("P2-seen-successors", initial, successors, 0) == "controller-seen-successors"


def test_missing_charge_keeps_hypothetical_total_unknown() -> None:
    initial, calls = trace()
    calls[2]["cost"]["effective_usd"] = None
    projected = prefix(initial, calls, "P1-source-complete", 8)
    assert projected["hypothetical_omitted_effective_usd"] is None
    assert not projected["suffix_cost_complete"]
