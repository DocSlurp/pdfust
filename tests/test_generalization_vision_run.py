"""CPU-only image comparator metering, provenance, and atomic response admission."""

# Mock transport dictionaries deliberately match heterogeneous provider envelopes.
# ruff: noqa: ANN401
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from bench import generalization_vision_run as runner
from bench import pipeline_vision_transcription as adapter
from PIL import Image
from test_pipeline_run import pdf_bytes, record

import pdfust

if TYPE_CHECKING:
    import pytest


def settings(**extra: Any) -> dict[str, Any]:
    return {"campaign": "P002", "run_id": "mock-vision", "generation_model": "anthropic/claude-sonnet-5.5", **extra}


def test_explicit_jpeg_quality_preserves_requested_pixel_dimensions() -> None:
    with pdfust.open(stream=pdf_bytes()) as document:
        default_url, default = runner.image(document[0], 2048)
        compressed_url, compressed = runner.image(document[0], 2048, 70)
    assert default["image_size"] == compressed["image_size"]
    assert default["image_viewport"] == compressed["image_viewport"]
    assert compressed["image_quality"] == 70
    assert compressed["image_bytes"] < default["image_bytes"]
    assert compressed_url != default_url
    assert compressed["body_limit_adaptation"] is False


def response(*, finish: str = "stop", tables: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if tables is None:
        tables = [{"bbox": [100, 200, 900, 800], "matrix": [["Name", "Value"], ["Alpha", "42"]], "mergedspans": []}]
    return {
        "choices": [
            {"finish_reason": finish, "message": {"content": json.dumps({"answers": {"q0": {"tables": tables}}})}}
        ],
        "usage": {"prompt_tokens": 123, "completion_tokens": 456, "cost": 0.015},
    }


def client(tmp_path: Path, answer: dict[str, Any]) -> Any:
    ledger = tmp_path / "mock-ledger.json"
    ledger.write_text(json.dumps({"requests": []}))
    requests: list[dict[str, Any]] = []

    def request(body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        requests.append({"body": body, **kwargs})
        entry = {
            "index": 0,
            "tag": kwargs["tag"],
            "accounted_usd": 0.015,
            "provider_reported_usd": 0.015,
            "cost_status": "provider-reported USD",
        }
        ledger.write_text(json.dumps({"requests": [entry]}))
        return {"result": answer, "entry": entry, "replayed": False}

    return SimpleNamespace(ledger=ledger, request=request, requests=requests)


def test_image_only_payload_and_complete_transcribed_table_provenance(tmp_path: Path) -> None:
    source = {
        **record(tmp_path),
        "reference_path": "DO_NOT_FORWARD",
        "gold": "DO_NOT_FORWARD",
        "family": "DO_NOT_FORWARD",
    }
    metered = client(tmp_path, response())
    result = runner.process(source, settings(), tmp_path, metered)
    assert result["status"] == "ok"
    assert result["route"] == "vision_transcription"
    assert result["output_scope"] == "table_only"
    assert not result["source_conserved"]
    assert "source" not in result
    assert result["unresolved_ids"] == []
    body = metered.requests[0]["body"]
    assert "DO_NOT_FORWARD" not in json.dumps(body)
    assert "opaque-page" not in json.dumps(body)
    assert list(body["messages"][1]["content"][0]) == ["type", "image_url"]
    assert len(body["messages"][1]["content"]) == 1
    assert body["max_tokens"] == 16384
    assert metered.requests[0]["max_body_bytes"] == 750_000
    assert metered.requests[0]["replay"] is False
    assert metered.requests[0]["tag"] == "P002/mock-vision/opaque-page/vision/0"
    url = body["messages"][1]["content"][0]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
    image_bytes = base64.b64decode(url.split(",", 1)[1])
    assert runner.sha(image_bytes) == result["image"]["image_sha256"]
    assert result["image"]["image_quality"] == 90
    assert result["image"]["image_codec"] == "JPEG"
    assert result["image"]["image_bytes"] == len(image_bytes)
    with Image.open(io.BytesIO(image_bytes)) as raster:
        assert raster.mode == "RGB"
        assert max(raster.size) == 1200
        assert list(raster.size) == result["image"]["image_size"]
    parsed = json.loads((tmp_path / "opaque-page-structure.json").read_text())
    assert parsed == adapter.parse(response(), result["viewport"])
    assert result["tables"] == parsed["tables"]
    assert all(table["text_provenance"] == "model-transcribed" for table in result["tables"])
    assert (tmp_path / "opaque-page.md").read_text() == adapter.markdown(parsed)


def test_calls_usage_and_raw_response_are_retained_before_parser_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    answer = response(finish="length")
    metered = client(tmp_path, answer)
    original = adapter.parse

    def parse(raw: dict[str, Any], viewport: list[float]) -> dict[str, Any]:
        retained = json.loads((tmp_path / "opaque-page-result.json").read_text())
        assert retained["transcription_response"] == raw
        assert retained["calls"][0]["usage"] == answer["usage"]
        assert retained["calls"][0]["entry"]["accounted_usd"] == 0.015
        assert (tmp_path / "opaque-page-request-0.json").exists()
        assert (tmp_path / "opaque-page-response-0.json").exists()
        return original(raw, viewport)

    monkeypatch.setattr(adapter, "parse", parse)
    result = runner.process(record(tmp_path), settings(), tmp_path, metered)
    assert result["status"] == "error"
    assert result["error_stage"] == "parse"
    assert result["tables"] == []
    assert len(result["calls"]) == 1
    assert result["transcription_response"] == answer
    assert not (tmp_path / "opaque-page-structure.json").exists()
    assert not (tmp_path / "opaque-page.md").exists()


def test_transport_error_retains_new_ledger_reservation_without_error_body(tmp_path: Path) -> None:
    metered = client(tmp_path, response())

    def request(_body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        metered.ledger.write_text(
            json.dumps(
                {
                    "requests": [
                        {
                            "index": 0,
                            "tag": kwargs["tag"],
                            "accounted_usd": 0.30,
                            "cost_status": "reserved",
                            "error": "HTTP 503",
                        }
                    ]
                }
            )
        )
        message = "DO_NOT_RETAIN_PROVIDER_BODY"
        raise RuntimeError(message)

    metered.request = request
    result = runner.process(record(tmp_path), settings(), tmp_path, metered)
    assert result["status"] == "error"
    assert len(result["calls"]) == 1
    assert result["calls"][0]["entry"]["accounted_usd"] == 0.30
    assert result["calls"][0]["status"] == "transport_error"
    assert "DO_NOT_RETAIN_PROVIDER_BODY" not in json.dumps(result)
    assert result["tables"] == []


def test_wave_cap_rejects_before_transmission_and_preserves_prior_entries(tmp_path: Path) -> None:
    metered = client(tmp_path, response())
    previous = {
        "requests": [
            {"index": 0, "tag": "P002/other", "accounted_usd": 49.8},
            {"index": 1, "tag": "P001/old", "accounted_usd": 50},
        ]
    }
    metered.ledger.write_text(json.dumps(previous))
    result = runner.process(record(tmp_path), settings(), tmp_path, metered)
    assert result["status"] == "error"
    assert result["error_type"] == "RuntimeError"
    assert result["calls"] == []
    assert metered.requests == []
    assert json.loads(metered.ledger.read_text()) == previous


def test_over_body_admission_is_visible_without_resize_or_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metered = client(tmp_path, response())
    original = adapter.request

    def request(*args: Any, **kwargs: Any) -> dict[str, Any]:
        body = original(*args, **kwargs)
        body["messages"][0]["content"] += "x" * 750_000
        return body

    monkeypatch.setattr(adapter, "request", request)
    result = runner.process(record(tmp_path), settings(image_edge=2048), tmp_path, metered)
    assert result["status"] == "error"
    assert "no resize or retry" in result["error"]
    assert result["request"]["body_bytes"] > 750_000
    assert result["image"]["image_edge"] == 2048
    assert metered.requests == []
    assert result["calls"] == []


def test_rotation_is_preserved_and_frozen_hash_mismatch_stops_before_request(tmp_path: Path) -> None:
    source = record(tmp_path)
    with pdfust.open(stream=pdf_bytes()) as document:
        document[0].set_rotation(90)
        data = document.tobytes()
    Path(source["pdf_path"]).write_bytes(data)
    source["pdf_sha256"] = runner.sha(data)
    metered = client(tmp_path, response())
    result = runner.process(source, settings(normalize_rotation=True), tmp_path, metered)
    assert result["status"] == "ok"
    assert result["original_rotation"] == 90
    assert not result["rotation_normalized"]
    assert result["viewport"] == [0, 0, 300, 340]
    source["pdf_sha256"] = "bad-frozen-hash"
    metered.requests.clear()
    result = runner.process(source, settings(), tmp_path, metered)
    assert result["status"] == "error"
    assert result["error_stage"] == "input"
    assert metered.requests == []


