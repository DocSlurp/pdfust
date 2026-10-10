"""CPU-only synthetic replay and resource measurement; no provider requests."""

# Resource measurement is an explicitly Linux-local benchmark, not a library API.
# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import argparse
import json
import platform
import resource
import time
from pathlib import Path
from typing import Any

from bench.decision_p003_boundaries import apply, request
from bench.pipeline_repair import _table


def synthetic(rows: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create known local source rows, alternating records and hanging continuations."""
    words, cells = [], []
    for row in range(rows):
        parts = []
        for col, text in enumerate(["continued" if row % 2 else f"Record-{row // 2}", "" if row % 2 else "10"]):
            ids = []
            if text:
                ident = f"w{row}c{col}"
                words.append({"id": ident, "text": text, "bbox": [col * 100, row * 12, col * 100 + 45, row * 12 + 10]})
                ids.append(ident)
            parts.append(ids)
        cells.append(parts)
    page = {"page_size": [300, rows * 12 + 30], "words": words, "vector_candidates": []}
    state = {"tables": [_table(cells, {w["id"]: w for w in words})], "unresolved_ids": []}
    return page, state


def main() -> None:
    """Retain complete inputs, fake model scores, output and measurements locally."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--rows", type=int, default=129)
    options = parser.parse_args()
    if not 1 <= options.iterations <= 1000 or not 2 <= options.rows <= 129:
        raise ValueError("Offline work must use 1-1000 iterations and 2-129 rows")
    page, state = synthetic(options.rows)
    started, cpu_started = time.perf_counter(), time.process_time()
    for _ in range(options.iterations):
        menu, body = request(page, state, "offline-no-inference")
        answer = {b["id"]: {"join": 0.9, "split": 0.1, "unresolved": 0} for b in menu["boundaries"]}
        output, audit = apply(page, state, menu, answer)
    wall, cpu = time.perf_counter() - started, time.process_time() - cpu_started
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    observation = {
        "iterations": options.iterations,
        "rows": options.rows,
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "cpu_utilization_percent": 100 * cpu / wall,
        "peak_rss_kib": int(status["VmHWM"].split()[0]),
        "getrusage_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "getrusage_scope_caveat": "Pre-exec launcher RSS may persist; post-exec proc VmHWM is benchmark peak",
        "timing_scope": "100% of replay loop; excludes Python startup and module import",
        "measurement": "perf_counter/process_time and /proc/self/status VmHWM post-exec high-water RSS on Linux",
        "sampling_interval": "none; process CPU counter and OS VmHWM peak-RSS counter",
        "scope": "one Python process; no subprocesses",
        "concurrency": "serial, CPU-only",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packet_bytes": len(json.dumps(menu, ensure_ascii=False).encode()),
        "answer_bytes": len(json.dumps(answer).encode()),
        "expected_logical_rows": (options.rows + 1) // 2,
        "actual_logical_rows": output["tables"][0]["row_count"],
        "hosted_inference": False,
        "provider_charges": "not applicable",
    }
    destination = Path("bench/results/pdf-master-artifacts/p003-decisions/offline-replay.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "measurement": observation,
                "page": page,
                "state": state,
                "menu": menu,
                "request": body,
                "fake_answer": answer,
                "output": output,
                "audit": audit,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(observation, indent=2))
    print(f"Complete synthetic replay: {destination}")


if __name__ == "__main__":
    main()
