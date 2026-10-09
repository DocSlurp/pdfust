"""Reproduce CPU cost and conservation of the private glyph snapshot.

Run normal extraction and snapshot-plus-text on the same installed extension.
Original104 requires an explicit DEV manifest; no artifact directories are searched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import shutil
import statistics
import subprocess
import sys
import time
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

import pylopdf
from bench.lowlevel_cases import cases
from bench.silver import guard_path, load_manifest, verify_input, write_json
from pylopdf import pylopdf_core

MODES = ("text", "snapshot_text")
ORIGINAL_COUNT = 104
DEFAULT_REPEATS = 5


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_inputs(original_manifest: Path | None = None) -> dict[str, list[tuple[str, bytes]]]:
    """Load authored controls and optionally the explicitly named original DEV set."""
    cohorts = {"cohort72": [(row["id"], row["pdf_bytes"]) for row in cases()]}
    if original_manifest is not None:
        path = guard_path(original_manifest)
        if path.name != "manifest.json":
            message = "Supply the explicit original104 manifest.json file"
            raise ValueError(message)
        manifest = load_manifest(path.parent)
        if len(manifest["cases"]) != ORIGINAL_COUNT:
            message = "Original104 opt-in requires exactly 104 explicit DEV records"
            raise ValueError(message)
        cohorts["original104"] = [(row["id"], verify_input(path.parent, row).read_bytes()) for row in manifest["cases"]]
    return cohorts


def extract(data: bytes, mode: str) -> dict[str, Any]:
    """Perform complete extraction and verify admitted mapped-character multiplicity."""
    if mode not in MODES:
        message = "Unknown CPU measurement mode"
        raise ValueError(message)
    mapped: Counter[str] = Counter()
    glyph_count = skipped = 0
    with pylopdf.Document(stream=data) as document:
        pages = len(document)
        if mode == "snapshot_text":
            document._ensure_fallback_fonts()  # noqa: SLF001 - match public locale-provider initialization.
            for page in range(pages):
                _, _, rows, unmapped = document._doc.extract_glyph_snapshot(page + 1)  # noqa: SLF001
                glyph_count += len(rows)
                skipped += unmapped
                mapped.update(char for row in rows for char in row[1] if not char.isspace())
                document._emit_warnings()  # noqa: SLF001 - private hook does not deliver Python warnings.
        text = document.get_text()
    encoded = text.encode()
    assembled = Counter(char for char in text if not char.isspace()) if mode == "snapshot_text" else Counter()
    return {
        "pages": pages,
        "text_sha256": _hash(encoded),
        "output_bytes": len(encoded),
        "mapped_glyphs": glyph_count if mode == "snapshot_text" else None,
        "skipped_no_unicode": skipped if mode == "snapshot_text" else None,
        "character_conservation": mapped == assembled if mode == "snapshot_text" else None,
        "mapped_only": dict(mapped - assembled) if mode == "snapshot_text" else None,
        "text_only": dict(assembled - mapped) if mode == "snapshot_text" else None,
    }


def _peak_rss() -> int:
    path = Path("/proc/self/status")
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1]) * 1024
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def _environment() -> dict[str, Any]:
    source = Path(__file__).resolve()
    core = Path(pylopdf_core.__file__).resolve()
    package = Path(pylopdf.__file__).resolve()
    revision = subprocess.run(  # noqa: S603 - fixed read-only git arguments; executable resolved locally.
        [shutil.which("git") or "/usr/bin/git", "rev-parse", "HEAD"],
        cwd=source.parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        "load_average": list(os.getloadavg()) if hasattr(os, "getloadavg") else None,
        "rayon_num_threads": os.environ.get("RAYON_NUM_THREADS"),
        "library_version": pylopdf.__version__,
        "benchmark_repository_revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "extension_build_revision": "unmeasured; extension file hash is authoritative",
        "files": {str(path): _hash(path.read_bytes()) for path in (source, package, core)},
        "pid": os.getpid(),
        "concurrency": "one Python process; sequential documents; no GPU work",
    }


def benchmark(  # noqa: C901 - explicit warmup, paired measurements and correctness gates.
    workloads: dict[str, list[tuple[str, bytes]]], *, repeats: int = DEFAULT_REPEATS, inner_repeats: int = 1
) -> dict[str, Any]:
    """Alternate balanced same-build arms with fresh Documents and retained failures."""
    if type(repeats) is not int or repeats < 1 or type(inner_repeats) is not int or inner_repeats < 1:
        message = "Both repetition counts must be positive integers"
        raise ValueError(message)
    identities: dict[str, list[dict[str, Any]]] = {
        dataset: [{"id": ident, "pdf_sha256": _hash(data), "input_bytes": len(data)} for ident, data in records]
        for dataset, records in workloads.items()
    }
    for identity_records in identities.values():
        if not identity_records or len({row["id"] for row in identity_records}) != len(identity_records):
            message = "Each workload requires nonempty, unique source identities"
            raise ValueError(message)
    runs: list[dict[str, Any]] = []
    expected_hashes: dict[tuple[str, str], str] = {}
    warmup = []
    # Exercise both paths over every input before balanced measurements. Every
    # measured operation still opens a fresh Document; process-level state is warm.
    with warnings.catch_warnings(record=True):
        for mode in MODES:
            started, cpu = time.perf_counter(), time.process_time()
            for dataset, records in workloads.items():
                for ident, data in records:
                    output = extract(data, mode)
                    expected_hashes.setdefault((dataset, ident), output["text_sha256"])
            warmup.append(
                {"mode": mode, "wall_seconds": time.perf_counter() - started, "cpu_seconds": time.process_time() - cpu}
            )
    for block in range(repeats):
        order = MODES if block % 2 == 0 else tuple(reversed(MODES))
        for mode in order:
            for dataset, records in workloads.items():
                documents: list[dict[str, Any]] = []
                started, cpu = time.perf_counter(), time.process_time()
                before = resource.getrusage(resource.RUSAGE_SELF)
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter("always")
                    for repeat in range(inner_repeats):
                        for ident, data in records:
                            doc_started, doc_cpu = time.perf_counter(), time.process_time()
                            output = extract(data, mode)
                            key = (dataset, ident)
                            baseline = expected_hashes.setdefault(key, output["text_sha256"])
                            documents.append(
                                {
                                    "id": ident,
                                    "inner_repeat": repeat,
                                    **output,
                                    "text_matches_all_prior_runs": baseline == output["text_sha256"],
                                    "wall_seconds": time.perf_counter() - doc_started,
                                    "cpu_seconds": time.process_time() - doc_cpu,
                                }
                            )
                after = resource.getrusage(resource.RUSAGE_SELF)
                runs.append(
                    {
                        "block": block,
                        "mode": mode,
                        "dataset": dataset,
                        "order": list(order),
                        "inner_repeats": inner_repeats,
                        "wall_seconds": time.perf_counter() - started,
                        "cpu_seconds": time.process_time() - cpu,
                        "user_cpu_seconds": after.ru_utime - before.ru_utime,
                        "system_cpu_seconds": after.ru_stime - before.ru_stime,
                        "process_lifetime_peak_rss_bytes": _peak_rss(),
                        "documents": documents,
                        "warnings": dict(Counter(str(warning.message) for warning in captured)),
                    }
                )
    matches = all(row["text_matches_all_prior_runs"] for run in runs for row in run["documents"])
    conservation = all(row["character_conservation"] is not False for run in runs for row in run["documents"])
    summaries = {}
    for dataset in workloads:
        normal = [run for run in runs if run["dataset"] == dataset and run["mode"] == "text"]
        snapshot = [run for run in runs if run["dataset"] == dataset and run["mode"] == "snapshot_text"]
        ratios = [
            candidate["wall_seconds"] / baseline["wall_seconds"]
            for baseline, candidate in zip(normal, snapshot, strict=True)
        ]
        summaries[dataset] = {
            "median_text_wall_seconds_per_corpus": statistics.median(run["wall_seconds"] for run in normal)
            / inner_repeats,
            "median_snapshot_text_wall_seconds_per_corpus": statistics.median(run["wall_seconds"] for run in snapshot)
            / inner_repeats,
            "median_text_cpu_seconds_per_corpus": statistics.median(run["cpu_seconds"] for run in normal)
            / inner_repeats,
            "median_snapshot_text_cpu_seconds_per_corpus": statistics.median(run["cpu_seconds"] for run in snapshot)
            / inner_repeats,
            "paired_wall_ratios": ratios,
            "median_paired_wall_ratio": statistics.median(ratios),
            "paired_repetitions_same_process": repeats,
        }
    return {
        "schema": 1,
        "environment": _environment(),
        "inputs": identities,
        "runs": runs,
        "summaries": summaries,
        "warmup": warmup,
        "repeats": repeats,
        "inner_repeats": inner_repeats,
        "all_text_hashes_match": matches,
        "mapped_nonwhitespace_characters_conserved": conservation,
        "measurement": (
            "perf_counter/process_time and getrusage(RUSAGE_SELF) user/system deltas; all process threads; "
            "inputs preloaded; one process shared by all arms; both modes warm all inputs before measurement; "
            "fresh Documents in timed runs; "
            "OS/file caches not dropped; no sampling; VmHWM or kernel lifetime peak RSS is cumulative "
            "across arms and cannot establish per-arm memory differences; startup/input loading excluded; "
            "snapshot arm includes character-conservation oracle and evidence materialization"
        ),
        "limits": (
            "same installed build only; not a cross-revision comparison; character multiplicity ignores whitespace "
            "and does not establish reading order, semantics, or unmapped-glyph recovery"
        ),
    }


def main() -> None:
    """Print and retain a reproducible CPU-only same-build comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-manifest", type=Path)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--inner-repeats", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = guard_path(args.output)
    os.environ.setdefault("RAYON_NUM_THREADS", "1")
    result = benchmark(load_inputs(args.original_manifest), repeats=args.repeats, inner_repeats=args.inner_repeats)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    print(json.dumps(result, indent=2))
    if not result["all_text_hashes_match"] or not result["mapped_nonwhitespace_characters_conserved"]:
        message = "Output hash or character conservation gate failed; observations retained"
        raise SystemExit(message)


if __name__ == "__main__":
    main()
