"""Apply bounded accepted relations over retained PDF source IDs.

This experiment records logical edges without generating, merging, deleting, or
reordering source text. It does not reconstruct a PDF, infer missing cells, or
prove pixel visibility. Source IDs must belong to one immutable page snapshot;
case snapshots remain isolated even when their integer IDs overlap.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

_MAX_EDGES = 256
_MAX_REFERENCES = 256
_MAX_WORDS = 65_536
_KINDS = {"table", "wrap", "header", "assignment"}


def _ids(value: object) -> list[int] | None:
    if not isinstance(value, list) or not value or len(value) > _MAX_REFERENCES:
        return None
    if any(type(item) is not int for item in value):
        return None
    return value


def _validate(edge: dict[str, Any], word_ids: set[int]) -> str | None:  # noqa: C901, PLR0911
    if not isinstance(edge.get("kind"), str) or edge["kind"] not in _KINDS:
        return "invalid_relation_kind"
    if edge.get("decision") is not True:
        if edge.get("decision") is False:
            return "negative_decision"
        return "abstained_decision" if edge.get("decision") is None else "invalid_decision"
    if edge["kind"] == "table":
        rows = edge.get("rows")
        if not isinstance(rows, list) or len(rows) < 2 or len(rows) > _MAX_REFERENCES:  # noqa: PLR2004
            return "invalid_table_rows"
        if any(_ids(row) is None or len(row) < 2 for row in rows):  # noqa: PLR2004
            return "invalid_table_rows"
        references = [wid for row in rows for wid in row]
    else:
        source, target = _ids(edge.get("source_ids")), _ids(edge.get("target_ids"))
        if source is None or target is None:
            return "invalid_relation_ids"
        references = source + target
    if len(references) > _MAX_REFERENCES:
        return "reference_limit"
    if len(set(references)) != len(references):
        return "duplicate_relation_ids"
    if not set(references) <= word_ids:
        return "missing_source_ids"
    return None


def _assignment_conflicts(edges: list[dict[str, Any]]) -> set[int]:
    assignments = [
        (index, set(edge["source_ids"]), set(edge["target_ids"]))
        for index, edge in enumerate(edges)
        if edge["kind"] == "assignment"
    ]
    conflicts: set[int] = set()
    for offset, (index, source, target) in enumerate(assignments):
        for other_index, other_source, other_target in assignments[offset + 1 :]:
            if (source & other_source and target != other_target) or (target & other_target and source != other_source):
                conflicts.update((index, other_index))
    return conflicts


def _hierarchy_cycles(edges: list[dict[str, Any]]) -> set[int]:
    directed = {
        index: (set(edge["source_ids"]), set(edge["target_ids"]))
        for index, edge in enumerate(edges)
        if edge["kind"] in {"wrap", "header"}
    }
    graph = {
        index: {other for other, (source, _target) in directed.items() if target & source}
        for index, (_source, target) in directed.items()
    }
    cycles: set[int] = set()
    for index, successors in graph.items():
        pending = list(successors)
        seen = set()
        while pending:
            current = pending.pop()
            if current == index:
                cycles.add(index)
                break
            if current not in seen:
                seen.add(current)
                pending.extend(graph[current] - seen)
    return cycles


def apply_relations(words: Sequence[dict[str, Any]], edges: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Retain source words and admit only valid, nonconflicting affirmative edges.

    Each edge supplies a unique nonempty string ``id``, a ``kind``, and a
    thresholded ``decision`` (True, False, or None). Directed kinds additionally
    supply nonempty ``source_ids`` and ``target_ids`` lists. Table edges supply
    two or more ``rows`` of two or more IDs. Lists cannot repeat IDs. Assignment
    ownership is exclusive in both directions. Wrap/header edges share a cycle
    check; every cycle participant abstains. Conflicting edges all abstain,
    irrespective of their input order. Word dictionaries are copied verbatim; unrelated edge metadata is discarded.
    """
    retained = deepcopy(list(words))
    result: dict[str, Any] = {"words": retained, "accepted": [], "abstained": []}
    if len(words) > _MAX_WORDS:
        result["abstained"] = [{"id": edge.get("id"), "reason": "word_limit"} for edge in edges]
        return result
    if len(edges) > _MAX_EDGES:
        result["abstained"] = [{"id": edge.get("id"), "reason": "edge_limit"} for edge in edges]
        return result
    source_ids = [word.get("id") for word in words]
    invalid_source = any(type(wid) is not int for wid in source_ids) or len(set(source_ids)) != len(source_ids)
    word_ids = {wid for wid in source_ids if type(wid) is int}
    edge_ids = Counter(edge.get("id") for edge in edges if isinstance(edge.get("id"), str))
    valid: list[dict[str, Any]] = []
    for edge in edges:
        identifier = edge.get("id")
        reason: str | None
        if invalid_source:
            reason = "invalid_source_word_ids"
        elif not isinstance(identifier, str) or not identifier:
            reason = "invalid_edge_id"
        elif edge_ids[identifier] != 1:
            reason = "duplicate_edge_id"
        else:
            reason = _validate(edge, word_ids)
        if reason is None:
            keys = (
                ("id", "kind", "decision", "rows")
                if edge["kind"] == "table"
                else ("id", "kind", "decision", "source_ids", "target_ids")
            )
            valid.append({key: deepcopy(edge[key]) for key in keys})
        else:
            result["abstained"].append({"id": identifier, "reason": reason})
    conflicts, cycles = _assignment_conflicts(valid), _hierarchy_cycles(valid)
    for index, edge in enumerate(valid):
        if index in conflicts or index in cycles:
            reason = "conflicting_assignment" if index in conflicts else "hierarchy_cycle"
            result["abstained"].append({"id": edge["id"], "reason": reason})
        else:
            result["accepted"].append(edge)
    return result


def assemble_case(case: dict[str, Any], decision: bool | None) -> dict[str, Any]:  # noqa: FBT001
    """Apply a thresholded outcome to exactly its supplied frozen candidate."""
    state = case["state"]
    kind, candidate = state["task"], state["candidate"]
    edge: dict[str, Any] = {"id": case["id"], "kind": kind, "decision": decision}
    if kind == "table":
        edge["rows"] = candidate["rows"]
    elif kind == "wrap":
        edge.update(source_ids=candidate["from"], target_ids=candidate["to"])
    elif kind == "header":
        edge.update(source_ids=candidate["header"], target_ids=[wid for group in candidate["values"] for wid in group])
    elif kind == "assignment":
        edge.update(source_ids=candidate["label"], target_ids=candidate["value"])
    return {"id": case["id"], **apply_relations(state["words"], [edge])}


def assemble_cases(outcomes: Sequence[tuple[dict[str, Any], bool | None]]) -> list[dict[str, Any]]:
    """Apply outcomes in independent snapshots; never mix page-local source IDs."""
    return [assemble_case(case, decision) for case, decision in outcomes]
