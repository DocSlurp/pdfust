"""Association equivalence and bounded allocation checks without model imports."""

# Optional isolated NumPy arrays are deliberately typed dynamically.
# ruff: noqa: ANN401

from __future__ import annotations

import importlib.metadata
import sys
from typing import Any

import pytest

np = pytest.importorskip("numpy", reason="cell matching needs optional CPU benchmark NumPy")
try:
    importlib.metadata.version("rapid-table")
except importlib.metadata.PackageNotFoundError:
    pytest.skip("upstream TableMatch is an optional isolated benchmark dependency", allow_module_level=True)

from bench.cell_matching import (  # noqa: E402
    MAX_CELLS,
    MAX_CHUNK_WORDS,
    MAX_WORDS,
    admitted_arrays,
    match_cells,
    optimized,
    reference,
    upstream_matcher,
)


def arrays(values: list[list[float]], *, width: int = 4, dtype: str = "float32") -> Any:
    """Give empty inputs a defined two-dimensional shape."""
    return np.array(values, dtype=dtype).reshape(-1, width)


def parity(cells: Any, words: Any, *, chunk: int = 64) -> None:
    """Compare exact filtered associations and HTML against installed source."""
    matcher, _ = upstream_matcher()
    ids = [f"word-{index}" for index in range(len(words))]
    records = [(f"source {index}", 1.0) for index in range(len(words))]
    tags = ["<table><tr>", *["<td></td>"] * len(cells), "</tr></table>"]
    baseline, baseline_html = reference(matcher, cells, words, records, tags)
    observed, observed_html = optimized(matcher, cells, words, records, tags, ids, chunk_words=chunk)
    assert observed.matches == baseline
    assert observed_html == baseline_html


def test_identical_cells_choose_earliest_index() -> None:
    cells = arrays([[0, 0, 10, 10], [0, 0, 10, 10]])
    words = arrays([[1, 1, 9, 9]])
    result = match_cells(cells, words, ["source"])
    assert result.matches == {0: [0]}
    assert result.unassigned_ids == ()
    parity(cells, words)


def test_equal_iou_uses_corner_weighted_distance() -> None:
    cells = arrays([[0, 0, 40, 10], [0, 0, 20, 20]])
    words = arrays([[0, 0, 10, 10]])
    result = match_cells(cells, words, ["source"])
    assert result.matches == {1: [0]}
    parity(cells, words)


def test_nonoverlap_and_filtered_words_remain_unassigned() -> None:
    cells = arrays([[0, 20, 10, 30]])
    words = arrays([[0, 0, 10, 10], [40, 20, 50, 30], [1, 21, 9, 29]])
    result = match_cells(cells, words, ["above", "beside", "inside"])
    assert result.kept_indexes == (1, 2)
    assert result.matches == {0: [1]}
    assert result.filtered_ids == ("above",)
    assert result.unassigned_ids == ("above", "beside")
    parity(cells, words)


@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_degenerate_and_inverted_rectangles(dtype: str) -> None:
    cells = arrays([[0, 0, 0, 10], [0, 0, 10, 0], [20, 20, 10, 10], [0, 0, 10, 10]], dtype=dtype)
    words = arrays([[0, 0, 0, 10], [20, 20, 10, 10], [1, 1, 9, 9]], dtype=dtype)
    result = match_cells(cells, words, ["zero-width", "inverted", "valid"])
    assert result.matches == {3: [2]}
    assert result.unassigned_ids == ("zero-width", "inverted")
    parity(cells, words)


def test_empty_inputs_are_defined_without_source_loss() -> None:
    words = arrays([[1, 1, 2, 2]])
    empty = arrays([])
    result = match_cells(empty, words, ["source"])
    assert result.matches == {}
    assert result.unassigned_ids == ("source",)
    assert result.chunk_pairs == 0
    result = match_cells(arrays([[0, 0, 10, 10]]), empty, [])
    assert result.matches == {}
    assert result.unassigned_ids == ()
    parity(arrays([[0, 0, 10, 10]]), empty)


@pytest.mark.parametrize("dtype", ["float32", "float64"])
@pytest.mark.parametrize("chunk", [1, 7, 64])
def test_polygon_and_chunk_equivalence(dtype: str, chunk: int) -> None:
    rng = np.random.default_rng(20261008)
    origin = rng.uniform(0, 80, size=(24, 2))
    extent = rng.uniform(3, 25, size=(24, 2))
    cells = np.column_stack((origin, origin + extent * [1, 0], origin + extent, origin + extent * [0, 1])).astype(dtype)
    starts = rng.uniform(0, 100, size=(47, 2))
    words = np.column_stack((starts, starts + rng.uniform(1, 12, size=(47, 2)))).astype(dtype)
    parity(cells, words, chunk=chunk)


def test_float32_near_threshold_and_iou_rounding() -> None:
    cells = arrays([[0, 0, 10000, 10000], [1, 1, 10001, 10001]])
    words = arrays([[0, 0, 1, 1], [1, 1, 2, 2], [10, 10, 20, 20]])
    parity(cells, words)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 10000001.0])
def test_coordinate_admission(value: float) -> None:
    with pytest.raises(ValueError, match="coordinate"):
        match_cells(arrays([[0, 0, value, 10]]), arrays([[1, 1, 2, 2]]), ["source"])


def test_count_and_scratch_boundaries() -> None:
    cells = np.zeros((MAX_CELLS, 4), dtype=np.float32)
    words = np.zeros((MAX_WORDS, 4), dtype=np.float32)
    source_ids = [f"source-{index}" for index in range(MAX_WORDS)]
    admitted_arrays(cells, words, source_ids, 64)
    with pytest.raises(ValueError, match="count"):
        match_cells(np.zeros((MAX_CELLS + 1, 4), dtype=np.float32), words[:1], source_ids[:1])
    with pytest.raises(ValueError, match="count"):
        match_cells(cells[:1], np.zeros((MAX_WORDS + 1, 4), dtype=np.float32), ["source"] * (MAX_WORDS + 1))
    with pytest.raises(ValueError, match="scratch"):
        match_cells(cells, words[:65], source_ids[:65], chunk_words=65)
    with pytest.raises(ValueError, match="chunk_words"):
        match_cells(cells[:1], words[:1], source_ids[:1], chunk_words=MAX_CHUNK_WORDS + 1)


def test_duplicate_source_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="source IDs"):
        match_cells(arrays([[0, 0, 10, 10]]), arrays([[1, 1, 2, 2], [3, 3, 4, 4]]), ["duplicate", "duplicate"])


def test_upstream_loader_imports_no_model_or_runtime() -> None:
    before = set(sys.modules)
    matcher, metadata = upstream_matcher()
    assert matcher is not None
    assert metadata["source_sha256"]["main.py"]
    added = set(sys.modules) - before
    assert not any(
        name.startswith(("onnxruntime", "rapid_table.table_structure", "rapid_table.main")) for name in added
    )
