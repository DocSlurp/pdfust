# ruff: noqa: ANN001, ANN002, ANN003, ANN204, SLF001, ANN201, ANN202 - injected fake process APIs.
import json
import signal
from types import SimpleNamespace

import pytest
from bench import remote_vllm_sweep as sweep


def test_command_is_bounded_and_model_specific(monkeypatch, tmp_path):
    models = dict(sweep.MODELS)
    models.update({"HuggingFaceTB/SmolVLM2-2.2B-Instruct": "smol-pin", "openbmb/MiniCPM-V-4": "mini-pin"})
    monkeypatch.setattr(sweep, "MODELS", models)
    normal = sweep.server_command("Qwen/Qwen3.5-2B", tmp_path)
    assert normal[normal.index("--host") + 1] == "127.0.0.1"
    assert normal[normal.index("--max-model-len") + 1] == "8192"
    assert "--no-enable-prefix-caching" in normal
    assert normal[normal.index("--limit-mm-per-prompt") + 1] == '{"image":1,"video":0}'
    assert "--trust-remote-code" not in normal
    assert "--trust-remote-code" in sweep.server_command("openbmb/MiniCPM-V-4", tmp_path)
    assert "--chat-template-content-format" in sweep.server_command("HuggingFaceTB/SmolVLM2-2.2B-Instruct", tmp_path)
    assert "token=False" in sweep.SNAPSHOT_CODE
    assert "*.safetensors" in sweep.SNAPSHOT_CODE


def test_controls_require_three_correct_choices(tmp_path):
    (tmp_path / "status.json").write_text('{"status":"complete"}')
    rows = [
        {"event": "attempt_started", "status": "ok", "response": {"answers": {"q": {"choice": choice}}}}
        for choice in ("join", "split", "unresolved")
    ]
    path = tmp_path / "attempts.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows))
    assert sweep.controls_pass(tmp_path)
    rows[1]["response"]["answers"]["q"]["choice"] = "join"
    path.write_text("\n".join(json.dumps(row) for row in rows))
    assert not sweep.controls_pass(tmp_path)


def test_stop_verifies_owned_group(monkeypatch):
    signals = []

    def kill(pid, sig):
        assert pid == 42
        signals.append(sig)
        if sig == 0:
            raise ProcessLookupError

    monkeypatch.setattr(sweep.os, "killpg", kill)
    sweep.stop_group(SimpleNamespace(pid=42, wait=lambda **_: 0))
    assert signals == [signal.SIGTERM, 0]


def test_run_model_controls_failure_always_stops_server(monkeypatch, tmp_path):
    processes = []
    stopped = []
    workers = []

    def spawn(*_args, **_kwargs):
        process = SimpleNamespace(pid=100 + len(processes), wait=lambda **_: 0, returncode=0, poll=lambda: None)
        processes.append(process)
        return process

    monkeypatch.setattr(sweep.subprocess, "run", lambda *_a, **_k: None)
    monkeypatch.setattr(sweep.subprocess, "Popen", spawn)
    monkeypatch.setattr(sweep, "wait_health", lambda *_a: None)
    monkeypatch.setattr(sweep, "stop_group", lambda p: stopped.append(p.pid))
    monkeypatch.setattr(sweep, "_worker", lambda *_a: workers.append(_a[3]))
    monkeypatch.setattr(sweep, "controls_pass", lambda *_a: False)
    result = sweep.run_model(tmp_path, tmp_path, "Qwen/Qwen3.5-2B", sweep.time.monotonic() + 10)
    assert result["status"] == "failed"
    assert workers == ["controls"]
    assert stopped == [100]
    assert result["server_exit_verified"]
    assert (tmp_path / "result.json").exists()


def test_cleanup_failure_blocks_success(monkeypatch, tmp_path):
    monkeypatch.setattr(sweep.subprocess, "run", lambda *_a, **_k: None)
    monkeypatch.setattr(
        sweep.subprocess,
        "Popen",
        lambda *_a, **_k: SimpleNamespace(pid=1, wait=lambda **_: 0, returncode=0, poll=lambda: None),
    )
    monkeypatch.setattr(sweep, "wait_health", lambda *_a: None)
    monkeypatch.setattr(sweep, "_worker", lambda *_a: None)
    monkeypatch.setattr(sweep, "controls_pass", lambda *_a: True)

    def refuse(_process):
        message = "still alive"
        raise RuntimeError(message)

    monkeypatch.setattr(sweep, "stop_group", refuse)
    result = sweep.run_model(tmp_path, tmp_path, "Qwen/Qwen3.5-2B", sweep.time.monotonic() + 10)
    assert result["status"] == "cleanup_failed"
    assert not result["server_exit_verified"]


def test_unadmitted_models_and_invalid_deadlines_refused(tmp_path):
    with pytest.raises(ValueError, match="admitted"):
        sweep.sweep(["unknown"], tmp_path)
    with pytest.raises(ValueError, match="finite"):
        sweep.sweep(["Qwen/Qwen3.5-2B"], tmp_path, float("inf"))


def test_worker_timeout_stops_child_group(monkeypatch, tmp_path):
    stopped = []

    def wait(**_kwargs):
        command = "worker"
        raise sweep.subprocess.TimeoutExpired(command, 1)

    worker = SimpleNamespace(pid=99, wait=wait)
    monkeypatch.setattr(sweep.subprocess, "Popen", lambda *_a, **_k: worker)
    monkeypatch.setattr(sweep, "stop_group", lambda process: stopped.append(process.pid))
    with pytest.raises(sweep.subprocess.TimeoutExpired):
        sweep._worker(tmp_path, tmp_path, tmp_path / "worker", "packets", 216, sweep.time.monotonic() + 10)
    assert stopped == [99]


