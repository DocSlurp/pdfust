"""Strict raw-response attribution, distinct attempts and first-error admission stop."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_structure_admission as admission
from bench import p003_structure_admission_run as runner
from bench import p003_structure_admission_verification as verifier
from bench.silver import sha, write_json


def fixture(output: Path, choice: str = "retain") -> tuple[list[dict], dict, list[dict]]:
    config = {**runner.configuration(admission.MODELS[0], "detector", 0.5, 0, 1), "run_id": output.name}
    body = admission.request(config["model"], "Complete literal evidence", None)
    selected = [{"index": 0, "page_id": "p", "candidate": {"id": "c"}, "body": body}]
    probabilities = dict.fromkeys(admission.CHOICES, 0.1)
    probabilities[choice] = 0.8
    response = {
        "entry": {
            "index": 9,
            "requested_model": config["model"],
            "tag": f"P003/{config['run_id']}/structure-admission/0",
            "request_sha256": sha(json.dumps(body, separators=(",", ":")).encode()),
        },
        "result": {"answers": {"q0": {"type": "choice", "choice": choice, "probabilities": probabilities}}},
        "replayed": False,
    }
    row = {
        "index": 0,
        "page_id": "p",
        "candidate_id": "c",
        "model": config["model"],
        "status": choice,
        "entry": response["entry"],
        "replayed": False,
        "usage": {},
        "receipt": runner.receipt(response["result"]),
    }
    write_json(output / "candidate-0-response.json", response)
    write_json(output / "candidate-0-result.json", row)
    return selected, config, [row]


def test_exact_raw_native_receipt_passes(tmp_path: Path) -> None:
    selected, config, rows = fixture(tmp_path)
    verifier.verify_decisions(tmp_path, selected, config, rows, initialization_failed=False)


@pytest.mark.parametrize("field", ["requested_model", "request_sha256", "tag"])
def test_wrong_request_attribution_rejected(tmp_path: Path, field: str) -> None:
    selected, config, rows = fixture(tmp_path)
    rows[0]["entry"][field] = "wrong"
    response = verifier.read(tmp_path / "candidate-0-response.json")
    response["entry"] = rows[0]["entry"]
    write_json(tmp_path / "candidate-0-response.json", response)
    write_json(tmp_path / "candidate-0-result.json", rows[0])
    with pytest.raises(ValueError, match="request hash/model/tag"):
        verifier.verify_decisions(tmp_path, selected, config, rows, initialization_failed=False)


def test_invalid_mass_cannot_receive_retain_credit(tmp_path: Path) -> None:
    selected, config, rows = fixture(tmp_path)
    response = verifier.read(tmp_path / "candidate-0-response.json")
    response["result"]["answers"]["q0"]["probabilities"]["retain"] = 0.01
    write_json(tmp_path / "candidate-0-response.json", response)
    with pytest.raises(ValueError, match="Invalid native answer"):
        verifier.verify_decisions(tmp_path, selected, config, rows, initialization_failed=False)
    rows[0].update(status="malformed_response", error={"stage": "parse"})
    write_json(tmp_path / "candidate-0-result.json", rows[0])
    verifier.verify_decisions(tmp_path, selected, config, rows, initialization_failed=False)


def test_initialization_failure_forbids_paid_answer(tmp_path: Path) -> None:
    selected, config, rows = fixture(tmp_path)
    with pytest.raises(ValueError, match="continued after"):
        verifier.verify_decisions(tmp_path, selected, config, rows, initialization_failed=True)


def test_complete_refusal_cannot_issue_request(tmp_path: Path) -> None:
    selected, config, rows = fixture(tmp_path)
    selected[0]["body"] = None
    rows[0]["status"] = "no_question_refusal"
    write_json(tmp_path / "candidate-0-result.json", rows[0])
    with pytest.raises(ValueError, match="Oversized complete"):
        verifier.verify_decisions(tmp_path, selected, config, rows, initialization_failed=False)


def test_dense_source_rendering_keeps_all_words_and_source_cap() -> None:
    text = "complete literal " * 3000
    source = {"page_size": [0, 0, 100, 100], "words": [{"id": "a", "text": text, "bbox": [1, 1, 20, 10]}]}
    state = {"tables": [], "unresolved_ids": ["a"]}
    assert text in runner.markdown(source, state)
    source["words"][0]["text"] = "x" * (2 * 1024 * 1024)
    with pytest.raises(ValueError, match="2MiB"):
        runner.markdown(source, state)


def test_rendering_rejects_duplicate_ownership_before_output() -> None:
    source = {"page_size": [0, 0, 100, 100], "words": [{"id": "a", "text": "literal", "bbox": [1, 1, 20, 10]}]}
    with pytest.raises(ValueError, match="exactly one owner"):
        runner.markdown(source, {"tables": [], "unresolved_ids": ["a", "a"]})
