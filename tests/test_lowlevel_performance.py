"""Verify benchmark gates reject skipped work while retaining observations."""

from __future__ import annotations

from typing import Any

import pytest
from bench.lowlevel_performance import benchmark


def test_benchmark_oracles_fail_for_skipped_work(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def skipped(data: bytes, mode: str) -> dict[str, Any]:
        calls.append((data, mode))
        return {
            "text_sha256": "complete" if mode == "text" else "skipped",
            "character_conservation": mode == "text",
            "output_bytes": 8,
        }

    monkeypatch.setattr("bench.lowlevel_performance.extract", skipped)
    monkeypatch.setattr("bench.lowlevel_performance._environment", dict)
    result = benchmark({"toy": [("a", b"pdf-a"), ("b", b"pdf-b")]}, repeats=2, inner_repeats=2)
    assert not result["all_text_hashes_match"]
    assert not result["mapped_nonwhitespace_characters_conserved"]
    assert len(result["runs"]) == 4
    assert all(len(run["documents"]) == 4 for run in result["runs"])
    assert len(calls) == 20  # Both modes warm both inputs, then 16 timed workload units.
    assert result["runs"][0]["order"] == ["text", "snapshot_text"]
    assert result["runs"][2]["order"] == ["snapshot_text", "text"]
    assert all(run["user_cpu_seconds"] >= 0 and run["system_cpu_seconds"] >= 0 for run in result["runs"])
    assert result["summaries"]["toy"]["paired_repetitions_same_process"] == 2


def test_benchmark_rejects_empty_or_duplicate_workloads() -> None:
    workloads: list[dict[str, list[tuple[str, bytes]]]] = [{"empty": []}, {"duplicate": [("a", b"x"), ("a", b"y")]}]
    for workload in workloads:
        with pytest.raises(ValueError, match="unique source"):
            benchmark(workload)
    with pytest.raises(ValueError, match="positive"):
        benchmark({"toy": [("a", b"x")]}, repeats=0)
