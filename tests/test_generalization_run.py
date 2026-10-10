"""End-to-end CPU seams for source-only regional extraction and metering."""

from __future__ import annotations

import base64
import io
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import generalization_run as runner
from bench import pipeline_run as baseline
from bench.pipeline_regions import split
from PIL import Image
from test_pipeline_run import config, pdf_bytes, record

import pylopdf


@pytest.mark.parametrize("factor", [0.5, 1, 2, 4])
def test_fixed_ocr_edge_preserves_raster_size_under_physical_scaling(factor: float) -> None:
    viewport = [10 * factor, 20 * factor, 410 * factor, 620 * factor]
    dpi, metadata = runner.ocr_resolution(viewport, {"ocr_edge": 2048, "ocr_dpi": 150})
    assert (viewport[3] - viewport[1]) * dpi / 72 == pytest.approx(2048)
    assert (viewport[2] - viewport[0]) * dpi / 72 == pytest.approx(2048 * 2 / 3)
    assert metadata["resolution_mode"] == "fixed_edge"
    assert metadata["display_viewport"] == viewport


def test_fixed_dpi_is_unchanged_without_explicit_ocr_edge() -> None:
    assert runner.ocr_resolution([0, 0, 400, 600], {"ocr_dpi": 300})[0] == 300


@pytest.mark.parametrize(
    ("viewport", "edge"), [([0, 0, 0, 600], 2048), ([0, 0, 400, float("inf")], 2048), ([0, 0, 400, 600], True)]
)
def test_ocr_resolution_rejects_invalid_geometry_or_choice(viewport: list[float], edge: object) -> None:
    with pytest.raises(ValueError, match="OCR"):
        runner.ocr_resolution(viewport, {"ocr_edge": edge})


def test_region_native_output_is_complete_and_has_no_api_calls(tmp_path: Path) -> None:
    settings = {**config("native"), "ocr_empty": False}
    result = runner.process(record(tmp_path), settings, tmp_path, None)
    assert result["status"] == "ok"
    assert len(result["tables"]) == 1
    assert result["calls"] == []
    assert result["source_conserved"]
    assert all("state" in region for region in result["regions"])
    assert (tmp_path / "opaque-page.md").read_text().count("<table>") == 1


def test_invalid_native_topology_retains_all_words_for_rediscovery() -> None:
    with pylopdf.open(stream=pdf_bytes()) as doc:
        source = baseline.source(doc[0])
    source["vector_candidates"][0]["spans"].pop()
    clean, warnings = runner.sanitize_vectors(source)
    assert clean["words"] == source["words"]
    assert clean["vector_candidates"] == []
    assert len(warnings) == 1
    plan = split(clean)
    assert Counter(i for r in plan["regions"] for i in r["source_ids"]) == Counter(w["id"] for w in source["words"])


@pytest.mark.parametrize("edge", [256, 512, 1024])
def test_crop_raster_records_global_viewport(edge: int) -> None:
    box: list[float] = [40, 40, 300, 120]
    with pylopdf.open(stream=pdf_bytes()) as doc:
        url, metadata = runner.region_image(doc[0], box, edge)
    assert url is not None
    assert metadata["image_viewport"] == box
    with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as raster:
        assert max(raster.size) <= edge
        assert raster.width > raster.height
        assert list(raster.size) == metadata["image_size"]


def test_p002_budget_uses_its_own_wave_and_stops_before_request(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            {"requests": [{"tag": "P001/old", "accounted_usd": 49.9}, {"tag": "P002/new", "accounted_usd": 49.8}]}
        )
    )
    client: Any = SimpleNamespace(
        ledger=ledger, request=lambda *_a, **_kw: pytest.fail("Request passed exhausted wave")
    )
    with pytest.raises(RuntimeError, match="P002 reservation"):
        baseline.call(client, {"model": "stub"}, "P002/run/page")


def test_p001_spend_does_not_consume_p002_wave_allowance(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"requests": [{"tag": "P001/old", "accounted_usd": 50}]}))

    def request(*_args: object, **kwargs: object) -> dict[str, Any]:
        assert kwargs["replay"] is False
        return {
            "result": {"answers": {"q0": {"type": "choice", "choice": "x", "probabilities": {"x": 1}}}},
            "entry": {},
            "replayed": False,
        }

    client: Any = SimpleNamespace(ledger=ledger, request=request)
    result = baseline.call(
        client, {"model": "stub", "questions": {"q0": {"criteria": {"x": "choose"}}}}, "P002/run/page"
    )
    assert result["answer"]["choice"] == "x"


def test_unknown_campaign_rejected_before_metering(tmp_path: Path) -> None:
    client: Any = SimpleNamespace(ledger=tmp_path / "absent")
    with pytest.raises(ValueError, match="Unknown"):
        baseline.call(client, {}, "unregistered/run")


