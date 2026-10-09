"""R001 offline freeze, deterministic DEV selection and no-call budget tests."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import decision_row_run as runner
from bench.decision_context_cases import context_cases
from bench.decision_rows import build_request, pilot_case, score_response


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    """Generate authored DEV controls without hosted calls or retained data access."""
    return context_cases()


def native_response(pilot: dict) -> dict:
    """Return an oracle native Choice payload solely for local scorer verification."""
    body = build_request(pilot["input"], "test-model")
    answers = {}
    for index, fragment in enumerate(pilot["input"]["fragments"]):
        expected = pilot["expected_assignments"][fragment["id"]]
        choice = "unassigned" if expected is None else f"slot{fragment['allowed_slots'].index(expected)}"
        answers[f"q{index}"] = {
            "type": "choice",
            "choice": choice,
            "probabilities": {key: float(key == choice) for key in body["questions"][f"q{index}"]["criteria"]},
        }
    return {"answers": answers, "usage": {"input_tokens": 100, "output_tokens": 10, "cost": 0.01}}


def test_selection_prespecified_all_templates_with_family_breadth(cases: list[dict]) -> None:
    indices = runner.selected_indices(cases)
    assert indices == [0, 11, 22, 3, 14, 25, 6, 17, 28, 9]
    assert {cases[i]["id"].rsplit("-", 1)[1] for i in indices} == {f"{i:02d}" for i in range(10)}
    assert len({cases[i]["family"] for i in indices}) == 3
    changed = deepcopy(cases)
    for case in changed:
        case["gold"] = {"choice": "private changed gold"}
    assert runner.selected_indices(changed) == indices
    assert runner.selected_indices(cases, all30=True) == list(range(30))


def test_prepare_freezes_every_body_before_client_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_client() -> None:
        message = "Credential-bearing client must not be constructed during preparation"
        raise AssertionError(message)

    monkeypatch.setattr(runner, "DecisionClient", forbidden_client)
    manifest = runner.prepare(tmp_path, ["test-model"], ["geometry"])
    assert len(manifest["records"]) == 10
    persisted = json.loads((tmp_path / "manifest.json").read_text())
    runner.verify_manifest(tmp_path, persisted)
    for row in persisted["records"]:
        body = json.loads((tmp_path / row["request_file"]).read_text())
        assert "gold" not in body["state"]
        assert "expected_assignments" not in body["state"]
        assert "case_id" not in body["state"]
        pilot = persisted["targets"][str(row["case_index"])]
        assert score_response(pilot, native_response(pilot))["region_exact"]
    assert manifest["preparation"]["cpu_seconds"] >= 0


def small_manifest(tmp_path: Path, cases: list[dict]) -> dict:
    """Use a singleton frozen artifact with only test-authored ledger data."""
    pilot = pilot_case(cases[0])
    pilot.pop("original_case")
    pilot["local_to_original_source_ids"] = {str(k): v for k, v in pilot["local_to_original_source_ids"].items()}
    body = build_request(pilot["input"], "m")
    data = runner.encode(body)
    key = hashlib.sha256(data).hexdigest()
    path = tmp_path / "request.json"
    path.write_bytes(data)
    targets = {"0": pilot}
    return {
        "models": ["m"],
        "arms": ["geometry"],
        "prices": {"m": {"input": 0.01, "output": 0}},
        "targets": targets,
        "targets_sha256": hashlib.sha256(json.dumps(targets, sort_keys=True).encode()).hexdigest(),
        "records": [
            {
                "model": "m",
                "arm": "geometry",
                "case_index": 0,
                "case_id": "test-only",
                "request_file": path.name,
                "request_sha256": key,
                "request_bytes": len(data),
            }
        ],
    }


def test_budget_and_tampering_fail_before_transmission(tmp_path: Path, cases: list[dict]) -> None:
    manifest = small_manifest(tmp_path, cases)
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"requests": [{"request_sha256": "prior", "accounted_usd": 0.21}]}))
    (tmp_path / "results.json").write_text(json.dumps({"schema": 1, "wave_start": 0, "records": []}))
    calls = []
    client = SimpleNamespace(ledger=ledger, request=lambda *args, **_kwargs: calls.append(args))
    report = runner.run(tmp_path, manifest, client=client)
    assert calls == []
    assert report["budget_exhausted"]
    assert report["records"][0]["status"] == "unattempted"
    changed = deepcopy(manifest)
    changed["targets"]["0"]["expected_choice"] = "B"
    with pytest.raises(ValueError, match="target hash"):
        runner.run(tmp_path, changed, client=object())
    (tmp_path / "request.json").write_text("tampered")
    with pytest.raises(ValueError, match="request hash"):
        runner.run(tmp_path, manifest, client=object())


def test_success_checkpoint_resume_and_unique_cost(tmp_path: Path, cases: list[dict]) -> None:
    manifest = small_manifest(tmp_path, cases)
    ledger = tmp_path / "ledger.json"
    calls = []

    def request(body: dict[str, Any], **kwargs: Any) -> dict:  # noqa: ANN401
        calls.append(kwargs)
        entry = {
            "index": 0,
            "request_sha256": hashlib.sha256(runner.encode(body)).hexdigest(),
            "response_file": "test-response.json",
            "accounted_usd": 0.01,
            "cost_status": "provider-reported USD",
            "elapsed_ms": 100,
        }
        ledger.write_text(json.dumps({"requests": [entry]}))
        return {"entry": entry, "result": native_response(manifest["targets"]["0"]), "replayed": False}

    client = SimpleNamespace(ledger=ledger, request=request)
    report = runner.run(tmp_path, manifest, client=client)
    assert report["records"][0]["score"]["region_exact"]
    resumed = runner.run(tmp_path, manifest, client=client)
    assert len(calls) == 1
    assert calls[0]["max_body_bytes"] == 750000
    summary = runner.summarize(manifest, resumed)
    assert summary["unique_requests"] == 1
    assert summary["effective_usd"] == 0.01
    row = summary["rows"][0]
    assert row["fragment_accuracy"] == row["record_f1"] == 1.0
    assert row["candidate_oracle_covered"] == row["candidate_oracle_total"] == 3
    assert row["transmitted_pages_per_api_minute"] == 600


def test_failed_model_stops_without_retry(tmp_path: Path, cases: list[dict]) -> None:
    manifest = small_manifest(tmp_path, cases)
    second = deepcopy(manifest["records"][0])
    second["case_index"] = 1
    manifest["records"].append(second)
    ledger = tmp_path / "ledger.json"
    calls = []

    def failure(body: dict[str, Any], **kwargs: Any) -> None:  # noqa: ANN401
        calls.append(kwargs)
        ledger.write_text(
            json.dumps(
                {
                    "requests": [
                        {
                            "index": 0,
                            "request_sha256": hashlib.sha256(runner.encode(body)).hexdigest(),
                            "accounted_usd": 0.30,
                            "error": "HTTP 400",
                        }
                    ]
                }
            )
        )
        message = "hosted call failed (HTTP 400); reservation retained"
        raise RuntimeError(message)

    client = SimpleNamespace(ledger=ledger, request=failure)
    report = runner.run(tmp_path, manifest, client=client)
    assert len(calls) == 1
    assert report["records"][0]["status"] == "failed"
    assert report["records"][0]["entry"]["accounted_usd"] == 0.30
    assert report["records"][1]["status"] == "unattempted"
    runner.run(tmp_path, manifest, client=client)
    assert len(calls) == 1


def test_zero_reported_cost_uses_catalog_and_replays_deduplicate(tmp_path: Path, cases: list[dict]) -> None:
    manifest = small_manifest(tmp_path, cases)
    pilot = manifest["targets"]["0"]
    row = {
        **manifest["records"][0],
        "status": "ok",
        "replayed": True,
        "score": score_response(pilot, native_response(pilot)),
        "usage": {"cost": 0, "input_tokens": 100, "output_tokens": 10},
        "entry": {"index": 9, "accounted_usd": 0.30, "cost_status": "reserved", "elapsed_ms": 10},
    }
    summary = runner.summarize(manifest, {"records": [row, deepcopy(row)]})
    assert summary["unique_requests"] == 1
    assert summary["effective_usd"] == 1.0
    assert summary["costs"][0]["reported_usd"] == 0
    assert summary["rows"][0]["replayed_inputs"] == 2
    assert summary["rows"][0]["transmitted_pages_per_api_minute"] == 0


def test_page_scope_default_and_region_explicit(
    tmp_path: Path, cases: list[dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "context_cases", lambda: cases[:1])
    page = runner.prepare(tmp_path / "page", ["test-model"], ["image512"])
    region = runner.prepare(tmp_path / "region", ["test-model"], ["image512"], scope="region")
    assert page["scope"] == "page"
    assert page["records"][0]["image"]["identity"]["scope"] == "page"
    assert region["scope"] == "region"
    assert region["records"][0]["image"]["identity"]["scope"] == "region"
    assert page["records"][0]["request_sha256"] != region["records"][0]["request_sha256"]
    with pytest.raises(ValueError, match="different configuration"):
        runner.prepare(tmp_path / "page", ["test-model"], ["image512"], scope="region")
