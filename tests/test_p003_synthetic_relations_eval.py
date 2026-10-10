"""Independent synthetic replay, label isolation, denominators and tamper rejection."""

# ruff: noqa: ANN401
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import p003_synthetic_relations_eval as evaluator
from bench import p003_synthetic_relations_prepare as corpus
from bench import p003_synthetic_relations_run as runner
from bench.silver import sha, write_json

MODEL = "perplexity/pplx-decider-v1.1-27b"


class Client:
    """Deterministic owned mock; records financial receipts once per request."""

    def __init__(self) -> None:
        """Initialize an in-memory receipt list, without any ledger or transport."""
        self.entries: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return one fresh strict answer, with positive mock reported charges."""
        entry = {
            "tag": kwargs["tag"],
            "requested_model": body["model"],
            "request_sha256": sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()),
            "accounted_usd": 0.01,
            "provider_reported_usd": 0.01,
            "cost_status": "provider-reported USD",
        }
        self.entries.append(entry)
        return {
            "entry": entry,
            "replayed": False,
            "result": {
                "model": body["model"],
                "answers": {
                    "q0": {
                        "type": "choice",
                        "choice": "same",
                        "probabilities": {"same": 0.7, "separate": 0.3, "unresolved": 0.0},
                    }
                },
            },
        }


@pytest.fixture(scope="module")
def inputs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("synthetic-evaluation")
    pool = root / "pool"
    corpus.prepare(pool)
    frozen = evaluator.load(pool / "frozen.json")
    source_map = root / "source-map.json"
    write_json(source_map, {**frozen["code_sha256"], "source_frozen_sha256": sha((pool / "frozen.json").read_bytes())})
    runs = []
    for mode in ("text_geometry", "rows_rules"):
        client = Client()
        output = root / mode
        runner.run(
            pool,
            source_map,
            output,
            model=MODEL,
            mode=mode,
            run_hosted=True,
            client_factory=lambda *_, mock=client: mock,
            entries_reader=lambda *_, mock=client: mock.entries,
        )
        runtime_map = root / (mode + "-map.json")
        write_json(runtime_map, evaluator.load(output / "frozen.json")["code_sha256"])
        runs.append((output, runtime_map))
    return {
        "pool": pool,
        "source_map": source_map,
        "runs": runs,
        "context": evaluator.source_context(pool, source_map),
        "gold_sha256": sha((pool / "private-gold.json").read_bytes()),
    }


def test_source_only_verification_then_all_cued_ambiguous_score(
    inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path.read_bytes

    def no_gold(path: Path) -> bytes:
        if path.name == "private-gold.json":
            pytest.fail("Gold must not be read during source/request/response verification")
        return original(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", no_gold)
        verified = [evaluator.verify_run(run, authority, inputs["context"]) for run, authority in inputs["runs"]]
    gold = evaluator.load_gold(inputs["pool"] / "private-gold.json", inputs["gold_sha256"], inputs["context"])
    for replay in verified:
        result = evaluator.score(replay, gold, inputs["context"])
        assert result["all_24"]["intended_count"] == 24
        assert result["all_24"]["author_label_matches"] == 12
        assert result["visually_cued_18"]["intended_count"] == 18
        assert result["indeterminate_6"]["intended_count"] == 6
        assert result["twins_summary"]["consistent_choice_count"] == 12
        assert result["charges"]["provider_reported_usd"] == pytest.approx(0.24)
        assert result["full_pipeline_rate"] is None
    assert verified[0]["config"]["mode"] == "text_geometry"
    text = evaluator.score(verified[0], gold, inputs["context"])
    rules = evaluator.score(verified[1], gold, inputs["context"])
    assert text["evidence_conditioned_control"]["deterministic_identical_response_author_label_maximum"] == 12
    assert rules["evidence_conditioned_control"]["deterministic_identical_response_author_label_maximum"] == 21


@pytest.mark.parametrize("fault", ["archive", "outcome", "financial", "raw_probability", "self_hashed_request"])
def test_replay_rejects_tampering(inputs: dict[str, Any], tmp_path: Path, fault: str) -> None:
    run, authority = inputs["runs"][0]
    # Keep basename because it is the immutable run/tag identity.
    target = tmp_path / run.name
    shutil.copytree(run, target)
    if fault == "archive":
        path = target / "code/p003_synthetic_relations_run.py"
        path.write_bytes(path.read_bytes() + b"\n# changed\n")
    elif fault == "outcome":
        report = evaluator.load(target / "report.json")
        report["results"][0]["receipt"]["choice"] = "separate"
        write_json(target / "report.json", report)
    elif fault == "financial":
        report = evaluator.load(target / "report.json")
        report["charges"]["provider_reported_usd"] = 0.0
        write_json(target / "report.json", report)
    elif fault == "raw_probability":
        response = evaluator.load(target / "question-0-response.json")
        response["result"]["answers"]["q0"]["probabilities"]["same"] = 0.6
        write_json(target / "question-0-response.json", response)
    else:
        frozen = evaluator.load(target / "frozen.json")
        body = evaluator.load(target / "question-0-wire-request.json")
        state = json.loads(body["state"])
        state["source"]["words"][0]["text"] = "altered"
        body["state"] = json.dumps(state)
        for kind in ("canonical", "wire"):
            path = target / f"question-0-{kind}-request.json"
            write_json(path, body)
            frozen["artifact_sha256"][path.name] = sha(path.read_bytes())
        encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
        path = target / "question-0-wire-encoded.json"
        path.write_bytes(encoded)
        frozen["artifact_sha256"][path.name] = sha(encoded)
        frozen["selected"][0]["wire_encoded_sha256"] = sha(encoded)
        write_json(target / "frozen.json", frozen)
    with pytest.raises(ValueError, match=r"authority|outcome|financial|probabilities|replay|denominator"):
        evaluator.verify_run(target, authority, inputs["context"])


def test_gold_authority_is_separate_and_complete(inputs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="separately supplied"):
        evaluator.load_gold(inputs["pool"] / "private-gold.json", "bad", inputs["context"])


def test_abstention_and_errors_preserve_strict_denominator(inputs: dict[str, Any]) -> None:
    run, authority = inputs["runs"][0]
    verified = deepcopy(evaluator.verify_run(run, authority, inputs["context"]))
    gold = evaluator.load_gold(inputs["pool"] / "private-gold.json", inputs["gold_sha256"], inputs["context"])
    first, second, third = verified["rows"][:3]
    first["status"] = "valid_abstention"
    first["receipt"]["choice"] = "unresolved"
    for row, status in ((second, "malformed_response"), (third, "transport_error")):
        row["status"] = status
        del row["receipt"]
    scored = evaluator.score(verified, gold, inputs["context"])
    assert scored["all_24"]["intended_count"] == 24
    assert scored["all_24"]["valid_nonabstaining_count"] == 21
    assert scored["all_24"]["status_counts"]["valid_abstention"] == 1
    assert sum(r["count"] for r in scored["all_24"]["confusion"]) == 24
    assert scored["all_24"]["strict_author_label_fraction"] == scored["all_24"]["author_label_matches"] / 24


def test_unknown_charges_and_reservations_never_become_complete() -> None:
    assert evaluator.charges([], 1)["effective_usd"] is None
    value = evaluator.charges([{"accounted_usd": 0.3, "cost_status": "reserved"}], 1)
    assert value["effective_usd"] is None
    assert value["unresolved_reserved_usd"] == 0.3
    assert value["provider_reported_usd"] is None


def test_evaluation_archive_no_pipeline_credit(inputs: dict[str, Any], tmp_path: Path) -> None:
    result = evaluator.evaluate(
        inputs["pool"],
        inputs["source_map"],
        [r[0] for r in inputs["runs"]],
        [r[1] for r in inputs["runs"]],
        inputs["pool"] / "private-gold.json",
        inputs["gold_sha256"],
        tmp_path / "evaluation",
    )
    assert len(result["scores"]) == 2
    assert result["new_calls"] == 0
    assert result["ledger_accessed"] is False
    assert result["full_pipeline_rate"] is None


def test_unknown_cost_basis_is_not_a_complete_estimate() -> None:
    entry = {"cost_status": "unknown", "accounted_usd": 0.3}
    result = evaluator.charges([entry], 1)
    assert result["effective_usd"] is None
    assert result["known_partial_effective_usd"] == 0
    assert result["accounted_usd"] == 0.3
    assert result["unresolved_reserved_usd"] == 0
