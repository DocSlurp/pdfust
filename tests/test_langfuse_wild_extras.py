from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

import pytest
from bench import langfuse_backfill
from bench.langfuse_wild_extras import (
    audit_plan,
    audit_scores,
    dataset_name,
    quirk_item_id,
    quirk_items,
    raster_items,
    real_world_items,
    sync_all,
    vision_document_scores,
    vision_plan,
    wild_v2_items,
)

if TYPE_CHECKING:
    from pathlib import Path


class FakeClient(langfuse_backfill.Client):
    """Record requests instead of sending them."""

    def __init__(self) -> None:
        """Bind a dummy endpoint."""
        super().__init__({"LANGFUSE_BASE_URL": "https://example.test"})
        self.sent: list[tuple[str, Any]] = []

    def post(self, path: str, body: object) -> dict[str, Any]:
        """Record one POST."""
        self.sent.append((path, body))
        return {}

    def get(self, path: str) -> dict[str, Any]:
        """Serve an empty dataset listing."""
        assert "HELD-OUT" not in path
        return {"data": [], "meta": {"totalPages": 1}}

    def bodies(self, path: str) -> list[Any]:
        """Return recorded bodies sent to ``path``."""
        return [body for sent, body in self.sent if sent == path]


def _hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:32]


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _pdf(path: Path, data: bytes = b"%PDF-1.7 x") -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(langfuse_backfill, "MARKERS", tmp_path / "markers")
    root = tmp_path / "artifacts"
    wild = root / "wild-v1"
    _write(wild / "docs" / "d1" / "truth.json", {"blocks": []})
    doc_sha = _pdf(wild / "quirks" / "q1" / "d1.pdf", b"doc")
    raw_sha = _pdf(wild / "quirks" / "q2" / "raw-d1.pdf", b"raw")
    cases = [
        {
            "case_id": "q1/d1",
            "quirk_id": "q1",
            "family": "producer",
            "doc_id": "d1",
            "source_doc_id": "d1",
            "path": "quirks/q1/d1.pdf",
            "tool": "gs",
            "measured": {"sha256": doc_sha},
        },
        {
            "case_id": "q2/raw-d1",
            "quirk_id": "q2",
            "family": "font_encoding",
            "doc_id": None,
            "source_doc_id": "d1",
            "path": "quirks/q2/raw-d1.pdf",
            "tool": "raw",
            "expected_text": "secret truth text",
            "expected_lines": ["a", "b"],
            "measured": {"sha256": raw_sha},
        },
    ]
    _write(wild / "quirks" / "manifest.json", {"case_count": 2, "cases": cases})
    _write(
        wild / "variants" / "d1" / "raster.json",
        {
            "source": {"sha256": "s"},
            "skipped": {"R10_jbig2": "no encoder"},
            "variants": {
                "R01_72dpi": {"output": "R01_72dpi.pdf", "output_sha256": "a" * 64, "text_layer": "none"},
                "R02_100dpi": {"output": "R02_100dpi.pdf", "output_sha256": "b" * 64, "text_layer": "none"},
            },
        },
    )
    audits = [
        {
            "doc_id": "d1",
            "level": "L0_tagged",
            "markdown": {"f1": 0.5, "precision": 0.4, "recall": 0.6},
            "text": {"f1": 0.9},
            "text_nfkc": {"f1": 0.95},
            "tables": [{"cell_recall": 1.0, "exact": True}, {"cell_recall": 0.5, "exact": False}],
            "image_only_text_recovered": None,
        },
        {"doc_id": "d1", "level": "R01_72dpi", "text": {"f1": 0.1}, "image_only_text_recovered": 0.2},
        {"doc_id": "d1", "level": "Q:q1", "path": str(wild / "quirks/q1/d1.pdf"), "text": {"f1": 1.0}},
        {"doc_id": "d1", "level": "Q:q2", "path": str(wild / "quirks/q2/raw-d1.pdf"), "text": {"f1": 0.7}},
    ]
    _write(wild / "audit.json", {"audits": audits})
    vision = wild / "vision-v1"
    page = {"doc_id": "d1", "level": "L4_raster", "page": 0, "model": "m/a", "image": {"jpeg_sha256": "f" * 64}}
    _write(vision / "arm-a" / "d1--L4_raster--p0.json", {**page, "status": "ok", "markdown": "# Hi", "usage": {}})
    _write(vision / "arm-a" / "d1--L4_raster--p1.json", {**page, "page": 1, "status": "ok", "markdown": "x"})
    _write(vision / "arm-a" / "summary.json", {"model": "m/a", "intended_pages": 2, "status": {"ok": 2}})
    _write(vision / "arm-b" / "d1--L4_raster--p0.json", {**page, "status": "error", "error": "boom"})
    _write(vision / "arm-b" / "summary.json", {"intended_pages": 2, "status": {"error": 1, "not_attempted": 1}})
    _write(vision / "arm-c" / "d1--L4_raster--p0.json", {**page, "status": "ok", "markdown": "y"})
    _write(
        vision / "scores.json",
        {
            "arm-a": {
                "documents": {
                    "L4_raster": [
                        {
                            "doc_id": "d1",
                            "text": {"f1": 0.8},
                            "image_only_text_recovered": 0.3,
                            "tables": [{"cell_recall": 0.6, "exact": False}],
                        }
                    ]
                }
            }
        },
    )
    rw = root / "real-world-v2"
    rw_sha = _pdf(rw / "pdfs" / "r1.pdf", b"r1")
    _pdf(rw / "pdfs" / "r2.pdf", b"r2")
    documents = [
        {
            "id": "r1",
            "path": "pdfs/r1.pdf",
            "sha256": rw_sha,
            "license": "CC-BY-4.0",
            "profile": {"pdf_version": "1.5"},
        },
        {"id": "r2", "path": "pdfs/r2.pdf", "sha256": "0" * 64, "license": "PD"},
    ]
    _write(rw / "manifest.json", {"documents": documents})
    _write(rw / "truth" / "r1.json", {"truth_status": "verified", "blocks": [{"text": "t"}]})
    return root


