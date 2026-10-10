"""Conservation, conflict and exact evidence tests for experimental relations."""

# ruff: noqa: SLF001 - exhaustive comparison intentionally reuses geometry primitives.

import random
from typing import Any

import pytest
from bench import p003_pair_relations as relations


def source() -> dict[str, Any]:
    return {
        "page_size": [100, 100],
        "words": [
            {"id": "w0", "text": "same", "bbox": [0, 0, 8, 10]},
            {"id": "w1", "text": "same", "bbox": [9, 0, 17, 10]},
            {"id": "w2", "text": "end", "bbox": [18, 0, 26, 10]},
        ],
    }


def test_inventory_keeps_duplicates_and_packet_scope() -> None:
    s = source()
    plan = relations.freeze(s)
    assert len(plan["groups"]) == 3
    assert len(plan["edges"]) == 3
    assert plan["omitted_pairs"] == 0
    bodies = relations.batches(s, plan, "typesafe/test")
    assert len(bodies) == 1
    assert len(bodies[0]["questions"]) == 9
    assert "partial source" in bodies[0]["state"]
    assert "images" not in bodies[0]
    assert isinstance(relations.batches(s, plan, "typesafe/test", "data:image/png;base64,AA==")[0]["state"], list)


def test_false_positive_chain_cannot_merge_negative_triangle() -> None:
    s = source()
    plan = relations.freeze(s)
    answers = {e["id"]: dict.fromkeys(relations.AXES, "yes") for e in plan["edges"]}
    diagonal = next(e["id"] for e in plan["edges"] if (e["a"], e["b"]) == ("g0", "g2"))
    answers[diagonal] = dict.fromkeys(relations.AXES, "no")
    receipt = relations.decode(s, plan, answers)
    assert sorted(map(len, receipt["partitions"]["cell"])) == [1, 2]
    assert receipt["refused_merges"]
    assert len(receipt["unresolved_ids"]) == 1
    assert receipt["cell_groups"][0]["text"] == "same same"


def test_complete_triangle_and_missing_responses() -> None:
    s = source()
    plan = relations.freeze(s)
    complete = {e["id"]: dict.fromkeys(relations.AXES, "yes") for e in plan["edges"]}
    assert relations.decode(s, plan, complete)["cell_groups"][0]["source_ids"] == ["w0", "w1", "w2"]
    missing = relations.decode(s, plan, {})
    assert missing["unresolved_ids"] == ["w0", "w1", "w2"]
    assert missing["missing_response_edges"] == 3


def test_stale_source_and_cross_axis_conflict() -> None:
    s = source()
    plan = relations.freeze(s)
    answers = {e["id"]: {"cell": "yes", "row": "no", "column": "uncertain"} for e in plan["edges"]}
    assert relations.decode(s, plan, answers)["unresolved_ids"] == ["w0", "w1", "w2"]
    s["words"][0]["text"] = "changed"
    with pytest.raises(ValueError, match="Plan differs"):
        relations.decode(s, plan, answers)


def test_geometry_control_is_source_conserving_and_unknown_ids_fail() -> None:
    s = source()
    plan = relations.freeze(s)
    control = relations.decode(s, plan, relations.geometry_control(plan))
    owned = control["unresolved_ids"] + [i for c in control["cell_groups"] for i in c["source_ids"]]
    assert sorted(owned) == ["w0", "w1", "w2"]
    with pytest.raises(ValueError, match="Unknown edge"):
        relations.decode(s, plan, {"invented": {"cell": "yes"}})


def test_collect_typed_distributions_and_exact_body_replay() -> None:
    s = source()
    plan = relations.freeze(s)
    bodies = relations.batches(s, plan, "typesafe/test")
    answer = {"type": "choice", "choice": "yes", "probabilities": {"yes": 0.9, "no": 0.05, "uncertain": 0.05}}
    results = [{"answers": dict.fromkeys(b["questions"], answer)} for b in bodies]
    receipt = relations.collect(s, plan, bodies, results)
    assert len(relations.decode(s, plan, receipt["answers"])["cell_groups"]) == 1
    assert receipt["decisions"]["e0_cell"]["probabilities"]["yes"] == 0.9
    bodies[0]["questions"]["e0_cell"]["instructions"] = "changed"
    with pytest.raises(ValueError, match="bodies differ"):
        relations.collect(s, plan, bodies, results)


def test_interval_sweep_matches_exhaustive_directional_neighbors() -> None:
    rng = random.Random(17)  # noqa: S311 - reproducible synthetic geometry, not secrets.
    words = []
    for i in range(80):
        x, y = rng.randrange(20), rng.randrange(20)
        words.append({"id": f"w{i}", "text": str(i), "bbox": [x, y, x + rng.randrange(5), y + rng.randrange(5)]})
    s = {"words": words}
    expected = set()
    for i, a in enumerate(words):
        ax, ay = relations._center(a["bbox"])
        buckets: dict[str, list[tuple[float, int]]] = {k: [] for k in ("left", "right", "above", "below")}
        for j, b in enumerate(words):
            if i == j:
                continue
            bx, by = relations._center(b["bbox"])
            distance = (bx - ax) ** 2 + (by - ay) ** 2
            if relations._overlap(a["bbox"], b["bbox"], 1) > 0:
                buckets["left" if bx < ax else "right"].append((distance, j))
            if relations._overlap(a["bbox"], b["bbox"], 0) > 0:
                buckets["above" if by < ay else "below"].append((distance, j))
        for entries in buckets.values():
            expected.update((min(i, j), max(i, j)) for _, j in sorted(entries)[:2])
    actual = {(int(e["a"][1:]), int(e["b"][1:])) for e in relations.freeze(s)["edges"]}
    assert actual == expected
