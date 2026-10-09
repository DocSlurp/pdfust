"""Build and inspect a reproducible silver PDF challenge, using CPU only."""

# Heterogeneous artifact dictionaries retain producer metadata and parser observations.
# ruff: noqa: EM101, TRY003, PLR2004, PLC0415

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts/silver-v1"
SCHEMA = 1
MAX_WORKERS = 4


def canonical(value: object) -> bytes:
    """Serialize strict deterministic JSON for dataset and configuration identities."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def sha(data: bytes) -> str:
    """Identify exact source bytes without relying on filenames."""
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    """Write a complete JSON artifact atomically."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def guard_path(path: Path) -> Path:
    """Reject held-out locations before any artifact or PDF read, including symlinks."""
    for candidate in (path, path.resolve()):
        name = str(candidate).lower()
        if "heldout-silver" in name or "silver-heldout-v1" in name:
            raise ValueError("Held-out silver paths are forbidden in this DEV runner")
    return path.resolve()


def dataset_path(directory: Path, relative: str) -> Path:
    """Resolve one manifest path within its DEV dataset, rejecting traversal."""
    base = guard_path(directory)
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Dataset paths must be relative and cannot traverse parents")
    resolved = guard_path(base / path)
    if not resolved.is_relative_to(base):
        raise ValueError("Dataset path escapes its directory")
    return resolved


def load_manifest(directory: Path) -> dict[str, Any]:
    """Validate all DEV split declarations and input paths before reading gold or PDFs."""
    directory = guard_path(directory)
    manifest: dict[str, Any] = json.loads(dataset_path(directory, "manifest.json").read_text())
    if manifest.get("split") != "DEV" or not isinstance(manifest.get("cases"), list):
        raise ValueError("Silver runner accepts only explicit DEV manifests")
    seen: set[str] = set()
    for record in manifest["cases"]:
        if record.get("split") != "DEV":
            raise ValueError("Every silver case must explicitly declare split DEV")
        case_id = record.get("id")
        if (
            not isinstance(case_id, str)
            or not case_id
            or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in case_id)
        ):
            raise ValueError("Invalid case ID")
        if case_id in seen:
            raise ValueError("Duplicate case ID")
        seen.add(case_id)
        dataset_path(directory, record["pdf_path"])
    return manifest


def verify_input(directory: Path, record: dict[str, Any]) -> Path:
    """Verify the immutable PDF checksum before extraction or gallery rendering."""
    path = dataset_path(directory, record["pdf_path"])
    if sha(path.read_bytes()) != record["pdf_sha256"]:
        raise ValueError("Input hash changed after dataset freeze")
    return path


def build(directory: Path = ARTIFACTS) -> Path:
    """Build a content-addressed DEV dataset with gold separate from inputs."""
    from bench.silver_layouts import generate_cases as layouts
    from bench.silver_math import generate_cases as math_cases

    directory = guard_path(directory)
    cases = layouts() + math_cases()
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)) or not 50 <= len(cases) <= 150:
        raise ValueError("Silver challenge requires 50–150 unique cases")
    records = []
    gold = []
    for case in sorted(cases, key=lambda case: case["id"]):
        if Path(case["id"]).name != case["id"] or not case["pdf"].startswith(b"%PDF-"):
            raise ValueError("Invalid case ID or PDF payload")
        record = {key: value for key, value in case.items() if key not in ("pdf", "expected_text", "reference_math")}
        record.update(
            pdf_sha256=sha(case["pdf"]),
            pdf_path="pdfs/" + case["id"] + ".pdf",
            label_status="silver-authored-unadjudicated",
            split="DEV",
            source_kind="generated",
        )
        records.append(record)
        gold.append(
            {
                "id": case["id"],
                "pdf_sha256": record["pdf_sha256"],
                "expected_text": case.get("expected_text", []),
                "reference_math": case.get("reference_math"),
                "label_status": "silver-authored-unadjudicated",
            }
        )
    identity = sha(canonical({"schema": SCHEMA, "records": records, "gold": gold}))
    target = directory / identity[:16]
    (target / "pdfs").mkdir(parents=True, exist_ok=True)
    for case in cases:
        path = target / "pdfs" / (case["id"] + ".pdf")
        if path.exists() and path.read_bytes() != case["pdf"]:
            raise ValueError("Existing immutable input disagrees with generated bytes")
        path.write_bytes(case["pdf"])
    manifest = {
        "schema": SCHEMA,
        "split": "DEV",
        "dataset_sha256": identity,
        "case_count": len(cases),
        "cases": records,
        "split_policy": "DEV only. Template siblings must remain together in any future split.",
        "generator_sha256": {
            name: sha((ROOT / "bench" / name).read_bytes())
            for name in ("silver_layouts.py", "silver_math.py", "silver.py", "silver_metadata.py")
        },
    }
    write_json(target / "manifest.json", manifest)
    write_json(target / "gold.json", gold)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "latest.json", {"dataset_sha256": identity, "path": str(target)})
    return target


