from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from bench.decision_context_cases import context_cases
from bench.decision_oplog import apply, from_context, make_cell, operation, proposals
from bench.decision_oplog_run import (
    CASE_INDICES,
    MAX_BODY_BYTES,
    MAX_CALLS,
    MODELS,
    encode,
    parse_choice,
    prepare,
    run,
    score,
    verify,
    wave_admission,
)


@pytest.fixture(scope="module")
def cases() -> list[dict[str, Any]]:
    return context_cases()


@pytest.fixture
def frozen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cases: list[dict[str, Any]]) -> tuple[Path, dict[str, Any]]:
    class MockImageBuilder:
        def __init__(self, _directory: Path) -> None:
            pass

        def make_variant(self, pdf: bytes, _bbox: object, **options: Any) -> dict[str, Any]:  # noqa: ANN401 - mock transport.
            # This stub represents bytes only; no visual quality assertion uses it.
            return {"data": hashlib.sha256(pdf).digest(), "edge": options["edge"], "mode": options["mode"]}

    monkeypatch.setattr("bench.decision_oplog_run.VariantCache", MockImageBuilder)
    monkeypatch.setattr("bench.decision_oplog_run.context_cases", lambda: cases)
    directory = tmp_path / "pilot"
    return directory, prepare(directory, max_steps=2)


class MockClient:
    """Persist synthetic ledger entries without credentials or a transport."""

    def __init__(self, directory: Path, fail_model: str | None = None) -> None:
        """Create an isolated mock ledger."""
        self.ledger = directory / "ledger.json"
        directory.mkdir(parents=True, exist_ok=True)
        self.fail_model = fail_model
        self.calls: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict[str, Any]:
        """Return bounded one-hot operation choices or a retained failure."""
        assert max_body_bytes == MAX_BODY_BYTES
        assert len(encode(body)) <= max_body_bytes
        self.calls.append(body)
        entries = json.loads(self.ledger.read_text())["requests"] if self.ledger.exists() else []
        entry: dict[str, Any] = {
            "index": len(entries),
            "tag": tag,
            "accounted_usd": 0.30,
            "cost_status": "reserved",
            "request_sha256": hashlib.sha256(encode(body)).hexdigest(),
            "elapsed_ms": 4.0,
        }
        if body["model"] == self.fail_model:
            entries.append(entry)
            self.ledger.write_text(json.dumps({"requests": entries}))
            message = "synthetic failed call"
            raise RuntimeError(message)
        options = body["questions"]["q0"]["criteria"]
        choice = next(key for key, text in options.items() if key != "abstain" and json.loads(text)["kind"] == "assign")
        result = {
            "usage": {"input_tokens": 100, "output_tokens": 0, "cost": 0.000001},
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": {key: float(key == choice) for key in options},
                }
            },
        }
        entry.update(accounted_usd=0.000001, cost_status="provider-reported USD", response_file="mock-response.json")
        entries.append(entry)
        self.ledger.write_text(json.dumps({"requests": entries}))
        return {"result": result, "entry": entry, "replayed": False}


