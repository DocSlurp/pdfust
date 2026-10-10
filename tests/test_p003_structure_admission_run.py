"""Pure per-model admission, frozen-before-client and source-safe error outcomes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_structure_admission as helper
from bench import p003_structure_admission_run as runner
from bench.silver import sha, write_json
from tests.test_p003_structure_admission import example


def prepared(output: Path, *, same_page: bool = False, refusal: bool = False) -> tuple[dict, dict]:
    source, shape = example()
    config = {**runner.configuration(helper.MODELS[0], "detector", 0.5, 0, 3), "run_id": output.name}
    selected = []
    for i in range(3):
        candidate = {
            "id": f"c{i}",
            "table": helper.source_table(source, shape, ["a", "b"]),
            "source_ids": ["a", "b"],
            "question_status": "no_question_refusal" if refusal else "prepared",
        }
        body = None if refusal else helper.request(config["model"], "literal", None)
        selected.append({"index": i, "page_id": "p0" if same_page else f"p{i}", "candidate": candidate, "body": body})
    output.mkdir()
    write_json(output / "frozen.json", {"selected": selected})
    return {"pages": {f"p{i}": {"source": source} for i in range(16)}, "selected": selected}, config


class Client:
    """Metered CPU-only transport fixture."""

    def __init__(self, output: Path, actions: list[str]) -> None:
        """Retain independent canned attempts."""
        self.output, self.actions, self.calls, self.entries = output, actions, [], []

    def request(self, body: dict, **options: object) -> dict:
        """Assert request freezing and return a fresh native answer."""
        assert (self.output / "frozen.json").exists()
        assert options["replay"] is False
        action = self.actions[len(self.calls)]
        self.calls.append(body)
        entry = {
            "tag": options["tag"],
            "accounted_usd": 0.001,
            "cost_status": "reported",
            "provider_reported_usd": 0.001,
        }
        self.entries.append(entry)
        if action == "transport":
            entry.update(cost_status="reserved", accounted_usd=0.3)
            message = "fixture transport stopped"
            raise RuntimeError(message)
        probabilities = dict.fromkeys(helper.CHOICES, 0.1)
        probabilities[action if action in helper.CHOICES else "retain"] = 0.8
        answer = {"type": "choice", "choice": action, "probabilities": probabilities}
        return {"result": {"answers": {"q0": answer}}, "entry": entry, "replayed": False}


def test_transport_stops_remainder_and_never_credits_baseline(tmp_path: Path) -> None:
    output = tmp_path / "pure"
    prep, config = prepared(output)
    client = Client(output, ["retain", "transport"])
    report = runner.execute(
        prep, output, config, client_factory=lambda *_a: client, entries_reader=lambda *_a: client.entries
    )
    assert len(client.calls) == 2
    assert report["decision_status_counts"] == {"retain": 1, "transport_error": 1, "not_attempted": 1}
    assert len(report["results"]) == report["intended_page_count"] == 16
    assert report["results"][0]["tables"][0]["values"] == [["literal DATA", "formula x^2"]]
    for row in report["results"][1:]:
        assert row["tables"] == []
        assert row["unresolved_ids"] == ["a", "b"]
        assert row["baseline_credit"] is False
    assert report["incremental_admission"]["charges"]["effective_usd"] is None
    assert report["incremental_admission"]["charges"]["unresolved_reserved_usd"] == 0.3
    assert report["full_pipeline_pages_per_minute"] is None


def test_malformed_proceeds_distinct_question_but_page_atomic_failure(tmp_path: Path) -> None:
    output = tmp_path / "atomic"
    prep, config = prepared(output, same_page=True)
    client = Client(output, ["retain", "invalid", "reject"])
    report = runner.execute(
        prep, output, config, client_factory=lambda *_a: client, entries_reader=lambda *_a: client.entries
    )
    assert len(client.calls) == 3
    assert report["decision_status_counts"] == {"retain": 1, "malformed_response": 1, "reject": 1}
    assert report["results"][0]["status"] == "error"
    assert report["results"][0]["tables"] == []
    assert report["results"][0]["unresolved_ids"] == ["a", "b"]
    assert (output / "candidate-1-response.json").exists()


def test_abstain_reject_and_no_question_source_unresolved(tmp_path: Path) -> None:
    output = tmp_path / "abstain"
    prep, config = prepared(output)
    client = Client(output, ["unresolved", "reject", "retain"])
    report = runner.execute(
        prep, output, config, client_factory=lambda *_a: client, entries_reader=lambda *_a: client.entries
    )
    assert report["results"][0]["status"] == "ok"
    assert report["results"][0]["tables"] == report["results"][1]["tables"] == []
    assert report["results"][2]["tables"]
    output = tmp_path / "refusal"
    prep, config = prepared(output, refusal=True)
    client = Client(output, [])
    report = runner.execute(
        prep, output, config, client_factory=lambda *_a: client, entries_reader=lambda *_a: client.entries
    )
    assert not client.calls
    assert report["decision_status_counts"] == {"no_question_refusal": 3}
    assert all(not r["tables"] for r in report["results"])


def test_exact_parser_no_partial_menu_or_false_calibration() -> None:
    response = {
        "answers": {
            "q0": {
                "type": "choice",
                "choice": "retain",
                "probabilities": {"retain": 0.8, "reject": 0.1, "unresolved": 0.1},
                "confidence": 0.93,
            }
        }
    }
    receipt = runner.receipt(response)
    assert receipt["raw_confidence"] == 0.93
    assert receipt["uncalibrated"] is True
    response["answers"]["wrong"] = response["answers"]["q0"]
    with pytest.raises(ValueError, match="exact"):
        runner.receipt(response)
    response["answers"].pop("wrong")
    response["answers"]["q0"]["probabilities"].pop("reject")
    with pytest.raises(ValueError, match="exactly"):
        runner.receipt(response)


def test_explicit_arm_and_hosted_optin_no_gateway(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="admitted"):
        runner.configuration("liquid/d1", "detector", 0.5, 0, 3)
    with pytest.raises(ValueError, match="edge"):
        runner.configuration(helper.MODELS[0], "detector", 0.5, 128, 6)
    with pytest.raises(ValueError, match="run-hosted"):
        runner.run(
            tmp_path,
            tmp_path,
            tmp_path,
            tmp_path,
            model=helper.MODELS[0],
            acquisition="detector",
            threshold=0.5,
            image_edge=128,
        )


def test_prepare_freezes_exact_insertion_order_wire_before_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pool = tmp_path / "pool"
    (pool / "c0").mkdir(parents=True)
    source, shape = example()
    candidate = {"id": "c0", "table": helper.source_table(source, shape, ["a", "b"]), "source_ids": ["a", "b"]}
    text, packet = helper.packet(source, candidate["table"], candidate["source_ids"], pixels_available=False)
    body = helper.request(helper.MODELS[0], text, None)
    write_json(pool / "c0" / "candidate.json", candidate)
    (pool / "c0" / "text-packet.json").write_text(text)
    write_json(pool / "c0" / "request.json", body)
    variant = {
        "treatment": "text",
        "packet": packet,
        "requests": [
            {
                "model": helper.MODELS[0],
                "path": "request.json",
                "request_sha256": sha(json.dumps(body, separators=(",", ":")).encode()),
            }
        ],
    }
    baseline = tmp_path / "source-baseline"
    baseline.mkdir()
    write_json(baseline / "frozen.json", {"config": {}, "manifest_sha256": "manifest"})
    write_json(baseline / "report.json", {"metrics": {"wall_seconds": 23}, "effective_usd": 4})
    authenticated = {
        "frozen": {"arms": {}},
        "pages": {f"p{i}": {"record": {"id": f"p{i}"}, "source": source} for i in range(16)},
        "baselines": {
            baseline: (
                {"config": {}, "manifest_sha256": "manifest"},
                {"effective_usd": 4, "metrics": {"wall_seconds": 23}},
            )
        },
        "report": {
            "entries": [{"arm": "detector", "threshold": 0.5, "folder": "c0", "page_id": "p0", "variants": [variant]}]
        },
    }
    write_json(pool / "frozen.json", {"source_only": True})
    write_json(pool / "report.json", {"source_only": True})
    monkeypatch.setattr(runner, "authenticate_pool", lambda *_a: authenticated)
    output = tmp_path / "prepared"
    config = {**runner.configuration(helper.MODELS[0], "detector", 0.5, 0, 3), "run_id": "prepared"}
    result = runner.prepare(pool, {"root": "trust"}, {"source": "trust"}, output, config)
    assert (output / "candidate-0-wire.json").read_bytes() == json.dumps(body, separators=(",", ":")).encode()
    assert result["selected"][0]["body"] == body
    frozen = json.loads((output / "frozen.json").read_bytes())
    assert frozen["all_inputs_frozen_before_client"] is True
    assert frozen["baselines"][0]["historical_effective_usd"] == 4
    assert len(frozen["records"]) == 16
    for name, digest in frozen["artifact_sha256"].items():
        assert sha((output / name).read_bytes()) == digest
    with pytest.raises(FileExistsError):
        runner.prepare(pool, {}, {}, output, config)
