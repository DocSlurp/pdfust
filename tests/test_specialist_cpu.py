"""Deterministic CPU-pilot guards without downloading or running a model."""

from __future__ import annotations

import pytest
from bench.feature_cases import page_pdf, text_op
from bench.specialist_cpu import (
    contains_center,
    merge_regions,
    opaque_bgr,
    pixel_region,
    project_box,
    require_cpu,
)
from bench.structure_core import score_tables

import pdfust


def test_cpu_provider_must_be_exclusive() -> None:
    require_cpu(["CPUExecutionProvider"])
    for providers in (
        [],
        ["CUDAExecutionProvider", "CPUExecutionProvider"],
        ["AzureExecutionProvider"],
        ["DmlExecutionProvider"],
        ["CANNExecutionProvider"],
    ):
        with pytest.raises(RuntimeError, match="CPU-only"):
            require_cpu(providers)


def test_crop_coordinate_projection_uses_actual_raster_scale() -> None:
    assert project_box([10, 20, 30, 40], (5, 10), (2, 3)) == [15, 50, 55, 110]
    assert pixel_region([-1, 1.1, 9.8, 30], (2, 3), (18, 60)) == (0, 3, 18, 60)
    assert contains_center([10, 10, 20, 20], [9, 9, 13, 13])
    assert not contains_center([10, 10, 20, 20], [1, 1, 3, 3])


def test_merging_avoids_duplicate_source_replacement() -> None:
    regions: list[list[float]] = [[0, 0, 10, 10], [20, 20, 30, 30], [8, 8, 21, 21]]
    assert merge_regions(regions) == [[0, 0, 30, 30]]
    assert regions[0] == [0, 0, 10, 10]


def test_crop_count_is_bounded() -> None:
    with pytest.raises(RuntimeError, match="region count"):
        merge_regions([[index * 3, 0, index * 3 + 1, 1] for index in range(9)])


def test_failed_predictions_keep_cell_denominator() -> None:
    gold = ((("Name", "Amount"), ("Alpha", "42")),)
    score = score_tables([], gold)
    assert score["correct_cells"] == 0
    assert score["total_cells"] == 4
    assert not score["exact"]
    assert not score_tables([[["prose"]]], ())["exact"]


def test_raster_requires_opaque_compositing_and_visible_content() -> None:
    np = pytest.importorskip("numpy")

    rgba = np.zeros((2, 2, 4), dtype=np.uint8)
    with pytest.raises(RuntimeError, match="opaque white"):
        opaque_bgr(rgba)
    rgba[:, :, :] = 255
    with pytest.raises(RuntimeError, match="blank"):
        opaque_bgr(rgba)
    rgba[0, 0, :3] = [20, 40, 60]
    bgr = opaque_bgr(rgba)
    assert bgr[0, 0].tolist() == [60, 40, 20]
    assert int(bgr.max()) > int(bgr.min())


def test_pdf_fixture_renders_visible_on_white() -> None:
    np = pytest.importorskip("numpy")

    with pdfust.open(stream=page_pdf(text_op("Visible input", 40, 700))) as document:
        pixmap = document[0].get_pixmap(dpi=72, background=(255, 255, 255))
        rgba = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 4)
        assert bool((rgba[:, :, 3] == 255).all())
        raster = opaque_bgr(rgba)
        assert int(raster.min()) < 255
        assert int(raster.max()) == 255
