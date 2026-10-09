"""Matched chat transport freezes complete source evidence without invented confidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from bench import anthropic_baseline as baseline
from bench.rolling_topology import configs, propose, union_candidates, union_request
from bench.rolling_topology_run import MODELS


def fixture(tmp_path: Path, *, ambiguous: bool = False) -> tuple[Path, Path]:
    page = {
        "id": "opaque",
        "page_size": [0, 0, 300, 500],
        "vector_candidates": [],
        "words": [
            {"id": "w0", "text": "Category", "bbox": [10, 10, 50, 20]},
            {"id": "w1", "text": "Measure", "bbox": [110, 10, 150, 20]},
            {"id": "w2", "text": "Node", "bbox": [10, 50, 35, 60]},
            {"id": "w3", "text": "12", "bbox": [170, 50, 180, 60]},
        ],
    }
    source_path = tmp_path / "source.json"
    source_raw = json.dumps({"pages": [page]}).encode()
    source_path.write_bytes(source_raw)
    candidates, _ = union_candidates(page, [], [propose(page, configs()[0])])
    directory = tmp_path / "frozen"
    directory.mkdir()
    records = []
    for index, model in enumerate(sorted(MODELS)):
        body = union_request(page, candidates, model)
        raw = json.dumps(body).encode()
        filename = f"request-{index}.json"
        (directory / filename).write_bytes(raw)
        records.append(
            {
                "id": "cohort0-page000",
                "route": "hosted_admission",
                "model": model,
                "request": filename,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "choices": list(body["questions"]["q0"]["criteria"]),
            }
        )
    manifest = {
        "models": sorted(MODELS),
        "records": records,
        "cohorts": [
            {
                "source_path": str(source_path),
                "source_sha256": hashlib.sha256(source_raw).hexdigest(),
                "pages": [{"id": "cohort0-page000", "source_id": "opaque", "candidates": candidates}],
            }
        ],
        "wall_seconds": 0.01,
        "cpu_seconds": 0.01,
        "peak_rss_bytes": 1,
        "measurement": "test",
    }
    (directory / "manifest.json").write_text(json.dumps(manifest))
    targets = tmp_path / "targets.json"
    targets.write_text(
        json.dumps(
            [
                {
                    "id": "opaque",
                    "kind": "ambiguous" if ambiguous else "borderless",
                    "binary_admission_eligible": not ambiguous,
                    "tables": [] if ambiguous else [candidates[0]["table"]],
                }
            ]
        )
    )
    return directory, targets


class FakeClient:
    """Retain bounded fake charge observations without credentials or network."""

    def __init__(self, path: Path, *, fail: bool = False, unknown: bool = False) -> None:
        """Use an isolated ledger."""
        path.mkdir()
        prices = path / "langfuse"
        prices.mkdir()
        (prices / "catalog-prices.json").write_text(
            json.dumps({"prices": {model: {"input": 1e-6, "output": 5e-6} for model in baseline.MODELS}})
        )
        self.ledger = path / "ledger.json"
        self.calls = 0
        self.fail = fail
        self.unknown = unknown

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int, reservation_usd: float) -> dict[str, Any]:
        """Return strict JSON or persist a simulated failed reservation."""
        assert max_body_bytes == 750_000
        assert reservation_usd == 1.25
        self.calls += 1
        entries = json.loads(self.ledger.read_bytes())["requests"] if self.ledger.exists() else []
        entry = {
            "index": len(entries),
            "tag": tag,
            "requested_model": body["model"],
            "accounted_usd": 1.25 if self.fail else 0.001,
            "cost_status": "reserved",
            "request_sha256": hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest(),
            "elapsed_ms": 2,
        }
        if not self.fail:
            entry["response_file"] = "fake.json"
        entries.append(entry)
        self.ledger.write_text(json.dumps({"requests": entries}))
        if self.fail:
            raise RuntimeError("Simulated failed provider")  # noqa: EM101, TRY003
        answer = {"answers": {"q0": {"choice": "c0"}}}
        return {
            "entry": entry,
            "replayed": False,
            "result": {
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(answer)}}],
                "usage": {} if self.unknown else {"cost": 0.001},
            },
        }


def test_exact_image_evidence_and_strict_schema() -> None:
    text = ' {"source_words": ["Unicode α"], "spacing": "  "} '
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA==", "detail": "high"}}
    question = {
        "type": "choice",
        "instructions": "Original instruction.",
        "criteria": {"c0": "Accept", "unresolved": "Abstain"},
    }
    original = {"state": [text, image], "questions": {"q0": question}}
    frozen = json.dumps(original)
    body = baseline.translate(original, baseline.MODELS[0])
    assert body["messages"][0]["content"] == question["instructions"]
    assert json.loads(body["messages"][1]["content"])["q0"]["criteria"] == question["criteria"]
    assert body["messages"][2]["content"] == [{"type": "text", "text": text}, image]
    assert json.dumps(original) == frozen
    schema = body["response_format"]["json_schema"]
    assert schema["strict"]
    assert schema["schema"]["properties"]["answers"]["properties"]["q0"]["properties"]["choice"]["enum"] == [
        "c0",
        "unresolved",
    ]
    assert body["reasoning"] == {"effort": "medium"}
    assert "temperature" not in body


@pytest.mark.parametrize(
    "answer",
    [
        {"answers": {"q0": {"choice": "bad"}}},
        {"answers": {"q0": {"choice": "c0", "confidence": 1}}},
        {"answers": {"q0": {"choice": "c0"}, "q1": {"choice": "c0"}}},
        {"choice": "c0"},
    ],
)
def test_reject_unscoped_or_fabricated_confidence(answer: dict[str, Any]) -> None:
    response = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(answer)}}]}
    with pytest.raises(ValueError, match=r"Unexpected|exactly|only|outside"):
        baseline.parse_choice(response, {"c0"})
    response["choices"][0]["finish_reason"] = "length"
    with pytest.raises(ValueError, match="finish"):
        baseline.parse_choice(response, {"c0"})


def test_prepare_freezes_before_targets_and_tamper_prevents_calls(tmp_path: Path) -> None:
    parent, targets = fixture(tmp_path)
    targets.unlink()
    directory = tmp_path / "baseline"
    prepared = baseline.prepare(parent, directory)
    assert prepared["requests"] == 3
    manifest, _ = baseline.verify(directory)
    assert manifest["models"] == list(baseline.MODELS)
    record = manifest["records"][0]
    (directory / record["request"]).write_text("{}")
    client = FakeClient(tmp_path / "ledger")
    with pytest.raises(ValueError, match="changed"):
        baseline.run(directory, [targets], client)
    assert client.calls == 0


def test_success_rates_and_unknown_cost_remain_partial(tmp_path: Path) -> None:
    parent, targets = fixture(tmp_path)
    directory = tmp_path / "baseline"
    baseline.prepare(parent, directory)
    client = FakeClient(tmp_path / "ledger", unknown=True)
    result = baseline.run(directory, [targets], client)
    assert client.calls == 3
    assert result["effective_usd"] is None
    assert result["known_partial_usd"] == 0
    assert result["unknown_cost_requests"] == 3
    assert result["source_conservation"]
    assert all(c["rows"][0]["scores"]["exact_page"] for c in result["cohorts"].values())
    baseline.run(directory, [targets], client)
    assert client.calls == 3
    assert "Matched Anthropic 5.5" in baseline.report(result)
    assert "Pages/HTTP minute" in baseline.report(result)


def test_persistent_failures_no_retries_and_prefix_cap(tmp_path: Path) -> None:
    parent, targets = fixture(tmp_path)
    directory = tmp_path / "baseline"
    baseline.prepare(parent, directory)
    client = FakeClient(tmp_path / "ledger", fail=True)
    result = baseline.run(directory, [targets], client)
    assert client.calls == 3
    assert set(result["stopped_models"]) == set(baseline.MODELS)
    baseline.run(directory, [targets], client)
    assert client.calls == 3
    baseline.wave_admission([{"tag": "other/", "accounted_usd": 100}])
    with pytest.raises(RuntimeError, match="prefix cap"):
        baseline.wave_admission([{"tag": baseline.TAG_PREFIX + "prior", "accounted_usd": 3.76}])


def test_catalog_reservation_bound_precedes_paid_calls(tmp_path: Path) -> None:
    parent, targets = fixture(tmp_path)
    directory = tmp_path / "baseline"
    baseline.prepare(parent, directory)
    client = FakeClient(tmp_path / "ledger")
    catalog_path = client.ledger.parent / "langfuse/catalog-prices.json"
    catalog = json.loads(catalog_path.read_bytes())
    catalog["prices"][baseline.MODELS[0]]["input"] = 1
    catalog_path.write_text(json.dumps(catalog))
    with pytest.raises(ValueError, match="exceeds"):
        baseline.run(directory, [targets], client)
    assert client.calls == 0


def test_complete_positive_cost_rates_and_partial_cost(tmp_path: Path) -> None:
    parent, targets = fixture(tmp_path)
    directory = tmp_path / "baseline"
    baseline.prepare(parent, directory)
    client = FakeClient(tmp_path / "ledger")
    result = baseline.run(directory, [targets], client)
    assert result["effective_usd"] == 0.003
    assert all(s["requested_pages_per_usd"] == 1000 for s in result["model_stats"].values())
    assert all(s["requested_pages_per_http_minute"] == 30000 for s in result["model_stats"].values())
    manifest, sources = baseline.verify(directory)
    calls = json.loads((directory / "hosted-results.json").read_bytes())["calls"]
    calls[0]["cost"]["effective_usd"] = None
    partial = baseline.evaluate(manifest, sources, calls, [0], [targets], set())
    assert partial["effective_usd"] is None
    assert partial["known_partial_usd"] == 0.002
    assert partial["unknown_cost_requests"] == 1
