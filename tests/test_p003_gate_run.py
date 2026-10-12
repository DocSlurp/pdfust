"""In-process fresh gate isolation and independently authenticated baseline checks."""

# Controlled heterogeneous transport records and private validation seams.
# ruff: noqa: EM101, TRY003
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import generalization_run as regions
from bench import p003_gate_run as gate
from bench import pipeline_run as pipeline
from bench.decision_gateway_vision import ENDPOINT
from bench.pipeline_assembly import native_state, propose
from bench.silver import canonical, sha, write_json
from test_pipeline_run import record

import pdfust


def baseline(tmp_path: Path) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    rec = record(tmp_path)
    directory = tmp_path / "ordinal"
    directory.mkdir()
    with pdfust.open(rec["pdf_path"]) as document:
        source = pipeline.source(document[0])
    generated = native_state(source)
    source["vector_candidates"] = []
    region = {
        "id": "r0",
        "boundary": "fixture",
        "kind": "detector_proposal",
        "context_complete": True,
        "bbox": [0, 0, 340, 300],
        "source_ids": [w["id"] for w in source["words"]],
        "source": {
            **deepcopy(source),
            "words": [{key: word[key] for key in ("id", "text", "bbox")} for word in source["words"]],
        },
    }
    original: dict[str, Any] = {
        "id": rec["id"],
        "status": "ok",
        "source": source,
        "region_plan": {"page_size": source["page_size"], "regions": [region]},
        "regions": [
            {"id": "r0", "bbox": region["bbox"], "boundary": "fixture", "route": "generated", "state": generated}
        ],
        "original_rotation": 0,
        "effective_rotation": 0,
        "source_conserved": True,
        "calls": [{"kind": "source_id_generation", "usage": {"prompt_tokens": 10}}],
        "route": "regions",
    }
    state, markdown = gate.compose_selected(original, {"r0": generated}, "original")
    original.update(tables=state["tables"], unresolved_ids=state["unresolved_ids"])
    config = {
        "processor": "regions",
        "assembly_method": "generate",
        "generation_format": "indices",
        "policy": "gated",
        "layout_detector": "yolo",
        "source_order": "original",
        "raster_rules": False,
    }
    code = directory / "code"
    code.mkdir()
    trusted = {}
    for name in gate.BASELINE_CODE:
        data = Path(gate.__file__).with_name(name).read_bytes()
        (code / name).write_bytes(data)
        trusted[name] = sha(data)
    write_json(
        directory / "frozen.json",
        {"config": config, "code_sha256": trusted, "records": [rec], "manifest_sha256": "fixture-manifest"},
    )
    write_json(directory / "report.json", {"config": config, "results": [original], "page_count": 1})
    write_json(directory / f"{rec['id']}-result.json", original)
    write_json(directory / f"{rec['id']}-structure.json", state)
    write_json(directory / f"{rec['id']}-request-0.json", {"model": "historical", "source": "fixture"})
    (directory / f"{rec['id']}.md").write_text(markdown)
    trusted_path = tmp_path / "trusted.json"
    write_json(trusted_path, trusted)
    return directory, trusted_path, rec, original


def settings(directory: Path) -> dict[str, Any]:
    return {
        "baseline_directory": str(directory),
        "baseline_source_order": "original",
        "gate_image": True,
        "gate_image_edge": 128,
        "gate_image_mode": "grayscale8",
        "gate_packet": "compact",
        "gate_instructions": "visual_schema",
        "gate_row_evidence": False,
        "answer_tokens": 2048,
        "model": "cloudflare/clef-flash",
        "run_id": "fresh",
        "campaign": "P003",
    }


