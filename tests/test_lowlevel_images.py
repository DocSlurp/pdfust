"""Image-factor provenance and all-model focus byte bounds."""

# Imported pytest fixture names are also test parameter names.
# ruff: noqa: F811
import base64
import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench.lowlevel_images import MODELS, MODES, SIZES, image_variant, non_image_bytes, prepare, request, verify
from PIL import Image
from test_lowlevel_packets import parent  # noqa: F401 - shared immutable-source fixture.


def observation(parent: Path) -> dict:
    manifest = json.loads((parent / "manifest.json").read_bytes())
    return json.loads((parent / manifest["pages"][0]["observation_file"]).read_bytes())


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("size", SIZES)
def test_png_factors_are_deterministic_and_source_linked(parent: Path, mode: str, size: int) -> None:
    source = observation(parent)
    before = deepcopy(source)
    image = image_variant(source, edge=size, mode=mode)
    assert image == image_variant(source, edge=size, mode=mode)
    assert source == before
    assert image["source_crop_sha256"] == source["images"]["crop512"]["sha256"]
    assert image["bbox"] == source["images"]["crop512"]["bbox"]
    assert max(image["pixels"]) == size
    with Image.open(io.BytesIO(base64.b64decode(image["png_base64"]))) as decoded:
        assert decoded.format == "PNG"
        assert list(decoded.size) == image["pixels"]
        if mode == "lowbit":
            assert image["png_bit_depth"] == 2
            assert set(decoded.convert("L").tobytes()) <= {0, 85, 170, 255}


def test_all_four_models_receive_identical_bounded_focus_evidence(parent: Path) -> None:
    source = observation(parent)
    bodies = [request([source], model, "focus-rgb-128") for model in MODELS]
    assert len(bodies) == 4
    assert all(body["state"] == bodies[0]["state"] and body["questions"] == bodies[0]["questions"] for body in bodies)
    assert all(non_image_bytes(body) <= 1800 for body in bodies)
    reference = json.loads(bodies[0]["state"][0])["observations"]
    for mode in MODES:
        for size in SIZES:
            factored = request([source], MODELS[0], f"focus-{mode}-{size}")
            assert json.loads(factored["state"][0])["observations"] == reference
    expanded_image = deepcopy(bodies[0])
    expanded_image["state"][1]["image_url"]["url"] += "x" * 10000
    assert non_image_bytes(expanded_image) == non_image_bytes(bodies[0])
    expanded_question = deepcopy(bodies[0])
    expanded_question["questions"]["q0"]["instructions"] += "x" * 1000
    assert non_image_bytes(expanded_question) == non_image_bytes(bodies[0]) + 1000
    with pytest.raises(ValueError, match="unadmitted"):
        request([source], MODELS[2], "rich-rgb-128")


def test_focus_prepare_covers_every_model_arm_and_verifies(parent: Path, tmp_path: Path) -> None:
    catalog = tmp_path / "complete-catalog.json"
    catalog.write_text(json.dumps({"prices": {model: {"input": 0.1, "output": 0.0} for model in MODELS}}))
    directory = tmp_path / "images"
    manifest = prepare(parent, directory, catalog=catalog)
    assert manifest["models"] == list(MODELS)
    assert len(manifest["records"]) == len(manifest["pages"]) * len(MODELS) * len(MODES) * len(SIZES)
    assert verify(directory) == manifest
    assert all(record["non_image_bytes"] <= 1800 for record in manifest["records"])
    manifest["records"].pop()
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="incomplete"):
        verify(directory)
