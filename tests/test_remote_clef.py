# The mock mirrors the dynamically typed external helper contract.
# ruff: noqa: ANN401

"""CPU mock checks for pinned Clef translation, admission and native responses."""

import hashlib
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import remote_clef
from PIL import Image


class Helper:
    """Observe the native boundary without loading torch or weights."""

    def __init__(self, length: int = 100) -> None:
        """Freeze the source input token count for admission checks."""
        self.length = length
        self.calls = 0
        self.request: dict[str, Any] = {}
        self.response: dict[str, Any] = {
            "model": "clef",
            "answers": {"q0": {"choice": "unresolved"}},
            "usage": {"input_tokens": 100},
        }

    def encode_record(self, _tokenizer: Any, request: dict[str, Any], **kwargs: Any) -> Any:
        """Expose complete source tokens without a model call."""
        assert kwargs["max_length"] > remote_clef.MAX_LENGTH
        self.request = request
        return SimpleNamespace(input_ids=range(self.length))

    def systemone(self, _model: Any, _processor: Any, _request: dict[str, Any], **kwargs: Any) -> Any:
        """Return an intentionally sparse native response unchanged."""
        assert kwargs["max_length"] == remote_clef.MAX_LENGTH
        self.calls += 1
        return self.response


def body() -> dict[str, Any]:
    """Supply only source evidence and the shared decision menu."""
    return {
        "model": "clef",
        "state": [
            "Literal state: \u0394\n{}",
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,frozen"}},
        ],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Which grouping is supported?",
                "criteria": {"join": "one group", "split": "two groups", "unresolved": "insufficient evidence"},
            }
        },
    }


def test_native_image_and_literal_text_preserved(tmp_path: Path) -> None:
    image = tmp_path / "crop.png"
    Image.new("RGB", (5, 3), (4, 7, 10)).save(image)
    request = body()
    before = deepcopy(request)
    helper = Helper()
    engine = remote_clef.Engine(object(), SimpleNamespace(tokenizer=object()), helper)
    result = remote_clef.predict(engine, request, [image])
    assert request == before
    assert helper.request["state"] == request["state"][0]
    assert helper.request["questions"] == request["questions"]
    assert helper.request["images"][0].tobytes() == Image.open(image).tobytes()
    assert result is helper.response
    assert "confidence" not in result["answers"]["q0"]
    assert "output_tokens" not in result["usage"]
    assert helper.calls == 1


def test_complete_input_refused_before_model() -> None:
    helper = Helper(remote_clef.MAX_LENGTH + 1)
    engine = remote_clef.Engine(object(), SimpleNamespace(tokenizer=object()), helper)
    request = body()
    request["state"] = {"observations": {"q0": "literal source"}}
    with pytest.raises(ValueError, match="complete source input"):
        remote_clef.predict(engine, request, [])
    assert helper.calls == 0
    assert helper.request["state"] == request["state"]


def test_text_only_at_limit_preserves_native_usage() -> None:
    helper = Helper(remote_clef.MAX_LENGTH)
    request = body()
    request["state"] = "literal source"
    engine = remote_clef.Engine(object(), SimpleNamespace(tokenizer=None), helper)
    assert remote_clef.predict(engine, request, []) is helper.response
    assert "images" not in helper.request


@pytest.mark.parametrize("change", ["missing_paths", "two_texts", "mixed_images", "extra_field"])
def test_unsupported_evidence_shapes_refused(change: str) -> None:
    request = body()
    if change == "two_texts":
        request["state"].insert(0, "second literal text")
    elif change == "mixed_images":
        request["images"] = ["source.png"]
    elif change == "extra_field":
        request["max_state_tokens"] = 1
    with pytest.raises(ValueError, match=r"paths|literal text|mixed|unsupported"):
        remote_clef.predict(remote_clef.Engine(None, None, None), request, [])


def test_unpinned_helper_refused_before_import(tmp_path: Path) -> None:
    (tmp_path / "joint_schema_model.py").write_text("raise AssertionError('must not execute')")
    with pytest.raises(ValueError, match="pinned release"):
        remote_clef.load(tmp_path, device="cpu")


def test_missing_local_directory_refused(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        remote_clef.load(tmp_path / "missing")


def test_incomplete_response_refused() -> None:
    helper = Helper()
    helper.response["answers"] = {}
    request = body()
    request["state"] = "literal source"
    engine = remote_clef.Engine(object(), SimpleNamespace(tokenizer=None), helper)
    with pytest.raises(ValueError, match="source questions"):
        remote_clef.predict(engine, request, [])


def test_load_uses_local_files_and_requested_device(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = b"# inert mock source\n"
    (tmp_path / "joint_schema_model.py").write_bytes(source)
    digest = hashlib.sha256(source).hexdigest()
    monkeypatch.setattr(remote_clef, "HELPER_SHA256", digest)
    calls = []

    def fake_load(directory: Path, **kwargs: Any) -> tuple[object, object]:
        calls.append((directory, kwargs))
        return object(), object()

    helper = SimpleNamespace(load_release_model=fake_load)
    monkeypatch.setitem(sys.modules, "_jev_remote_clef_" + digest, helper)
    engine = remote_clef.load(tmp_path, device="cpu")
    assert engine.helper is helper
    assert calls == [(tmp_path.resolve(), {"device": "cpu", "local_files_only": True})]


def test_top_level_native_images_and_all_question_types(tmp_path: Path) -> None:
    image = tmp_path / "crop.png"
    Image.new("L", (2, 3), 72).save(image)
    request = body()
    request["state"] = {"observations": {"q0": "source chars"}}
    request["images"] = ["frozen-image-reference"]
    request["questions"]["q1"] = {"type": "noul", "instructions": "Is the header visible?"}
    request["questions"]["q2"] = {"type": "score", "criteria": ["unclear", "clear"]}
    helper = Helper()
    helper.response["answers"].update({"q1": {"noul": 0.7}, "q2": {"score": 0.8}})
    engine = remote_clef.Engine(None, SimpleNamespace(tokenizer=None), helper)
    assert remote_clef.predict(engine, request, [image]) is helper.response
    assert helper.request["state"] == request["state"]
    assert helper.request["questions"] == request["questions"]
    assert helper.request["images"][0].mode == "L"


def test_image_pixel_admission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    image = tmp_path / "crop.png"
    Image.new("RGB", (3, 3)).save(image)
    monkeypatch.setattr(remote_clef, "MAX_IMAGE_PIXELS", 8)
    with pytest.raises(ValueError, match="pixel bound"):
        remote_clef.predict(remote_clef.Engine(None, None, None), body(), [image])
