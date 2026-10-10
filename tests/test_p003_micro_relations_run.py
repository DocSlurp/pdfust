"""Single-model micro probe selection, frozen requests and circuit behavior."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from bench import p003_micro_relations as micro
from bench import p003_micro_relations_run as runner
from bench.silver import write_json


def source(page: int) -> dict:
    return {
        "page_size": [100, 100],
        "words": [
            {
                "id": f"w{page}-{i}",
                "text": "literal " + str(i),
                "bbox": [10 + 30 * (i % 2), 10 + 20 * (i // 2), 30 + 30 * (i % 2), 20 + 20 * (i // 2)],
            }
            for i in range(6)
        ],
    }


def baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    directory = tmp_path / "baseline"
    directory.mkdir()
    frozen = {"records": [{"id": f"p{i}"} for i in range(16)], "manifest_sha256": "source-manifest"}
    report = {"results": [{"id": f"p{i}", "status": "ok", "source": source(i)} for i in range(16)]}
    write_json(directory / "frozen.json", frozen)
    write_json(directory / "report.json", report)
    trust = tmp_path / "trust.json"
    write_json(trust, {"root": "independent"})
    monkeypatch.setattr(runner.source, "authenticate_source", lambda *_args: (frozen, report))
    return directory, trust


class MockClient:
    """No-network metered transport fixture."""

    def __init__(self, output: Path, behaviors: list[str]) -> None:
        """Retain explicit outcomes and charges in memory only."""
        self.output, self.behaviors = output, behaviors
        self.calls: list[dict] = []
        self.entries: list[dict] = []

    def request(self, body: dict, **kwargs: object) -> dict:
        """Verify frozen inputs before returning one fresh response."""
        # Everything, including actual encoded wire bodies, must already be frozen.
        assert (self.output / "frozen.json").exists()
        assert len(list(self.output.glob("question-*-wire-encoded.json"))) == 12
        assert kwargs["replay"] is False
        index = len(self.calls)
        self.calls.append({"body": body, "kwargs": kwargs})
        action = self.behaviors[index] if index < len(self.behaviors) else "same"
        entry = {
            "tag": kwargs["tag"],
            "accounted_usd": 0.001,
            "cost_status": "reported",
            "provider_reported_usd": 0.001,
        }
        self.entries.append(entry)
        if action == "transport":
            entry.update(cost_status="reserved", accounted_usd=0.3)
            message = "Do not retain arbitrary transport detail"
            raise RuntimeError(message)
        if action == "malformed":
            result = {"answers": {"wrong-id": {}}, "usage": {"input_tokens": 3}}
        else:
            probabilities = {"same": 0.1, "separate": 0.1, "unresolved": 0.1}
            probabilities[action] = 0.8
            result = {
                "answers": {"q0": {"type": "choice", "choice": action, "probabilities": probabilities}},
                "usage": {"input_tokens": 5},
            }
        return {"result": result, "entry": entry, "replayed": False, "admission_wait_seconds": 0.01}


def test_source_hash_quota_identical_for_models_and_modes_and_refusal() -> None:
    plans = {f"p{i}": micro.freeze(source(i)) for i in range(16)}
    chosen = runner.select(plans)
    assert len(chosen) == 12
    assert Counter(pair["kind"] for pair in chosen) == {"cell": 4, "row": 4, "wrap": 4}
    assert max(Counter(pair["page_id"] for pair in chosen).values()) <= 2
    assert runner.select(dict(reversed(list(plans.items())))) == chosen
    for pair in chosen:
        compact = micro.body(plans[pair["page_id"]], pair["id"], "liquid/d1")
        verbose = micro.body(plans[pair["page_id"]], pair["id"], "convaiinnovations/laya", mode="verbose")
        assert compact["questions"] == verbose["questions"]
    with pytest.raises(ValueError, match="cannot meet"):
        runner.select({"p0": plans["p0"]})


def test_transport_failure_stops_without_later_reservations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory, trust = baseline(tmp_path, monkeypatch)
    output = tmp_path / "probe"
    client = MockClient(output, ["same", "transport"])
    report = runner.run(
        directory,
        trust,
        output,
        model="convaiinnovations/laya",
        provider="gateway",
        mode="micro",
        run_hosted=True,
        exclusive_paid_work=True,
        client_factory=lambda *_a: client,
        entries_reader=lambda *_a: client.entries,
    )
    assert len(client.calls) == 2
    assert report["status_counts"] == {"valid_nonabstaining": 1, "transport_error": 1, "not_attempted": 10}
    assert report["charges"]["effective_usd"] is None
    assert report["charges"]["unresolved_reserved_usd"] == 0.3
    assert report["results"][1]["error"]["detail"] is None
    assert report["pages_per_minute"] is None
    assert report["pages_per_dollar"] is None
    assert report["source_assignments_applied"] == 0
    frozen = json.loads((output / "frozen.json").read_bytes())
    assert frozen["config"]["model_fallback"] is False
    for call in client.calls:
        assert call["body"]["providerOptions"] == {"gateway": {"only": ["boundless"]}}


def test_malformed_return_continues_next_distinct_pair_and_abstention_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory, trust = baseline(tmp_path, monkeypatch)
    output = tmp_path / "probe"
    client = MockClient(output, ["malformed", "unresolved"])
    report = runner.run(
        directory,
        trust,
        output,
        model="liquid/d1",
        provider="gateway",
        mode="verbose",
        run_hosted=True,
        exclusive_paid_work=True,
        client_factory=lambda *_a: client,
        entries_reader=lambda *_a: client.entries,
    )
    assert len(client.calls) == 12
    assert report["status_counts"] == {"malformed_response": 1, "valid_abstention": 1, "valid_nonabstaining": 10}
    assert report["results"][1]["receipt"]["abstained"]
    assert len({call["kwargs"]["tag"] for call in client.calls}) == 12
    assert all(call["body"]["model"] == "liquid/d1" for call in client.calls)
    assert all("input" in call["body"] for call in client.calls)
    assert (output / "question-0-response.json").exists()
    assert report["results"][1]["admission_wait_seconds"] == 0.01
    assert report["correctness_measured"] is False
    assert report["baseline_credit"] is False
    assert report["charges"]["effective_usd"] == pytest.approx(0.012)
    assert "relationship probe" in report["charges"]["cost_scope"]
    assert report["retries"] == 0


def test_optin_and_gateway_exclusive_serial_before_source_read(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="run-hosted"):
        runner.run(
            tmp_path / "missing",
            tmp_path / "missing",
            tmp_path / "out",
            model="liquid/d1",
            provider="gateway",
            mode="micro",
        )
    for concurrency, exclusive in ((3, True), (1, False)):
        with pytest.raises(ValueError, match="serial transport"):
            runner.run(
                tmp_path / "missing",
                tmp_path / "missing",
                tmp_path / "out",
                model="liquid/d1",
                provider="gateway",
                mode="micro",
                run_hosted=True,
                transport_concurrency=concurrency,
                exclusive_paid_work=exclusive,
            )


def test_openrouter_three_uses_shared_client_and_native_unchanged_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory, trust = baseline(tmp_path, monkeypatch)
    output = tmp_path / "native-three"
    client = MockClient(output, [])
    monkeypatch.setattr(runner, "P003ConcurrentClient", lambda _root: client)
    report = runner.run(
        directory,
        trust,
        output,
        model=runner.DECISION_MODELS[0],
        provider="openrouter",
        mode="micro",
        run_hosted=True,
        transport_concurrency=3,
        entries_reader=lambda *_a: client.entries,
    )
    assert len(client.calls) == 12
    assert report["config"]["transport_concurrency"] == 3
    assert all("state" in call["body"] for call in client.calls)
    assert all("providerOptions" not in call["body"] for call in client.calls)
    assert all(len(call["body"]["state"].encode()) <= 768 for call in client.calls)
    frozen = json.loads((output / "frozen.json").read_bytes())
    for chosen in frozen["selected"]:
        raw = (output / f"question-{chosen['index']}-wire-encoded.json").read_bytes()
        assert runner.sha(raw) == chosen["wire_encoded_sha256"]
    assert sum(row["attempted_pair_modes"] for row in report["pure_model_outcomes_by_page"].values()) == 12
