from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from bench import decision_hosted as hosted
from bench import decisions as runner

REQUESTED_MODELS = (
    "perplexity/pplx-decider-v1.1-27b",
    "upstage/solar-decide-flash",
    "openai/gpt-6-luna-decisions",
    "liquid/d1",
    "cloudflare/clef-flash",
    "togethercomputer/tev1-4b-experimental",
    "inception/mercury-decide",
    "respan/span-01",
)


@pytest.fixture
def cases() -> list[dict[str, Any]]:
    return [
        {
            "question": "Does the value belong to the label?",
            "gold": True,
            "split": "test",
            "state": {
                "task": "assignment",
                "words": [{"id": 0, "text": "Amount"}, {"id": 1, "text": "120 USD"}],
                "candidate": {"label": [0], "value": [1], "alternatives": [[1]]},
            },
        }
    ]


@pytest.mark.parametrize("model", REQUESTED_MODELS)
def test_requested_models_use_native_questions_and_probability_parser(
    model: str,
    cases: list[dict[str, Any]],
) -> None:
    body = hosted.request_body(model, cases, "rich")
    assert body["model"] == model
    assert set(body) == {"model", "state", "questions"}
    assert set(body["questions"]) == {"q0_yes", "q0_answerable"}
    assert all(question["type"] == "noul" for question in body["questions"].values())
    assert "gold" not in json.dumps(body)
    result = {
        "answers": {
            "q0_yes": {"type": "noul", "noul": 0.2},
            "q0_answerable": {"type": "noul", "noul": 0.9},
        }
    }
    assert hosted.parse_answers(model, result, 1) == [{"p_yes": 0.2, "p_answerable": 0.9}]
    result["answers"].pop("q0_answerable")
    with pytest.raises(ValueError, match="keys"):
        hosted.parse_answers(model, result, 1)


@pytest.mark.parametrize("model", [*REQUESTED_MODELS, *hosted.DEFAULT_MODELS])
def test_catalog_routes_with_reservation_and_dummy_prior_ledger(
    model: str,
    cases: list[dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hosted, "read_key", lambda _root: "dummy-catalog-test-key")
    prior = tmp_path / "bench/results/structure-artifacts/hosted-ledger.json"
    prior.parent.mkdir(parents=True)
    prior.write_text(json.dumps({"requests": [{"accounted_usd": 0.12}]}))
    client = hosted.DecisionClient(tmp_path)
    body = hosted.request_body(model, cases, "rich")
    endpoint = "alpha/decisions" if model in (*REQUESTED_MODELS, hosted.JEV) else "v1/chat/completions"

    def transmit(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401
        reserved = json.loads(client.ledger.read_text())["requests"][0]
        assert reserved["requested_model"] == model
        assert reserved["case_count"] == 1
        assert reserved["accounted_usd"] == hosted.RESERVATION
        assert reserved["prior_accounted_usd"] == pytest.approx(hosted.PRIOR_RENTAL + 0.12)
        assert request.full_url == "https://openrouter.ai/api/" + endpoint
        assert json.loads(request.data) == body
        assert timeout == 90
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"usage": {"cost": 0.001}}).encode()
        return response

    mock = MagicMock(side_effect=transmit)
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    outcome = client.request(body, tag="catalog-routing")
    assert outcome["entry"]["accounted_usd"] == 0.001
    assert outcome["entry"]["cost_status"] == "provider-reported USD"
    assert mock.call_count == 1
    assert "dummy-catalog-test-key" not in client.ledger.read_text()


@pytest.mark.parametrize("model", REQUESTED_MODELS)
def test_native_question_limit_refuses_before_ledger_or_network(
    model: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hosted, "read_key", lambda _root: "dummy-catalog-test-key")
    client = hosted.DecisionClient(tmp_path)
    body = {
        "model": model,
        "state": "bounded source evidence",
        "questions": {
            f"q{index}": {"type": "noul", "instructions": "Is the relationship supported?"} for index in range(17)
        },
    }
    assert hosted.MAX_QUESTIONS == 16
    assert len(json.dumps(body).encode()) < hosted.MAX_BODY_BYTES
    transmit = MagicMock()
    prior_cost = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    monkeypatch.setattr(client, "_prior_api_cost", prior_cost)
    with pytest.raises(ValueError, match="admission"):
        client.request(body, tag="too-many-questions")
    transmit.assert_not_called()
    prior_cost.assert_not_called()
    assert not client.ledger.exists()
    assert not list(client.directory.glob("request-*.json"))


@pytest.mark.parametrize("model", [REQUESTED_MODELS[0], hosted.DEFAULT_MODELS[1]])
def test_provider_pin_preserves_price_caps_and_distinguishes_predictions(
    model: str,
    cases: list[dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases[0]["id"] = "catalog-case"
    monkeypatch.setattr(runner, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(runner, "build_cases", lambda: cases)
    monkeypatch.setattr(runner, "write_cases", MagicMock())
    monkeypatch.setattr(runner, "load_predictions", lambda *_args: [])
    save_report = MagicMock()
    monkeypatch.setattr(runner, "save_report", save_report)
    expected_provider = hosted.request_body(model, cases, "rich").get("provider", {}).copy()
    expected_provider.update(only=["test-provider"], allow_fallbacks=False)
    result: dict[str, Any] = (
        {"answers": {"q0_yes": {"noul": 0.2}, "q0_answerable": {"noul": 0.9}}}
        if model in hosted.DECISION_MODELS
        else {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": json.dumps({"answers": {"q0": {"p_yes": 0.2, "p_answerable": 0.9}}})},
                }
            ],
        }
    )
    client = MagicMock()
    client.request.return_value = {
        "result": result,
        "entry": {"index": 0, "elapsed_ms": 1, "accounted_usd": 0.001},
        "replayed": False,
    }
    monkeypatch.setattr(runner, "DecisionClient", lambda: client)
    args = argparse.Namespace(
        controls=False,
        report_only=False,
        smoke=False,
        single=False,
        batch_size=runner.BATCH_SIZE,
        provider="test-provider",
        models=[model],
        variant="rich",
    )
    runner.run(args)
    body = client.request.call_args.args[0]
    assert body["provider"] == expected_provider
    if model not in hosted.DECISION_MODELS:
        assert body["provider"]["max_price"] == {"prompt": 5, "completion": 25}
        assert body["provider"]["require_parameters"] is True
    assert client.request.call_args.kwargs["tag"] == f"{model}@rich-via-test-provider/batch/000"
    prediction = save_report.call_args.args[1][0]
    assert prediction["model"] == f"{model}@rich-via-test-provider"
    assert prediction["p_yes"] == 0.2
    assert prediction["p_answerable"] == 0.9
