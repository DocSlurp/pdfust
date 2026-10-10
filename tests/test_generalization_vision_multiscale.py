"""Fixed raw detector mapping and atomic crop reuse need no model inference."""

# Heterogeneous JSON fixtures model retained detector responses.
# ruff: noqa: ANN401, EM101, TRY003
import io
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_vision_multiscale as multi
from bench.generalization_vision_regions import compose
from bench.silver import sha
from PIL import Image

import pylopdf


def raster(size: tuple[int, int] = (100, 100)) -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", size, "white").save(stream, format="PNG")
    return stream.getvalue()


class Detector:
    """Mock persistent CPU detector returning exact supplied-image mappings."""

    def __init__(self, fail_at: int | None = None, *, boxes: bool = True) -> None:
        """Configure only transport failure ordinal and source proposals."""
        self.fail_at, self.boxes, self.calls = fail_at, boxes, 0

    def detect(self, image: bytes, *, viewport: list[float]) -> dict[str, Any]:
        """Return deterministic proposals wholly within the submitted viewport."""
        self.calls += 1
        if self.calls == self.fail_at:
            raise RuntimeError("mock detector error")
        with Image.open(io.BytesIO(image)) as pixels:
            width, height = pixels.size
        normalized = [0.0, 0.0, 1.0, 1.0] if self.calls == 1 else [0.1, 0.1, 0.9, 0.9]
        pixel = [normalized[0] * width, normalized[1] * height, normalized[2] * width, normalized[3] * height]
        # Use the same inverse mapping arithmetic as the real persistent detector.
        normalized = [pixel[0] / width, pixel[1] / height, pixel[2] / width, pixel[3] / height]
        box = {
            "label": "Table",
            "confidence": 0.8,
            "pixel_bbox": pixel,
            "normalized_bbox": normalized,
            "bbox": [
                viewport[0] + normalized[0] * (viewport[2] - viewport[0]),
                viewport[1] + normalized[1] * (viewport[3] - viewport[1]),
                viewport[0] + normalized[2] * (viewport[2] - viewport[0]),
                viewport[1] + normalized[3] * (viewport[3] - viewport[1]),
            ],
        }
        return {
            "type": "result",
            "device": "cpu",
            "viewport": list(viewport),
            "image_size": [width, height],
            "boxes": [box] if self.boxes else [],
        }


def wrapper() -> multi.MultiscaleDetector:
    return multi.MultiscaleDetector(Detector(), raster(), [10, 20, 110, 120])


def test_five_raw_calls_replay_exactly_and_contained_members_are_retained() -> None:
    detector = wrapper()
    fused = detector.detect(raster(), viewport=[10, 20, 110, 120])
    original = deepcopy(detector.raw_calls)
    assert fused == multi.replay(detector.raw_calls, [10, 20, 110, 120], [100, 100])
    assert detector.raw_calls == original
    assert len(detector.raw_calls) == 5
    assert fused["raw_box_count"] == 5
    assert len(fused["boxes"]) == 1
    assert len(fused["boxes"][0]["members"]) == 5
    assert fused["fusion"]["arm"] == "larger_containment"
    assert detector.received_base_image is not None
    assert detector.received_base_image["used_for_inference"] is False
    assert multi.RULES["preliminary_nms"] is False


@pytest.mark.parametrize("tamper", ["mapping", "window", "order", "dimensions", "missing", "cpu"])
def test_replay_refuses_tampered_or_incomplete_detection(tamper: str) -> None:
    detector = wrapper()
    detector.detect(raster(), viewport=[10, 20, 110, 120])
    raw = deepcopy(detector.raw_calls)
    if tamper == "mapping":
        raw[1]["result"]["boxes"][0]["bbox"][0] += 1
    elif tamper == "window":
        raw[1]["tile_pixel_bbox"][0] += 1
    elif tamper == "order":
        raw[1]["call_id"] = "g2-t3"
    elif tamper == "dimensions":
        raw[1]["result"]["image_size"][0] += 1
    elif tamper == "cpu":
        raw[1]["result"]["device"] = "gpu"
    else:
        raw.pop()
    with pytest.raises(ValueError, match=r".+"):
        multi.replay(raw, [10, 20, 110, 120], [100, 100])


