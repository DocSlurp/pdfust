"""Frozen raster OCR to physical/rolling assembly on the 28-page DEV companion."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.omnidoc_ocr import MODELS, RSS_LIMIT, TIME_LIMIT
from bench.rolling_rows import assemble
from bench.silver import guard_path

ROOT = Path("/home/dan/code/oss/pylopdf")
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts"
CORPUS = ARTIFACTS / "borderless-dev-v1/66c3cde77b110038"
OUTPUT = ARTIFACTS / "ocr-rolling-v1/66c3cde77b110038"
SCALES = (640, 1200)
COHORT_SECONDS = 600
PAGE_COUNT = 28


def sha(path: Path) -> str:
    """Identify retained source and output bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def conservation(source: list[dict[str, Any]], alternative: dict[str, Any]) -> bool:
    """Check exact OCR-ID multiplicity, separately from reference-word accuracy."""
    assigned = [
        identifier
        for table in alternative["candidates"]
        for cell in table["cells"]
        for identifier in cell["source_ids"]
    ]
    return Counter(assigned + alternative["unresolved_ids"]) == Counter(word["id"] for word in source)


def geometry_diagnostics(source: list[dict[str, Any]], alternative: dict[str, Any]) -> dict[str, int]:
    """Count sparse nonnumeric bands blocked by overlapping OCR-region boxes."""
    lookup = {word["id"]: word for word in source}
    sparse = negative = 0
    for table in alternative["candidates"]:
        previous_bottom = None
        for row in range(table["row_count"]):
            cells = table["cells"][row * table["col_count"] : (row + 1) * table["col_count"]]
            occupied = {column for column, cell in enumerate(cells) if cell["source_ids"]}
            identifiers = [identifier for cell in cells for identifier in cell["source_ids"]]
            top = min(lookup[identifier]["bbox"][1] for identifier in identifiers)
            bottom = max(lookup[identifier]["bbox"][3] for identifier in identifiers)
            hanging = len(occupied) < table["col_count"] and not occupied.intersection(
                table["numeric_column_hypotheses"]
            )
            if hanging and previous_bottom is not None:
                sparse += 1
                negative += top < previous_bottom
            previous_bottom = bottom
    return {"sparse_nonnumeric_rows": sparse, "negative_gap_sparse_rows": negative}


def literal_recall(expected: list[str], observed: list[str]) -> dict[str, int | float | None]:
    """Compute case-sensitive whitespace-token multiset recall without source splitting."""
    reference = Counter(word for text in expected for word in text.split())
    actual = Counter(word for text in observed for word in text.split())
    shared = (reference & actual).total()
    return {
        "expected_tokens": reference.total(),
        "observed_tokens": actual.total(),
        "matched_tokens": shared,
        "recall": shared / reference.total() if reference else None,
    }


def immutable(path: Path, value: object) -> None:
    """Write new artifacts once, rejecting attempts to change frozen output."""
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    if path.exists() and path.read_bytes() != data:
        message = "Frozen artifact already exists with different bytes"
        raise ValueError(message)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)


