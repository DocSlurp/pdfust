"""CPU-only concurrency checks with mocked workers and resource samplers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from bench import remote_concurrent as rc


def packets(tmp_path: Path, count: int = 8) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    rows = []
    for i in range(count):
        name = f"p{i}.json"
        (source / name).write_text(
            json.dumps(
                {
                    "state": [f"literal source {i}"],
                    "questions": {"q0": {"criteria": {"join": "a", "split": "b", "unresolved": "c"}}},
                }
            )
        )
        image = f"p{i}.png"
        (source / image).write_bytes(b"source-image-" + bytes([i]))
        rows.append({"id": f"p{i}", "request_file": name, "image_files": [image]})
    manifest = source / "manifest.json"
    manifest.write_text(json.dumps({"records": rows}))
    return manifest


def complete_worker(output: Path, rows: list[dict], *, fail: bool = False) -> None:
    output.mkdir(parents=True)
    events = []
    for i, row in enumerate(rows):
        events.extend(
            [
                {"event": "attempt_started", "id": row["id"], "monotonic_seconds": 10.0 + i},
                {
                    "event": "attempt_completed",
                    "id": row["id"],
                    "monotonic_seconds": 10.0 + i,
                    "wall_seconds": 0.5,
                    "request_sha256": row["request_sha256"],
                    "status": "error" if fail else "ok",
                },
            ]
        )
    (output / "attempts.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (output / "status.json").write_text(json.dumps({"status": "complete", "cpu_seconds": 2.0, "peak_rss_bytes": 100}))


def test_shards_preserve_bytes_and_ids(tmp_path: Path) -> None:
    source = packets(tmp_path)
    out = tmp_path / "out"
    facts = rc.shard(source, out, 8, 4)
    seen = []
    for lane in range(4):
        manifest = out / "shards" / f"lane-{lane:02d}" / "manifest.json"
        rows = json.loads(manifest.read_text())["records"]
        assert len(rows) == 2
        for row in rows:
            seen.append(row["id"])
            i = row["id"][1:]
            assert (manifest.parent / row["request_file"]).read_bytes() == (source.parent / f"p{i}.json").read_bytes()
            assert (manifest.parent / row["image_files"][0]).read_bytes() == (source.parent / f"p{i}.png").read_bytes()
    assert set(seen) == {f"p{i}" for i in range(8)}
    assert len(seen) == len(set(seen))
    assert facts["source_manifest_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        rc.shard(source, out, 8, 4)


@pytest.mark.parametrize("lanes", [0, 3, 16])
def test_invalid_lane_counts(tmp_path: Path, lanes: int) -> None:
    with pytest.raises(ValueError, match="lanes"):
        rc.shard(packets(tmp_path), tmp_path / "out", 8, lanes)


def test_collect_separates_actual_wall_from_sum_latency_and_peak_rss(tmp_path: Path) -> None:
    out = tmp_path / "out"
    facts = rc.shard(packets(tmp_path), out, 8, 2)
    for lane in range(2):
        complete_worker(out / f"worker-{lane:02d}", [r for r in facts["records"] if r["lane"] == lane])
    result = rc.collect(out, 5.0)
    assert result["status"] == "complete"
    assert result["successful_records"] == 8
    assert result["cpu_seconds"] == 4.0
    assert result["peak_rss_bytes"] is None
    assert result["regions_per_global_minute"] == 96
    assert result["concurrent_request_span_seconds"] == 3.5
    assert len((out / "attempts.jsonl").read_text().splitlines()) == 16


def test_collect_rejects_changed_hash_and_duplicate_attempt(tmp_path: Path) -> None:
    out = tmp_path / "out"
    facts = rc.shard(packets(tmp_path, 2), out, 2, 1)
    complete_worker(out / "worker-00", facts["records"])
    path = out / "worker-00/attempts.jsonl"
    payload = path.read_text()
    path.write_text(payload.replace(facts["records"][0]["request_sha256"], "wrong"))
    with pytest.raises(ValueError, match="hash"):
        rc.collect(out, 1)
    path.write_text(payload + payload)
    with pytest.raises(ValueError, match="duplicate"):
        rc.collect(out, 1)


def test_checkpoint_does_not_invent_complete_throughput(tmp_path: Path) -> None:
    out = tmp_path / "out"
    facts = rc.shard(packets(tmp_path, 4), out, 4, 2)
    complete_worker(out / "worker-00", [r for r in facts["records"] if r["lane"] == 0])
    result = rc.collect(out, 3)
    assert result["status"] == "checkpoint"
    assert result["successful_records"] == 2
    assert result["regions_per_global_minute"] is None
    assert result["cpu_seconds"] is None


def test_native_memory_admission_before_staging(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="memory"):
        rc.run(
            adapter="bench.remote_clef",
            model_dir="local",
            packets=str(packets(tmp_path)),
            output=str(tmp_path / "out"),
            limit=8,
            lanes=2,
            deadline_seconds=2,
            native_budget_gib=80,
            per_lane_peak_gib=51,
        )
    assert not (tmp_path / "out").exists()


def test_run_uses_current_venv_and_keeps_server_shared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = packets(tmp_path, 4)
    out = tmp_path / "out"
    commands = []

    class SilentSampler:
        def __init__(self, *args: object) -> None:
            pass

        def start(self) -> None:
            pass

        def close(self) -> None:
            pass

    class FakeProcess:
        returncode = 0
        pid = 123

        def __init__(self, command: list[str], **_kwargs: object) -> None:
            commands.append(command)
            lane_manifest = Path(command[command.index("--packets") + 1])
            output = Path(command[command.index("--output") + 1])
            rows = json.loads(lane_manifest.read_text())["records"]
            complete_worker(
                output,
                [
                    {
                        "id": r["id"],
                        "request_sha256": hashlib.sha256(
                            (lane_manifest.parent / r["request_file"]).read_bytes()
                        ).hexdigest(),
                    }
                    for r in rows
                ],
            )

        def poll(self) -> int:
            return 0

    monkeypatch.setattr(rc, "Sampler", SilentSampler)
    monkeypatch.setattr(rc, "ProcessSampler", SilentSampler)
    monkeypatch.setattr(rc.subprocess, "Popen", FakeProcess)
    result = rc.run(
        adapter="bench.remote_vllm",
        model_dir="shared-server-config",
        packets=str(manifest),
        output=str(out),
        limit=4,
        lanes=2,
        deadline_seconds=5,
        server_pid=999,
    )
    assert result["status"] == "complete"
    assert len(commands) == 2
    assert all(c[0] == rc.sys.executable for c in commands)
    assert all("shared-server-config" in c for c in commands)
    assert result["server_pid"] == 999
