"""Frozen source evidence gates and all-pass cost accounting."""

from __future__ import annotations

from typing import Any

import pytest
from bench.pipeline_ocr_orientation import choose, evidence, recognize
from bench.pipeline_ocr_sources import extract, whitespace_projection

import pylopdf


def _words(text: str = "North district total 123", confidence: float = 0.95) -> list[dict[str, Any]]:
    return [{"text": text, "confidence": confidence, "bbox": [100, 200 + i * 30, 350, 220 + i * 30]} for i in range(3)]


def test_clear_inventory_margin_selects_source_rotation() -> None:
    candidates = [
        {"rotation": rotation, "evidence": evidence(_words() if rotation == 270 else [])}
        for rotation in (0, 90, 180, 270)
    ]
    assert choose(candidates)["selected_rotation"] == 270


@pytest.mark.parametrize("weak", ["tie", "short", "confidence", "boxes"])
def test_uncertain_evidence_abstains(weak: str) -> None:
    words = _words()
    if weak == "short":
        words = _words("1")
    if weak == "confidence":
        words = _words(confidence=0.5)
    if weak == "boxes":
        words = words[:1]
    candidates = [
        {"rotation": rotation, "evidence": evidence(words if rotation == 0 or weak == "tie" else [])}
        for rotation in (0, 90, 180, 270)
    ]
    assert choose(candidates)["selected_rotation"] is None


def test_four_passes_retained_and_costed(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake(_page: pylopdf.Page, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        calls.append(kwargs["rotation"])
        return _words() if kwargs["rotation"] == 90 else []

    monkeypatch.setattr(pylopdf.Page, "get_text_ocr", fake)
    with pylopdf.Document() as document:
        result = recognize(document.new_page(), dpi=150)
    assert calls == [0, 90, 180, 270]
    assert result["selected_rotation"] == 90
    assert len(result["candidates"]) == 4
    assert result["all_pass_wall_seconds"] == sum(c["wall_seconds"] for c in result["candidates"])


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_whitespace_projection_follows_corrected_baseline(rotation: int) -> None:
    projected = whitespace_projection([{"text": "AA BB", "bbox": [0, 0, 100, 100], "rotation": rotation}])
    first, second = [word["bbox"] for word in projected]
    assert all(word["rotation"] == rotation for word in projected)
    if rotation == 0:
        assert first[0] < second[0]
    elif rotation == 90:
        assert first[1] > second[1]
    elif rotation == 180:
        assert first[0] > second[0]
    else:
        assert first[1] < second[1]


@pytest.mark.parametrize("tokenization", ["whitespace", "reextract"])
def test_orientation_extract_preserves_caller_and_native_text(
    tokenization: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake(_page: pylopdf.Page, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        return _words() if kwargs["rotation"] == 0 else []

    monkeypatch.setattr(pylopdf.Page, "get_text_ocr", fake)
    with pylopdf.Document() as document:
        page = document.new_page()
        before = document.tobytes()
        result = extract(page, orientation="candidates", tokenization=tokenization)
        assert document.tobytes() == before
        assert page.get_text() == ""
        assert result["diagnostics"]["orientation_passes"][0]["selected_rotation"] == 0
        assert len(result["diagnostics"]["recognized"]) == 3


def test_abstention_exposes_no_candidate_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pylopdf.Page, "get_text_ocr", lambda *_args, **_kwargs: _words())
    with pylopdf.Document() as document:
        result = extract(document.new_page(), orientation="candidates")
    assert result["source"]["words"] == []
    assert result["diagnostics"]["orientation_passes"][0]["status"] == "abstained_uncertain_orientation"


@pytest.mark.parametrize("dpi", [0, -1, float("nan"), True])
def test_orientation_refuses_invalid_dpi_before_ocr(dpi: float) -> None:
    with pylopdf.Document() as document, pytest.raises(ValueError, match="DPI"):
        recognize(document.new_page(), dpi=dpi)


def test_four_pass_pixel_admission_is_complete() -> None:
    with pylopdf.Document() as document, pytest.raises(ValueError, match="raster"):
        recognize(document.new_page(width=3000, height=3000), dpi=150)
