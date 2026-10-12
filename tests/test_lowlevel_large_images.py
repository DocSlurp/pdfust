"""CPU-only fresh rendering and provider transport contract checks."""

import hashlib
import io
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import lowlevel_large_images as large
from PIL import Image

import pdfust


def template() -> dict[str, Any]:
    return {
        "model": large.MODELS[0],
        "state": [
            json.dumps(
                {
                    "observations": {
                        "q0": {
                            "task": "character_boundary",
                            "chunks": [{"text": "source"}],
                            "target_boxes": [[1, 2, 3, 4], [5, 2, 7, 4]],
                            "nearby_words": [],
                        }
                    }
                }
            )
        ],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Choose source relationship",
                "criteria": {"join": "joined", "split": "separated"},
            }
        },
    }


def test_fresh_render_uses_source_at_each_resolution(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    with pdfust.Document() as doc:
        page = doc.new_page(width=200, height=100)
        page.insert_text((20, 40), "Fresh source pixels")
        doc.save(source)
    for edge in large.SIZES:
        rgb, metadata = large.raster(source, [10, 10, 190, 70], edge)
        assert rgb.size == (edge, round(edge / 3))
        assert metadata["render_pixels"][0] >= edge
        assert metadata["render_scale"] == (edge + 2) / 180
        assert metadata["pixel_area"] == rgb.width * rgb.height


@pytest.mark.parametrize(("mode", "depth", "color"), [("rgb", 8, "RGB"), ("gray", 8, "L"), ("lowbit", 2, "P")])
def test_independent_color_treatments_and_exact_gateway_translation(mode: str, depth: int, color: str) -> None:
    rgb = Image.new("RGB", (512, 64), (100, 120, 130))
    png = large.variant(rgb, mode)
    assert png[24] == depth
    with Image.open(io.BytesIO(png)) as image:
        assert image.mode == color
        assert image.size == rgb.size
    original = template()
    preserved = deepcopy(original)
    info = {"pixels": [512, 64], "bbox": [0, 0, 80, 10]}
    native = large.body(original, "liquid/d1", png, info, mode)
    gateway = large.body(original, "liquid/d1", png, info, mode, gateway=True)
    assert gateway["input"][0]["content"][0] == {"type": "input_text", "text": native["state"][0]}
    assert gateway["input"][0]["content"][1] == {
        "type": "input_image",
        "image_url": native["state"][1]["image_url"]["url"],
        "detail": "high",
    }
    question = gateway["questions"][0]
    assert question["name"] == "q0"
    assert question["instructions"] == original["questions"]["q0"]["instructions"]
    assert question["choices"] == [
        {"value": k, "description": v} for k, v in original["questions"]["q0"]["criteria"].items()
    ]
    assert large.validate_wire(gateway, large.BODY_CAP) == large.encoded_body(gateway)
    assert original == preserved
    assert json.loads(native["state"][0])["observations"] == json.loads(original["state"][0])["observations"]


def test_admissions_reject_unknown_treatments_and_oversized_text() -> None:
    with pytest.raises(ValueError, match="Unadmitted"):
        large.variant(Image.new("RGB", (2, 2)), "unknown")
    data = template()
    data["questions"]["q0"]["instructions"] = "x" * 2000
    with pytest.raises(ValueError, match="1800"):
        large.body(
            data,
            large.MODELS[0],
            large.variant(Image.new("RGB", (2, 2)), "rgb"),
            {"pixels": [2, 2], "bbox": [0, 0, 2, 2]},
            "rgb",
        )


def test_gateway_requires_matched_images_before_any_artifact_access(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="image_freeze"):
        large.prepare(tmp_path / "missing", tmp_path / "out", gateway=True)
    assert not (tmp_path / "out").exists()


def test_entire_matrix_is_frozen_before_scorer_copy_and_retains_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    pages, records = [], []
    for index in range(24):
        ident = str(index)
        source, observation, request = f"source-{index}.pdf", f"observation-{index}.json", f"prior-{index}.json"
        source_raw = b"mock source"
        obs_raw = json.dumps({"images": {"crop512": {"bbox": [0, 0, 80, 10], "sha256": "historical"}}}).encode()
        (parent / source).write_bytes(source_raw)
        (parent / observation).write_bytes(obs_raw)
        (parent / request).write_bytes(large.encoded_body(template()))
        pages.append(
            {
                "id": ident,
                "source_file": source,
                "source_sha256": hashlib.sha256(source_raw).hexdigest(),
                "observation_file": observation,
                "observation_sha256": hashlib.sha256(obs_raw).hexdigest(),
            }
        )
        records.append({"request": request, "model": large.MODELS[0], "arm": "focus-rgb-512", "page_ids": [ident]})
    (parent / "manifest.json").write_text(
        json.dumps({"experiment": "L006", "kind": "focus", "pages": pages, "records": records})
    )
    (parent / "catalog-prices.json").write_text(json.dumps({"prices": {key: {} for key in large.MODELS}}))
    monkeypatch.setattr(large, "source_templates", lambda *_: {p["id"]: template() for p in pages})

    def fake_raster(_source: Path, bbox: list[float], edge: int) -> tuple[Image.Image, dict[str, Any]]:
        image = Image.new("RGB", (edge, edge // 8), "white")
        return image, {
            "bbox": bbox,
            "pixels": list(image.size),
            "pixel_area": image.width * image.height,
            "width": image.width,
            "height": image.height,
            "render_scale": edge / 80,
        }

    monkeypatch.setattr(large, "raster", fake_raster)

    def finish(parent: Path, directory: Path, manifest: dict[str, Any]) -> dict[str, Any]:
        assert not (parent / "private-targets.json").exists()
        assert len(manifest["records"]) == 864
        assert all((directory / record["request"]).exists() for record in manifest["records"])
        assert manifest["unique_requests"] == 36
        assert sum(record["exact_body_alias"] for record in manifest["records"]) == 828
        return manifest

    monkeypatch.setattr(large, "finish", finish)
    large.prepare(parent, tmp_path / "freeze")
