"""Coordinator-run pinned local vLLM sweep; no provider or lifecycle credentials.

Workspace contains bench/, packets/manifest.json and controls/manifest.json.
Controls are ordered join, split, unresolved. Results are exclusive-created under
workspace/vllm-sweep. Server resources are measured separately from HTTP worker
CPU/RSS; device-wide GPU samples do not measure server allocator reservations.
"""

# ruff: noqa: ANN401, PLR0913, S603, PLR0917, PLR2004, TRY301, C901, PLR0911 - explicit coordinator subprocesses and injectable mocks.
from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import json
import math
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from bench.remote_vllm import MODELS

HEALTH_SECONDS = 180
FAILED_MODEL_LIMIT = 3
SNAPSHOT_CODE = """
import sys
from huggingface_hub import snapshot_download
snapshot_download(sys.argv[1], revision=sys.argv[2], local_dir=sys.argv[3], token=False,
 allow_patterns=['*.json','*.safetensors','*.py','*.jinja','tokenizer.model','*.tiktoken',
                 'vocab.txt','merges.txt','README.md','LICENSE*'])
"""


def server_command(model: str, snapshot: Path, *, safe_attention: bool = False) -> list[str]:
    """Build the admitted bounded single-image localhost server command."""
    if model not in MODELS:
        message = "Model is outside the explicit admitted inventory"
        raise ValueError(message)
    command = [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        str(snapshot),
        "--served-model-name",
        model,
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--dtype",
        "bfloat16",
        "--max-model-len",
        "8192",
        "--max-num-seqs",
        "8",
        "--gpu-memory-utilization",
        "0.65",
        "--enforce-eager",
        "--no-enable-prefix-caching",
        "--mm-processor-cache-gb",
        "0",
        "--limit-mm-per-prompt",
        '{"image":1,"video":0}',
    ]
    if model.startswith("HuggingFaceTB/SmolVLM2-"):
        command.extend(["--chat-template-content-format", "openai"])
    if model == "LiquidAI/LFM2-VL-1.6B":
        # The pinned publisher stores its template separately from tokenizer_config.
        command.extend(
            ["--chat-template", str(snapshot / "chat_template.jinja"), "--chat-template-content-format", "openai"]
        )
    if model == "openbmb/MiniCPM-V-4":
        command.append("--trust-remote-code")
    if safe_attention:
        command.extend(
            [
                "--attention-backend",
                "TRITON_ATTN",
                "--mm-encoder-attn-backend",
                "TORCH_SDPA",
                "--kernel-config",
                '{"enable_flashinfer_autotune":false}',
            ]
        )
    return command


def controls_pass(directory: Path) -> bool:
    """Require all three ordered transport controls exactly once and correct."""
    status = json.loads((directory / "status.json").read_bytes())
    if status.get("status") != "complete":
        return False
    rows = [json.loads(line) for line in (directory / "attempts.jsonl").read_text().splitlines()]
    answers = [row for row in rows if row.get("event") in {"attempt_completed", "attempt_finished"}]
    # Worker versions historically retained event=attempt_started on completion.
    if not answers:
        answers = [row for row in rows if "status" in row]
    if len(answers) != 3:
        return False
    for row, expected in zip(answers, ("join", "split", "unresolved"), strict=True):
        response = row.get("response", {})
        if row.get("status") != "ok" or len(response.get("answers", {})) != 1:
            return False
        if next(iter(response["answers"].values())).get("choice") != expected:
            return False
    return True


def controls_healthy(directory: Path, model: str) -> bool:
    """Verify all three schema-valid model-identified replies for a diagnostic gate."""
    if model not in MODELS:
        return False
    status = json.loads((directory / "status.json").read_bytes())
    if status.get("status") != "complete":
        return False
    rows = [json.loads(line) for line in (directory / "attempts.jsonl").read_text().splitlines()]
    completed = [row for row in rows if row.get("event") == "attempt_completed"]
    started = [row for row in rows if row.get("event") == "attempt_started"]
    if len(completed) != 3 or len(started) != 3:
        return False
    identities = [row.get("id") for row in completed]
    if len(set(identities)) != 3 or identities != [row.get("id") for row in started]:
        return False
    for row in completed:
        response = row.get("response", {})
        if (
            row.get("status") != "ok"
            or response.get("model") != model
            or response.get("model_revision") != MODELS[model]
            or response.get("backend") != "stock-vllm-json"
        ):
            return False
        answers = response.get("answers")
        if not isinstance(answers, dict) or set(answers) != {"q0"}:
            return False
        answer = answers["q0"]
        if (
            not isinstance(answer, dict)
            or answer.get("type") != "choice"
            or answer.get("choice") not in ("join", "split", "unresolved")
            or "confidence" in answer
            or "probabilities" in answer
        ):
            return False
    return True


