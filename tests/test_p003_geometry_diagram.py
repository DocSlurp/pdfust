"""Synthetic diagram provenance and matched candidate preservation."""

from __future__ import annotations

import base64
import io
import json
from typing import Any

import pytest
from bench import p003_candidate_choice as choice
from bench import p003_geometry_diagram as d
from bench.pipeline_vision_transcription import parse
from PIL import Image


def source() -> dict[str, Any]:
    """Keep duplicate physical words and partial crop context explicit."""
    return {
        "page_size": [0, 0, 200, 100],
        "words": [
            {"id": "a", "text": "Alpha", "bbox": [10, 10, 30, 30]},
            {"id": "b", "text": "Alpha", "bbox": [10, 10, 30, 30]},
            {"id": "c", "text": "outside", "bbox": [120, 10, 140, 30]},
        ],
    }


def candidate(text: str) -> dict[str, Any]:
    """Construct strictly admitted independent transcription candidates."""
    payload = {
        "answers": {"q0": {"tables": [{"bbox": [0, 0, 1000, 1000], "matrix": [[text, "value"]], "mergedspans": []}]}}
    }
    return parse(
        {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}]}, [0, 0, 100, 100]
    )


def test_geometry_deterministic_and_independent_of_literal_strings() -> None:
    """No word text, duplicate ID color, or candidate alias changes diagram pixels."""
    page = source()
    url, metadata = d.diagram(page, ["a", "b", "c"], [0, 0, 100, 100], 128, "filled")
    page["words"][0]["text"] = "completely different glyph content"
    other, changed = d.diagram(page, ["a", "b", "c"], [0, 0, 100, 100], 128, "filled")
    assert url == other
    assert metadata["source_sha256"] != changed["source_sha256"]
    assert metadata["drawn_word_count"] == 2
    assert metadata["not_drawable_owned_word_count"] == 1
    assert len(metadata["source_id_pixel_mapping"]) == 3
    assert metadata["source_pixels_supplied"] is False
    png = base64.b64decode(url.split(",", 1)[1])
    assert png[24:26] == bytes([8, 2])
    with Image.open(io.BytesIO(png)) as image:
        assert image.mode == "RGB"
        assert image.size == (128, 128)
        assert {image.getpixel((x, y)) for x in range(image.width) for y in range(image.height)} == {
            (255, 255, 255),
            (96, 96, 96),
        }


def test_clipping_edges_and_outline_are_explicit_distinct_treatments() -> None:
    """Partially visible source words clip deterministically without hidden ID loss."""
    page = source()
    page["words"][0]["bbox"] = [-5, 10, 30, 30]
    filled, metadata = d.diagram(page, ["a"], [0, 0, 100, 50], 400, "filled")
    outline, outlined = d.diagram(page, ["a"], [0, 0, 100, 50], 400, "outline")
    assert filled != outline
    assert metadata["image_size"] == [400, 200]
    assert metadata["source_id_pixel_mapping"][0]["bbox_clipped"]
    assert outlined["outline_width_pixels"] == 1
    assert metadata["owned_word_geometry_omitted_count"] == 0


def test_candidate_evidence_aliases_and_criteria_preserved_with_notice() -> None:
    """The deliberate instruction change must not alter choices or candidate payload."""
    pool = choice.freeze_pool([0, 0, 100, 100], [candidate("one"), candidate("two")], seed=20261010)
    url, _ = d.diagram(source(), ["a"], [0, 0, 100, 100], 512, "filled")
    original = choice.request(pool, "perplexity/pplx-decider-v1.1-27b", url)
    body, metadata = d.request(pool, original["model"], url)
    assert body is not None
    before, after = json.loads(original["state"][0]), json.loads(body["state"][0])
    assert after["candidates"] == before["candidates"]
    assert body["questions"]["q0"]["criteria"] == original["questions"]["q0"]["criteria"]
    assert metadata["instruction_treatment_changed"]
    assert not metadata["pure_pixel_causal_control"]
    assert after["image_evidence_kind"] == "synthetic_source_word_geometry_only"
    assert "no original source pixels" in body["questions"]["q0"]["instructions"]


def test_invalid_ownership_and_edges_refused() -> None:
    """No implicit image-mode coercion or foreign source-ID geometry is admitted."""
    with pytest.raises(ValueError, match="contract"):
        d.diagram(source(), ["foreign"], [0, 0, 100, 100], 128, "filled")
    with pytest.raises(ValueError, match="contract"):
        d.diagram(source(), ["a", "a"], [0, 0, 100, 100], 128, "filled")
    with pytest.raises(ValueError, match="contract"):
        d.diagram(source(), ["a"], [0, 0, 100, 100], 256, "filled")


def test_capacity_refuses_complete_evidence_without_implicit_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    """The extra notice cannot silently push a complete packet past its declared cap."""
    pool = choice.freeze_pool([0, 0, 100, 100], [candidate("one"), candidate("two")], seed=1)
    url, _ = d.diagram(source(), ["a"], [0, 0, 100, 100], 128, "filled")
    original = choice.request(pool, "perplexity/pplx-decider-v1.1-27b", url)
    monkeypatch.setattr(choice, "MAX_COMPARISON_BYTES", len(original["state"][0].encode()) + 1)
    body, metadata = d.request(pool, original["model"], url)
    assert body is None
    assert metadata["status"] == "no_question_refusal"
    assert metadata["evidence_omitted_bytes"] == 0