def rss_bytes() -> int | None:
    """Return current-exec peak RSS; avoid inherited Linux getrusage high-water."""
    if sys.platform.startswith("linux"):
        try:
            for line in Path("/proc/self/status").read_text().splitlines():
                if line.startswith("VmHWM:"):
                    return int(line.split()[1]) * 1024
        except (OSError, ValueError):
            return None
        return None
    try:
        import resource
    except ImportError:
        return None
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(usage * (1 if sys.platform == "darwin" else 1024))


def measure(data: bytes) -> dict[str, Any]:
    """Time cold and reused all-page extraction without model inference or rendering."""
    import pylopdf

    start = time.perf_counter()
    cpu = time.process_time()
    with pylopdf.open(stream=data) as document:
        text = "\n".join(page.get_text() for page in document)
        markdown = document.to_markdown()
        cold_ms = (time.perf_counter() - start) * 1000
        cold_cpu_ms = (time.process_time() - cpu) * 1000
        warm_start = time.perf_counter()
        warm_cpu = time.process_time()
        warm = "\n".join(page.get_text() for page in document)
        warm_markdown = document.to_markdown()
        warm_ms = (time.perf_counter() - warm_start) * 1000
        warm_cpu_ms = (time.process_time() - warm_cpu) * 1000
    return {
        "cold_wall_ms": cold_ms,
        "cold_cpu_ms": cold_cpu_ms,
        "warm_wall_ms": warm_ms,
        "warm_cpu_ms": warm_cpu_ms,
        "text_sha256": sha(text.encode()),
        "markdown_sha256": sha(markdown.encode()),
        "warm_equal": text == warm and markdown == warm_markdown,
        "text": text,
        "markdown": markdown,
    }


def worker(path: Path) -> dict[str, Any]:
    """Measure one document in a fresh process; process RSS covers all phases."""
    path = guard_path(path)
    directory = path.parent.parent
    manifest = load_manifest(directory)
    record = next((r for r in manifest["cases"] if dataset_path(directory, r["pdf_path"]) == path), None)
    if record is None:
        raise ValueError("Worker input is absent from the DEV manifest")
    verify_input(directory, record)
    import pylopdf  # noqa: F401 - load extension before CPU counters begin.
    from bench.silver_metadata import analyze_pdf

    start = time.perf_counter()
    cpu = time.process_time()
    before = os.times()
    initial_rss = rss_bytes()
    data = path.read_bytes()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        metadata = analyze_pdf(data)
        metadata_wall_ms = (time.perf_counter() - start) * 1000
        result = measure(data)
    elapsed = time.perf_counter() - start
    cpu_seconds = time.process_time() - cpu
    after = os.times()
    return {
        "metadata": metadata,
        "extraction": result,
        "warnings": sorted({str(w.message) for w in captured}),
        "resources": {
            "wall_ms": elapsed * 1000,
            "cpu_ms": cpu_seconds * 1000,
            "cpu_utilization_pct": 100 * cpu_seconds / elapsed if elapsed else None,
            "user_cpu_ms": (after.user - before.user) * 1000,
            "system_cpu_ms": (after.system - before.system) * 1000,
            "peak_rss_bytes": rss_bytes(),
            "initial_peak_rss_bytes": initial_rss,
            "metadata_wall_ms": metadata_wall_ms,
            "scope": (
                "wall/CPU counters cover file read, metadata and cold/warm extraction after imports and input "
                "validation; peak RSS is the fresh worker lifetime including imports and validation"
            ),
            "tool": "time.process_time/os.times; Linux /proc/self/status VmHWM; other Unix getrusage.ru_maxrss",
            "sampling_interval": "OS cumulative counters and process high-water RSS; no periodic sampling",
        },
    }


