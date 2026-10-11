from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from bench import langfuse_backfill
from bench.langfuse_adapters import discover
from bench.langfuse_adapters.base import Experiment, Item, Row, Run, clean_scores, export, guard, item_id, validate

if TYPE_CHECKING:
    from pathlib import Path


class FakeClient(langfuse_backfill.Client):
    """Record requests instead of sending them."""

    def __init__(self) -> None:
        """Start with an empty dataset."""
        super().__init__({"LANGFUSE_BASE_URL": "https://example.test"})
        self.sent: list[tuple[str, Any]] = []

    def post(self, path: str, body: object) -> dict[str, Any]:
        """Record one POST."""
        self.sent.append((path, body))
        return {}

    def get(self, path: str) -> dict[str, Any]:
        """Serve an empty item listing and a known dataset run."""
        if "/runs/" in path:
            return {"id": "run-1"}
        return {"data": [], "meta": {"totalPages": 1}}


def experiment() -> Experiment:
    rows = [
        Row("a", {"answer": "x"}, {"correct": True, "probability": 0.9, "unknown": None}, {"status": "ok"}),
        Row("b", None, {"correct": False}, {"status": "error"}),
    ]
    return Experiment(
        dataset="exp/test/v1",
        description="test",
        items=[Item("a", {"q": 1}, {"gold": "x"}), Item("b", {"q": 2}, {"gold": "y"})],
        runs=[Run("model-1", "desc", rows, {"model": "m"}, {"accuracy": 0.5})],
        source="bench/results/pdf-master-artifacts/test",
    )


def test_clean_scores_keeps_finite_numbers_and_booleans() -> None:
    assert clean_scores({"a": True, "b": 0, "c": float("nan"), "d": None, "e": "1"}) == {"a": 1.0, "b": 0.0}


def test_validate_rejects_rows_for_unknown_items_and_duplicates() -> None:
    value = experiment()
    assert validate(value)["rows"] == 2
    value.runs[0].rows.append(Row("missing", None))
    with pytest.raises(ValueError, match="unknown item"):
        validate(value)
    value = experiment()
    value.items.append(Item("a", {}))
    with pytest.raises(ValueError, match="duplicate item"):
        validate(value)


def test_guard_refuses_protected_paths(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        guard(tmp_path / "silver-heldout-v1" / "x.json")


def test_export_links_rows_scores_and_replays(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(langfuse_backfill, "MARKERS", tmp_path / "markers")
    client = FakeClient()
    value = experiment()
    status = export(client, value)
    assert status["runs_exported"] == 1
    items = {body["id"] for path, body in client.sent if path == "/api/public/dataset-items"}
    assert items == {item_id(value.dataset, item) for item in value.items}
    links = [body for path, body in client.sent if path == "/api/public/dataset-run-items"]
    assert {link["datasetItemId"] for link in links} == items
    scores = [event["body"] for path, body in client.sent if path == "/api/public/ingestion" for event in body["batch"]]
    assert sorted((s["name"], s["value"]) for s in scores if "traceId" in s) == [
        ("correct", 0.0),
        ("correct", 1.0),
        ("probability", 0.9),
    ]
    assert [(s["name"], s["value"]) for s in scores if "datasetRunId" in s] == [("accuracy", 0.5)]

    replay = FakeClient()
    assert export(replay, value)["runs_replayed"] == 1
    assert not [path for path, _ in replay.sent if path == "/api/public/dataset-run-items"]

    value.runs[0].rows[1].scores["correct"] = True
    changed = FakeClient()
    assert export(changed, value)["runs_exported"] == 1


def test_export_scrubs_and_bounds_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(langfuse_backfill, "MARKERS", tmp_path / "markers")
    value = experiment()
    value.runs[0].rows[0].output = {"text": "token: sk-abcdefghijklmnopqrstuvwx", "big": "x" * 100_000}
    client = FakeClient()
    export(client, value)
    payload = str([body for path, body in client.sent if path == "/api/public/otel/v1/traces"])
    assert "sk-abcdefghijklmnop" not in payload
    assert "truncated" in payload


def test_every_discovered_adapter_has_the_contract() -> None:
    for module in discover():
        assert isinstance(module.NAME, str)
        assert callable(module.collect)


class LinkingClient(FakeClient):
    """Serve existing run-item links for the repair path."""

    def __init__(self, existing_traces: list[str]) -> None:
        """Pretend these trace IDs are already linked."""
        super().__init__()
        self.existing_traces = existing_traces

    def get(self, path: str) -> dict[str, Any]:
        """Serve dataset, run-item, and item listings."""
        if path.startswith("/api/public/v2/datasets/"):
            return {"id": "dataset-1"}
        if path.startswith("/api/public/dataset-run-items?"):
            return {"data": [{"traceId": t} for t in self.existing_traces], "meta": {"totalPages": 1}}
        return super().get(path)


def test_first_link_is_posted_alone_and_repair_posts_only_missing_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(langfuse_backfill, "MARKERS", tmp_path / "markers")
    value = experiment()
    first = FakeClient()
    export(first, value)
    paths = [path for path, _ in first.sent]
    links = [body for path, body in first.sent if path == "/api/public/dataset-run-items"]
    assert len(links) == 2
    # The run-creating link precedes every other link and the score batch.
    assert paths.index("/api/public/dataset-run-items") < paths.index("/api/public/ingestion")

    repair = LinkingClient([links[0]["traceId"]])
    status = export(repair, value, repair=True)
    reposted = [body for path, body in repair.sent if path == "/api/public/dataset-run-items"]
    assert status["links_repaired"] == 1
    assert [body["traceId"] for body in reposted] == [links[1]["traceId"]]
    assert "/api/public/otel/v1/traces" not in [path for path, _ in repair.sent]

    complete = LinkingClient([link["traceId"] for link in links])
    assert export(complete, value, repair=True)["links_repaired"] == 0