def test_three_failed_models_stop_sweep(monkeypatch, tmp_path):
    for directory in ("bench", "packets", "controls"):
        (tmp_path / directory).mkdir()
    calls = []

    def run(_workspace, _directory, model, _deadline, **_options):
        calls.append(model)
        return {"status": "failed", "server_exit_verified": True}

    class Probe:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def connect_ex(self, _address):
            return 1

    monkeypatch.setattr(sweep.socket, "socket", Probe)
    monkeypatch.setattr(sweep, "run_model", run)
    sweep.sweep(list(sweep.MODELS)[:4], tmp_path)
    assert len(calls) == 3
    with pytest.raises(FileExistsError):
        sweep.sweep(list(sweep.MODELS)[:4], tmp_path)


def test_health_refuses_dead_server():
    with pytest.raises(RuntimeError, match="exited"):
        sweep.wait_health(SimpleNamespace(poll=lambda: 1), sweep.time.monotonic() + 10)


def test_success_runs_controls_then_source_once(monkeypatch, tmp_path):
    workers = []
    monkeypatch.setattr(sweep.subprocess, "run", lambda *_a, **_k: None)
    monkeypatch.setattr(
        sweep.subprocess,
        "Popen",
        lambda *_a, **_k: SimpleNamespace(pid=1, wait=lambda **_: 0, returncode=0, poll=lambda: None),
    )
    monkeypatch.setattr(sweep, "wait_health", lambda *_a: None)
    monkeypatch.setattr(sweep, "stop_group", lambda *_a: None)
    monkeypatch.setattr(sweep, "_worker", lambda *_a: workers.append((_a[3], _a[4])))
    monkeypatch.setattr(sweep, "controls_pass", lambda *_a: True)
    result = sweep.run_model(tmp_path, tmp_path, "Qwen/Qwen3.5-2B", sweep.time.monotonic() + 10)
    assert result["status"] == "complete"
    assert workers == [("controls", 3), ("packets", 216)]


def test_safe_attention_opt_in_only(tmp_path):
    ordinary = sweep.server_command("Qwen/Qwen3.5-2B", tmp_path)
    safe = sweep.server_command("Qwen/Qwen3.5-2B", tmp_path, safe_attention=True)
    assert safe[: len(ordinary)] == ordinary
    assert "--attention-backend" not in ordinary
    assert safe[safe.index("--attention-backend") + 1] == "TRITON_ATTN"
    assert safe[safe.index("--mm-encoder-attn-backend") + 1] == "TORCH_SDPA"
    assert json.loads(safe[safe.index("--kernel-config") + 1]) == {"enable_flashinfer_autotune": False}


def test_diagnostic_health_requires_identity_and_schema(tmp_path):
    model = "Qwen/Qwen3.5-0.8B"
    (tmp_path / "status.json").write_text('{"status":"complete"}')
    rows = []
    for index, choice in enumerate(("unresolved", "split", "unresolved")):
        rows.append({"id": f"c{index}", "event": "attempt_started"})
        rows.append(
            {
                "id": f"c{index}",
                "event": "attempt_completed",
                "status": "ok",
                "response": {
                    "model": model,
                    "model_revision": sweep.MODELS[model],
                    "backend": "stock-vllm-json",
                    "answers": {"q0": {"type": "choice", "choice": choice}},
                },
            }
        )
    path = tmp_path / "attempts.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows))
    assert not sweep.controls_pass(tmp_path)
    assert sweep.controls_healthy(tmp_path, model)
    rows[1]["response"]["model"] = "wrong-model"
    path.write_text("\n".join(json.dumps(row) for row in rows))
    assert not sweep.controls_healthy(tmp_path, model)
    rows[1]["response"]["model"] = model
    rows[1]["response"]["answers"]["q0"]["choice"] = "unknown"
    path.write_text("\n".join(json.dumps(row) for row in rows))
    assert not sweep.controls_healthy(tmp_path, model)


@pytest.mark.parametrize(("healthy", "admitted"), [(True, True), (False, False)])
def test_semantic_diagnostic_gate_cannot_bypass_transport(monkeypatch, tmp_path, healthy, admitted):
    workers = []
    monkeypatch.setattr(sweep.subprocess, "run", lambda *_a, **_k: None)
    monkeypatch.setattr(
        sweep.subprocess,
        "Popen",
        lambda *_a, **_k: SimpleNamespace(pid=1, wait=lambda **_: 0, returncode=0, poll=lambda: None),
    )
    monkeypatch.setattr(sweep, "wait_health", lambda *_a: None)
    monkeypatch.setattr(sweep, "stop_group", lambda *_a: None)
    monkeypatch.setattr(sweep, "_worker", lambda *_a: workers.append(_a[3]))
    monkeypatch.setattr(sweep, "controls_pass", lambda *_a: False)
    monkeypatch.setattr(sweep, "controls_healthy", lambda *_a: healthy)
    result = sweep.run_model(
        tmp_path, tmp_path, "Qwen/Qwen3.5-2B", sweep.time.monotonic() + 10, allow_semantic_control_failure=True
    )
    assert not result["semantic_passed"]
    assert (result["status"] == "complete") == admitted
    assert ("packets" in workers) == admitted
    if admitted:
        assert result["evaluation_admission"] == "diagnostic-semantic-control-failure"


