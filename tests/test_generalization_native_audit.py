"""Disjoint authored source inventories and retained caller ownership contracts."""

from __future__ import annotations

from typing import Any

import pytest
from bench.generalization_native_audit import IDS, construction_references, run, source_cases
from bench.pipeline_ocr_sources import extract

import pylopdf


@pytest.fixture(scope="module")
def cases() -> dict[str, dict[str, Any]]:
    """Build sources once for the bounded contract matrix."""
    return {case["id"]: case for case in source_cases()}


def test_fourteen_source_contracts_match_separate_construction_inventory() -> None:
    result = run()
    assert len(result["cases"]) == len(IDS) == 14
    assert all(row["discovery_matches_construction"] and row["caller_preserved"] for row in result["cases"])
    assert result["ocr"] is False
    assert all(row["runs"] == [] for row in result["cases"])
    assert construction_references()["two-image-tables"]["uncovered_regions"] == 2


@pytest.mark.parametrize("identifier", IDS)
@pytest.mark.parametrize("tokenization", ["whitespace", "reextract"])
def test_both_modes_preserve_each_source_and_global_word_ids(
    cases: dict[str, dict[str, Any]],
    identifier: str,
    tokenization: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def recognized(_page: pylopdf.Page, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        clip = kwargs.get("clip") or [100, 150, 500, 330]
        x, y = clip[:2]
        return [{"text": "地域 12", "bbox": pylopdf.Rect(x + 10, y + 10, x + 110, y + 25), "confidence": 0.9}]

    monkeypatch.setattr(pylopdf.Page, "get_text_ocr", recognized)
    case = cases[identifier]
    with pylopdf.Document(stream=case["pdf"]) as document:
        page = document[case["page_number"]]
        before, native = document.tobytes(), page.get_text()
        for mode in ("empty", "uncovered_images"):
            result = extract(page, mode=mode, tokenization=tokenization)
            words = result["source"]["words"]
            assert len({word["id"] for word in words}) == len(words)
            assert result["source"]["page_size"] == list(page.rect)
            assert document.tobytes() == before
            assert page.get_text() == native
            if mode == "empty" and native:
                assert result["diagnostics"]["status"] == "skipped_existing_native_text"
            if mode == "uncovered_images" and identifier in {"native-intersection", "overlapping-images"}:
                assert result["diagnostics"]["status"] == "abstained_no_uncovered_image_regions"
