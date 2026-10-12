"""Behavioral regressions for the isolated CPU table-routing experiment."""

from __future__ import annotations

import re

import pytest

import pdfust

pytest.importorskip("markdown_it", reason="geometry study uses optional benchmark Markdown parsing")

from bench.feature_cases import page_pdf, text_op
from bench.geometry_cascade import (
    MAX_CELLS,
    MAX_WORDS,
    bounded,
    derivative,
    extract,
    geometry,
    header_control,
    positioned_words,
    strict_header_records,
)
from bench.structure_core import score_tables, source_agreement


@pytest.mark.parametrize("style", ["solid", "dashed", "filled", "broken", "missing", "partial"])
def test_encodings_preserve_complete_cells(style: str) -> None:
    case = derivative(style, reverse=True)
    with pdfust.open(stream=case.feature.data) as document:
        output = extract(document[0], "geometry")
    assert score_tables(output["tables"], case.tables)["exact"]


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_geometry_restores_logical_rotation(rotation: int) -> None:
    case = derivative("partial", rotation=rotation, reverse=True)
    with pdfust.open(stream=case.feature.data) as document:
        output = extract(document[0], "geometry")
    assert score_tables(output["tables"], case.tables)["exact"]


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_header_boxes_follow_logical_axes(rotation: int) -> None:
    case = derivative("partial", rotation=rotation, reverse=True)
    with pdfust.open(stream=case.feature.data) as document:
        page = document[0]
        words = positioned_words(page)
        output = extract(page, "cascade")
    assert output["route"] == "strict-vector-header"
    assert score_tables(output["tables"], case.tables)["exact"]
    agreement = source_agreement(output["markdown"], words)
    assert agreement["missing_tokens"] == 0
    assert agreement["extra_tokens"] == 0


def test_header_uses_baseline_instead_of_page_rotation() -> None:
    case = derivative("partial", reverse=True)
    match = re.search(rb"stream\n(.*?)\nendstream", case.feature.data, re.DOTALL)
    assert match is not None
    content = match.group(1).decode("latin-1")
    data = page_pdf("q 0 1 -1 0 750 0 cm\n" + content + "\nQ")
    with pdfust.open(stream=data) as document:
        page = document[0]
        assert page.rotation == 0
        words = positioned_words(page)
        output = extract(page, "cascade")
    assert output["header_diagnostics"][0]["orientation"] != 0
    assert output["route"] == "strict-vector-header"
    assert score_tables(output["tables"], case.tables)["exact"]
    agreement = source_agreement(output["markdown"], words)
    assert agreement["missing_tokens"] == 0
    assert agreement["extra_tokens"] == 0


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_native_full_grid_uses_logical_markdown(rotation: int) -> None:
    case = derivative("solid", rotation=rotation, reverse=True)
    with pdfust.open(stream=case.feature.data) as document:
        output = extract(document[0], "native")
    assert score_tables(output["tables"], case.tables)["exact"]


def test_prose_gate_abstains_and_preserves_source() -> None:
    case = derivative("prose", reverse=True)
    with pdfust.open(stream=case.feature.data) as document:
        page = document[0]
        words = positioned_words(page)
        unconditional = extract(page, "geometry")
        output = extract(page, "cascade")
    assert unconditional["tables"]  # This is the measured false-positive control.
    assert output["tables"] == []
    assert output["route"] == "abstain"
    agreement = source_agreement(output["markdown"], words)
    assert agreement["missing_tokens"] == 0
    assert agreement["extra_tokens"] == 0


def test_wrapped_body_and_footnote_stop() -> None:
    case = header_control("footnote")
    with pdfust.open(stream=case.feature.data) as document:
        page = document[0]
        words = positioned_words(page)
        matrices, consumed, diagnostics = strict_header_records(page, words)
        output = extract(page, "cascade")
        original = extract(page, "header")
    assert score_tables(matrices, case.tables)["exact"]
    assert diagnostics[0]["stop"] == "unsupported-record-or-prose"
    assert diagnostics[0]["admission"] == "accepted"
    header_ids = diagnostics[0]["header_ids"]
    assert len(header_ids) == len(set(header_ids))
    assert set(header_ids) <= consumed
    stopped = set(diagnostics[0]["stopped_word_ids"])
    assert stopped.isdisjoint(consumed)
    assert "Note: descriptive prose belongs outside the records." in output["markdown"]
    assert not score_tables(original["tables"], case.tables)["exact"]
    agreement = source_agreement(output["markdown"], words)
    assert agreement["missing_tokens"] == agreement["extra_tokens"] == 0


def test_header_does_not_extend_into_prose() -> None:
    case = header_control("prose")
    with pdfust.open(stream=case.feature.data) as document:
        page = document[0]
        matrices, used, diagnostics = strict_header_records(page, positioned_words(page))
        original = extract(page, "header")
        output = extract(page, "cascade")
    assert matrices == []
    assert used == set()
    assert diagnostics[0]["admission"] == "insufficient-numeric-records"
    assert original["tables"]
    assert len(original["tables"][0]) > 2
    assert score_tables(output["tables"], case.tables)["exact"]


def test_bounded_admission_refuses_complete_result() -> None:
    with pytest.raises(ValueError, match="word admission"):
        geometry([{}] * (MAX_WORDS + 1))
    with pytest.raises(ValueError, match="table admission"):
        bounded([[[""] * (MAX_CELLS + 1)]])


def test_unassigned_literals_preserve_source_tokens() -> None:
    data = page_pdf(text_op("Literal <tag> *stars* [label] code_value = 42", 40, 700))
    with pdfust.open(stream=data) as document:
        page = document[0]
        words = positioned_words(page)
        output = extract(page, "cascade")
    assert output["tables"] == []
    assert "&lt;tag&gt;" in output["markdown"]
    agreement = source_agreement(output["markdown"], words)
    assert agreement["missing_tokens"] == 0
    assert agreement["extra_tokens"] == 0
