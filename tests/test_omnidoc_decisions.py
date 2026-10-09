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
    jpeg_manifest = prepare(tmp_path / "jpeg80", registry, images, jpeg80_only=True)
    assert jpeg_manifest["logical_requests"] == 64
    assert len(jpeg_manifest["requests"]) == 64
    assert jpeg_manifest["arms"] == ("jpeg80-rgb1200",)
    jpeg_report = evaluate(tmp_path / "jpeg80", jpeg_manifest, {"rows": []})
    assert jpeg_report["logical_requests"] == 64
    assert len(jpeg_report["groups"]) == 4
    assert all(group["logical_pages"] == 16 for group in jpeg_report["groups"].values())
    report = evaluate(directory, manifest, {"rows": []})
    assert all(group["logical_pages"] == 16 for group in report["groups"].values())
    assert all(group["confusion"][0]["unscored"] == 16 for group in report["groups"].values())
    with pytest.raises(ValueError, match="already frozen"):
        prepare(directory, registry, images)
    request = next(row for row in manifest["requests"] if row["status"] == "prepared")
    (directory / request["request_file"]).write_text("{}")
    with pytest.raises(ValueError, match="request body changed"):
        verify(directory, manifest)


def test_jpeg80_is_named_lossy_rgb_with_same_dimensions_and_bytes() -> None:
    from bench.omnidoc_decisions import JPEG_ARM  # noqa: PLC0415

    reference = image_variant(png(), "rgb1200")
    variant = image_variant(png(), JPEG_ARM)
    assert variant["pixels"] == reference["pixels"]
    assert variant["mime"] == "image/jpeg"
    assert variant["data"].startswith(b"\xff\xd8")
    assert variant["data"].endswith(b"\xff\xd9")
    assert variant["jpeg_quality"] == 80
    assert variant["jpeg_precision_bits"] == 8
    assert variant["original_png_bytes"] == len(reference["data"])
    assert variant["original_png_sha256"] == sha(reference["data"])
    with Image.open(io.BytesIO(variant["data"])) as decoded, Image.open(io.BytesIO(reference["data"])) as original:
        assert decoded.mode == "RGB"
        assert decoded.format == "JPEG"
        assert variant["decoded_pixels_changed"] == (decoded.tobytes() != original.tobytes())
    assert variant["lossy"]
    body = body_for(MODELS[0], variant)
    assert isinstance(body["state"][0], str)
    url = body["state"][1]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
    import base64  # noqa: PLC0415

    assert base64.b64decode(url.split(",", 1)[1]) == variant["data"]
    assert sha(json.dumps(body).encode()) != sha(json.dumps(body_for(MODELS[0], reference)).encode())


def test_jpeg_model_body_has_no_label_input_and_keeps_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    from bench.omnidoc_decisions import JPEG_ARM  # noqa: PLC0415

    variant = image_variant(png(), JPEG_ARM)
    before = body_for(MODELS[2], variant)
    row = sample()
    row["category_counts"] = {}
    row["attributes"]["layout"] = "other_layout"
    assert private_labels(row, JPEG_ARM) == [False, False, None]
    assert body_for(MODELS[2], variant) == before
    monkeypatch.setattr(omnidoc_decisions, "CLEF_IMAGE_CHARACTERS", 20)
    with pytest.raises(ValueError, match="no crop or resize"):
        body_for(MODELS[2], variant)
    assert variant["pixels"] == [800, 1200]


def test_stop_file_and_model_failure_preserve_complete_unattempted_rows(tmp_path: Path) -> None:
    from bench.omnidoc_decisions import run  # noqa: PLC0415

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

    class FakeClient:
        ledger = tmp_path / "ledger.json"

        def __init__(self) -> None:
            self.calls: list[str] = []

        def request(self, body: dict, *, tag: str, max_body_bytes: int) -> dict:
            assert tag.startswith("omnidoc-dev/")
            assert max_body_bytes > 0
            self.calls.append(body["model"])
            if body["model"] == MODELS[0]:
                raise RuntimeError("simulated provider failure")  # noqa: EM101, TRY003
            return {
                "entry": {"index": len(self.calls), "accounted_usd": 0.00001, "cost_status": "provider-reported USD"},
                "result": {"answers": {f"q{i}": {"noul": 0.1} for i in range(3)}},
                "replayed": False,
            }

    client = FakeClient()
    (directory / "STOP").touch()
    stopped = run(directory, manifest, client)
    assert len(stopped["rows"]) == 256
    assert not client.calls
    assert all(row["status"] == "unattempted" for row in stopped["rows"])
    (directory / "STOP").unlink()
    results = run(directory, manifest, client)
    assert len(results["rows"]) == 256
    assert client.calls.count(MODELS[0]) == 1
    failed_model = [row for row in results["rows"] if row["model"] == MODELS[0]]
    assert sum(row["status"] == "failed" for row in failed_model) == 1
    assert sum(row["status"] == "unattempted" for row in failed_model) == 63
    again = run(directory, manifest, client)
    assert len(again["rows"]) == 256
    assert client.calls.count(MODELS[0]) == 1
