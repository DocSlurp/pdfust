"""Mock-only contract tests; no Transformers, GPU or model downloads."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import remote_intern as intern


def canonical() -> dict[str, Any]:
    return {
        "model": "cloudflare/clef",
        "state": [" source  text\n", {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}],
        "questions": {
            "q0": {"type": "choice", "instructions": "Use source only", "criteria": {"join": "a", "split": "b"}}
        },
    }


def test_preserves_exact_text_questions_and_image_order(tmp_path: Path) -> None:
    paths = [tmp_path / "second.png", tmp_path / "first.png"]
    for path in paths:
        path.write_bytes(b"mock image")
    body = canonical()
    body["state"].append(deepcopy(body["state"][1]))
    before = deepcopy(body)
    projected = intern.native_request(body, paths)
    assert projected["state"] == " source  text\n"
    assert projected["questions"] == body["questions"]
    assert projected["images"] == [str(path) for path in paths]
    assert body == before


def test_multiple_text_parts_and_structured_state_are_lossless() -> None:
    body = canonical()
    body["state"] = ["a\n", {"type": "text", "text": " b"}]
    assert intern.native_request(body, [])["state"] == ["a\n", " b"]
    body["state"] = {"geometry": [[1, 2, 3, 4]], "text": "literal"}
    assert intern.native_request(body, [])["state"] == body["state"]


def test_mock_load_uses_pinned_native_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(
        intern, "_runtime", lambda _: SimpleNamespace(DecisionEngine=lambda **kwargs: calls.append(kwargs) or "mock")
    )
    assert intern.load(tmp_path, device="cpu") == "mock"
    assert calls == [
        {
            "checkpoint": str(tmp_path),
            "device": "cpu",
            "backend": "hf",
            "dtype": "bfloat16",
            "attn_implementation": "sdpa",
            "max_length": 8192,
            "media_root": str(tmp_path),
        }
    ]
    assert "temperature" not in calls[0]


def test_runtime_source_mismatch_refuses_before_import(tmp_path: Path) -> None:
    (tmp_path / "inference.py").write_text("raise AssertionError('must not execute')")
    with pytest.raises(ValueError, match="pinned source"):
        intern.load(tmp_path)


def test_native_usage_and_answers_preserved_without_invented_confidence() -> None:
    body = canonical()
    body["state"] = "exact text"
    native = {
        "answers": {"q0": {"choice": "join", "probabilities": {"join": 0.9, "split": 0.1}}},
        "usage": {"input_tokens": 123, "output_tokens": 1},
        "timing": {"inference_ms": 4},
    }
    before = deepcopy(native)
    result = intern.predict(SimpleNamespace(predict=lambda _: native), body, [])
    assert result["answers"] == native["answers"]
    assert result["usage"] == native["usage"]
    assert result["timing"] == native["timing"]
    assert result["runtime_elapsed_seconds"] >= 0
    assert "confidence" not in result["answers"]["q0"]
    assert native == before
    absent = intern.predict(SimpleNamespace(predict=lambda _: {"answers": native["answers"]}), body, [])
    assert "usage" not in absent


def test_rejects_image_mismatch_and_unexpected_answers() -> None:
    with pytest.raises(ValueError, match="image count"):
        intern.native_request(canonical(), [])
    body = canonical()
    body["state"] = "text"
    with pytest.raises(ValueError, match="inventory"):
        intern.predict(SimpleNamespace(predict=lambda _: {"answers": {}}), body, [])
    body["state"] = [{"unsupported": "part"}]
    with pytest.raises(ValueError, match="unsupported"):
        intern.native_request(body, [])
