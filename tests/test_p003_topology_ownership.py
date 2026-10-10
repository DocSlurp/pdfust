"""Synthetic topology and typed responses only; no model, PDF, or annotation access."""

from __future__ import annotations

import base64
import json
from copy import deepcopy
from typing import Any

import pytest
from bench import p003_topology_ownership as own
from bench.pipeline_assembly import validate

MODEL = "typesafe/jev-1.13"
IMAGE = "data:image/png;base64," + base64.b64encode(b"synthetic-frozen-pixels").decode()


def response(tables: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "answers": {"q0": {"tables": tables}},
                        }
                    )
                },
            }
        ]
    }


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    source = {
        "page_size": [100, 100],
        "words": [
            {"id": f"id{i}", "text": text, "bbox": [10, i * 10, 20, i * 10 + 5]}
            for i, text in enumerate(["Label", "Value", "name", "10", "cont", "20"])
        ],
        "gold": "must-never-enter-prompt",
    }
    topology = response([{"bbox": [0, 0, 1000, 1000], "row_count": 3, "col_count": 2, "mergedspans": [[1, 0, 2, 1]]}])
    return source, topology


def answers(bodies: list[dict[str, Any]], choices: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "answers": {
                key: {
                    "type": "choice",
                    "choice": choices[key],
                    "confidence": {"raw": "untrusted"},
                    "probabilities": {option: float(option == choices[key]) for option in question["criteria"]},
                }
                for key, question in body["questions"].items()
            }
        }
        for body in bodies
    ]


