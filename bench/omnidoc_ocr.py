"""Bounded CPU native-OCR admission probe on frozen external DEV page images."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path("/home/dan/code/oss/pylopdf")
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts/omnidoc-dev"
OUTPUT = ARTIFACTS / "ocr-admission"
MODELS = ROOT / "models/pylopdf-ocr-models/src/pylopdf_ocr_models"
SELECTED = (1, 2, 5, 9)
SCALES = (640, 1200)
RSS_LIMIT = 1024**3
TIME_LIMIT = 30.0


def normalized_counter(text: str, *, nfkc: bool) -> Counter[str]:
    """Count non-whitespace characters without claiming reading-order accuracy."""
    value = unicodedata.normalize("NFKC", text) if nfkc else text
    return Counter(character for character in value if not character.isspace())


def score_blocks(annotation: dict[str, Any], words: list[dict[str, Any]]) -> dict[str, Any]:
    """Use annotations only after OCR, with disjoint spatial assignments."""
    blocks = [
        block
        for block in annotation["layout_dets"]
        if not block.get("ignore", False) and block["category_type"] == "text_block" and block.get("text")
    ]
    assignments: list[list[str]] = [[] for _ in blocks]
    for word in words:
        x0, y0, x1, y1 = word["source_bbox"]
        center_x, center_y = (x0 + x1) / 2, (y0 + y1) / 2
        candidates = []
        for index, block in enumerate(blocks):
            polygon = block["poly"]
            bx0, bx1 = min(polygon[::2]), max(polygon[::2])
            by0, by1 = min(polygon[1::2]), max(polygon[1::2])
            if bx0 <= center_x <= bx1 and by0 <= center_y <= by1:
                candidates.append(((bx1 - bx0) * (by1 - by0), index))
        if candidates:
            assignments[min(candidates)[1]].append(word["text"])
    totals = {}
    for normalized in (False, True):
        reference_characters = observed_characters = shared = plain_blocks = 0
        for block, actual in zip(blocks, assignments, strict=True):
            expected = block["text"]
            if "$" in expected or "\\" in expected:
                continue
            plain_blocks += 1
            reference = normalized_counter(expected, nfkc=normalized)
            observed = normalized_counter(" ".join(actual), nfkc=normalized)
            reference_characters += reference.total()
            observed_characters += observed.total()
            shared += (reference & observed).total()
        totals["nfkc" if normalized else "strict"] = {
            "plain_text_blocks": plain_blocks,
            "reference_characters": reference_characters,
            "observed_characters_in_plain_blocks": observed_characters,
            "shared_character_count": shared,
            "character_bag_recall": shared / reference_characters if reference_characters else None,
            "character_bag_precision": shared / observed_characters if observed_characters else None,
        }
    return {
        "text_blocks": len(blocks),
        "spatially_covered_text_blocks": sum(bool(x) for x in assignments),
        "unassigned_words": len(words) - sum(len(x) for x in assignments),
        "excluded_formula_blocks": sum(
            not b.get("ignore", False) and b["category_type"] == "equation_isolated" for b in annotation["layout_dets"]
        ),
        "excluded_table_blocks": sum(
            not b.get("ignore", False) and b["category_type"] == "table" for b in annotation["layout_dets"]
        ),
        "character_bags": totals,
        "metric_limit": "Spatial bbox-center coverage and per-block character bags, not CER or reading order",
    }


def worker(sample: int, edge: int, output: Path) -> None:
    """Observe pixels only; never read annotations or scoring labels."""
    import pylopdf  # noqa: PLC0415 - CPU extension used only by isolated workers

    registry = json.loads((Path(__file__).parent / "omnidoc-dev/registry.json").read_text())
    row = registry["rows"][sample - 1]
    path = ARTIFACTS / "images" / row["id"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != row["image_sha256"]:
        message = "Source image identity differs"
        raise ValueError(message)
    model_paths = [MODELS / name for name in ("PP-OCRv6_det_small.rten", "PP-OCRv6_rec_small.rten", "ppocrv6_dict.txt")]
    before = resource.getrusage(resource.RUSAGE_SELF)
    init_start = time.perf_counter()
    engine = pylopdf.OcrEngine(*model_paths, threads=2, max_concurrent=1)
    init_after = resource.getrusage(resource.RUSAGE_SELF)
    initialization = {
        "wall_seconds": time.perf_counter() - init_start,
        "cpu_seconds": init_after.ru_utime + init_after.ru_stime - before.ru_utime - before.ru_stime,
        "peak_rss_kib": init_after.ru_maxrss,
    }
    prep_start = time.perf_counter()
    with pylopdf.Document() as document:
        page = document.new_page(width=row["width"] * 0.36, height=row["height"] * 0.36)
        page.insert_image((0, 0, page.rect.width, page.rect.height), filename=path)
        preparation_seconds = time.perf_counter() - prep_start
        dpi = 200 * edge / max(row["width"], row["height"])
        started = time.perf_counter()
        before = resource.getrusage(resource.RUSAGE_SELF)
        temporary_phase = output / "phase.tmp"
        temporary_phase.write_text(json.dumps({"phase": "ocr", "started_monotonic": started}))
        temporary_phase.replace(output / "phase.json")
        observed = page.get_text_ocr(dpi=dpi, engine=engine)
        after = resource.getrusage(resource.RUSAGE_SELF)
        words: list[dict[str, Any]] = [
            {
                "source_id": f"ocr-s{sample}-e{edge}-w{index}",
                "source_bbox": [x / 0.36 for x in word["bbox"]],
                "display_bbox": list(word["bbox"]),
                "text": word["text"],
                "confidence": word["confidence"],
            }
            for index, word in enumerate(observed)
        ]
        result = {
            "sample": sample,
            "edge": edge,
            "id": row["id"],
            "input_kind": "synthetic_image_carrier_pdf",
            "image_sha256": row["image_sha256"],
            "ocr_wall_seconds": time.perf_counter() - started,
            "ocr_cpu_user_seconds": after.ru_utime - before.ru_utime,
            "ocr_cpu_system_seconds": after.ru_stime - before.ru_stime,
            "peak_rss_kib": after.ru_maxrss,
            "initialization": initialization,
            "carrier_preparation_wall_seconds": preparation_seconds,
            "dpi": dpi,
            "words": words,
            "characters": sum(len(word["text"]) for word in words),
            "threads": 2,
            "max_concurrent": 1,
            "tile_size": 1408,
            "overlap": 192,
            "min_confidence": 0.5,
            "pylopdf_version": pylopdf.__version__,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "models": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in model_paths},
        }
        (output / "observed.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))


def run(output: Path) -> None:
    """Enforce per-call wall and worker-RSS gates from a CPU-only parent."""
    output.mkdir(parents=True, exist_ok=True)
    for sample in SELECTED:
        for edge in SCALES:
            directory = output / f"s{sample}-e{edge}"
            directory.mkdir(exist_ok=True)
            phase = directory / "phase.json"
            phase.unlink(missing_ok=True)
            start = time.perf_counter()
            samples = []
            status = "complete"
            with (directory / "worker.log").open("w") as log:
                process = subprocess.Popen(  # noqa: S603 - fixed local worker module
                    [
                        sys.executable,
                        "-m",
                        "bench.omnidoc_ocr",
                        "--worker",
                        "--sample",
                        str(sample),
                        "--edge",
                        str(edge),
                        "--output",
                        str(directory),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                while process.poll() is None:
                    try:
                        rss = (
                            int(
                                next(
                                    line.split()[1]
                                    for line in Path(f"/proc/{process.pid}/status").read_text().splitlines()
                                    if line.startswith("VmRSS:")
                                )
                            )
                            * 1024
                        )
                    except (OSError, StopIteration):
                        rss = None
                    samples.append({"elapsed_seconds": time.perf_counter() - start, "rss_bytes": rss})
                    call_start = json.loads(phase.read_text())["started_monotonic"] if phase.exists() else start
                    if (rss is not None and rss > RSS_LIMIT) or time.perf_counter() - call_start > TIME_LIMIT:
                        status = "rss_limit" if rss is not None and rss > RSS_LIMIT else "time_limit"
                        process.kill()
                        process.wait()
                        break
                    time.sleep(0.05)
                if process.returncode != 0 and status == "complete":
                    status = "worker_error"
            telemetry = {
                "status": status,
                "whole_worker_wall_seconds": time.perf_counter() - start,
                "sampling_interval_seconds": 0.05,
                "scope": "single worker PID including threads; no children",
                "rss_limit_bytes": RSS_LIMIT,
                "ocr_time_limit_seconds": TIME_LIMIT,
                "samples": samples,
            }
            (directory / "telemetry.json").write_text(json.dumps(telemetry, indent=2))
            print(f"sample={sample} edge={edge}: {status}", flush=True)
            if status != "complete":
                return


def summarize(output: Path) -> None:
    """Load reference annotations only after complete OCR artifacts are frozen."""
    rows = []
    for sample in SELECTED:
        for edge in SCALES:
            directory = output / f"s{sample}-e{edge}"
            if not (directory / "telemetry.json").exists():
                continue
            telemetry = json.loads((directory / "telemetry.json").read_text())
            row = {"sample": sample, "edge": edge, "status": telemetry["status"]}
            if row["status"] == "complete":
                observed_path = directory / "observed.json"
                observed = json.loads(observed_path.read_text())
                annotation = json.loads((ARTIFACTS / "annotations" / (observed["id"] + ".json")).read_text())
                row.update(
                    {
                        "observed_sha256": hashlib.sha256(observed_path.read_bytes()).hexdigest(),
                        "ocr_seconds": observed["ocr_wall_seconds"],
                        "words": len(observed["words"]),
                        "characters": observed["characters"],
                        "peak_rss_mib": observed["peak_rss_kib"] / 1024,
                        "score": score_blocks(annotation, observed["words"]),
                        "initialization": observed["initialization"],
                        "cpu_seconds": observed["ocr_cpu_user_seconds"] + observed["ocr_cpu_system_seconds"],
                    }
                )
            rows.append(row)
    (output / "scores.json").write_text(json.dumps(rows, indent=2))
    lines = [
        "# External DEV native OCR admission probe",
        "",
        (
            "Four frozen OmniDocBench images (#1 English exam, #2 Chinese academic paper, #5 Chinese report, "
            "#9 English notes), metadata-selected before OCR. CPU only, existing PP-OCRv6 small RTen weights, "
            "two threads and one admitted call. These are image-carrier PDFs, not original native PDFs. "
            "No GPU, hosted API, training, or provider spending occurred."
        ),
        "",
        (
            "| Sample | Max edge | Status | OCR wall / CPU | Lifetime RSS | OCR words / chars | "
            "Text block coverage | Scored plain blocks/chars | Strict bag recall | NFKC bag recall / precision |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        if row["status"] != "complete":
            lines.append(f"| {row['sample']} | {row['edge']} | {row['status']} | — | — | — | — | — | — |")
            continue
        score = row["score"]
        strict = score["character_bags"]["strict"]["character_bag_recall"]
        normalized = score["character_bags"]["nfkc"]

        def display(value: float | None) -> str:
            return "n/a" if value is None else f"{value:.3f}"

        lines.append(
            f"| {row['sample']} | {row['edge']} | complete | {row['ocr_seconds']:.3f}s / "
            f"{row['cpu_seconds']:.3f}s | {row['peak_rss_mib']:.1f} MiB | {row['words']} / {row['characters']} | "
            f"{score['spatially_covered_text_blocks']}/{score['text_blocks']} | "
            f"{normalized['plain_text_blocks']}/{normalized['reference_characters']} | {display(strict)} | "
            f"{display(normalized['character_bag_recall'])} / {display(normalized['character_bag_precision'])} |"
        )
    lines.extend(
        [
            "",
            (
                "Scoring uses nonignored text_block annotations only. Each OCR word center is assigned to "
                "one containing annotation bbox (smallest-area tie choice). Formula and table blocks are separate "
                "excluded categories; text blocks containing LaTeX markers are also excluded from character-bag "
                "metrics. Coverage counts a block with at least one OCR observation and is not recognition accuracy. "
                "Character bags count matching nonwhitespace characters per block with strict or NFKC forms. "
                "They ignore order and are not CER, word accuracy, mathematical fidelity, or complete reconstruction."
            ),
            "",
            (
                "Each observed word retains a unique run-local source ID and source-image/display bbox. These "
                "records permit spatial candidate experiments but do not establish row membership or header ownership. "
                "OCR items can contain full lines, so their boxes are not guaranteed word/cell geometry. "
                "No reference answer enters OCR or image cropping; full pages and fixed scales are used. "
                "Annotations are loaded only by the scorer after observed outputs are persisted."
            ),
            "",
            (
                "Timing uses perf_counter and resource.getrusage SELF user/system CPU; RSS is process-lifetime "
                "ru_maxrss. The parent samples one worker PID at a 0.05s target interval plus query overhead, "
                "kills on observed RSS above 1 GiB or OCR wall above 30s, and aborts remaining calls after a refusal. "
                "There are no worker children; threads are included. Engine initialization is separated per call "
                "in retained artifacts, and image insertion precedes the OCR timer. Rendering and recognition are "
                "both included in OCR time. Gate detection can overshoot by one sampling interval; this is a watchdog, "
                "not an OS memory reservation. Initialization and pre-OCR preparation also have a 30s watchdog."
            ),
            "",
            (
                "Reproduce with `.venv/bin/python -m bench.omnidoc_ocr --run --report` in the worktree. "
                "Complete words, bboxes, initialization timings, model/image hashes, CPU measurements, and telemetry "
                "remain in ignored `omnidoc-dev/ocr-admission/`. "
                "Public benchmark pretraining contamination is unknown; "
                "these are DEV observations. OmniDocBench retains its noncommercial research restriction."
            ),
            "",
        ]
    )
    lines.extend(
        [
            "",
            (
                "The 1200-pixel arm supplies usable positioned printed-text evidence on the three populated pages "
                "within 6.81s and 289 MiB each, but 640 pixels misses both Chinese-report prose blocks. "
                "The smaller scale is therefore not admitted as an interchangeable input for row assembly. "
                "At 1200 pixels, normalized character-bag recall reaches 0.978/1.000/1.000 for the scored "
                "English-exam/Chinese-academic/Chinese-report blocks. "
                "These are limited content-retention observations, "
                "not structural correctness or calibrated model confidence. The metadata-selected note page is "
                "essentially blank ruled paper with a small header; it has no text_block annotation and provides no "
                "handwriting or unsupported-language accuracy estimate. English and simplified-Chinese printed text "
                "both yield observations here; no other script capability is inferred."
            ),
            "",
        ]
    )
    for row in rows:
        if row["status"] == "complete":
            init = row["initialization"]
            lines.extend(
                [
                    (
                        f"Sample {row['sample']} edge {row['edge']} engine initialization: "
                        f"{init['wall_seconds']:.3f}s wall / {init['cpu_seconds']:.3f}s CPU; "
                        f"{init['peak_rss_kib'] / 1024:.1f} MiB lifetime RSS."
                    ),
                    "",
                ]
            )
    (Path(__file__).parent / "results/omnidoc-ocr.md").write_text("\n".join(lines))


def main() -> None:
    """Execute guarded pixel observation and a separate post-output scorer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--sample", type=int, choices=SELECTED)
    parser.add_argument("--edge", type=int, choices=SCALES)
    args = parser.parse_args()
    if args.worker:
        worker(args.sample, args.edge, args.output)
    if args.run:
        run(args.output)
    if args.report:
        summarize(args.output)


if __name__ == "__main__":
    main()
