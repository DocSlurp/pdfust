"""CPU-only JPT runtime mocks; no torch, model weights, inference or secrets."""

from __future__ import annotations

import base64
import hashlib
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import remote_jpt as adapter


def body() -> dict[str, Any]:
    return {
        "model": "kirp/jpt-4b",
        "state": "Literal source  Ω\nA  B; 10.00",
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Choose source grouping.",
                "criteria": {"join": "one group", "split": "two groups", "unresolved": "insufficient evidence"},
            }
        },
    }


class Scorer:
    """Retain native inputs and return an already calibrated named distribution."""

    def __init__(self) -> None:
        """Initialize CPU call retention."""
        self.calls: list[Any] = []

    def __call__(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:  # noqa: ANN401
        """Return the native full Choice menu without generation."""
        self.calls.append((deepcopy(state), deepcopy(questions)))
        return {
            name: {
                "type": "choice",
                "choice": "join",
                "probabilities": {"join": 0.6, "split": 0.3, "unresolved": 0.1},
                "confidence": 0.123,
            }
            for name in questions
        }


def engine() -> adapter.Engine:
    return adapter.Engine(Scorer(), {"model": "kirp/jpt-4b"})


def test_literal_questions_native_calibration_retained() -> None:
    source, native = body(), engine()
    original = deepcopy(source)
    result = adapter.predict(native, source, [])
    assert native.scorer.calls == [(source["state"], source["questions"])]
    assert result == {
        "answers": {
            "q0": {"type": "choice", "choice": "join", "probabilities": {"join": 0.6, "split": 0.3, "unresolved": 0.1}}
        }
    }
    assert source == original


def test_images_translate_to_official_chat_parts_without_reordering(tmp_path: Path) -> None:
    source, native = body(), engine()
    image = tmp_path / "private-source-name.png"
    image.write_bytes(b"frozen bytes")
    url = "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode()
    source["state"] = ["first  ", {"type": "image_url", "image_url": {"url": url}}, "\nsecond"]
    adapter.predict(native, source, [image])
    assert native.scorer.calls[0][0] == [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "first  "},
                {"type": "image", "image": url},
                {"type": "text", "text": "\nsecond"},
            ],
        }
    ]
    image.write_bytes(b"changed bytes")
    with pytest.raises(ValueError, match="differs"):
        adapter.predict(native, source, [image])
    assert len(native.scorer.calls) == 1


@pytest.mark.parametrize(
    "mutation", ["unsupported", "remote", "duplicate", "model", "extra", "questions", "large", "chat"]
)
def test_refusal_before_native_scoring(mutation: str) -> None:
    source, native = body(), engine()
    url = "data:image/png;base64,YQ=="
    if mutation == "unsupported":
        source["state"] = ["source", {"type": "unknown"}]
    elif mutation == "remote":
        source["images"] = ["https://example.com/image.png"]
    elif mutation == "duplicate":
        source["state"], source["images"] = ["source", {"type": "image_url", "image_url": {"url": url}}], [url]
    elif mutation == "model":
        source["model"] = "generic/chat"
    elif mutation == "extra":
        source["expected"] = "join"
    elif mutation == "questions":
        source["questions"]["q0"]["criteria"] = {"only": "wrong menu"}
    elif mutation == "chat":
        source["state"] = {"messages": [{"role": "user", "content": "outside contract"}]}
    else:
        source["state"] = "x" * adapter.MAX_BODY_BYTES
    with pytest.raises(ValueError, match="JPT"):
        adapter.predict(native, source)
    assert not native.scorer.calls


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"type": "choice", "choice": "split", "probabilities": {"join": 0.6, "split": 0.3, "unresolved": 0.1}},
        {"type": "choice", "choice": "join", "probabilities": {"join": 0.6, "split": 0.3, "unresolved": 0.3}},
    ],
)
def test_bad_native_answer_refuses(answer: dict[str, Any]) -> None:
    native = adapter.Engine(lambda _state, _questions: {"q0": answer}, {"model": "kirp/jpt-4b"})
    with pytest.raises(ValueError, match="probabilities"):
        adapter.predict(native, body())


def test_actual_combined_token_admission() -> None:
    adapter.admit_tokens(None, (), {"input_ids": SimpleNamespace(shape=(1, adapter.MAX_COMBINED_TOKENS))})
    with pytest.raises(ValueError, match="32768"):
        adapter.admit_tokens(None, (), {"input_ids": SimpleNamespace(shape=(1, adapter.MAX_COMBINED_TOKENS + 1))})


@pytest.mark.parametrize(("name", "temperature"), [("kirp/jpt-4b", 1.036), ("kirp/jpt-9b", 1.087)])
def test_pinned_loader_uses_official_hf_scorer_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, temperature: float
) -> None:
    model_dir, runtime = tmp_path / "model", tmp_path / "llm2jev"
    model_dir.mkdir()
    runtime.mkdir()
    config = b"pinned mock config"
    (model_dir / "config.json").write_bytes(config)
    monkeypatch.setattr(
        adapter,
        "MODELS",
        {name: {"config_sha256": hashlib.sha256(config).hexdigest(), "revision": "a" * 40, "temperature": temperature}},
    )
    monkeypatch.setattr(adapter, "PROCESSOR_PINS", {})
    (runtime / "__init__.py").write_bytes(b"pinned mock runtime")
    monkeypatch.setattr(
        adapter, "RUNTIME_PINS", {"__init__.py": hashlib.sha256((runtime / "__init__.py").read_bytes()).hexdigest()}
    )
    monkeypatch.setattr(
        adapter.importlib.util, "find_spec", lambda _name: SimpleNamespace(origin=runtime / "__init__.py")
    )
    calls: list[Any] = []
    hooks: list[Any] = []
    backend = SimpleNamespace(
        processor="processor",
        tok="tokenizer",
        model=SimpleNamespace(register_forward_pre_hook=lambda hook, **kw: hooks.append((hook, kw))),
    )

    def make_hf(path: str, **kwargs: object) -> Any:  # noqa: ANN401
        calls.append((path, kwargs))
        return backend

    def make_scorer(processor: str, loaded_backend: Any, **kwargs: object) -> Scorer:  # noqa: ANN401
        calls.append((processor, loaded_backend, kwargs))
        return Scorer()

    module = SimpleNamespace(__file__=runtime / "__init__.py", LLM2Jev=make_scorer)
    backends = SimpleNamespace(__file__=runtime / "backends.py", HF=make_hf)
    monkeypatch.setattr(
        adapter.importlib, "import_module", lambda module_name: module if module_name == "llm2jev" else backends
    )
    native = adapter.load(model_dir)
    assert calls[0] == (str(model_dir), {"device": "cuda", "dtype": "bfloat16"})
    assert calls[1] == ("processor", backend, {"temperature": temperature, "style": "chat", "workers": 1})
    assert hooks == [(adapter.admit_tokens, {"with_kwargs": True})]
    assert native.metadata["model"] == name
    assert native.metadata["temperature"] == temperature
    (runtime / "__init__.py").write_bytes(b"changed runtime")
    with pytest.raises(ValueError, match="hash mismatch"):
        adapter.load(model_dir)
    assert len(calls) == 2
