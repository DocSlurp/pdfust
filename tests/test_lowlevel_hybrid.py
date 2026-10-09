"""Offline routing preserves losses, missing outcomes and whole-batch accounting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import lowlevel_hybrid as hybrid

if TYPE_CHECKING:
    import pytest


def test_hybrid_freezes_before_labels_and_retains_losses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    (source / "manifest.json").write_text("{}")
    pages = []
    for ident, choice in (("a", "join"), ("b", "join"), ("c", "unresolved")):
        name = ident + ".json"
        (source / name).write_text(json.dumps({"source_choice": choice}))
        pages.append({"id": ident, "observation_file": name})
    records = [
        {"sha256": "batch1", "model": "m", "arm": "x", "page_ids": ["a", "b"]},
        {"sha256": "batch2", "model": "m", "arm": "x", "page_ids": ["a", "c"]},
    ]
    monkeypatch.setattr(hybrid, "verify_directory", lambda _: {"pages": pages, "records": records})
    monkeypatch.setattr(hybrid, "source_decision", lambda observation: observation["source_choice"])

    def evaluation(_: Path) -> dict[str, Any]:
        frozen = json.loads((output / "routing-before-scoring.json").read_text())
        assert frozen["routing"] == {"a": "join", "b": "join", "c": "unresolved"}
        return {
            "cohorts": [{"model": "m", "arm": "x"}],
            "outcomes": [
                {"id": "a", "model": "m", "arm": "x", "choice": "split", "expected": "join"},
                {"id": "b", "model": "m", "arm": "x", "choice": "split", "expected": "split"},
                {"id": "c", "model": "m", "arm": "x", "choice": None, "expected": "join"},
            ],
        }

    monkeypatch.setattr(hybrid, "evaluate", evaluation)
    row = hybrid.compare(source, output)["cohorts"][0]
    assert (row["paired"], row["inputs"], row["known_inputs"]) == (2, 3, 3)
    assert (row["direct_known_exact"], row["hybrid_known_exact"], row["gains"], row["losses"]) == (1, 1, 1, 1)
    assert (row["whole_bodies_skippable"], row["planned_bodies"]) == (1, 2)
