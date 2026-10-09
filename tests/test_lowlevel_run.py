"""CPU-only L001 parsing, ownership, frozen-input and budget regression checks."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from bench.lowlevel_run import (
    CHOICES,
    TAG_PREFIX,
    evaluate,
    materialize,
    parse_response,
    report,
    run,
    score,
    wave_admission,
)


def response(choice: str = "join", **changes: Any) -> dict[str, Any]:  # noqa: ANN401
    answer = {"type": "choice", "choice": choice, "probabilities": {key: float(key == choice) for key in CHOICES}}
    return {"answers": {"q0": {**answer, **changes}}}


def observation() -> dict[str, Any]:
    return {
        "target_atoms": [[{"id": "g0", "text": "AB"}], [{"id": "g1", "text": "C"}]],
        "all_target_ids": ["g0", "g1"],
        "native_choice": "split",
        "candidates": {"join": [["g0", "g1"]], "split": [["g0"], ["g1"]], "unresolved": []},
    }


def test_strict_choice_response_and_rounding_ties() -> None:
    parsed = parse_response(response(probabilities={"join": 0.6, "split": 0.2, "unresolved": 0.19}), 1)[0]
    assert parsed["choice"] == "join"
    assert sum(parsed["probabilities"].values()) == pytest.approx(1)
    assert parsed["raw_probabilities"]["unresolved"] == 0.19
    tied = parse_response(response(probabilities={"join": 0.5, "split": 0.5, "unresolved": 0}), 1)[0]
    assert tied["choice"] == "unresolved"
    assert tied["raw_choice"] == "join"
    assert tied["tie_abstention"]
    result: dict[str, Any]
    for result in (
        {"answers": {}},
        {"answers": {**response()["answers"], "q1": response()["answers"]["q0"]}},
        response(type="score"),
        response(probabilities={"join": 0.9, "split": 0.1}),
        response(probabilities={"join": True, "split": 0, "unresolved": 0}),
        response(probabilities={"join": float("nan"), "split": 0, "unresolved": 0}),
        response(probabilities={"join": 0.7, "split": 0.2, "unresolved": 0.2}),
        response("split", probabilities={"join": 0.7, "split": 0.2, "unresolved": 0.1}),
    ):
        with pytest.raises(ValueError, match=r"L001|probability"):
            parse_response(result, 1)


def test_conservation_is_not_grouping_correctness() -> None:
    observed = observation()
    target = {"expected": "join", "expected_groups": [["irrelevant private full row amount"]]}
    wrong = score(observed, target, "split")
    assert wrong["output"]["conservation"]
    assert not wrong["description_partition_exact"]
    assert wrong["output"]["group_text"] == ["AB", "C"]
    assert score(observed, target, "join")["description_partition_exact"]
    unknown = materialize(observed, "unresolved")
    assert unknown["conservation"]
    assert unknown["unresolved_ids"] == ["g0", "g1"]
    assert unknown["unresolved_atoms"] == [atom for part in observed["target_atoms"] for atom in part]
    for groups in ([["g0"]], [["g0", "g0", "g1"]], [["g0", "invented"]]):
        changed = {**observed, "candidates": {**observed["candidates"], "join": groups}}
        with pytest.raises(ValueError, match=r"source|target"):
            materialize(changed, "join")


def test_persistent_budget_counts_failed_reservations() -> None:
    entries = [{"tag": TAG_PREFIX + str(i), "accounted_usd": 0.3} for i in range(4)]
    wave_admission(entries)
    entries.append({"tag": TAG_PREFIX + "failed", "accounted_usd": 0.3})
    with pytest.raises(RuntimeError, match="cap exhausted"):
        wave_admission(entries)
    wave_admission([{"tag": "another-campaign", "accounted_usd": 14.0}])
    with pytest.raises(ValueError, match="accounted_usd"):
        wave_admission([{"tag": TAG_PREFIX, "accounted_usd": float("nan")}])


@pytest.fixture
def frozen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "frozen"
    directory.mkdir()
    manifest: dict[str, Any] = {
        "schema": 1,
        "records": [],
        "pages": [],
        "models": ["m1", "m2"],
        "arms": ["glyph"],
        "preparation": {"cpu_seconds": 1},
    }
    targets: list[dict[str, Any]] = []
    for i in range(6):
        page_id = f"p{i}"
        obs = observation()
        filename = f"observation-{i}.json"
        data = json.dumps(obs).encode()
        (directory / filename).write_bytes(data)
        manifest["pages"].append(
            {"id": page_id, "observation_file": filename, "observation_sha256": hashlib.sha256(data).hexdigest()}
        )
        targets.append(
            {
                "id": page_id,
                "logical_id": f"logical-{i // 3}",
                "family": "wrap",
                "encoding": f"e{i % 3}",
                "expected": "join" if i < 3 else "unresolved",
                "expected_groups": [],
            }
        )
    for batch in range(2):
        for model in manifest["models"]:
            body = {
                "model": model,
                "state": {"literal": "source"},
                "questions": {
                    f"q{i}": {"type": "choice", "criteria": dict.fromkeys(CHOICES, "source-derived option")}
                    for i in range(3)
                },
            }
            body["state"]["batch"] = batch
            data = json.dumps(body, separators=(",", ":")).encode()
            filename = f"request-{batch}-{model}.json"
            (directory / filename).write_bytes(data)
            manifest["records"].append(
                {
                    "request": filename,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "model": model,
                    "arm": "glyph",
                    "page_ids": [f"p{i}" for i in range(batch * 3, batch * 3 + 3)],
                }
            )
    target_bytes = json.dumps(targets).encode()
    (directory / "private-targets.json").write_bytes(target_bytes)
    manifest["targets_sha256"] = hashlib.sha256(target_bytes).hexdigest()
    (directory / "manifest.json").write_text(json.dumps(manifest))
    (directory / "catalog-prices.json").write_text(
        json.dumps({"prices": {model: {"input": 0.000001, "output": 0.000001} for model in manifest["models"]}})
    )

    def verified(path: Path) -> dict[str, Any]:
        retained = json.loads((path / "manifest.json").read_text())
        for item in retained["records"]:
            assert hashlib.sha256((path / item["request"]).read_bytes()).hexdigest() == item["sha256"]
        for page in retained["pages"]:
            assert (
                hashlib.sha256((path / page["observation_file"]).read_bytes()).hexdigest() == page["observation_sha256"]
            )
        return retained

    monkeypatch.setattr("bench.lowlevel_run.verify_directory", verified)
    return directory


class MockClient:
    """Persist local mock accounting without credential access or a transport."""

    def __init__(self, directory: Path, fail_model: str | None = None) -> None:
        """Create an isolated local mock ledger."""
        directory.mkdir()
        self.ledger = directory / "ledger.json"
        self.fail_model = fail_model
        self.calls: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict[str, Any]:
        """Return a complete mock Choice response or persist a failed reservation."""
        assert max_body_bytes == 200000
        self.calls.append(body)
        entries = json.loads(self.ledger.read_text())["requests"] if self.ledger.exists() else []
        entry: dict[str, Any] = {
            "index": len(entries),
            "tag": tag,
            "request_sha256": hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest(),
            "accounted_usd": 0.3,
            "cost_status": "reserved",
            "elapsed_ms": 10,
        }
        if body["model"] == self.fail_model:
            entries.append(entry)
            self.ledger.write_text(json.dumps({"requests": entries}))
            message = "mock provider failure"
            raise RuntimeError(message)
        result = {
            "usage": {"input_tokens": 10, "output_tokens": 0, "cost": 0.002},
            "answers": {key: response("join")["answers"]["q0"] for key in body["questions"]},
        }
        entry.update(accounted_usd=0.002, cost_status="provider-reported USD", response_file="mock.json")
        entries.append(entry)
        self.ledger.write_text(json.dumps({"requests": entries}))
        return {"result": result, "entry": entry, "replayed": False}


def test_run_is_target_blind_and_reports_complete_denominators(
    frozen: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = MockClient(tmp_path / "ledger")
    original = Path.read_text

    def guarded(path: Path, *args: Any, **kwargs: Any) -> str:  # noqa: ANN401
        if path.name == "private-targets.json":
            message = "Runner must not read gold before transmission"
            raise AssertionError(message)
        return original(path, *args, **kwargs)

    with monkeypatch.context() as scope:
        scope.setattr(Path, "read_text", guarded)
        result = run(frozen, client=client)
    assert len(client.calls) == 4
    assert result["status"] == "complete"
    assert all("expected" not in json.dumps(body) for body in client.calls)
    scored = report(frozen)
    assert (frozen / "report.md").exists()
    for cohort in scored["cohorts"]:
        assert cohort["scored"] == cohort["inputs"] == 6
        assert cohort["known_exact"] == cohort["known_inputs"] == 3
        assert cohort["ambiguous_abstentions"] == 0
        assert cohort["ambiguous_inputs"] == 3
        assert cohort["encoding_consistent_logical_cases"] == 2
        assert cohort["effective_usd"] == pytest.approx(0.004)
    run(frozen, client=client)
    assert len(client.calls) == 4


def test_failure_stops_only_that_model_and_unknown_charge_stays_unknown(frozen: Path, tmp_path: Path) -> None:
    client = MockClient(tmp_path / "ledger", fail_model="m1")
    result = run(frozen, client=client)
    assert result["stopped_models"] == ["m1"]
    assert [body["model"] for body in client.calls] == ["m1", "m2", "m2"]
    cohorts = {row["model"]: row for row in evaluate(frozen)["cohorts"]}
    assert cohorts["m1"]["failures"] == 3
    assert cohorts["m1"]["unattempted"] == 3
    assert cohorts["m1"]["effective_usd"] is None
    assert cohorts["m1"]["unknown_cost_requests"] == 1
    assert cohorts["m2"]["scored"] == 6
    run(frozen, client=client)
    assert len(client.calls) == 3


def test_offline_report_never_instantiates_client_and_detects_changed_gold(
    frozen: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden() -> None:
        message = "Offline report must not read credentials"
        raise AssertionError(message)

    monkeypatch.setattr("bench.lowlevel_run.DecisionClient", forbidden)
    assert all(row["scored"] == 0 for row in report(frozen)["cohorts"])
    (frozen / "private-targets.json").write_text("[]")
    with pytest.raises(ValueError, match="targets changed"):
        evaluate(frozen)


def test_verify_runs_before_transport_and_gold(frozen: Path, tmp_path: Path) -> None:
    client = MockClient(tmp_path / "ledger")
    (frozen / "observation-0.json").write_text("changed")
    with pytest.raises(AssertionError):
        run(frozen, client=client)
    assert not client.calls


def test_bounded_request_slice_resumes_without_changing_denominators(frozen: Path, tmp_path: Path) -> None:
    client = MockClient(tmp_path / "ledger")
    first = run(frozen, client=client, max_requests=1)
    assert first["status"] == "slice_complete"
    assert first["planned_requests"] == 4
    assert first["completed_requests"] == 1
    assert len(client.calls) == 1
    assert sum(row["scored"] for row in evaluate(frozen)["cohorts"]) == 3
    complete = run(frozen, client=client)
    assert complete["status"] == "complete"
    assert len(client.calls) == 4


def test_catalog_reservation_preflight_is_not_observed_cost() -> None:
    from bench.lowlevel_run import reservation_preflight  # noqa: PLC0415 - isolate the policy under test.

    assert reservation_preflight(200000, {"input": 0.0000001}) == pytest.approx(0.02)
    with pytest.raises(ValueError, match="exceeds"):
        reservation_preflight(200000, {"input": 0.001})
    with pytest.raises(ValueError, match="missing"):
        reservation_preflight(100, {})


def test_swapped_and_reordered_candidate_aliases_are_refused() -> None:
    observed = observation()
    for candidates in (
        {"join": observed["candidates"]["split"], "split": observed["candidates"]["join"], "unresolved": []},
        {"join": [["g1", "g0"]], "split": [["g0"], ["g1"]], "unresolved": []},
        {"join": [["g0", "g1"]], "split": [["g1"], ["g0"]], "unresolved": []},
    ):
        changed = {**observed, "candidates": candidates}
        for choice in CHOICES:
            with pytest.raises(ValueError, match="partition"):
                score(changed, {"expected": choice}, choice)


def test_resource_history_preserves_all_resume_invocations(frozen: Path, tmp_path: Path) -> None:
    client = MockClient(tmp_path / "ledger")
    first = run(frozen, client=client, max_requests=1)
    first_resources = dict(first["execution_resources"])
    complete = run(frozen, client=client)
    history = complete["execution_history"]
    assert len(history) == 2
    assert history[0]["wall_seconds"] == first_resources["wall_seconds"]
    assert complete["execution_resources"]["wall_seconds"] == sum(row["wall_seconds"] for row in history)
    assert complete["execution_resources"]["cpu_seconds"] == sum(row["cpu_seconds"] for row in history)
    assert complete["execution_resources"]["peak_rss_bytes"] == max(row["peak_rss_bytes"] for row in history)


def test_model_failure_persists_across_frozen_directories(frozen: Path, tmp_path: Path) -> None:
    client = MockClient(tmp_path / "ledger", fail_model="m1")
    run(frozen, client=client)
    other = tmp_path / "another-freeze"
    shutil.copytree(frozen, other)
    (other / "results.json").unlink()
    client.fail_model = None
    before = len(client.calls)
    result = run(other, client=client)
    assert result["stopped_models"] == ["m1"]
    assert all(body["model"] == "m2" for body in client.calls[before:])
    assert result["model_stop_details"]["m1"]["request_sha256"]
    cohort = next(row for row in evaluate(other)["cohorts"] if row["model"] == "m1")
    assert cohort["refused_inputs"] == 6
    assert cohort["refusal_reasons"] == {"persistent model stop": 6}


def test_successful_http_with_invalid_schema_is_a_durable_model_stop(frozen: Path, tmp_path: Path) -> None:
    class InvalidClient(MockClient):
        def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict[str, Any]:
            """Corrupt only one model's schema after retaining successful accounting."""
            result = super().request(body, tag=tag, max_body_bytes=max_body_bytes)
            if body["model"] == "m1":
                result["result"]["answers"] = {}
            return result

    client = InvalidClient(tmp_path / "ledger")
    run(frozen, client=client)
    entries = json.loads(client.ledger.read_text())["requests"]
    assert entries[0]["response_file"]
    assert "error" not in entries[0]
    registry = json.loads((client.ledger.parent / "L001-model-stops.json").read_text())
    assert "m1" in registry["models"]
    assert registry["models"]["m1"]["reason"].startswith("model stopped")
