"""Reproducible metadata-selected OmniDocBench DEV page-image sample."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

import pylopdf

REVISION = "aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec"
SOURCE = "https://huggingface.co/datasets/opendatalab/OmniDocBench"
DEFAULT_ARTIFACTS = Path("/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/omnidoc-dev")
REGISTRY = Path(__file__).parent / "omnidoc-dev" / "registry.json"
SEED = "pdf-master-omnidoc-dev-v1"


def digest(data: bytes) -> str:
    """Return a SHA256 identity for retained bytes."""
    return hashlib.sha256(data).hexdigest()


def canonical(data: object) -> bytes:
    """Serialize annotation data with stable ordering."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def row_id(row: dict[str, Any]) -> str:
    """Return the official page-image identifier."""
    return str(row["page_info"]["image_path"])


def features(row: dict[str, Any]) -> set[str]:
    """Use classification metadata and category presence, never answer text."""
    attr = row["page_info"]["page_attribute"]
    values = {f"{key}:{attr.get(key, 'unknown')}" for key in ("data_source", "language", "layout")}
    categories = {block["category_type"] for block in row["layout_dets"]}
    values.add("math:" + str("equation_isolated" in categories))
    values.add("table:" + str("table" in categories))
    return values


def select_rows(rows: list[dict[str, Any]], count: int = 16) -> list[dict[str, Any]]:
    """Greedily cover metadata, then hash-fill; ties use a frozen seeded hash."""
    if not 1 <= count <= len(rows):
        message = "sample count must be between one and the number of rows"
        raise ValueError(message)
    if len({row_id(row) for row in rows}) != len(rows):
        message = "image identifiers must be unique"
        raise ValueError(message)
    remaining = sorted(rows, key=lambda row: digest((SEED + row_id(row)).encode()))
    covered: set[str] = set()
    selected = []
    for _ in range(count):
        winner = max(range(len(remaining)), key=lambda i: len(features(remaining[i]) - covered))
        row = remaining.pop(winner)
        selected.append(row)
        covered.update(features(row))
    return selected


