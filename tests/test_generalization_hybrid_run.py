"""Offline hybrid orchestration preserves evidence and refuses partial output."""

# The stub models heterogeneous transport and explicit unused detector inputs.
# ruff: noqa: ANN401, ARG005
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import bench
import pytest
from bench import generalization_hybrid_run as hybrid
from bench.silver import sha, write_json

import pylopdf


@pytest.fixture
def setup(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    data: dict[str, Any] = {
        "native_status": "ok",
        "vision_status": "ok",
        "composition_status": "ok",
        "native_calls": [],
    }
    source = {"page_size": [0, 0, 100, 100], "words": [], "vector_candidates": []}
    native_state: dict = {"tables": [], "unresolved_ids": []}
    vision_state = {"tables": [{"values": [["model literal"]]}]}
    raw = {"boxes": [{"label": "Table", "bbox": [0, 0, 40, 40]}, {"label": "Table", "bbox": [60, 60, 90, 90]}]}

    def exclude(response: dict, boxes: list) -> tuple[dict, list]:
        assert boxes == [[0, 0, 50, 50]]
        filtered = deepcopy(response)
        filtered["boxes"] = filtered["boxes"][1:]
        return filtered, [{"excluded": response["boxes"][0]}]

    def compose(actual_source: dict, actual_native: dict, actual_vision: dict) -> dict:
        assert actual_source == source
        assert actual_native == native_state
        assert actual_vision == vision_state
        return {
            "status": data["composition_status"],
            "tables": actual_vision["tables"],
            "markdown": "hybrid markup",
            "source_conserved": False,
            "source_inventory_complete": True,
            "accounting_complete": True,
            "unresolved_ids": [],
            "superseded_ids": [],
            "ledger": [],
        }

    helper = SimpleNamespace(
        sanitize_vectors=deepcopy,
        native_boxes=lambda *_: [[0, 0, 50, 50]],
        exclude_native_proposals=exclude,
        compose=compose,
        markdown=lambda actual: actual["markdown"],
    )
    monkeypatch.setitem(sys.modules, "bench.pipeline_hybrid_composition", helper)
    monkeypatch.setattr(bench, "pipeline_hybrid_composition", helper, raising=False)
    data["detector"] = SimpleNamespace(detect=lambda image, *, viewport: deepcopy(raw))

    def native_process(record: dict, config: dict, output: Path, client: Any) -> dict:
        data["native_config"] = config
        assert client is None
        assert output.name == "native"
        write_json(output / f"{record['id']}-structure.json", native_state)
        return {
            "id": record["id"],
            "status": data["native_status"],
            "source": source,
            "calls": data["native_calls"],
            "tables": [],
        }

    def vision_process(record: dict, config: dict, output: Path, client: Any) -> dict:
        data["vision_config"] = config
        assert output.name == "vision"
        assert client == "fake-client"
        response = config["_layout_detector"].detect(b"unchanged raster", viewport=[0, 0, 100, 100])
        assert len(response["boxes"]) == 1
        write_json(output / f"{record['id']}-structure.json", vision_state)
        return {
            "id": record["id"],
            "status": data["vision_status"],
            "calls": [{"entry": {"tag": "P002/test/page/vision/0"}}],
            "viewport": [0, 0, 100, 100],
            "original_rotation": 90,
        }

    monkeypatch.setattr(hybrid.native, "process", native_process)
    monkeypatch.setattr(hybrid.regions, "process", vision_process)
    data["config"] = {
        "campaign": "P002",
        "policy": "gated",
        "layout_detector": "yolo",
        "_layout_detector": data["detector"],
        "image_edge": 1024,
        "jpeg_quality": 90,
        "ocr_edge": 2048,
        "ocr_mode": "uncovered_images",
    }
    return data


def run(setup: dict[str, Any], output: Path) -> dict:
    return hybrid.process({"id": "page"}, setup["config"], output, "fake-client")


def test_success_retains_children_composition_detector_and_config(setup: dict[str, Any], tmp_path: Path) -> None:
    result = run(setup, tmp_path)
    assert result["status"] == "ok"
    assert result["tables"] == result["composition"]["tables"]
    assert result["calls"] == result["native_result"]["calls"] + result["vision_result"]["calls"]
    assert result["filtered_layout_detection"] == setup["vision_config"]["_layout_detector"].filtered
    assert len(result["raw_layout_detection"]["boxes"]) == 2
    assert result["excluded_native_proposals"]
    assert json.loads((tmp_path / "page-structure.json").read_text()) == result["composition"]
    assert (tmp_path / "page.md").read_text() == "hybrid markup"
    config = setup["native_config"]
    assert config["policy"] == "native"
    assert config["layout_detector"] == "none"
    assert config["normalize_rotation"] is False
    assert config["rotation_mode"] == "preserve"
    assert config["ocr_source"] == "whitespace"
    assert config["ocr_dpi"] == 150
    assert config["ocr_edge"] == 2048
    assert config["ocr_mode"] == "uncovered_images"
    assert "_layout_detector" not in config


@pytest.mark.parametrize(
    ("key", "status", "stage"),
    [
        ("native_status", "unsupported_no_text", "native"),
        ("native_status", "error", "native"),
        ("vision_status", "error", "vision"),
        ("composition_status", "abstained", "compose"),
    ],
)
def test_child_or_composition_failure_is_atomic(
    setup: dict[str, Any], tmp_path: Path, key: str, status: str, stage: str
) -> None:
    setup[key] = status
    (tmp_path / "page.md").write_text("stale")
    write_json(tmp_path / "page-structure.json", {"tables": ["stale"]})
    result = run(setup, tmp_path)
    assert result["status"] != "ok"
    assert result["tables"] == []
    assert result["error_stage"] == stage
    assert not (tmp_path / "page.md").exists()
    assert not (tmp_path / "page-structure.json").exists()
    if stage != "native":
        assert len(result["calls"]) == 1
        assert result["native_result"]["status"] == "ok"
        assert result["raw_layout_detection"] is not None
    if status == "unsupported_no_text":
        assert result["status"] == "unsupported_no_text"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("campaign", "P001"),
        ("policy", "native"),
        ("image_edge", 1200),
        ("jpeg_quality", 70),
        ("normalize_rotation", True),
        ("rotation_mode", "always"),
        ("_layout_detector", None),
    ],
)
def test_fixed_hybrid_config_is_required(setup: dict[str, Any], tmp_path: Path, key: str, value: Any) -> None:
    setup["config"][key] = value
    result = run(setup, tmp_path)
    assert result["status"] == "error"
    assert result["error_stage"] == "config"
    assert "native_result" not in result
    assert result["calls"] == []


