"""CPU-only checks for frozen P002 inputs and construction references."""

# Test fixture rows retain a readable construction loop.
# ruff: noqa: PERF401

import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
from bench import generalization_corpus as corpus
from bench.generalization_corpus import FAMILIES, authored_cases, image_pdf, parent_group, select_rows
from PIL import Image

import pylopdf


def _rows() -> list[dict]:
    rows = []
    for count in (0, 1, 2):
        for index in range(40):
            rows.append(
                {
                    "page_info": {
                        "image_path": f"document-{count}-{index}.pdf_1.jpg",
                        "page_attribute": {"language": "en" if index % 2 else "zh", "layout": str(index % 3)},
                    },
                    "layout_dets": [{"category_type": "table"} for _ in range(count)],
                }
            )
    return rows


def test_selection_fixed_quotas_and_disjoint_parents() -> None:
    """Stratification and exclusions cannot depend on extraction or answer strings."""
    rows = _rows()
    excluded = {"document-2-0.pdf_7.jpg", "document-1-0.pdf_1.jpg"}
    selected = select_rows(rows, excluded)
    assert len(selected) == 64
    assert Counter(len(row["layout_dets"]) for row in selected) == {0: 24, 1: 24, 2: 16}
    assert not {parent_group(row["page_info"]["image_path"]) for row in selected} & {
        parent_group(identifier) for identifier in excluded
    }
    assert selected == select_rows(list(reversed(rows)), excluded)
    for row in rows:
        for block in row["layout_dets"]:
            block["html"] = "Changed recognition answer"
    assert selected == select_rows(rows, excluded)


def test_selection_fails_if_fixed_quota_unavailable() -> None:
    """Missing metadata strata must not silently weaken the frozen design."""
    with pytest.raises(ValueError, match="Insufficient"):
        select_rows(_rows()[:40], set())


def test_authored_designs_are_new_and_complete() -> None:
    """Every new construction has an opaque-independent reference and unique input."""
    cases = authored_cases()
    assert len(cases) == len(FAMILIES) * 12
    assert len({case["pdf"] for case in cases}) == len(cases)
    assert Counter(case["family"] for case in cases) == dict.fromkeys(FAMILIES, 12)
    for case in cases:
        with pylopdf.Document(stream=case["pdf"]) as document:
            assert len(document) == 1
            assert document[0].rotation == case["diversity"]["rotation"]
        for table in case["tables"]:
            assert len(table["values"]) == table["row_count"]
            assert all(len(row) == table["col_count"] for row in table["values"])
            assert all(table["values"][s["row"]][s["column"]] is not None for s in table["spans"])
    merged = next(case for case in cases if case["family"] == "merged")
    assert merged["tables"][0]["values"][0][1] is None
    assert merged["tables"][0]["spans"][0]["column_span"] == 2


def test_image_carrier_has_no_injected_reference_text(tmp_path: Path) -> None:
    """Raster wrapping preserves geometry without installing scoring text in the PDF."""
    image = tmp_path / "input.png"
    Image.new("RGB", (24, 32), "white").save(image)
    data = image_pdf(image, 72, 96)
    assert data == image_pdf(image, 72, 96)
    with pylopdf.Document(stream=data) as document:
        assert document[0].rect.width == 72
        assert document[0].rect.height == 96
        assert document[0].get_text() == ""
        assert len(document[0].get_images()) == 1


def test_frozen_manifest_separates_private_references(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Only opaque source fields are admitted to model evidence; rebuilding refuses."""
    case = authored_cases()[0]
    monkeypatch.setattr(corpus, "authored_cases", lambda: [case])
    monkeypatch.setattr(corpus, "native_pages", list)
    monkeypatch.setitem(
        sys.modules, "bench.generalization_scoring", SimpleNamespace(parse_annotation_html=lambda _: {})
    )
    manifest = corpus.build(tmp_path, [])
    assert manifest["model_fields"] == ["id", "pdf_path", "pdf_sha256", "page_number"]
    assert "tables" not in manifest["pages"][0]
    target = json.loads((tmp_path / "private-targets.json").read_text())
    assert target["dataset_sha256"] == manifest["dataset_sha256"]
    assert target["pages"][0]["id"] == manifest["pages"][0]["id"]
    assert target["pages"][0]["tables"] == case["tables"]
    with pytest.raises(ValueError, match="already frozen"):
        corpus.build(tmp_path, [])
