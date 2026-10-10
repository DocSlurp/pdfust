"""Offline rolling decisions enforce source ownership and global row constraints."""

import json
from copy import deepcopy
from itertools import pairwise, product
from typing import Any

import pytest
from bench import decision_p003_boundaries as boundary
from bench.pipeline_repair import validate
from test_pipeline_repair import fixture


def scores(menu: dict[str, Any], *, join: float = 0.9) -> dict[str, Any]:
    return {b["id"]: {"join": join, "split": 1 - join, "unresolved": 0} for b in menu["boundaries"]}


def test_multiple_wrapped_rows_join_in_one_answer_without_transcription() -> None:
    page, state = fixture([["Long", "10"], ["continuation", ""], ["Other", "20"], ["wrap", ""], ["Last", "30"]])
    original = deepcopy((page, state))
    menu = boundary.build(page, state)
    result, audit = boundary.apply(page, state, menu, scores(menu))
    assert result["tables"][0]["values"] == [["Long continuation", "10"], ["Other wrap", "20"], ["Last", "30"]]
    assert audit["joined"] == ["t0b0", "t0b2"]
    validate(page, result)
    assert (page, state) == original


def test_global_chain_and_minimum_row_constraints() -> None:
    page, state = fixture([[str(i), "20"] for i in range(8)])
    menu = boundary.build(page, state)
    result, audit = boundary.apply(page, state, menu, scores(menu))
    assert result["tables"][0]["row_count"] == 3
    assert all(end - start <= 3 for start, end in audit["groups"]["0"])
    assert len(audit["qualified_but_constrained"]) == 2
    page, state = fixture([["Record", "20"], ["wrap", ""]])
    menu = boundary.build(page, state)
    result, audit = boundary.apply(page, state, menu, scores(menu))
    assert result == state
    assert audit["qualified_but_constrained"] == ["t0b0"]


def test_abstention_and_low_margin_keep_existing_partition() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    menu = boundary.build(page, state)
    for answer in (
        scores(menu, join=0.5),
        {b["id"]: {"join": 0, "split": 0, "unresolved": 1} for b in menu["boundaries"]},
    ):
        result, audit = boundary.apply(page, state, menu, answer)
        assert result == state
        assert audit["joined"] == []


def test_preserves_native_vector_and_merged_grids() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    page["vector_candidates"] = deepcopy(state["tables"])
    menu = boundary.build(page, state)
    assert menu["protected_tables"] == [0]
    assert menu["boundaries"] == []
    assert boundary.apply(page, state, menu, {})[0] == state
    page["vector_candidates"] = []
    state["tables"][0]["spans"] = [
        {"row": 0, "column": 0, "row_span": 1, "column_span": 1},
        {"row": 0, "column": 1, "row_span": 2, "column_span": 1},
        {"row": 1, "column": 0, "row_span": 1, "column_span": 1},
        {"row": 2, "column": 0, "row_span": 1, "column_span": 1},
        {"row": 2, "column": 1, "row_span": 1, "column_span": 1},
    ]
    state["tables"][0]["values"][1][1] = None
    assert boundary.build(page, state)["protected_tables"] == [0]


def test_geometry_unavailable_joins_and_outside_sources_preserved() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    page["words"][2]["bbox"][1] = 70
    page["words"][2]["bbox"][3] = 80
    page["words"].append({"id": "outside", "text": "note", "bbox": [0, 100, 20, 110]})
    state["unresolved_ids"] = ["outside"]
    menu = boundary.build(page, state)
    assert all(not b["join_available"] for b in menu["boundaries"])
    assert boundary.apply(page, state, menu, scores(menu))[0] == state
    assert menu["words"][-1][1] == "note"


@pytest.mark.parametrize("bad", [True, -1, 1.5, float("nan"), "0.9"])
def test_invalid_scores_rejected_atomically(bad: Any) -> None:  # noqa: ANN401
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    before = deepcopy(state)
    menu = boundary.build(page, state)
    answer = scores(menu)
    answer["t0b0"]["join"] = bad
    with pytest.raises(ValueError, match="finite numbers"):
        boundary.apply(page, state, menu, answer)
    assert state == before