def flatten(value: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten scalars for CSV grouping; retain arrays as JSON cells."""
    result = {}
    for key, item in value.items():
        name = prefix + key
        if isinstance(item, dict):
            result.update(flatten(item, name + "."))
        elif isinstance(item, list):
            result[name] = canonical(item).decode()
        else:
            result[name] = item
    return result


def export_rows(output: Path, name: str, rows: list[dict[str, Any]]) -> None:
    """Export full JSON rows and flattened CSV rows for independent grouping."""
    with (output / (name + ".jsonl")).open("w") as handle:
        for row in rows:
            handle.write(canonical(row).decode() + "\n")
    flattened = [flatten(row) for row in rows]
    columns = sorted({key for row in flattened for key in row})
    with (output / (name + ".csv")).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(flattened)


def benchmark(directory: Path, *, workers: int = 1) -> dict[str, Any]:
    """Retain failures and full all-page outputs; score only declared literal anchors."""
    if not 1 <= workers <= MAX_WORKERS:
        raise ValueError("Worker count must be between 1 and 4")
    directory = guard_path(directory)
    manifest = load_manifest(directory)
    paths = {record["id"]: verify_input(directory, record) for record in manifest["cases"]}
    gold = {r["id"]: r for r in json.loads(dataset_path(directory, "gold.json").read_text())}
    for record in manifest["cases"]:
        if record["id"] not in gold or gold[record["id"]]["pdf_sha256"] != record["pdf_sha256"]:
            raise ValueError("Gold input identity disagrees with the DEV manifest")
    runs = directory / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    output = Path(mkdtemp(prefix=time.strftime("%Y%m%dT%H%M%S-", time.gmtime()), dir=runs))

    def one(record: dict[str, Any]) -> dict[str, Any]:
        path = paths[record["id"]]
        began = time.perf_counter()
        try:
            process = subprocess.run(  # noqa: S603 - fixed interpreter/module, validated DEV input path.
                [sys.executable, "-m", "bench.silver", "--worker", str(path)],
                cwd=ROOT,
                env={**os.environ, "CUDA_VISIBLE_DEVICES": ""},
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            row = {
                **record,
                "process_wall_ms": (time.perf_counter() - began) * 1000,
                "status": "error",
                "error_type": "TimeoutExpired",
                "error": str(exc),
                "timeout_seconds": 120,
            }
            write_json(output / (record["id"] + ".json"), row)
            return row
        row = {**record, "process_wall_ms": (time.perf_counter() - began) * 1000}
        if process.returncode:
            row.update(status="error", returncode=process.returncode, error=process.stderr[-4000:])
        else:
            row.update(json.loads(process.stdout))
            row["status"] = "ok"
            extracted = row["extraction"]
            text = extracted.pop("text")
            markdown = extracted.pop("markdown")
            (output / (record["id"] + ".txt")).write_text(text)
            (output / (record["id"] + ".md")).write_text(markdown)
            expected = gold[record["id"]]["expected_text"]
            normalized = " ".join(text.split())
            row["silver_anchor_score"] = {
                "found": sum(" ".join(a.split()) in normalized for a in expected),
                "total": len(expected),
                "metric": "visible literal anchor recall; not layout/math correctness",
            }
        write_json(output / (record["id"] + ".json"), row)
        return row

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(one, manifest["cases"]))
    elapsed = time.perf_counter() - start
    export_rows(output, "metadata", rows)
    pages = [
        {
            "id": row["id"],
            "family": row.get("family"),
            "encoding": row.get("encoding"),
            "producer_group": row.get("producer_group"),
            "split": row["split"],
            "pdf_sha256": row["pdf_sha256"],
            **page,
        }
        for row in rows
        if row["status"] == "ok"
        for page in row["metadata"].get("pages") or []
    ]
    export_rows(output, "pages", pages)
    summary = {
        "dataset_sha256": manifest["dataset_sha256"],
        "documents": len(rows),
        "completed": sum(r["status"] == "ok" for r in rows),
        "wall_seconds": elapsed,
        "workers": workers,
        "machine": {
            "platform": platform.platform(),
            "python": sys.version,
            "cpu_logical_count": os.cpu_count(),
            "cpu_name": platform.processor(),
        },
        "run_directory": str(output),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "metadata_sha256": sha((ROOT / "bench/silver_metadata.py").read_bytes()),
    }
    write_json(output / "summary.json", summary)
    write_json(directory / "latest-run.json", summary)
    return summary


def gallery(directory: Path) -> Path:
    """Render one example per family and encoding into a local contact sheet."""
    from PIL import Image, ImageDraw

    import pylopdf

    directory = guard_path(directory)
    manifest = load_manifest(directory)
    paths = {case["id"]: verify_input(directory, case) for case in manifest["cases"]}
    seen = set()
    chosen = []
    for case in manifest["cases"]:
        key = (case["family"], case.get("encoding"))
        if key not in seen:
            chosen.append(case)
            seen.add(key)
    target = directory / "gallery"
    target.mkdir(exist_ok=True)
    width, height = 260, 370
    sheet = Image.new("RGB", (width * 4, height * ((len(chosen) + 3) // 4)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, case in enumerate(chosen):
        with pylopdf.open(paths[case["id"]]) as doc:
            page = doc[0]
            pix = page.get_pixmap(scale=240 / max(page.rect[2:]), background=(255, 255, 255))
            image = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples).convert("RGB")
        image.save(target / (case["id"] + ".png"))
        x = (index % 4) * width
        y = (index // 4) * height
        sheet.paste(image, (x, y + 35))
        draw.text((x + 3, y + 3), case["id"], fill="black")
    sheet.save(target / "contact-sheet.png")
    return target / "contact-sheet.png"


def main() -> None:
    """Run opt-in local generation, metadata collection, baseline and gallery."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--gallery", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(canonical(worker(args.worker)).decode())
        return
    directory = build(args.directory or ARTIFACTS) if args.build else args.directory
    if directory is None:
        directory = Path(json.loads(guard_path(ARTIFACTS / "latest.json").read_text())["path"])
    print("Dataset:", directory)
    if args.benchmark:
        print(json.dumps(benchmark(directory, workers=args.workers), indent=2))
    if args.gallery:
        print("Gallery:", gallery(directory))


if __name__ == "__main__":
    main()
