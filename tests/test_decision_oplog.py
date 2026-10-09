from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace

import pytest
from bench.decision_oplog import (
    MAX_MENU,
    Atom,
    Session,
    State,
    apply,
    from_context,
    make_cell,
    make_request,
    operation,
    proposals,
    replay,
    validate,
)


def initial() -> State:
    atoms = (
        Atom("w0", "first", (10, 10, 20, 20)),
        Atom("w1", "100", (70, 10, 80, 20)),
        Atom("w2", "second", (10, 30, 20, 40)),
        Atom("w3", "line", (22, 30, 30, 40)),
    )
    return State(atoms, (), tuple(atom.id for atom in atoms), (), (0, 0, 100, 100), 8, 2)


def assigned() -> State:
    state = initial()
    return apply(state, operation(state, "assign", put=(make_cell(state, 0, 0, ("w0",)),)))


def test_source_atoms_and_snapshots_are_immutable() -> None:
    state = initial()
    with pytest.raises(FrozenInstanceError):
        state.atoms[0].text = "invented"  # type: ignore[misc]
    assert initial().sha256 == state.sha256


def test_assign_move_join_split_and_unresolved_preserve_sources() -> None:
    state = assigned()
    state = apply(state, operation(state, "assign", put=(make_cell(state, 1, 0, ("w2", "w3")),)))
    state = apply(
        state,
        operation(state, "join", remove=("r0c0", "r1c0"), put=(make_cell(state, 0, 0, ("w0", "w2", "w3")),)),
    )
    assert state.cells[0].source_ids == ("w0", "w2", "w3")
    state = apply(
        state,
        operation(
            state,
            "split",
            remove=("r0c0",),
            put=(make_cell(state, 0, 0, ("w0",)), make_cell(state, 1, 0, ("w2", "w3"))),
        ),
    )
    state = apply(state, operation(state, "move", remove=("r1c0",), put=(make_cell(state, 2, 0, ("w2", "w3")),)))
    state = apply(state, operation(state, "leave_unresolved", remove=("r2c0",), ids=("w2", "w3")))
    assert state.unassigned == ("w1", "w2", "w3")
    assert state.deferred == ("w2", "w3")
    validate(state)
    finished = apply(state, operation(state, "finish"))
    assert finished.finished
    assert finished.unassigned == state.unassigned


def test_rejection_is_atomic_for_stale_unknown_duplicate_and_out_of_range() -> None:
    state = assigned()
    original = state.sha256
    bad = (
        operation(initial(), "finish"),
        operation(state, "assign", put=(make_cell(state, 1, 0, ("w0",)),)),
        operation(state, "assign", put=(make_cell(state, 8, 0, ("w1",)),)),
        operation(state, "move", remove=("missing",), put=(make_cell(state, 1, 0, ("w0",)),)),
        replace(operation(state, "finish"), id="made-up"),
    )
    for op in bad:
        with pytest.raises(ValueError, match=r"Finished|Assign|Cell|Removed|identity"):
            apply(state, op)
        assert state.sha256 == original


def test_empty_fabricated_geometry_and_duplicate_slot_are_rejected() -> None:
    state = assigned()
    with pytest.raises(ValueError, match="nonempty"):
        make_cell(state, 1, 0, ())
    cell = make_cell(state, 1, 1, ("w1",))
    with pytest.raises(ValueError, match="bbox"):
        apply(state, operation(state, "assign", put=(replace(cell, bbox=(0, 0, 90, 90)),)))
    with pytest.raises(ValueError, match="slots"):
        apply(state, operation(state, "assign", put=(replace(make_cell(state, 0, 0, ("w1",)), id="other"),)))
    with pytest.raises(ValueError, match="geometry"):
        validate(replace(state, atoms=(replace(state.atoms[0], bbox=(10, 10, float("nan"), 20)), *state.atoms[1:])))


def test_source_derived_overlapping_cells_are_rejected() -> None:
    state = initial()
    atoms = (*state.atoms, Atom("w4", "overprint", (15, 12, 25, 22)))
    state = replace(state, atoms=atoms, unassigned=tuple(atom.id for atom in atoms))
    state = apply(state, operation(state, "assign", put=(make_cell(state, 0, 0, ("w0",)),)))
    with pytest.raises(ValueError, match="bboxes overlap"):
        apply(state, operation(state, "assign", put=(make_cell(state, 1, 0, ("w4",)),)))