def test_missing_extra_fields_bad_sum_and_stale_replay_rejected() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    menu = boundary.build(page, state)
    answer = scores(menu)
    with pytest.raises(ValueError, match="exactly once"):
        boundary.apply(page, state, menu, {})
    extra = deepcopy(answer)
    extra["t0b0"]["cell_text"] = "invented"
    with pytest.raises(ValueError, match="score fields"):
        boundary.apply(page, state, menu, extra)
    answer["t0b0"]["split"] = 0.9
    with pytest.raises(ValueError, match="sum to one"):
        boundary.apply(page, state, menu, answer)
    changed = deepcopy(page)
    changed["words"][0]["text"] = "changed"
    changed_state = deepcopy(state)
    changed_state["tables"][0]["values"][0][0] = "changed"
    with pytest.raises(ValueError, match="Stale"):
        boundary.apply(changed, changed_state, menu, scores(menu))
    modified = deepcopy(menu)
    modified["boundaries"][0]["join_available"] = False
    with pytest.raises(ValueError, match="Stale"):
        boundary.apply(page, state, modified, scores(menu))


def test_gold_metadata_never_changes_generation() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    menu, request = boundary.request(page, state, "offline-model", "data:image/png;base64,fixture")
    page.update(gold={"correct_rows": 2}, family="secret", filename="secret.pdf")
    state.update(gold="never read", score=1)
    assert boundary.request(page, state, "offline-model", "data:image/png;base64,fixture") == (menu, request)
    assert request["messages"][1]["content"][1]["type"] == "image_url"
    assert set(boundary.schema(menu)["properties"]) == {"t0b0", "t0b1"}


def test_complete_inventory_and_packet_refuse_instead_of_truncate(monkeypatch: pytest.MonkeyPatch) -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    monkeypatch.setattr(boundary, "MAX_BOUNDARIES", 1)
    with pytest.raises(ValueError, match="no truncation"):
        boundary.build(page, state)
    monkeypatch.setattr(boundary, "MAX_BOUNDARIES", 128)
    monkeypatch.setattr(boundary, "MAX_PACKET_BYTES", 10)
    with pytest.raises(ValueError, match="no truncation"):
        boundary.build(page, state)


def test_parser_rejects_duplicate_keys_and_truncation() -> None:
    def completion(text: str, finish: str = "stop") -> dict[str, Any]:
        return {"choices": [{"finish_reason": finish, "message": {"content": text}}]}

    assert (
        boundary.parse(completion(json.dumps({"answers": {"t0b0": {"join": 0.9, "split": 0.1, "unresolved": 0}}})))[
            "t0b0"
        ]["join"]
        == 0.9
    )
    with pytest.raises(ValueError, match="complete completion"):
        boundary.parse(completion("{}", "length"))
    with pytest.raises(ValueError, match="Duplicate"):
        boundary.parse(completion('{"x": 1, "x": 2}'))


def test_decoder_matches_exhaustive_global_objective() -> None:
    count = 7
    for availability in product((False, True), repeat=count - 1):
        weights = [(0.5 + i / 10) if yes else None for i, yes in enumerate(availability)]
        groups = boundary._partition(count, weights)  # noqa: SLF001 - verify decoder against an independent oracle.
        chosen = {r for start, end in groups for r in range(start, end - 1)}
        actual = sum(weights[r] for r in chosen)
        alternatives = []
        for decisions in product((False, True), repeat=count - 1):
            if any(join and weights[r] is None for r, join in enumerate(decisions)):
                continue
            starts = [0, *[r + 1 for r, join in enumerate(decisions) if not join], count]
            if len(starts) < 3 or any(b - a > 3 for a, b in pairwise(starts)):
                continue
            alternatives.append(sum(weights[r] for r, join in enumerate(decisions) if join))
        assert actual == pytest.approx(max(alternatives))


def test_inline_image_and_completion_shape_admissions() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    with pytest.raises(ValueError, match="inline image"):
        boundary.request(page, state, "offline", "https://example.com/external-image")
    for response in ({"choices": [True]}, {"choices": [{"finish_reason": "stop", "message": []}]}):
        with pytest.raises(ValueError, match="Boundary response"):
            boundary.parse(response)