def prepare(output: Path) -> None:
    """Render pixels only, and freeze an explicitly separate native-vector arm."""
    import pylopdf  # noqa: PLC0415 - native CPU preparation environment
    from bench.silver_structure import observed_table  # noqa: PLC0415

    start = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_SELF)
    manifest = json.loads(guard_path(CORPUS / "manifest.json").read_text())
    if manifest["split"] != "DEV" or len(manifest["cases"]) != PAGE_COUNT:
        message = "Only the complete pinned 28-page DEV corpus is admitted"
        raise ValueError(message)
    rows, native = [], []
    for case in manifest["cases"]:
        path = guard_path(CORPUS / case["pdf_path"])
        if sha(path) != case["pdf_sha256"]:
            message = "Source PDF hash mismatch"
            raise ValueError(message)
        with pylopdf.Document(path) as doc:
            if doc.page_count != 1:
                message = "Companion inputs must remain single-page"
                raise ValueError(message)
            page = doc[0]
            size = [page.rect.width, page.rect.height]
            for edge in SCALES:
                image_path = output / "pixels" / f"{case['id']}-e{edge}.png"
                dpi = edge * 72 / max(size)
                if not image_path.exists():
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    image_path.write_bytes(page.render(dpi=dpi, background=(255, 255, 255)))
                rows.append(
                    {
                        "id": case["id"],
                        "edge": edge,
                        "page_size": size,
                        "dpi": dpi,
                        "image_path": str(image_path),
                        "image_sha256": sha(image_path),
                        "source_pdf_sha256": case["pdf_sha256"],
                    }
                )
            # This branch is never passed to OCR or the pure assemblers.
            native.append({"id": case["id"], "tables": [observed_table(table) for table in page.find_tables().tables]})
    after = resource.getrusage(resource.RUSAGE_SELF)
    immutable(output / "inputs.json", {"dataset_sha256": manifest["dataset_sha256"], "pages": rows})
    immutable(output / "native-vector.json", native)
    (output / "preparation.json").write_text(
        json.dumps(
            {
                "wall_seconds": time.perf_counter() - start,
                "cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                "peak_rss_kib": after.ru_maxrss,
                "scope": "single CPU process, render and separate native-vector branch",
            },
            indent=2,
        )
    )


def worker(identifier: str, edge: int, output: Path) -> None:
    """Observe only frozen page pixels and preserve complete OCR chunks."""
    import pylopdf  # noqa: PLC0415 - no GPU or model-server imports

    inputs = json.loads((output / "inputs.json").read_text())["pages"]
    row = next(row for row in inputs if row["id"] == identifier and row["edge"] == edge)
    image_path = Path(row["image_path"])
    if sha(image_path) != row["image_sha256"]:
        message = "Raster identity mismatch"
        raise ValueError(message)
    directory = output / str(edge) / identifier
    model_paths = [MODELS / name for name in ("PP-OCRv6_det_small.rten", "PP-OCRv6_rec_small.rten", "ppocrv6_dict.txt")]
    start = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_SELF)
    engine = pylopdf.OcrEngine(*model_paths, threads=2, max_concurrent=1)
    after = resource.getrusage(resource.RUSAGE_SELF)
    initialization = {
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
        "peak_rss_kib": after.ru_maxrss,
    }
    with pylopdf.Document() as doc:
        page = doc.new_page(width=row["page_size"][0], height=row["page_size"][1])
        page.insert_image((0, 0, *row["page_size"]), filename=image_path)
        start = time.perf_counter()
        before = resource.getrusage(resource.RUSAGE_SELF)
        temporary = directory / "phase.tmp"
        temporary.write_text(json.dumps({"started_monotonic": start}))
        temporary.replace(directory / "phase.json")
        observed = page.get_text_ocr(dpi=row["dpi"], engine=engine)
        after = resource.getrusage(resource.RUSAGE_SELF)
    words = [
        {
            "id": f"{identifier}-e{edge}-ocr{index}",
            "text": item["text"],
            "bbox": list(item["bbox"]),
            "confidence": item["confidence"],
        }
        for index, item in enumerate(observed)
    ]
    immutable(
        directory / "observed.json",
        {
            "id": identifier,
            "edge": edge,
            "words": words,
            "page_size": row["page_size"],
            "initialization": initialization,
            "ocr_wall_seconds": time.perf_counter() - start,
            "ocr_cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
            "peak_rss_kib": after.ru_maxrss,
            "image_sha256": row["image_sha256"],
            "input_kind": "frozen_raster_carrier",
            "models": {path.name: sha(path) for path in model_paths},
            "pylopdf_version": pylopdf.__version__,
            "threads": 2,
            "max_concurrent": 1,
            "tile_size": 1408,
            "overlap": 192,
            "min_confidence": 0.5,
        },
    )


