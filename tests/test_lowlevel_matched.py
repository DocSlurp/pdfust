"""Matched singleton freezing changes row encoding alone."""

# Imported pytest fixture names are also test parameter names.
# ruff: noqa: F811

import json
from pathlib import Path

import pytest
from bench.lowlevel_compact import expand
from bench.lowlevel_matched import prepare, verify
from test_lowlevel_packets import parent  # noqa: F401 - imported pytest source-freeze fixture.


def test_matched_raw_and_compact_have_identical_source_and_questions(parent: Path, tmp_path: Path) -> None:
    directory = tmp_path / "matched"
    manifest = prepare(parent, directory)
    assert manifest["experiment"] == "L005"
    assert verify(directory) == manifest
    by_key = {
        (record["model"], record["page_ids"][0], record["arm"]): json.loads(
            (directory / record["request"]).read_bytes()
        )
        for record in manifest["records"]
    }
    for model in manifest["models"]:
        for page in manifest["pages"]:
            raw = by_key[model, page["id"], "rawbothcanonical"]
            compact = by_key[model, page["id"], "compactbothcanonical"]
            assert raw["questions"] == compact["questions"]
            assert raw["model"] == compact["model"]
            assert expand(compact["state"]["observations"]["q0"]) == raw["state"]["observations"]["q0"]
    assert all(record["body_bytes"] <= 32000 for record in manifest["records"])


def test_matched_verification_rejects_missing_control(parent: Path, tmp_path: Path) -> None:
    directory = tmp_path / "matched"
    manifest = prepare(parent, directory)
    manifest["records"].pop()
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="incomplete"):
        verify(directory)
