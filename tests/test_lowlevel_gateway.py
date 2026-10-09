"""Gateway transport projection retains evidence and excludes scorer metadata."""

# Reused source-freeze fixture has the same name as the test parameter.
# ruff: noqa: F811
from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench.lowlevel_gateway import MODELS, TEXT_ARMS, prepare, request, verify
from bench.lowlevel_images import request as image_request
from test_lowlevel_packets import parent  # noqa: F401


def test_gateway_text_matrix_is_complete_and_source_only(parent: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "gateway.json"
    catalog.write_text(json.dumps({"prices": {m: {"input": 0, "output": 0} for m in MODELS}}))
    directory = tmp_path / "gateway"
    manifest = prepare(parent, directory, catalog)
    assert verify(directory) == manifest
    assert len(manifest["records"]) == len(manifest["pages"]) * len(MODELS) * len(TEXT_ARMS)
    record = manifest["records"][0]
    page = next(p for p in manifest["pages"] if p["id"] == record["page_ids"][0])
    observation = json.loads((directory / page["observation_file"]).read_text())
    original = request([observation], record["model"], record["arm"])
    observation.update(expected="PRIVATE_LABEL", family="PRIVATE_LABEL")
    assert request([observation], record["model"], record["arm"]) == original
    assert "PRIVATE_LABEL" not in json.dumps(original)
    assert all(r["body_bytes"] <= 7500 for r in manifest["records"])
    manifest["records"].pop()
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="incomplete"):
        verify(directory)


def test_serialized_state_is_lossless_compatibility_control(parent: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "gateway.json"
    catalog.write_text(json.dumps({"prices": {m: {"input": 0, "output": 0} for m in MODELS}}))
    directory = tmp_path / "serialized"
    manifest = prepare(parent, directory, catalog, kind="text-serialized")
    assert manifest["experiment"] == "L010"
    assert verify(directory) == manifest
    page = manifest["pages"][0]
    observed = json.loads((directory / page["observation_file"]).read_text())
    for model in MODELS:
        for arm in TEXT_ARMS:
            original = request([observed], model, arm)
            changed = request([observed], model, arm + "-serialized")
            assert isinstance(changed["state"], str)
            assert json.loads(changed["state"]) == original["state"]
            assert changed["questions"] == original["questions"]


def test_gateway_image_translation_preserves_literal_evidence(parent: Path) -> None:
    manifest = json.loads((parent / "manifest.json").read_text())
    page = manifest["pages"][0]
    observed = json.loads((parent / page["observation_file"]).read_text())
    for edge in (64, 128, 256, 400, 500, 512):
        for mode in ("rgb", "gray", "lowbit"):
            arm = f"focus-{mode}-{edge}"
            original = image_request([observed], "perplexity/pplx-decider-v1.1-27b", arm)
            gateway = request([observed], "liquid/d1", arm)
            assert gateway["questions"] == original["questions"]
            assert gateway["state"] == "\n".join(part for part in original["state"] if isinstance(part, str))
            assert gateway["images"] == [
                part["image_url"]["url"] for part in original["state"] if isinstance(part, dict)
            ]