@pytest.mark.parametrize("choice", ["table", "prose", "unresolved"])
def test_fresh_gate_reuses_only_declared_generation_or_exact_c0(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
) -> None:
    directory, _trusted, rec, original = baseline(tmp_path)
    calls = []

    def call(_client: object, body: dict[str, Any], tag: str) -> dict[str, Any]:
        calls.append((body, tag))
        return {"answer": {"choice": choice}, "usage": {"prompt_tokens": 42}}

    monkeypatch.setattr(pipeline, "call", call)
    monkeypatch.setattr(regions, "generate_region", lambda *_a, **_k: pytest.fail("Generation repeated"))
    monkeypatch.setattr(pipeline, "source", lambda *_a, **_k: pytest.fail("Source extraction repeated"))
    output = tmp_path / "fresh"
    output.mkdir()
    result = gate.process(rec, settings(directory), output, object())
    assert result["status"] == "ok"
    assert len(result["calls"]) == 1
    assert result["historical_calls"] == original["calls"]
    assert result["tables"] == (original["tables"] if choice == "table" else [])
    assert result["source_conserved"] is True
    assert result["evaluation_scope"] == "conditional_on_frozen_generation"
    region = result["regions"][0]
    assert region["admission_reason"] == choice
    assert region["reported_usage"] == {"prompt_tokens": 42}
    assert region["image"]["image_mode"] == "L"
    assert region["evidence"]["provider_state_truncation_risk"] is True
    assert region["selected_state_sha256"] == sha(canonical(region["state"]))
    body = json.loads((output / f"{rec['id']}-request-0.json").read_text())
    assert body == calls[0][0]
    assert calls[0][1] == f"P003/fresh/{rec['id']}/r0/0"


def test_gate_failure_keeps_receipt_and_page_failure_without_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory, _trusted, rec, _original = baseline(tmp_path)

    def fail(*_args: object) -> dict[str, Any]:
        raise RuntimeError("Transport failed")

    monkeypatch.setattr(pipeline, "call", fail)
    output = tmp_path / "fresh"
    output.mkdir()
    result = gate.process(rec, settings(directory), output, object())
    assert result["status"] == "error"
    assert result["gate_status"] == "failed_atomic"
    assert result["tables"] == []
    assert result["regions"][0]["admission_reason"] == "pending"
    assert "state" not in result["regions"][0]
    assert (output / f"{rec['id']}-request-0.json").is_file()
    assert not (output / f"{rec['id']}-structure.json").exists()


def test_fallback_matches_existing_c0_without_proposal_ranking(tmp_path: Path) -> None:
    _directory, _trusted, _rec, original = baseline(tmp_path)
    source = original["region_plan"]["regions"][0]["source"]
    assert gate.fallback_state(source) == propose(source)[0]


def test_baseline_requires_independent_code_and_complete_source_ownership(tmp_path: Path) -> None:
    directory, trusted, _rec, original = baseline(tmp_path)
    gate.authenticate(directory, json.loads(trusted.read_text()))
    with pytest.raises(ValueError, match="independent"):
        gate.authenticate(directory, {})
    with pytest.raises(ValueError, match="Untrusted"):
        gate.authenticate(directory, {"pipeline_regions.py": "self-attested"})
    state_path = directory / f"{original['id']}-structure.json"
    state = json.loads(state_path.read_text())
    state["tables"][0]["values"][0][0] = "invented"
    write_json(state_path, state)
    with pytest.raises(ValueError, match="Retained complete structure"):
        gate.authenticate(directory, json.loads(trusted.read_text()))


def test_unknown_and_reserved_costs_never_become_complete_totals() -> None:
    result = gate.charges(
        [
            {"cost_status": "unknown", "accounted_usd": 0.1},
            {"cost_status": "reserved", "accounted_usd": 0.3},
            {"cost_status": "reported", "accounted_usd": 0.05, "provider_reported_usd": 0.05},
        ]
    )
    assert result["effective_usd"] is None
    assert result["provider_reported_usd"] is None
    assert result["known_partial_effective_usd"] == 0.05
    assert result["unresolved_reserved_usd"] == 0.3


def test_full_run_copies_complete_authenticated_baseline_and_labels_incremental_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, trusted, rec, original = baseline(tmp_path)
    ledger = tmp_path / "ledger.json"
    write_json(ledger, {"requests": []})
    client = SimpleNamespace(ledger=ledger)
    monkeypatch.setattr(pipeline, "call", lambda *_args: {"answer": {"choice": "table"}, "usage": {}})
    result = gate.run(directory, trusted, tmp_path / "fresh", {**settings(directory), "run_hosted": True}, client)
    assert result["page_count"] == 1
    assert result["complete_output_pages"] == 1
    assert result["baseline_report"]["results"] == [original]
    assert result["pages_per_minute"] is None
    assert result["incremental_gate"]["cost_scope"].startswith("Fresh gate")
    frozen = json.loads((tmp_path / "fresh/frozen.json").read_text())
    assert frozen["baseline"]["trusted_code_manifest_sha256"] == sha(trusted.read_bytes())
    assert frozen["baseline"]["file_sha256"][f"{rec['id']}-result.json"] == sha(
        (directory / f"{rec['id']}-result.json").read_bytes(),
    )


