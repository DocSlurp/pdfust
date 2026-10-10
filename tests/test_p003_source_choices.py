from copy import deepcopy

import pytest
from bench.p003_source_choices import apply_cohorts, cohorts, difference_packet, generate
from bench.pipeline_repair import validate


def fixture() -> tuple[dict, dict]:
    words = [
        {"id": f"w{i}", "text": text, "bbox": box}
        for i, (text, box) in enumerate(
            [
                ("same", [5, 5, 15, 15]),
                ("same", [5, 5, 15, 15]),
                ("right", [75, 5, 85, 15]),
                ("bottom", [5, 75, 15, 85]),
                ("outside", [95, 95, 99, 99]),
            ]
        )
    ]
    source = {"page_size": [0, 0, 100, 100], "words": words, "vector_candidates": []}
    table = {
        "row_count": 2,
        "col_count": 2,
        "values": [["INJECTED", "discard"], ["all", "values"]],
        "cells": [{"source_ids": ids, "role": "unknown"} for ids in (["w2"], ["w0", "w1"], ["w3"], [])],
        "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)],
    }
    return source, {"id": "c0", "tables": [table], "unresolved_ids": ["w4"]}


def test_generated_strings_discarded_and_physical_duplicates_retained() -> None:
    source, prior = fixture()
    pool = generate(source, prior)
    assert len(pool["policies"]) == 6
    assert len(pool["candidates"]) > 1
    for candidate in pool["candidates"]:
        state = candidate["state"]
        validate(source, state)
        assert "INJECTED" not in str(state)
        ids = [ident for table in state["tables"] for cell in table["cells"] for ident in cell["source_ids"]]
        assert sorted(ids + state["unresolved_ids"]) == [f"w{i}" for i in range(5)]
    changed = deepcopy(prior)
    changed["tables"][0]["values"] = [["other", "text"], ["irrelevant", "stuff"]]
    assert generate(source, changed) == pool


def test_partial_difference_packet_explicitly_records_omissions() -> None:
    source, prior = fixture()
    pool = generate(source, prior)
    text, metadata = difference_packet(source, pool)
    assert "INJECTED" not in text
    assert "source_id_fallback" not in text
    assert metadata["shown_words"] + metadata["omitted_unchanged_words"] == len(source["words"])
    assert metadata["evidence_utf8_bytes"] == len(text.encode())


def test_disjoint_cohort_choices_preserve_fallback_and_reject_stale_menu() -> None:
    source, prior = fixture()
    pool = generate(source, prior)
    fallback = next(item for item in pool["policies"] if item["policy"] == "source_id_fallback")
    label = next(item["label"] for item in pool["candidates"] if item["state_sha256"] == fallback["state_sha256"])
    menu = cohorts(source, pool)
    choices = {item["id"]: label for item in menu["cohorts"]}
    assert apply_cohorts(source, pool, menu, choices, default=label) == fallback["state"]
    for candidate in pool["candidates"]:
        choices = {item["id"]: candidate["label"] for item in menu["cohorts"]}
        validate(source, apply_cohorts(source, pool, menu, choices, default=label))
    stale = deepcopy(menu)
    stale["cohorts"][0]["source_ids"].append("w4")
    with pytest.raises(ValueError, match="stale"):
        apply_cohorts(source, pool, stale, choices, default=label)


def test_exact_cohort_oracle_can_select_geometry_gain() -> None:
    from bench.p003_source_choice_oracle import select  # noqa: PLC0415

    source, prior = fixture()
    pool = generate(source, prior)
    target = {"row_count": 2, "col_count": 2, "values": [["same same", "right"], ["bottom", ""]]}
    result = select(source, pool, cohorts(source, pool), {0: target})
    assert result["exact"]
    assert result["strict_anchor_score"] == 4
    validate(source, result["state"])


def test_exact_max_sum_matches_exhaustive_assignments() -> None:
    import itertools  # noqa: PLC0415

    from bench.p003_source_choice_oracle import maximize  # noqa: PLC0415

    factors = [
        {"scope": scope, "scores": {pair: int(pair[0] == pair[1]) for pair in itertools.product(range(2), repeat=2)}}
        for scope in ((0, 1), (1, 2), (0, 2))
    ]
    factors.append({"scope": (1,), "scores": {(0,): 0, (1,): 2}})
    score, choices, peak = maximize([2, 2, 2], factors)
    brute = max(
        sum(f["scores"][tuple(assignment[v] for v in f["scope"])] for f in factors)
        for assignment in itertools.product(range(2), repeat=3)
    )
    assert score == brute == 5
    assert choices == [1, 1, 1]
    assert peak <= 8


def test_native_request_is_blind_and_preserves_explicit_partial_scope() -> None:
    from bench.p003_source_choices import request  # noqa: PLC0415

    source, prior = fixture()
    pool = generate(source, prior)
    body, metadata = request(source, pool, "typesafe/jev-1.13")
    assert body["model"] == "typesafe/jev-1.13"
    assert "typesafe" not in body["state"]
    assert "source_id_fallback" not in body["state"]
    assert "unresolved" in body["questions"]["q0"]["criteria"]
    assert metadata["pixels_available"] is False
    assert metadata["unresolved_action"].startswith("retain independently authenticated")
