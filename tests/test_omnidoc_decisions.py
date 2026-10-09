"""Frozen image bodies, private-label isolation, admission and complete confusion."""

from __future__ import annotations

import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import omnidoc_decisions
from bench.omnidoc_decisions import (
    ARMS,
    MODELS,
    body_for,
    evaluate,
    image_variant,
    prepare,
    private_labels,
    verify,
    wave_admission,
)
from bench.silver import sha
from PIL import Image


def png() -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (80, 120), (100, 120, 140)).save(stream, format="PNG")
    return stream.getvalue()


def sample() -> dict:
    return {
        "id": "source.png",
        "image_sha256": sha(png()),
        "category_counts": {"table": 1, "equation_isolated": 2},
        "attributes": {"layout": "double_column"},
    }


def test_source_body_invariant_under_private_metadata_perturbation() -> None:
    before = sample()
    after = deepcopy(before)
    after.update(category_counts={}, attributes={"layout": "other_layout"}, id="secret-annotation-name.png")
    variant = image_variant(png(), "rgb128")
    assert body_for(MODELS[0], variant) == body_for(MODELS[0], variant)
    assert private_labels(before, "rgb128") != private_labels(after, "rgb128")
    encoded = json.dumps(body_for(MODELS[0], variant))
    assert before["id"] not in encoded
    assert after["id"] not in encoded
    assert "category_counts" not in encoded
    assert "layout" not in encoded


def test_rgb_dimensions_and_matched_blank_do_not_crop() -> None:
    for arm, maximum in zip(ARMS, (128, 512, 1200, 512), strict=True):
        variant = image_variant(png(), arm)
        assert max(variant["pixels"]) == maximum
        with Image.open(io.BytesIO(variant["data"])) as image:
            assert image.mode == "RGB"
            assert abs(image.width / image.height - 2 / 3) < 0.01
            if arm == "blank512":
                assert image.getextrema() == ((255, 255),) * 3


def test_private_labels_and_unknown_layout() -> None:
    row = sample()
    assert private_labels(row, "rgb512") == [True, True, True]
    row["attributes"]["layout"] = "1andmore_column"
    assert private_labels(row, "rgb512")[2] is True
    row["attributes"]["layout"] = "other_layout"
    assert private_labels(row, "rgb512")[2] is None
    assert private_labels(row, "blank512") == [False, False, False]


def test_shared_wave_cap_includes_reservations_and_ignores_other_tags() -> None:
    wave_admission([{"tag": "another-wave/", "accounted_usd": 100}])
    wave_admission([{"tag": "omnidoc-dev/one", "accounted_usd": 0.20}])
    with pytest.raises(RuntimeError, match="cap exhausted"):
        wave_admission([{"tag": "omnidoc-dev/one", "accounted_usd": 0.20001}])
    with pytest.raises(RuntimeError, match="cap exhausted"):
        wave_admission([{"tag": "omnidoc-dev/failed", "accounted_usd": 0.30}])


def test_payload_admission_refuses_without_silent_resize(monkeypatch: pytest.MonkeyPatch) -> None:
    variant = image_variant(png(), "rgb512")
    monkeypatch.setattr(omnidoc_decisions, "MAX_BODY_BYTES", 20)
    with pytest.raises(ValueError, match="no crop or resize"):
        body_for(MODELS[0], variant)
    assert variant["pixels"] == [341, 512]


def test_prepare_complete_fixed_manifest_and_refuse_mutation(tmp_path: Path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    (images / "source.png").write_bytes(png())
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "purpose": "DEV tuning",
                "revision": "pinned",
                "license": "research-only",
                "contamination": "unknown",
                "rows": [sample() for _ in range(16)],
            }
        )
    )
    directory = tmp_path / "pilot"
    manifest = prepare(directory, registry, images)
    assert manifest["logical_requests"] == 256
    assert len(manifest["requests"]) == 256
    verify(directory, manifest)
    verify(directory, json.loads((directory / "manifest.json").read_text()))
    changed = json.loads(registry.read_text())
    for row in changed["rows"]:
        row["category_counts"] = {}
        row["attributes"]["layout"] = "other_layout"
    registry.write_text(json.dumps(changed))
    perturbed = prepare(tmp_path / "perturbed", registry, images)
    assert [row.get("request_sha256") for row in manifest["requests"]] == [
        row.get("request_sha256") for row in perturbed["requests"]
    ]
    assert manifest["private_labels_sha256"] != perturbed["private_labels_sha256"]
    report = evaluate(directory, manifest, {"rows": []})
    assert all(group["logical_pages"] == 16 for group in report["groups"].values())
    assert all(group["confusion"][0]["unscored"] == 16 for group in report["groups"].values())
    with pytest.raises(ValueError, match="already frozen"):
        prepare(directory, registry, images)
    request = next(row for row in manifest["requests"] if row["status"] == "prepared")
    (directory / request["request_file"]).write_text("{}")
    with pytest.raises(ValueError, match="request body changed"):
        verify(directory, manifest)