def test_source_policy_bypass_and_baseline_failures_remain_in_denominator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, _trusted, rec, original = baseline(tmp_path)
    original["region_plan"]["regions"][0]["kind"] = "residual"
    original["regions"][0].update(route="detector_residual_retained", state=native_state(original["source"]))
    write_json(directory / f"{rec['id']}-result.json", original)
    monkeypatch.setattr(pipeline, "call", lambda *_a: pytest.fail("Bypassed region transmitted"))
    output = tmp_path / "fresh"
    output.mkdir()
    result = gate.process(rec, settings(directory), output, object())
    assert result["status"] == "ok"
    assert result["calls"] == []
    assert result["regions"][0]["admission_reason"] == "detector_residual_retained"
    original.update(status="error", error_type="GenerationError", error="malformed generation")
    write_json(directory / f"{rec['id']}-result.json", original)
    failed = tmp_path / "failed"
    failed.mkdir()
    result = gate.process(rec, settings(directory), failed, object())
    assert result["status"] == "error"
    assert result["gate_status"] == "baseline_failed"
    assert result["calls"] == []
    assert result["error_type"] == "GenerationError"


def test_text_gate_performs_no_raster_render(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory, _trusted, rec, _original = baseline(tmp_path)
    monkeypatch.setattr(regions, "region_image", lambda *_a: pytest.fail("Text gate rendered pixels"))
    monkeypatch.setattr(pipeline, "call", lambda *_a: {"answer": {"choice": "unresolved"}})
    output = tmp_path / "fresh"
    output.mkdir()
    config = {**settings(directory), "gate_image": False, "gate_image_mode": "rgb"}
    result = gate.process(rec, config, output, object())
    assert result["status"] == "ok"
    assert result["regions"][0]["image"] == {"image": "none", "gate_image_mode": "rgb"}
    body = json.loads((output / f"{rec['id']}-request-0.json").read_text())
    assert isinstance(body["state"], str)


def test_fresh_response_archive_preserves_exact_failed_attempt_bytes(tmp_path: Path) -> None:
    output = tmp_path / "fresh"
    output.mkdir()
    (output / "page-request-0.json").write_text("{}")
    raw = b'{ "answers": {"q0": "malformed"} }\n'
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "response-001.json").write_bytes(raw)
    entry = {
        "tag": "P003/fresh/page/r0/0",
        "index": 1,
        "request_sha256": "wirehash",
        "response_file": "response-001.json",
    }
    client = SimpleNamespace(directory=shared)
    artifacts = gate.archive_responses(client, output, [entry])
    assert (output / "page-response-0.json").read_bytes() == raw
    assert artifacts["page-response-0.json"]["sha256"] == sha(raw)
    entry["tag"] = "P003/other/page/r0/0"
    with pytest.raises(ValueError, match="run scope"):
        gate.archive_responses(client, output, [entry])


def test_no_hosted_optin_never_constructs_a_client(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="opt-in"):
        gate.run(tmp_path / "missing", tmp_path / "trust", tmp_path / "output", {"model": "irrelevant"})


@pytest.mark.parametrize("model", gate.GATEWAY_MODELS)
def test_gateway_wire_replay_uses_actual_endpoint_and_boundless_laya(
    tmp_path: Path,
    model: str,
) -> None:
    directory, _trusted, _rec, original = baseline(tmp_path)
    config = {
        **settings(directory),
        "gate_provider": "vercel",
        "model": model,
        "gate_image": model == "liquid/d1",
        "gate_image_mode": "rgb",
    }
    region = original["region_plan"]["regions"][0]
    url = "data:image/png;base64,AA==" if config["gate_image"] else None
    body, evidence = gate.gate_request(region, config, url)
    raw: dict[str, Any]
    if model == "liquid/d1":
        assert evidence["endpoint"].endswith("/v1/decisions")
        assert body["input"][0]["content"][1] == {"type": "input_image", "image_url": url, "detail": "high"}
        raw = {
            "answers": [
                {
                    "name": "q0",
                    "type": "choice",
                    "choice": "table",
                    "probabilities": [
                        {"value": key, "probability": float(key == "table")} for key in ("table", "prose", "unresolved")
                    ],
                }
            ]
        }
    else:
        assert evidence["endpoint"].endswith("/typesafe/v1/systemone")
        assert body["providerOptions"] == {"gateway": {"only": ["boundless"]}}
        assert isinstance(body["state"], str)
        raw = {
            "answers": {
                "q0": {"type": "choice", "choice": "table", "probabilities": {"table": 1, "prose": 0, "unresolved": 0}}
            }
        }
    assert gate.parse_gate_response(body, raw, config)["choice"] == "table"
    assert evidence["request_sha256"] == sha(json.dumps(body, separators=(",", ":")).encode())
    assert evidence["request_identity_sha256"] != evidence["request_sha256"]


