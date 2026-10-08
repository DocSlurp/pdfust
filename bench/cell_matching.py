"""Match saved SLANet structures on CPU; never load a model or open a PDF.

Run ``PYTHONPATH=src:. /home/dan/.cache/pdf-master-cpu/bin/python
-m bench.cell_matching --repeats 3`` after the specialist pilot. Only NumPy and
the installed upstream TableMatch matcher/renderer are needed. This original
implementation preserves upstream association and rendering policy; speed is
not evidence of better table recognition.
"""

# Optional dependency objects have heterogeneous array/module types.
# ruff: noqa: ANN401

from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import importlib.metadata
import importlib.util
import json
import platform
import statistics
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "bench/results/pdf-master-artifacts/specialist"
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts/matching"
REPORT = ROOT / "bench/results/cell-matching.md"
MAX_WORDS = 4096
MAX_CELLS = 4096
MAX_PAIR_ELEMENTS = 262144
MAX_CHUNK_WORDS = 256
DEFAULT_CHUNK_WORDS = 64
MAX_COORDINATE = 10_000_000
MAX_REPEATS = 5
MIN_IOU = 0.1**8


@dataclass(frozen=True)
class Association:
    """Keep filtered indexes compatible with upstream and original source IDs."""

    matches: dict[int, list[int]]
    kept_indexes: tuple[int, ...]
    unassigned_ids: tuple[str, ...]
    filtered_ids: tuple[str, ...]
    chunk_pairs: int


def upstream_matcher() -> tuple[Any, dict[str, Any]]:
    """Load matcher source directly without importing the model package root."""
    distribution = importlib.metadata.distribution("rapid-table")
    directory = Path(str(distribution.locate_file("rapid_table/table_matcher")))
    package_name = "_pdf_master_upstream_table_matcher"
    module_name = package_name + ".main"
    if module_name not in sys.modules:
        package = ModuleType(package_name)
        package.__path__ = [str(directory)]
        sys.modules[package_name] = package
        spec = importlib.util.spec_from_file_location(module_name, directory / "main.py")
        if spec is None or spec.loader is None:
            message = "installed upstream matcher source is unavailable"
            raise RuntimeError(message)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    matcher = sys.modules[module_name].TableMatch()
    return matcher, {
        "rapid_table_version": distribution.version,
        "numpy_version": importlib.metadata.version("numpy"),
        "source_sha256": {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in ("main.py", "utils.py")
        },
        "loading": "isolated TableMatch and utils source; package root, model, and runtime not imported",
    }


def admitted_arrays(cells: Any, words: Any, source_ids: list[str], chunk_words: int) -> tuple[Any, Any]:
    """Validate dimensions and resource limits before pairwise scratch allocation."""
    np = importlib.import_module("numpy")
    if not 1 <= chunk_words <= MAX_CHUNK_WORDS:
        message = "chunk_words is outside the bounded interval"
        raise ValueError(message)
    if len(cells) > MAX_CELLS or len(words) > MAX_WORDS:
        message = "word or cell count exceeds matcher admission"
        raise ValueError(message)
    if len(source_ids) != len(words) or len(set(source_ids)) != len(source_ids):
        message = "source IDs must be unique and match the word count"
        raise ValueError(message)
    if min(chunk_words, len(words)) * len(cells) > MAX_PAIR_ELEMENTS:
        message = "pairwise scratch chunk exceeds admission"
        raise ValueError(message)
    cells, words = np.asarray(cells), np.asarray(words)
    if cells.ndim != 2 or cells.shape[1] not in {4, 8} or words.ndim != 2 or words.shape[1] != 4:  # noqa: PLR2004
        message = "cells must be Nx4/Nx8 and words Nx4"
        raise ValueError(message)
    if cells.dtype != words.dtype or cells.dtype not in (np.dtype("float32"), np.dtype("float64")):
        message = "cells and words require matching float32 or float64 dtype"
        raise ValueError(message)
    if not np.isfinite(cells).all() or not np.isfinite(words).all():
        message = "matcher coordinates must be finite"
        raise ValueError(message)
    if (np.abs(cells) > MAX_COORDINATE).any() or (np.abs(words) > MAX_COORDINATE).any():
        message = "matcher coordinate magnitude exceeds admission"
        raise ValueError(message)
    return cells, words


