"""Independent gate encodings and source-image replay; in-process CPU only."""

# ruff: noqa: SLF001, PLC0415
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_report as report
from bench import generalization_run as run
from bench import p003_gate_image as gate
from bench.silver import sha
from PIL import Image
from test_generalization_vision_regions import _record

import pylopdf


def rgb(edge: int = 128) -> tuple[str, dict[str, Any]]:
    image = Image.new("RGB", (edge, max(1, edge // 4)))
    image.putdata([(i % 256, (i * 7) % 256, (i * 13) % 256) for i in range(image.width * image.height)])
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    data = stream.getvalue()
    return "data:image/png;base64," + base64.b64encode(data).decode(), {
        "image_edge": edge, "image_size": list(image.size), "image_viewport": [1, 2, 3, 4],
        "image_sha256": sha(data), "image_bytes": len(data),
    }


@pytest.mark.parametrize("edge", gate.EDGES)
@pytest.mark.parametrize("mode", gate.MODES)
def test_actual_png_encodings_dimensions_and_determinism(edge: int, mode: str) -> None:
    url, metadata = rgb(edge)
    transformed, actual = gate.transform(url, metadata, mode)
    assert transformed is not None
    assert gate.transform(url, metadata, mode) == (transformed, actual)
    assert actual["image_size"] == metadata["image_size"]
    assert actual["image_viewport"] == metadata["image_viewport"]
    data = base64.b64decode(transformed.split(",", 1)[1])
    assert actual["image_sha256"] == sha(data)
    assert actual["image_bytes"] == len(data)
    with Image.open(io.BytesIO(data)) as decoded:
        assert list(decoded.size) == metadata["image_size"]
        if mode == "rgb":
            assert transformed == url
            assert actual == metadata
            assert decoded.mode == "RGB"
        elif mode == "grayscale8":
            assert decoded.mode == "L"
            assert (data[24], data[25]) == (8, 0)
            assert actual["palette_entries"] == 0
        else:
            assert decoded.mode == "P"
            assert (data[24], data[25]) == (4, 3)
            assert len(set(decoded.tobytes())) <= 16
            assert actual["palette_entries"] <= 16
            assert actual["lossy_color_transform"] is True
    assert "source_rgb_sha256" not in metadata


def test_no_pixels_and_unknown_mode_refuse_explicitly() -> None:
    assert gate.transform(None, {"image": "none"}) == (None, {"image": "none"})
    with pytest.raises(ValueError, match="source PNG"):
        gate.transform(None, {}, "grayscale8")
    with pytest.raises(ValueError, match="Unknown"):
        gate.transform(None, {}, "rgb565")


def test_source_metadata_tampering_refused() -> None:
    url, metadata = rgb()
    metadata["image_sha256"] = "incorrect"
    with pytest.raises(ValueError, match="retained RGB metadata"):
        gate.transform(url, metadata, "rgb_palette16")


@pytest.mark.parametrize("mode", ["grayscale8", "rgb_palette16"])
def test_frozen_source_replay_checks_actual_body_and_payload_metadata(tmp_path: Path, mode: str) -> None:
    record = _record(tmp_path)
    config = {"gate_image_mode": mode, "gate_image_edge": 128, "image_edge": 512, "rotation_mode": "preserve"}
    bbox: list[float] = [10, 20, 100, 150]
    with pylopdf.open(record["pdf_path"]) as document:
        source_url, source_metadata = run.region_image(document[0], bbox, 128)
    url, metadata = gate.transform(source_url, source_metadata, mode)
    prediction = {
        "id": "fixture", "calls": [{}], "region_plan": {"regions": [{"id": "r0", "bbox": bbox}]},
        "gate_image_evidence": [{"region_id": "r0", "request_index": 0, "image": metadata}],
    }
    (tmp_path / "frozen.json").write_text(json.dumps({"records": [record]}))
    body: dict[str, Any] = {"state": [{"type": "image_url", "image_url": {"url": url}}]}
    path = tmp_path / "fixture-request-0.json"
    path.write_text(json.dumps(body))
    report._verify_gate_images(tmp_path, prediction, config)
    body["state"][0]["image_url"]["url"] = source_url
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError, match="Actual gate pixels"):
        report._verify_gate_images(tmp_path, prediction, config)
    path.write_text(json.dumps({"state": [{"type": "image_url", "image_url": {"url": url}}]}))
    metadata["png_bit_depth"] = 99
    with pytest.raises(ValueError, match="metadata differs"):
        report._verify_gate_images(tmp_path, prediction, config)


@pytest.mark.parametrize("model", ["perplexity/pplx-decider-v1.1-27b", "openai/gpt-6-luna"])
@pytest.mark.parametrize("mode", ["grayscale8", "rgb_palette16"])
@pytest.mark.parametrize("style", ["visual_schema", "recall_first", "skeptical", "local_relations"])
def test_actual_request_transforms_only_gate_pixels_and_uses_frozen_rubric(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, style: str, model: str,
) -> None:
    from bench import pipeline_run as baseline
    from bench.p003_prompt_variants import instructions
    from bench.pipeline_assembly import native_state
    from test_pipeline_run import config

    source = {"page_size": [100, 100], "words": [{"id": "w0", "text": "literal", "bbox": [1, 1, 10, 10]}]}
    region = {"id": "r0", "boundary": "unsplit", "bbox": [0, 0, 100, 100], "source": source}
    generation_url, generation_meta = rgb(512)
    gate_url, gate_meta = rgb(128)
    expected_url, expected_meta = gate.transform(gate_url, gate_meta, mode)
    requests = []
    generated = []

    def image(_page: object, _bbox: object, edge: int) -> tuple[str, dict[str, Any]]:
        return (generation_url, generation_meta) if edge == 512 else (gate_url, gate_meta)

    def call(_client: object, request: dict[str, Any], _tag: str) -> dict[str, Any]:
        requests.append(request)
        return {"answer": {"choice": "table", "probabilities": {"table": 1}}}

    def generate(*args: object, **_kwargs: object) -> dict[str, Any]:
        generated.append(args)
        return native_state(source)

    monkeypatch.setattr(run, "region_image", image)
    monkeypatch.setattr(baseline, "call", call)
    monkeypatch.setattr(run, "generate_region", generate)
    settings = {
        **config("gated"), "model": model, "campaign": "P003",
        "assembly_method": "gated_generate", "image_edge": 512, "gate_image_edge": 128,
        "gate_packet": "compact", "gate_instructions": style, "gate_image_mode": mode, "answer_tokens": 2048,
    }
    prediction: dict[str, Any] = {"id": "opaque", "calls": [], "region_plan": {"regions": [region]}}
    _, info = run.select_region(region, None, settings, tmp_path, prediction, object())  # type: ignore[arg-type]
    if "questions" in requests[0]:
        assert requests[0]["state"][1]["image_url"]["url"] == expected_url
        assert requests[0]["questions"]["q0"]["instructions"] == instructions(style)
    else:
        assert requests[0]["messages"][2]["content"][1]["image_url"]["url"] == expected_url
        rubric = json.loads(requests[0]["messages"][1]["content"])["questions"]["q0"]["instructions"]
        assert rubric == instructions(style)
        assert requests[0]["max_tokens"] == settings["answer_tokens"]
    assert generated[0][2] == generation_url
    assert info["gate_image_metadata"] == expected_meta
    assert prediction["gate_image_evidence"][0]["image"] == expected_meta
    report._verify_gate_instructions(tmp_path, prediction, settings)
    archived = tmp_path / "opaque-request-0.json"
    body = json.loads(archived.read_text())
    if "questions" in body:
        body["questions"]["q0"]["instructions"] = "A different rubric"
    else:
        body["messages"][1]["content"] = "A different rubric"
    archived.write_text(json.dumps(body))
    with pytest.raises(ValueError, match="frozen semantic"):
        report._verify_gate_instructions(tmp_path, prediction, settings)
