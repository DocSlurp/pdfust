"""Chunked evidence retains complete sources and combines native answers atomically."""

import base64
import json
from copy import deepcopy
from typing import Any

import pytest
from bench import p003_topology_chunks as chunks
from bench import p003_topology_ownership as own

IMAGE = "data:image/png;base64," + base64.b64encode(b"offline-crop").decode()
MODEL = "typesafe/jev-1.13"


def plan(count: int = 300) -> own.Plan:
    """Freeze a whole inventory larger than the historical request-level cap."""
    source = {
        "page_size": [100, 100],
        "words": [{"id": f"id{i}", "text": f"literal-{i}", "bbox": [10, 10, 20, 20]} for i in range(count)],
    }
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "answers": {
                                "q0": {
                                    "tables": [
                                        {"bbox": [0, 0, 1000, 1000], "row_count": 1, "col_count": 1, "mergedspans": []}
                                    ]
                                }
                            }
                        }
                    )
                },
            }
        ]
    }
    return chunks.freeze(source, response, [0, 0, 100, 100], IMAGE)


def results(bodies: list[dict[str, Any]], choice: str) -> list[dict[str, Any]]:
    """Create deterministic typed fake choices, without a probability claim."""
    return [
        {
            "answers": {
                key: {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": {option: 1 if option == choice else 0 for option in question["criteria"]},
                }
                for key, question in body["questions"].items()
            }
        }
        for body in bodies
    ]


@pytest.mark.parametrize("mode", ["compact", "neighbors", "bands"])
@pytest.mark.parametrize("image", [True, False])
def test_complete_large_inventory_with_bounded_local_evidence(mode: str, *, image: bool) -> None:
    frozen = plan()
    bodies = chunks.batches(frozen, MODEL, IMAGE, max_questions=16, image=image, evidence_mode=mode)
    assert len(bodies) == 19
    assert all(len(b["questions"]) <= 16 for b in bodies)
    evidence = [json.loads(b["state"][0] if image else b["state"]) for b in bodies]
    ids = [e["target_source_ids"][f"w{i}"] for e in evidence for i in range(len(e["target_source_ids"]))]
    assert ids == [f"id{i}" for i in range(300)]
    assert all(e["global_snapshot_sha256"] == frozen.sha256 for e in evidence)
    if mode == "neighbors":
        assert all(len(e["context_words"]) <= chunks.MAX_CONTEXT_WORDS for e in evidence)
    rows = chunks.collect(frozen, bodies, results(bodies, "t0r0"))
    cells = chunks.batches(frozen, MODEL, IMAGE, rows=rows, image=image, evidence_mode=mode)
    audit = chunks.assemble(frozen, bodies, results(bodies, "t0r0"), cells, results(cells, "t0r0c0"))
    assigned = audit["state"]["tables"][0]["cells"][0]["source_ids"]
    assert assigned == ids
    assert len(set(assigned)) == 300
    assert audit["source_conserved"] is True
    assert "literal-299" in audit["state"]["tables"][0]["values"][0][0]


def test_duplicate_missing_changed_evidence_and_late_malformed_fail_atomically() -> None:
    frozen = plan(40)
    bodies = chunks.batches(frozen, MODEL, IMAGE, image=False)
    raw = results(bodies, "outside")
    with pytest.raises(ValueError, match="incomplete"):
        chunks.collect(frozen, bodies[:-1], raw[:-1])
    with pytest.raises(ValueError, match="duplicate"):
        chunks.collect(frozen, [bodies[0], bodies[0], bodies[2]], raw)
    changed = deepcopy(bodies)
    value = json.loads(changed[0]["state"])
    value["words"]["w0"]["text"] = "invented"
    changed[0]["state"] = json.dumps(value)
    with pytest.raises(ValueError, match="immutable"):
        chunks.collect(frozen, changed, raw)
    raw[-1]["answers"]["w0"]["choice"] = "invented"
    with pytest.raises(ValueError, match="raw maximum"):
        chunks.collect(frozen, bodies, raw)


def test_full_200_row_inventory_projects_complete_tables_and_global_ids() -> None:
    source = {
        "page_size": [100, 100],
        "words": [
            {"id": "right", "text": "whole right", "bbox": [60, 0.1, 70, 0.8]},
            {"id": "left", "text": "whole left", "bbox": [10, 0.1, 20, 0.8]},
        ],
    }
    tables = [
        {"bbox": bbox, "row_count": 100, "col_count": 1, "mergedspans": []}
        for bbox in ([0, 0, 500, 1000], [500, 0, 1000, 1000])
    ]
    response = {
        "choices": [
            {"finish_reason": "stop", "message": {"content": json.dumps({"answers": {"q0": {"tables": tables}}})}}
        ]
    }
    frozen = chunks.freeze(source, response, [0, 0, 100, 100], IMAGE)
    bodies = chunks.batches(frozen, MODEL, IMAGE, max_questions=1, image=False)
    assert json.loads(bodies[0]["state"])["table_ids"] == ["t1"]
    assert json.loads(bodies[1]["state"])["table_ids"] == ["t0"]
    assert set(bodies[0]["questions"]["w0"]["criteria"]) == {"outside", "unresolved"} | {f"t1r{i}" for i in range(100)}
    raw = results(bodies[:1], "t1r0") + results(bodies[1:], "t0r0")
    receipt = chunks.collect(frozen, bodies, raw)
    cells = chunks.batches(frozen, MODEL, IMAGE, rows=receipt, max_questions=1, image=False)
    audit = chunks.assemble(frozen, bodies, raw, cells, results(cells[:1], "t1r0c0") + results(cells[1:], "t0r0c0"))
    assert audit["state"]["tables"][0]["cells"][0]["source_ids"] == ["left"]
    assert audit["state"]["tables"][1]["cells"][0]["source_ids"] == ["right"]
