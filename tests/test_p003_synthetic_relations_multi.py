"""Mock-only shared-context scopes, atomic failures and independent replay."""

# ruff: noqa: ANN401, TRY003, EM101
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import p003_synthetic_relations as evidence
from bench import p003_synthetic_relations_eval as single_eval
from bench import p003_synthetic_relations_multi as protocol
from bench import p003_synthetic_relations_multi_eval as evaluator
from bench import p003_synthetic_relations_multi_run as runner
from bench import p003_synthetic_relations_prepare as corpus
from bench.silver import sha, write_json

MODEL = "perplexity/pplx-decider-v1.1-27b"


class Client:
    """Own an in-memory mocked transport and one receipt per shared request."""

    def __init__(self, *, failures: bool = False) -> None:
        """Choose strict responses or one malformed group followed by transport failure."""
        self.entries: list[dict[str, Any]] = []
        self.calls = 0
        self.failures = failures

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return a native scoped answer envelope without calling a network or ledger."""
        index = self.calls
        self.calls += 1
        assert kwargs["replay"] is False
        entry = {
            "tag": kwargs["tag"],
            "requested_model": body["model"],
            "request_sha256": sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()),
            "accounted_usd": 0.01,
            "provider_reported_usd": 0.01,
            "cost_status": "provider-reported USD",
        }
        if self.failures and index == 2:
            entry.update(accounted_usd=0.3, cost_status="reserved")
            del entry["provider_reported_usd"]
            self.entries.append(entry)
            raise RuntimeError("Owned mocked transport failure")
        self.entries.append(entry)
        answers = {
            key: {
                "type": "choice",
                "choice": "same",
                "probabilities": {"same": 0.7, "separate": 0.3, "unresolved": 0.0},
            }
            for key in body["questions"]
        }
        if self.failures and index == 0:
            answers["q1"]["name"] = "q1"
        return {"entry": entry, "replayed": False, "result": {"model": body["model"], "answers": answers}}


@pytest.fixture(scope="module")
def inputs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("shared-context")
    pool = root / "pool"
    corpus.prepare(pool)
    frozen = json.loads((pool / "frozen.json").read_bytes())
    authority = root / "source-map.json"
    write_json(authority, {**frozen["code_sha256"], "source_frozen_sha256": sha((pool / "frozen.json").read_bytes())})
    arms = []
    for size, mode, failures in ((4, "text_geometry", False), (8, "rows_rules", False), (4, "rows_rules", True)):
        output = root / f"arm-{size}-{mode}-{failures}"
        client = Client(failures=failures)
        runner.run(
            pool,
            authority,
            output,
            model=MODEL,
            size=size,
            mode=mode,
            run_hosted=True,
            client_factory=lambda *_, mock=client: mock,
            entries_reader=lambda *_, mock=client: mock.entries,
        )
        runtime_map = root / (output.name + "-map.json")
        write_json(runtime_map, json.loads((output / "frozen.json").read_bytes())["code_sha256"])
        arms.append((output, runtime_map, client.calls))
    return {"pool": pool, "authority": authority, "context": single_eval.source_context(pool, authority), "arms": arms}


def test_groups_complete_source_hash_order_no_labels(inputs: dict[str, Any]) -> None:
    records = inputs["context"]["records"]
    for size in protocol.SIZES:
        groups = protocol.groups(records, size)
        assert len(groups) == 24 // size
        assert protocol.groups(list(reversed(records)), size) == groups
        assert {r["id"] for group in groups for r in group} == {r["id"] for r in records}
        cfg = runner.configuration(MODEL, size=size, mode="rows_rules")
        body = protocol.request(groups[0], cfg)
        state = json.loads(body["state"])
        assert isinstance(body["state"], str)
        for index, record in enumerate(groups[0]):
            key = f"q{index}"
            assert state["questions"][key] == evidence.packet(record, mode="rows_rules")
            assert record["id"] not in body["state"]
            assert "state.questions." + key in body["questions"][key]["instructions"]
            assert state["questions"][key]["omitted_word_count"] == 0
        assert cfg["isolation_guaranteed"] is False


@pytest.mark.parametrize("fault", ["missing", "extra", "name", "probability", "model"])
def test_complete_envelope_atomic_no_repair(inputs: dict[str, Any], fault: str) -> None:
    group = protocol.groups(inputs["context"]["records"], 4)[0]
    cfg = runner.configuration(MODEL, size=4)
    body = protocol.request(group, cfg)
    raw = Client().request(body, tag="mock", replay=False)["result"]
    if fault == "missing":
        del raw["answers"]["q3"]
    elif fault == "extra":
        raw["answers"]["q4"] = deepcopy(raw["answers"]["q0"])
    elif fault == "name":
        raw["answers"]["q1"]["name"] = "q1"
    elif fault == "probability":
        raw["answers"]["q2"]["probabilities"]["same"] = 0.8
    else:
        raw["model"] = "other/model"
    with pytest.raises(ValueError, match=r"envelope|fields|maximum|model"):
        protocol.parse(group, body, raw, cfg)


def test_mock_atomic_failure_continues_then_stops_all24(inputs: dict[str, Any]) -> None:
    run, authority, calls = inputs["arms"][2]
    verified = evaluator.verify_run(run, authority, inputs["context"])
    assert calls == 3
    assert [g["status"] for g in verified["groups"]] == [
        "malformed_response",
        "valid",
        "transport_error",
        "not_attempted",
        "not_attempted",
        "not_attempted",
    ]
    assert dict(__import__("collections").Counter(r["status"] for r in verified["rows"])) == {
        "malformed_response": 4,
        "valid_nonabstaining": 4,
        "transport_error": 4,
        "not_attempted": 12,
    }
    assert verified["charges"]["effective_usd"] is None
    assert verified["charges"]["unresolved_reserved_usd"] == 0.3
    assert verified["charges"]["known_partial_effective_usd"] == 0.02


def test_independent_replay_no_gold_shared_charge_once(inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_bytes

    def no_gold(path: Path) -> bytes:
        if path.name == "private-gold.json":
            pytest.fail("Source replay must not read labels")
        return original(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", no_gold)
        arms = [evaluator.verify_run(run, authority, inputs["context"]) for run, authority, _ in inputs["arms"][:2]]
    for arm, expected in zip(arms, (0.06, 0.03), strict=True):
        assert arm["charges"]["effective_usd"] == pytest.approx(expected)
        assert len(arm["rows"]) == 24
        assert arm["full_pipeline_rate"] is None
    gold_path = inputs["pool"] / "private-gold.json"
    gold = single_eval.load_gold(gold_path, sha(gold_path.read_bytes()), inputs["context"])
    scores = [evaluator.score(arm, gold, inputs["context"]) for arm in arms]
    for scored in scores:
        assert scored["all_24"]["author_label_matches"] == 12
        assert scored["visually_cued_18"]["intended_count"] == 18
        assert scored["indeterminate_6"]["intended_count"] == 6
        assert "deterministic_identical_response_author_label_maximum" not in scored["evidence_conditioned_control"]
    assert scores[0]["twins_summary"]["identical_local_evidence_pair_count"] == 12
    assert scores[1]["twins_summary"]["identical_local_evidence_pair_count"] == 3


@pytest.mark.parametrize("fault", ["financial_duplicate", "partial_outcome", "raw", "self_hashed_request"])
def test_independent_tamper_rejection(inputs: dict[str, Any], tmp_path: Path, fault: str) -> None:
    run, authority, _ = inputs["arms"][0]
    target = tmp_path / run.name
    shutil.copytree(run, target)
    if fault == "financial_duplicate":
        path = target / "report.json"
        value = single_eval.load(path)
        value["charges"]["entries"].append(deepcopy(value["charges"]["entries"][0]))
        write_json(path, value)
    elif fault == "partial_outcome":
        path = target / "results.json"
        value = single_eval.load(path)
        value["results"][0]["receipt"]["choice"] = "separate"
        write_json(path, value)
    elif fault == "raw":
        path = target / "group-0-response.json"
        value = single_eval.load(path)
        value["result"]["answers"]["q3"]["probabilities"]["same"] = 0.8
        write_json(path, value)
    else:
        frozen = single_eval.load(target / "frozen.json")
        body = single_eval.load(target / "group-0-wire-request.json")
        state = json.loads(body["state"])
        state["questions"]["q1"]["source"]["words"][0]["text"] = "altered"
        body["state"] = evidence.dump(state)
        for kind in ("canonical", "wire"):
            path = target / f"group-0-{kind}-request.json"
            write_json(path, body)
            frozen["artifact_sha256"][path.name] = sha(path.read_bytes())
        path = target / "group-0-wire-encoded.json"
        path.write_bytes(json.dumps(body, separators=(",", ":"), allow_nan=False).encode())
        frozen["artifact_sha256"][path.name] = sha(path.read_bytes())
        write_json(target / "frozen.json", frozen)
    with pytest.raises(ValueError, match=r"receipt|outcomes|probabilities|replay|denominator"):
        evaluator.verify_run(target, authority, inputs["context"])


def test_no_opt_in_no_client(inputs: dict[str, Any], tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Explicit root"):
        runner.run(
            inputs["pool"],
            inputs["authority"],
            tmp_path / "absent",
            model=MODEL,
            size=4,
            client_factory=lambda *_: pytest.fail("No client during preparation"),
        )


def test_interference_comparison_requires_matched_treatments(inputs: dict[str, Any]) -> None:
    run, authority, _ = inputs["arms"][0]
    multi = evaluator.verify_run(run, authority, inputs["context"])
    control = deepcopy(multi)
    control["config"]["processor"] = "p003_synthetic_relations"
    control["rows"][0]["receipt"]["choice"] = "separate"
    comparison = evaluator.compare(control, multi)
    assert comparison["case_count"] == 24
    assert comparison["choice_changed_count"] == 1
    assert comparison["accuracy_claim"] is False
    control["config"]["mode"] = "rows_rules"
    with pytest.raises(ValueError, match="Matching authenticated"):
        evaluator.compare(control, multi)
