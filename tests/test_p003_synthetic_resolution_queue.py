# ruff: noqa: PT012, EM101, TRY003
"""Mock-only checks of queue arguments, breadth scheduling, restoration and transport bounds."""

import random
from pathlib import Path
from types import SimpleNamespace

import pytest
from bench import p003_synthetic_resolution_queue as queue
from bench.silver import sha


def test_exact_arguments_and_controls_refused(tmp_path: Path) -> None:
    rows = queue.queue_plan(tmp_path, tmp_path, tmp_path, tmp_path)
    assert len(rows) == 25
    assert all("arguments" in row and "args" not in row for row in rows)
    assert {queue.validate_arguments(row) for row in rows} == {256, 400, 500, 768, 1024}
    bad = {**rows[0], "arguments": [*rows[0]["arguments"], "--run-hosted", "yes"]}
    with pytest.raises(ValueError, match=r"required|admitted"):
        queue.validate_arguments(bad)
    bad = {**rows[0], "arguments": [*rows[0]["arguments"][:-1], "128"]}
    with pytest.raises(ValueError, match=r"required|admitted"):
        queue.validate_arguments(bad)


def test_isolated_commands_seeded_breadth_heavy_limit_and_restoration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    rows = queue.queue_plan(tmp_path, tmp_path, tmp_path, tmp_path)
    core = mock_core(tmp_path)
    monkeypatch.setattr(queue, "QUEUE_SHA256", sha(Path(core.__file__).read_bytes()))
    original = {
        name: getattr(core, name)
        for name in ("MODULES", "QUESTION_SCOPES", "command_for", "validate_plan", "next_launch_index")
    }
    with pytest.raises(RuntimeError, match="owned test"), queue.adapt(core, tmp_path, {}):
        ordered = core.validate_plan(rows, queue.SEED)
        assert ordered == core.validate_plan(rows, queue.SEED)
        assert [queue.validate_arguments(row) for row in ordered] == sorted(
            queue.validate_arguments(row) for row in rows
        )
        command = core.command_for(ordered[0], None, tmp_path / "future" / ordered[0]["name"])
        assert "--transport-concurrency" not in command
        assert "--run-hosted" in command
        assert command[2] == "bench.p003_synthetic_resolution_run"
        assert core.next_launch_index(ordered, ordered[:3], 3) is None
        assert core.next_launch_index(ordered, ordered[:2], 3) == 0
        assert core.QUESTION_SCOPES[queue.KIND] == queue.SCOPE
        raise RuntimeError("owned test")
    for name, value in original.items():
        assert getattr(core, name) is value


def test_cutoff_changes_refused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    core = mock_core(tmp_path)
    monkeypatch.setattr(queue, "QUEUE_SHA256", sha(Path(core.__file__).read_bytes()))
    monkeypatch.setattr(core, "P003_PAID_CUTOFF", queue.CUTOFF + 1)
    with pytest.raises(ValueError, match="exact cutoff"), queue.adapt(core, tmp_path, {}):
        raise AssertionError("not admitted")


def mock_core(tmp_path: Path) -> SimpleNamespace:
    script = tmp_path / "owned-core.py"
    script.write_text("# mocked queue contract\n")

    def validate(rows: list, seed: int) -> list:
        result = list(rows)
        random.Random(seed).shuffle(result)
        return result

    def next_index(rows: list, active: list, limit: int) -> int | None:
        assert all(row["kind"] == "synthetic_relations" for row in [*rows, *active])
        return 0 if rows and len(active) < min(3, limit) else None

    return SimpleNamespace(
        __file__=str(script),
        MAX_CONCURRENT=3,
        P003_PAID_CUTOFF=queue.CUTOFF,
        MODULES={},
        QUESTION_SCOPES={},
        command_for=None,
        validate_plan=validate,
        next_launch_index=next_index,
    )
