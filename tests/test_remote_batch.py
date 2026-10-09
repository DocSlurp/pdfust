"""CPU-only true-batch worker accounting and source-hash checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from bench import remote_batch as worker


def packets(path: Path, count: int) -> Path:
    source = path / "packets"
    source.mkdir()
    rows = []
    for i in range(count):
        name = f"p{i}.json"
        (source / name).write_text(json.dumps({"state": f"literal-{i}"}))
        rows.append({"id": f"p{i}", "request_file": name, "image_files": []})
    manifest = source / "manifest.json"
    manifest.write_text(json.dumps({"records": rows}))
    return manifest


def test_worker_uses_one_engine_and_unique_batch_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = packets(tmp_path, 5)
    loads = []
    calls = []

    def load(folder: str, **_options: object) -> object:
        loads.append(folder)
        return "engine"

    def predict(engine: object, bodies: list, _images: list) -> list:
        assert engine == "engine"
        calls.append([b["state"] for b in bodies])
        return [
            {
                "answers": {
                    "q0": {
                        "type": "choice",
                        "choice": "join",
                        "probabilities": {"join": 0.7, "split": 0.2, "unresolved": 0.1},
                    }
                },
                "usage": {"input_tokens": 7, "output_tokens": 0},
            }
            for _ in bodies
        ]

    monkeypatch.setattr(worker, "_cuda", lambda **_kw: {"peak_allocated_bytes": 100, "peak_reserved_bytes": 200})
    result = worker.run(
        SimpleNamespace(load=load, predict_batch=predict),
        model_dir="local",
        packets=str(manifest),
        output=str(tmp_path / "out"),
        limit=5,
        batch_size=2,
        deadline_seconds=20,
        device="cpu",
        sample_gpu=False,
    )
    assert result["status"] == "complete"
    assert loads == ["local"]
    assert list(map(len, calls)) == [2, 2, 1]
    assert result["successful_records"] == 5
    batches = [json.loads(x) for x in (tmp_path / "out/batches.jsonl").read_text().splitlines()]
    assert len(batches) == 3
    assert result["total_batch_inference_seconds"] == sum(b["inference_wall_seconds"] for b in batches)
    events = [json.loads(x) for x in (tmp_path / "out/attempts.jsonl").read_text().splitlines()]
    done = [e for e in events if e["event"] == "attempt_completed"]
    assert len(done) == 5
    for e in done:
        assert e["request_sha256"] == hashlib.sha256((manifest.parent / f"{e['id']}.json").read_bytes()).hexdigest()
        assert e["inference_wall_seconds"] is None
        assert e["wall_seconds"] is None
        assert e["response"]["usage"]["input_tokens"] == 7
    with pytest.raises(FileExistsError):
        worker.run(
            SimpleNamespace(),
            model_dir="local",
            packets=str(manifest),
            output=str(tmp_path / "out"),
            limit=5,
            batch_size=2,
            deadline_seconds=20,
            sample_gpu=False,
        )


def test_failed_batch_preserves_all_ids_no_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = packets(tmp_path, 8)
    calls = []

    def predict(_engine: object, bodies: list, _images: list) -> list:
        calls.append(bodies)
        message = "mock refusal"
        raise ValueError(message)

    monkeypatch.setattr(worker, "_cuda", lambda **_kw: {"peak_allocated_bytes": None, "peak_reserved_bytes": None})
    result = worker.run(
        SimpleNamespace(load=lambda *_a, **_k: None, predict_batch=predict),
        model_dir="local",
        packets=str(manifest),
        output=str(tmp_path / "out"),
        limit=8,
        batch_size=4,
        deadline_seconds=20,
        sample_gpu=False,
    )
    assert result["status"] == "failure_limit"
    assert len(calls) == 1
    assert result["attempted_records"] == 4
    assert result["failed_records"] == 4
    events = [json.loads(x) for x in (tmp_path / "out/attempts.jsonl").read_text().splitlines()]
    assert len(events) == 8
    assert all(e.get("request_sha256") for e in events if e["event"] == "attempt_completed")
    assert "regions_per_batch_inference_minute" not in result


def test_hard_deadline_preserves_active_checkpoint_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "out"
    calls: list[tuple[str, float | None]] = []

    class BlockedProcess:
        exitcode = None

        def __init__(self, **_options: object) -> None:
            self.alive = True

        def start(self) -> None:
            output.mkdir()
            (output / "status.json").write_text(json.dumps({"status": "running", "active_records": ["p0", "p1"]}))

        def join(self, timeout: float) -> None:
            calls.append(("join", timeout))

        def is_alive(self) -> bool:
            return self.alive

        def terminate(self) -> None:
            calls.append(("terminate", None))
            self.alive = False

    context = SimpleNamespace(Process=BlockedProcess)
    monkeypatch.setattr(worker.multiprocessing, "get_context", lambda _method: context)
    assert worker.supervise({"output": str(output), "deadline_seconds": 2}) == 2
    status = json.loads((output / "status.json").read_text())
    assert status["status"] == "deadline_exceeded"
    assert status["active_records"] == ["p0", "p1"]
    assert status["hard_deadline"] is True
    assert calls == [("join", 2), ("terminate", None), ("join", 3)]
    with pytest.raises(ValueError, match="fresh"):
        worker.supervise({"output": str(output), "deadline_seconds": 2})
