"""CPU-only orchestration mocks; no credentials, provider calls or OCR."""

from __future__ import annotations

import json
import random
import threading
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from bench import decision_hosted as hosted
from bench import pipeline_run as runner
from bench.decision_concurrent import ConcurrentDecisionClient


def config(**extra: Any) -> dict[str, Any]:  # noqa: ANN401
    return {
        "campaign": "P002", "processor": "vision", "policy": "gated", "run_id": "mock",
        "generation_model": "anthropic/claude-haiku-5.5", "workers": 4,
        "generation_tokens": 16384, "pilot": False, "order_seed": 42, **extra,
    }


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, hosted.DecisionClient]:
    client = hosted.DecisionClient.__new__(hosted.DecisionClient)
    client.root = tmp_path
    client.directory = tmp_path / "ledger"
    client.directory.mkdir()
    client.ledger = client.directory / "ledger.json"
    client.ledger.write_text('{"requests":[]}')
    client.key = "mock-never-used"
    monkeypatch.setattr(runner, "DecisionClient", lambda: client)
    monkeypatch.setattr(runner, "ARTIFACTS", client.directory)
    monkeypatch.setattr(runner, "runtime_fingerprints", lambda: {"mock": True})
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"split": "DEV", "pages": [
        {"id": f"p{i}", "pdf_path": str(tmp_path / "source.pdf"), "pdf_sha256": "mock",
         "page_number": i, "pilot": True} for i in range(4)
    ]}))
    return manifest, client


def test_four_workers_overlap_drain_failures_and_preserve_frozen_order(
    setup: tuple[Path, hosted.DecisionClient], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _client = setup
    overlap = threading.Barrier(4)
    expected = [f"p{i}" for i in range(4)]
    random.Random(42).shuffle(expected)  # noqa: S311 - matched frozen order.
    gates = {ident: threading.Event() for ident in expected}
    gates[expected[-1]].set()
    finished: list[str] = []
    lock = threading.Lock()

    def process(record: dict[str, Any], settings: dict[str, Any], output: Path, client: Any) -> dict[str, Any]:  # noqa: ANN401
        assert isinstance(client, ConcurrentDecisionClient)
        assert client.policy == {"max_inflight": 4, "wave_limits_usd": {"P002": 50.0}}
        assert settings["workers"] == 4
        overlap.wait(timeout=5)
        ident = record["id"]
        assert gates[ident].wait(timeout=5)
        with lock:
            finished.append(ident)
        rank = expected.index(ident)
        if rank:
            gates[expected[rank - 1]].set()
        if record["id"] == "p1":
            raise ValueError  # catastrophic processor failure must remain a page
        row = {"id": record["id"], "status": "ok", "tables": [], "calls": []}
        runner.write_json(output / f"{record['id']}-result.json", row)
        return row

    monkeypatch.setattr(runner, "_processor", lambda _name: process)
    output = tmp_path / "output"
    result = runner.run(manifest, output, config())
    frozen = json.loads((output / "frozen.json").read_text())
    assert finished == list(reversed(expected))
    assert [row["id"] for row in result["results"]] == [row["id"] for row in frozen["records"]]
    assert result["page_count"] == 4
    assert result["complete_output_pages"] == 3
    assert next(row for row in result["results"] if row["id"] == "p1")["error_stage"] == "worker"
    assert frozen["concurrency"] == 4
    assert "nonadditive" in result["metrics"]["per_page_cpu_scope"]
    for name in ("decision_concurrent.py", "decision_gateway.py", "decision_langfuse.py", "reprice_model_rates.py"):
        assert frozen["code_sha256"][name] == runner.sha((runner.ROOT / "bench" / name).read_bytes())
        assert (output / "code" / name).exists()


def test_default_serial_path_keeps_client_and_dependency_set(
    setup: tuple[Path, hosted.DecisionClient], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, original = setup
    called: list[str] = []

    def process(record: dict[str, Any], _settings: dict[str, Any], _output: Path, client: Any) -> dict[str, Any]:  # noqa: ANN401
        assert client is original
        called.append(record["id"])
        return {"id": record["id"], "status": "ok", "calls": []}

    monkeypatch.setattr(runner, "_processor", lambda _name: process)
    settings = config(generation_model="anthropic/claude-sonnet-5.5")
    del settings["workers"]
    output = tmp_path / "serial"
    result = runner.run(manifest, output, settings)
    frozen = json.loads((output / "frozen.json").read_text())
    assert called == [row["id"] for row in frozen["records"]]
    assert result["page_count"] == 4
    assert frozen["concurrency"] == 1
    assert "decision_concurrent.py" not in frozen["code_sha256"]
    assert "per_page_cpu_scope" not in result["metrics"]


@pytest.mark.parametrize("override", [
    {"processor": "regions"}, {"processor": "vision_regions"}, {"processor": "hybrid"},
    {"campaign": "P001"}, {"generation_model": "anthropic/claude-sonnet-5.5"},
    {"model": "anthropic/claude-opus-5.5"}, {"generation_tokens": 16385},
    {"generation_tokens": True}, {"ocr_empty": True}, {"layout_detector": "yolo"},
    {"retry_failed_index": 1, "retry_reason": "reviewed"}, {"replay": True},
    {"policy": "native"}, {"workers": 2},
])
def test_unsupported_routes_reject_before_manifest_client_or_output(
    override: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    construct = MagicMock(side_effect=AssertionError("Client must not be constructed"))
    monkeypatch.setattr(runner, "DecisionClient", construct)
    output = tmp_path / "absent"
    with pytest.raises(ValueError, match=r"Workers|Four workers"):
        runner.run(tmp_path / "missing-manifest.json", output, config(**override))
    assert not output.exists()
    construct.assert_not_called()


def test_duplicate_ids_reject_before_client_or_output(
    setup: tuple[Path, hosted.DecisionClient], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, _client = setup
    content = json.loads(manifest.read_text())
    content["pages"][1]["id"] = content["pages"][0]["id"]
    manifest.write_text(json.dumps(content))
    construct = MagicMock(side_effect=AssertionError("Client must not be constructed"))
    monkeypatch.setattr(runner, "DecisionClient", construct)
    output = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="unique"):
        runner.run(manifest, output, config())
    assert not output.exists()
    construct.assert_not_called()


def test_parallel_page_cpu_labels_are_explicit_on_visible_input_failure(tmp_path: Path) -> None:
    from bench import generalization_vision_run as vision  # noqa: PLC0415 - exercise the retained page path.

    row = vision.process(
        {"id": "missing", "pdf_path": str(tmp_path / "absent.pdf"), "pdf_sha256": "mock", "page_number": 0},
        config(), tmp_path, None,
    )
    assert row["status"] == "error"
    assert "nonadditive" in row["cpu_measurement_scope"]
    assert (tmp_path / "missing-result.json").exists()
