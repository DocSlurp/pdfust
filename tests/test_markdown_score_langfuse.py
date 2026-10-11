from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
from bench import decision_langfuse, markdown_score_langfuse
from bench.markdown_score_langfuse import DATASET, _redact, item_id, run_name, sync

if TYPE_CHECKING:
    from pathlib import Path

CONFIG = {
    "LANGFUSE_PUBLIC_KEY": "test-public",
    "LANGFUSE_SECRET_KEY": "test-secret",
    "LANGFUSE_BASE_URL": "https://example.test",
}
CASE = {"source": "synthetic", "notes": "one image", "truth": {"images": 1, "text": ["Caption"]}}


def artifacts(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    root = tmp_path / "markdown-scores"
    (root / "inputs").mkdir(parents=True)
    (root / "inputs" / "case-a.pdf").write_bytes(b"%PDF-1.7 synthetic")
    (root / "truth.json").write_text(json.dumps({"case-a": CASE}))
    output = root / "outputs" / "tool-x"
    output.mkdir(parents=True)
    (output / "case-a.md").write_text("Caption\n\n![](data:image/png;base64,iVBORw0KGgo=)\n")
    meta = {
        "tool": "tool-x",
        "options": "defaults",
        "versions": {"tool-x": "1.0"},
        "peak_rss_mib": 10.0,
        "source": {"commit": "a" * 40, "dirty": True},
        "cases": {"case-a": {"wall_ms": 5.0, "cpu_ms": 4.0, "error": None}},
    }
    (output / "run.json").write_text(json.dumps(meta))
    report = {
        "commit": "b" * 40,
        "dirty": False,
        "tools": {
            "tool-x": {
                "meta": meta,
                "overall": 0.5,
                "categories": {"Text": {"score": 1.0, "checks": 1}, "Images": {"score": 0.0, "checks": 2}},
                "cases": {"case-a": {"Text": [1.0], "Images": [0.0, 0.0]}},
            }
        },
    }
    return root, report


def test_redact_hashes_inline_payloads_and_bounds_text() -> None:
    redacted = _redact("![](data:image/png;base64,QUJD) " + "x" * 70_000)
    assert "QUJD" not in redacted
    assert "data:image/png;sha256=" in redacted
    assert redacted.endswith("chars]")


def test_identifiers_follow_fixture_content_and_producing_checkout() -> None:
    first = item_id("case-a", CASE, "1" * 64)
    assert first == item_id("case-a", CASE, "1" * 64)
    assert first != item_id("case-a", CASE, "2" * 64)
    meta = {"source": {"commit": "c" * 40, "dirty": True}}
    assert run_name("tool-x", meta, {"case-a": "x"}).startswith("tool-x @ cccccccccccc-dirty out:")
    assert run_name("tool-x", {}, {"case-a": "x"}).startswith("tool-x @ unknown out:")


def test_sync_is_disabled_without_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in CONFIG:
        monkeypatch.delenv(key, raising=False)
    root, report = artifacts(tmp_path)
    assert sync(tmp_path, root, report) == {"status": "disabled"}


def test_sync_sends_dataset_run_and_scores_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, report = artifacts(tmp_path)
    calls: list[tuple[str, str, Any]] = []

    def fake_http(url: str, method: str = "GET", body: object = None, config: object = None) -> dict[str, Any]:
        assert config is not None
        calls.append((method, url.removeprefix("https://example.test"), body))
        if "/runs/" in url:
            return {"id": "run-1"}
        if url.endswith("/otel/v1/traces"):
            return {}
        return {"data": [], "meta": {"totalPages": 1}}

    monkeypatch.setattr(decision_langfuse, "_configuration", lambda _root: CONFIG)
    monkeypatch.setattr(decision_langfuse, "_http", fake_http)
    status = sync(tmp_path, root, report)
    assert status["status"] == "ok"
    run = status["runs"]["tool-x"]
    assert run["status"] == "exported"
    assert run["run"].startswith("tool-x @ aaaaaaaaaaaa-dirty")
    sent = json.dumps([body for _, _, body in calls])
    assert "iVBORw0KGgo" not in sent

    paths = [path for _, path, _ in calls]
    assert paths.count("/api/public/otel/v1/traces") == 1
    item = next(body for _, path, body in calls if path == "/api/public/dataset-items")
    assert item["datasetName"] == DATASET
    assert item["expectedOutput"] == CASE["truth"]
    run_item = next(body for _, path, body in calls if path == "/api/public/dataset-run-items")
    assert run_item["datasetItemId"] == item["id"]
    scores = [body for _, path, body in calls if path == "/api/public/scores"]
    trace_scores = {s["name"]: s["value"] for s in scores if "traceId" in s}
    assert trace_scores == {"md.text": 1.0, "md.images": 0.0, "md.case_mean": pytest.approx(1 / 3)}
    run_scores = {s["name"]: s["value"] for s in scores if "datasetRunId" in s}
    assert run_scores == {"md.text": 1.0, "md.images": 0.0, "md.overall": 0.5}

    calls.clear()
    monkeypatch.setattr(markdown_score_langfuse, "_MARKERS", "markers")
    assert sync(tmp_path, root, report)["runs"]["tool-x"]["status"] == "exported"
    calls.clear()
    assert sync(tmp_path, root, report)["runs"]["tool-x"]["status"] == "replayed"
    assert "/api/public/otel/v1/traces" not in [path for _, path, _ in calls]


def test_sync_errors_are_sanitized_and_nonfatal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, report = artifacts(tmp_path)

    def failing_http(*_args: object, **_kwargs: object) -> dict[str, Any]:
        raise ConnectionRefusedError(CONFIG["LANGFUSE_SECRET_KEY"])

    monkeypatch.setattr(decision_langfuse, "_configuration", lambda _root: CONFIG)
    monkeypatch.setattr(decision_langfuse, "_http", failing_http)
    assert sync(tmp_path, root, report) == {"status": "error", "error": "ConnectionRefusedError"}
