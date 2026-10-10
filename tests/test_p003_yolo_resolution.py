"""Matched detector settings and lossless geometry admission without actual model calls."""

from __future__ import annotations

import math

import pytest
from bench import p003_yolo_resolution as yolo


def _box() -> dict:
    return {"class_id": 8, "label": "table", "confidence": 0.7, "pixel_bbox": [10.0, 20.0, 80.0, 90.0]}


def test_only_resolution_changes_between_prediction_arms() -> None:
    configs = [yolo.configuration(s) for s in yolo.SIZES]
    assert [c.pop("imgsz") for c in configs] == [640, 1024, 1280]
    assert configs[0] == configs[1] == configs[2]
    assert configs[0]["device"] == "cpu"
    assert configs[0]["batch"] == 1
    assert configs[0]["conf"] == 0.25
    with pytest.raises(ValueError, match="resolution"):
        yolo.configuration(True)


def test_projection_preserves_class_confidence_and_offset_viewport() -> None:
    box = _box()
    other = {**box, "class_id": 1, "label": "text"}
    projected = yolo.project([box, other], [100.0, 200.0, 300.0, 400.0], [100, 100])
    assert projected[0] == {**box, "global_bbox": [120.0, 240.0, 260.0, 380.0]}
    assert projected[1]["label"] == "text"
    assert "global_bbox" not in box


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("confidence", True),
        ("confidence", math.nan),
        ("pixel_bbox", [-1.0, 0.0, 10.0, 10.0]),
        ("pixel_bbox", [0.0, 0.0, 101.0, 100.0]),
        ("class_id", True),
    ],
)
def test_invalid_raw_geometry_is_refused_without_clipping(field: str, value: object) -> None:
    box = {**_box(), field: value}
    with pytest.raises(ValueError, match="out-of-frame"):
        yolo.project([box], [0.0, 0.0, 100.0, 100.0], [100, 100])


def test_complete_box_and_pixel_boundaries_refuse_not_truncate() -> None:
    with pytest.raises(ValueError, match="admission"):
        yolo.project([_box()] * (yolo.MAX_BOXES + 1), [0.0, 0.0, 100.0, 100.0], [100, 100])
    with pytest.raises(ValueError, match="admission"):
        yolo.project([], [0.0, 0.0, 100.0, 100.0], [3000, 3000])
    with pytest.raises(ValueError, match="admission"):
        yolo.project([], [0.0, 0.0, 100.0, 100.0], [0, 100])