def test_dataset_name_refuses_heldout() -> None:
    assert dataset_name("dev/wild-v1-quirks") == "dev/wild-v1-quirks"
    for name in ("HELD-OUT-NOT-FOR-TRAINING/silver", "dev/silver-heldout-v1", "x/heldout-silver"):
        with pytest.raises(PermissionError):
            dataset_name(name)


def test_protected_paths_are_refused(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        real_world_items(tmp_path / "silver-heldout-v1")
    with pytest.raises(PermissionError):
        quirk_items(tmp_path / "heldout-silver")


def test_quirk_items_reference_truth_without_raw_text(artifacts: Path) -> None:
    meta, items = quirk_items(artifacts / "wild-v1")
    assert meta["split"] == "DEV"
    assert meta["heldout"] is False
    by_case = {metadata["case_id"]: (item_id, payload) for item_id, payload, metadata in items}
    doc_id, doc = by_case["q1/d1"]
    assert doc["expectedOutput"]["kind"] == "document_truth"
    assert doc["expectedOutput"]["truth"]["sha256"]
    raw_id, raw = by_case["q2/raw-d1"]
    expected = raw["expectedOutput"]
    assert expected["expected_text_sha256"] == hashlib.sha256(b"secret truth text").hexdigest()
    assert expected["expected_text_chars"] == len("secret truth text")
    assert expected["expected_lines"] == 2
    assert "secret truth text" not in json.dumps(raw)
    assert raw["input"]["pdf_sha256"] == hashlib.sha256(b"raw").hexdigest()
    assert len({doc_id, raw_id}) == 2
    assert quirk_items(artifacts / "wild-v1")[1] == items


def test_raster_items_are_per_document_variant(artifacts: Path) -> None:
    meta, items = raster_items(artifacts / "wild-v1")
    assert [m["variant"] for _, _, m in items] == ["R01_72dpi", "R02_100dpi"]
    assert meta["skipped_variants"] == {"R10_jbig2": "no encoder"}
    assert all(m["split"] == "DEV" and m["heldout"] is False for _, _, m in items)


def test_real_world_items_carry_verified_truth(artifacts: Path) -> None:
    meta, items = real_world_items(artifacts / "real-world-v2")
    assert meta["verified_truth"] == 1
    by_doc = {m["doc_id"]: p for _, p, m in items}
    assert by_doc["r1"]["expectedOutput"]["truth"]["blocks"] == [{"text": "t"}]
    assert by_doc["r1"]["input"]["sha256_matches_manifest"] is True
    assert by_doc["r2"]["expectedOutput"] is None
    assert by_doc["r2"]["input"]["sha256_matches_manifest"] is False


def test_wild_v2_skips_until_complete(tmp_path: Path) -> None:
    directory = tmp_path / "wild-v2"
    assert isinstance(wild_v2_items(directory), str)
    _write(directory / "docs" / "build-report.json", {"documents": [{"doc_id": "a"}]})
    assert "incomplete" in str(wild_v2_items(directory))
    _write(directory / "docs" / "a" / "truth.json", {"blocks": []})
    _pdf(directory / "docs" / "a" / "source.pdf")
    built = wild_v2_items(directory)
    assert not isinstance(built, str)
    assert built[1][0][1]["expectedOutput"]["truth"] == {"blocks": []}


def test_audit_scores_and_plan(artifacts: Path) -> None:
    scores = audit_scores(json.loads((artifacts / "wild-v1" / "audit.json").read_text())["audits"][0])
    assert scores["wild.text_f1"] == pytest.approx(0.9)
    assert scores["wild.text_nfkc_f1"] == pytest.approx(0.95)
    assert scores["wild.table_cell_recall_mean"] == pytest.approx(0.75)
    assert scores["wild.table_exact_count"] == 1
    assert "wild.image_only_text_recall" not in scores
    digest, plan = audit_plan(artifacts / "wild-v1")
    _, items = quirk_items(artifacts / "wild-v1")
    quirk_ids = {item_id for item_id, _, _ in items}
    assert {link[1] for link in plan["Q:q1"] + plan["Q:q2"]} == quirk_ids
    assert plan["L0_tagged"][0][1] == _hex("dev/wild-v1|d1")
    # Level rows reuse the trace IDs of bench.langfuse_backfill.sync_wild_runs.
    assert plan["L0_tagged"][0][0] == _hex(f"wild-v1 audit L0_tagged @ {digest}|d1")


def test_vision_plan_restores_unattempted_pages_and_skips_running_arms(artifacts: Path) -> None:
    plans, skipped = vision_plan(artifacts / "wild-v1" / "vision-v1")
    assert skipped == ["arm-c"]
    assert len(plans["arm-b"]["keys"]) == 2
    assert len(plans["arm-b"]["pages"]) == 1
    scores = vision_document_scores({"text": {"f1": 0.8}, "image_only_text_recovered": None, "tables": []})
    assert scores == {"vision.text_f1": 0.8}


def test_sync_all_is_idempotent(artifacts: Path) -> None:
    client = FakeClient()
    results = sync_all(client, artifacts)
    assert all(not (isinstance(r, dict) and r.get("status") == "error") for r in results.values()), results
    assert results["wild-v2"]["status"] == "skipped"
    datasets = {body["name"] for body in client.bodies("/api/public/v2/datasets")}
    assert datasets == {"dev/wild-v1-quirks", "dev/wild-v1-raster", "dev/real-world-v2"}
    items = client.bodies("/api/public/dataset-items")
    assert len(items) == 2 + 2 + 2
    assert all(item["metadata"]["split"] == "DEV" and item["metadata"]["heldout"] is False for item in items)
    run_items = client.bodies("/api/public/dataset-run-items")
    runs = {body["runName"] for body in run_items}
    assert any(name.startswith("wild-v1 audit Q:q1 @") for name in runs)
    assert {"wild-v1 vision arm-a", "wild-v1 vision arm-b"} <= runs
    assert "wild-v1 vision arm-c" not in runs
    quirk_links = [b for b in run_items if b["runName"].startswith("wild-v1 audit Q:")]
    assert {b["datasetItemId"] for b in quirk_links} == {
        quirk_item_id(case) for case in json.loads((artifacts / "wild-v1/quirks/manifest.json").read_text())["cases"]
    }
    scores = [event["body"] for batch in client.bodies("/api/public/ingestion") for event in batch["batch"]]
    names = {score["name"] for score in scores}
    assert {
        "wild.text_f1",
        "wild.markdown_f1",
        "vision.page_ok_rate",
        "vision.text_f1",
        "vision.text_f1/L4_raster",
        "vision.table_cell_recall",
    } <= names
    # Langfuse keeps one run item per (run, dataset item): never link two traces to one item.
    links = [(b["runName"], b["datasetItemId"]) for b in run_items]
    assert len(links) == len(set(links))
    rates = {s["traceId"]: s["value"] for s in scores if s["name"] == "vision.page_ok_rate"}
    assert rates[_hex("wild-v1 vision arm-a|doc|d1")] == 1.0
    assert rates[_hex("wild-v1 vision arm-b|doc|d1")] == 0.0
    assert len({score["id"] for score in scores}) == len(scores)
    traces = [
        span
        for batch in client.bodies("/api/public/otel/v1/traces")
        for rs in batch["resourceSpans"]
        for scope in rs["scopeSpans"]
        for span in scope["spans"]
    ]
    assert "base64" not in json.dumps(traces)
    assert "data:image" not in json.dumps(traces)
    pages = [t for t in traces if t.get("parentSpanId") and t["traceId"] == _hex("wild-v1 vision arm-b|doc|d1")]
    assert sorted(t["name"] for t in pages) == ["page L4_raster p0 error", "page L4_raster p1 not_attempted"]
    first = len(client.sent)
    again = sync_all(client, artifacts)
    assert all(r.get("status") == "replayed" for r in (again["quirks"], again["raster"], again["real-world-v2"]))
    resent = [path for path, _ in client.sent[first:]]
    assert set(resent) <= {"/api/public/v2/datasets"}


def test_legacy_runs_only_receive_scores(artifacts: Path) -> None:
    digest, _ = audit_plan(artifacts / "wild-v1")
    langfuse_backfill._mark("wild-run", f"wild-v1 audit L0_tagged @ {digest}", {})  # noqa: SLF001
    client = FakeClient()
    result = sync_all(client, artifacts, steps=["audit-runs"])["audit-runs"]
    statuses = {row["run"].split(" @ ")[0]: row["status"] for row in result}
    assert statuses["wild-v1 audit L0_tagged"] == "scored-existing"
    assert not [b for b in client.bodies("/api/public/dataset-run-items") if "L0_tagged" in b["runName"]]


def test_sync_errors_are_reported_not_raised(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(langfuse_backfill, "MARKERS", tmp_path / "markers")
    result = sync_all(FakeClient(), tmp_path / "missing", steps=["quirks"])
    assert result["quirks"]["status"] == "error"
