"""CPU mocks for source conservation, batch mapping and complete-input admission."""

from __future__ import annotations

import builtins
from contextlib import nullcontext
from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest
from bench import remote_clef_batch as batch
from bench.remote_clef import Engine


class Logits:
    """Tiny tensor protocol retaining precomputed mock probabilities."""

    def __init__(self, values: list[builtins.float]) -> None:
        """Keep the fake probabilities local to one encoded question."""
        self.values = values

    def float(self) -> Logits:
        """Mirror the publisher's explicit float probability conversion."""
        return self

    def softmax(self, axis: int) -> Logits:
        """Accept the publisher's fixed last-dimension operation."""
        assert axis == -1
        return self

    def tolist(self) -> list[builtins.float]:
        """Return mock native probabilities without model inference."""
        return self.values


def engine_fixture(monkeypatch: pytest.MonkeyPatch, *, lengths: list[int] | None = None) -> tuple[Engine, list]:
    calls: list[tuple[str, Any]] = []
    encoded_calls = []

    def encode(_tokenizer: object, request: dict, **kwargs: Any) -> object:  # noqa: ANN401
        encoded_calls.append(deepcopy(request))
        assert kwargs["max_length"] == 1_000_000_000
        length = lengths[len(encoded_calls) - 1] if lengths else len(request["state"])
        return SimpleNamespace(
            input_ids=tuple(range(length)),
            questions=[
                SimpleNamespace(question_id=k, option_ids=tuple(q["criteria"])) for k, q in request["questions"].items()
            ],
        )

    def collate(records: list, pad: int, device: str) -> dict:
        assert pad == 9
        assert device == "mock-cuda"
        calls.append(("collate", records))
        return {"records": records}

    class Model:
        def parameters(self):  # noqa: ANN202
            return iter([SimpleNamespace(device="mock-cuda")])

        def __call__(self, value: dict) -> list:
            calls.append(("forward", value))
            return [
                [Logits([0.7, 0.2, 0.1] if i == 0 else [0.1, 0.8, 0.1]) for _ in record.questions]
                for i, record in enumerate(value["records"])
            ]

    def answer(question: dict, probabilities: dict) -> dict:
        keys = list(question["criteria"])
        assert list(probabilities) == keys
        choice = max(keys, key=probabilities.__getitem__)
        return {
            "type": question["type"],
            "choice": choice,
            "confidence": round(probabilities[choice], 4),
            "probabilities": {key: round(probabilities[key], 4) for key in keys},
        }

    helper = SimpleNamespace(
        encode_record=encode,
        collate_records=collate,
        systemone_answer=answer,
        QUESTION_TYPES={"choice": 0},
        torch=SimpleNamespace(inference_mode=nullcontext),
    )
    monkeypatch.setattr(batch, "_request", lambda body, _images: deepcopy(body))
    return Engine(Model(), SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=9)), helper), calls


def body(text: str, qid: str = "q0") -> dict:
    return {
        "model": "transport",
        "state": text,
        "questions": {
            qid: {"type": "choice", "criteria": {"join": "source A", "split": "source B", "unresolved": "insufficient"}}
        },
    }


def test_one_forward_preserves_distinct_records_questions_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, calls = engine_fixture(monkeypatch)
    bodies = [body("first"), body("second", "different_id")]
    before = deepcopy(bodies)
    answers = batch.predict_batch(engine, bodies, [[], []])
    assert bodies == before
    assert len([c for c in calls if c[0] == "forward"]) == 1
    assert list(answers[0]["answers"]) == ["q0"]
    assert list(answers[1]["answers"]) == ["different_id"]
    assert answers[0]["answers"]["q0"]["choice"] == "join"
    assert answers[1]["answers"]["different_id"]["choice"] == "split"
    assert answers[0]["usage"] == {"input_tokens": 5, "output_tokens": 0}
    assert answers[1]["usage"] == {"input_tokens": 6, "output_tokens": 0}
    assert answers[0]["answers"]["q0"]["probabilities"] == {"join": 0.7, "split": 0.2, "unresolved": 0.1}


def test_late_overlength_refuses_entire_batch_before_forward(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, calls = engine_fixture(monkeypatch, lengths=[3, batch.MAX_LENGTH + 1])
    with pytest.raises(ValueError, match="complete source input"):
        batch.predict_batch(engine, [body("a"), body("b")], [[], []])
    assert calls == []


def test_padded_total_bound_refuses_without_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, calls = engine_fixture(monkeypatch, lengths=[1, 20])
    with pytest.raises(ValueError, match="padded batch"):
        batch.predict_batch(engine, [body("a"), body("b")], [[], []], max_padded_tokens=39)
    assert calls == []


@pytest.mark.parametrize("count", [0, 17])
def test_batch_count_refusal(monkeypatch: pytest.MonkeyPatch, count: int) -> None:
    engine, calls = engine_fixture(monkeypatch)
    with pytest.raises(ValueError, match="1-16"):
        batch.predict_batch(engine, [body("a")] * count, [[]] * count)
    assert calls == []


def test_source_image_groups_remain_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, _ = engine_fixture(monkeypatch)
    groups = []

    def request(body: dict, images: list) -> dict:
        groups.append(images)
        return deepcopy(body)

    monkeypatch.setattr(batch, "_request", request)
    batch.predict_batch(engine, [body("a"), body("b")], [["first.png"], ["second.png"]])
    assert groups == [["first.png"], ["second.png"]]
