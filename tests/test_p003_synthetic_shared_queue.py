"""Source-only plan preparation and own-process queue adaptation, never hosted calls."""

# ruff: noqa: PT012, EM101, TRY003
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from bench import p003_synthetic_relations_multi_run as runner
from bench import p003_synthetic_shared_queue as driver
from bench.silver import write_json

MAIN = Path("/home/dan/code/oss/pylopdf")
ARTIFACTS = MAIN / "bench/results/pdf-master-artifacts/pipeline-p003"
POOL = ARTIFACTS / "synthetic-micro-relations-v2"
SOURCE_MAP = ARTIFACTS / "trusted-code/synthetic-micro-relations-v2.json"


@pytest.fixture
def core() -> ModuleType:
    spec = importlib.util.spec_from_file_location("owned_test_current_queue", MAIN / "bench/p003_parallel.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_plan_inventory_and_actual_cli_parser(
    core: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plan = driver.generate_plan(POOL, SOURCE_MAP)
    assert len(plan) == 56
    assert len({a["name"] for a in plan}) == 56
    configs = [driver.validate_arguments(a, POOL, SOURCE_MAP) for a in plan]
    assert len({(c["model"], c["question_group_size"], c["mode"]) for c in configs}) == 56
    authority = driver.runtime_authority(MAIN)
    observed = []
    with driver.adapt(core, MAIN, authority):
        order = core.validate_plan(plan, driver.SEED)
        assert order == core.validate_plan(plan, driver.SEED)
        assert order != plan
        for arm in order:
            command = core.command_for(arm, None, tmp_path / "owned-unused" / arm["name"])
            assert command[2] == "bench.p003_synthetic_relations_multi_run"
            assert command.count("--run-hosted") == 1
            assert command.count("--transport-concurrency") == 1
            monkeypatch.setattr(runner, "run", lambda *_, **kwargs: observed.append(kwargs) or {})
            monkeypatch.setattr("sys.argv", ["runner", *command[3:]])
            runner.main()
    assert len(observed) == 56
    assert all(v["run_hosted"] is True for v in observed)


def test_adapter_restores_globals_and_classifies_heavy(core: ModuleType) -> None:
    originals = {
        name: getattr(core, name) for name in ("MODULES", "command_for", "next_launch_index", "QUESTION_SCOPES")
    }
    authority = driver.runtime_authority(MAIN)
    plan = driver.generate_plan(POOL, SOURCE_MAP)
    with pytest.raises(RuntimeError, match="Owned cleanup test"), driver.adapt(core, MAIN, authority):
        assert core.next_launch_index(plan, [{"kind": driver.KIND}] * 3, 6) is None
        assert core.next_launch_index(plan, [{"kind": driver.KIND}] * 2, 6) == 0
        raise RuntimeError("Owned cleanup test")
    assert all(getattr(core, k) is v for k, v in originals.items())


def test_prelaunch_exact25_map_and_shared_counts(core: ModuleType, tmp_path: Path) -> None:
    authority = driver.runtime_authority(MAIN)
    arm = driver.generate_plan(POOL, SOURCE_MAP)[0]
    (tmp_path / "trusted-code").mkdir()
    path = tmp_path / "trusted-code" / (arm["name"] + ".json")
    write_json(path, {"unapproved_extra": "bad"})
    with driver.adapt(core, MAIN, authority):
        core.command_for(arm, None, tmp_path / arm["name"])
        assert json.loads(path.read_bytes()) == authority
        assert len(authority) == 25
        status = {"kind": driver.KIND, "wall_seconds": 2.0}
        report = {
            "results": [{"kind": "cell", "status": "valid_abstention"}] * 24,
            "attempted_question_count": 24,
            "charges": {"effective_usd": 0.06},
            "group_count": 6,
            "attempted_group_count": 6,
            "group_status_counts": {"valid": 6},
        }
        core.report_counts(status, report)
        assert status["attempted_shared_requests"] == 6
        assert status["valid_returned_questions"] == 24
        assert status["pages_per_minute"] is None
        summary = core.summarize_rates([status], 2.0, [])
        assert summary["by_kind"][driver.KIND]["attempted_shared_requests_known"] == 6
        assert (
            core.summarize_rates([status], 2.0, ["not-started"])["by_kind"][driver.KIND][
                "attempted_shared_requests_per_minute"
            ]
            is None
        )


def test_queue_digest_and_injected_arguments_fail(core: ModuleType) -> None:
    authority = driver.runtime_authority(MAIN)
    core.__file__ = __file__
    with pytest.raises(ValueError, match="queue function bytes"), driver.adapt(core, MAIN, authority):
        pytest.fail("Unexpected queue must not execute")
    arm = driver.generate_plan(POOL, SOURCE_MAP)[0]
    arm["arguments"][0] = "--output"
    with pytest.raises(ValueError, match="flags"):
        driver.validate_arguments(arm, POOL, SOURCE_MAP)


def test_dirty_runtime_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "bench").mkdir()
    originals = {name: (MAIN / "bench" / name).read_bytes() for name in (*runner.CODE_FILES, "p003_parallel.py")}
    for name, raw in originals.items():
        (tmp_path / "bench" / name).write_bytes(raw)
    monkeypatch.setattr(driver.subprocess, "check_output", lambda argv, **_: originals[argv[-1].split("bench/")[1]])
    assert len(driver.runtime_authority(tmp_path)) == 25
    (tmp_path / "bench" / runner.CODE_FILES[0]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="Dirty runtime"):
        driver.runtime_authority(tmp_path)


def test_prepare_and_mock_launch_replay_before_queue(
    core: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared = tmp_path / "prepared"
    receipt = driver.prepare(POOL, SOURCE_MAP, prepared, root=MAIN, core=core)
    assert receipt["arm_count"] == 56
    assert sum(len(a["requests"]) for a in receipt["prepared_arms"]) == 252
    assert receipt["hosted_calls"] == 0
    assert receipt["gold_read"] is False
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(core, "run_queue", lambda *_, **kwargs: calls.append(kwargs) or {"mocked": True})
    assert driver.launch(prepared, tmp_path / "not-launched", root=MAIN, core=core) == {"mocked": True}
    assert calls[0]["max_parallel_arms"] == 6
    assert calls[0]["cutoff"] == 1791684720.0
    assert not (tmp_path / "not-launched").exists()
    packet = prepared / receipt["prepared_arms"][0]["requests"][0]["path"]
    packet.write_bytes(b"changed")
    with pytest.raises(ValueError, match="wire replay"):
        driver.launch(prepared, tmp_path / "never-launched", root=MAIN, core=core)
    assert len(calls) == 1
