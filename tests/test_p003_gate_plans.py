import json
from pathlib import Path

import pytest
from bench.p003_gate_plans import plans, token_audit, validate_arm


def test_factorial_and_screen_use_actual_parser_without_output(tmp_path: Path) -> None:
    baseline, trust = tmp_path / "baseline", tmp_path / "trust.json"
    queues = plans(baseline, trust)
    assert {key: len(value) for key, value in queues.items()} == {
        "image-a": 36,
        "image-b": 36,
        "prompt-core": 20,
        "prompt-followup": 8,
    }
    arms = [arm for queue in queues.values() for arm in queue]
    assert len({arm["name"] for arm in arms}) == len(arms)
    assert not list(tmp_path.iterdir())
    image = queues["image-a"] + queues["image-b"]
    assert (
        len(
            {
                (
                    validate_arm(arm, tmp_path / arm["name"])["model"],
                    validate_arm(arm, tmp_path / arm["name"])["gate_image_edge"],
                    validate_arm(arm, tmp_path / arm["name"])["gate_image_mode"],
                )
                for arm in image
            }
        )
        == 72
    )
    assert all("clef-flash" not in str(arm) for arm in arms)


def test_actual_treatment_guard_rejects_gray_text_without_io(tmp_path: Path) -> None:
    arm = plans(tmp_path / "base", tmp_path / "trust")["prompt-core"][0]
    arguments = arm["arguments"]
    arguments[arguments.index("--gate-image-mode") + 1] = "grayscale8"
    with pytest.raises(ValueError, match="Invalid gate-only"):
        validate_arm(arm, tmp_path / "never-created")
    assert not list(tmp_path.iterdir())


def test_token_audit_excludes_historical_calls_and_preserves_reported_counts(tmp_path: Path) -> None:
    directory = tmp_path / "declared-arm"
    directory.mkdir()
    (tmp_path / "status.json").write_text(
        json.dumps(
            {"arms": [{"name": "declared-arm", "incremental_accounting": {"entries": [{}, {}], "ledger_attempts": 2}}]}
        )
    )
    (directory / "report.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "id": "page",
                        "calls": [{"usage": {"input_tokens": 999999}}],
                        "ranking_calls": [{"crop_index": 0, "usage": {"input_tokens": 8000}, "entry": {}}],
                    }
                ]
            }
        )
    )
    (directory / "page-selector-0-request.json").write_text(
        json.dumps(
            {
                "model": "cloudflare/clef",
                "state": ["évidence", {"image_url": {"url": "data:image/png;base64,ignored"}}],
                "questions": {"q0": {}, "q1": {}},
            }
        )
    )
    audit = token_audit(tmp_path / "status.json")
    (observation,) = audit["observations"]
    assert observation["state_utf8_bytes"] == len("évidence".encode())
    assert observation["image_count"] == 1
    assert observation["question_count"] == 2
    assert observation["reported_usage"] == {"input_tokens": 8000}
    assert audit["attempt_inventory"][0]["entries"] == 2