def test_join_split_preconditions_reject_nonadjacent_slots_and_changed_roles() -> None:
    state = assigned()
    with pytest.raises(ValueError, match="role"):
        apply(state, operation(state, "move", remove=("r0c0",), put=(make_cell(state, 1, 0, ("w0",), "header"),)))
    state = apply(state, operation(state, "assign", put=(make_cell(state, 2, 0, ("w2", "w3")),)))
    with pytest.raises(ValueError, match="adjacent"):
        apply(
            state,
            operation(state, "join", remove=("r0c0", "r2c0"), put=(make_cell(state, 0, 0, ("w0", "w2", "w3")),)),
        )


def test_log_undo_and_replay_are_deterministic_and_detect_tampering() -> None:
    session = Session(initial())
    for _ in range(2):
        menu = proposals(session.state)
        selected = next(op for op in menu if op.kind == "assign")
        session.choose(selected.id, menu)
    history = tuple(session.history)
    final = session.state
    assert replay(session.initial, history) == final
    assert session.undo() == history[-1].before
    assert session.undo() == initial()
    with pytest.raises(ValueError, match="before snapshot"):
        replay(initial(), (replace(history[0], before=final),))


def test_step_cap_abstention_and_loop_preserve_partial_state() -> None:
    session = Session(initial(), max_steps=1)
    menu = proposals(session.state)
    op = next(op for op in menu if op.kind == "assign")
    partial = session.choose(op.id, menu)
    assert session.stop_reason == "step-cap"
    assert session.choose("anything", ()) == partial
    session = Session(assigned())
    menu = proposals(session.state)
    move = next(op for op in menu if op.kind == "move")
    moved = session.choose(move.id, menu)
    menu = proposals(session.state)
    back = next(op for op in menu if op.kind == "move" and op.put_cells[0].row == 0)
    assert session.choose(back.id, menu) == moved
    assert session.stop_reason == "loop"
    session = Session(initial())
    assert session.choose("abstain", proposals(session.state)) == initial()
    assert session.stop_reason == "abstained"


def test_menus_are_bounded_and_scheduling_policies_select_different_focus() -> None:
    state = initial()
    next_row = [op for op in proposals(state, "next-uncertain-row") if op.kind == "assign"]
    largest = [op for op in proposals(state, "largest-unassigned-cluster") if op.kind == "assign"]
    full = proposals(state, "model-menu")
    assert {op.put_cells[0].row for op in next_row} == {0}
    assert largest[0].put_cells[0].source_ids == ("w2", "w3")
    assert len(full) <= MAX_MENU
    session = Session(state)
    with pytest.raises(ValueError, match="existing operation"):
        session.choose("model-invented-op", full)


def test_existing_thirty_dev_adapter_and_proposals_do_not_use_gold_or_fixture_ids() -> None:
    from bench.decision_context_cases import context_cases  # noqa: PLC0415 - CPU fixture generation only.

    for case in context_cases():
        state = from_context(case)
        assert sum(cell.role == "header" for cell in state.cells) == 2
        request = make_request(state, proposals(state), "test-model")
        changed = deepcopy(case)
        changed.update(gold={"choice": "SECRET GOLD"}, id="SECRET FIXTURE", family="SECRET FAMILY")
        changed["evidence"]["candidates"] = {"SECRET CANDIDATE": []}
        changed["evidence"]["assemblies"] = {"SECRET ASSEMBLY": []}
        other = from_context(changed)
        assert make_request(other, proposals(other), "test-model") == request
        assert "SECRET" not in json.dumps(request)
        validate(state)


def test_optional_image_and_current_cells_use_existing_operation_choice_ids() -> None:
    state = assigned()
    menu = proposals(state)
    image = "data:image/png;base64,cGl4ZWxz"
    request = make_request(state, menu, "test-model", image=image)
    assert request["state"][1]["image_url"]["url"] == image
    assert set(request["questions"]["q0"]["criteria"]) == {*(op.id for op in menu), "abstain"}
    with pytest.raises(ValueError, match="PNG data URL"):
        make_request(state, menu, "test-model", image="https://example.test/private.png")
    with pytest.raises(ValueError, match="explicitly DEV"):
        from_context({"split": "HELDOUT"})