def test_native_model_calls_are_retained_but_refused(setup: dict[str, Any], tmp_path: Path) -> None:
    setup["native_calls"] = [{"entry": {"tag": "unexpected"}}]
    result = run(setup, tmp_path)
    assert result["status"] == "error"
    assert result["calls"] == setup["native_calls"]
    assert "vision_result" not in result


def test_detector_wrapper_refuses_repeated_calls(setup: dict[str, Any], tmp_path: Path) -> None:
    run(setup, tmp_path)
    wrapper = setup["vision_config"]["_layout_detector"]
    with pytest.raises(ValueError, match="only once"):
        wrapper.detect(b"unchanged raster", viewport=[0, 0, 100, 100])


def test_actual_native_and_empty_crop_children_compose_without_inference(tmp_path: Path) -> None:
    with pylopdf.Document() as document:
        page = document.new_page(width=600, height=800)
        page.insert_text((20, 40), "Literal native prose")
        content = document.tobytes()
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(content)
    detector = SimpleNamespace(
        detect=lambda image, *, viewport: {"type": "result", "device": "cpu", "viewport": viewport, "boxes": []}
    )
    config = {"campaign": "P002", "policy": "gated", "layout_detector": "yolo", "_layout_detector": detector}
    result = hybrid.process(
        {"id": "real", "pdf_path": str(pdf), "pdf_sha256": sha(content), "page_number": 0},
        config,
        tmp_path / "output",
        None,
    )
    assert result["status"] == "ok", result
    assert result["source_conserved"] is True
    assert result["accounting_complete"] is True
    assert result["calls"] == []
    assert result["tables"] == []
    assert result["vision_result"]["coverage"] == "unverified"
    assert "Literal native prose" in (tmp_path / "output" / "real.md").read_text()
    assert result["route"] == "hybrid"


def test_invalid_native_vector_is_quarantined_without_losing_words(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [{"id": "r:w0", "text": "Retained literal", "bbox": [10, 10, 30, 20]}],
        "vector_candidates": [{"row_count": 2, "col_count": 2, "cells": [[0, 0, 50, 50]], "spans": []}],
    }
    state = {"tables": [], "unresolved_ids": ["r:w0"]}
    original = deepcopy(source)

    def native_process(record: dict, _config: dict, output: Path, _client: Any) -> dict:
        write_json(output / f"{record['id']}-structure.json", state)
        return {"id": record["id"], "status": "ok", "source": source, "calls": [], "tables": []}

    def vision_process(record: dict, config: dict, output: Path, _client: Any) -> dict:
        detection = config["_layout_detector"].detect(b"pixels", viewport=[0, 0, 100, 100])
        write_json(
            output / f"{record['id']}-structure.json",
            {"tables": [], "text_provenance": "model-transcribed", "source_conserved": False},
        )
        return {
            "id": record["id"],
            "status": "ok",
            "calls": [],
            "tables": [],
            "viewport": [0, 0, 100, 100],
            "layout_detection": detection,
        }

    monkeypatch.setattr(hybrid.native, "process", native_process)
    monkeypatch.setattr(hybrid.regions, "process", vision_process)
    detector = SimpleNamespace(detect=lambda image, *, viewport: {"boxes": []})
    config = {"campaign": "P002", "policy": "gated", "layout_detector": "yolo", "_layout_detector": detector}
    result = hybrid.process({"id": "quarantine"}, config, tmp_path, None)
    assert result["status"] == "ok", result
    assert result["source"]["words"] == source["words"]
    assert result["source"]["vector_candidates"] == []
    assert result["native_warnings"] == [{"native_index": 0, "reason": "Invalid or over-limit native table slots"}]
    assert result["unresolved_ids"] == ["r:w0"]
    assert result["source_conserved"] is True
    assert source == original
    assert result["native_result"]["source"] == original
    assert "Retained literal" in (tmp_path / "quarantine.md").read_text()
