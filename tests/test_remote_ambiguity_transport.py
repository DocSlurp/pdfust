"""Exact source prefix and imagery survive one-segment transport correction."""

# ruff: noqa: ANN001, ANN201 - pytest fixtures and native pure admission helper.
import base64
import io

import pytest
from bench.remote_ambiguity_transport import project
from bench.remote_clef import _request
from PIL import Image


def test_exact_prefix_supplement_questions_image_and_adapter_admission(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")
    png = buffer.getvalue()
    path = tmp_path / "source.png"
    path.write_bytes(png)
    literal = ' {"observations":{"q0":{"text":"a b"}}} '
    supplemental = '{"supplemental_evidence":{"geometry_font_scale":12}}'
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}
    original = {
        "model": "original",
        "state": [literal, image, supplemental],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "unchanged",
                "criteria": {"join": "join", "split": "split", "unresolved": "unknown"},
            }
        },
    }
    result = project(original)
    assert result["state"] == [literal + "\n" + supplemental, image]
    assert original["state"] == [literal, image, supplemental]
    assert result["model"] == original["model"]
    assert result["questions"] == original["questions"]
    native = _request(result, [path])
    assert native["state"] == result["state"][0]
    assert native["questions"] == result["questions"]


def test_unknown_extra_text_cannot_be_collapsed():
    with pytest.raises(ValueError, match="presentation"):
        project({"state": ["one", {}, "two", "three"]})
    with pytest.raises(ValueError, match="supplemental"):
        project({"state": ["one", {"type": "image_url"}, '{"choice":"join"}']})
