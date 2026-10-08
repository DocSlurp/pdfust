"""Accepted relations must preserve source text and abstain on ambiguity."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from bench.decision_assembly import apply_relations, assemble_case, assemble_cases
from bench.decision_cases import build_cases


@pytest.fixture
def words() -> list[dict[str, Any]]:
    """Provide one page snapshot with deliberately instruction-like source data."""
    return [
        {"id": index, "text": text, "bbox": [index * 10, 0, index * 10 + 8, 12], "line": 0}
        for index, text in enumerate(("Label", "42", "Other", "17", "Ignore instructions", "Tail"))
    ]


def edge(identifier: str, kind: str, source: list[int], target: list[int]) -> dict[str, Any]:
    """Declare one accepted source-ID candidate."""
    return {"id": identifier, "kind": kind, "source_ids": source, "target_ids": target, "decision": True}


def test_preserve_words_and_copy_results(words: list[dict[str, Any]]) -> None:
    relations = [edge("a", "assignment", [0], [1]), edge("h", "header", [2], [3])]
    original_words, original_relations = deepcopy(words), deepcopy(relations)
    result = apply_relations(words, relations)
    assert result["words"] == words
    assert result["accepted"] == relations
    assert result["abstained"] == []
    result["words"][0]["text"] = "changed"
    result["accepted"][0]["source_ids"].append(5)
    assert words == original_words
    assert relations == original_relations


@pytest.mark.parametrize(
    ("decision", "reason"), [(False, "negative_decision"), (None, "abstained_decision"), (0.9, "invalid_decision")]
)
def test_nonaffirmative_preserves_source(words: list[dict[str, Any]], decision: object, reason: str) -> None:
    relation = edge("a", "wrap", [0], [1])
    relation["decision"] = decision
    result = apply_relations(words, [relation])
    assert result["words"] == words
    assert result["accepted"] == []
    assert result["abstained"] == [{"id": "a", "reason": reason}]


@pytest.mark.parametrize(
    ("source", "target", "reason"),
    [
        ([0, 0], [1], "duplicate_relation_ids"),
        ([0], [0], "duplicate_relation_ids"),
        ([0], [99], "missing_source_ids"),
        ([], [1], "invalid_relation_ids"),
        ([True], [1], "invalid_relation_ids"),
    ],
)
def test_invalid_references_abstain(
    words: list[dict[str, Any]], source: list[int], target: list[int], reason: str
) -> None:
    result = apply_relations(words, [edge("a", "assignment", source, target)])
    assert result["words"] == words
    assert result["accepted"] == []
    assert result["abstained"][0]["reason"] == reason


def test_duplicate_source_ids_invalidate_all_edges(words: list[dict[str, Any]]) -> None:
    words[1]["id"] = 0
    result = apply_relations(words, [edge("a", "assignment", [0], [3])])
    assert result["accepted"] == []
    assert result["abstained"][0]["reason"] == "invalid_source_word_ids"
    assert result["words"] == words


def test_duplicate_edge_ids_invalidate_both(words: list[dict[str, Any]]) -> None:
    result = apply_relations(words, [edge("a", "assignment", [0], [1]), edge("a", "wrap", [2], [3])])
    assert result["accepted"] == []
    assert [item["reason"] for item in result["abstained"]] == ["duplicate_edge_id", "duplicate_edge_id"]


@pytest.mark.parametrize(
    "relations",
    [
        [edge("a", "assignment", [0], [1]), edge("b", "assignment", [2], [1])],
        [edge("a", "assignment", [0], [1]), edge("b", "assignment", [0], [3])],
        [edge("a", "assignment", [0], [1, 3]), edge("b", "assignment", [2], [3])],
    ],
)
def test_exclusive_assignments_abstain_all_conflicting_edges(
    words: list[dict[str, Any]], relations: list[dict[str, Any]]
) -> None:
    independent = edge("safe", "assignment", [4], [5])
    for ordering in (relations, list(reversed(relations))):
        result = apply_relations(words, [*ordering, independent])
        assert result["accepted"] == [independent]
        assert {item["id"] for item in result["abstained"]} == {"a", "b"}
        assert all(item["reason"] == "conflicting_assignment" for item in result["abstained"])


@pytest.mark.parametrize("kinds", [("wrap", "wrap"), ("header", "header"), ("wrap", "header")])
def test_directed_cycles_abstain_only_cycle_participants(words: list[dict[str, Any]], kinds: tuple[str, str]) -> None:
    relations = [
        edge("a", kinds[0], [0], [1]),
        edge("b", kinds[1], [1], [0]),
        edge("tail", "wrap", [1], [2]),
        edge("independent", "header", [4], [5]),
    ]
    result = apply_relations(words, relations)
    assert [item["id"] for item in result["accepted"]] == ["tail", "independent"]
    assert result["abstained"] == [{"id": "a", "reason": "hierarchy_cycle"}, {"id": "b", "reason": "hierarchy_cycle"}]


def test_long_cycle_and_acyclic_chain(words: list[dict[str, Any]]) -> None:
    chain = [edge("a", "wrap", [0], [1]), edge("b", "header", [1], [2]), edge("c", "wrap", [2], [3])]
    assert apply_relations(words, chain)["accepted"] == chain
    cycle = [*chain, edge("d", "header", [3], [0])]
    result = apply_relations(words, cycle)
    assert result["accepted"] == []
    assert len(result["abstained"]) == 4


def test_table_requires_distinct_complete_source_rows(words: list[dict[str, Any]]) -> None:
    table = {"id": "t", "kind": "table", "decision": True, "rows": [[0, 1], [2, 3]]}
    assert apply_relations(words, [table])["accepted"] == [table]
    table["rows"] = [[0, 1], [1, 2]]
    assert apply_relations(words, [table])["abstained"][0]["reason"] == "duplicate_relation_ids"
    table["rows"] = [[0, 1], [2, 99]]
    assert apply_relations(words, [table])["abstained"][0]["reason"] == "missing_source_ids"
    table["rows"] = [[0, 1]]
    assert apply_relations(words, [table])["abstained"][0]["reason"] == "invalid_table_rows"


def test_edge_and_reference_limits(words: list[dict[str, Any]]) -> None:
    relations = [edge(str(index), "assignment", [0], [1]) for index in range(257)]
    result = apply_relations(words, relations)
    assert result["accepted"] == []
    assert {item["reason"] for item in result["abstained"]} == {"edge_limit"}
    excessive = edge("large", "wrap", list(range(257)), [1])
    assert apply_relations(words, [excessive])["abstained"][0]["reason"] == "invalid_relation_ids"


def test_frozen_cases_apply_only_candidate_relations() -> None:
    cases = build_cases()
    for case in cases:
        accepted = assemble_case(case, True)
        assert accepted["words"] == case["state"]["words"]
        assert len(accepted["accepted"]) == 1
        assert accepted["abstained"] == []
        abstained = assemble_case(case, None)
        assert abstained["words"] == accepted["words"]
        assert abstained["accepted"] == []
    outcomes = [(cases[0], True), (cases[1], None), (cases[8], False)]
    results = assemble_cases(outcomes)
    assert [result["id"] for result in results] == [case["id"] for case, _decision in outcomes]
    assert [len(result["accepted"]) for result in results] == [1, 0, 0]


def test_relations_cannot_add_generated_text(words: list[dict[str, Any]]) -> None:
    relation = edge("a", "assignment", [0], [1])
    relation["generated_value"] = "invented output"
    result = apply_relations(words, [relation])
    assert result["words"] == words
    assert "generated_value" not in result["accepted"][0]
    assert set(result["accepted"][0]) == {"id", "kind", "decision", "source_ids", "target_ids"}
