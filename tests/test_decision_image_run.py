"""Offline batch isolation, frozen identity and spend admission regression checks."""

from __future__ import annotations

import hashlib
import io
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import decision_image_run as runner
from bench.decision_context_cases import context_cases
from PIL import Image


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    """Generate only repository-authored CPU DEV controls."""
    return context_cases()


def test_batch_observations_and_gold_isolation(cases: list[dict]) -> None:
    batch = runner.batch_request(cases[:6], "test-model", [None] * 6)
    altered = deepcopy(cases[:6])
    for case in altered:
        case["gold"] = {"secret": "PRIVATE_GOLD_MARKER"}
        case["family"] = case["id"] = "PRIVATE_GOLD_MARKER"
    assert batch == runner.batch_request(altered, "test-model", [None] * 6)
    assert "PRIVATE_GOLD_MARKER" not in json.dumps(batch)
    assert set(batch["questions"]) == {f"q{i}" for i in range(6)}
    for index in range(6):
        assert f"corresponding observation q{index}" in batch["questions"][f"q{index}"]["instructions"]
        assert f"Observation q{index}:" in batch["state"][index * 3]
    with pytest.raises(ValueError, match="six"):
        runner.batch_request([], "test-model", [])


def frozen_batch(tmp_path: Path, cases: list[dict]) -> dict:
    """Build one frozen request using the exact hosted-client JSON encoding."""
    body = runner.batch_request(cases[:6], "test-model", [None] * 6)
    data = runner.encode(body)
    key = hashlib.sha256(data).hexdigest()
    path = tmp_path / "request.json"
    path.write_bytes(data)
    return {
        "models": ["test-model"],
        "prices": {},
        "batches": [
            {
                "model": "test-model",
                "scope": "region",
                "arm": "current",
                "offset": 0,
                "case_indices": list(range(6)),
                "case_ids": [c["id"] for c in cases[:6]],
                "request_sha256": key,
                "request_file": path.name,
                "request_bytes": len(data),
            }
        ],
    }


def test_budget_refuses_before_client_request(tmp_path: Path, cases: list[dict]) -> None:
    manifest = frozen_batch(tmp_path, cases)
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"requests": [{"request_sha256": "unrelated", "accounted_usd": 2.0}]}))
    (tmp_path / "results.json").write_text(json.dumps({"schema": 1, "wave_start": 0, "batches": []}))
    calls = []
    client = SimpleNamespace(ledger=ledger, request=lambda *args, **_kwargs: calls.append(args))
    report = runner.run(tmp_path, manifest, client=client)
    assert calls == []
    assert report["budget_exhausted"]
    assert report["batches"][0]["status"] == "unattempted"
    with pytest.raises(RuntimeError, match="budget"):
        runner.wave_admission([{"accounted_usd": 1.8}], 0)


def test_hash_validation_precedes_client_request(tmp_path: Path, cases: list[dict]) -> None:
    manifest = frozen_batch(tmp_path, cases)
    (tmp_path / "request.json").write_text("tampered")
    with pytest.raises(ValueError, match="hash"):
        runner.run(tmp_path, manifest, client=object())


def test_first_failure_stops_model_and_retains_reservation(tmp_path: Path, cases: list[dict]) -> None:
    manifest = frozen_batch(tmp_path, cases)
    duplicate = deepcopy(manifest["batches"][0])
    duplicate["offset"] = 6
    duplicate["case_indices"] = list(range(6, 12))
    manifest["batches"].append(duplicate)
    ledger = tmp_path / "ledger.json"
    calls = []

    def fail(body: dict[str, Any], **kwargs: Any) -> None:  # noqa: ANN401
        calls.append(kwargs)
        ledger.write_text(
            json.dumps(
                {
                    "requests": [
                        {
                            "request_sha256": hashlib.sha256(runner.encode(body)).hexdigest(),
                            "index": 0,
                            "accounted_usd": 0.3,
                            "error": "HTTP 400",
                        }
                    ]
                }
            )
        )
        message = "hosted call failed (HTTP 400); reservation retained"
        raise RuntimeError(message)

    client = SimpleNamespace(ledger=ledger, request=fail)
    report = runner.run(tmp_path, manifest, client=client)
    assert len(calls) == 1
    assert calls[0]["max_body_bytes"] == 750_000
    assert report["batches"][0]["status"] == "failed"
    assert report["batches"][0]["entry"]["accounted_usd"] == 0.3
    assert report["batches"][1]["status"] == "unattempted"
    resumed = runner.run(tmp_path, manifest, client=client)
    assert resumed["batches"][0]["status"] == "failed"
    assert len(calls) == 1