@pytest.mark.parametrize("method", ["generate", "gated_generate"])
def test_generation_can_construct_without_a_geometry_alternative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    source = {"page_size": [100, 100], "words": [{"id": "w0", "text": "literal", "bbox": [1, 1, 10, 10]}]}
    region = {"id": "r0", "boundary": "unsplit", "bbox": [0, 0, 100, 100], "source": source}
    calls = []

    def generate(*args: object, **_kwargs: object) -> dict[str, Any]:
        calls.append(args)
        return baseline.native_state(source)

    monkeypatch.setattr(runner, "generate_region", generate)
    monkeypatch.setattr(
        runner, "_request", lambda *_args, **_kwargs: {"choice": "table", "probabilities": {"table": 1}}
    )
    settings = {**config("gated"), "assembly_method": method, "image_edge": 0}
    state, info = runner.select_region(region, None, settings, tmp_path, {"id": "opaque", "calls": []}, None)
    assert len(calls) == 1
    assert state["unresolved_ids"] == ["w0"]
    assert "generated" in info["route"]


def test_raster_grid_requires_semantic_admission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pylopdf.open(stream=pdf_bytes()) as doc:
        source = baseline.source(doc[0])
    region = split(source)["regions"][0]
    region["kind"] = "raster"
    calls = []

    def reject(*args: object, **_kwargs: object) -> dict[str, Any]:
        calls.append(args)
        return {"choice": "prose", "probabilities": {"prose": 1}}

    monkeypatch.setattr(runner, "_request", reject)
    state, info = runner.select_region(
        region, None, {**config("gated"), "image_edge": 0}, tmp_path, {"id": "opaque", "calls": []}, None
    )
    assert len(calls) == 1
    assert state["tables"] == []
    assert len(state["unresolved_ids"]) == len(source["words"])
    assert info["route"] == "gated_out"
    assert any(c["mechanism"] == "raster_rules" for c in info["candidates"])


def test_detector_residual_retains_all_source_without_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {"page_size": [100, 100], "words": [{"id": "w0", "text": "prose", "bbox": [1, 1, 10, 10]}]}
    region = {"id": "r0", "kind": "residual", "boundary": "unsplit", "bbox": [0, 0, 100, 100], "source": source}
    monkeypatch.setattr(runner, "generate_region", lambda *_a, **_k: pytest.fail("Residual triggered inference"))
    settings = {
        **config("gated"),
        "assembly_method": "generate",
        "layout_detector": "yolo",
        "detector_residual": "retain",
    }
    state, info = runner.select_region(region, None, settings, tmp_path, {"id": "opaque", "calls": []}, None)
    assert state["unresolved_ids"] == ["w0"]
    assert state["tables"] == []
    assert info["route"] == "detector_residual_retained"


@pytest.mark.parametrize("response_format", ["anchors", "matrix", "indices"])
@pytest.mark.parametrize("url", [None, "data:image/png;base64,YQ=="])
def test_row_observations_reach_generation_without_changing_literal_inventory(
    tmp_path: Path, response_format: str, url: str | None
) -> None:
    source = {"page_size": [100, 100], "words": [{"id": "w7", "text": "literal", "bbox": [1, 1, 10, 10]}]}
    ledger = tmp_path / "ledger.json"
    ledger.write_text('{"requests":[]}')
    captured = []

    def request(body: dict[str, Any], **_kwargs: object) -> dict[str, Any]:
        captured.append(body)
        return {
            "entry": {},
            "replayed": False,
            "result": {
                "choices": [{"finish_reason": "stop", "message": {"content": '{"answers":{"q0":{"tables":[]}}}'}}]
            },
        }

    client: Any = SimpleNamespace(ledger=ledger, request=request)
    state = runner.generate_region(
        source,
        [0, 0, 100, 100],
        url,
        {"run_id": "fixture", "generation_format": response_format, "generation_row_evidence": True},
        tmp_path,
        {"id": "opaque", "calls": []},
        "r0",
        client,
    )
    content = captured[0]["messages"][1]["content"]
    text = content if isinstance(content, str) else content[-1]["text"]
    assert "Additional source-derived observations" in text
    assert ('"word_indexes":[0]' if response_format == "indices" else '"source_ids":["w7"]') in text
    assert state["unresolved_ids"] == ["w7"]
    assert state["tables"] == []


def test_gate_receives_complete_row_context_only_when_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = {"page_size": [100, 100], "words": [{"id": "w0", "text": "literal", "bbox": [1, 1, 10, 10]}]}
    region = {"id": "r0", "boundary": "unsplit", "bbox": [0, 0, 100, 100], "source": source}
    prompts = []

    def reject(*args: object, **_kwargs: object) -> dict[str, Any]:
        assert isinstance(args[5], str)
        prompts.append(args[5])
        return {"choice": "prose", "probabilities": {"prose": 1}}

    monkeypatch.setattr(runner, "_request", reject)
    for enabled in (False, True):
        settings = {
            **config("gated"),
            "assembly_method": "gated_generate",
            "image_edge": 0,
            "gate_row_evidence": enabled,
        }
        state, _ = runner.select_region(region, None, settings, tmp_path, {"id": "opaque", "calls": []}, None)
        assert state["unresolved_ids"] == ["w0"]
    assert "Additional source-derived observations" not in prompts[0]
    assert "Additional source-derived observations" in prompts[1]
