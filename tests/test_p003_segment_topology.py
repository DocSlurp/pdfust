"""Source conservation and actual topology changes in bounded segment proposals."""

from __future__ import annotations

from typing import Any

import pytest
from bench import p003_segment_topology as s
from bench.pipeline_repair import validate


def source(rows: int = 3, cols: int = 2) -> dict[str, Any]:
    """Generate repeated literal words with separate source identities."""
    return {
        "page_size": [0, 0, 400, 400],
        "words": [
            {"id": f"w{r}-{c}", "text": "literal", "bbox": [10 + c * 40, 10 + r * 15, 20 + c * 40, 20 + r * 15]}
            for r in range(rows)
            for c in range(cols)
        ],
    }


def test_topology_changes_and_literal_conservation() -> None:
    """Both joins and splits change table dimensions, while duplicates survive."""
    page = source()
    plan = s.freeze(page, [w["id"] for w in page["words"]], [0, 0, 100, 100])
    pool = s.candidates(page, plan)
    assert len(plan["column_proposals"]) == 1
    assert len(plan["row_proposals"]) == 2
    assert len(pool) == 8
    assert pool[0]["topology"] == [{"rows": 3, "columns": 2}]
    assert {tuple(p["topology"][0][k] for k in ("rows", "columns")) for p in pool} == {
        (r, c) for r in (1, 2, 3) for c in (1, 2)
    }
    for candidate in pool:
        validate(page, candidate["state"])
        ids = [i for t in candidate["state"]["tables"] for c in t["cells"] for i in c["source_ids"]]
        assert set(ids) == {w["id"] for w in page["words"]}
    assert s.freeze(page, [w["id"] for w in page["words"]], [0, 0, 100, 100]) == plan


def test_eight_boundary_cap_and_explicit_refusals() -> None:
    """A large menu remains exactly bounded without hidden proposal truncation."""
    page = source(9, 7)
    plan = s.freeze(page, [w["id"] for w in page["words"]], page["page_size"])
    assert plan["boundary_count"] == 8
    assert len(s.candidates(page, plan)) == 256
    assert {p["reason"] for p in plan["proposal_refusals"]} >= {"row_boundary_cap", "column_boundary_cap"}
    assert plan["owned_words_omitted_count"] == 0


def test_crossing_word_is_unresolved_and_complete_literal_retained() -> None:
    """A whole word crossing a proposed column is not split or silently reassigned."""
    page = source(3)
    page["words"].append({"id": "cross", "text": "whole payload", "bbox": [25, 75, 45, 85]})
    page["words"].append({"id": "outside", "text": "context", "bbox": [110, 10, 120, 20]})
    plan = s.freeze(page, [w["id"] for w in page["words"]], [0, 0, 100, 100])
    state = s.candidates(page, plan)[0]["state"]
    assert {"cross", "outside"} <= set(state["unresolved_ids"])
    assert ["cross", "whole payload", 25, 75, 45, 85] in plan["literal_words"]
    assert plan["words_excluded_from_assignment"] == [
        {"source_id": "outside", "reason": "outside_or_nonpositive_crop_geometry"}
    ]
    validate(page, state)


def test_foreign_identity_or_modified_source_is_rejected() -> None:
    """Frozen menus are source-specific, and arbitrary choices cannot expand topology."""
    page = source()
    with pytest.raises(ValueError, match="ownership"):
        s.freeze(page, ["missing"], page["page_size"])
    plan = s.freeze(page, [w["id"] for w in page["words"]], page["page_size"])
    with pytest.raises(ValueError, match="boundary"):
        s.decode(page, plan, ["invented"])
    page["words"][0]["text"] = "changed"
    with pytest.raises(ValueError, match="source changed"):
        s.decode(page, plan, [])


def test_empty_crop_and_conflict_composition_keep_all_ids_unresolved() -> None:
    """No-candidate pages and overlapping table hypotheses remain explicit abstentions."""
    page = source()
    empty = s.freeze(page, [], page["page_size"])
    assert empty["status"] == "no_candidate_refusal"
    assert not s.candidates(page, empty)[0]["state"]["tables"]
    plan = s.freeze(page, [w["id"] for w in page["words"]], page["page_size"])
    candidate = s.candidates(page, plan)[0]["state"]
    composed = s.compose(page, [candidate, candidate])
    assert composed["conflicting_table_indices"] == [0, 1]
    assert not composed["tables"]
    assert len(composed["unresolved_ids"]) == len(page["words"])
    validate(page, composed)


def test_composition_rejects_invalid_selected_state_before_conflict_removal() -> None:
    """Dropping overlapping hypotheses must not hide a malformed source partition."""
    page = source()
    invalid = {"id": "c0", "tables": [], "unresolved_ids": []}
    with pytest.raises(ValueError, match="exactly one owner"):
        s.compose(page, [invalid])
