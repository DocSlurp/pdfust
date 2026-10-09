"""Hosted retrieval validates the independent-vector contract."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PIL")
from bench.decision_hosted import read_key
from bench.decision_retrieval_run import parse_embeddings


def test_embedding_parser_orders_indexes() -> None:
    assert parse_embeddings(
        {"data": [{"index": 1, "embedding": [0.1, 0.2]}, {"index": 0, "embedding": [0.3, 0.4]}]}, 2
    ) == [[0.3, 0.4], [0.1, 0.2]]


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [{"index": 0, "embedding": [1]}, {"index": 0, "embedding": [2]}],
        [{"index": True, "embedding": [1]}, {"index": 1, "embedding": [2]}],
        [{"index": 0, "embedding": [float("nan")]}, {"index": 1, "embedding": [2]}],
    ],
)
def test_embedding_parser_rejects_incomplete_or_invalid(rows: list) -> None:
    with pytest.raises(ValueError, match="Embedding"):
        parse_embeddings({"data": rows}, 2)


def test_openrouter_env_precedence_and_fallback(tmp_path: Path) -> None:
    (tmp_path / ".env.remote-hosts").write_text("OPENROUTER_API_KEY=old-fixture\n")
    assert read_key(tmp_path) == "old-fixture"
    (tmp_path / ".env").write_text('OPENROUTER_API_KEY="new-fixture" # comment\n')
    assert read_key(tmp_path) == "new-fixture"
    (tmp_path / ".env").write_text('OPENROUTER_API_KEY=""\n')
    assert read_key(tmp_path) == "old-fixture"
