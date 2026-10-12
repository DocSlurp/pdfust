from __future__ import annotations

import pytest
from bench.feature_cases import FeatureCase, build_cases
from bench.features import inspect_output

import pylopdf


@pytest.fixture(scope="module")
def cases() -> dict[str, FeatureCase]:
    """Build the inputs once; their inventories establish the intended coverage."""
    return {case.name: case for case in build_cases()}


def test_feature_fixtures_contain_links_images_merged_cells_and_unicode(cases: dict[str, FeatureCase]) -> None:
    with pylopdf.open(stream=cases["links-and-outline"].data) as doc:
        links = doc[0].get_links()
        assert [link["kind"] for link in links] == [pylopdf.LINK_URI, pylopdf.LINK_GOTO, pylopdf.LINK_GOTO]
        assert links[1]["page"] == links[2]["page"] == 1
        assert links[2]["nameddest"] == "section-two"
        assert doc.get_toc() == [[1, "Outline destination", 2]]
    with pylopdf.open(stream=cases["image-only"].data) as doc:
        assert doc.get_text() == ""
        assert len(doc[0].get_images()) == 1
        assert doc[0].get_drawings()
    with pylopdf.open(stream=cases["table-merged"].data) as doc:
        table = doc[0].find_tables()[0]
        assert table.extract()[0][:2] == ["Merged header", None]
        assert table.extract()[-1][-1] == ""
    with pylopdf.open(stream=cases["unicode-cmap-and-emoji"].data) as doc:
        assert doc.metadata["title"] == cases["unicode-cmap-and-emoji"].source_values["title"]
        assert b"D83DDE00" in cases["unicode-cmap-and-emoji"].data
        assert all(value in doc.get_text() for value in cases["unicode-cmap-and-emoji"].expected_text)


def test_markdown_observations_distinguish_literal_punctuation_from_structure() -> None:
    pytest.importorskip("markdown_it")
    pytest.importorskip("mdit_py_plugins")
    case = FeatureCase("probe", b"", (), "", ("Literal *stars*", "cell", "formula"))
    output = (
        r"Literal \*stars\*"
        "\n\n**bold** _italic_ `code`\n\n"
        '<table><tr><td colspan="2">cell</td></tr></table>\n\n'
        "$formula$\n\n[section](#target)\n\n![caption](image.png)"
    )
    observed = inspect_output(output, "markdown", case)
    assert all(observed["literal_text"].values())
    assert observed["syntax"]["strong"] == observed["syntax"]["emphasis"] == 1
    assert observed["syntax"]["html_tables"] == 1
    assert observed["syntax"]["html_table_spans"] == [{"colspan": "2"}]
    assert observed["syntax"]["math"] == observed["syntax"]["images"] == 1
    assert observed["syntax"]["links"] == ["#target"]
    plain = inspect_output(output, "text", case)
    assert plain["syntax"] == {}


def test_reference_order_fails_when_text_is_missing_or_interleaved() -> None:
    case = FeatureCase("order", b"", (), "", expected_order=("LEFT0", "LEFT1", "RIGHT0", "RIGHT1"))
    assert inspect_output("LEFT0 LEFT1 RIGHT0 RIGHT1", "text", case)["reference_order"]
    assert not inspect_output("LEFT0 RIGHT0 LEFT1 RIGHT1", "text", case)["reference_order"]
    assert not inspect_output("LEFT0 LEFT1 RIGHT0", "text", case)["reference_order"]


