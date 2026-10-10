"""Crop coordinate provenance, atomic composition and fake metered transport."""

# ruff: noqa: ANN401, SLF001
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_vision_regions as regions
from bench import generalization_vision_run as vision
from bench.silver import sha
from PIL import Image

import pylopdf


def raw(matrix: list | None = None, bbox: list | None = None) -> dict[str, Any]:
    tables = (
        []
        if matrix is None
        else [{"bbox": [0, 0, 1000, 1000] if bbox is None else bbox, "matrix": matrix, "mergedspans": []}]
    )
    return {
        "choices": [
            {"finish_reason": "stop", "message": {"content": json.dumps({"answers": {"q0": {"tables": tables}}})}}
        ]
    }


def region(index: int, viewport: list, response: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": index,
        "request_index": index,
        "viewport": viewport,
        "status": "ok",
        "transcription_response": response,
    }


def test_compose_maps_literal_tables_into_global_viewport_in_declared_order() -> None:
    values = [region(0, [10, 20, 100, 150], raw([["First"]])), region(1, [200, 20, 400, 150], raw([["Second"]]))]
    parsed = regions.compose(values, [0, 0, 600, 800])
    assert [table["values"] for table in parsed["tables"]] == [[["First"]], [["Second"]]]
    assert [table["bbox"] for table in parsed["tables"]] == [[10, 20, 100, 150], [200, 20, 400, 150]]
    assert parsed["source_conserved"] is False


@pytest.mark.parametrize("problem", ["overlap", "outside", "index", "request", "error", "truncated"])
def test_compose_refuses_invalid_or_partial_region_state(problem: str) -> None:
    values = [region(0, [10, 20, 100, 150], raw([["A"]])), region(1, [200, 20, 400, 150], raw([["B"]]))]
    if problem == "overlap":
        values[1]["viewport"] = [50, 20, 200, 150]
    elif problem == "outside":
        values[1]["viewport"] = [200, 20, 700, 150]
    elif problem == "index":
        values[1]["index"] = 0
    elif problem == "request":
        values[1]["request_index"] = 0
    elif problem == "error":
        values[1]["status"] = "error"
    else:
        values[1]["transcription_response"]["choices"][0]["finish_reason"] = "length"
    with pytest.raises(ValueError, match=r"."):
        regions.compose(values, [0, 0, 600, 800])


def test_aggregate_slot_limit_is_independent_of_individual_region_admission() -> None:
    matrix = [[""] * 64 for _ in range(33)]
    values = [region(0, [0, 0, 100, 100], raw(matrix)), region(1, [200, 0, 300, 100], raw(matrix))]
    with pytest.raises(ValueError, match="4096 slots"):
        regions.compose(values, [0, 0, 600, 800])


@pytest.mark.parametrize("edge", [400, 512, 768, 1024])
def test_crop_preserves_exact_fractional_viewport_and_fixed_jpeg_edge(edge: int) -> None:
    image = Image.new("RGB", (4096, 2048), "white")
    url, metadata = regions._crop(image, [0, 0, 600, 300], [10.25, 20.75, 110.5, 70.125], edge)
    assert metadata["image_viewport"] == [10.25, 20.75, 110.5, 70.125]
    assert metadata["image_size"][0] == edge
    assert metadata["image_edge"] == edge
    assert metadata["image_quality"] == 90
    assert metadata["body_limit_adaptation"] is False
    with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as decoded:
        assert max(decoded.size) == edge
        assert decoded.mode == "RGB"


@pytest.mark.parametrize("edge", [True, 512.0, 0, 401, 2048])
def test_invalid_crop_edge_refuses_before_pixels(edge: Any) -> None:
    with pytest.raises(ValueError, match="fixed comparison"):
        regions._crop(None, [0, 0, 600, 300], [10, 20, 100, 70], edge)


class Detector:
    """Fixed local proposals with no model or network access."""

    def __init__(self, boxes: list[dict[str, Any]]) -> None:
        """Retain explicit source proposals."""
        self.boxes = boxes

    def detect(self, _pixels: bytes, *, viewport: list) -> dict[str, Any]:
        """Return proposals in the supplied global viewport."""
        return {"type": "result", "device": "cpu", "viewport": viewport, "boxes": self.boxes}


def _record(tmp_path: Path) -> dict[str, Any]:
    with pylopdf.Document() as document:
        document.new_page(width=600, height=800)
        data = document.tobytes()
    path = tmp_path / "source.pdf"
    path.write_bytes(data)
    return {"id": "fixture", "pdf_path": str(path), "pdf_sha256": sha(data), "page_number": 0}


