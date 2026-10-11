"""Exact alias authority cannot relax model identity or strict numeric choices."""
# ruff: noqa: E501, FBT001
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_synthetic_alias_replay as replay
from bench import p003_synthetic_relations_run as runner
from bench.silver import sha, write_json


@pytest.fixture
def attestation(tmp_path: Path) -> dict:
    path = tmp_path / "aliases.json"
    write_json(path, {"schema": 1, "aliases": {"liquid/d1": ["liquid/d1-20260930"]}})
    return replay.authority(path, sha(path.read_bytes()))


def test_exact_model_only_copy_preserves_probabilities(attestation: dict) -> None:
    raw = {"model": "liquid/d1-20260930", "answers": {"q0": {"type": "choice", "choice": "same", "probabilities": {"same": .7, "separate": .3, "unresolved": 0.0}, "confidence": .81}}, "provider": "retained-provider"}
    before = deepcopy(raw)
    normalized, receipt = replay.normalized_model(raw, "liquid/d1", attestation)
    assert raw == before
    assert normalized == {**before, "model": "liquid/d1"}
    assert receipt["raw_returned_model"] == "liquid/d1-20260930"
    assert receipt["alias_changed"] is True
    body = {"model": "liquid/d1", "questions": {"q0": {"criteria": runner.evidence.CRITERIA["cell"]}}}
    record = {"kind": "cell", "pair_source_ids": ["w0", "w1"], "source": {"words": []}}
    parsed = runner.parse_response(record, body, normalized, {"model": "liquid/d1"})
    assert parsed["probabilities"] == before["answers"]["q0"]["probabilities"]
    normalized["answers"]["q0"]["probabilities"]["same"] = .5
    with pytest.raises(ValueError, match="mass"):
        runner.parse_response(record, body, normalized, {"model": "liquid/d1"})


@pytest.mark.parametrize("returned", ["liquid/d1-20261001", "openai/gpt-6-luna-decisions-20261006", "liquid/d1-20260930-extra"])
def test_unknown_or_provider_fallback_refused(attestation: dict, returned: str) -> None:
    with pytest.raises(ValueError, match="Unrecognized exact alias"):
        replay.normalized_model({"model": returned}, "liquid/d1", attestation)


def test_authority_sha_and_wildcards_refused(tmp_path: Path) -> None:
    path = tmp_path / "aliases.json"
    write_json(path, {"schema": 1, "aliases": {"liquid/d1": ["liquid/d1-*"]}})
    with pytest.raises(ValueError, match="SHA"):
        replay.authority(path, "0" * 64)
    with pytest.raises(ValueError, match="wildcard"):
        replay.authority(path, sha(path.read_bytes()))


def test_explicit_null_is_not_an_attested_alias(attestation: dict) -> None:
    with pytest.raises(ValueError, match="Unrecognized exact alias"):
        replay.normalized_model({"model": None}, "liquid/d1", attestation)


@pytest.mark.parametrize("wrong_tag", [False, True])
def test_secondary_requires_original_verification_and_exact_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, wrong_tag: bool
) -> None:
    alias_path = tmp_path / "aliases.json"
    write_json(alias_path, {"schema": 1, "aliases": {"liquid/d1": ["liquid/d1-20260930"]}})
    cfg = {"model": "liquid/d1"}
    response_path = tmp_path / "question-0-response.json"
    response = {"entry": {"requested_model": "liquid/d1", "tag": "wrong" if wrong_tag else "exact", "request_sha256": "wire"}, "replayed": False, "result": {"model": "liquid/d1-20260930", "answers": {"q0": {"type": "choice", "choice": "same", "probabilities": {"same": .9, "separate": .9, "unresolved": 0}}}}}
    write_json(response_path, response)
    original = {"config": cfg, "rows": [{"index": 0, "id": "case", "status": "malformed_response", "tag": "exact", "wire_encoded_sha256": "wire", "response_sha256": sha(response_path.read_bytes())}], "status_counts": {"malformed_response": 1}, "rates": {}, "charges": {"effective_usd": .01}, "reported_metrics": {"wall_seconds": 1}}
    called = []

    def original_verify(*_args: object) -> dict:
        called.append("original_verified")
        return deepcopy(original)

    monkeypatch.setattr(replay.evaluator, "verify_run", original_verify)
    body = {"model": "liquid/d1", "questions": {"q0": {"criteria": runner.evidence.CRITERIA["cell"]}}}
    monkeypatch.setattr(replay.runner, "rebuild_request", lambda *_args: (body, {}))
    before = response_path.read_bytes()
    context = {"pool": tmp_path, "records": [{"kind": "cell", "pair_source_ids": ["w0", "w1"], "source": {}}]}
    if wrong_tag:
        with pytest.raises(ValueError, match="exact original fresh"):
            replay.replay(tmp_path, tmp_path / "unused", context, alias_path, sha(alias_path.read_bytes()))
    else:
        result = replay.replay(tmp_path, tmp_path / "unused", context, alias_path, sha(alias_path.read_bytes()))
        assert result["original_verified"] == original
        assert result["secondary_verified"]["status_counts"] == {"malformed_response": 1}
        assert result["secondary_verified"]["rows"][0]["secondary_parse_error"] == "ValueError"
        assert result["new_api_calls"] == 0
    assert called == ["original_verified"]
    assert response_path.read_bytes() == before
