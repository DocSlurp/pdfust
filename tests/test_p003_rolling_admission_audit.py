"""Check A002 literal selection, failure scope and authenticated typed responses."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from bench import p003_rolling_admission_audit as audit
from bench.silver import sha


def source_fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Make one source-owned proposal and one unresolved heading word."""
    source = {
        "id": "case",
        "words": [{"id": "w0", "text": "North"}, {"id": "w1", "text": "depot"}, {"id": "w2", "text": "Heading"}],
    }
    alternative = {
        "variant": "rolling",
        "source_words": copy.deepcopy(source["words"]),
        "unresolved_ids": ["w2"],
        "candidates": [
            {
                "row_count": 1,
                "col_count": 1,
                "values": [["North depot"]],
                "spans": [],
                "header_role": "unknown",
                "cells": [{"role": "unknown", "source_ids": ["w0", "w1"]}],
            }
        ],
    }
    return source, [alternative]


def test_exact_selection_has_no_native_credit() -> None:
    source, alternatives = source_fixture()
    row = audit.chosen_prediction(source, alternatives, {"status": "ok", "answer": {"choice": "rolling"}})
    assert row["tables"][0]["values"] == [["North depot"]]
    assert row["owned_source_ids"] == 2
    assert row["selection"] == "rolling"


@pytest.mark.parametrize("choice", ["not_table", "unresolved"])
def test_nonselection_preserves_complete_source(choice: str) -> None:
    source, alternatives = source_fixture()
    row = audit.chosen_prediction(source, alternatives, {"status": "ok", "answer": {"choice": choice}})
    assert row["tables"] == []
    assert row["unresolved_source_ids"] == len(source["words"])
    assert row["status"] == "ok"


@pytest.mark.parametrize("call", [None, {"status": "error", "answer": {"choice": "rolling"}}])
def test_failed_or_unattempted_has_zero_selected_credit(call: dict[str, Any] | None) -> None:
    source, alternatives = source_fixture()
    row = audit.chosen_prediction(source, alternatives, call)
    assert row["tables"] == []
    assert row["status"] == "error"
    assert row["unresolved_source_ids"] == len(source["words"])


def native_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    source, _alternatives = source_fixture()
    table = {"row_count": 1, "col_count": 1, "values": [["North depot"]], "spans": []}
    source["vector_candidates"] = [table]
    return source, {
        "tables": [table],
        "word_ownership": [{"table": 0, "cell": 0, "source_ids": ["w0", "w1"]}],
        "unresolved_ids": ["w2"],
    }


def test_native_separate_fixed_scope() -> None:
    source, selected = native_fixture()
    row = audit.native_prediction(source, selected)
    assert row["selection"] == "fixed_native_vector"
    assert row["owned_source_ids"] == 2


@pytest.mark.parametrize("change", ["duplicate", "literal", "incomplete"])
def test_native_refuses_false_ownership(change: str) -> None:
    source, selected = native_fixture()
    if change == "duplicate":
        selected["unresolved_ids"].append("w0")
    elif change == "literal":
        selected["word_ownership"][0]["source_ids"].reverse()
    else:
        selected["word_ownership"].clear()
    with pytest.raises(ValueError, match=r"differs|required"):
        audit.native_prediction(source, selected)


def response_fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    body = {"model": "model", "questions": {"q0": {"criteria": {"rolling": "", "unresolved": ""}}}}
    raw = json.dumps(body, separators=(",", ":")).encode()
    record = {
        "model": "model",
        "arm": "text",
        "id": "case",
        "request": "case.json",
        "sha256": sha(raw),
        "choices": ["rolling", "unresolved"],
        "route": "hosted_admission",
        "bytes": len(raw),
    }
    response = {
        "model": "model-version",
        "id": "generation",
        "provider": "provider",
        "usage": {},
        "answers": {
            "q0": {"type": "choice", "choice": "rolling", "probabilities": {"rolling": 1.0, "unresolved": 0.0}}
        },
    }
    (tmp_path / "response-1.json").write_text(json.dumps(response))
    call = {
        **record,
        "status": "ok",
        "usage": {},
        "answer": {
            "choice": "rolling",
            "probabilities": {"rolling": 1.0, "unresolved": 0.0},
            "normalization_delta": 0.0,
        },
        "entry": {
            "index": 1,
            "request_sha256": sha(raw),
            "requested_model": "model",
            "tag": "A002-rolling-admission/model/text/case",
            "response_file": "response-1.json",
            "served_model": "model-version",
            "generation_id": "generation",
            "provider": "provider",
        },
    }
    return record, call, body


def test_typed_raw_response_matches(tmp_path: Path) -> None:
    record, call, body = response_fixture(tmp_path)
    receipt = audit.verify_call(record, call, body, tmp_path)
    assert receipt["raw_response_sha256"] == sha((tmp_path / "response-1.json").read_bytes())


@pytest.mark.parametrize("change", ["choice", "identity", "wire", "usage", "tag", "filename"])
def test_response_receipt_refuses_corruption(change: str, tmp_path: Path) -> None:
    record, call, body = response_fixture(tmp_path)
    if change == "tag":
        call["entry"]["tag"] = "different"
    elif change == "filename":
        call["entry"]["response_file"] = "response-2.json"
    elif change == "wire":
        call["entry"]["request_sha256"] = "changed"
    else:
        response = json.loads((tmp_path / "response-1.json").read_bytes())
        if change == "choice":
            response["answers"]["q0"]["choice"] = "unresolved"
        elif change == "identity":
            response["id"] = "other"
        else:
            response["usage"] = {"input_tokens": 10}
        (tmp_path / "response-1.json").write_text(json.dumps(response))
    with pytest.raises(ValueError, match=r"differs|not a maximum"):
        audit.verify_call(record, call, body, tmp_path)


def test_prepare_existing_output_before_source_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object) -> None:
        pytest.fail("Opened retained artifact before existing-output refusal")

    monkeypatch.setattr(audit, "pinned", forbidden)
    with pytest.raises(FileExistsError):
        audit.prepare(tmp_path / "original", tmp_path / "candidate-plan", tmp_path / "responses", tmp_path)


def test_duplicate_provider_index_refused() -> None:
    with pytest.raises(ValueError, match="Global unique provider receipt indices"):
        audit.validate_provider_indices([{"entry": {"index": 1}}, {"entry": {"index": 1}}])
    audit.validate_provider_indices([{"entry": {"index": 1}}, {"status": "error"}])


def test_reference_dictionary_cannot_hide_duplicate() -> None:
    ids = {f"case-{i}" for i in range(audit.candidates.PAGE_COUNT)}
    targets = [{"id": i} for i in sorted(ids)]
    audit.validate_targets(targets, ids)
    targets[-1] = targets[0]
    with pytest.raises(ValueError, match="Complete exact unique"):
        audit.validate_targets(targets, ids)


def test_score_authority_before_plan_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trust = tmp_path / "trust.json"
    trust.write_text("{}")

    def forbidden(*_args: object) -> None:
        pytest.fail("Opened source plan before checking external current helper authority")

    monkeypatch.setattr(audit, "pinned", forbidden)
    with pytest.raises(ValueError, match="Independent current helper authority"):
        audit.audit(tmp_path / "plan", tmp_path / "out", plan_sha256="bad", trusted_code=trust, targets_sha256="bad")