def test_silver_fixed_image_question_and_variable_last_batch() -> None:
    variants = [{"data": b"fake-png"}] * 5
    body = runner.silver_batch_request(variants, "test-model")
    assert len(body["questions"]) == 5
    assert "at least two rows and two columns" in body["questions"]["q0"]["instructions"]
    assert "pdf_sha256" not in json.dumps(body)
    assert "expected_document" not in json.dumps(body)


def test_silver_confusion_and_positive_cost_precedence() -> None:
    rows = [
        {
            "case_id": str(i),
            "expected_document": expected,
            "answer": {"choice": choice},
            "score": {"region_exact": expected == choice, "record_f1": None},
        }
        for i, (expected, choice) in enumerate([("A", "A"), ("A", "unresolved"), ("B", "A"), ("B", "B")])
    ]
    manifest = {"silver_directory": "fake", "prices": {"m": {"input": 0.1, "output": 0.1}}}
    report = {
        "batches": [
            {
                "model": "m",
                "scope": "page",
                "arm": "rgb8-128",
                "offset": 0,
                "status": "ok",
                "case_indices": list(range(4)),
                "observations": rows,
                "request_bytes": 100,
                "entry": {"index": 0, "accounted_usd": 0.02, "cost_status": "provider-reported USD"},
                "usage": {"cost": 0, "input_tokens": 100, "output_tokens": 1},
            }
        ]
    }
    result = runner.summarize(manifest, report)
    row = result["rows"][0]
    assert (row["tp"], row["fp"], row["fn"], row["tn"]) == (1, 1, 1, 1)
    assert row["precision"] == row["recall"] == row["specificity"] == 0.5
    assert row["unresolved"] == 1
    assert result["effective_usd"] == 0.02


def test_clef_provider_bounds_and_large_image_batch_splitting(cases: list[dict]) -> None:
    clef = runner.admitted_batches(cases[:6], [None] * 6, "cloudflare/clef", silver=False)
    assert sum(len(chosen) for _, chosen, _, _ in clef) == 6
    assert all(len(body["questions"]) <= 4 for _, _, _, body in clef)
    assert all(sum(len(v.encode()) for v in body["state"] if isinstance(v, str)) <= 4000 for _, _, _, body in clef)
    images = [{"data": b"x" * 120_000}] * 6
    batches = runner.admitted_batches(cases[:6], images, "test-model", silver=True)
    assert len(batches) > 1
    assert sum(len(chosen) for _, chosen, _, _ in batches) == 6
    assert all(len(runner.encode(body)) <= runner.MAX_BODY_BYTES for _, _, _, body in batches)


def test_clef_lossless_transport_preserves_pixels(monkeypatch: pytest.MonkeyPatch) -> None:
    image = Image.new("RGB", (20, 20), (20, 90, 180))
    raw = io.BytesIO()
    image.save(raw, format="PNG")
    monkeypatch.setattr(runner, "CLEF_PNG_BYTES", 1)
    converted = runner.provider_transport({"data": raw.getvalue()}, "cloudflare/clef")
    assert converted is not None
    assert converted["mime"] == "image/webp"
    with Image.open(io.BytesIO(converted["data"])) as decoded:
        assert image.tobytes() == decoded.convert("RGB").tobytes()
    request = runner.silver_batch_request([converted], "cloudflare/clef")
    assert request["state"][1]["image_url"]["url"].startswith("data:image/webp;base64,")
