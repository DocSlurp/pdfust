"""True Clef microbatches using the pinned publisher's joint decision head.

One engine holds one model allocation. Each source record retains its own schema,
media and option order; response conversion matches publisher systemone exactly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.remote_clef import MAX_LENGTH, Engine, _request, load

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

MAX_BATCH_SIZE = 16
MAX_PADDED_TOKENS = 65_536


def predict_batch(  # noqa: C901, PLR0912
    engine: Engine,
    bodies: Sequence[dict[str, Any]],
    image_paths: Sequence[Sequence[str | Path]],
    *,
    max_padded_tokens: int = MAX_PADDED_TOKENS,
) -> list[dict[str, Any]]:
    """Preflight every complete input, collate once, then preserve native answers.

    Refuse the entire batch before forward if any record exceeds its token bound.
    Usage is the publisher's actual per-record encoded token length and zero
    generated tokens; batch padding is not assigned as invented per-record usage.
    """
    if not bodies or len(bodies) > MAX_BATCH_SIZE or len(bodies) != len(image_paths):
        message = "batch requires 1-16 records with matching image path groups"
        raise ValueError(message)
    if isinstance(max_padded_tokens, bool) or not isinstance(max_padded_tokens, int) or max_padded_tokens < 1:
        message = "padded-token bound must be a positive integer"
        raise ValueError(message)
    requests = []
    encoded = []
    for body, images in zip(bodies, image_paths, strict=True):
        request = _request(body, images)
        for question_id, question in request["questions"].items():
            if question.get("type") not in engine.helper.QUESTION_TYPES:
                message = f"{question_id}: unsupported native question type"
                raise ValueError(message)
            if question["type"] != "noul" and not question.get("criteria"):
                message = f"{question_id}: criteria must not be empty"
                raise ValueError(message)
        record = engine.helper.encode_record(
            engine.processor.tokenizer, request, max_length=1_000_000_000, processor=engine.processor
        )
        if len(record.input_ids) > MAX_LENGTH:
            message = f"complete source input exceeds Clef limit of {MAX_LENGTH} tokens"
            raise ValueError(message)
        requests.append(request)
        encoded.append(record)
    padded_tokens = len(encoded) * max(len(record.input_ids) for record in encoded)
    if padded_tokens > max_padded_tokens:
        message = "padded batch exceeds its complete-input token admission"
        raise ValueError(message)
    device = next(engine.model.parameters()).device
    with engine.helper.torch.inference_mode():
        batch = engine.helper.collate_records(encoded, engine.processor.tokenizer.pad_token_id, device)
        logits = engine.model(batch)
        if len(logits) != len(encoded):
            message = "native batch response count differs from source records"
            raise ValueError(message)
        responses = []
        for request, record, record_logits in zip(requests, encoded, logits, strict=True):
            if len(record_logits) != len(record.questions):
                message = "native question logits differ from source schema"
                raise ValueError(message)
            answers = {}
            for question, question_logits in zip(record.questions, record_logits, strict=True):
                values = question_logits.float().softmax(-1).tolist()
                if len(values) != len(question.option_ids):
                    message = "native option logits differ from source schema"
                    raise ValueError(message)
                answers[question.question_id] = engine.helper.systemone_answer(
                    request["questions"][question.question_id], dict(zip(question.option_ids, values, strict=True))
                )
            if set(answers) != set(request["questions"]):
                message = "native answers do not cover source questions"
                raise ValueError(message)
            responses.append(
                {
                    "model": request["model"],
                    "answers": answers,
                    "usage": {"input_tokens": len(record.input_ids), "output_tokens": 0},
                }
            )
    return responses


__all__ = ["load", "predict_batch"]
