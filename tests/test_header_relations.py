"""Independent relationship checks for the private CPU benchmark prototype."""

from __future__ import annotations

import pytest
from bench.header_relations import (
    Decision,
    first_row,
    fixture_pdf,
    fixtures,
    gold_edges,
    graph,
    infer_bands,
    normalized_edges,
    strict_bands,
)

import pdfust


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("family", ["hierarchy", "repeated-labels", "units", "row-headings"])
def test_source_graph_matches_declared_scope(family: str, rotation: int) -> None:
    """Merged ancestry, repeated labels, and row scope survive rotation."""
    fixture = next(item for item in fixtures() if item.family == family)
    with pdfust.open(stream=fixture_pdf(fixture, rotation=rotation)) as doc:
        layout = doc[0].get_layout()
    table = layout.tables[0]
    decision = infer_bands(table)
    assert (decision.header_rows, decision.row_header_columns) == (fixture.header_rows, fixture.row_headers)
    edges = graph(table, decision)
    assert normalized_edges(table, edges) == gold_edges(fixture)
    source_ids = {cell.id for cell in table.cells}
    assert all(edge.source_id in source_ids and edge.target_id in source_ids for edge in edges)
    assert {word_id for cell in table.cells for word_id in cell.word_ids} <= {word.id for word in layout.words}
    # Prove snapshot references are sufficient after closing the document.
    assert all(table.cells[index].text for index in range(len(table.cells)))


@pytest.mark.parametrize("family", ["numeric-headers", "date-headers", "headerless-numeric", "all-text-headers"])
def test_ambiguous_semantics_preserve_original_cells(family: str) -> None:
    """Lack of semantic evidence produces no invented header edges."""
    fixture = next(item for item in fixtures() if item.family == family)
    with pdfust.open(stream=fixture_pdf(fixture)) as doc:
        table = doc[0].get_layout().tables[0]
    before = table.cells
    decision = infer_bands(table)
    assert decision.header_rows is None
    assert graph(table, decision) == ()
    assert table.cells == before


def test_repeated_labels_keep_distinct_parent_ids() -> None:
    """Repeated Count labels have separate East/West ancestries."""
    fixture = next(item for item in fixtures() if item.family == "repeated-labels")
    with pdfust.open(stream=fixture_pdf(fixture)) as doc:
        table = doc[0].get_layout().tables[0]
    counts = [cell for cell in table.cells if cell.text == "Count"]
    assert len(counts) == 2
    assert counts[0].id != counts[1].id
    ancestors = [edge for edge in graph(table, infer_bands(table)) if edge.kind == "ancestor"]
    parents = {edge.source_id for edge in ancestors if edge.target_id in {cell.id for cell in counts}}
    assert len(parents) == 2
    assert first_row(table).header_rows is None


def test_known_type_shift_false_positive_is_scored_as_wrong() -> None:
    """A plausible source-only edge can still be semantically false."""
    fixture = next(item for item in fixtures() if item.family == "headerless-type-shift")
    with pdfust.open(stream=fixture_pdf(fixture)) as doc:
        table = doc[0].get_layout().tables[0]
    decision = infer_bands(table)
    assert decision.header_rows == 1
    assert gold_edges(fixture) == set()
    assert normalized_edges(table, graph(table, decision))


def test_declared_band_cannot_split_a_merged_header() -> None:
    """Graph construction enforces the production merged-cell invariant."""
    fixture = next(item for item in fixtures() if item.family == "hierarchy")
    with pdfust.open(stream=fixture_pdf(fixture)) as doc:
        table = doc[0].get_layout().tables[0]
    with pytest.raises(pdfust.PdfError, match="merged"):
        graph(table, Decision(1, 0, "invalid declaration"))


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_identical_observations_require_independent_role_evidence(rotation: int) -> None:
    """Metadata-free inference cannot distinguish identical PDFs with different scope."""
    data = next(item for item in fixtures() if item.family == "headerless-type-shift")
    header = next(item for item in fixtures() if item.family == "type-shift-declared-header")
    assert fixture_pdf(data, rotation=rotation) == fixture_pdf(header, rotation=rotation)
    with pdfust.open(stream=fixture_pdf(data, rotation=rotation)) as doc:
        table = doc[0].get_layout().tables[0]
    assert strict_bands(table).header_rows is None
    assert graph(table, strict_bands(table)) == ()
    assert graph(table, strict_bands(table, declared=(0, 0))) == ()
    declared = strict_bands(table, declared=(1, 0))
    assert normalized_edges(table, graph(table, declared)) == gold_edges(header)
    assert gold_edges(data) != gold_edges(header)


def test_segmented_outer_border_preserves_pixels_and_native_detection() -> None:
    """Adjacent collinear PDF rule segments retain native table connectivity."""
    fixture = next(item for item in fixtures() if item.family == "three-level")
    results = []
    for coalesce in (False, True):
        with pdfust.open(stream=fixture_pdf(fixture, coalesce=coalesce)) as doc:
            results.append((doc[0].get_pixmap().samples, doc[0].get_layout()))
    assert results[0][0] == results[1][0]
    assert results[0][1].tables == results[1][1].tables
    table = results[1][1].tables[0]
    assert normalized_edges(table, graph(table, infer_bands(table))) == gold_edges(fixture)
