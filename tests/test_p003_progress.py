"""Progress tables preserve verified quality, financial provenance and provider cache scope."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.p003_progress import cache_usage, load_evaluations, render
from bench.silver import write_json


def run_record() -> dict[str, Any]:
    return {
        "name": "example",
        "report_sha256": "reporthash",
        "code_sha256": {"fixture.py": "trustedhash"},
        "intended_pages": 16,
        "operational_pages": 15,
        "errors": 1,
        "exact_positive_pages": 2,
        "evaluation_scope": "complete pipeline",
        "config": {"transport_concurrency": 3},
        "scores": {
            "complete_tables": 3,
            "expected_tables": 53,
            "strict_exact_cells": 393,
            "expected_cells": 2333,
            "correct_text_cells": 406,
            "correct_structure_cells": 491,
            "missing_tables": 37,
            "false_positive_tables": 1,
            "false_positive_page": 1,
            "negative_page": 4,
        },
        "resources": {"wall_seconds": 100, "cpu_seconds": 80, "peak_rss_bytes": 1024},
        "costs": {"effective_api_usd": None, "accounted_usd_including_reservations": 0.3},
        "pages_per_minute": 9,
        "pages_per_api_usd": None,
    }


def test_progress_prefers_verified_overlay_keeps_original_unknown_and_pending(tmp_path: Path) -> None:
    directory = tmp_path / "example"
    directory.mkdir()
    original = run_record()
    overlay = deepcopy(original)
    overlay.update(cost_reconciliation={"reconciled": {"effective_api_usd": 0.012}}, reconciled_pages_per_api_usd=1250)
    write_json(directory / "evaluation.json", {"runs": [original]})
    write_json(directory / "evaluation-cost-reconciled.json", {"runs": [overlay]})
    runs, pending = load_evaluations([directory, tmp_path / "planned"])
    assert runs[0]["costs"]["effective_api_usd"] is None
    assert runs[0]["cost_reconciliation"]["reconciled"]["effective_api_usd"] == 0.012
    text = render(runs, pending)
    assert "15/16" in text
    assert "393/2333" in text
    assert "contended (3)" in text
    assert "Reconciled pages/APIUSD" in text
    assert "1250" in text
    assert "Pending completed evaluation" in text
    assert str(tmp_path) not in text
    assert "| Run | Model | Treatment |" in text


def test_progress_rejects_removed_error_denominator(tmp_path: Path) -> None:
    run = run_record()
    run["intended_pages"] = 15
    write_json(tmp_path / "evaluation.json", {"runs": [run]})
    with pytest.raises(ValueError, match="denominator"):
        load_evaluations([tmp_path / "evaluation.json"])


def test_cache_usage_deduplicates_fresh_indices_keeps_missing_counter_unknown() -> None:
    call = {"entry": {"index": 1}, "usage": {"prompt_tokens_details": {"cached_tokens": 7}}, "replayed": False}
    result = cache_usage(
        [
            call,
            deepcopy(call),
            {"entry": {"index": 2}, "usage": {}, "replayed": False},
            {"entry": {"index": 3}, "usage": {}, "replayed": True},
        ],
        3,
    )
    assert result["unique_fresh_returned_attempts"] == 2
    assert not result["all_attempt_usage_coverage"]
    assert result["counters"]["cached_tokens"]["provider_reported_known_subtotal"] == 7
    assert result["counters"]["cached_tokens"]["complete_counter_total"] is None
    assert result["counters"]["cache_write_tokens"]["counter_missing_calls"] == 2
    assert result["replayed_records_excluded"] == 1


def test_cache_usage_rejects_conflicting_same_attempt_usage() -> None:
    calls = [
        {"entry": {"index": 1}, "usage": {"prompt_tokens_details": {"cached_tokens": value}}, "replayed": False}
        for value in (0, 7)
    ]
    with pytest.raises(ValueError, match="Conflicting provider usage"):
        cache_usage(calls, 1)


def test_cache_source_report_requires_independently_verified_hash(tmp_path: Path) -> None:
    write_json(tmp_path / "evaluation.json", {"runs": [run_record()]})
    write_json(tmp_path / "report.json", {"config": {}, "results": []})
    with pytest.raises(ValueError, match="verified report hash"):
        load_evaluations([tmp_path / "evaluation.json"])
