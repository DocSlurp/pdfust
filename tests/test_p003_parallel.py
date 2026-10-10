"""CPU subprocesses and mocked plans only; no credentials or hosted requests."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from bench import p003_parallel as parallel
from bench import p003_run

# ruff: noqa: ANN001, ANN201, ANN202, ANN003 - short mock fixtures and observed counters.


def test_seeded_plan_is_copied_and_control_overrides_rejected():
    plan = [{"name": str(i), "arguments": ["--model", "mock"]} for i in range(8)]
    assert parallel.validate_plan([{
        "name": "a", "arguments": ["--gate-provider", "openrouter"],
    }], 1)[0]["name"] == "a"
    out = parallel.validate_plan(plan, 13)
    assert out == parallel.validate_plan(plan, 13)
    assert out != parallel.validate_plan(plan, 14)
    out[0]["arguments"].append("anything")
    assert all(len(arm["arguments"]) == 2 for arm in plan)
    for arguments in (["--workers=4"], ["--gate-provider", "vercel"], ["--output=x"],
                      ["--generation-provider", "vercel"], ["--transport-concurrency", "1"]):
        with pytest.raises(ValueError, match=r"Queue owns|forbidden"):
            parallel.validate_plan([{"name": "a", "arguments": arguments}], 1)


def test_queue_cpu_children_overlap_freeze_and_no_overwrite(tmp_path, monkeypatch):
    original_popen = subprocess.Popen
    commands = []

    def cpu_popen(command, **kwargs):
        commands.append(command)
        output = command[command.index("--output") + 1]
        code = (
            "import pathlib,json,time; "
            f"p=pathlib.Path({output!r}); p.mkdir(); "
            "end=time.monotonic()+0.35; "
            "exec('while time.monotonic()<end: sum(range(2000))'); "
            "(p/'report.json').write_text(json.dumps({'results':[{'status':'ok'}]}))"
        )
        return original_popen([sys.executable, "-c", code], **kwargs)

    monkeypatch.setattr(parallel.subprocess, "Popen", cpu_popen)
    monkeypatch.setattr(parallel.subprocess, "check_output", lambda *_a, **_k: "bench/p003_parallel.py\n")
    directory = tmp_path / "queue"
    root = Path(parallel.__file__).resolve().parent.parent
    plan = [{"name": f"a{i}", "arguments": []} for i in range(4)]
    result = parallel.run_queue(plan, tmp_path / "manifest.json", directory,
                                seed=1, cutoff=time.time() + 1000, root=root)
    assert result["max_observed_concurrent_arms"] == 3
    assert len(result["arms"]) == 4
    assert all(arm["status"] == "completed" for arm in result["arms"])
    assert all("--workers" not in command for command in commands)
    assert all(command[command.index("--transport-concurrency") + 1] == "3" for command in commands)
    assert len(result["frozen_order"]) == 4
    assert result["resources"]["cpu_seconds_sampled"] > 0
    assert result["resources"]["peak_aggregate_rss_bytes_sampled"] > 0
    assert result["resources"]["samples"] >= 4
    assert result["aggregate_rates"]["completed_page_runs_known"] == 4
    assert result["aggregate_rates"]["completed_page_runs_per_minute"] > 0
    assert len(list((directory / "trusted-code").glob("*.json"))) == 4
    assert json.loads((directory / "status.json").read_text())["frozen_order"] == result["frozen_order"]
    with pytest.raises(FileExistsError):
        parallel.run_queue(plan, tmp_path / "manifest.json", directory, seed=1)


def test_cutoff_never_launches_and_records_not_started(tmp_path, monkeypatch):
    monkeypatch.setattr(parallel.subprocess, "Popen", lambda *_a, **_k: pytest.fail("must not launch"))
    result = parallel.run_queue([{"name": "a", "arguments": []}], tmp_path / "manifest",
                                tmp_path / "queue", seed=1, cutoff=time.time() + 100)
    assert result["not_started"] == ["a"]
    assert result["aggregate_rates"]["completed_page_runs_per_minute"] is None


def test_stop_group_reaps_cpu_child():
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"], start_new_session=True)
    parallel.stop_group(process)
    assert process.poll() is not None


def test_mixed_kinds_fixed_commands_and_separate_rate_scopes(tmp_path):
    for kind, module in parallel.MODULES.items():
        arm = {"name": kind, "kind": kind, "arguments": ["--model", "mock"]}
        command = parallel.command_for(arm, tmp_path / "manifest", tmp_path / kind)
        assert command[2] == module
        assert ("--manifest" in command) is (kind == "pipeline")
        assert "--workers" not in command
        assert ("--run-hosted" in command) is (kind != "pipeline")
        assert command[command.index("--transport-concurrency") + 1] == "3"
    with pytest.raises(ValueError, match="manifest"):
        parallel.command_for({"name": "a", "arguments": []}, None, tmp_path / "a")
    with pytest.raises(ValueError, match="kind"):
        parallel.validate_plan([{"name": "a", "kind": "arbitrary", "arguments": []}], 1)
    assert parallel.validate_plan([{"name": "a", "kind": "candidate", "arguments": [
        "--baseline", str(tmp_path / "base"), "--trusted-code=" + str(tmp_path / "trust.json"),
    ]}], 1)
    statuses = []
    for kind in parallel.MODULES:
        status = {"kind": kind, "wall_seconds": 10}
        report = {"results": [{"status": "ok", "ranking_status": "not_applicable", "repair_status": "completed",
                               "gate_status": "complete", "topology_status": "completed"}],
                  "incremental_ranking": {"returned_calls": 1}, "incremental_repair": {"returned_calls": 2},
                  "incremental_gate": {"returned_calls": 3}, "incremental_ownership": {"returned_calls": 4}}
        parallel.report_counts(status, report)
        assert ("contended_pages_per_minute" in status) is (kind == "pipeline")
        statuses.append(status)
    summary = parallel.summarize_rates(statuses, 20, [])
    assert summary["completed_page_runs_known"] == 1
    assert summary["by_kind"]["candidate"]["scope"] == "incremental retained artifacts"
    assert summary["by_kind"]["boundary"]["completed_page_runs_known"] == 1
    assert statuses[1]["incremental_status_counts"] == {"not_applicable": 1}


def test_incremental_declared_paths_use_guard_before_launch(tmp_path, monkeypatch):
    seen = []

    def guarded(path):
        seen.append(str(path))
        if str(path) == "blocked-fixture":
            message = "Mock protected path refusal"
            raise ValueError(message)
        return tmp_path / path.name

    monkeypatch.setattr(parallel, "guard_path", guarded)
    plan = [{"name": "a", "kind": "candidate", "arguments": ["--baseline", "base", "--trusted-code=trust"]}]
    frozen = parallel.validate_plan(plan, 1)
    assert seen == ["base", "trust"]
    assert frozen[0]["arguments"] == ["--baseline", str(tmp_path / "base"), "--trusted-code=" + str(tmp_path / "trust")]
    assert plan[0]["arguments"][1] == "base"
    with pytest.raises(ValueError, match="Mock protected"):
        parallel.validate_plan([{"name": "a", "kind": "boundary", "arguments": ["--baseline=blocked-fixture"]}], 1)


def test_pipeline_queue_command_passes_real_cli_parser(tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(p003_run.pipeline_run, "run", lambda *args: captured.append(args) or {})
    command = parallel.command_for(
        {"name": "integration", "arguments": ["--preset", "gated_ordinal"]},
        tmp_path / "manifest.json", tmp_path / "integration",
    )
    monkeypatch.setattr(sys, "argv", [command[2], *command[3:]])
    p003_run.main()
    assert captured[0][2]["workers"] == 1
    assert captured[0][2]["transport_concurrency"] == 3


def test_union_cli_activates_cpu_detector_and_declared_overlap_policy(tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(p003_run.pipeline_run, "run", lambda *args: captured.append(args) or {})
    command = parallel.command_for(
        {"name": "union", "arguments": ["--preset", "p003_regions", "--image-edge", "1024",
         "--region-proposal-arm", "yolo_fixed2", "--region-conflict-policy", "small_area_then_probability"]},
        tmp_path / "manifest.json", tmp_path / "union",
    )
    monkeypatch.setattr(sys, "argv", [command[2], *command[3:]])
    p003_run.main()
    config = captured[0][2]
    assert config["layout_detector"] == "yolo"
    assert config["region_proposal_arm"] == "yolo_fixed2"
    assert config["conflict_policy"] == "small_area_then_probability"
    assert config["gate_enabled"] is True
    assert config["workers"] == 1