def wait_health(server: Any, deadline: float) -> None:
    """Poll only localhost; refuse a failed server or bounded startup expiry."""
    limit = min(deadline, time.monotonic() + HEALTH_SECONDS)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < limit:
        if server.poll() is not None:
            message = "vLLM exited before health admission"
            raise RuntimeError(message)
        try:
            with opener.open(
                "http://127.0.0.1:8000/health", timeout=min(2, max(0.01, limit - time.monotonic()))
            ) as reply:
                if reply.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(min(1, max(0, limit - time.monotonic())))
    message = "vLLM health deadline exceeded"
    raise TimeoutError(message)


def stop_group(server: Any) -> None:
    """Terminate the owned session and verify its process group disappears."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(server.pid, sig)
        except ProcessLookupError:
            server.wait(timeout=2)
            return
        with contextlib.suppress(subprocess.TimeoutExpired):
            server.wait(timeout=5)
        until = time.monotonic() + 5
        while time.monotonic() < until:
            try:
                os.killpg(server.pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.1)
    message = "Owned vLLM process group remains; refusing to start another model"
    raise RuntimeError(message)


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        message = "Global sweep deadline exhausted"
        raise TimeoutError(message)
    return remaining


def _worker(workspace: Path, snapshot: Path, directory: Path, packets: str, limit: int, deadline: float) -> None:
    command = [
        sys.executable,
        "-m",
        "bench.remote_worker",
        "--adapter",
        "bench.remote_vllm",
        "--model-dir",
        str(snapshot),
        "--packets",
        str(workspace / packets / "manifest.json"),
        "--output",
        str(directory),
        "--limit",
        str(limit),
        "--deadline-seconds",
        str(_remaining(deadline)),
    ]
    with (directory.parent / f"{directory.name}.log").open("x") as log:
        worker = subprocess.Popen(command, cwd=workspace, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = worker.wait(timeout=_remaining(deadline))
            if code:
                raise subprocess.CalledProcessError(code, command)
        finally:
            stop_group(worker)


def run_model(
    workspace: Path,
    directory: Path,
    model: str,
    deadline: float,
    *,
    safe_attention: bool = False,
    allow_semantic_control_failure: bool = False,
) -> dict[str, Any]:
    """Run one staged model once; retain each phase and always stop its server."""
    snapshot = directory / "models" / model.split("/")[1]
    state: dict[str, Any] = {"model": model, "revision": MODELS[model], "status": "started"}
    state["safe_attention"] = safe_attention
    state["allow_semantic_control_failure"] = allow_semantic_control_failure
    state["runtime_treatment"] = (
        "triton-main/torch-sdpa-vision/no-flashinfer-autotune" if safe_attention else "original"
    )
    server = monitor = None
    log = monitor_log = None
    try:
        began = time.monotonic()
        with (directory / "download.log").open("x") as download_log:
            subprocess.run(
                [sys.executable, "-c", SNAPSHOT_CODE, model, MODELS[model], str(snapshot)],
                stdout=download_log,
                stderr=subprocess.STDOUT,
                timeout=_remaining(deadline),
                check=True,
            )
        state["download_seconds"] = time.monotonic() - began
        command = server_command(model, snapshot, safe_attention=safe_attention)
        state["server_command"] = command
        began = time.monotonic()
        log = (directory / "server.log").open("x")
        server = subprocess.Popen(command, cwd=workspace, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        state["server_pid"] = server.pid
        monitor_log = (directory / "monitor.log").open("x")
        monitor = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "bench.remote_monitor",
                "--pid",
                str(server.pid),
                "--output",
                str(directory / "server-resources.jsonl"),
                "--deadline-seconds",
                str(_remaining(deadline)),
            ],
            cwd=workspace,
            stdout=monitor_log,
            stderr=subprocess.STDOUT,
        )
        wait_health(server, deadline)
        state["startup_seconds"] = time.monotonic() - began
        if monitor.poll() is not None:
            message = "Server resource monitor exited before control admission"
            raise RuntimeError(message)
        _worker(workspace, snapshot, directory / "controls", "controls", 3, deadline)
        state["controls_passed"] = controls_pass(directory / "controls")
        state["semantic_passed"] = state["controls_passed"]
        state["evaluation_admission"] = "semantic-controls-passed" if state["semantic_passed"] else "not-admitted"
        if not state["semantic_passed"]:
            if not allow_semantic_control_failure:
                message = "Semantic controls failed; source packets were not attempted"
                raise RuntimeError(message)
            state["controls_schema_healthy"] = controls_healthy(directory / "controls", model)
            if not state["controls_schema_healthy"]:
                message = "Control transport/schema/model identity failed; diagnostic admission refused"
                raise RuntimeError(message)
            state["evaluation_admission"] = "diagnostic-semantic-control-failure"
        _worker(workspace, snapshot, directory / "worker", "packets", 216, deadline)
        state["status"] = "complete"
    except Exception as error:
        state.update(status="failed", error_type=type(error).__name__, error=str(error)[:4096])
    finally:
        try:
            if server is not None:
                stop_group(server)
            state["server_exit_verified"] = True
        except Exception as error:
            state.update(status="cleanup_failed", cleanup_error=str(error)[:4096], server_exit_verified=False)
        if monitor is not None:
            try:
                monitor.wait(timeout=3)
            except subprocess.TimeoutExpired:
                monitor.terminate()
                monitor.wait(timeout=3)
            state["monitor_exit_code"] = monitor.returncode
        if log is not None:
            log.close()
        if monitor_log is not None:
            monitor_log.close()
        (directory / "result.json").write_text(json.dumps(state, indent=2) + "\n")
    return state


def sweep(
    models: list[str],
    workspace: Path,
    deadline_seconds: float = 2700,
    *,
    safe_attention: bool = False,
    allow_semantic_control_failure: bool = False,
) -> Path:
    """Run explicit unique models serially within one finite global admission."""
    if not models or len(set(models)) != len(models) or any(model not in MODELS for model in models):
        message = "Select explicit unique admitted model IDs"
        raise ValueError(message)
    if not math.isfinite(deadline_seconds) or deadline_seconds <= 0:
        message = "Deadline must be positive and finite"
        raise ValueError(message)
    workspace = workspace.resolve(strict=True)
    for name in ("bench", "packets", "controls"):
        if not (workspace / name).is_dir():
            message = "Workspace requires bench, packets and controls directories"
            raise ValueError(message)
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 8000)) == 0:
            message = "Port8000 is already occupied; refusing to replace another server"
            raise RuntimeError(message)
    output = workspace / "vllm-sweep"
    output.mkdir(exist_ok=False)
    versions: dict[str, str | None] = {}
    for name in ("torch", "transformers", "vllm", "huggingface-hub", "psutil", "kernels"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    (output / "environment.json").write_text(
        json.dumps(
            {
                "versions": versions,
                "python": sys.version,
                "executable": sys.executable,
                "models": models,
                "safe_attention": safe_attention,
                "allow_semantic_control_failure": allow_semantic_control_failure,
                "deadline_seconds": deadline_seconds,
                "concurrency": "one server/model at a time",
                "resources": "server+recursive children sampled separately; HTTP worker process excludes server",
            },
            indent=2,
        )
        + "\n"
    )
    deadline = time.monotonic() + deadline_seconds
    failures = 0
    for index, model in enumerate(models):
        if time.monotonic() >= deadline:
            break
        directory = output / f"{index:02d}-{model.replace('/', '--')}"
        directory.mkdir()
        result = run_model(
            workspace,
            directory,
            model,
            deadline,
            safe_attention=safe_attention,
            allow_semantic_control_failure=allow_semantic_control_failure,
        )
        with (output / "results.jsonl").open("a") as stream:
            stream.write(json.dumps(result) + "\n")
        failures += result["status"] != "complete"
        if not result.get("server_exit_verified") or failures >= FAILED_MODEL_LIMIT:
            break
    return output


def main() -> None:
    """Run the coordinator-authorized remote sweep."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=list(MODELS), required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--deadline-seconds", type=float, default=2700)
    parser.add_argument("--safe-attention", action="store_true", help="Explicit Triton/SDPA/no-autotune treatment")
    parser.add_argument(
        "--allow-semantic-control-failure",
        action="store_true",
        help="Diagnostic admission only for three schema-valid identified control responses",
    )
    args = parser.parse_args()
    print(
        sweep(
            args.models,
            args.workspace,
            args.deadline_seconds,
            safe_attention=args.safe_attention,
            allow_semantic_control_failure=args.allow_semantic_control_failure,
        )
    )


if __name__ == "__main__":
    main()
