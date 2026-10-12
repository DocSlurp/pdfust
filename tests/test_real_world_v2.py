"""Offline schema checks for the real-world-v2 DEV corpus tooling (no network, no PDFs)."""
# ruff: noqa: ANN401

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
from bench import real_world_v2 as rw


def _record(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": "uk-example",
        "url": "https://assets.publishing.service.gov.uk/media/x/example.pdf",
        "license": "OGL-UK-3.0",
        "license_url": rw.LICENSES["OGL-UK-3.0"],
        "attribution": "Contains public sector information licensed under the OGL v3.0.",
        "kind": "uk-gov",
        "title": "Example",
        "languages": ["en-GB"],
        "retrieved_at": "2026-10-12T01:00:00Z",
        "sha256": "a" * 64,
        "original_sha256": "b" * 64,
        "page_range_kept": "1-6",
        "page_count": 6,
        "bytes": 1024,
        "path": "pdfs/uk-example.pdf",
    }
    record.update(overrides)
    return record


def _truth(**overrides: Any) -> dict[str, Any]:
    truth: dict[str, Any] = {
        "version": 1,
        "doc_id": "uk-example",
        "pages": [1],
        "languages": ["en-GB"],
        "truth_status": "verified",
        "truth_method": "Three extractors reconciled against a 100 dpi render.",
        "uncertainty": [],
        "blocks": [
            {"kind": "heading", "level": 1, "page": 1, "text": "Title"},
            {"kind": "paragraph", "page": 1, "text": "Body."},
            {
                "kind": "table",
                "id": "t1",
                "page": 1,
                "rendering": "ruled",
                "header_rows": 1,
                "values": [["Year", "Value"], ["2011", "1.0"]],
                "spans": [],
            },
        ],
    }
    truth.update(overrides)
    return truth


def test_user_agent_has_no_email() -> None:
    assert "@" not in rw.USER_AGENT


def test_valid_manifest_record() -> None:
    assert rw.validate_manifest_record(_record()) == []


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"license": "All rights reserved"}, "license"),
        ({"sha256": "xyz"}, "sha256"),
        ({"retrieved_at": "yesterday"}, "retrieved_at"),
        ({"page_count": 31}, "page_count"),
        ({"bytes": 6 * 1024 * 1024}, "bytes"),
        ({"page_range_kept": "6-1"}, "page_range_kept"),
        ({"path": "../escape.pdf"}, "path"),
        ({"kind": "random-web"}, "kind"),
        ({"url": "http://insecure.example/x.pdf"}, "url"),
        ({"languages": []}, "languages"),
        ({"page_count": True}, "page_count"),
    ],
)
def test_invalid_manifest_records(overrides: dict[str, Any], fragment: str) -> None:
    errors = rw.validate_manifest_record(_record(**overrides))
    assert any(error.startswith(fragment) for error in errors), errors


def test_missing_manifest_key_is_reported() -> None:
    record = _record()
    del record["attribution"]
    assert any(error.startswith("attribution") for error in rw.validate_manifest_record(record))


@pytest.mark.parametrize("spec", ["1", "1-6", "1-10,35-36", "2,4,6-8"])
def test_valid_page_ranges(spec: str) -> None:
    assert rw.valid_range(spec)


@pytest.mark.parametrize("spec", ["", "0-3", "a-b", "3-1", "1--2"])
def test_invalid_page_ranges(spec: str) -> None:
    assert not rw.valid_range(spec)


def test_clamp_range() -> None:
    assert rw.clamp_range("1-10", 3) == "1-3"
    assert rw.clamp_range(None, 3) is None
    assert rw.clamp_range("1-10,35-36", 40) == "1-10,35-36"


def test_valid_truth() -> None:
    assert rw.validate_truth(_truth()) == []


def test_partial_paragraph_requires_partial_status() -> None:
    truth = _truth()
    truth["blocks"][1]["partial"] = True
    assert any("partial" in error for error in rw.validate_truth(truth))
    truth["truth_status"] = "partial"
    assert rw.validate_truth(truth) == []


def test_tables_must_be_complete_and_rectangular() -> None:
    truth = _truth(truth_status="partial")
    truth["blocks"][2]["partial"] = True
    assert any("complete" in error for error in rw.validate_truth(truth))
    ragged = _truth()
    ragged["blocks"][2]["values"] = [["Year", "Value"], ["2011"]]
    assert any("rows must all have" in error for error in rw.validate_truth(ragged))


def test_span_bounds_and_header_rows() -> None:
    truth = _truth()
    table = truth["blocks"][2]
    table["spans"] = [{"row": 1, "column": 1, "row_span": 2, "column_span": 1}]
    assert any("spans" in error for error in rw.validate_truth(truth))
    table["spans"] = [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}]
    assert rw.validate_truth(truth) == []
    table["header_rows"] = 3
    assert any("header_rows" in error for error in rw.validate_truth(truth))


def test_truth_rejects_unknown_kinds_pages_and_status() -> None:
    truth = _truth(truth_status="done")
    truth["blocks"].append({"kind": "banner", "page": 1, "text": "x"})
    truth["blocks"].append({"kind": "paragraph", "page": 9, "text": "x"})
    errors = rw.validate_truth(truth)
    assert any(error.startswith("truth_status") for error in errors)
    assert any("kind" in error for error in errors)
    assert any(".page" in error for error in errors)


def test_duplicate_table_ids_rejected() -> None:
    truth = _truth()
    truth["blocks"].append(copy.deepcopy(truth["blocks"][2]))
    assert any(".id" in error for error in rw.validate_truth(truth))


def test_heading_level_required() -> None:
    truth = _truth()
    del truth["blocks"][0]["level"]
    assert any("level" in error for error in rw.validate_truth(truth))


def test_bigram_f1() -> None:
    assert rw.bigram_f1("abc def", "abcdef") == 1.0
    assert rw.bigram_f1("", "") is None
    assert rw.bigram_f1("abcd", "wxyz") == 0.0


def test_producer_family() -> None:
    assert rw.producer_family("Microsoft® Word 2016", "") == "Microsoft Word"
    assert rw.producer_family("Adobe PDF Library 25", "Acrobat PDFMaker 25 for Word").startswith("Microsoft Office via")
    assert rw.producer_family("GPL Ghostscript 10.00.0", "LaTeX with powerdot class") == "Ghostscript"
    assert rw.producer_family("", "") == "unknown"


def test_guard_rejects_heldout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Held-out"):
        rw.guard_path(tmp_path / "silver-heldout-v1")
