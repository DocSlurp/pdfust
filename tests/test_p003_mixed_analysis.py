"""Mixed diagnostics retain failed secondary pages and expose false duplicate status labels."""

from bench.p003_mixed_analysis import page_sensitivity, ranking_admission


def test_distinct_pending_pool_is_never_counted_as_genuine_duplicate() -> None:
    report = {
        "results": [
            {
                "ranking_status": "failed_retained_first",
                "ranking_regions": [
                    {"ranking_status": "not_applicable_duplicates", "pool": {"candidates": [1]}},
                    {"ranking_status": "not_applicable_duplicates", "pool": {"candidates": [1, 2]}},
                ],
                "ranking_errors": [
                    {"error_type": "ValueError", "detail": "Request exceeds frozen model/input admission"}
                ],
                "ranking_calls": [],
            }
        ],
        "incremental_ranking": {"ledger_attempts": 0},
    }
    observed = ranking_admission(report)
    assert observed["genuine_duplicate_pools"] == observed["distinct_pools_mislabeled_duplicates"] == 1
    assert observed["input_admission_refusals"] == 1
    assert observed["page_status_counts"]["failed_retained_first"] == 1


def test_secondary_sensitivity_keeps_failed_positive_and_negative_denominators() -> None:
    def page(identifier: str, cells: int, correct: int, error: int) -> dict[str, int | str]:
        return {
            "id": identifier,
            "strict_exact_cells": correct,
            "expected_cells": cells,
            "expected_tables": int(cells > 0),
            "complete_tables": int(correct == cells and cells > 0),
            "missing_tables": int(error > 0),
            "false_positive_tables": 0,
            "false_positive_page": 0,
            "error": error,
            "negative_page": int(cells == 0),
            "positive_page": int(cells > 0),
        }

    observed = page_sensitivity(
        {
            "page_scores": [
                page("dense", 100, 100, 0),
                page("good", 1, 1, 0),
                page("failed", 1, 0, 1),
                page("negative", 0, 0, 0),
            ]
        },
        frozenset({"dense"}),
    )
    assert observed["retained_pages"] == 3
    assert observed["positive_pages"] == 2
    assert observed["totals"]["error"] == observed["totals"]["negative_page"] == 1
    assert observed["positive_macro_strict_recall"] == 0.5
    assert observed["dense_strict_cells"] == 100
