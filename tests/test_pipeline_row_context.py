"""Source-only row context preserves identity and refuses incomplete packets."""

import json
from copy import deepcopy

import pytest
from bench.pipeline_row_context import context
from test_pipeline_row_evidence import source


@pytest.mark.parametrize("ordinal", [False, True])
def test_context_keeps_complete_identity_without_duplicating_words(*, ordinal: bool) -> None:
    data = source()
    original = deepcopy(data)
    packet = json.loads(context(data, ordinal=ordinal).split("\n", 1)[1])
    assert data == original
    assert "words" not in packet
    assert "word_fields" not in packet
    key = "word_indexes" if ordinal else "source_ids"
    assert [identifier for row in packet["rows"] for identifier in row[key]] == (
        list(range(4)) if ordinal else [word["id"] for word in data["words"]]
    )
    assert packet["rows"][1]["adjacent"]["previous"]["center_gap_em"] == 2


def test_context_ignores_reference_metadata_and_refuses_over_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    data = source()
    before = context(data)
    data.update(gold="irrelevant", family="irrelevant", filename="irrelevant.pdf")
    assert context(data) == before
    monkeypatch.setattr("bench.pipeline_row_context.MAX_CONTEXT_BYTES", 20)
    with pytest.raises(ValueError, match="no truncation"):
        context(data)
