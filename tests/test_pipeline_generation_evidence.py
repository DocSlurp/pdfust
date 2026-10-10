"""Lossless source-array transport and bounded quarter-unit evidence perturbation."""

import hashlib
import json
import math
from copy import deepcopy
from types import ModuleType
from typing import Any

import pytest
from bench import pipeline_generation as anchors
from bench import pipeline_matrix_generation as matrices
from bench.pipeline_generation_evidence import encode


def source() -> dict:
    return {
        "page_size": [-10, 20, 590, 820],
        "gold": "SECRET",
        "words": [
            {"id": "原id", "text": 'héllo 世界 \n" |', "bbox": [-1.113, 24.127, 40.376, 37.999], "gold": "SECRET"},
            {"id": "w1", "text": "42", "bbox": [50.0625, 70.125, 61.124, 84.249]},
        ],
    }


@pytest.mark.parametrize(
    ("adapter", "legacy_hash"),
    [
        (anchors, "e90f42bf7af9ece65dc1c0cfcfd39008ce6cc43489494d5fba95eb4ad6a2867c"),
        (matrices, "c16b248e3cb43812de0593416c4d58aadabc3c9fd64411f6721b613b8ea5ce72"),
    ],
)
def test_objects_default_preserves_exact_legacy_transport(adapter: ModuleType, legacy_hash: str) -> None:
    # Digests captured from the reviewed pre-change requests, including their schemas.
    body = adapter.request(
        source(), "anthropic/claude-sonnet-5.5", "data:image/png;base64,YQ==", [-10, 20, 590, 820], 8192
    )
    explicit = adapter.request(
        source(),
        "anthropic/claude-sonnet-5.5",
        "data:image/png;base64,YQ==",
        [-10, 20, 590, 820],
        8192,
        evidence_format="objects",
    )
    assert body == explicit
    assert hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest() == legacy_hash


@pytest.mark.parametrize("adapter", [anchors, matrices])
def test_arrays_reconstruct_every_literal_word_and_box_without_metadata(adapter: ModuleType) -> None:
    original = source()
    before = deepcopy(original)
    viewport = [-10, 20, 590, 820]
    body = adapter.request(original, "anthropic/claude-haiku-5.5", viewport=viewport, evidence_format="arrays")
    packet = json.loads(body["messages"][1]["content"])
    reconstructed = [dict(zip(packet["word_fields"], row, strict=True)) for row in packet["words"]]
    assert reconstructed == [{key: word[key] for key in ("id", "text", "bbox")} for word in original["words"]]
    assert packet["page_size"] == original["page_size"]
    assert packet["viewport"] == viewport
    assert packet["geometry"]["maximum_coordinate_error"] == 0
    assert "SECRET" not in json.dumps(body)
    assert original == before


@pytest.mark.parametrize("adapter", [anchors, matrices])
def test_quarter_preserves_text_and_ids_and_has_bounded_finite_ordered_boxes(adapter: ModuleType) -> None:
    original = source()
    before = deepcopy(original)
    body = adapter.request(
        original, "anthropic/claude-haiku-5.5", viewport=[-10, 20, 590, 820], evidence_format="quarter"
    )
    packet = json.loads(body["messages"][1]["content"])
    assert packet["geometry"]["maximum_coordinate_error"] == 0.125
    assert "nearest 0.25" in packet["geometry"]["rounding"]
    for word, row in zip(original["words"], packet["words"], strict=True):
        assert row[0].encode() == word["id"].encode()
        assert row[1].encode() == word["text"].encode()
        assert all(math.isfinite(value) for value in row[2])
        assert row[2][0] <= row[2][2]
        assert row[2][1] <= row[2][3]
        assert max(abs(a - b) for a, b in zip(row[2], word["bbox"], strict=True)) <= 0.125
        assert all(value * 4 == round(value * 4) for value in row[2])
    assert packet["page_size"] == original["page_size"]
    assert packet["viewport"] == [-10, 20, 590, 820]
    assert "SECRET" not in json.dumps(body)
    assert original == before


def test_encoding_precedes_packet_admission_without_bypassing_source_admission() -> None:
    dense: dict[str, Any] = {
        "page_size": [600, 800],
        "words": [
            {
                "id": f"w{i}",
                "text": "x",
                "bbox": [0.1234567890123456, 1.1234567890123457, 2.1234567890123457, 3.1234567890123457],
            }
            for i in range(1200)
        ],
    }
    with pytest.raises(ValueError, match="packet exceeds"):
        anchors.request(dense, anchors.MODELS[0])
    body = anchors.request(dense, anchors.MODELS[0], evidence_format="arrays")
    assert len(json.loads(body["messages"][1]["content"])["words"]) == 1200
    dense["words"][0]["text"] = "x" * 16_001
    for evidence_format in ("objects", "arrays", "quarter"):
        with pytest.raises(ValueError, match="source text exceeds"):
            anchors.request(dense, anchors.MODELS[0], evidence_format=evidence_format)


def test_quarter_extreme_finite_coordinates_do_not_overflow_or_replace_originals() -> None:
    original: dict[str, Any] = {
        "page_size": [600, 800],
        "words": [{"id": "w0", "text": "x", "bbox": [1e308, 1e308, 1e308, 1e308]}],
    }
    encoded = json.loads(encode(original, None, "quarter"))
    assert encoded["words"][0][2] == original["words"][0]["bbox"]
    with pytest.raises(ValueError, match="Unknown"):
        encode(original, None, "unregistered")
