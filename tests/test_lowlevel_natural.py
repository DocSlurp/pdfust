"""Natural geometry selection, evidence admission and separate annotation checks."""

import base64
import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench.lowlevel_natural import ARMS, MODELS, annotate, prepare, request, select, verify
from PIL import Image

SOURCE = Path(__file__).parent / "assets/real_world/senate-expenditures.pdf"


@pytest.fixture(scope="module")
def frozen(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("natural") / "freeze"
    prepare(SOURCE, directory)
    return directory


def test_selection_is_source_geometry_and_exact_inventory(frozen: Path) -> None:
    selection = select(SOURCE.read_bytes())
    assert len(selection["pairs"]) == 24
    assert {pair["page_index"] for pair in selection["pairs"]} == {0}
    assert len({pair["id"] for pair in selection["pairs"]}) == 24
    assert [pair["line_indices"] for pair in selection["pairs"]] == [
        [index, index + 1] for index in list(range(9)) + list(range(10, 25))
    ]
    assert all("choice" not in pair and "expected" not in pair for pair in selection["pairs"])
    manifest = verify(frozen)
    assert len(manifest["records"]) == 24 * len(ARMS)
    assert not (frozen / "private-references.json").exists()
    with pytest.raises(ValueError, match="12 to 24"):
        select(SOURCE.read_bytes(), count=25)


def test_same_literal_actions_and_fresh_pixel_provenance(frozen: Path) -> None:
    manifest = verify(frozen)
    for page in manifest["pages"]:
        observation = json.loads((frozen / page["observation_file"]).read_bytes())
        before = deepcopy(observation)
        observation["expected"] = "DO NOT SEND"
        observation["family"] = "DO NOT SEND"
        questions = []
        for arm in ARMS:
            body = request(observation, MODELS[0], arm)
            assert "DO NOT SEND" not in json.dumps(body)
            state = json.loads(body["state"][0])
            assert state["observations"]["q0"]["target_boxes"] == observation["selector"]["target"]["boxes"]
            assert set(body["questions"]["q0"]["criteria"]) == {"join", "split", "unresolved"}
            questions.append(body["questions"])
            raster = observation["images"][arm]
            with Image.open(io.BytesIO(base64.b64decode(raster["png_base64"]))) as image:
                assert list(image.size) == raster["pixels"]
                assert image.mode == "RGB"
                assert max(image.tobytes()) > min(image.tobytes())
            assert "fresh source render" in raster["method"]
            assert abs(raster["pixels"][0] - int(arm.split("-")[1])) <= 1
        assert all(question == questions[0] for question in questions)
        for model in (*MODELS, "liquid/d1"):
            assert request(observation, model, ARMS[0])["state"] == request(observation, MODELS[0], ARMS[0])["state"]
        observation.pop("expected")
        observation.pop("family")
        assert observation == before


def test_annotation_requires_complete_separate_references(frozen: Path, tmp_path: Path) -> None:
    import shutil  # noqa: PLC0415 - isolate mutable scorer artifact.

    isolated = tmp_path / "copy"
    shutil.copytree(frozen, isolated)
    manifest = verify(isolated)
    references = [
        {
            "id": page["id"],
            "choice": "unresolved",
            "evidence": "review pending",
            "uncertainty": "Not independently adjudicated",
        }
        for page in manifest["pages"]
    ]
    before = (isolated / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="complete separate"):
        annotate(isolated, references[:-1])
    result = annotate(isolated, references)
    assert "Single source-aware" in result["annotation"]
    assert (isolated / "manifest.json").read_bytes() == before
    assert verify(isolated) == manifest
    with pytest.raises(ValueError, match="Preserve existing"):
        annotate(isolated, references)
    manifest["records"].pop()
    (isolated / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="incomplete"):
        verify(isolated)
