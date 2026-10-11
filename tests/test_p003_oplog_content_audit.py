"""Conditional oplog projection preserves omissions, headers and partial state."""

from __future__ import annotations

from dataclasses import replace

import pytest
from bench.decision_oplog import Atom, State, apply, make_cell, operation
from bench.p003_oplog_content_audit import body_table, parse_choice
from bench.p003_oplog_content_eval import target_body


def initial() -> State:
    state = State(
        tuple(
            Atom(f"w{i}", text, (float(i * 20), 0.0 if i < 2 else 20.0, float(i * 20 + 10), 8.0 if i < 2 else 28.0))
            for i, text in enumerate(("Name", "USD", "Alpha", "Beta", "120"))
        ),
        (),
        tuple(f"w{i}" for i in range(5)),
        (),
        (0.0, 0.0, 200.0, 100.0),
        256,
        2,
    )
    for column in range(2):
        state = apply(state, operation(state, "assign", put=(make_cell(state, 0, column, (f"w{column}",), "header"),)))
    return state


def test_declared_rows_and_source_order_survive_projection() -> None:
    start = initial()
    state = apply(start, operation(start, "assign", put=(make_cell(start, 1, 0, ("w3", "w2")),)))
    state = apply(state, operation(state, "assign", put=(make_cell(state, 3, 1, ("w4",)),)))
    assert body_table(state, start) == {
        "row_count": 3,
        "col_count": 2,
        "values": [["Beta Alpha", ""], ["", ""], ["", "120"]],
        "spans": [],
    }
    assert body_table(start, start) is None


def test_partial_unassigned_source_is_not_inserted() -> None:
    start = initial()
    state = apply(start, operation(start, "assign", put=(make_cell(start, 1, 0, ("w2",)),)))
    state = apply(state, operation(state, "leave_unresolved", ids=("w3", "w4")))
    assert body_table(state, start)["values"] == [["Alpha", ""]]
    assert state.unassigned == ("w3", "w4")
    assert state.deferred == ("w3", "w4")


def test_header_role_or_source_changes_rejected() -> None:
    start = initial()
    moved = replace(start, cells=(replace(start.cells[0], role="data", row=1), start.cells[1]))
    with pytest.raises(ValueError, match="headers changed"):
        body_table(moved, start)
    changed = replace(start, atoms=(replace(start.atoms[0], text="Invented"), *start.atoms[1:]))
    with pytest.raises(ValueError, match="Original source"):
        body_table(changed, start)


def test_duplicate_ownership_rejected() -> None:
    start = initial()
    with pytest.raises(ValueError, match="owned once"):
        body_table(replace(start, unassigned=("w0", *start.unassigned)), start)


def test_probability_contract_and_abstention() -> None:
    raw = {"answers": {"q0": {"type": "choice", "choice": "abstain", "probabilities": {"op1": 0.2, "abstain": 0.8}}}}
    assert parse_choice(raw, {"op1", "abstain"})["choice"] == "abstain"
    raw["answers"]["q0"]["probabilities"]["op1"] = True
    with pytest.raises(ValueError, match="Finite probability"):
        parse_choice(raw, {"op1", "abstain"})


def target_case() -> dict:
    """Build independent authored slots for projection policy checks."""
    start = initial()
    return {
        "gold": {"choice": "A"},
        "evidence": {
            "words": [{"id": i, "text": a.text, "bbox": list(a.bbox)} for i, a in enumerate(start.atoms)],
            "assemblies": {
                "A": {
                    "cells": [
                        {"id": "description_header", "source_ids": [0]},
                        {"id": "value_header", "source_ids": [1]},
                        {"id": "r0c0", "source_ids": [2, 3]},
                        {"id": "r0c1", "source_ids": [4]},
                        {"id": "r1c0", "source_ids": []},
                        {"id": "r1c1", "source_ids": []},
                    ]
                }
            },
        },
    }


def test_reference_projects_explicit_empty_slots() -> None:
    body, exclusion = target_body(target_case(), initial())
    assert exclusion is None
    assert body["values"] == [["Alpha Beta", "120"], ["", ""]]


def test_missing_slot_and_unresolved_never_fill_from_prediction() -> None:
    case = target_case()
    case["evidence"]["assemblies"]["A"]["cells"][2]["id"] = "unknown"
    assert target_body(case, initial()) == (None, "missing-slot-annotation")
    case["gold"]["choice"] = "unresolved"
    assert target_body(case, initial()) == (None, "author-unresolved")


def test_reference_invented_or_duplicated_source_rejected() -> None:
    case = target_case()
    case["evidence"]["assemblies"]["A"]["cells"][2]["source_ids"].append(2)
    with pytest.raises(ValueError, match="conservation"):
        target_body(case, initial())
