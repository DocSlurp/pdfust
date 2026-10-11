"""Applied-edit attribution excludes preserved historical tables and failures."""
from copy import deepcopy
from typing import Any

import pytest
from bench.p003_additional_incremental_audit import primary


def fixture() -> dict[str, Any]:
    table = {"row_count": 1, "col_count": 1, "values": [["a b"]], "cells": [[{"source_ids": [0, 1]}]], "spans": []}
    old = {**table, "values": [["a"], ["b"]], "row_count": 2}
    page = {"id": "test", "status": "ok", "repair_status": "completed", "tables": [{**table, "bbox": [0, 0, 10, 10]}],
            "repair_regions": [{"repair_status": "completed", "original_state": {"tables": [old]},
                                "updated_state": {"tables": [table]}, "audit": {"joined": ["b0"]}}]}
    return {"config": {"processor": "p003_boundary_repair"}, "results": [page]}


def test_only_applied_complete_edit_is_credited() -> None:
    report = fixture()
    rows, scope = primary(report)
    assert rows[0]["tables"] == report["results"][0]["tables"]
    assert rows[0]["applied_join_count"] == 1
    assert "geometry included" in scope


@pytest.mark.parametrize("failure", ["failed_retained_baseline", "not_applicable"])
def test_fallback_has_no_tables(failure: str) -> None:
    report = fixture()
    report["results"][0]["repair_status"] = failure
    assert primary(report)[0][0]["tables"] == []


def test_completed_below_threshold_or_unchanged_has_no_credit() -> None:
    report = fixture()
    region = report["results"][0]["repair_regions"][0]
    region["updated_state"] = deepcopy(region["original_state"])
    assert primary(report)[0][0]["tables"] == []
    report = fixture()
    report["results"][0]["repair_regions"][0]["audit"]["joined"] = []
    assert primary(report)[0][0]["tables"] == []


def test_missing_actual_complete_output_refuses() -> None:
    report = fixture()
    report["results"][0]["tables"] = []
    with pytest.raises(ValueError, match="absent"):
        primary(report)