def run(output: Path) -> None:
    """Bound all 56 calls and freeze candidates before any target reads."""
    start = time.perf_counter()
    inputs = json.loads((output / "inputs.json").read_text())["pages"]
    for edge in SCALES:
        for row in (row for row in inputs if row["edge"] == edge):
            directory = output / str(edge) / row["id"]
            directory.mkdir(parents=True, exist_ok=True)
            if (directory / "observed.json").exists() and (directory / "candidates.json").exists():
                continue
            status = "complete"
            samples = []
            worker_start = time.perf_counter()
            with (directory / "worker.log").open("w") as log:
                process = subprocess.Popen(  # noqa: S603 - fixed CPU worker module
                    [
                        sys.executable,
                        "-m",
                        "bench.ocr_rolling",
                        "--worker",
                        "--output",
                        str(output),
                        "--id",
                        row["id"],
                        "--edge",
                        str(edge),
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
                    samples.append({"elapsed_seconds": time.perf_counter() - worker_start, "rss_bytes": rss})
                    phase = directory / "phase.json"
                    phase_start = json.loads(phase.read_text())["started_monotonic"] if phase.exists() else worker_start
                    if (
                        (rss is not None and rss > RSS_LIMIT)
                        or time.perf_counter() - phase_start > TIME_LIMIT
                        or time.perf_counter() - start > COHORT_SECONDS
                    ):
                        status = "resource_or_cohort_refusal"
                        process.kill()
                        process.wait()
                        break
                    time.sleep(0.05)
                if process.returncode != 0 and status == "complete":
                    status = "worker_error"
            (directory / "telemetry.json").write_text(
                json.dumps(
                    {
                        "status": status,
                        "samples": samples,
                        "whole_worker_wall_seconds": time.perf_counter() - worker_start,
                        "sampling_interval_seconds": 0.05,
                        "scope": "single worker PID including native threads, no child workers",
                    },
                    indent=2,
                )
            )
            if status == "complete":
                observed = json.loads((directory / "observed.json").read_text())
                source = {"words": observed["words"], "page_size": observed["page_size"]}
                assembler_start = time.perf_counter()
                alternatives = {variant: assemble(source, variant) for variant in ("physical", "rolling")}
                immutable(
                    directory / "candidates.json",
                    {
                        "observed_sha256": sha(directory / "observed.json"),
                        "alternatives": alternatives,
                        "assemble_wall_seconds": time.perf_counter() - assembler_start,
                        "assembler_sha256": sha(Path(__file__).parent / "rolling_rows.py"),
                        "fragments_sha256": sha(Path(__file__).parent / "decision_evidence_designs.py"),
                    },
                )
            print(f"edge={edge} {row['id']}: {status}", flush=True)
            if status != "complete":
                return
        print(f"Frozen complete {edge}-pixel pass; scoring may now run separately", flush=True)


def score(output: Path) -> None:
    """Compare frozen outputs to private targets without rewriting observation."""
    from bench.borderless_challenge import score as score_target  # noqa: PLC0415 - post-freeze scorer only

    targets = json.loads((CORPUS / "private-targets.json").read_text())
    native = {row["id"]: row["tables"] for row in json.loads((output / "native-vector.json").read_text())}
    rows = []
    for edge in SCALES:
        for target in targets:
            directory = output / str(edge) / target["id"]
            if not (directory / "candidates.json").exists():
                rows.append({"edge": edge, "id": target["id"], "kind": target["kind"], "status": "missing_or_refused"})
                continue
            observed = json.loads((directory / "observed.json").read_text())
            candidates = json.loads((directory / "candidates.json").read_text())["alternatives"]
            expected_text = [
                value for table in target["tables"] for cells in table["values"] for value in cells if value
            ]
            if not expected_text:
                expected_text = [target["prose"]]
            recall = literal_recall(expected_text, [word["text"] for word in observed["words"]])
            for variant, alternative in candidates.items():
                tables = alternative["candidates"]
                hybrid = native[target["id"]] or tables
                rows.append(
                    {
                        "edge": edge,
                        "id": target["id"],
                        "kind": target["kind"],
                        "variant": variant,
                        "status": "complete",
                        "pure": score_target(target, tables),
                        "hybrid": score_target(target, hybrid),
                        "native_override": bool(native[target["id"]]),
                        "original_token_recall": recall,
                        "ocr_ids_conserved": conservation(observed["words"], alternative),
                        "geometry_diagnostics": geometry_diagnostics(observed["words"], alternative),
                        "ocr_items": len(observed["words"]),
                        "multi_token_ocr_items": sum(len(word["text"].split()) > 1 for word in observed["words"]),
                        "ocr_seconds": observed["ocr_wall_seconds"],
                        "initialization": observed["initialization"],
                        "whole_worker_wall_seconds": json.loads((directory / "telemetry.json").read_text())[
                            "whole_worker_wall_seconds"
                        ],
                        "ocr_cpu_seconds": observed["ocr_cpu_seconds"],
                        "peak_rss_kib": observed["peak_rss_kib"],
                        "observed_sha256": sha(directory / "observed.json"),
                        "candidates_sha256": sha(directory / "candidates.json"),
                    }
                )
    (output / "scores.json").write_text(json.dumps(rows, indent=2))
    report(rows, output)


def report(rows: list[dict[str, Any]], output: Path) -> None:
    """Summarize all denominators, ownership, and resource measurements."""
    lines = [
        "# Raster OCR to rolling assembly DEV test",
        "",
        (
            "Fixed corpus: 28 pages (12 borderless, 12 aligned prose negatives, four merged vector controls), "
            "`66c3cde77b110038`. The pure OCR arms use frozen rendered pixels and exact OCR region strings/IDs/bboxes. "
            "There is no native extracted text or gold-guided splitting in their inputs. Physical and rolling rules "
            "are unchanged. Native vector override is an explicitly separate hybrid arm."
        ),
        "",
        (
            "| Edge | Assembly | Path | Borderless exact /12 | Prose false positives /12 | Merged exact /4 | "
            "Complete exact /28 | Refused/missing /28 | OCR ID conservation /28 |"
        ),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for edge in SCALES:
        for variant in ("physical", "rolling"):
            selected = [r for r in rows if r["edge"] == edge and r.get("variant") == variant]
            for path in ("pure", "hybrid"):
                exact = {
                    kind: sum(r[path]["exact_page"] for r in selected if r["kind"] == kind)
                    for kind in ("borderless", "ruled-control")
                }
                fp = sum(r[path]["false_positive_page"] for r in selected if r["kind"] == "prose")
                conserved = sum(r["ocr_ids_conserved"] for r in selected)
                lines.append(
                    f"| {edge} | {variant} | {path} | {exact['borderless']}/12 | {fp}/12 | "
                    f"{exact['ruled-control']}/4 | {sum(r[path]['exact_page'] for r in selected)}/28 | "
                    f"{28 - len(selected)}/28 | {conserved}/28 |"
                )
    lines.extend(
        [
            "",
            (
                "| Edge | Kind | OCR target-token recall | Correct pure physical / rolling cell-owned tokens | "
                "Multi-token OCR regions |"
            ),
            "|---|---|---|---|---|",
        ]
    )
    for edge in SCALES:
        for kind in ("borderless", "prose", "ruled-control"):
            a = [r for r in rows if r["edge"] == edge and r.get("variant") == "physical" and r["kind"] == kind]
            b = [r for r in rows if r["edge"] == edge and r.get("variant") == "rolling" and r["kind"] == kind]
            expected = sum(r["original_token_recall"]["expected_tokens"] for r in a)
            matched = sum(r["original_token_recall"]["matched_tokens"] for r in a)
            lines.append(
                f"| {edge} | {kind} | {matched}/{expected} | "
                f"{sum(r['pure']['owned_words'] for r in a)} / {sum(r['pure']['owned_words'] for r in b)} | "
                f"{sum(r['multi_token_ocr_items'] for r in a)}/{sum(r['ocr_items'] for r in a)} |"
            )
    for edge in SCALES:
        selected = [r for r in rows if r["edge"] == edge and r.get("variant") == "physical"]
        lines.extend(
            [
                "",
                (
                    f"{edge}-pixel OCR completed {len(selected)}/28: "
                    f"{sum(r['ocr_seconds'] for r in selected):.3f}s summed OCR wall, "
                    f"{sum(r['ocr_cpu_seconds'] for r in selected):.3f}s summed worker CPU, "
                    f"{sum(r['whole_worker_wall_seconds'] for r in selected):.3f}s complete worker wall. "
                    f"Separate engine initialization totals: "
                    f"{sum(r['initialization']['wall_seconds'] for r in selected):.3f}s wall / "
                    f"{sum(r['initialization']['cpu_seconds'] for r in selected):.3f}s CPU. "
                    f"{max((r['peak_rss_kib'] for r in selected), default=0) / 1024:.1f} MiB "
                    "largest worker lifetime RSS."
                ),
            ]
        )
    lines.extend(
        [
            "",
            (
                "OCR-ID conservation counts each observed region once across candidates and unresolved items; "
                "it does not measure original PDF-word recall. Target-token recall is a post-output, case-sensitive "
                "whitespace-token bag metric over expected cell text (or authored prose on negatives); "
                "it ignores order "
                "and is not CER or spatial ownership. Cell-owned tokens use the unchanged authored matrix scorer and "
                "only receive credit in correctly dimensioned candidate slots. Native hybrid tables use original "
                "PDF vectors/text; OCR IDs remain a separately checked pure-path inventory, "
                "not hybrid cell attribution."
            ),
            "",
            (
                "All 28 denominators remain explicit at both scales. Missing/refused pages score as unavailable, "
                "not as successful abstentions. Engine initialization precedes each OCR timer and remains separately "
                "retained; rendering/raster preparation and native-vector preparation are separately recorded. "
                "OCR includes raster-carrier render plus recognition. CPU2 threads, max_concurrent1, "
                "tile1408, overlap192, "
                "confidence0.5; watchdog30s per OCR call,1GiB observed RSS,10min cohort. "
                "Parent samples /proc worker PID "
                "at0.05s target interval plus overhead; killing can overshoot one polling interval. SELF getrusage "
                "records worker CPU and lifetime peak RSS, including native threads; there are no worker children."
            ),
            "",
            (
                "Reproduce `.venv/bin/python -m bench.ocr_rolling --prepare --run --score`. Frozen rasters, exact OCR "
                "items, candidate matrices/IDs, source/model/assembler hashes, telemetry, native-vector branch, and "
                "private scores remain ignored under `ocr-rolling-v1/66c3cde77b110038/`. No hosted spending, GPU work, "
                "training, heldout access, or production API changes occurred. This is correlated authored DEV "
                "evidence, not independent-producer validation."
            ),
            "",
        ]
    )
    for edge in SCALES:
        selected = [row for row in rows if row["edge"] == edge and row.get("variant") == "physical"]
        sparse = sum(row["geometry_diagnostics"]["sparse_nonnumeric_rows"] for row in selected)
        negative = sum(row["geometry_diagnostics"]["negative_gap_sparse_rows"] for row in selected)
        lines.extend(
            [
                "",
                (
                    f"Source-only geometry diagnostic at edge {edge}: {negative}/{sparse} sparse "
                    "nonnumeric physical rows have negative bbox gaps to the preceding row. "
                    "The unchanged rolling rule requires a nonnegative gap before joining. "
                    "OCR region padding/overlap therefore blocks these continuation candidates even when "
                    "their literal text is retained. This diagnoses the current geometry interface; no bbox "
                    "shrinking, OCR-string splitting, or gold-directed correction was applied."
                ),
            ]
        )
    lines.extend(
        [
            "",
            (
                "Higher resolution improves recognition and six no-wrap borderless matrices, but does not "
                "repair wrapped row joining, merged spans, or prose/table semantic admission. Pure merged cells "
                "can retain all target words while unit-span proposals fail complete merged structure. "
                "Native vector override restores four merged controls only in the separately labeled hybrid. "
                "OCR source-ID conservation is necessary but insufficient for original-word and cell ownership."
            ),
            "",
        ]
    )
    preparation = json.loads((output / "preparation.json").read_text())
    lines.extend(
        [
            "",
            (
                f"Raster and separate native-vector preparation: {preparation['wall_seconds']:.3f}s wall / "
                f"{preparation['cpu_seconds']:.3f}s CPU; "
                f"{preparation['peak_rss_kib'] / 1024:.1f} MiB process-lifetime getrusage peak RSS. "
                "This parent-process lifetime peak is distinct from per-call OCR worker memory and includes "
                "the complete 56-raster preparation pass. No preparation-memory bound is inferred from the "
                "smaller OCR worker peaks."
            ),
            "",
        ]
    )
    (Path(__file__).parent / "results/ocr-rolling.md").write_text("\n".join(lines))


def overlap_ablation(output: Path) -> None:
    """Freeze three source-only overlap hypotheses before paired DEV scoring."""
    directory = output / "overlap-a004-v1"
    paths = [
        output / str(edge) / f"case-{index:03d}" / "observed.json" for edge in SCALES for index in range(PAGE_COUNT)
    ]
    config: dict[str, Any] = {
        "experiment": "A004",
        "overlap_heights": [0.0, 0.25, 0.5],
        "scope": "otherwise eligible sparse nonnumeric rolling continuations only",
        "source_observations": {str(path.relative_to(output)): sha(path) for path in paths},
        "assembler_sha256": sha(Path(__file__).parent / "rolling_rows.py"),
        "default_changed": False,
        "new_ocr_calls": 0,
        "provider_charge": 0,
    }
    immutable(directory / "frozen-config.json", config)
    started, cpu = time.perf_counter(), time.process_time()
    rows = []
    for path in paths:
        source = json.loads(path.read_text())
        hypotheses = {
            str(value): assemble(source, "rolling", overlap_heights=value) for value in config["overlap_heights"]
        }
        baseline = json.loads((path.parent / "candidates.json").read_text())["alternatives"]["rolling"]
        if hypotheses["0.0"] != baseline:
            message = "Default assembler no longer matches the original frozen baseline"
            raise ValueError(message)
        rows.append(
            {
                "id": source["id"],
                "edge": source["edge"],
                "source_words": source["words"],
                "hypotheses": hypotheses,
                "baseline_matches_original": True,
            }
        )
    immutable(directory / "frozen-candidates.json", rows)
    after = resource.getrusage(resource.RUSAGE_SELF)
    (directory / "resources.json").write_text(
        json.dumps(
            {
                "assembly_wall_seconds": time.perf_counter() - started,
                "assembly_cpu_seconds": time.process_time() - cpu,
                "peak_rss_kib": after.ru_maxrss,
                "scope": "single sequential CPU process; getrusage lifetime RSS; no sampling",
            },
            indent=2,
        )
    )
    # Only the independent scorer below opens construction references.
    from bench.borderless_challenge import score as score_target  # noqa: PLC0415

    targets = {target["id"]: target for target in json.loads((CORPUS / "private-targets.json").read_text())}
    native = {row["id"]: row["tables"] for row in json.loads((output / "native-vector.json").read_text())}
    scores = []
    for row in rows:
        target = targets[row["id"]]
        for allowance, candidate in row["hypotheses"].items():
            pure = candidate["candidates"]
            scores.append(
                {
                    "id": row["id"],
                    "edge": row["edge"],
                    "allowance": allowance,
                    "kind": target["kind"],
                    "wrap": target["wrap"],
                    "pure": score_target(target, pure),
                    "hybrid": score_target(target, native[row["id"]] or pure),
                    "conserved": conservation(row["source_words"], candidate),
                }
            )
    (directory / "scores.json").write_text(json.dumps(scores, indent=2))
    lines = [
        "# A004 OCR overlap ablation",
        "",
        (
            "Three allowances (0.0, 0.25, 0.5 median OCR item heights) were frozen before this paired scorer ran. "
            "All use the same 56 immutable OCR observations; no new OCR, inference, geometry shrinking, "
            "string splitting, or case-specific rule changes occur. Original A003/default behavior remains unchanged; "
            "the optional keyword defaults to zero and validates finite values in [0, 0.5]."
        ),
        "",
        (
            "| Edge | Allowance | Borderless exact /12 | Wrapped exact /6 | Prose FP /12 | "
            "Pure merged exact /4 | Pure complete /28 | Hybrid complete /28 | OCR IDs conserved /28 |"
        ),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for edge in SCALES:
        for allowance in ("0.0", "0.25", "0.5"):
            selected = [row for row in scores if row["edge"] == edge and row["allowance"] == allowance]
            borderless = [row for row in selected if row["kind"] == "borderless"]
            wrapped = [row for row in borderless if row["wrap"]]
            lines.append(
                f"| {edge} | {allowance} | {sum(r['pure']['exact_page'] for r in borderless)}/12 | "
                f"{sum(r['pure']['exact_page'] for r in wrapped)}/6 | "
                f"{sum(r['pure']['false_positive_page'] for r in selected if r['kind'] == 'prose')}/12 | "
                f"{sum(r['pure']['exact_page'] for r in selected if r['kind'] == 'ruled-control')}/4 | "
                f"{sum(r['pure']['exact_page'] for r in selected)}/28 | "
                f"{sum(r['hybrid']['exact_page'] for r in selected)}/28 | "
                f"{sum(r['conserved'] for r in selected)}/28 |"
            )
    resources = json.loads((directory / "resources.json").read_text())
    lines.extend(
        [
            "",
            (
                "All 56 zero-allowance outputs exactly match the original frozen candidates. "
                "Missing/refused counts are 0/28 per scale; all denominators include "
                "12 borderless, 12 prose, and 4 merged pages. "
                "The lower gap boundary alone becomes -height×allowance; numeric-bearing and complete bands "
                "still cannot join, and the existing upper-gap, anchor-support, column and source-conservation "
                "conditions remain active. Native vectors/text are used solely for the separately labeled hybrid."
            ),
            "",
            (
                f"CPU assembly-only pass: {resources['assembly_wall_seconds']:.3f}s wall / "
                f"{resources['assembly_cpu_seconds']:.3f}s CPU; {resources['peak_rss_kib'] / 1024:.1f} MiB "
                "process-lifetime getrusage SELF RSS, single sequential process, no sampling/children/GPU. "
                "No provider spending or additional OCR resource usage. These are authored correlated DEV results, "
                "not independent confirmation or production acceptance."
            ),
            "",
            (
                "Reproduce `.venv/bin/python -m bench.ocr_rolling --overlap` after the frozen baseline exists. "
                "Config, source hashes, candidate matrices/IDs, full scores and resources remain ignored in "
                "`ocr-rolling-v1/66c3cde77b110038/overlap-a004-v1/`. The default candidate artifact is preserved."
            ),
            "",
        ]
    )
    (Path(__file__).parent / "results/ocr-rolling-overlap.md").write_text("\n".join(lines))


def main() -> None:
    """Prepare pixels, freeze OCR candidates, then score in a separate phase."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--overlap", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--id")
    parser.add_argument("--edge", type=int, choices=SCALES)
    args = parser.parse_args()
    if args.prepare:
        prepare(args.output)
    if args.worker:
        worker(args.id, args.edge, args.output)
    if args.run:
        run(args.output)
    if args.score:
        score(args.output)
    if args.overlap:
        overlap_ablation(args.output)


if __name__ == "__main__":
    main()
