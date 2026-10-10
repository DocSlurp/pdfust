"""Independent forked-process reservation proof with mocked transport only."""

from __future__ import annotations

import json
import multiprocessing
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from bench import decision_hosted as hosted
from bench.decision_concurrent import ConcurrentDecisionClient

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="Requires Unix fork and flock")
def test_independent_processes_reserve_atomically_and_keep_both_charges(  # noqa: PLR0915
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two processes overlap transport; a third admission cannot exceed the wave cap."""
    ctx = multiprocessing.get_context("fork")
    both_transports = ctx.Barrier(3)
    release = ctx.Event()
    results = ctx.Queue()
    base = hosted.DecisionClient.__new__(hosted.DecisionClient)
    base.root = tmp_path
    base.directory = tmp_path / "artifacts"
    base.directory.mkdir()
    base.ledger = base.directory / "ledger.json"
    base.key = "mock-only-key"
    monkeypatch.setattr(base, "_prior_api_cost", lambda: 0)
    monkeypatch.setattr(base, "_telemetry", lambda *_args: {"status": "disabled"})

    def opener(_request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401
        assert timeout == 90
        both_transports.wait(timeout=10)
        assert release.wait(timeout=10)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"usage":{"cost":0.01}}'
        return response

    client = ConcurrentDecisionClient(base, max_inflight=3, wave_limits={"P002": 0.6}, opener=opener)

    def worker(name: str) -> None:
        try:
            result = client.request({"model": hosted.JEV, "state": name, "questions": {}}, tag=f"P002/{name}")
            results.put(("ok", result["entry"]["index"]))
        except Exception as exc:  # noqa: BLE001
            results.put(("error", type(exc).__name__))

    processes = [ctx.Process(target=worker, args=(name,)) for name in ("a", "b")]
    try:
        for process in processes:
            process.start()
        both_transports.wait(timeout=10)
        before = json.loads(base.ledger.read_text())
        assert len(before["requests"]) == 2
        assert sum(row["accounted_usd"] for row in before["requests"]) == pytest.approx(0.6)
        assert {row["concurrent_state"] for row in before["requests"]} == {"in_flight"}
        with pytest.raises(RuntimeError, match="wave cap"):
            client.request({"model": hosted.JEV, "state": "c", "questions": {}}, tag="P002/c")
        release.set()
        for process in processes:
            process.join(timeout=10)
            assert process.exitcode == 0
        assert sorted(results.get(timeout=2) for _ in processes) == [("ok", 0), ("ok", 1)]
        after = json.loads(base.ledger.read_text())
        assert len(after["requests"]) == 2
        assert {row["concurrent_state"] for row in after["requests"]} == {"completed"}
        assert len({row["reservation_uuid"] for row in after["requests"]}) == 2
        assert sum(row["accounted_usd"] for row in after["requests"]) == pytest.approx(0.02)
        assert "mock-only-key" not in base.ledger.read_text()
    finally:
        release.set()
        for process in processes:
            if process.pid is not None:
                process.join(timeout=2)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
        results.close()
        results.join_thread()
