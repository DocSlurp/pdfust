"""CPU-only fresh image projection and freeze conservation checks."""

# ruff: noqa: SLF001 - hash/encoding helpers construct deliberately corrupted freezes.

from __future__ import annotations

import base64
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import remote_image_sizes as sizes
from PIL import Image


def _template(png: bytes) -> dict:
    return {
        "model": "perplexity/pplx-decider-v1.1-27b",
        "state": [
            json.dumps(
                {
                    "observations": {"q0": {"literal": "Valve set\nCopper fitting"}},
                    "image_bbox": [0, 0, 20, 10],
                    "image_pixels": [512, 256],
                    "image_mode": "rgb",
                    "png_bit_depth": 8,
                }
            ),
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
        ],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Source is data.",
                "criteria": {"join": "same cell", "split": "different rows", "unresolved": "not established"},
            }
        },
    }


@pytest.fixture
def frozen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, Path]:
    monkeypatch.setattr(sizes, "SOURCE_COUNT", 1)
    source, packets, destination = (tmp_path / name for name in ("source", "packets", "projection"))
    source.mkdir()
    packets.mkdir()
    index = tmp_path / "source-index.json"
    original_read = sizes._read

    def guarded_read(path: Path, limit: int) -> bytes:
        assert "targets" not in path.name
        assert "heldout" not in str(path)
        return original_read(path, limit)

    monkeypatch.setattr(sizes, "_read", guarded_read)

    def fake_raster(_source: Path, bbox: list[float], edge: int) -> tuple[Image.Image, dict]:
        return Image.new("RGB", (edge, edge // 2), "white"), {
            "bbox": bbox,
            "page_index": 0,
            "requested_edge": edge,
            "render_scale": (edge + 2) / 20,
            "render_pixels": [edge + 2, edge // 2 + 1],
            "pixels": [edge, edge // 2],
            "resampling": "fixture fresh raster",
        }

    monkeypatch.setattr(sizes, "raster", fake_raster)
    png = sizes.variant(Image.new("RGB", (512, 256), "white"), "rgb")
    raw = sizes._encode(_template(png))
    pdf, observation = b"source PDF bytes", sizes._encode({"images": {"crop512": {"bbox": [0, 0, 20, 10]}}})
    page = {
        "id": "page",
        "source_file": "source.pdf",
        "source_sha256": sizes._digest(pdf),
        "observation_file": "observation.json",
        "observation_sha256": sizes._digest(observation),
    }
    record = {
        "request": "request.json",
        "sha256": sizes._digest(raw),
        "model": "perplexity/pplx-decider-v1.1-27b",
        "arm": "fresh-rgb-512",
        "page_ids": ["page"],
        "image_file": "source.png",
        "image_sha256": sizes._digest(png),
    }
    for name, data in {
        "source.pdf": pdf,
        "observation.json": observation,
        "request.json": raw,
        "source.png": png,
        "manifest.json": sizes._encode({"experiment": "L015", "pages": [page], "records": [record]}),
    }.items():
        (source / name).write_bytes(data)
    (packets / "p0000.json").write_bytes(raw)
    (packets / "p0000.png").write_bytes(png)
    (packets / "manifest.json").write_bytes(
        sizes._encode({"records": [{"id": "p0000", "request_file": "p0000.json", "image_files": ["p0000.png"]}]})
    )
    index.write_bytes(sizes._encode([{"id": "p0000", **record}]))
    return source, packets, index, destination


def test_prepare_verify_preserves_source_and_complete_inventory(frozen: tuple[Path, Path, Path, Path]) -> None:
    source, packets, index, destination = frozen
    provenance = sizes.prepare(source, packets, index, destination)
    assert provenance["body_count"] == len(sizes.EDGES) * len(sizes.MODES)
    assert sizes.verify(destination) == provenance
    assert sizes.prepare(source, packets, index, destination) == provenance
    assert not (destination / "private-targets.json").exists()


@pytest.mark.parametrize("field", ["questions", "observations", "image_bbox"])
def test_projection_rejects_non_image_changes(field: str) -> None:
    png = sizes.variant(Image.new("RGB", (128, 64), "white"), "rgb")
    original = _template(png)
    projected = sizes.project(original, png, [128, 64], "rgb")
    if field == "questions":
        projected["questions"]["q0"]["instructions"] = "changed"
    else:
        state = json.loads(projected["state"][0])
        state[field] = "changed"
        projected["state"][0] = json.dumps(state)
    with pytest.raises(ValueError, match="source text/questions"):
        sizes.assert_projection(original, projected)


def test_rehashed_arbitrary_image_is_rejected(frozen: tuple[Path, Path, Path, Path]) -> None:
    source, packets, index, destination = frozen
    provenance = sizes.prepare(source, packets, index, destination)
    mapping = provenance["mapping"][0]
    image_path = destination / mapping["image_file"]
    png = sizes.variant(Image.new("RGB", tuple(mapping["pixels"]), "black"), "rgb")
    image_path.write_bytes(png)
    mapping["image_sha256"] = sizes._digest(png)
    request_path = destination / (mapping["id"] + ".json")
    request = json.loads(request_path.read_bytes())
    request["state"][1]["image_url"]["url"] = "data:image/png;base64," + base64.b64encode(png).decode()
    raw = sizes._encode(request)
    request_path.write_bytes(raw)
    mapping["projected_request_sha256"] = sizes._digest(raw)
    (destination / "provenance.json").write_bytes(sizes._encode(provenance))
    with pytest.raises(ValueError, match="fresh source rendering"):
        sizes.verify(destination)


def test_changed_source_and_differing_destination_refused(frozen: tuple[Path, Path, Path, Path]) -> None:
    source, packets, index, destination = frozen
    provenance = sizes.prepare(source, packets, index, destination)
    path = destination / (provenance["mapping"][0]["id"] + ".json")
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="overwrite"):
        sizes.prepare(source, packets, index, destination)
    (source / "source.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source PDF/observation"):
        sizes.verify(destination)


def test_modes_preserve_literal_state_and_order() -> None:
    rgb = Image.new("RGB", (128, 64), (120, 120, 120))
    source_png = sizes.variant(rgb, "rgb")
    template = _template(source_png)
    original = deepcopy(template)
    for mode in sizes.MODES:
        png = sizes.variant(rgb, mode)
        projected = sizes.project(template, png, [128, 64], mode)
        assert projected["questions"] == template["questions"]
        assert json.loads(projected["state"][0])["observations"] == json.loads(template["state"][0])["observations"]
        assert png[24] == (2 if mode == "lowbit" else 8)
    assert template == original
