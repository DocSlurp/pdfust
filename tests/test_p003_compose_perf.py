"""Set reuse must preserve refusals and exact ownership, not skip useful work."""
from copy import deepcopy
from typing import Any

import pytest
from bench import p003_compose_perf as experiment


def data() -> tuple[dict[str, Any], dict[str, Any]]:
    source = {"page_size": [0, 0, 100, 100], "words": [
        {"id": "w0", "text": "same", "bbox": [1, 1, 2, 2]},
        {"id": "w1", "text": "same", "bbox": [11, 1, 12, 2]},
        {"id": "w2", "text": "unresolved", "bbox": [1, 50, 20, 60]},
    ]}
    table = {"row_count": 1, "col_count": 2, "bbox": [0, 0, 20, 10],
             "values": [["same", "same"]],
             "cells": [{"source_ids": ["w0"], "role": "unknown"},
                       {"source_ids": ["w1"], "role": "unknown"}],
             "spans": [{"row": 0, "column": c, "row_span": 1, "column_span": 1} for c in range(2)]}
    return source, {"status": "prepared", "table": table}


@pytest.mark.parametrize("case", ["normal", "overlap", "error"])
def test_identical_composition_and_unmutated_inputs(case: str) -> None:
    source, proposal = data()
    proposals = [proposal]
    if case == "overlap":
        proposals.append(deepcopy(proposal))
    elif case == "error":
        proposals.append({"status": "postprocess_error", "table": None})
    before = deepcopy((source, proposals))
    assert experiment.cached_set(source, proposals) == experiment.baseline.compose(source, proposals)
    assert (source, proposals) == before


def test_duplicate_ownership_still_refuses() -> None:
    source, proposal = data()
    second = deepcopy(proposal)
    second["table"]["bbox"] = [40, 40, 60, 60]
    for operation in (experiment.baseline.compose, experiment.cached_set):
        with pytest.raises(ValueError, match="Cross-table source duplication"):
            operation(source, [proposal, second])


def test_measurement_cannot_pass_skipped_work(monkeypatch: pytest.MonkeyPatch) -> None:
    source, proposal = data()
    record = {"id": "test", "size": 1280, "threshold": 0.5,
              "source": source, "proposals": [proposal], **experiment.baseline.compose(source, [proposal])}
    monkeypatch.setattr(experiment, "cached_set", lambda *_: {})
    with pytest.raises(ValueError, match="immutable original output"):
        experiment.measure([record], "cached_set")