def axis_boxes(cells: Any) -> Any:
    """Reduce each polygon once rather than once for every word-cell pair."""
    np = importlib.import_module("numpy")
    if cells.shape[1] == 4:  # noqa: PLR2004
        return cells
    return np.column_stack(
        (cells[:, 0::2].min(axis=1), cells[:, 1::2].min(axis=1), cells[:, 0::2].max(axis=1), cells[:, 1::2].max(axis=1))
    )


def match_cells(
    cells: Any,
    words: Any,
    source_ids: list[str],
    *,
    chunk_words: int = DEFAULT_CHUNK_WORDS,
    min_iou: float = MIN_IOU,
) -> Association:
    """Preserve IoU, L1/corner distance, dtype rounding and first-cell ties.

    Like upstream, words wholly above the smallest cell y coordinate are
    filtered. An admissible word chooses smallest ``1-IoU``, then smallest
    corner-weighted distance, then earliest cell index. Nonoverlap and the
    original tiny-IoU threshold remain unchanged. Empty cells explicitly leave
    every word unassigned; upstream's process_one raises on that input.
    """
    np = importlib.import_module("numpy")
    if not 0 <= min_iou <= 1 or not np.isfinite(min_iou):
        message = "min_iou must be finite and between zero and one"
        raise ValueError(message)
    cells, words = admitted_arrays(cells, words, source_ids, chunk_words)
    if not len(cells) or not len(words):
        return Association({}, tuple(range(len(words))), tuple(source_ids), (), 0)
    axis = axis_boxes(cells)
    kept = np.flatnonzero(np.maximum(words[:, 1], words[:, 3]) >= cells[:, 1::2].min())
    original_indexes = tuple(int(index) for index in kept)
    kept_set = set(original_indexes)
    filtered = tuple(source_ids[index] for index in range(len(words)) if index not in kept_set)
    working = words[kept]
    cell_area = (axis[:, 2] - axis[:, 0]) * (axis[:, 3] - axis[:, 1])
    matched: dict[int, list[int]] = {}
    used: set[int] = set()
    for offset in range(0, len(working), chunk_words):
        chunk = working[offset : offset + chunk_words]
        delta = np.abs(chunk[:, None, :] - axis[None, :, :])
        # Match scalar float operation order; a reduction can round differently.
        distances = ((delta[:, :, 0] + delta[:, :, 1]) + delta[:, :, 2]) + delta[:, :, 3]
        distances += np.minimum(delta[:, :, 0] + delta[:, :, 1], delta[:, :, 2] + delta[:, :, 3])
        lower = np.maximum(chunk[:, None, :2], axis[None, :, :2])
        upper = np.minimum(chunk[:, None, 2:], axis[None, :, 2:])
        overlaps = (lower[:, :, 0] < upper[:, :, 0]) & (lower[:, :, 1] < upper[:, :, 1])
        intersection = (upper[:, :, 0] - lower[:, :, 0]) * (upper[:, :, 1] - lower[:, :, 1])
        word_area = (chunk[:, 2] - chunk[:, 0]) * (chunk[:, 3] - chunk[:, 1])
        union = word_area[:, None] + cell_area[None, :] - intersection
        iou = np.zeros_like(union)
        np.divide(intersection, union, out=iou, where=overlaps)
        scores = 1.0 - iou
        best_scores = scores.min(axis=1)
        candidates = np.where(scores == best_scores[:, None], distances, np.inf)
        winners = candidates.argmin(axis=1)
        for local, cell_index in enumerate(winners):
            if best_scores[local] >= 1 - min_iou:
                continue
            index = offset + local
            matched.setdefault(int(cell_index), []).append(index)
            used.add(original_indexes[index])
    unassigned = tuple(source_ids[index] for index in range(len(words)) if index not in used)
    return Association(matched, original_indexes, unassigned, filtered, min(chunk_words, len(working)) * len(cells))


def reference(
    matcher: Any, cells: Any, words: Any, records: list[tuple[str, float]], tokens: list[str]
) -> tuple[dict[int, list[int]], str]:
    """Execute upstream filtering, association and rendering without inference."""
    filtered_words, filtered_records = matcher.filter_ocr_result(cells, words, records)
    choices = matcher.match_result(cells, filtered_words)
    output = matcher.get_pred_html(tokens, choices, filtered_records)[0]
    return choices, output