def test_partial_detector_failure_retains_previous_raw_results() -> None:
    detector = multi.MultiscaleDetector(Detector(fail_at=3), raster(), [0, 0, 100, 100])
    with pytest.raises(RuntimeError, match="mock"):
        detector.detect(raster(), viewport=[0, 0, 100, 100])
    assert [call["status"] for call in detector.raw_calls] == ["ok", "ok", "error"]
    assert detector.fused is None
    with pytest.raises(ValueError, match="one matching"):
        detector.detect(raster(), viewport=[0, 0, 100, 100])


def record(tmp_path: Path) -> dict:
    with pylopdf.Document() as document:
        document.new_page(width=100, height=100)
        data = document.tobytes()
    path = tmp_path / "source.pdf"
    path.write_bytes(data)
    return {"id": "test", "pdf_path": str(path), "pdf_sha256": sha(data), "page_number": 0}


def test_real_crop_processor_zero_proposals_stays_unverified_and_makes_no_calls(tmp_path: Path) -> None:
    config = {"campaign": "P002", "layout_detector": "yolo", "_layout_detector": Detector(boxes=False)}
    result = multi.process(record(tmp_path), config, tmp_path / "output", None)
    assert result["status"] == "ok", result
    assert result["processor"] == "vision_multiscale"
    assert result["coverage"] == "unverified"
    assert result["calls"] == []
    assert result["tables"] == []
    assert len(result["multiscale_raw_calls"]) == 5
    assert max(result["multiscale_image"]["image_size"]) <= 3072
    assert result["layout_detection"] == multi.replay(
        result["multiscale_raw_calls"], result["viewport"], result["multiscale_image"]["image_size"]
    )


def test_detector_failure_is_atomic_with_partial_raw_evidence(tmp_path: Path) -> None:
    config = {"campaign": "P002", "layout_detector": "yolo", "_layout_detector": Detector(fail_at=3)}
    result = multi.process(record(tmp_path), config, tmp_path / "output", None)
    assert result["status"] == "error"
    assert result["tables"] == []
    assert len(result["multiscale_raw_calls"]) == 3
    assert not (tmp_path / "output" / "test-structure.json").exists()
    assert not (tmp_path / "output" / "test.md").exists()


@pytest.mark.parametrize(
    ("key", "value"),
    [("detector_tiles", "3x3"), ("detector_fusion", "nms"), ("image_edge", 1200), ("jpeg_quality", 70)],
)
def test_only_predeclared_settings_are_admitted(tmp_path: Path, key: str, value: Any) -> None:
    config = {"campaign": "P002", "layout_detector": "yolo", "_layout_detector": Detector(), key: value}
    result = multi.process({"id": "test"}, config, tmp_path, None)
    assert result["status"] == "error"
    assert result["error_stage"] == "config"


def test_final_crop_composition_overlap_gate_is_unchanged() -> None:
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": '{"answers":{"q0":{"tables":[{"bbox":[0,0,1000,1000],'
                    '"matrix":[["A"]],"mergedspans":[]}]}}}'
                },
            }
        ]
    }
    raw = [
        {
            "index": index,
            "request_index": index,
            "status": "ok",
            "viewport": [0, 0, 100, 100],
            "transcription_response": response,
        }
        for index in range(2)
    ]
    with pytest.raises(ValueError, match="overlap"):
        compose(raw, [0, 0, 100, 100])


def test_tile_only_proposals_survive_whole_page_miss() -> None:
    detector = wrapper()
    detector.detect(raster(), viewport=[10, 20, 110, 120])
    raw = deepcopy(detector.raw_calls)
    raw[0]["result"]["boxes"] = []
    result = multi.replay(raw, [10, 20, 110, 120], [100, 100])
    assert result["raw_box_count"] == 4
    assert len(result["boxes"]) == 4
    assert all(box["detector_full_page_member"] is False for box in result["boxes"])
    assert all(box["detector_partial_context"] is True for box in result["boxes"])