def stages(
    plan: own.Plan,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    row_choices = {f"w{i}": f"t0r{i // 2}" for i in range(6)}
    row_bodies = own.batches(plan, MODEL, IMAGE, max_questions=2)
    row_results = answers(row_bodies, row_choices)
    rows = own.collect(plan, row_bodies, row_results)
    cell_bodies = own.batches(plan, MODEL, IMAGE, rows=rows, max_questions=2)
    cell_choices = {f"w{i}": f"t0r{1 if i == 4 else i // 2}c{i % 2}" for i in range(6)}
    return row_bodies, row_results, cell_bodies, answers(cell_bodies, cell_choices)


def test_complete_source_owned_merged_rows_exact_strings_and_no_annotations() -> None:
    source, topology = fixture()
    prior = deepcopy((source, topology))
    plan = own.freeze(source, topology, [0, 0, 100, 100], IMAGE)
    bodies = stages(plan)
    result = own.assemble(plan, *bodies)
    state = result["state"]
    assert state["tables"][0]["values"] == [["Label", "Value"], ["name cont", "10"], [None, "20"]]
    assert state["tables"][0]["cells"][2]["source_ids"] == ["id2", "id4"]
    validate(source, state)
    assert result["source_conserved"] is True
    assert result["missing_source_text_recoverable"] is False
    assert result["rows"]["decisions"]["w0"]["raw_probabilities"]["t0r0"] == 1
    assert result["rows"]["decisions"]["w0"]["raw_confidence"] == {"raw": "untrusted"}
    assert "must-never-enter-prompt" not in json.dumps(bodies)
    assert (source, topology) == prior
    assert all(len(body["questions"]) <= 2 for body in bodies[0] + bodies[2])
    assert "t0r1c0" in bodies[2][2]["questions"]["w4"]["criteria"]
    assert "t0r2c0" not in bodies[2][2]["questions"]["w4"]["criteria"]


def test_abstention_and_outside_preserve_original_inventory_order() -> None:
    source, topology = fixture()
    plan = own.freeze(source, topology, [0, 0, 100, 100], IMAGE)
    rb = own.batches(plan, MODEL, IMAGE)
    rr = answers(
        rb, {"w0": "unresolved", "w1": "outside", "w2": "t0r1", "w3": "outside", "w4": "unresolved", "w5": "outside"}
    )
    rows = own.collect(plan, rb, rr)
    cb = own.batches(plan, MODEL, IMAGE, rows=rows)
    cr = answers(cb, {"w2": "unresolved"})
    output = own.assemble(plan, rb, rr, cb, cr)
    assert output["state"]["unresolved_ids"] == [f"id{i}" for i in range(6)]
    assert output["outside_ids"] == ["id1", "id3", "id5"]
    assert output["abstained_ids"] == ["id0", "id2", "id4"]
    assert all(not cell["source_ids"] for cell in output["state"]["tables"][0]["cells"])


@pytest.mark.parametrize("change", ["missing", "duplicate", "extra", "probabilities", "choice", "image", "text"])
def test_late_error_refuses_complete_assembly_without_mutation(change: str) -> None:
    source, topology = fixture()
    plan = own.freeze(source, topology, [0, 0, 100, 100], IMAGE)
    rb, rr, cb, cr = stages(plan)
    before = plan.packet_json
    if change == "missing":
        cr.pop()
    elif change == "duplicate":
        cb.append(deepcopy(cb[0]))
        cr.append(deepcopy(cr[0]))
    elif change == "extra":
        cr[-1]["answers"]["bad"] = deepcopy(cr[-1]["answers"]["w4"])
    elif change == "probabilities":
        cr[-1]["answers"]["w4"]["probabilities"]["t0r1c0"] = float("nan")
    elif change == "choice":
        cr[-1]["answers"]["w4"]["choice"] = "t0r2c0"
    elif change == "image":
        cb[-1]["state"][1]["image_url"]["url"] = "data:image/png;base64,Y2hhbmdlZA=="
    else:
        cb[-1]["state"][0] = "invented-word"
    with pytest.raises((ValueError, TypeError, KeyError)):
        own.assemble(plan, rb, rr, cb, cr)
    assert plan.packet_json == before


@pytest.mark.parametrize(
    "table",
    [
        {"bbox": [0, 0, 1010, 1000], "row_count": 2, "col_count": 2, "mergedspans": []},
        {"bbox": [0, 0, 1000, 1000], "row_count": 129, "col_count": 2, "mergedspans": []},
        {"bbox": [0, 0, 1000, 1000], "row_count": True, "col_count": 2, "mergedspans": []},
        {"bbox": [0, 0, 1000, 1000], "row_count": 2, "col_count": 2, "mergedspans": [[0, 0, 3, 1]]},
        {"bbox": [0, 0, 1000, 1000], "row_count": 2, "col_count": 2, "mergedspans": [[0, 0, 2, 1], [1, 0, 1, 2]]},
    ],
)
def test_strict_topology_refusals(table: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r"Topology|span|Span|bounds|Bound|Covered|overlap"):
        own.parse_topology(response([table]), [0, 0, 100, 100])


def test_overlap_no_tables_empty_source_and_batch_caps() -> None:
    _source, topology = fixture()
    table = json.loads(topology["choices"][0]["message"]["content"])["answers"]["q0"]["tables"][0]
    with pytest.raises(ValueError, match="overlaps"):
        own.parse_topology(response([table, table]), [0, 0, 100, 100])
    empty = own.freeze({"page_size": [100, 100], "words": []}, response([]), [0, 0, 100, 100], IMAGE)
    assert own.batches(empty, MODEL, IMAGE) == []
    assert own.assemble(empty, [], [], [], [])["state"]["tables"] == []
    many = {"page_size": [100, 100], "words": [{"id": str(i), "text": "x", "bbox": [0, 0, 1, 1]} for i in range(33)]}
    plan = own.freeze(many, topology, [0, 0, 100, 100], IMAGE)
    with pytest.raises(ValueError, match="16 batches"):
        own.batches(plan, MODEL, IMAGE, max_questions=2)
    with pytest.raises(ValueError, match="no truncation"):
        own.freeze({**many, "words": many["words"] * 10}, topology, [0, 0, 100, 100], IMAGE)


def test_image_topology_request_and_rounding_provenance() -> None:
    request = own.topology_request("anthropic/claude-sonnet-5.5", IMAGE, [10, 20, 110, 120])
    assert request["response_format"]["json_schema"]["name"] == "p003_frozen_topology"
    source, topology = fixture()
    plan = own.freeze(source, topology, [10, 20, 110, 120], IMAGE)
    rb = own.batches(plan, MODEL, IMAGE)
    rr = answers(rb, {f"w{i}": "unresolved" for i in range(6)})
    rr[0]["answers"]["w0"]["probabilities"]["unresolved"] = 0.99
    output = own.collect(plan, rb, rr)
    assert output["decisions"]["w0"]["normalization_delta"] == pytest.approx(-0.01)
    assert output["decisions"]["w0"]["raw_probabilities"]["unresolved"] == 0.99
    rr[0]["answers"]["w0"]["probabilities"]["unresolved"] = 0.9
    with pytest.raises(ValueError, match="rounding"):
        own.collect(plan, rb, rr)


def test_text_only_native_body_all_declared_models_and_strict_replay() -> None:
    """Withheld pixels are explicit and the entire source choice remains replayable."""
    # Existing helper fixture is intentionally source-only and offline.
    source = {"page_size": [100, 100], "words": [{"id": "literal", "text": "whole", "bbox": [10, 10, 20, 20]}]}
    payload = {
        "answers": {"q0": {"tables": [{"bbox": [0, 0, 1000, 1000], "row_count": 1, "col_count": 1, "mergedspans": []}]}}
    }
    response = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}]}
    frozen = own.freeze(source, response, [0, 0, 100, 100], IMAGE)
    for model in own.DECISION_MODELS:
        bodies = own.batches(frozen, model, IMAGE, image=False)
        assert isinstance(bodies[0]["state"], str)
        assert "image_url" not in json.dumps(bodies)
        assert "Text-only control" in bodies[0]["questions"]["w0"]["instructions"]
        options = bodies[0]["questions"]["w0"]["criteria"]
        result = {
            "answers": {
                "w0": {
                    "type": "choice",
                    "choice": "t0r0",
                    "probabilities": {k: 1 if k == "t0r0" else 0 for k in options},
                }
            }
        }
        receipt = own.collect(frozen, bodies, [result])
        cells = own.batches(frozen, model, IMAGE, rows=receipt, image=False)
        options = cells[0]["questions"]["w0"]["criteria"]
        cell_result = {
            "answers": {
                "w0": {
                    "type": "choice",
                    "choice": "t0r0c0",
                    "probabilities": {k: 1 if k == "t0r0c0" else 0 for k in options},
                }
            }
        }
        audit = own.assemble(frozen, bodies, [result], cells, [cell_result])
        assert audit["state"]["tables"][0]["cells"][0]["source_ids"] == ["literal"]
