"""Fixed source tiling, duplicate suppression, and explicit boundary abstention."""

import io
from collections import Counter
from typing import Any

import pytest
from bench.pipeline_layout_tiles import class_nms, multiscale, tile_regions, tile_windows
from PIL import Image


def test_overlap_tiles_cover_source_and_respect_pixel_boundary() -> None:
    for grid in (2, 3):
        windows = tile_windows(3072, 2400, grid)
        assert len(windows) == grid * grid
        assert windows[0][:2] == [0, 0]
        assert windows[-1][2:] == [3072, 2400]
        assert all((box[2] - box[0]) * (box[3] - box[1]) <= 4_000_000 for box in windows)
        assert windows[0][2] > windows[1][0]
        assert windows[0][3] > windows[grid][1]
    with pytest.raises(ValueError, match="admission"):
        tile_windows(3073, 2400, 2)
    with pytest.raises(ValueError, match="two or three"):
        tile_windows(300, 300, 4)


def detection(label: str = "Table", confidence: float = 0.9, *, edge: bool = False) -> dict[str, Any]:
    return {
        "label": label,
        "confidence": confidence,
        "bbox": [0, 0, 50, 50],
        "call_id": "g2-t0",
        "tile_viewport": [0, 0, 50, 50],
        "tile_boundary_risk": edge,
    }


def test_class_aware_nms_preserves_classes_and_deterministic_confidence_priority() -> None:
    first = detection(confidence=0.8)
    second = detection(confidence=0.9)
    other = detection("Text")
    boxes = class_nms([first, second, other])
    assert [box["label"] for box in boxes] == ["Table", "Text"]
    assert boxes[0]["confidence"] == 0.9
    assert first["confidence"] == 0.8
    with pytest.raises(ValueError, match="confidence"):
        class_nms([detection(confidence=float("nan"))])


def source() -> dict[str, Any]:
    return {
        "page_size": [100, 100],
        "vector_candidates": [],
        "words": [
            {"id": "global0", "text": "literal", "bbox": [5, 5, 15, 15]},
            {"id": "global1", "text": "crossing", "bbox": [45, 20, 55, 30]},
            {"id": "global2", "text": "residual", "bbox": [70, 70, 90, 80]},
        ],
    }


def test_boundary_fragments_abstain_and_source_ids_remain_exact_partition() -> None:
    plan = tile_regions(source(), [detection(edge=True)])
    owned = next(region for region in plan["regions"] if region["kind"] == "detector_proposal")
    assert owned["boundary"] == "detector_tile_boundary"
    assert not owned["context_complete"]
    assert owned["detector"]["source_words_cross_tile"]
    assert Counter(i for region in plan["regions"] for i in region["source_ids"]) == Counter(
        ["global0", "global1", "global2"]
    )


def test_source_word_crossing_alone_requires_boundary_abstention() -> None:
    plan = tile_regions(source(), [detection(edge=False)])
    owned = next(region for region in plan["regions"] if region["kind"] == "detector_proposal")
    assert not owned["detector"]["tile_boundary_risk"]
    assert owned["detector"]["source_words_cross_tile"]
    assert not owned["context_complete"]


def test_multiscale_retains_all_calls_and_maps_interior_boundary_evidence() -> None:
    class FakeDetector:
        def detect(self, image: bytes, *, viewport: list[float]) -> dict[str, Any]:
            with Image.open(io.BytesIO(image)) as pixels:
                assert pixels.getpixel((0, 0)) == (255, 255, 255)
                size = list(pixels.size)
            return {
                "image_size": size,
                "boxes": [
                    {
                        "label": "Table",
                        "confidence": 0.9,
                        "bbox": list(viewport),
                        "normalized_bbox": [0, 0, 1, 1],
                        "pixel_bbox": [0, 0, *size],
                    }
                ],
            }

    body = io.BytesIO()
    Image.new("RGBA", (300, 600), (0, 0, 0, 0)).save(body, format="PNG")
    result = multiscale(FakeDetector(), body.getvalue(), viewport=[20, 40, 320, 640])  # type: ignore[arg-type]
    assert len(result["calls"]) == 14
    assert result["raw_box_count"] == 14
    assert result["calls"][0]["boxes"][0]["bbox"] == [20, 40, 320, 640]
    assert not result["calls"][0]["boxes"][0]["tile_boundary_risk"]
    assert all(call["boxes"][0]["tile_boundary_risk"] for call in result["calls"][1:])
    for call in result["calls"]:
        assert call["tile_viewport"][0] >= 20
        assert call["tile_viewport"][2] <= 320
