"""CPU-only mocked local server tests; never execute model inference."""

import base64
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import remote_vllm as stock


def canonical() -> dict[str, Any]:
    return {
        "state": [" exact source\n"],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "group source",
                "criteria": {"join": "one row", "split": "two rows", "unresolved": "unknown"},
            }
        },
    }


def test_load_is_local_configuration_only(tmp_path: Path) -> None:
    directory = tmp_path / "Qwen3.5-9B"
    directory.mkdir()
    engine = stock.load(directory)
    assert engine.model_id == "Qwen/Qwen3.5-9B"
    assert engine.base_url == "http://127.0.0.1:8000/v1"
    with pytest.raises(ValueError, match="loopback"):
        stock.load(directory, base_url="https://provider.example/v1")
    with pytest.raises(ValueError, match="actual model_id"):
        stock.load(tmp_path)


def test_request_preserves_source_questions_and_order(tmp_path: Path) -> None:
    paths = [tmp_path / "second.png", tmp_path / "first.png"]
    for index, path in enumerate(paths):
        path.write_bytes(b"mock image" + bytes([index]))
    body = canonical()
    for path in paths:
        body["state"].append(
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()},
            }
        )
    before = deepcopy(body)
    request = stock.request_body(stock.Engine(stock.MODEL_ID, "http://127.0.0.1:8000/v1"), body, paths)
    content = request["messages"][1]["content"]
    assert content[0] == {"type": "text", "text": body["state"][0]}
    assert content[1:3] == body["state"][1:]
    assert json.loads(content[-1]["text"]) == {"questions": body["questions"]}
    assert request["structured_outputs"]["json"]["properties"]["q0"]["enum"] == list(stock.CHOICES)
    assert request["chat_template_kwargs"] == {"enable_thinking": False}
    assert request["temperature"] == 0
    assert body == before


def test_qwen_request_bytes_preserve_original_prompt() -> None:
    request = stock.request_body(stock.Engine(stock.MODEL_ID, "http://127.0.0.1:8000/v1"), canonical(), [])
    raw = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
    assert hashlib.sha256(raw).hexdigest() == "cdd7a05a7324aee4122eb507fec0d5a2cd7c4f94cb2d5c94f9aa061349083b0f"


@pytest.mark.parametrize(
    "model_id",
    ["HuggingFaceTB/SmolVLM2-2.2B-Instruct", "LiquidAI/LFM2-VL-1.6B", "openbmb/MiniCPM-V-4"],
)
def test_non_qwen_models_preserve_evidence_without_thinking_args(tmp_path: Path, model_id: str) -> None:
    directory = tmp_path / model_id.rsplit("/", maxsplit=1)[-1]
    directory.mkdir()
    engine = stock.load(directory)
    assert engine.model_id == model_id
    image = tmp_path / "retained.png"
    image.write_bytes(b"frozen source PNG")
    body = canonical()
    body["state"].append(
        {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode()},
        }
    )
    original = deepcopy(body)
    request = stock.request_body(engine, body, [image])
    qwen_request = stock.request_body(stock.Engine(stock.MODEL_ID, engine.base_url), body, [image])
    qwen_request["model"] = model_id
    del qwen_request["chat_template_kwargs"]
    assert request == qwen_request
    assert request["messages"][1]["content"][1] == body["state"][1]
    assert json.loads(request["messages"][1]["content"][-1]["text"]) == {"questions": body["questions"]}
    assert body == original


def test_smolvlm_single_image_contract_refuses_multiple_images(tmp_path: Path) -> None:
    image = tmp_path / "source.png"
    image.write_bytes(b"source")
    part = {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode()},
    }
    body = canonical()
    body["state"].extend([part, deepcopy(part)])
    engine = stock.Engine("HuggingFaceTB/SmolVLM2-2.2B-Instruct", "http://127.0.0.1:8000/v1")
    with pytest.raises(ValueError, match="one image"):
        stock.request_body(engine, body, [image, image])


def test_choice_only_response_retains_usage_without_probability_invention(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "model": stock.MODEL_ID,
        "choices": [{"finish_reason": "stop", "message": {"content": '{"q0":"split"}'}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 8, "total_tokens": 108},
    }
    monkeypatch.setattr(stock.Engine, "post", lambda *_: response)
    result = stock.predict(stock.Engine(stock.MODEL_ID, "http://127.0.0.1:8000/v1"), canonical(), [])
    assert result["answers"]["q0"] == {"type": "choice", "choice": "split", "decision": "split"}
    assert result["usage"] == response["usage"]
    assert result["raw_response"] == response
    assert result["runtime_elapsed_seconds"] >= 0
    del response["usage"]
    assert "usage" not in stock.predict(stock.Engine(stock.MODEL_ID, "http://127.0.0.1:8000/v1"), canonical(), [])


@pytest.mark.parametrize(
    ("content", "finish"), [('{"q0":"invalid"}', "stop"), ('{"q1":"join"}', "stop"), ('{"q0":"join"}', "length")]
)
def test_rejects_incomplete_or_non_schema_labels(content: str, finish: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        stock.Engine,
        "post",
        lambda *_: {"model": stock.MODEL_ID, "choices": [{"finish_reason": finish, "message": {"content": content}}]},
    )
    with pytest.raises(ValueError, match=r"schema|incomplete"):
        stock.predict(stock.Engine(stock.MODEL_ID, "http://127.0.0.1:8000/v1"), canonical(), [])


def test_mismatched_pixels_refused_before_server_call(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"other")
    body = canonical()
    body["state"].append({"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}})
    with pytest.raises(ValueError, match="exact canonical image"):
        stock.request_body(stock.Engine(stock.MODEL_ID, "http://127.0.0.1:8000/v1"), body, [image])
