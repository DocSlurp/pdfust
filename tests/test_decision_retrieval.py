"""Local deterministic checks for image-only retrieval fixtures and scoring."""

import math

import pytest
from bench.decision_retrieval import (
    evaluate,
    image_embedding_body,
    literal_baseline,
    normalized_literal,
    query_embedding_body,
    retrieval_cases,
)


def tiny_cases() -> dict:
    return {
        "documents": [{"id": "positive"}, {"id": "negative"}],
        "queries": [
            {"id": "match", "positive_ids": ["positive"], "hard_negative_ids": ["negative"]},
            {"id": "none", "positive_ids": [], "hard_negative_ids": []},
        ],
    }


def test_fixtures_and_literal_context_ambiguity() -> None:
    cases = retrieval_cases()
    assert len(cases["documents"]) == 24
    assert len(cases["queries"]) == 8
    assert len({doc["id"] for doc in cases["documents"]}) == 24
    baseline = literal_baseline(cases)
    assert baseline["matched_queries"] == 6
    assert baseline["no_match_queries"] == 2
    assert baseline["forced_no_match_false_hits"] == 2
    assert all(
        baseline["literal_match_counts"][query["id"]] == 0 for query in cases["queries"] if not query["positive_ids"]
    )
    # A literal phrase exists across the separate-cell negative despite the
    # semantic requirement that the expression belong to one record/cell.
    assert all(
        baseline["literal_match_counts"][query["id"]] == 3 for query in cases["queries"] if query["positive_ids"]
    )


def test_image_body_excludes_native_text() -> None:
    body = image_embedding_body("provider/model", ["data:image/png;base64,AA=="])
    assert body["input"] == [{"content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}]}]
    assert "text" not in str(body)
    assert query_embedding_body("provider/model", ["plain query"])["input"] == ["plain query"]


def test_perfect_rank_and_no_match_are_separate() -> None:
    result = evaluate({"positive": [1, 0], "negative": [0, 1]}, {"match": [1, 0], "none": [-1, 0]}, tiny_cases())
    assert result["mrr"] == result["recall_at_1"] == result["pair_win_rate"] == 1
    assert result["forced_no_match_false_hits"] == 1
    assert result["rows"][1]["hit_at_1"] is None


def test_ties_deterministic_and_not_pair_wins() -> None:
    result = evaluate(
        {"positive": [1e300, 0], "negative": [1e-300, 0]}, {"match": [1, 0], "none": [1, 0]}, tiny_cases()
    )
    assert result["rows"][0]["ranking"] == ["negative", "positive"]
    assert result["pair_win_rate"] == 0
    assert result["pair_ties"] == 1
    assert result["mrr"] == 0.5


@pytest.mark.parametrize("bad", [[], [0, 0], [math.nan, 1], [math.inf, 1], [1]])
def test_invalid_vectors_reject_complete_scores(bad: list[float]) -> None:
    with pytest.raises(ValueError, match=r"dimension|nonfinite|zero"):
        evaluate({"positive": [1, 0], "negative": bad}, {"match": [1, 0], "none": [1, 0]}, tiny_cases())


def test_missing_id_rejected() -> None:
    with pytest.raises(ValueError, match="IDs"):
        evaluate({"positive": [1, 0]}, {"match": [1, 0], "none": [1, 0]}, tiny_cases())


def test_literal_hyphen_join_and_whitespace() -> None:
    assert normalized_literal("Recom-\nmended dosage\n 20 mg daily") == "recommended dosage 20 mg daily"
    assert normalized_literal("high-quality") == "high-quality"
