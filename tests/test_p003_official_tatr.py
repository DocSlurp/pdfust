"""Upstream cell adapters must retain complete source ownership and failure semantics."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench.p003_official_tatr import compose, decode, load_upstream


def source() -> dict[str, Any]:
    return {"page_size": [0, 0, 100, 100], "words": [
        {"id": "w0", "text": "same", "bbox": [10, 10, 20, 20]},
        {"id": "w1", "text": "same", "bbox": [60, 10, 70, 20]},
        {"id": "w2", "text": "outside", "bbox": [10, 80, 30, 90]},
    ]}


def upstream(*, duplicate: bool = False, missing: bool = False) -> SimpleNamespace:
    def cells(_table: object, _objects: object, tokens: list[dict[str, Any]],
              _names: object, _thresholds: object) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
        result = [
            {"row_nums": [0], "column_nums": [0], "spans": [tokens[0]]},
            {"row_nums": [0], "column_nums": [1], "spans": [tokens[0 if duplicate else 1]]},
        ]
        if missing:
            result.pop()
        return {"rows": [{}], "columns": [{}, {}]}, result, 0.9
    return SimpleNamespace(iob=lambda _word, _box: 1.0, objects_to_cells=cells)


def decoded(**kwargs: bool) -> dict[str, Any]:
    return decode(source(), {"source_ids": ["w0", "w1"]}, {
        "threshold": 0.5, "objects": [{"bbox": [0, 0, 80, 30], "score": 0.99, "label": "table"}],
    }, upstream(**kwargs))


def test_duplicate_literal_text_keeps_distinct_source_ids_and_unresolved_word() -> None:
    result = compose(source(), [decoded()])
    assert [c["source_ids"] for c in result["state"]["tables"][0]["cells"]] == [["w0"], ["w1"]]
    assert result["state"]["unresolved_ids"] == ["w2"]


@pytest.mark.parametrize("kwargs", [{"duplicate": True}, {"missing": True}])
def test_bad_upstream_ownership_or_tiling_refuses(kwargs: dict[str, bool]) -> None:
    with pytest.raises(ValueError, match="Upstream"):
        decoded(**kwargs)


def test_overlap_refuses_both_and_retains_all_source() -> None:
    first = decoded()
    result = compose(source(), [first, deepcopy(first)])
    assert result["state"]["tables"] == []
    assert result["state"]["unresolved_ids"] == ["w0", "w1", "w2"]
    assert result["conflicting_table_indices"] == [0, 1]


def test_unexpected_upstream_error_cannot_credit_partial_page() -> None:
    result = compose(source(), [decoded(), {"status": "postprocess_error", "table": None}])
    assert result["state"]["tables"] == []
    assert result["state"]["unresolved_ids"] == ["w0", "w1", "w2"]


def test_altered_download_is_never_executed(tmp_path: Path) -> None:
    (tmp_path / "postprocess.py").write_text("raise RuntimeError('must not execute')")
    (tmp_path / "LICENSE").write_text("altered")
    with pytest.raises(ValueError, match="Pinned upstream"):
        load_upstream(tmp_path)
