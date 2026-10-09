"""Bounded union runs use only frozen generic menus and conserve source IDs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import bench.rolling_topology_run as runner
import pytest
from bench.rolling_topology import configs, propose, union_candidates, union_request
from bench.rolling_topology_run import MODELS, TAG_PREFIX, evaluate, materialize, run, verify, wave_admission


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
    """Retain accounting like the shared client without keys or network."""

    def __init__(self, path: Path, *, fail: bool = False) -> None:
        """Create isolated fake accounting."""
        self.ledger = path / "ledger.json"
        path.mkdir(exist_ok=True)
        self.calls = 0
        self.fail = fail

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict[str, Any]:
        """Return one strict Choice or persist a simulated failure."""
        assert max_body_bytes > 0
        self.calls += 1
        entries = json.loads(self.ledger.read_bytes())["requests"] if self.ledger.exists() else []
        entry = {
            "index": len(entries),
            "tag": tag,
            "requested_model": body["model"],
            "accounted_usd": 0.30,
            "request_sha256": hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest(),
            "elapsed_ms": 2,
        }
        if not self.fail:
            entry["response_file"] = "retained-test-response.json"
        entries.append(entry)
        self.ledger.write_text(json.dumps({"requests": entries}))
        if self.fail:
            message = "simulated provider failure"
            raise RuntimeError(message)
        options = body["questions"]["q0"]["criteria"]
        return {
            "entry": entry,
            "replayed": False,
            "result": {
                "usage": {"cost": 0.001},
                "answers": {
                    "q0": {"type": "choice", "choice": "c0", "probabilities": {k: float(k == "c0") for k in options}},
                },
            },
        }


def test_selected_structure_and_ambiguous_unscored(tmp_path: Path) -> None:
    directory, targets = fixture(tmp_path, ambiguous=True)
    manifest, sources = verify(directory)
    calls = [
        {"model": model, "id": "cohort0-page000", "status": "ok", "answer": {"choice": "c0"}}
        for model in manifest["models"]
    ]
    summary = evaluate(manifest, sources, calls, [0], [targets], set())
    for cohort in summary["cohorts"].values():
        assert cohort["slices"]["ambiguous"]["scored_pages"] == 0
        assert cohort["slices"]["ambiguous"]["accepted_pages"] == 1
        assert cohort["rows"][0]["scores"] is None
    page = sources[0]["opaque"]
    with pytest.raises(ValueError, match="frozen source menu"):
        materialize(page, manifest["cohorts"][0]["pages"][0]["candidates"], "bad")


def test_hash_verification_precedes_calls(tmp_path: Path) -> None:
    directory, targets = fixture(tmp_path)
    (directory / "request-0.json").write_text("{}")
    client = FakeClient(tmp_path / "ledger")
    with pytest.raises(ValueError, match="changed"):
        run(directory, [targets], client)
    assert client.calls == 0


def test_persistent_reservation_cap_and_success_conservation(tmp_path: Path) -> None:
    directory, targets = fixture(tmp_path)
    client = FakeClient(tmp_path / "ledger")
    summary = run(directory, [targets], client)
    assert client.calls == 1
    assert summary["budget_stopped"]
    assert summary["source_conservation"]
    assert summary["effective_usd"] == 0.001
    rerun = run(directory, [targets], client)
    assert client.calls == 1
    assert rerun["unique_requests"] == 1
    wave_admission([{"tag": "other-wave/", "accounted_usd": 10}])
    with pytest.raises(RuntimeError, match="prefix cap"):
        wave_admission([{"tag": TAG_PREFIX + "prior", "accounted_usd": 0.3}])


def test_failure_stops_model_persistently(tmp_path: Path) -> None:
    directory, targets = fixture(tmp_path)
    client = FakeClient(tmp_path / "ledger", fail=True)
    result = run(directory, [targets], client)
    assert client.calls == 1
    assert len(result["stopped_models"]) == 1
    run(directory, [targets], client)
    assert client.calls == 1


def test_offline_cli_uses_retained_calls_without_constructing_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    directory, targets = fixture(tmp_path)
    client = FakeClient(tmp_path / "ledger")
    original = run(directory, [targets], client)
    retained_before = (directory / "hosted-results.json").read_bytes()
    report_path = tmp_path / "report.md"

    def forbidden_client() -> None:
        pytest.fail("Offline report must not construct a credential-reading hosted client")

    monkeypatch.setattr(runner, "DecisionClient", forbidden_client)
    monkeypatch.setattr(
        "sys.argv",
        [
            "rolling_topology_run",
            "--directory",
            str(directory),
            "--cohorts",
            "0",
            "--targets",
            str(targets),
            "--report",
            str(report_path),
        ],
    )
    runner.main()
    printed = json.loads(capsys.readouterr().out)
    assert printed["unique_requests"] == original["unique_requests"] == 1
    assert printed["effective_usd"] == original["effective_usd"] == 0.001
    assert "Unique requests 1;" in report_path.read_text()
    assert "Pages/USD" in report_path.read_text()
    assert (directory / "hosted-results.json").read_bytes() == retained_before
    stats = next(s for s in original["model_stats"].values() if s["requested_pages"])
    assert stats["requested_pages_per_usd"] == 1000
    assert stats["requested_pages_per_http_minute"] == 30000
    assert client.calls == 1
