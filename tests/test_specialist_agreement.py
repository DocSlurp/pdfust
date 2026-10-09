"""Source partition agreement is stronger than complete textual matrix identity."""

from copy import deepcopy
from typing import Any

from bench.specialist_agreement import strict_agrees, text_agrees, unique_selection


def table() -> dict[str, Any]:
    """Return one complete frozen cell and its unresolved source inventory."""
    return {
        "row_count": 1,
        "col_count": 1,
        "values": [["Same text"]],
        "anchors": [[0, 0]],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}],
        "cells": [{"source_ids": ["w0"]}],
        "unresolved_ids": ["w1"],
    }


def prediction() -> dict[str, Any]:
    """Retain one decoded HTML anchor and its predicted-cell center ownership."""
    return {
        "matrices": [table()],
        "observed": {"outputs": [{}]},
        "ownership": {
            "cells": [{"output": 0, "cell": 0, "source_ids": ["dev-000-w0"]}],
            "unresolved_ids": ["dev-000-w1"],
        },
    }


def test_strict_matching_source_partition_accepts() -> None:
    """A complete, identical source partition is accepted independently of labels."""
    assert strict_agrees(prediction(), table())


def test_equal_text_with_wrong_sources_is_only_weak_agreement() -> None:
    """Identical words cannot substitute for exact source-ID cell ownership."""
    other = table()
    other["cells"][0]["source_ids"] = ["w1"]
    other["unresolved_ids"] = ["w0"]
    assert text_agrees(prediction()["matrices"][0], other)
    assert not strict_agrees(prediction(), other)


def test_missing_cell_anchor_correspondence_defers() -> None:
    """A missing predicted cell-to-HTML mapping is not repaired from a reference."""
    observed = prediction()
    observed["ownership"]["cells"] = []
    assert not strict_agrees(observed, table())


def test_span_difference_refuses_both_rules() -> None:
    """Explicit spans are compared even when displayed text happens to match."""
    other = table()
    other["spans"][0]["column_span"] = 2
    assert not text_agrees(table(), other)
    assert not strict_agrees(prediction(), other)


def test_duplicate_hypotheses_deduplicate_but_conflict_defers() -> None:
    """Identical source hypotheses count once; conflicting partitions defer."""
    assert unique_selection([table(), deepcopy(table())]) is not None
    other = table()
    other["cells"][0]["source_ids"] = ["w1"]
    assert unique_selection([table(), other]) is None
