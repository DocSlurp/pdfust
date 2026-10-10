"""Read-only P003 accounting serialization measurement on an explicit snapshot."""

from __future__ import annotations

import argparse
import json
import resource
import statistics
import time
from pathlib import Path

from bench.silver import guard_path, sha, write_json

MAX_REPEATS = 20


def measure(snapshot: Path, output: Path, repeats: int = 5) -> dict[str, object]:
    """Compare exact JSON round trips without loading credentials or changing a ledger."""
    snapshot, output = guard_path(snapshot), guard_path(output)
    if output.exists() or repeats < 1 or repeats > MAX_REPEATS:
        msg = "Use a fresh result path and between one and twenty repetitions"
        raise ValueError(msg)
    raw = snapshot.read_bytes()
    value = json.loads(raw)
    cpu_start, wall_start = time.process_time(), time.perf_counter()
    treatments: dict[str, object] = {}
    for name, kwargs in (
        ("current_indent2", {"ensure_ascii": False, "indent": 2}),
        ("compact", {"ensure_ascii": False, "separators": (",", ":")}),
    ):
        encode_wall, decode_wall, encode_cpu, decode_cpu = [], [], [], []
        for _ in range(repeats):
            wall, cpu = time.perf_counter(), time.process_time()
            encoded = (json.dumps(value, **kwargs) + "\n").encode()
            encode_wall.append(time.perf_counter() - wall)
            encode_cpu.append(time.process_time() - cpu)
            wall, cpu = time.perf_counter(), time.process_time()
            decoded = json.loads(encoded)
            decode_wall.append(time.perf_counter() - wall)
            decode_cpu.append(time.process_time() - cpu)
            if decoded != value:
                msg = "Serialization changed accounting values"
                raise ValueError(msg)
        treatments[name] = {
            "bytes": len(encoded), "json_sha256": sha(encoded), "exact_roundtrip": True,
            "encode_wall_seconds": encode_wall, "decode_wall_seconds": decode_wall,
            "encode_cpu_seconds": encode_cpu, "decode_cpu_seconds": decode_cpu,
            "median_encode_wall_seconds": statistics.median(encode_wall),
            "median_decode_wall_seconds": statistics.median(decode_wall),
            "median_encode_cpu_seconds": statistics.median(encode_cpu),
            "median_decode_cpu_seconds": statistics.median(decode_cpu),
        }
    report: dict[str, object] = {
        "snapshot_sha256": sha(raw), "snapshot_bytes": len(raw), "requests": len(value["requests"]),
        "repeats": repeats, "treatments": treatments,
        "wall_seconds": time.perf_counter() - wall_start,
        "cpu_seconds": time.process_time() - cpu_start,
        "process_lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "Single CPU process; serialization/parsing only; no disk-write/lock/network measurement",
        "caveat": (
            "Contended local timing; no live ledger mutation or throughput claim; full objects retained in memory"
        ),
        "source_sha256": sha(Path(__file__).read_bytes()),
    }
    write_json(output, report)
    return report


def main() -> None:
    """Accept explicit root-owned immutable snapshot and new output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.snapshot, args.output)))


if __name__ == "__main__":
    main()
