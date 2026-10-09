"""Mock-only native Nimble v3 text-ablation contract tests."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import remote_nimble as nimble


def canonical() -> dict[str, Any]:
    return {
        "model": "cloudflare/clef",
        "state": [" source  geometry\n"],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Preserve source",
                "criteria": {"join": "one row", "split": "two rows", "unresolved": "unknown"},
            }
        },
    }


def test_exact_literal_state_questions_and_missing_usage_preserved() -> None:
    body = canonical()
    before = deepcopy(body)
    calls = []
    answer = {"answers": {"q0": {"choice": "split", "probabilities": {"join": 0.1, "split": 0.8, "unresolved": 0.1}}}}

    class Mock:
        def synchronize(self) -> None:
            calls.append("sync")

        def __call__(self, state: str, questions: dict[str, Any]) -> tuple[dict[str, Any], None]:
            calls.append((state, deepcopy(questions)))
            return answer, None

    result = nimble.predict(Mock(), body, [])
    assert calls == ["sync", (" source  geometry\n", body["questions"]), "sync"]
    assert result["answers"] == answer["answers"]
    assert "confidence" not in result["answers"]["q0"]
    assert "usage" not in result
    assert result["adapter"]["evidence_scope"] == "geometry-text-only"
    assert body == before


@pytest.mark.parametrize("mode", ["staged", "inline", "top", "structured", "encoded"])
def test_images_refused_before_native_call(mode: str) -> None:
    body = canonical()
    paths = []
    if mode == "staged":
        paths = ["not-read.png"]
    elif mode == "inline":
        body["state"].append({"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}})
    elif mode == "top":
        body["images"] = ["not-read.png"]
    elif mode == "structured":
        body["state"] = {"observations": {"crop": {"png_base64": "AA=="}}}
    else:
        body["state"] = json.dumps({"type": "image_url", "image_url": {"url": "ignored-pixels"}})
    with pytest.raises(ValueError, match="image"):
        nimble.predict(SimpleNamespace(), body, paths)


def test_mock_load_uses_complete_native_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "base").mkdir()
    (tmp_path / "reference").mkdir()
    contract = {
        "model": nimble.BASE_MODEL_ID,
        "revision": nimble.BASE_REVISION,
        "task": "schema_candidate_classification_v2",
        "prompt_source_sha256": {
            name: nimble.SOURCE_SHA256[name] for name in ("parallel_schema.py", "extended_schema.py")
        },
    }
    (tmp_path / "schema_config.json").write_text(json.dumps(contract))
    calls = []
    monkeypatch.setattr(
        nimble, "_reference", lambda _: SimpleNamespace(NimbleEngine=lambda **kwargs: calls.append(kwargs) or "mock")
    )
    assert nimble.load(tmp_path) == "mock"
    assert calls[0] == {
        "adapter": str(tmp_path),
        "model": str(tmp_path / "base"),
        "revision": nimble.BASE_REVISION,
        "max_tokens": 32768,
        "batch_tokens": 65536,
        "shared_prefix": True,
        "cache_tokens": 131072,
    }
    assert "temperature" not in calls[0]
    contract["revision"] = "wrong"
    (tmp_path / "schema_config.json").write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="contract"):
        nimble.load(tmp_path)


def test_native_usage_retained_and_context_not_truncated() -> None:
    body = canonical()

    class Mock:
        def synchronize(self) -> None:
            pass

        def __call__(self, state: str, questions: dict[str, Any]) -> tuple[dict[str, Any], None]:
            assert state == body["state"][0]
            assert questions == body["questions"]
            return {
                "answers": {
                    "q0": {"choice": "join", "probabilities": {"join": 0.9, "split": 0.05, "unresolved": 0.05}}
                },
                "usage": {"input_tokens": 100},
            }, None

    result = nimble.predict(Mock(), body, [])
    assert result["usage"] == {"input_tokens": 100}
    assert "output_tokens" not in result["usage"]
    assert "float64" in result["adapter"]["calibration"]
    body["questions"]["q0"]["criteria"] = dict.fromkeys(map(str, range(256)), "description")
    with pytest.raises(ValueError, match="bounded"):
        nimble.predict(Mock(), body, [])


def test_native_context_refusal_is_propagated_without_retry() -> None:
    calls = []

    class Mock:
        def synchronize(self) -> None:
            pass

        def __call__(self, state: str, _questions: dict[str, Any]) -> tuple[dict[str, Any], None]:
            calls.append(state)
            message = "maximum context length"
            raise ValueError(message)

    body = canonical()
    with pytest.raises(ValueError, match="maximum context"):
        nimble.predict(Mock(), body, [])
    assert calls == [body["state"][0]]


def test_forged_reference_source_refused_before_import(tmp_path: Path) -> None:
    package = tmp_path / "nimble" / "evaluation"
    package.mkdir(parents=True)
    (package / "decision_index_engine.py").write_text("raise AssertionError('must not run')")
    with pytest.raises(ValueError, match="pinned reference"):
        nimble._reference(tmp_path)  # noqa: SLF001 - admission tested before any optional import.
