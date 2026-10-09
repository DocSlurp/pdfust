"""CPU-only fixed-rule tests; model inputs never receive scorer references."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import remote_combinations as combinations


@pytest.mark.parametrize(
    ("labels", "unanimity", "majority", "cheap", "pair"),
    [
        (("join", "join", "join"), "join", "join", "join", "join"),
        (("split", "join", "join"), "unresolved", "join", "join", "unresolved"),
        (("join", "split", "unresolved"), "unresolved", "unresolved", "unresolved", "unresolved"),
        (("unresolved", "unresolved", "split"), "unresolved", "unresolved", "unresolved", "unresolved"),
    ],
)
def test_predeclared_label_rules(
    labels: tuple[str, str, str], unanimity: str, majority: str, cheap: str, pair: str
) -> None:
    values = dict(zip(("intern", "flash", "pplx"), labels, strict=True))
    assert combinations.combine("unanimity3", values) == unanimity
    assert combinations.combine("majority3", values) == majority
    assert combinations.combine("flash_pplx_consensus", values) == cheap
    assert combinations.combine("intern_flash_consensus", values) == pair


def rows() -> list[dict[str, Any]]:
    return [
        {
            "id": "known",
            "page_id": "known-page",
            "arm": combinations.ARMS[0],
            "expected": "join",
            "labels": {"intern": "join", "flash": "split", "pplx": "unresolved", "clef": "split", "qwen4": "split"},
            "durations": {model: float(index) for index, model in enumerate(combinations.MODELS)},
        },
        {
            "id": "ambiguous",
            "page_id": "ambiguous-page",
            "arm": combinations.ARMS[0],
            "expected": "unresolved",
            "labels": dict.fromkeys(combinations.MODELS, "join"),
            "durations": dict.fromkeys(combinations.MODELS, 0.0),
        },
    ]


def metric(report: dict[str, Any], name: str) -> dict[str, Any]:
    return next(row for row in report["metrics"] if row["arm"] == combinations.ARMS[0] and row["name"] == name)


def test_known_abstention_and_wrong_decision_denominators_are_separate() -> None:
    report = combinations.summarize(rows())
    majority = metric(report, "majority3")
    assert majority["known_abstentions"] == 1
    assert majority["wrong_known_decisions"] == 0
    assert majority["known_correct"] == 0
    assert majority["ambiguous_abstentions"] == 0
    assert majority["ambiguous_decisions"] == 1
    assert metric(report, "flash")["wrong_known_decisions"] == 1
    assert majority["inference_calls"] == 6
    assert majority["calls_per_page_input"] == 3
    assert majority["measured_serial_latency_sum_seconds"] == 3.0
    assert metric(report, "flash_pplx_consensus")["calls_per_page_input"] == 2
    assert metric(report, "flash_pplx_consensus")["measured_serial_latency_sum_seconds"] == 3.0
    assert majority["cost_usd"] is None


@pytest.mark.parametrize("bad", [None, -1.0, float("nan"), True])
def test_missing_or_invalid_latency_is_unknown_not_zero(bad: Any) -> None:  # noqa: ANN401
    selected = rows()
    selected[0]["durations"]["pplx"] = bad
    report = combinations.summarize(selected)
    assert metric(report, "unanimity3")["measured_serial_latency_sum_seconds"] is None
    assert metric(report, "flash_pplx_consensus")["measured_serial_mean_seconds_per_page_input"] is None
    assert metric(report, "intern_flash_consensus")["measured_serial_latency_sum_seconds"] == 1.0


def test_oracle_is_not_a_policy_and_references_do_not_change_selection() -> None:
    selected = rows()
    expected = combinations.combine("majority3", selected[0]["labels"])
    changed = deepcopy(selected)
    changed[0]["expected"] = "split"
    combinations.summarize(changed)
    assert combinations.combine("majority3", changed[0]["labels"]) == expected
    report = combinations.summarize(selected)
    assert report["complementarity"][0]["oracle_union_known_correct_trio"] == 1
    assert all(not row["name"].startswith("oracle") for row in report["metrics"])
    assert "unattainable" in report["complementarity"][0]["oracle_semantics"]


def test_shared_known_abstention_is_not_a_wrong_decision() -> None:
    selected = rows()[:1]
    selected[0]["labels"] = dict.fromkeys(combinations.MODELS, "unresolved")
    report = combinations.summarize(selected)
    assert report["complementarity"][0]["trio_shared_wrong_known"] == 0
    assert metric(report, "unanimity3")["known_abstentions"] == 1
    assert report["priority_groups"]["shared_known_wrong_all5_all_sizes"] == []


def fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    source, output, packets = tmp_path / "source", tmp_path / "outputs", tmp_path / "packets.json"
    source.mkdir()
    (source / "private-targets.json").write_text("forbidden direct reference access")
    index = tmp_path / "index.json"
    index.write_text(
        json.dumps([{"id": f"p{i}", "arm": arm, "page_ids": ["same-page"]} for i, arm in enumerate(combinations.ARMS)])
    )
    packets.write_text('{"records":[]}')
    for name in combinations.MODELS:
        directory = output / (name + "-l015")
        directory.mkdir(parents=True)
        (directory / "status.json").write_text('{"status":"complete"}')
        events = [{"event": "attempt_completed", "id": f"p{i}", "inference_wall_seconds": 0.1} for i in range(3)]
        (directory / "attempts.jsonl").write_text("\n".join(json.dumps(row) for row in events) + "\n")
    return source, index, output, packets


def test_reference_access_delegated_to_approved_scorer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import remote_report  # noqa: PLC0415

    source, index, output, packets = fixture(tmp_path)
    calls = []

    def verified(*args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        calls.append((args, kwargs))
        return {
            "checkpoint": False,
            "incomplete_final_log_line": False,
            "worker_status": {"status": "complete"},
            "source_manifest_sha256": "source-hash",
            "source_index_sha256": "index-hash",
            "results": [
                {"id": f"p{i}", "status": "ok", "parsed": {"choice": "join"}, "score": {"expected": "join"}}
                for i in range(3)
            ],
        }

    monkeypatch.setattr(remote_report, "evaluate", verified)
    original_read = combinations._read  # noqa: SLF001

    def guarded_read(path: Path) -> bytes:
        if path.name == "private-targets.json":
            pytest.fail("references must only be read by the approved scorer")
        return original_read(path)

    monkeypatch.setattr(combinations, "_read", guarded_read)
    report = combinations.evaluate(source, index, output, packets)
    assert len(calls) == len(combinations.MODELS)
    assert report["matched_inputs"] == 3
    assert report["logical_inputs"] == 1
    assert metric(report, "unanimity3")["known_correct"] == 1


def test_scorer_rejection_propagates_without_quality_exclusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import remote_report  # noqa: PLC0415

    source, index, output, packets = fixture(tmp_path)

    def rejected(*_args: object, **_kwargs: object) -> None:
        message = "source hash mismatch"
        raise ValueError(message)

    monkeypatch.setattr(remote_report, "evaluate", rejected)
    with pytest.raises(ValueError, match="hash mismatch"):
        combinations.evaluate(source, index, output, packets)