def test_empty_proposals_emit_empty_tables_with_unverified_coverage_and_no_requests(tmp_path: Path) -> None:
    result = regions.process(_record(tmp_path), {"_layout_detector": Detector([])}, tmp_path, None)
    assert result["status"] == "ok"
    assert result["coverage"] == "unverified"
    assert result["tables"] == []
    assert result["calls"] == []
    assert result["proposal_count"] == 0


def test_table_class_and_fixed_confidence_only_proposals() -> None:
    detection: dict[str, Any] = {
        "type": "result",
        "device": "cpu",
        "viewport": [0, 0, 600, 800],
        "boxes": [
            {"label": "Text", "confidence": 0.99, "bbox": [10, 10, 50, 50]},
            {"label": "Table", "confidence": 0.24, "bbox": [60, 10, 100, 50]},
            {"label": "Table", "confidence": 0.25, "bbox": [110, 10, 150, 50]},
        ],
    }
    assert [proposal["viewport"] for proposal in regions.proposals(detection, detection["viewport"])] == [
        [110, 10, 150, 50]
    ]


def test_parse_error_keeps_raw_responses_costs_and_fails_complete_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    boxes = [{"label": "Table", "confidence": 0.9, "bbox": box} for box in ([10, 20, 100, 150], [200, 20, 400, 150])]
    calls = []

    def fake(_client: Any, _body: dict, _config: dict, result: dict, output: Path, *, request_index: int) -> dict:
        calls.append(request_index)
        response = raw([["A"]]) if request_index == 0 else raw([["B"], ["C", "D"]])
        result["calls"].append({"retained_cost": 0.01, "request_index": request_index})
        result["request"] = {"request_index": request_index}
        result["transcription_response"] = response
        (output / f"fixture-response-{request_index}.json").write_text(json.dumps(response))
        return response

    monkeypatch.setattr(vision, "_transcribe", fake)
    result = regions.process(_record(tmp_path), {"_layout_detector": Detector(boxes)}, tmp_path, None)
    assert calls == [0, 1]
    assert len(result["calls"]) == 2
    assert result["status"] == "error"
    assert result["tables"] == []
    assert result["transcription_regions"][0]["status"] == "ok"
    assert result["transcription_regions"][1]["status"] == "error"
    assert "transcription_response" in result["transcription_regions"][1]
    assert not (tmp_path / "fixture-structure.json").exists()
    assert not (tmp_path / "fixture.md").exists()


def test_indexed_transport_retains_unique_files_tags_and_default_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Client:
        """Record a local transport stub without inference or credentials."""

        ledger = tmp_path / "absent-ledger.json"

        def __init__(self) -> None:
            self.tags: list[str] = []

        def request(self, _body: dict, **kwargs: Any) -> dict:
            self.tags.append(kwargs["tag"])
            return {"entry": {"index": len(self.tags) - 1}, "result": raw([[str(len(self.tags))]]), "replayed": False}

    monkeypatch.setattr(vision, "_ledger", lambda _client: [])
    client: Any = Client()
    body = {"model": "anthropic/claude-sonnet-5.5", "max_tokens": 100, "messages": []}
    result: dict[str, Any] = {"id": "fixture", "calls": []}
    config = {"run_id": "test"}
    vision._transcribe(client, body, config, result, tmp_path)
    before = (tmp_path / "fixture-response-0.json").read_bytes()
    vision._transcribe(client, body, config, result, tmp_path, request_index=1)
    assert (tmp_path / "fixture-response-0.json").read_bytes() == before
    assert (tmp_path / "fixture-response-1.json").exists()
    assert (tmp_path / "fixture-request-0.json").read_bytes() == (tmp_path / "fixture-request-1.json").read_bytes()
    assert client.tags == ["P002/test/fixture/vision/0", "P002/test/fixture/vision/1"]
    assert len(result["calls"]) == 2
    assert "request_index" not in result["request"]


def test_complete_proposals_over32_refuse_before_any_request() -> None:
    detection: dict[str, Any] = {
        "type": "result",
        "device": "cpu",
        "viewport": [0, 0, 600, 800],
        "boxes": [{"label": "Table", "confidence": 0.8, "bbox": [10, 10, 50, 50]} for _ in range(33)],
    }
    with pytest.raises(ValueError, match="32 regions"):
        regions.proposals(detection, detection["viewport"])
