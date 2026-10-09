"""CPU-only worker admission, durable logs, watchdog and resource mocks."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import remote_worker


@pytest.fixture(autouse=True)
def mock_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the entire test module CPU-only even if another test imported torch."""
    monkeypatch.setitem(
        remote_worker.sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    )


class Adapter:
    """Injected model facade; no weights, hardware or credentials."""

    def __init__(self, *, failing: bool = False, init_failing: bool = False) -> None:
        """Set deterministic source-independent mock behavior."""
        self.failing = failing
        self.init_failing = init_failing
        self.loads = 0
        self.calls: list[tuple[dict[str, Any], list[Path]]] = []

    def load(self, _model_dir: str | Path, device: str) -> object:
        """Record a local initialization without importing a model library."""
        self.loads += 1
        assert device == "cpu"
        if self.init_failing:
            message = "mock initialization refused"
            raise RuntimeError(message)
        return object()

    def predict(self, _engine: object, body: dict[str, Any], image_paths: list[Path]) -> dict[str, Any]:
        """Return native fields or an intentional bounded failure."""
        self.calls.append((body, image_paths))
        if self.failing:
            message = "mock inference refused"
            raise RuntimeError(message)
        return {"answers": {"q0": {"choice": "unresolved"}}, "usage": {"native_counter": 17}}


@pytest.fixture
def packets(tmp_path: Path) -> Path:
    """Freeze five source-only packets and one local image per request."""
    records = []
    for index in range(5):
        request = tmp_path / f"request-{index}.json"
        request.write_text(json.dumps({"state": f"source {index}", "questions": {"q0": {"type": "choice"}}}))
        image = tmp_path / f"image-{index}.png"
        image.write_bytes(b"mock staged image; adapter mock does not decode")
        records.append({"id": str(index), "request_file": request.name, "image_files": [image.name]})
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"records": records}))
    return manifest


def test_success_limit_logs_and_native_response(packets: Path, tmp_path: Path) -> None:
    adapter = Adapter()
    output = tmp_path / "output"
    status = remote_worker.run(adapter, tmp_path, packets, output, 2, device="cpu", sample_gpu=False)
    assert status["status"] == "complete"
    assert status["attempted_records"] == status["successful_records"] == 2
    assert adapter.loads == 1
    assert len(adapter.calls) == 2
    entries = [json.loads(line) for line in (output / "attempts.jsonl").read_text().splitlines()]
    assert len(entries) == 4
    assert [entry["event"] for entry in entries] == ["attempt_started", "attempt_completed"] * 2
    completed = entries[1]
    assert completed["response"]["usage"] == {"native_counter": 17}
    assert "input_tokens" not in completed["response"]["usage"]
    assert completed["wall_seconds"] >= 0
    assert completed["cpu_seconds"] >= 0
    assert status["initialization"]["wall_seconds"] >= 0
    assert json.loads((output / "status.json").read_text()) == status


def test_three_failures_stop_without_retry(packets: Path, tmp_path: Path) -> None:
    adapter = Adapter(failing=True)
    status = remote_worker.run(adapter, tmp_path, packets, tmp_path / "fail", 5, device="cpu", sample_gpu=False)
    assert status["status"] == "failure_limit"
    assert status["attempted_records"] == status["failed_records"] == 3
    assert len(adapter.calls) == 3


def test_existing_output_refused(packets: Path, tmp_path: Path) -> None:
    output = tmp_path / "done"
    remote_worker.run(Adapter(), tmp_path, packets, output, 1, device="cpu", sample_gpu=False)
    adapter = Adapter()
    with pytest.raises(ValueError, match="no automatic retries"):
        remote_worker.run(adapter, tmp_path, packets, output, 1, device="cpu", sample_gpu=False)
    assert adapter.loads == 0


def test_initialization_failure_checkpoint(packets: Path, tmp_path: Path) -> None:
    adapter = Adapter(init_failing=True)
    status = remote_worker.run(adapter, tmp_path, packets, tmp_path / "init", 1, device="cpu", sample_gpu=False)
    assert status["status"] == "worker_error"
    assert status["attempted_records"] == 0
    assert status["error_type"] == "RuntimeError"
    assert not adapter.calls


def test_source_manifest_cannot_include_references(packets: Path) -> None:
    manifest = json.loads(packets.read_text())
    manifest["references"] = {"0": "join"}
    packets.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="only records"):
        remote_worker.inventory(packets, 1)


def test_path_escape_refused(packets: Path, tmp_path: Path) -> None:
    other = tmp_path.parent / "outside-source.json"
    other.write_text("{}")
    manifest = json.loads(packets.read_text())
    manifest["records"][0]["request_file"] = str(other)
    packets.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="inside the manifest"):
        remote_worker.inventory(packets, 1)


def test_unknown_cuda_measurements_are_not_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(remote_worker.sys.modules, "torch", raising=False)
    stats = remote_worker._cuda()  # noqa: SLF001 -- optional measurement boundary
    assert stats["peak_allocated_bytes"] is None
    assert stats["peak_reserved_bytes"] is None


def test_sampler_unavailable_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sampled = threading.Event()

    def missing_smi(*_args: Any, **_kwargs: Any) -> None:  # noqa: ANN401
        sampled.set()
        message = "mock missing nvidia-smi"
        raise FileNotFoundError(message)

    monkeypatch.setattr(remote_worker.subprocess, "run", missing_smi)
    sampler = remote_worker.Sampler(tmp_path / "samples.jsonl")
    sampler.start()
    assert sampled.wait(timeout=1)
    sampler.close()
    sample = json.loads((tmp_path / "samples.jsonl").read_text().splitlines()[0])
    assert sample["raw_csv"] is None
    assert sample["scope"] == "device-wide"
    assert sample["interval_seconds"] == 1


def test_supervisor_kills_blocked_child(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Process:
        exitcode = None

        def __init__(self, **_kwargs: Any) -> None:  # noqa: ANN401
            self.alive = True
            self.terminated = False

        def start(self) -> None:
            pass

        def join(self, timeout: float) -> None:
            pass

        def is_alive(self) -> bool:
            return self.alive

        def terminate(self) -> None:
            self.alive = False
            self.terminated = True

    process = Process()
    monkeypatch.setattr(
        remote_worker.multiprocessing, "get_context", lambda _method: SimpleNamespace(Process=lambda **_kwargs: process)
    )
    output = tmp_path / "watchdog"
    code = remote_worker.supervise({"output": str(output), "deadline_seconds": 0.1, "adapter": "bench.remote_clef"})
    assert code == 2
    assert process.terminated
    status = json.loads((output / "status.json").read_text())
    assert status["status"] == "deadline_exceeded"
    assert status["hard_deadline"] is True


def test_failure_streak_resets_on_success(packets: Path, tmp_path: Path) -> None:
    class Intermittent(Adapter):
        def predict(self, _engine: object, body: dict[str, Any], image_paths: list[Path]) -> dict[str, Any]:
            self.failing = body["state"] != "source 1"
            return super().predict(_engine, body, image_paths)

    adapter = Intermittent()
    status = remote_worker.run(adapter, tmp_path, packets, tmp_path / "streak", 5, device="cpu", sample_gpu=False)
    assert status["status"] == "failure_limit"
    assert status["failed_records"] == 4
    assert status["successful_records"] == 1
    assert status["attempted_records"] == 5