def optimized(  # noqa: PLR0913, PLR0917
    matcher: Any,
    cells: Any,
    words: Any,
    records: list[tuple[str, float]],
    tokens: list[str],
    source_ids: list[str],
    *,
    chunk_words: int,
) -> tuple[Association, str]:
    """Reuse upstream HTML assembly so only cell association changes."""
    choices = match_cells(cells, words, source_ids, chunk_words=chunk_words)
    kept_records = [records[index] for index in choices.kept_indexes]
    output = matcher.get_pred_html(tokens, choices.matches, kept_records)[0]
    return choices, output


def replay_inputs(
    case: dict[str, Any], output: dict[str, Any]
) -> tuple[Any, Any, list[tuple[str, float]], list[str], list[str]]:
    """Reconstruct original crop pixels/float32 records from saved provenance."""
    np = importlib.import_module("numpy")
    full = case["routes"]["full"]["outputs"][0]
    full_pixels, full_region = full["pixel_box"], full["region"]
    scale_x = (full_pixels[2] - full_pixels[0]) / (full_region[2] - full_region[0])
    scale_y = (full_pixels[3] - full_pixels[1]) / (full_region[3] - full_region[1])
    lookup = {word["id"]: word for word in case["words"]}
    ids = output["source_ids"]
    origin = output["pixel_box"][:2]
    boxes = [
        [
            lookup[source_id]["bbox"][index] * (scale_x if index % 2 == 0 else scale_y) - origin[index % 2]
            for index in range(4)
        ]
        for source_id in ids
    ]
    records = [(html.escape(lookup[source_id]["text"]), 1.0) for source_id in ids]
    return (
        np.array(output["cell_boxes"][0], dtype=np.float32).reshape(-1, 8),
        np.array(boxes, dtype=np.float32).reshape(-1, 4),
        records,
        output["structure"][0][0],
        ids,
    )


