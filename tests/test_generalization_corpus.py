"""CPU-only checks for frozen P002 inputs and construction references."""

# Test fixture rows retain a readable construction loop.
# ruff: noqa: PERF401

import io
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


def test_natural_screen_is_separate_and_metadata_selected(tmp_path: Path) -> None:
    """The second screen preserves source identities and leaves the base manifest untouched."""
    pages = []
    targets = []
    for row in _rows():
        count = len(row["layout_dets"])
        identifier = row["page_info"]["image_path"]
        family = ("no-table", "single-table", "multiple-table")[count]
        pages.append(
            {
                "id": identifier,
                "family": "omni/" + family,
                "pdf_path": "/unused/input.pdf",
                "pilot": False,
                "diversity": {"attributes": row["page_info"]["page_attribute"], "category_counts": {"table": count}},
            }
        )
        targets.append({"id": identifier, "tables": [], "structural_scored": True})
    base = {"schema": 1, "split": "DEV", "dataset_sha256": "frozen-base", "pages": pages}
    corpus.write_json(tmp_path / "manifest.json", base)
    corpus.write_json(tmp_path / "private-targets.json", {"pages": targets})
    corpus.write_json(tmp_path / "private-provenance.json", [])
    original = (tmp_path / "manifest.json").read_bytes()
    screen = corpus.natural_screen(tmp_path)
    assert len(screen["pages"]) == 16
    assert Counter(row["family"] for row in screen["pages"]) == {
        "omni/multiple-table": 6,
        "omni/single-table": 6,
        "omni/no-table": 4,
    }
    assert all(row["pilot"] for row in screen["pages"])
    assert screen["source_dataset_sha256"] == "frozen-base"
    assert screen["dataset_sha256"] != "frozen-base"
    assert (tmp_path / "manifest.json").read_bytes() == original
    with pytest.raises(ValueError, match="already frozen"):
        corpus.natural_screen(tmp_path)


def test_transparent_carrier_composites_onto_white(tmp_path: Path) -> None:
    """Invisible black RGBA background cannot erase visible black source text."""
    image = tmp_path / "transparent.png"
    rgba = Image.new("RGBA", (24, 32), (0, 0, 0, 0))
    rgba.putpixel((5, 5), (0, 0, 0, 255))
    rgba.save(image)
    with pylopdf.Document(stream=image_pdf(image, 72, 96)) as document:
        retained = Image.open(io.BytesIO(document[0].get_images()[0]["image"])).convert("RGB")
        assert retained.getpixel((0, 0)) == (255, 255, 255)
        assert retained.getpixel((5, 5)) == (0, 0, 0)


def test_white_alpha_revision_preserves_r1_and_stable_ids(tmp_path: Path) -> None:
    """A source correction creates a new frozen identity, never overwriting the old manifest."""
    image = tmp_path / "ocr-carrier-00.png"
    Image.new("RGBA", (24, 32), (0, 0, 0, 0)).save(image)
    pages = [
        {
            "id": "carrier",
            "family": "authored/ocr-carrier",
            "pdf_path": "/original/carrier.pdf",
            "pdf_sha256": "r1-source",
        },
        {"id": "native", "family": "native/diagnostic", "pdf_path": "/original/native.pdf", "pdf_sha256": "unchanged"},
    ]
    base = {"schema": 1, "split": "DEV", "dataset_sha256": "r1-frozen", "pages": pages}
    targets = {"schema": 1, "dataset_sha256": "r1-frozen", "pages": [{"id": row["id"], "tables": []} for row in pages]}
    corpus.write_json(tmp_path / "manifest.json", base)
    corpus.write_json(tmp_path / "private-targets.json", targets)
    corpus.write_json(
        tmp_path / "private-provenance.json", [{"id": "carrier", "source_case": "authored/ocr-carrier-00"}]
    )
    original = (tmp_path / "manifest.json").read_bytes()
    revised = corpus.white_alpha_revision(tmp_path)
    assert revised["parent_dataset_sha256"] == "r1-frozen"
    assert revised["dataset_sha256"] != "r1-frozen"
    assert revised["pages"][0]["id"] == "carrier"
    assert revised["pages"][0]["pdf_sha256"] != "r1-source"
    assert revised["pages"][1] == pages[1]
    assert (tmp_path / "manifest.json").read_bytes() == original
    with pytest.raises(ValueError, match="already frozen"):
        corpus.white_alpha_revision(tmp_path)
