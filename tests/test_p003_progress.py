"""Progress tables preserve verified quality, financial provenance and provider cache scope."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.p003_progress import cache_usage, load_evaluations, render
from bench.silver import sha, write_json


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


@pytest.mark.parametrize(
    ("processor", "incremental", "call_key"),
    [
        ("p003_gate", "incremental_gate", "calls"),
        ("p003_topology_source", "incremental_ownership", "topology_calls"),
    ],
)
def test_gate_and_ownership_cache_scope_excludes_historical_usage(
    tmp_path: Path, processor: str, incremental: str, call_key: str
) -> None:
    def call(index: int, tokens: int) -> dict[str, Any]:
        return {
            "entry": {"index": index},
            "usage": {"prompt_tokens_details": {"cached_tokens": tokens}},
            "replayed": False,
        }

    page = {"calls": [call(0, 999)], call_key: [call(1, 7)]}
    report = {"config": {"processor": processor}, "results": [page], incremental: {"ledger_attempts": 1}}
    historical = {"results": [{"calls": [call(0, 999)]}], "ledger_attempts": 1}
    if processor == "p003_gate":
        report["baseline_report"] = historical
    else:
        report.update(source_generation_report=historical, topology_generation_report=historical)
    write_json(tmp_path / "report.json", report)
    record = {**run_record(), "report_sha256": sha((tmp_path / "report.json").read_bytes())}
    write_json(tmp_path / "evaluation.json", {"runs": [record]})
    runs, _ = load_evaluations([tmp_path / "evaluation.json"])
    assert runs[0]["provider_cache_usage"]["counters"]["cached_tokens"]["complete_counter_total"] == 7
    assert runs[0]["historical_provider_cache_usage"][0]["counters"]["cached_tokens"]["complete_counter_total"] == 999


def test_cache_usage_normalizes_nested_provider_wrappers_before_deduplication() -> None:
    usage = {"prompt_tokens_details": {"cached_tokens": 7, "cache_write_tokens": 11}}
    wrapped = {"entry": {"index": 1}, "result": {"usage": usage}, "replayed": False}
    flattened = {"entry": {"index": 1}, "usage": usage, "replayed": False}
    observed = cache_usage([wrapped, flattened], 1)
    assert observed["unique_fresh_returned_attempts"] == 1
    assert observed["counters"]["cached_tokens"]["complete_counter_total"] == 7
    assert observed["counters"]["cache_write_tokens"]["complete_counter_total"] == 11
    conflicting = deepcopy(wrapped)
    conflicting["result"]["usage"]["prompt_tokens_details"]["cached_tokens"] = 8
    with pytest.raises(ValueError, match="Conflicting provider usage"):
        cache_usage([wrapped, conflicting], 1)


def test_transcript_usage_is_historical_with_original_attempt_denominator(tmp_path: Path) -> None:
    call = {
        "entry": {"index": 11},
        "result": {"usage": {"prompt_tokens_details": {"cached_tokens": 7, "cache_write_tokens": 11}}},
        "replayed": False,
    }
    report = {
        "config": {"processor": "p003_topology_source", "transcript_replay": True},
        "results": [{"topology_calls": [call]}],
        "incremental_ownership": {"ledger_attempts": 0},
        "transcript_origin": {"original_report": {"incremental_ownership": {"ledger_attempts": 2}}},
    }
    write_json(tmp_path / "report.json", report)
    record = {**run_record(), "report_sha256": sha((tmp_path / "report.json").read_bytes())}
    write_json(tmp_path / "evaluation.json", {"runs": [record]})
    runs, _ = load_evaluations([tmp_path / "evaluation.json"])
    current = runs[0]["provider_cache_usage"]
    historical = runs[0]["retained_transcript_provider_cache_usage"]
    assert current["unique_fresh_returned_attempts"] == current["ledger_attempts"] == 0
    assert historical["unique_fresh_returned_attempts"] == 1
    assert historical["ledger_attempts"] == 2
    assert historical["counters"]["cached_tokens"]["provider_reported_known_subtotal"] == 7
    assert historical["counters"]["cached_tokens"]["complete_counter_total"] is None
    text = render(runs, [])
    assert "current measured stage | 0/0" in text
    assert "historical retained ownership decisions | 1/2 | 7 | 11" in text


def test_progress_displays_explicit_new_treatments() -> None:
    record = run_record()
    record["config"].update(
        image_visibility="blur",
        image_mode="rgb_palette16",
        gate_instructions="recall_first",
        evidence_mode="differences",
        ownership_protocol="direct_cell",
        topology_evidence="neighbors",
    )
    record.update(evaluation_sha256="fixture")
    text = render([record], [])
    for key, value in record["config"].items():
        if key != "transport_concurrency":
            assert f"{key}={value}" in text