def test_prepare_freezes_prespecified_inputs_and_implementation_without_credentials(
    frozen: tuple[Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, manifest = frozen

    def forbidden_client() -> None:
        message = "Prepare must not load credentials"
        raise AssertionError(message)

    monkeypatch.setattr("bench.decision_oplog_run.DecisionClient", forbidden_client)
    verify(directory, manifest)
    assert tuple(row["index"] for row in manifest["cases"]) == CASE_INDICES
    assert manifest["max_call_ceiling"] == 40
    assert manifest["candidate_oracle"].startswith("unmeasured")
    assert "decision_oplog.py" in " ".join(manifest["code_sha256"])
    assert "gold" not in manifest


def test_prepare_and_verification_reject_changed_admissions(frozen: tuple[Path, dict[str, Any]]) -> None:
    directory, manifest = frozen
    with pytest.raises(ValueError, match="step cap"):
        prepare(directory, max_steps=9)
    with pytest.raises(ValueError, match="Image edge"):
        prepare(directory, image_edge=999)
    with pytest.raises(ValueError, match="models"):
        prepare(directory, models=("unknown",))
    changed = {**manifest, "max_steps": 99}
    with pytest.raises(ValueError, match="admission"):
        verify(directory, changed)
    (directory / manifest["cases"][0]["image_file"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="image changed"):
        verify(directory, manifest)


def test_operation_choice_distribution_requires_declared_ids_and_finite_normalized_values() -> None:
    options = {"op-existing", "abstain"}
    valid = {
        "answers": {
            "q0": {"type": "choice", "choice": "op-existing", "probabilities": {"op-existing": 1, "abstain": 0}}
        }
    }
    assert parse_choice(valid, options)["choice"] == "op-existing"
    for probabilities in (
        {"op-existing": 1},
        {"op-existing": float("nan"), "abstain": 0},
        {"op-existing": 0.2, "abstain": 0.2},
        {"op-existing": True, "abstain": 0},
    ):
        changed = {"answers": {"q0": {**valid["answers"]["q0"], "probabilities": probabilities}}}
        with pytest.raises(ValueError, match=r"distribution|probability|probabilities"):
            parse_choice(changed, options)


def test_scoring_ownership_conservation_is_not_accuracy_and_slots_are_separate(cases: list[dict[str, Any]]) -> None:
    case = cases[0]
    state = from_context(case)
    wrong = score(case, state)
    assert wrong["conservation"] is True
    assert wrong["source_group_exact"] is False
    # Mechanically assign physical rows, then join the two descriptions.
    while state.unassigned:
        op = next(op for op in proposals(state) if op.kind == "assign")
        state = apply(state, op)
    split_score = score(case, state)
    assert split_score["selected"] == "B"
    assert split_score["source_group_exact"] is False
    join = next(op for op in proposals(state) if op.kind == "join")
    state = apply(state, join)
    exact = score(case, state)
    assert exact["selected"] == "A"
    assert exact["source_group_exact"] is True
    assert exact["row_column_exact"] is True
    cell = next(cell for cell in state.cells if cell.role == "data" and cell.column == 0)
    shifted = apply(state, operation(state, "move", remove=(cell.id,), put=(make_cell(state, 4, 0, cell.source_ids),)))
    shifted_score = score(case, shifted)
    assert shifted_score["source_group_exact"] is True
    assert shifted_score["row_column_exact"] is False
    assert shifted_score["candidate_oracle"] == "unmeasured"


def test_ambiguous_gold_marks_layout_unscored(cases: list[dict[str, Any]]) -> None:
    result = score(cases[4], from_context(cases[4]))
    assert result["source_group_exact"] is True
    assert result["row_column_exact"] is None
    assert result["placement_scored_sources"] == 0


def test_breadth_first_adaptive_hashes_and_history_are_retained(
    frozen: tuple[Path, dict[str, Any]],
    tmp_path: Path,
) -> None:
    directory, manifest = frozen
    client = MockClient(tmp_path / "shared")
    result = run(directory, manifest, client=client)
    assert len(result["calls"]) == 40
    assert [row["case_index"] for row in result["calls"][:20:2]] == list(CASE_INDICES)
    assert all(row["step"] == 0 for row in result["calls"][:20])
    assert all(row["step"] == 1 for row in result["calls"][20:])
    assert all(row["status"] == "ok" for row in result["calls"])
    assert all(row["stop_reason"] == "step-cap" for row in result["sessions"])
    assert all(len(row["history"]) == 2 for row in result["sessions"])
    assert all(row["cost"]["basis"] == "provider-reported USD" for row in result["calls"])
    for row in result["calls"]:
        raw = (directory / row["request_file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["request_sha256"]
        assert b'"gold"' not in raw
        assert b'"expected"' not in raw
    count = len(client.calls)
    assert run(directory, manifest, client=client) == result
    assert len(client.calls) == count


def test_failed_call_stops_model_without_retry_and_preserves_partial_state(
    frozen: tuple[Path, dict[str, Any]],
    tmp_path: Path,
) -> None:
    directory, manifest = frozen
    client = MockClient(tmp_path / "shared", fail_model=MODELS[0])
    result = run(directory, manifest, client=client)
    assert sum(body["model"] == MODELS[0] for body in client.calls) == 1
    assert result["stopped_models"] == [MODELS[0]]
    assert sum(row["status"] == "failed" for row in result["calls"]) == 1
    stopped = [row for row in result["sessions"] if row["model"] == MODELS[0]]
    assert all(row["stop_reason"] == "model-failed" for row in stopped)
    assert all(row["history"] == [] for row in stopped)


def test_persistent_wave_cap_counts_reservations_across_directories() -> None:
    with pytest.raises(RuntimeError, match="persistent wave cap"):
        wave_admission([{"tag": "oplog/earlier-directory", "accounted_usd": 0.30}])
    with pytest.raises(RuntimeError, match="persistent wave cap"):
        wave_admission([{"tag": "oplog/earlier-directory", "accounted_usd": 0} for _ in range(MAX_CALLS)])
    wave_admission([{"tag": "different-wave", "accounted_usd": 10}])
    with pytest.raises(ValueError, match="finite nonnegative"):
        wave_admission([{"tag": "oplog/invalid", "accounted_usd": -1}])


def test_protected_destination_is_rejected_before_creation(tmp_path: Path) -> None:
    protected = tmp_path / "heldout-silver" / "pilot"
    with pytest.raises(ValueError, match="Protected"):
        prepare(protected)
    assert not protected.exists()