def fetch(path: str, destination: Path) -> bytes:
    """Fetch a public pinned file or reuse retained local bytes."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with urlopen(f"{SOURCE}/resolve/{REVISION}/{quote(path, safe='/')}", timeout=90) as response:  # noqa: S310 - fixed public HTTPS origin
            data = response.read()
        temporary = destination.with_suffix(destination.suffix + ".part")
        temporary.write_bytes(data)
        temporary.replace(destination)
    return destination.read_bytes()


def acquire(artifacts: Path, registry_path: Path = REGISTRY) -> dict[str, Any]:
    """Acquire the frozen diversity sample and write its registry."""
    annotation_bytes = fetch("OmniDocBench.json", artifacts / "OmniDocBench.json")
    card_bytes = fetch("README.md", artifacts / "README.md")
    rows = json.loads(annotation_bytes)
    selected = select_rows(rows)
    entries = []
    for index, row in enumerate(selected, 1):
        image_name = row_id(row)
        if Path(image_name).name != image_name:
            message = "unexpected non-basename image identifier"
            raise ValueError(message)
        image = fetch("images/" + image_name, artifacts / "images" / image_name)
        row_bytes = canonical(row)
        (artifacts / "annotations").mkdir(exist_ok=True)
        (artifacts / "annotations" / (image_name + ".json")).write_bytes(row_bytes)
        info = row["page_info"]
        entries.append(
            {
                "sample": index,
                "id": image_name,
                "source_url": f"{SOURCE}/resolve/{REVISION}/images/{quote(image_name)}",
                "image_sha256": digest(image),
                "annotation_sha256": digest(row_bytes),
                "image_bytes": len(image),
                "width": info["width"],
                "height": info["height"],
                "page_no": info["page_no"],
                "attributes": info["page_attribute"],
                "category_counts": dict(sorted(Counter(x["category_type"] for x in row["layout_dets"]).items())),
                "input_kind": "official_page_image",
                "native_pdf_available_in_revision": False,
            }
        )
    registry = {
        "schema_version": 1,
        "purpose": "DEV tuning, not heldout evaluation",
        "dataset": "opendatalab/OmniDocBench",
        "revision": REVISION,
        "source": SOURCE,
        "annotation_sha256": digest(annotation_bytes),
        "card_sha256": digest(card_bytes),
        "source_rows": len(rows),
        "license": "Dataset card: research purposes only; not for commercial use",
        "license_source": f"{SOURCE}/blob/{REVISION}/README.md",
        "contamination": "Public benchmark; model pretraining contamination unknown",
        "selection": {
            "count": 16,
            "seed": SEED,
            "algorithm": "greedy uncovered metadata/category-presence coverage; seeded SHA256 tie order",
            "answer_text_used": False,
        },
        "rows": entries,
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    return registry


def baseline(artifacts: Path, registry: dict[str, Any]) -> dict[str, Any]:
    """Measure CPU image-carrier behavior; this is not an OCR accuracy score."""
    started = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_SELF)
    results = []
    for row in registry["rows"]:
        row_start = time.perf_counter()
        image = artifacts / "images" / row["id"]
        if digest(image.read_bytes()) != row["image_sha256"]:
            message = "image hash mismatch"
            raise ValueError(message)
        with pylopdf.Document() as document:
            page = document.new_page(width=row["width"] * 0.36, height=row["height"] * 0.36)
            page.insert_image((0, 0, page.rect.width, page.rect.height), filename=image)
            text = page.get_text()
            tables = page.find_tables()
            placements = page.get_images()
            png = page.render(dpi=72)
            markdown = document.to_markdown()
            output = {
                "id": row["id"],
                "input_kind": "synthetic_image_wrapped_pdf",
                "native_text_characters": len(text),
                "vector_tables": len(tables),
                "image_placements": len(placements),
                "render_png_bytes": len(png),
                "render_sha256": digest(png),
                "markdown_characters": len(markdown),
                "elapsed_seconds": time.perf_counter() - row_start,
            }
            results.append(output)
    after = resource.getrusage(resource.RUSAGE_SELF)
    result = {
        "pylopdf_version": pylopdf.__version__,
        "rows": results,
        "elapsed_seconds": time.perf_counter() - started,
        "cpu_user_seconds": after.ru_utime - before.ru_utime,
        "cpu_system_seconds": after.ru_stime - before.ru_stime,
        "peak_rss_kib": after.ru_maxrss,
        "measurement": (
            "Linux resource.getrusage(RUSAGE_SELF), process lifetime peak RSS; "
            "no sampling; single sequential process; CPU only; no children"
        ),
        "machine": platform.platform(),
        "cpu_count": os.cpu_count(),
        "remote_inference": "not run",
        "provider_charge": "not applicable",
    }
    (artifacts / "baseline.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def report(registry: dict[str, Any], measured: dict[str, Any], destination: Path) -> None:
    """Write the readable per-row CPU baseline summary."""
    outcomes = {row["id"]: row for row in measured["rows"]}
    lines = [
        "# OmniDocBench DEV sample",
        "",
        (
            f"16 deterministic DEV rows from {registry['source_rows']} official pages at revision "
            f"`{REVISION}`. Public benchmark contamination is unknown; this is not a heldout result."
        ),
        "",
        (
            "Selection greedily covers source type, language, layout, and isolated-formula/table "
            "presence, with seeded SHA256 tie order. It never uses recognition answer text, model "
            "outputs, or quality scores. Raw annotations/images and complete baseline outputs "
            "remain ignored local artifacts."
        ),
        "",
        (
            f"Dataset restriction: [{registry['license']}]({registry['license_source']}). Raw "
            f"dataset assets are not committed or redistributed."
        ),
        "",
        (
            "The pinned current release contains page images but no original PDFs. Each CPU check "
            "inserts the official image into a newly generated PDF without an OCR layer. Zero "
            "native text and zero vector tables are expected properties of these carriers, not "
            "native-PDF extraction failures. No OCR or hosted inference was run."
        ),
        "",
        (
            "| # | Page image ID | Source type | Language | Layout | Formula / table blocks | Image "
            "placements | Native text | Render |"
        ),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in registry["rows"]:
        attr = row["attributes"]
        counts = row["category_counts"]
        result = outcomes[row["id"]]
        lines.append(
            f"| {row['sample']} | `{row['id']}` | {attr['data_source']} | {attr['language']} | "
            f"{attr['layout']} | {counts.get('equation_isolated', 0)} / {counts.get('table', 0)} | "
            f"{result['image_placements']} | {result['native_text_characters']} | "
            f"{result['render_png_bytes']:,} B |"
        )
    lines.extend(
        [
            "",
            (
                f"CPU baseline: {measured['elapsed_seconds']:.3f}s elapsed, "
                f"{measured['cpu_user_seconds']:.3f}s user + {measured['cpu_system_seconds']:.3f}s "
                f"system CPU, {measured['peak_rss_kib'] / 1024:.1f} MiB process-lifetime peak RSS. "
                f"Tool/scope: {measured['measurement']}. Machine: `{measured['machine']}`, "
                f"{measured['cpu_count']} logical CPUs, pylopdf `{measured['pylopdf_version']}`. Network "
                f"download time is excluded; local image insertion/extraction/rendering is included. "
                f"Remote resource usage is unmeasured because no remote inference ran."
            ),
            "",
            (
                "This sample provides external page-image layout/language coverage. Native text, "
                "reading order, math transcription, and table recognition quality require OCR or "
                "matching original PDFs and a separately specified evaluation protocol."
            ),
            "",
        ]
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines))


def main() -> None:
    """Run sample acquisition or CPU baseline generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    registry = acquire(args.artifacts) if args.fetch else json.loads(REGISTRY.read_text())
    if args.baseline:
        measured = baseline(args.artifacts, registry)
        report(registry, measured, Path(__file__).parent / "results" / "omnidoc-sample.md")
    print(f"OmniDocBench DEV sample: {len(registry['rows'])} rows, revision {REVISION}")


if __name__ == "__main__":
    main()
