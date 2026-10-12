"""Spatial snapshots, explicit relationships, and bounded source-only decisions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from itertools import repeat

import pytest
from conftest import build_raw_pdf
from test_tables import _bordered_table_pdf

import pdfust


def fields_pdf(items: list[tuple[float, float, str]], rules: str = "") -> bytes:
    content = rules + "\n" + "\n".join(f"BT /F1 12 Tf 1 0 0 1 {x} {300 - y} Tm ({text}) Tj ET" for x, y, text in items)
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: (
                "<< /Type /Pages /Kids [4 0 R] /Count 1 /MediaBox [0 0 400 300] "
                "/Resources << /Font << /F1 3 0 R >> >> >>"
            ),
            3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            4: "<< /Type /Page /Parent 2 0 R /Contents 5 0 R >>",
            5: f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        }
    )


def test_combined_snapshot_matches_existing_paths_without_render(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_render(*_args: object, **_kwargs: object) -> None:
        pytest.fail("spatial extraction must never render")

    monkeypatch.setattr(pdfust.Page, "get_pixmap", no_render)
    with pdfust.open(stream=_bordered_table_pdf()) as doc:
        layout = doc[0].get_layout()
        assert [(word.text, word.bbox) for word in layout.words] == [
            (word[4], word[:4]) for word in doc[0].get_text("words")
        ]
        table = layout.tables[0]
        assert [cell.text for cell in table.cells] == [
            value for row in doc[0].find_tables()[0].extract() for value in row
        ]
        assert layout == doc[0].get_layout()
        assert not doc[0].get_layout(table_strategy=None).tables
        values = table.records(header_rows=1)[0]
        assert [(value.name, value.value) for value in values] == [("Name", "Alpha"), ("Value", "42")]
        for value in values:
            assert " ".join(layout.words[index].text for index in value.cell.word_ids) == value.value


def test_snapshot_lifetime_and_cache_invalidation() -> None:
    with pdfust.open(stream=_bordered_table_pdf()) as doc:
        page = doc[0]
        before = page.get_layout()
        page.insert_text((10, 20), "Added")
        after = page.get_layout()
        assert "Added" in [word.text for word in after.words]
        assert "Added" not in [word.text for word in before.words]
        doc.new_page()
        with pytest.raises(pdfust.StalePageError):
            page.get_layout()
    assert before.select((0, 0, 340, 300)) == before.words
    with pytest.raises(FrozenInstanceError):
        before.width = 1  # type: ignore[misc]


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_table_header_relations_follow_logical_orientation(rotation: int) -> None:
    with pdfust.open(stream=_bordered_table_pdf()) as doc:
        doc[0].set_rotation(rotation)
        layout = doc[0].get_layout()
        assert [(field.name, field.value) for field in layout.tables[0].records(header_rows=1)[0]] == [
            ("Name", "Alpha"),
            ("Value", "42"),
        ]
        for cell in layout.tables[0].cells:
            assert tuple(word.id for word in layout.select(cell.bbox)) == cell.word_ids


def test_merged_hierarchical_headers_preserve_identity() -> None:
    # Two repeated labels have different parents; merged top-left cells span two rows.
    rules = "40 140 320 120 re S 40 180 m 360 180 l S 140 220 m 360 220 l S 140 140 m 140 260 l S 250 140 m 250 220 l S"
    data = fields_pdf(
        [
            (50, 65, "Name"),
            (150, 65, "Revenue"),
            (150, 105, "Revenue"),
            (260, 105, "Cost"),
            (50, 145, "Alpha"),
            (150, 145, "100"),
            (260, 145, "60"),
        ],
        rules,
    )
    with pdfust.open(stream=data) as doc:
        table = doc[0].get_layout().tables[0]
        fields = table.records(header_rows=2, row_header_columns=1)[0]
        assert [item.name for item in fields] == ["Revenue / Revenue", "Revenue / Cost"]
        assert [item.value for item in fields] == ["100", "60"]
        assert fields[0].headers[0].id == fields[1].headers[0].id
        assert fields[0].headers[0].id != fields[0].headers[1].id
        assert fields[0].row_headers[0].text == "Alpha"
        with pytest.raises(pdfust.PdfError, match="merged"):
            table.records(header_rows=1)


def test_explicit_grid_and_half_open_spatial_selection() -> None:
    with pdfust.open(stream=_bordered_table_pdf()) as doc:
        layout = doc[0].get_layout(table_strategy=None)
        table = layout.grid(columns=[40, 170, 300], rows=[40, 80, 120])
        assert [(field.name, field.value) for field in table.records(header_rows=1)[0]] == [
            ("Name", "Alpha"),
            ("Value", "42"),
        ]
        first = layout.words[0]
        center = (first.bbox[0] + first.bbox[2]) / 2
        assert first not in layout.select((0, 0, center, 300))
        assert first in layout.select((center, 0, 340, 300))
        assert layout.extract_fields([pdfust.FieldSpec("value", region=(170, 80, 300, 120))])[0].value == "42"


def test_anchor_assignment_abstains_and_preserves_candidates() -> None:
    data = fields_pdf([(40, 60, "Total:"), (130, 60, "42"), (250, 60, "99")])
    with pdfust.open(stream=data) as doc:
        layout = doc[0].get_layout(table_strategy=None)
    spec = pdfust.FieldSpec("total", anchor="Total", max_distance=250, value_type="number")
    result = layout.extract_fields([spec])[0]
    assert result.status == "ambiguous"
    assert result.value is None
    assert {candidate.text for candidate in result.candidates} == {"42", "99"}
    # Fixed test coefficients make the nearest candidate win; this is a policy
    # test, not evidence that these coefficients generalize to real documents.
    model = pdfust.PlacementModel((40, 0, 0, 0, 0, 0), -4, threshold=0.9, margin=0.3)
    resolved = layout.extract_fields([spec], model=model)[0]
    assert resolved.value == "42"
    assert resolved.selected is not None
    assert resolved.selected.anchor_ids == (0,)
    assert resolved.selected.word_ids == result.candidates[0].word_ids
    cautious = pdfust.PlacementModel((0, 0, 0, 0, 0, 0), 20, margin=0.2)
    assert layout.extract_fields([spec], model=cautious)[0].status == "ambiguous"


def test_duplicate_anchor_missing_and_conflicting_values() -> None:
    data = fields_pdf([(40, 50, "ID:"), (140, 50, "A123"), (40, 100, "ID:"), (140, 100, "B456")])
    with pdfust.open(stream=data) as doc:
        layout = doc[0].get_layout(table_strategy=None)
    results = layout.extract_fields(
        [
            pdfust.FieldSpec("duplicate", anchor="ID"),
            pdfust.FieldSpec("missing", anchor="Never"),
        ]
    )
    assert [result.status for result in results] == ["ambiguous", "missing"]
    bounded = pdfust.FieldSpec("first", region=(0, 20, 300, 70), anchor="ID")
    assert layout.extract_fields([bounded])[0].value == "A123"
    conflict = layout.extract_fields([bounded, pdfust.FieldSpec("second", region=(120, 20, 200, 70))])
    assert [result.status for result in conflict] == ["conflict", "conflict"]
    assert all(result.value is None for result in conflict)


def test_values_cannot_cross_other_declared_labels() -> None:
    data = fields_pdf([(30, 50, "Tax:"), (95, 50, "10"), (160, 50, "Total:"), (250, 50, "90")])
    with pdfust.open(stream=data) as doc:
        layout = doc[0].get_layout(table_strategy=None)
    results = layout.extract_fields(
        [
            pdfust.FieldSpec("tax", anchor="Tax", value_type="number", max_distance=300),
            pdfust.FieldSpec("total", anchor="Total", value_type="number"),
        ]
    )
    assert [result.value for result in results] == ["10", "90"]


def test_spatial_limits_admit_interpretation_once_and_recover_after_refusal() -> None:
    # Exactly 16 source glyphs. A combined interpretation must not charge twice.
    data = _bordered_table_pdf()
    with pdfust.open(stream=data, limits=pdfust.DocumentLimits(max_text_glyphs=16)) as doc:
        assert doc[0].get_layout().tables
        assert doc[0].get_text("words")
        assert doc[0].find_tables()
    with pdfust.open(stream=data, limits=pdfust.DocumentLimits(max_text_glyphs=1)) as doc:
        for _ in range(2):
            with pytest.raises(pdfust.LimitError) as error:
                doc[0].get_layout()
            assert error.value.code == "text_glyph_count"
    with pdfust.open(stream=data) as doc:
        doc.new_page().insert_text((20, 20), "X")
        two_pages = doc.tobytes()
    with pdfust.open(stream=two_pages, limits=pdfust.DocumentLimits(max_text_glyphs=1)) as doc:
        with pytest.raises(pdfust.LimitError):
            doc[0].get_layout()
        assert [word.text for word in doc[1].get_layout().words] == ["X"]


def test_query_and_serialization_boundaries() -> None:
    with pdfust.open(stream=_bordered_table_pdf()) as doc:
        layout = doc[0].get_layout()
    with pytest.raises(pdfust.PdfError):
        layout.select((0, 0, float("nan"), 5))
    with pytest.raises(pdfust.PdfError):
        layout.grid(columns=[0, 5, 4], rows=[0, 5])
    with pytest.raises(pdfust.LimitError):
        layout.grid(columns=list(range(66)), rows=list(range(66)))
    with pytest.raises(pdfust.LimitError):
        layout.extract_fields(repeat(pdfust.FieldSpec("a", anchor="Name")))
    with pytest.raises(pdfust.PdfError):
        pdfust.PlacementModel((1,), 0)
    with pytest.raises(pdfust.PdfError):
        pdfust.FieldSpec("a")
    with pytest.raises(pdfust.PdfError):
        pdfust.FieldSpec("a", anchor="x", max_distance=float("nan"))
    text = layout.tables[0].to_bullets(header_rows=1)
    assert "Name: Alpha" in text
    assert "Value: 42" in text
    assert layout.tables[0].to_bullets(header_rows=1, max_size=len(text.encode())) == text
    with pytest.raises(pdfust.LimitError):
        layout.tables[0].to_bullets(header_rows=1, max_size=5)
