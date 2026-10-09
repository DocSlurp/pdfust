"""Follow-up selection uses observable source identity, never scores or labels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from bench import lowlevel_evidence, lowlevel_followups
from bench.lowlevel_cases import cases

if TYPE_CHECKING:
    import pytest


def test_followup_selects_shortest_visible_encoding_and_freezes_every_factor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts = tmp_path / "artifacts"
    (artifacts / "langfuse").mkdir(parents=True)
    (artifacts / "langfuse/catalog-prices.json").write_text('{"prices":{}}')
    monkeypatch.setattr(lowlevel_evidence, "ARTIFACTS", artifacts)
    parent, directory = tmp_path / "parent", tmp_path / "followup"
    cohort = cases()[:3]
    lowlevel_evidence.prepare(parent, cohort=cohort)
    frozen = lowlevel_followups.prepare(parent, directory)
    assert len(frozen["pages"]) == 1
    assert frozen["pages"][0]["id"] == min(cohort, key=lambda c: len(c["pdf_bytes"]))["id"]
    assert frozen["encoding_comparison"] is False
    assert lowlevel_evidence.verify(directory) == frozen
    assert {record["prompt_variant"] for record in frozen["records"]} == {"original", "typed", "both", "resolved"}
    for record in frozen["records"]:
        body = json.loads((directory / record["request"]).read_bytes())
        assert "logical_id" not in str(body)
        if record["prompt_variant"] in {"typed", "both"}:
            assert isinstance(body["state"], dict)
        if record["base_arm"].startswith("crop"):
            assert any(isinstance(item, dict) and item["type"] == "image_url" for item in body["state"])
