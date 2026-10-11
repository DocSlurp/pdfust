from __future__ import annotations

import base64
import json
import sys
from typing import TYPE_CHECKING, Any

import pytest
from bench import langfuse_backfill
from bench.langfuse_backfill import _guard, bound, scrub, sync_manifest_corpus

if TYPE_CHECKING:
    from pathlib import Path


class FakeClient(langfuse_backfill.Client):
    """Record requests instead of sending them."""

    def __init__(self, existing: list[dict[str, Any]] | None = None) -> None:
        """Serve ``existing`` as the dataset's current items."""
        super().__init__({"LANGFUSE_BASE_URL": "https://example.test"})
        self.sent: list[tuple[str, Any]] = []
        self.existing = existing or []

    def post(self, path: str, body: object) -> dict[str, Any]:
        """Record one POST."""
        self.sent.append((path, body))
        return {}

    def get(self, path: str) -> dict[str, Any]:
        """Return the configured dataset items."""
        assert path.startswith("/api/public/dataset-items?datasetName=")
        return {"data": self.existing, "meta": {"totalPages": 1}}


def corpus(tmp_path: Path) -> Path:
    directory = tmp_path / "corpus"
    (directory / "pdfs").mkdir(parents=True)
    (directory / "pdfs" / "a.pdf").write_bytes(b"%PDF-1.7 a")
    manifest = {"dataset_sha256": "d" * 64, "cases": [{"id": "a", "pdf_path": "pdfs/a.pdf"}]}
    (directory / "manifest.json").write_text(json.dumps(manifest))
    (directory / "gold.json").write_text(json.dumps([{"id": "a", "expected_text": ["A"]}]))
    return directory


def test_scrub_removes_credential_like_strings() -> None:
    text = 'key sk-or-v1-abcdefghijklmnopqrstuvwx and "api_key": "abcdef123456" Bearer abcdefghijklmnopqrstu'
    cleaned = scrub(text)
    assert "abcdefghijklmnop" not in cleaned
    assert "abcdef123456" not in cleaned
    assert cleaned.count("[redacted]") == 3
    assert bound("x" * 10, 4) == "xxxx\n[truncated 6 chars]"


def test_protected_prefixes_are_refused(tmp_path: Path) -> None:
    for name in ("silver-heldout-v1", "heldout-silver"):
        with pytest.raises(PermissionError):
            _guard(tmp_path / name / "manifest.json")
    assert _guard(tmp_path / "silver-v1") == tmp_path / "silver-v1"


def test_heldout_upload_requires_custodian_release(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(langfuse_backfill.transport, "_configuration", lambda _root: {"LANGFUSE_BASE_URL": "x"})
    monkeypatch.setattr(sys, "argv", ["langfuse_backfill", "heldout"])
    with pytest.raises(SystemExit, match="custodian-release"):
        langfuse_backfill.main()


def test_corpus_items_are_content_addressed_and_stale_items_archived(tmp_path: Path) -> None:
    directory = corpus(tmp_path)
    stale: dict[str, Any] = {"id": "old", "status": "ACTIVE", "input": {}, "expectedOutput": None, "metadata": {}}
    client = FakeClient([stale])
    status = sync_manifest_corpus(client, directory, "dev/x/1", "desc", {"split": "DEV"}, emit=False)
    assert status == {"dataset": "dev/x/1", "items": 1, "targets_matched": 1, "archived": 1}
    items = [body for path, body in client.sent if path == "/api/public/dataset-items"]
    current, archived = items[0], items[1]
    assert current["input"]["pdf_base64"] == base64.b64encode(b"%PDF-1.7 a").decode()
    assert current["expectedOutput"] == {"id": "a", "expected_text": ["A"]}
    assert current["metadata"] == {"split": "DEV", "case_id": "a"}
    assert archived == {
        "datasetName": "dev/x/1",
        **{k: stale[k] for k in ("id", "input", "expectedOutput", "metadata")},
        "status": "ARCHIVED",
    }

    (directory / "pdfs" / "a.pdf").write_bytes(b"%PDF-1.7 changed")
    second = FakeClient()
    sync_manifest_corpus(second, directory, "dev/x/1", "desc", {"split": "DEV"}, emit=False)
    changed = next(body for path, body in second.sent if path == "/api/public/dataset-items")
    assert changed["id"] != current["id"]
