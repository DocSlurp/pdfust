"""CPU-only fake-client tests for bounded actual cache resubmission probes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench import decision_cache_probe as probe


def fixture_requests(tmp_path: Path, conditions: int = 1) -> tuple[Path, list[Path]]:
    """Retain successful bodies and a tiny published-price snapshot without credentials."""
    directory = tmp_path / "retained"
    (directory / "langfuse").mkdir(parents=True)
    paths = []
    entries = []
    for index in range(conditions):
        body = {"model": "fixture-model", "state": f"source-only image{index}", "questions": {"q0": {}}}
        path = directory / f"request-{index}.json"
        path.write_text(json.dumps(body))
        response_name = f"response-{index}.json"
        (directory / response_name).write_text(json.dumps({"answers": {"q0": "A"}}))
        entries.append(
            {
                "index": index,
                "request_sha256": probe.body_sha(body),
                "response_file": response_name,
                "accounted_usd": 0.001,
                "cost_status": "provider-reported USD",
            }
        )
        paths.append(path)
    (directory / "ledger.json").write_text(json.dumps({"requests": entries}))
    (directory / "langfuse/catalog-prices.json").write_text(
        json.dumps(
            {
                "fetched_at": 1,
                "prices": {
                    "fixture-model": {"input": 1e-6, "output": 0, "input_cache_read": 1e-7, "input_cache_write": 0}
                },
            }
        )
    )
    return directory, paths


class FakeClient:
    """Persist fake accounting; no transport, inference or credentials are available."""

    def __init__(self, directory: Path, *, fail: bool = False, cost: float = 0.001) -> None:
        """Configure only local fake outcomes and accounting."""
        self.directory = directory
        self.fail = fail
        self.cost = cost
        self.calls: list[tuple[dict[str, Any], bool]] = []

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int, replay: bool) -> dict[str, Any]:
        """Return a local fake response with a distinct persisted trial entry."""
        # Fake responses still exercise persistent per-trial indexes and actual-replay flags.
        self.calls.append((body, replay))
        assert max_body_bytes == probe.MAX_IMAGE_BODY_BYTES
        ledger_path = self.directory / "ledger.json"
        ledger = json.loads(ledger_path.read_text())
        index = len(ledger["requests"])
        entry = {
            "index": index,
            "tag": tag,
            "request_sha256": probe.body_sha(body),
            "accounted_usd": self.cost,
            "cost_status": "provider-reported USD",
            "elapsed_ms": 12,
            "provider": "fixture-provider",
        }
        usage = {
            "input_tokens": 1000,
            "output_tokens": 0,
            "cost": self.cost,
            "input_tokens_details": {"cached_tokens": 900 if len(self.calls) > 1 else 0, "cache_write_tokens": 0},
        }
        result = {"model": body["model"], "provider": "fixture-provider", "answers": {"q0": "A"}, "usage": usage}
        if self.fail:
            result["error"] = {"code": 429}
        response_name = f"response-{index}.json"
        (self.directory / response_name).write_text(json.dumps(result))
        entry["response_file"] = response_name
        ledger["requests"].append(entry)
        ledger_path.write_text(json.dumps(ledger))
        return {"entry": entry, "result": result, "replayed": False}


def test_offline_default_never_constructs_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory, paths = fixture_requests(tmp_path)

    def forbidden() -> None:
        pytest.fail("Offline preparation must not construct a credential-bearing hosted client")

    monkeypatch.setattr(probe, "DecisionClient", forbidden)
    state = probe.run_probe(paths, tmp_path / "output", directory=directory)
    assert state["records"] == []
    assert state["status"] == "prepared; no provider calls"
    assert (tmp_path / "output/plan.json").exists()


def test_identical_actual_submissions_and_resume(tmp_path: Path) -> None:
    directory, paths = fixture_requests(tmp_path)
    client = FakeClient(directory)
    state = probe.run_probe(paths, tmp_path / "output", hosted=True, directory=directory, client=client)
    assert len(client.calls) == 3
    assert all(not replay for _, replay in client.calls)
    assert all(body == client.calls[0][0] for body, _ in client.calls)
    assert [row["submission"] for row in state["records"]] == ["first", "repeat-1", "repeat-2"]
    assert len({row["entry"]["index"] for row in state["records"]}) == 3
    assert state["records"][1]["cache_read_tokens"] == 900
    assert state["records"][1]["effective_pricing"]["effective_usd"] == 0.001
    assert state["records"][1]["catalog_token_estimate"]["effective_usd"] == pytest.approx(0.00019)
    report = (tmp_path / "output/report.md").read_text()
    assert "does not establish cold/warm cache state" in report
    resumed = probe.run_probe(paths, tmp_path / "output", hosted=True, directory=directory, client=client)
    assert len(client.calls) == 3
    assert resumed["status"] == "complete"


def test_failed_request_stops_entire_model(tmp_path: Path) -> None:
    directory, paths = fixture_requests(tmp_path, conditions=2)
    client = FakeClient(directory, fail=True)
    state = probe.run_probe(paths, tmp_path / "output", hosted=True, directory=directory, client=client)
    assert len(client.calls) == 1
    assert state["records"][0]["status"] == "provider-error"
    resumed = probe.run_probe(paths, tmp_path / "another-output", hosted=True, directory=directory, client=client)
    assert len(client.calls) == 1
    assert resumed["records"][0]["status"] == "provider-error"


def test_wave_budget_persists_across_output_directories(tmp_path: Path) -> None:
    directory, paths = fixture_requests(tmp_path, conditions=2)
    client = FakeClient(directory, cost=0.09)
    first = probe.run_probe(paths, tmp_path / "first", hosted=True, directory=directory, client=client)
    assert len(client.calls) == 3
    assert first["status"] == "budget-exhausted"
    second = probe.run_probe(paths, tmp_path / "second", hosted=True, directory=directory, client=client)
    assert second["status"] == "budget-exhausted"
    assert len(client.calls) == 3


def test_limit_models_conditions_and_successful_input(tmp_path: Path) -> None:
    directory, paths = fixture_requests(tmp_path, conditions=3)
    with pytest.raises(ValueError, match="conditions"):
        probe.prepare_requests(paths, directory)
    with pytest.raises(ValueError, match="distinct"):
        probe.prepare_requests([paths[0], paths[0]], directory)
    body = json.loads(paths[0].read_text())
    body["state"] = "not a retained successful body"
    paths[0].write_text(json.dumps(body))
    with pytest.raises(ValueError, match="successful"):
        probe.prepare_requests([paths[0]], directory)


def test_call_limit_and_unknown_charge_reservation() -> None:
    ledger = {"requests": [{"accounted_usd": 0.3}]}
    with pytest.raises(RuntimeError, match="budget"):
        probe.admission(ledger, 0)
    with pytest.raises(RuntimeError, match="budget"):
        probe.admission({"requests": [{"accounted_usd": 0}] * 24}, 0)


def test_http200_provider_error_is_not_success() -> None:
    assert not probe.successful({"choices": [{"finish_reason": "error", "error": {"code": 429}}]})


def test_manifest_prefers_successful1200_rgb8_condition(tmp_path: Path) -> None:
    directory, paths = fixture_requests(tmp_path, conditions=2)
    records = []
    for index, path in enumerate(paths):
        body = json.loads(path.read_text())
        records.append(
            {
                "model": body["model"],
                "request_path": str(path),
                "request_sha256": probe.body_sha(body),
                "configuration": {"edge": 512 if index == 0 else 1200, "mode": "rgb8", "blank": False},
            }
        )
    records.insert(0, {**records[1], "request_sha256": "not retained"})
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps({"split": "DEV", "records": records}))
    assert probe.select_requests(manifest, directory) == [paths[1], paths[0]]


def test_batched_manifest_request_files_and_metadata(tmp_path: Path) -> None:
    directory, paths = fixture_requests(tmp_path, conditions=2)
    batches = []
    for index, path in enumerate(paths):
        body = json.loads(path.read_text())
        edge = 128 if index == 0 else 1200
        batches.append(
            {
                "model": body["model"],
                "request_file": path.name,
                "request_sha256": probe.body_sha(body),
                "arm": f"rgb8-{edge}",
                "scope": "page",
                "offset": 0,
                "case_indices": [0, 1],
                "case_ids": ["opaque0", "opaque1"],
                "source_sha256": ["source0", "source1"],
                "configuration": {"edge": edge, "mode": "rgb8", "blank": False},
            }
        )
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps({"batches": batches, "scope": "page"}))
    selected = probe.select_requests(manifest, directory)
    assert selected == [paths[1], paths[0]]
    state = probe.run_probe(selected, tmp_path / "output", directory=directory, manifest_path=manifest)
    assert [item["condition"] for item in state["plan"]] == ["rgb8-1200", "rgb8-128"]
    assert state["plan"][0]["batch_metadata"]["case_indices"] == [0, 1]
    assert state["plan"][0]["batch_metadata"]["scope"] == "page"
    assert "expected_document" not in state["plan"][0]["batch_metadata"]


def test_batched_manifest_rejects_traversal_and_hash_changes(tmp_path: Path) -> None:
    directory, paths = fixture_requests(tmp_path)
    body = json.loads(paths[0].read_text())
    batch = {"model": body["model"], "request_file": "../outside.json", "request_sha256": probe.body_sha(body)}
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps({"batches": [batch]}))
    with pytest.raises(ValueError, match="filename"):
        probe.select_requests(manifest, directory)
    batch["request_file"] = paths[0].name
    manifest.write_text(json.dumps({"batches": [batch]}))
    paths[0].write_text(json.dumps({**body, "state": "changed"}))
    with pytest.raises(ValueError, match="hash"):
        probe.select_requests(manifest, directory)
