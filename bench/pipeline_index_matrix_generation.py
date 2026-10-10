"""Opt-in ordinal word matrices expanded through the unchanged strict ID parser."""

# Heterogeneous JSON transport and the existing private admission gates are deliberate.
# ruff: noqa: EM101, TRY003, SLF001, PLR0913, PLR2004, C901
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from bench import pipeline_generation as anchors
from bench import pipeline_matrix_generation as matrices
from bench.pipeline_frontier import _invalid_constant, _unique_pairs

SYSTEM = matrices.SYSTEM.replace("source IDs", "integer word indexes").replace(
    "supplied source IDs", "supplied integer word indexes"
).replace("an ID", "a word index").replace("IDs", "word indexes") + (
    " Each word's index is its exact zero-based position in the complete supplied words array. "
    "Indexes identify source words; they are never numeric cell values. Return integers, never strings, "
    "text, or numeric values copied from the document. Preserve index order within each cell."
)


@dataclass(frozen=True)
class IndexedSource:
    """Immutable complete source order and original geometry, retained only locally."""

    page_size: tuple[float, ...]
    words: tuple[tuple[str, str, tuple[float, ...]], ...]

    def source(self) -> dict[str, Any]:
        """Materialize a fresh source without exposing mutable snapshot internals."""
        return {
            "page_size": list(self.page_size),
            "words": [{"id": identifier, "text": text, "bbox": list(box)} for identifier, text, box in self.words],
        }


def freeze(source: dict[str, Any]) -> IndexedSource:
    """Freeze every admitted word once; no filtering, sorting, or coordinate rounding."""
    retained = anchors._source(source)
    if any(not word["id"] or len(word["id"]) > 128 for word in retained["words"]):
        raise ValueError("Invalid or over-limit source ID")
    return IndexedSource(
        tuple(retained["page_size"]),
        tuple((word["id"], word["text"], tuple(word["bbox"])) for word in retained["words"]),
    )


def _snapshot(source: dict[str, Any] | IndexedSource) -> IndexedSource:
    return source if isinstance(source, IndexedSource) else freeze(source)


def request(
    source: dict[str, Any] | IndexedSource,
    model: str,
    url: str | None = None,
    viewport: list[float] | tuple[float, ...] | None = None,
    max_tokens: int = 4096,
    *,
    evidence_format: str = "objects",
) -> dict[str, Any]:
    """Replace only evidence identity and answer identity; preserve existing admissions."""
    snapshot = _snapshot(source)
    body = matrices.request(snapshot.source(), model, url, viewport, max_tokens, evidence_format=evidence_format)
    content = body["messages"][1]["content"]
    packet_text = content if isinstance(content, str) else content[0]["text"]
    packet = json.loads(packet_text)
    if evidence_format == "objects":
        for index, word in enumerate(packet["words"]):
            del word["id"]
            word["index"] = index
    else:
        packet["word_fields"][0] = "index"
        for index, word in enumerate(packet["words"]):
            word[0] = index
    encoded = json.dumps(packet, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if len(encoded) > anchors.MAX_PACKET_CHARACTERS:
        raise ValueError("Complete ordinal packet exceeds admission")
    if isinstance(content, str):
        body["messages"][1]["content"] = encoded
    else:
        content[0]["text"] = encoded
    body["messages"][0]["content"] = SYSTEM
    schema = body["response_format"]["json_schema"]
    schema["name"] = "pdf_word_index_matrix"
    table = schema["schema"]["properties"]["answers"]["properties"]["q0"]["properties"]["tables"]["items"]
    cell = table["properties"]["matrix"]["items"]["items"]
    cell["maxItems"] = min(anchors.MAX_TABLE_SLOTS, len(snapshot.words))
    # With zero words maxItems=0 admits only []; avoid an invalid negative schema maximum.
    cell["items"] = {"type": "integer", "minimum": 0, "maximum": max(0, len(snapshot.words) - 1)}
    return body


def parse(source: dict[str, Any] | IndexedSource, result: dict[str, Any]) -> dict[str, Any]:
    """Expand exact integer identities, then replay the original strict matrix parser."""
    snapshot = _snapshot(source)
    if not isinstance(result, dict) or not isinstance(result.get("choices"), list) or len(result["choices"]) != 1:
        raise ValueError("Response must contain exactly one completion")
    completion = result["choices"][0]
    if not isinstance(completion, dict) or completion.get("finish_reason") not in ("stop", "end_turn"):
        raise ValueError("Response was truncated or has no normal finish")
    message = completion.get("message")
    if not isinstance(message, dict) or message.get("refusal") or not isinstance(message.get("content"), str):
        raise ValueError("Response has no admitted JSON content")
    if len(message["content"]) > anchors.MAX_RESPONSE_CHARACTERS:
        raise ValueError("Complete ordinal response exceeds admission")
    payload = json.loads(message["content"], object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    answers = anchors._object(payload, {"answers"}, "response")["answers"]
    answer = anchors._object(answers, {"q0"}, "answers")["q0"]
    tables = anchors._object(answer, {"tables"}, "q0")["tables"]
    if not isinstance(tables, list) or len(tables) > anchors.MAX_TABLES:
        raise ValueError("Invalid ordinal table collection")
    seen: set[int] = set()
    slots = 0
    for table in tables:
        matrices._convert(table)  # Validate rectangular topology and merged ownership before expansion.
        matrix = table["matrix"]
        slots += len(matrix) * len(matrix[0])
        if slots > anchors.MAX_TABLE_SLOTS:
            raise ValueError("Ordinal matrices exceed cumulative slot admission")
        for row in matrix:
            for cell in row:
                for position, index in enumerate(cell):
                    if type(index) is not int or not 0 <= index < len(snapshot.words):
                        raise ValueError("Word index must be an in-range integer")
                    if index in seen:
                        raise ValueError("Duplicate word index")
                    seen.add(index)
                    cell[position] = snapshot.words[index][0]
    expanded = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}]}
    state = matrices.parse(snapshot.source(), expanded)
    state["mechanism"] = "word_index_matrix_generation"
    return state
