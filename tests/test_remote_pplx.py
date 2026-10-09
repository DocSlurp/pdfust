"""CPU mocks for the pinned native adapter; no torch, weights or device work."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import remote_pplx as adapter


def body() -> dict[str, Any]:
    return {
        "model": adapter.HOSTED_MODEL,
        "state": "Literal source:  10.00; Ω\nkeep spaces",
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Keep source data literal.",
                "criteria": {"join": "one group", "split": "two groups", "unresolved": "insufficient evidence"},
            },
            "q1": {
                "type": "choice",
                "instructions": "Second unchanged question",
                "criteria": {"yes": None, "no": "No"},
            },
        },
    }


class Native:
    """Mock the supplied native predictor without importing its dependencies."""

    def __init__(self) -> None:
        """Retain predictor calls."""
        self.calls: list[Any] = []

    def predict(self, rows: list[Any], **kwargs: object) -> list[list[float]]:
        """Return already calibrated candidate probabilities."""
        self.calls.append((deepcopy(rows), kwargs))
        return [[0.6, 0.3, 0.1], [0.2, 0.8]]


def formatter(question: dict[str, Any], probabilities: list[float]) -> dict[str, Any]:
    options = list(question["criteria"])
    choice = options[max(range(len(probabilities)), key=probabilities.__getitem__)]
    return {"choice": choice, "probabilities": dict(zip(options, probabilities, strict=True)), "confidence": 0.7}


def engine() -> adapter.Engine:
    return adapter.Engine(Native(), formatter, {})


def test_exact_literal_questions_and_calibration_once() -> None:
    native, source = engine(), body()
    original = deepcopy(source)
    result = adapter.predict(native, source, [])
    rows, kwargs = native.model.calls[0]
    assert kwargs == {"batch_size": 1}  # no temperature or second calibration
    assert [row["question"] for row in rows] == list(source["questions"].values())
    assert all(row["state"] == source["state"] for row in rows)
    assert result["answers"]["q0"]["probabilities"] == {"join": 0.6, "split": 0.3, "unresolved": 0.1}
    assert result["answers"]["q1"]["choice"] == "no"
    assert all("confidence" not in answer for answer in result["answers"].values())
    assert set(result) == {"answers"}
    assert source == original


def test_staged_images_verified_and_source_ids_never_added(tmp_path: Path) -> None:
    raw = b"retained image bytes"
    image = tmp_path / "private-filename.png"
    image.write_bytes(raw)
    source, native = body(), engine()
    literal = source["state"]
    source["state"] = [
        literal,
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(raw).decode()}},
    ]
    adapter.predict(native, source, [image])
    rows = native.model.calls[0][0]
    assert all(row["state"] == literal and row["images"] == [image] for row in rows)
    assert "private-filename" not in rows[0]["state"]
    image.write_bytes(b"different bytes")
    with pytest.raises(ValueError, match="differ"):
        adapter.predict(native, source, [image])
    assert len(native.model.calls) == 1


def test_multiple_literals_keep_values_and_order() -> None:
    source, native = body(), engine()
    source["state"] = ["first  ", "\nsecond"]
    adapter.predict(native, source)
    assert native.model.calls[0][0][0]["state"] == source["state"]


@pytest.mark.parametrize(
    "mutation", ["unsupported", "remote", "reordered", "duplicate", "extra", "wrong-model", "count", "large"]
)
def test_source_refusal_before_native_inference(mutation: str) -> None:
    source, native = body(), engine()
    url = "data:image/png;base64,YQ=="
    part = {"type": "image_url", "image_url": {"url": url}}
    paths: list[Path] | None = None
    if mutation == "unsupported":
        source["state"] = ["literal", {"type": "unknown", "secret": "not discarded"}]
    elif mutation == "remote":
        source["images"] = ["https://example.com/image.png"]
    elif mutation == "reordered":
        source["state"] = [part, "literal"]
    elif mutation == "duplicate":
        source["state"], source["images"] = ["literal", part], [url]
    elif mutation == "extra":
        source["expected"] = "join"
    elif mutation == "wrong-model":
        source["model"] = "generic/chat"
    elif mutation == "count":
        source["images"], paths = [url], []
    else:
        source["state"] = "x" * adapter.MAX_BODY_BYTES
    with pytest.raises(ValueError, match="PPLX"):
        adapter.predict(native, source, paths)
    assert not native.model.calls


@pytest.mark.parametrize(
    "probabilities", [[[0.5, 0.5]], [[float("nan"), 0.3, 0.7], [0.2, 0.8]], [[0.6, 0.3, 0.2], [0.2, 0.8]]]
)
def test_malformed_native_distributions_refuse(probabilities: list[Any]) -> None:
    native = adapter.Engine(SimpleNamespace(predict=lambda _rows, **_kw: probabilities), formatter, {})
    with pytest.raises(ValueError, match=r"inventory|count"):
        adapter.predict(native, body())


def test_overflow_is_not_truncated() -> None:
    def overflow(_rows: list[Any], **_kwargs: object) -> None:
        message = "Question branch exceeds the 8192-token limit; no input was truncated."
        raise ValueError(message)

    native = adapter.Engine(SimpleNamespace(predict=overflow), formatter, {})
    with pytest.raises(ValueError, match="8192-token"):
        adapter.predict(native, body())


def checkpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config = {
        "base_model": "Qwen/Qwen3.8-27B",
        "revision": adapter.BASE_REVISION,
        "attention_mode": "noncausal_full_attention",
        "pooling": "last",
        "temperature": 1.0087417621345625,
    }
    files = {"decision_config.json": json.dumps(config).encode(), "source/src/autojev/model.py": b"mock source"}
    pins = {}
    for relative, raw in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        pins[relative] = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(adapter, "PINNED_FILES", pins)
    monkeypatch.delitem(sys.modules, "autojev", raising=False)
    monkeypatch.delitem(sys.modules, "autojev.model", raising=False)
    return tmp_path


def test_loader_uses_exact_native_class_and_preserves_saved_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = checkpoint(tmp_path, monkeypatch)
    calls = []

    def constructor(path: Path, **kwargs: object) -> SimpleNamespace:
        calls.append((path, kwargs))
        return SimpleNamespace(attention_mode="noncausal_full_attention", temperature=1.0087417621345625)

    native = SimpleNamespace(
        __file__=directory / "source/src/autojev/model.py", DecisionModel=constructor, answer=formatter
    )
    monkeypatch.setattr(adapter.importlib, "import_module", lambda _name: native)
    before = list(sys.path)
    loaded = adapter.load(directory, device="cuda:0")
    assert calls == [(directory, {"device": "cuda:0"})]
    assert loaded.metadata["revision"] == adapter.REVISION
    assert loaded.metadata["max_combined_tokens_per_question"] == 8192
    assert loaded.metadata["image_processor_max_pixels"] == 2048 * 2048
    assert sys.path == before


def test_loader_pins_refuse_modified_code_before_import(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = checkpoint(tmp_path, monkeypatch)
    (directory / "source/src/autojev/model.py").write_text("modified source")
    monkeypatch.setattr(adapter.importlib, "import_module", lambda _name: pytest.fail("must refuse before import"))
    with pytest.raises(ValueError, match="hash mismatch"):
        adapter.load(directory)


def test_loader_rejects_cross_checkpoint_package_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = checkpoint(tmp_path, monkeypatch)
    monkeypatch.setitem(sys.modules, "autojev.model", SimpleNamespace(__file__="/different/source/model.py"))
    with pytest.raises(ValueError, match="different autojev"):
        adapter.load(directory)