def test_gateway_process_uses_serial_shared_client_without_openrouter_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, _trusted, rec, original = baseline(tmp_path)
    ledger = tmp_path / "ledger.json"
    write_json(ledger, {"requests": []})
    requests = []

    def request(body: dict[str, Any], **kwargs: object) -> dict[str, Any]:
        requests.append((body, kwargs))
        return {
            "entry": {},
            "replayed": False,
            "result": {
                "answers": {
                    "q0": {
                        "type": "choice",
                        "choice": "table",
                        "probabilities": {"table": 1, "prose": 0, "unresolved": 0},
                    }
                }
            },
        }

    client = SimpleNamespace(ledger=ledger, request=request)
    monkeypatch.setattr(pipeline, "call", lambda *_a: pytest.fail("Gateway reached OpenRouter"))
    output = tmp_path / "fresh"
    output.mkdir()
    config = {**settings(directory), "gate_provider": "vercel", "model": "liquid/d1"}
    result = gate.process(rec, config, output, client)
    assert result["status"] == "ok"
    assert result["tables"] == original["tables"]
    assert requests[0][0]["model"] == "liquid/d1"
    assert requests[0][1]["replay"] is False
    assert result["regions"][0]["image"]["image_mode"] == "L"


def test_gateway_circuit_breaker_prevents_another_request(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    write_json(ledger, {"requests": []})
    calls = []

    def fail(*_args: object, **_kwargs: object) -> dict[str, Any]:
        calls.append(True)
        raise RuntimeError("Mocked transport failure")

    client = SimpleNamespace(ledger=ledger, request=fail)
    with pytest.raises(RuntimeError, match="Mocked"):
        gate.gateway_call(client, {}, "P003/fresh/page/r0/0")
    with pytest.raises(RuntimeError, match="stopped"):
        gate.gateway_call(client, {}, "P003/fresh/other/r0/0")
    assert len(calls) == 1


@pytest.mark.parametrize(
    "config_delta",
    [
        {"model": "liquid/d1", "transport_concurrency": 3},
        {"model": "convaiinnovations/laya", "gate_image": True},
    ],
)
def test_gateway_parallel_and_laya_images_refused_before_output_creation(
    tmp_path: Path,
    config_delta: dict[str, Any],
) -> None:
    directory, trusted, _rec, _original = baseline(tmp_path)
    config = {**settings(directory), "run_hosted": True, "gate_provider": "vercel", **config_delta}
    with pytest.raises(ValueError, match="Gateway requires"):
        gate.run(directory, trusted, tmp_path / "fresh", config, object())
    assert not (tmp_path / "fresh").exists()


def test_gateway_run_freezes_gateway_catalog_without_openrouter_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory, trusted, _rec, _original = baseline(tmp_path)
    ledger = tmp_path / "ledger.json"
    write_json(ledger, {"requests": []})
    catalog = {"fetched_at": "fixture", "prices": {"liquid/d1": {"input": 0.1, "output": 0.2}}}
    client = SimpleNamespace(ledger=ledger, endpoint=ENDPOINT, catalog=catalog)
    monkeypatch.setattr(gate, "gateway_call", lambda *_a: {"answer": {"choice": "table"}, "usage": {}})
    monkeypatch.setattr(pipeline, "call", lambda *_a: pytest.fail("Gateway reached OpenRouter"))
    config = {**settings(directory), "run_hosted": True, "gate_provider": "vercel", "model": "liquid/d1"}
    output = tmp_path / "fresh"
    result = gate.run(directory, trusted, output, config, client)
    assert result["complete_output_pages"] == 1
    frozen = json.loads((output / "frozen.json").read_text())
    assert frozen["gateway_pricing"]["catalog"] == catalog
    assert frozen["gateway_pricing"]["endpoint"] == ENDPOINT
    assert frozen["gateway_pricing_sha256"] == sha((output / "gateway-prices.json").read_bytes())