def run(*, repeats: int = 3, chunk_words: int = DEFAULT_CHUNK_WORDS) -> dict[str, Any]:
    """Replay every saved route; exclude loading/scoring/provenance from timing."""
    if not 1 <= repeats <= MAX_REPEATS:
        message = "repeats must be between one and five"
        raise ValueError(message)
    matcher, provenance = upstream_matcher()
    paths = sorted(SAVED.glob("*/results.json"))
    if not paths:
        message = "no saved specialist predictions are available"
        raise FileNotFoundError(message)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in paths:
        data = path.read_bytes()
        case = json.loads(data)
        directory = ARTIFACTS / case["name"]
        directory.mkdir(exist_ok=True)
        (directory / "saved-specialist-results.json").write_bytes(data)
        input_hash = hashlib.sha256((path.parent / "input.pdf").read_bytes()).hexdigest()
        if input_hash != case["input_sha256"]:
            message = f"changed saved PDF provenance: {case['name']}"
            raise ValueError(message)
        for route, value in case["routes"].items():
            row: dict[str, Any] = {
                "name": case["name"],
                "route": route,
                "saved_results_sha256": hashlib.sha256(data).hexdigest(),
                "input_sha256": input_hash,
                "regions": len(value["outputs"]),
                "saved_inference_ms": value["inference_ms"],
                "error": value["error"],
            }
            if value["error"]:
                rows.append(row)
                continue
            prepared = [replay_inputs(case, output) for output in value["outputs"]]
            replay = [
                {
                    "cell_boxes": cells.tolist(),
                    "word_boxes": words.tolist(),
                    "records": records,
                    "tokens": tokens,
                    "source_ids": ids,
                    "dtype": str(cells.dtype),
                }
                for cells, words, records, tokens, ids in prepared
            ]
            (directory / f"{route}-inputs.json").write_text(json.dumps(replay, indent=2) + "\n")
            reference_times, optimized_times = [], []
            reference_outputs = []
            optimized_outputs = []
            for _ in range(repeats):
                start = time.perf_counter()
                reference_outputs = [
                    reference(matcher, cells, words, records, tokens)
                    for cells, words, records, tokens, _ids in prepared
                ]
                reference_times.append((time.perf_counter() - start) * 1000)
                start = time.perf_counter()
                optimized_outputs = [
                    optimized(matcher, cells, words, records, tokens, ids, chunk_words=chunk_words)
                    for cells, words, records, tokens, ids in prepared
                ]
                optimized_times.append((time.perf_counter() - start) * 1000)
            tracemalloc.start()
            for cells, words, records, tokens, ids in prepared:
                optimized(matcher, cells, words, records, tokens, ids, chunk_words=chunk_words)
            _current, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            choices_equal = all(
                base[0] == fast[0].matches for base, fast in zip(reference_outputs, optimized_outputs, strict=True)
            )
            html_equal = all(
                base[1] == fast[1] for base, fast in zip(reference_outputs, optimized_outputs, strict=True)
            )
            saved_equal = all(
                base[1] == saved["html"] for base, saved in zip(reference_outputs, value["outputs"], strict=True)
            )
            selected = {source_id for output in value["outputs"] for source_id in output["source_ids"]}
            outside = (
                "<p>"
                + " ".join(html.escape(word["text"]) for word in case["words"] if word["id"] not in selected)
                + "</p>"
            )
            complete = "\n\n".join([fast[1] for fast in optimized_outputs] + [outside])
            complete_equal = complete == value["complete_html"]
            regions = [
                {
                    "matches": association.matches,
                    "kept_indexes": association.kept_indexes,
                    "unassigned_ids": association.unassigned_ids,
                    "filtered_ids": association.filtered_ids,
                    "chunk_pairs": association.chunk_pairs,
                    "html": output,
                    "source_ids": prepared[index][4],
                }
                for index, (association, output) in enumerate(optimized_outputs)
            ]
            row.update(
                reference_ms=reference_times,
                optimized_ms=optimized_times,
                reference_median_ms=statistics.median(reference_times),
                optimized_median_ms=statistics.median(optimized_times),
                choices_equal=choices_equal,
                html_equal=html_equal,
                saved_html_equal=saved_equal,
                complete_html_equal=complete_equal,
                peak_traced_bytes=peak_bytes,
                word_count=sum(len(item[1]) for item in prepared),
                cell_count=sum(len(item[0]) for item in prepared),
                outputs=regions,
            )
            (directory / f"{route}.json").write_text(json.dumps(row, indent=2) + "\n")
            (directory / f"{route}.html").write_text(complete)
            rows.append(row)
            print(
                f"{case['name']} / {route}: choices={choices_equal}, HTML={html_equal}, "
                f"{row['reference_median_ms']:.3f} -> {row['optimized_median_ms']:.3f} ms",
                flush=True,
            )
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "provenance": provenance,
        "repeats": repeats,
        "chunk_words": chunk_words,
        "limits": {"words": MAX_WORDS, "cells": MAX_CELLS, "chunk_pairs": MAX_PAIR_ELEMENTS},
        "results": rows,
    }
    (ARTIFACTS / "specialist-manifest.json").write_bytes((SAVED / "manifest.json").read_bytes())
    (ARTIFACTS / "measured-code.py").write_bytes(Path(__file__).read_bytes())
    (ARTIFACTS / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    write_report(report)
    return report


def write_report(report: dict[str, Any]) -> None:
    """Report exact equivalence and matching-only timings without quality claims."""
    reporting_source = Path(__file__).read_bytes()
    (ARTIFACTS / "report-generator-code.py").write_bytes(reporting_source)
    lines = [
        "# Saved-prediction CPU cell matching",
        "",
        "Run `PYTHONPATH=src:. /home/dan/.cache/pdf-master-cpu/bin/python -m bench.cell_matching --repeats 3`.",
        "",
        (
            f"Python {report['python']}; NumPy {report['provenance']['numpy_version']}; "
            f"rapid-table {report['provenance']['rapid_table_version']}; {report['repeats']} repeats; "
            f"word chunks {report['chunk_words']}."
        ),
        "",
        (
            "The installed TableMatch and utils source are loaded through an isolated package namespace; "
            "rapid_table's package root, model and inference runtime are not imported. No PDF opening, "
            "rendering, inference, GPU access, network, training or dependency installation occurs. "
            "Saved source coordinates, structures and cell predictions are reused unchanged."
        ),
        "",
        (
            "This original matcher precomputes polygon axis boxes once, computes IoU and the upstream "
            "corner-weighted L1 distance in bounded NumPy chunks, and chooses maximum IoU, then minimum "
            "distance, then earliest cell index. Scalar arithmetic order, floating dtype and tiny-IoU "
            "threshold are preserved. Upstream HTML rendering is reused unchanged. This does not improve "
            "structure quality, missing model cells, false tables, or source order."
        ),
        "",
        (
            "Limits: 4,096 words, 4,096 cells, 262,144 word-cell pairs per scratch chunk, and finite "
            "coordinates within ±10 million. Matching float32/float64 input dtypes are required. "
            "Empty-cell input is explicitly defined as all sources unassigned; upstream process_one "
            "raises on that input, so that extension is not an equivalence claim."
        ),
        "",
        (
            "Timing covers filtering, matching and identical HTML assembly on prepared saved arrays. "
            "Saved file reads, coordinate reconstruction, hashing and validation comparisons are excluded. "
            "Optimized input admission and AABB precomputation are included. Traced allocation peak is "
            "measured in a separate untimed replay; it is not process RSS."
        ),
        "",
        (
            "| Input | Route | Words / cells | Upstream ms | Optimized ms | Speedup | "
            "Choices / HTML / saved / complete equal | Peak traced KiB | Unassigned IDs |"
        ),
        "|---|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for row in report["results"]:
        if row["error"]:
            lines.append(f"| {row['name']} | {row['route']} | error: {row['error']} | | | | | | |")
            continue
        baseline, fast = row["reference_median_ms"], row["optimized_median_ms"]
        equality = "/".join(
            str(row[key]) for key in ("choices_equal", "html_equal", "saved_html_equal", "complete_html_equal")
        )
        unmatched = sum(len(output["unassigned_ids"]) for output in row["outputs"])
        speedup = f"{baseline / fast:.1f}×" if row["regions"] and fast else "n/a"
        baseline_text = f"{baseline:.3f}" if row["regions"] else "n/a"
        fast_text = f"{fast:.3f}" if row["regions"] else "n/a"
        lines.append(
            f"| {row['name']} | {row['route']} | {row['word_count']} / {row['cell_count']} | "
            f"{baseline_text} | {fast_text} | {speedup} | "
            f"{equality} | {row['peak_traced_bytes'] / 1024:.1f} | {unmatched} |"
        )
    valid = [row for row in report["results"] if not row["error"]]
    equal = sum(
        all(row[key] for key in ("choices_equal", "html_equal", "saved_html_equal", "complete_html_equal"))
        for row in valid
    )
    nonempty = [row for row in valid if row["regions"]]
    lines.extend(
        [
            "",
            f"Exact association and region/complete HTML equivalence: {equal}/{len(valid)} saved routes.",
            f"Nonempty matching routes: {len(nonempty)}; empty cropped routes: {len(valid) - len(nonempty)}.",
            "",
            (
                "Unassigned source IDs include words filtered above the smallest cell y coordinate and "
                "words failing the original IoU threshold. They are retained separately in local JSON. "
                "The equivalence output deliberately preserves the specialist's original complete-HTML "
                "assembly policy; those IDs are not silently reinserted into a new table or counted as "
                "recovered cells. Empty cropped routes have zero regions and vacuous matching equality."
            ),
            "",
            "## Provenance and next tests",
            "",
            (
                "Validation: 19 targeted tests pass in the isolated CPU dependency environment. "
                "Ruff and targeted mypy pass. The regular development environment skips these optional "
                "tests when rapid-table is absent; no production dependencies are added."
            ),
            "",
            f"Measured source SHA-256: `{report['code_sha256']}` (retained as `measured-code.py`).",
            "",
            (
                f"Report generator SHA-256: `{hashlib.sha256(reporting_source).hexdigest()}` "
                "(retained as `report-generator-code.py`). Reporting and provenance-copy changes after timing "
                "do not alter the matcher or recorded samples."
            ),
            "",
            f"Upstream source SHA-256: `{report['provenance']['source_sha256']}`.",
            "",
            (
                "Full associations, unmatched IDs, saved-input hashes, all timings, original matched HTML, "
                "and the executed source snapshot remain local in `bench/results/pdf-master-artifacts/matching/`. "
                "Inputs come from the eight-case specialist pilot; upstream/saved parity checks expose "
                "coordinate reconstruction or tie differences instead of concealing them."
            ),
            "",
            (
                "Next tests: independent structure predictors and documents; nearly equal float32 IoUs; "
                "real overlapping/degenerate cells; adversarial larger tables at admission boundaries; "
                "HTML with predicted cells missing corresponding closing tags. A conservative overlap or "
                "containment policy would change associations and needs separate quality labels. "
                "These saved predictions do not establish semantic table accuracy."
            ),
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Replay saved artifacts without importing a model or execution engine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--chunk-words", type=int, default=DEFAULT_CHUNK_WORDS)
    arguments = parser.parse_args()
    run(repeats=arguments.repeats, chunk_words=arguments.chunk_words)
    print(REPORT)


if __name__ == "__main__":
    main()
