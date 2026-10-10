"""Actual request archival and parser treatments using local transport stubs."""

# ruff: noqa: ANN401
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_report as report
from bench import generalization_vision_regions as regions
from bench import p003_client, pipeline_run
from bench import pipeline_vision_transcription as adapter
from bench.silver import sha
from test_generalization_vision_regions import Detector, _record, raw


class Client:
    """Retain actual wire dictionaries without credentials or inference."""

    def __init__(self, path: Path, response: dict[str, Any]) -> None:
        """Use an absent local ledger and predefined completion."""
        self.ledger = path / "absent-ledger.json"
        self.response = response
        self.bodies: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        """Capture the actual pinned transport body."""
        self.bodies.append(copy.deepcopy(body))
        return {"entry": {"index": len(self.bodies)}, "result": self.response, "replayed": False}


def atomic_response(*, gap: bool = False) -> dict[str, Any]:
    table = {"bbox": [0, 0, 1000, 1000], "row_count": 1, "col_count": 2 if gap else 1,
             "cells": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1, "text": "literal"}]}
    return {"choices": [{"finish_reason": "stop", "message": {
        "content": json.dumps({"answers": {"q0": {"tables": [table]}}}),
    }}]}


def test_legacy_constructor_byte_identical() -> None:
    args: tuple[str, str, list[float]] = ("anthropic/claude-haiku-5.5", "data:image/jpeg;base64,AA==", [0, 0, 1, 1])
    legacy = adapter.request(*args, max_tokens=321)
    actual = regions.transcription_request(*args, max_tokens=321)
    assert json.dumps(actual, separators=(",", ":")).encode() == json.dumps(legacy, separators=(",", ":")).encode()


@pytest.mark.parametrize("model", ["anthropic/claude-haiku-5.5", "openai/gpt-6-luna"])
@pytest.mark.parametrize("representation", ["legacy", "matrix_strict", "atomic_cells"])
@pytest.mark.parametrize("wire_schema", ["strict", "simple"])
def test_real_process_request_body_parser_and_saved_metadata(
    tmp_path: Path, model: str, representation: str, wire_schema: str,
) -> None:
    response = atomic_response() if representation == "atomic_cells" else raw([["literal"]])
    client = Client(tmp_path, response)
    config = {
        "campaign": "P003", "run_id": "stub", "generation_model": model, "generation_tokens": 321,
        "transcription_representation": representation, "generation_provider": "PinnedFixtureProvider",
        "transcription_wire_schema": wire_schema,
        "_layout_detector": Detector([{"label": "Table", "confidence": 0.9, "bbox": [10, 20, 100, 150]}]),
    }
    result = regions.process(_record(tmp_path), config, tmp_path, client)
    assert result["status"] == "ok"
    assert result["tables"][0]["values"] == [["literal"]]
    assert result["transcription_representation"] == representation
    assert len(client.bodies) == 1
    body = client.bodies[0]
    assert body["model"] == model
    assert body["max_tokens"] == 321
    assert body["provider"] == {"only": ["PinnedFixtureProvider"], "allow_fallbacks": False, "require_parameters": True}
    assert body == json.loads((tmp_path / "fixture-request-0.json").read_text())
    region = result["transcription_regions"][0]
    request = region["request"]
    encoded = json.dumps(body, separators=(",", ":")).encode()
    assert request["body_sha256"] == sha(encoded)
    assert request["body_bytes"] == len(encoded)
    assert request["transcription_representation"] == representation
    expected = regions.transcription_request(model, body["messages"][1]["content"][0]["image_url"]["url"],
                                             region["viewport"], max_tokens=321, representation=representation,
                                             wire_schema=wire_schema)
    assert expected["messages"] == body["messages"]
    assert expected["response_format"] == body["response_format"]
    assert report.verify_output(tmp_path, result, processor="vision_regions", config=config) == {
        "operational": True, "conserved": False,
    }
    if representation != "legacy" or wire_schema != "strict":
        body["messages"][0]["content"] = "changed prompt"
        (tmp_path / "fixture-request-0.json").write_text(json.dumps(body))
        with pytest.raises(ValueError, match="Actual transcription body"):
            report.verify_output(tmp_path, result, processor="vision_regions", config=config)


def test_failed_atomic_preserves_raw_body_costs_and_all_proposal_treatments(tmp_path: Path) -> None:
    client = Client(tmp_path, atomic_response(gap=True))
    config = {
        "campaign": "P003", "run_id": "stub", "generation_model": "anthropic/claude-haiku-5.5",
        "transcription_representation": "atomic_cells",
        "_layout_detector": Detector([{"label": "Table", "confidence": 0.9, "bbox": box}
                                      for box in ([10, 20, 100, 150], [200, 20, 400, 150])]),
    }
    result = regions.process(_record(tmp_path), config, tmp_path, client)
    assert result["status"] == "error"
    assert result["error_stage"] == "parse"
    assert result["tables"] == []
    assert len(result["calls"]) == 1
    assert json.loads((tmp_path / "fixture-response-0.json").read_text()) == client.response
    assert not (tmp_path / "fixture-structure.json").exists()
    assert [r["transcription_representation"] for r in result["transcription_regions"]] == ["atomic_cells"] * 2
    assert report.verify_output(tmp_path, result, processor="vision_regions", config=config) == {
        "operational": False, "conserved": False,
    }
    result["transcription_representation"] = "legacy"
    (tmp_path / "fixture-result.json").write_text(json.dumps(result))
    with pytest.raises(ValueError, match="representation differs"):
        report.verify_output(tmp_path, result, processor="vision_regions", config=config)


