"""Frozen source-only admission bodies, ownership and fail-closed outcomes."""

from __future__ import annotations

import base64
import io
import json
from typing import Any

import pytest
from bench import p003_structure_admission as admission
from bench.pipeline_repair import validate
from PIL import Image


def example() -> tuple[dict[str, Any], dict[str, Any]]:
    """Provide one complete geometry proposal and two exact literal source words."""
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "a", "text": "literal DATA", "bbox": [5, 5, 15, 15]},
            {"id": "b", "text": "formula x^2", "bbox": [60, 5, 75, 15]},
        ],
    }
    shape = {
        "status": "geometry_candidate",
        "row_count": 1,
        "column_count": 2,
        "bbox": [0, 0, 100, 50],
        "anchors": [
            {"row": 0, "column": c, "row_span": 1, "column_span": 1, "bbox": [c * 50, 0, (c + 1) * 50, 50]}
            for c in range(2)
        ],
    }
    return source, shape


def test_packet_complete_literals_exact_coords_no_true_cell_claim() -> None:
    """Source IDs/text/bboxes and explicit ownership claims survive unchanged."""
    source, shape = example()
    table = admission.source_table(source, shape, ["a"])
    text, meta = admission.packet(source, table, ["a"], pixels_available=True)
    assert text is not None
    packet = json.loads(text)
    assert packet["words"] == [["a", "literal DATA", 5, 5, 15, 15]]
    assert packet["candidate"]["ownership_is_proposed_not_verified"] is True
    assert packet["other_page_words_omitted_count"] == 1
    assert packet["pixel_viewport"] == shape["bbox"]
    assert meta["text_truncated"] is False


def test_oversize_complete_words_refuse_question_not_truncate() -> None:
    """All literals remain local when the complete request packet cannot fit."""
    source, shape = example()
    source["words"][0]["text"] = "z" * admission.MAX_PACKET_BYTES
    table = admission.source_table(source, shape, ["a"])
    text, meta = admission.packet(source, table, ["a"], pixels_available=False)
    assert text is None
    assert meta["status"] == "no_question_refusal"
    assert meta["owned_words_omitted_count"] == 0
    assert meta["utf8_bytes"] > admission.MAX_PACKET_BYTES
    assert source["words"][0]["text"] == "z" * admission.MAX_PACKET_BYTES


def test_native_body_independent_models_images_and_instruction() -> None:
    """Every configured native model receives the strict admission instruction."""
    for model in admission.MODELS:
        text = admission.request(model, "literal", "data:image/jpeg;base64,AAAA")
        assert text["model"] == model
        assert text["state"][0] == "literal"
        assert text["state"][1]["image_url"]["url"] == "data:image/jpeg;base64,AAAA"
        assert set(text["questions"]["q0"]["criteria"]) == {"retain", "reject", "unresolved"}
        assert text["questions"]["q0"]["instructions"] == admission.INSTRUCTIONS
        assert admission.request(model, "literal", None)["state"] == "literal"
    with pytest.raises(ValueError, match="Unknown"):
        admission.request("invented/model", "literal", None)


def test_retain_exact_source_reject_unresolved_failure_and_refusal() -> None:
    """Only retain admits; every other route preserves unresolved literal IDs."""
    source, shape = example()
    table = admission.source_table(source, shape, ["a", "b"])
    candidate = {"id": "c1", "table": table, "source_ids": ["a", "b"]}
    for answer in ("retain", "reject", "unresolved", None):
        result = admission.apply(source, [candidate], {"c1": answer})
        validate(source, result["state"])
        if answer == "retain":
            assert result["state"]["tables"][0]["values"] == [["literal DATA", "formula x^2"]]
        else:
            assert result["state"]["unresolved_ids"] == ["a", "b"]
    refused = {**candidate, "question_status": "no_question_refusal"}
    assert admission.apply(source, [refused], {"c1": "retain"})["state"]["tables"] == []
    assert admission.apply(source, [candidate], {})["admission_receipts"][0]["reason"] == "missing_or_failed_decision"


def test_multiple_retained_conflicts_no_implicit_replacement() -> None:
    """Conflicting positive candidates are all refused instead of merged or replaced."""
    source, shape = example()
    table = admission.source_table(source, shape, ["a", "b"])
    candidates = [{"id": identifier, "table": table, "source_ids": ["a", "b"]} for identifier in ("c1", "c2")]
    result = admission.apply(source, candidates, {"c1": "retain", "c2": "retain"})
    assert result["state"]["tables"] == []
    assert result["state"]["unresolved_ids"] == ["a", "b"]
    assert all(r["reason"] == "conflicting_retained_geometry_or_source_IDs" for r in result["admission_receipts"])
    with pytest.raises(ValueError, match="Unknown"):
        admission.apply(source, candidates, {"foreign": "retain"})


def test_admission_limits_before_table_allocation_and_foreign_words() -> None:
    """Invalid huge shape or ownership cannot create a partial usable candidate."""
    source, shape = example()
    shape["row_count"] = 100000000
    with pytest.raises(ValueError, match="slot admission"):
        admission.source_table(source, shape, ["a"])
    source, shape = example()
    table = admission.source_table(source, shape, ["a", "b"])
    with pytest.raises(ValueError, match="foreign"):
        admission.packet(source, table, ["a"], pixels_available=False)


def test_rgb128_and512_pixel_provenance_and_exact_encoding() -> None:
    """Both variants share the exact source box and preserve lossless RGB semantics."""
    image = Image.new("RGB", (100, 50), (20, 40, 60))
    metadata = []
    for edge in (128, 512):
        url, meta = admission.image_variant(image, [0, 0, 100, 50], [25, 0, 75, 50], edge)
        assert meta["image_size"] == [edge, edge]
        assert meta["image_mode"] == "RGB"
        with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as pixels:
            assert pixels.mode == "RGB"
            assert pixels.getpixel((edge // 2, edge // 2)) == (20, 40, 60)
        metadata.append(meta)
    assert metadata[0]["continuous_source_pixel_box"] == metadata[1]["continuous_source_pixel_box"]
    assert metadata[0]["image_sha256"] != metadata[1]["image_sha256"]
    with pytest.raises(ValueError, match="outside"):
        admission.image_variant(image, [0, 0, 100, 50], [-1, 0, 75, 50], 128)
