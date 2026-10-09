"""Selection policy must be reproducible and independent of recognition answers."""

from copy import deepcopy

import pytest
from bench.omnidoc_sample import features, row_id, select_rows


def sample_row(identifier: str, source: str, language: str, layout: str, categories: list[str]) -> dict:
    return {
        "page_info": {
            "image_path": identifier,
            "page_attribute": {
                "data_source": source,
                "language": language,
                "layout": layout,
            },
        },
        "layout_dets": [{"category_type": category, "text": "secret answer"} for category in categories],
    }


def test_selection_ignores_answers_and_source_order() -> None:
    rows = [
        sample_row(
            f"{index}.png",
            str(index % 3),
            str(index % 2),
            str(index % 4),
            ["table"] if index % 2 else ["equation_isolated"],
        )
        for index in range(20)
    ]
    changed = deepcopy(rows)
    changed.reverse()
    for row in changed:
        for block in row["layout_dets"]:
            block["text"] = "entirely different recognition answer"
            block["latex"] = "different equation"
    assert [row_id(row) for row in select_rows(rows, 8)] == [row_id(row) for row in select_rows(changed, 8)]
    assert set().union(*(features(row) for row in select_rows(rows, 8))) == set().union(
        *(features(row) for row in rows)
    )


def test_rejects_duplicate_ids_and_invalid_count() -> None:
    row = sample_row("one.png", "book", "english", "single_column", [])
    with pytest.raises(ValueError, match="unique"):
        select_rows([row, row], 1)
    with pytest.raises(ValueError, match="count"):
        select_rows([row], 2)