def test_nonlegacy_candidate_configuration_refuses_before_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Nonlegacy transcription"):
        pipeline_run.run(tmp_path / "no-manifest.json", tmp_path / "output", {
            "campaign": "P003", "processor": "p003_regions", "transcription_representation": "atomic_cells",
        })
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("representation", ["legacy", "matrix_strict", "atomic_cells"])
def test_freeze_variant_dependencies_without_client_or_requests(tmp_path: Path, representation: str) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"split": "DEV", "pages": []}))
    output = tmp_path / "run"
    result = pipeline_run.run(manifest, output, {
        "campaign": "P003", "processor": "vision_regions", "transcription_representation": representation,
        "policy": "native", "order_seed": 1, "pilot": False, "run_id": "offline-empty",
        "generation_model": "anthropic/claude-haiku-5.5", "generation_format": "indices",
    })
    frozen = json.loads((output / "frozen.json").read_text())
    assert ("p003_transcription_design.py" in frozen["code_sha256"]) is (representation != "legacy")
    assert result["calls"] == 0
    assert report.verify_code(output, frozen, processor="vision_regions")["archive_hashes_verified"] is True
    if representation != "legacy":
        frozen["code_sha256"].pop("p003_transcription_design.py")
        with pytest.raises(ValueError, match="required verifier dependencies"):
            report.verify_code(output, frozen, processor="vision_regions")


@pytest.mark.parametrize("settings", [
    {"campaign": "P002", "transport_concurrency": 3},
    {"campaign": "P003", "transport_concurrency": 3, "gate_provider": "vercel"},
    {"campaign": "P003", "transport_concurrency": True},
])
def test_transport_configuration_refuses_before_client_or_files(tmp_path: Path, settings: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="Transport concurrency"):
        pipeline_run.run(tmp_path / "absent.json", tmp_path / "output", settings)
    assert not (tmp_path / "output").exists()


def test_transport_three_client_freeze_and_contended_labels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    constructed = []

    def fake_concurrent(root: Path) -> Client:
        constructed.append(root)
        return Client(tmp_path, raw())

    (tmp_path / "ledger.json").write_text(json.dumps({"requests": []}))
    monkeypatch.setattr(pipeline_run, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(pipeline_run, "DecisionClient", lambda: Client(tmp_path, raw()))
    monkeypatch.setattr(p003_client, "P003ConcurrentClient", fake_concurrent)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"split": "DEV", "pages": []}))
    output = tmp_path / "run"
    result = pipeline_run.run(manifest, output, {
        "campaign": "P003", "processor": "vision_regions", "transport_concurrency": 3,
        "policy": "gated", "order_seed": 1, "pilot": False, "run_id": "offline-empty",
        "generation_model": "anthropic/claude-haiku-5.5",
    })
    frozen = json.loads((output / "frozen.json").read_text())
    assert constructed == [Path(pipeline_run.__file__).parent.parent]
    assert "decision_concurrent.py" in frozen["code_sha256"]
    assert frozen["concurrency"] == 1
    assert frozen["transport_concurrency"] == 3
    assert "contended" in result["performance_scope"]
    assert "contended" in result["metrics"]["performance_scope"]
    assert result["calls"] == 0


@pytest.mark.parametrize("representation", ["legacy", "matrix_strict", "atomic_cells"])
@pytest.mark.parametrize("concurrency", [1, 3])
def test_cli_declares_representation_and_only_explicit_three_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, representation: str, concurrency: int,
) -> None:
    import sys  # noqa: PLC0415 - isolated CLI fixture.

    from bench import p003_run  # noqa: PLC0415 - isolated CLI fixture.

    captured = []

    def fake_run(_manifest: Path, _output: Path, config: dict[str, Any]) -> dict[str, Any]:
        captured.append(config)
        return {}

    monkeypatch.setattr(pipeline_run, "run", fake_run)
    monkeypatch.setattr(sys, "argv", [
        "p003_run", "--manifest", str(tmp_path / "manifest.json"), "--output", str(tmp_path / "output"),
        "--preset", "vision_regions", "--image-edge", "1024",
        "--transcription-representation", representation, "--transport-concurrency", str(concurrency),
    ])
    p003_run.main()
    assert captured[0]["transcription_representation"] == representation
    assert captured[0].get("transport_concurrency", 1) == concurrency
    assert ("transport_concurrency" in captured[0]) is (concurrency == 3)
