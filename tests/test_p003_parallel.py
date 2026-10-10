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


def test_arm_duration_is_explicit_and_bounded():
    for value in (True, 0, 29, 10801, 2400.0, "2400"):
        with pytest.raises(ValueError, match="duration"):
            parallel.validate_plan([{"name": "a", "arguments": [], "max_wall_seconds": value}], 1)
    arm = {"name": "a", "arguments": [], "max_wall_seconds": 7200}
    assert parallel.validate_plan([arm], 1) == [arm]


@pytest.mark.parametrize("limit", [3, 6])
def test_queue_cpu_children_overlap_freeze_and_no_overwrite(tmp_path, monkeypatch, limit):
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
    count = limit + 1
    plan = [{"name": f"a{i}", "kind": "pipeline" if i < 3 else "gate", "arguments": []} for i in range(count)]
    result = parallel.run_queue(plan, tmp_path / "manifest.json", directory,
                                seed=1, cutoff=time.time() + 1000, root=root, max_parallel_arms=limit)
    assert result["max_observed_concurrent_arms"] == limit
    assert len(result["arms"]) == count
    assert all(arm["status"] == "completed" for arm in result["arms"])
    assert all(arm["max_wall_seconds"] == 2400 for arm in result["arms"])
    assert result["policy"]["heartbeat_seconds"] == 5.0
    assert all("--workers" not in command for command in commands)
    assert all(command[command.index("--transport-concurrency") + 1] == "3" for command in commands)
    assert len(result["frozen_order"]) == count
    assert result["resources"]["cpu_seconds_sampled"] > 0
    assert result["resources"]["peak_aggregate_rss_bytes_sampled"] > 0
    assert result["resources"]["samples"] >= 4
    assert result["aggregate_rates"]["completed_page_runs_known"] == 3
    assert result["aggregate_rates"]["completed_page_runs_per_minute"] > 0
    assert len(list((directory / "trusted-code").glob("*.json"))) == count
    assert json.loads((directory / "status.json").read_text())["frozen_order"] == result["frozen_order"]
    with pytest.raises(FileExistsError):
        parallel.run_queue(plan, tmp_path / "manifest.json", directory, seed=1)


def test_wide_queue_skips_cpu_heavy_head_without_changing_frozen_priority():
    ordered = [{"name": "heavy", "kind": "candidate"}, {"name": "light", "kind": "topology"}]
    active = [{"kind": "pipeline"}, {"kind": "candidate"}, {"kind": "pipeline"}]
    assert parallel.next_launch_index(ordered, active, 6) == 1
    assert parallel.next_launch_index(ordered, active, 3) is None
    assert parallel.next_launch_index(ordered[:1], active, 6) is None
    assert ordered[0]["name"] == "heavy"


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
        if kind == "micro":
            continue
        status = {"kind": kind, "wall_seconds": 10}
        report = {"results": [{"status": "ok", "ranking_status": "not_applicable", "repair_status": "completed",
                               "gate_status": "complete", "topology_status": "completed",
                               "decision_status": "evaluated", "selection_status": "selected"}],
                  "incremental_ranking": {"returned_calls": 1}, "incremental_repair": {"returned_calls": 2},
                  "incremental_gate": {"returned_calls": 3}, "incremental_ownership": {"returned_calls": 4},
                  "incremental_admission": {"returned_calls": 5}, "incremental_selection": {"returned_calls": 6}}
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


def test_explicit_per_arm_manifest_keeps_corpus_identity_and_path_guard(tmp_path):
    declared = tmp_path / "natural64.json"
    arm = {"name": "wide", "manifest": str(declared), "arguments": ["--preset", "ordinal"]}
    validated = parallel.validate_plan([arm], 1)[0]
    command = parallel.command_for(validated, tmp_path / "natural16.json", tmp_path / "wide")
    assert command[command.index("--manifest") + 1] == str(declared)
    with pytest.raises(ValueError, match="Only pipeline"):
        parallel.validate_plan([{**arm, "kind": "gate"}], 1)


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


def test_micro_relationship_metrics_never_become_page_rates():
    status = {"kind": "micro", "wall_seconds": 20}
    report = {"results": [
        {"status": "valid_nonabstaining", "page_id": "p0"},
        {"status": "valid_abstention", "page_id": "p0"},
        {"status": "transport_error", "page_id": "p1"},
        {"status": "not_attempted", "page_id": "p2"},
    ], "attempted_question_count": 3, "charges": {"effective_usd": None}}
    parallel.report_counts(status, report)
    assert status["valid_returned_questions"] == 2
    assert status["nonabstaining_questions"] == 1
    assert status["attempted_questions"] == 3
    assert status["contended_valid_questions_per_minute"] == 6
    assert status["pages_per_minute"] is None
    assert "completed_pages" not in status
    summary = parallel.summarize_rates([status], 40, [])
    assert summary["completed_page_runs_known"] == 0
    assert summary["by_kind"]["micro"]["valid_returned_questions_per_minute"] == 3
    assert summary["by_kind"]["micro"]["pages_per_dollar"] is None
    incomplete = parallel.summarize_rates([status, {"kind": "micro"}], 40, [])
    assert incomplete["by_kind"]["micro"]["valid_returned_questions_per_minute"] is None


@pytest.mark.parametrize("flag", [
    "--input", "--pool", "--pool-trusted-code", "--selector-trusted-code", "--input-trusted-code",
])
def test_auxiliary_paths_guarded_before_admission(tmp_path, monkeypatch, flag):
    seen = []
    def guarded(path):
        seen.append(path)
        return tmp_path / "approved"
    monkeypatch.setattr(parallel, "guard_path", guarded)
    for argument in ([flag, "source"], [flag + "=source"]):
        out = parallel.validate_plan([{"name": "probe", "kind": "admission", "arguments": argument}], 1)
        assert str(tmp_path / "approved") in " ".join(out[0]["arguments"])
    assert seen == [Path("source"), Path("source")]


def test_auxiliary_replay_obeys_cpu_capacity():
    active = [{"kind": "admission"}, {"kind": "diagram"}, {"kind": "candidate"}]
    ordered = [{"kind": "diagram"}, {"kind": "admission"}, {"kind": "micro"}]
    assert parallel.next_launch_index(ordered, active, 6) == 2
