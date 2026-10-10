"""Synthetic queue contracts: CLI mocks and local counters only, without a client."""
import sys
from pathlib import Path

import pytest
from bench import p003_parallel as parallel
from bench import p003_synthetic_relations_run as runner

# ruff: noqa: ANN001, ANN201, ANN202 - local mock fixtures.


def test_synthetic_command_matches_actual_cli(tmp_path, monkeypatch):
    arguments = ["--input", "input", "--trusted-code=trust.json", "--model", runner.DECISION_MODELS[0],
                 "--evidence", "text_geometry", "--image-edge", "0", "--viewport", "crop"]
    arm = parallel.validate_plan([{"name": "synthetic", "kind": "synthetic_relations",
                                  "arguments": arguments}], 1)[0]
    command = parallel.command_for(arm, None, tmp_path / "output")
    assert command[2] == "bench.p003_synthetic_relations_run"
    assert "--manifest" not in command
    assert "--workers" not in command
    seen = []
    monkeypatch.setattr(sys, "argv", [command[2], *command[3:]])
    monkeypatch.setattr(runner, "run", lambda *args, **kwargs: seen.append((args, kwargs)) or {})
    runner.main()
    args, kwargs = seen[0]
    assert all(isinstance(value, Path) and value.is_absolute() for value in args)
    assert kwargs["transport_concurrency"] == 3
    assert kwargs["run_hosted"] is True
    assert kwargs["viewport"] == "crop"
    assert kwargs["mode"] == "text_geometry"


@pytest.mark.parametrize("flag", ["--input", "--trusted-code"])
@pytest.mark.parametrize("equals", [False, True])
def test_synthetic_sources_guarded(flag, equals, tmp_path, monkeypatch):
    seen = []
    def guard(path):
        seen.append(path)
        return tmp_path / "approved"
    monkeypatch.setattr(parallel, "guard_path", guard)
    arguments = [flag + "=source"] if equals else [flag, "source"]
    result = parallel.validate_plan([{"name": "synthetic", "kind": "synthetic_relations",
                                      "arguments": arguments}], 1)
    assert seen == [Path("source")]
    assert str(tmp_path / "approved") in " ".join(result[0]["arguments"])


def test_synthetic_question_counts_and_accounting_cannot_be_pages():
    charges = {"effective_usd": 0.25, "reserved_unresolved_usd": 0.1}
    rows = [{"kind": "cell", "status": "valid_nonabstaining"},
            {"kind": "row", "status": "valid_abstention"},
            {"kind": "wrap", "status": "malformed_response"},
            {"kind": "wrap", "status": "transport_error"},
            {"kind": "cell", "status": "not_attempted"},
            {"kind": "row", "status": "capacity_refused"}]
    status = {"kind": "synthetic_relations", "wall_seconds": 30}
    parallel.report_counts(status, {"results": rows, "attempted_question_count": 4, "charges": charges})
    assert status["intended_questions"] == 6
    assert status["attempted_questions"] == 4
    assert status["valid_returned_questions"] == 2
    assert status["nonabstaining_questions"] == 1
    assert status["question_kind_counts"] == {"cell": 2, "row": 2, "wrap": 2}
    assert status["incremental_accounting"] is charges
    assert status["nonabstaining_questions_per_dollar"] == 4
    assert status["contended_attempted_questions_per_minute"] == 8
    assert status["pages_per_minute"] is None
    assert status["full_pipeline_rate"] is None
    assert status["correctness_measured"] is False
    assert "completed_pages" not in status
    summary = parallel.summarize_rates([status], 60, [])
    counts = summary["by_kind"]["synthetic_relations"]
    assert counts["valid_returned_questions_per_minute"] == 2
    assert counts["attempted_questions_per_minute"] == 4
    assert counts["nonabstaining_questions_per_minute"] == 1
    assert summary["completed_page_runs_known"] == 0
    assert counts["pages_per_dollar"] is None
    assert counts["correctness_measured"] is False
    assert parallel.summarize_rates([status], 60, ["pending"])["by_kind"]["synthetic_relations"][
        "attempted_questions_per_minute"] is None
    parallel.report_counts(status, {"results": rows, "attempted_question_count": 4,
                                    "charges": {"effective_usd": None}})
    assert status["nonabstaining_questions_per_dollar"] is None


def test_synthetic_render_replay_respects_cpu_lane():
    active = [{"kind": "pipeline"}, {"kind": "header"}, {"kind": "diagram"}]
    ordered = [{"kind": "synthetic_relations"}, {"kind": "micro"}]
    assert parallel.next_launch_index(ordered, active, 6) == 1
    assert parallel.next_launch_index(ordered, active[:2], 6) == 0
