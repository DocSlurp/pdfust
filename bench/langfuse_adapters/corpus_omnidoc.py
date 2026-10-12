"""OmniDocBench-derived studies: DEV baseline/OCR admission and TRAINING derivative generations.

OmniDocBench is third-party research-only data: images and annotations are referenced by
path and SHA-256, never inlined.

- ``omnidoc-dev/baseline.json`` (``bench/omnidoc_sample.py``; ``bench/results/omnidoc-sample.md``)
  is a CPU image-carrier measurement, not an accuracy score: its counts are reported as such.
- ``omnidoc-dev/ocr-admission/scores.json`` (``bench/omnidoc_ocr.py``;
  ``bench/results/omnidoc-ocr.md``): native OCR at two raster edges on four selected pages,
  scored by block coverage and per-block character bags (not CER or reading order).
- ``omnidoc-training-v1/synthetic-v*/manifest.json`` (``bench/omnidoc_training.py``;
  ``bench/results/omnidoc-training.md``): reference-derived TRAINING layouts compared to their
  reference pages by coarse ink statistics. Labeled ``split=TRAINING``; not an evaluation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.corpus_common import mtime, ref, rel, scalars

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "corpus-omnidoc"
DEV = "omnidoc-dev"
TRAINING = "omnidoc-training-v1"
LICENSE = "OmniDocBench: research purposes only; not for commercial use"
BASELINE_SCORES = ("native_text_characters", "vector_tables", "image_placements", "markdown_characters")


def _registry(artifacts: Path, name: str) -> dict[str, Any]:
    path = artifacts.parents[1] / name / "registry.json"
    return read_json(path) if path.is_file() else {}


def _dev_items(directory: Path, registry: dict[str, Any]) -> tuple[list[Item], dict[int, str]]:
    rows = registry.get("rows") or [
        {"sample": index, "id": path.name.removesuffix(".json")}
        for index, path in enumerate(sorted((directory / "annotations").glob("*.json")), 1)
    ]
    items, samples = [], {}
    for row in rows:
        samples[int(row["sample"])] = row["id"]
        items.append(
            Item(
                key=row["id"],
                input={
                    "page": row["id"],
                    "sample": row.get("sample"),
                    "image": ref(directory / "images" / row["id"]),
                    "width": row.get("width"),
                    "height": row.get("height"),
                    "attributes": row.get("attributes"),
                    "source_url": row.get("source_url"),
                },
                expected={
                    "annotation": ref(directory / "annotations" / f"{row['id']}.json"),
                    "category_counts": row.get("category_counts"),
                },
                metadata={"sample": row.get("sample"), "license": LICENSE},
            )
        )
    return items, samples


def _baseline_run(directory: Path) -> Run | None:
    path = directory / "baseline.json"
    if not path.is_file():
        return None
    baseline = read_json(path)
    rows = [
        Row(
            item_key=row["id"],
            output={key: row.get(key) for key in (*BASELINE_SCORES, "render_png_bytes", "render_sha256", "input_kind")},
            scores={key: row.get(key) for key in BASELINE_SCORES},
            metadata={"status": "complete", "elapsed_seconds": row.get("elapsed_seconds")},
            wall_ms=(row.get("elapsed_seconds") or 0) * 1000,
            name=f"{DEV}/{row['id']}/baseline",
        )
        for row in baseline.get("rows", [])
    ]
    return Run(
        name=f"baseline pdfust-{baseline.get('pdfust_version')}",
        description=(
            "Image-carrier PDF baseline: native text/table/image/Markdown counts on image-only pages. "
            "A CPU measurement, not an OCR accuracy score."
        ),
        rows=rows,
        metadata={
            "run_file": rel(path),
            **scalars({k: v for k, v in baseline.items() if k != "rows"}),
        },
        scores={
            "pages": len(rows),
            "pages_with_native_text": sum(bool(row.get("native_text_characters")) for row in baseline.get("rows", [])),
        },
        started=mtime(path),
    )


def _ocr_runs(directory: Path, samples: dict[int, str]) -> list[Run]:
    path = directory / "ocr-admission" / "scores.json"
    if not path.is_file():
        return []
    by_edge: dict[int, list[dict[str, Any]]] = {}
    for record in read_json(path):
        by_edge.setdefault(int(record["edge"]), []).append(record)
    runs = []
    for edge, records in sorted(by_edge.items()):
        rows = []
        for record in records:
            score = record.get("score") or {}
            bags = score.get("character_bags") or {}
            blocks = score.get("text_blocks") or 0
            row_scores: dict[str, Any] = {
                "completed": record.get("status") == "complete",
                "words": record.get("words"),
                "characters": record.get("characters"),
                "text_blocks": score.get("text_blocks"),
                "covered_text_blocks": score.get("spatially_covered_text_blocks"),
                "unassigned_words": score.get("unassigned_words"),
                "ocr_seconds": record.get("ocr_seconds"),
                "peak_rss_mib": record.get("peak_rss_mib"),
            }
            if blocks:
                row_scores["text_block_coverage"] = (score.get("spatially_covered_text_blocks") or 0) / blocks
            for form in ("strict", "nfkc"):
                values = bags.get(form) or {}
                row_scores[f"{form}.character_bag_recall"] = values.get("character_bag_recall")
                row_scores[f"{form}.character_bag_precision"] = values.get("character_bag_precision")
            page = samples.get(int(record["sample"]), f"sample-{record['sample']}")
            rows.append(
                Row(
                    item_key=page,
                    output={
                        "observed_sha256": record.get("observed_sha256"),
                        "words": record.get("words"),
                        "characters": record.get("characters"),
                        "observed": ref(directory / "ocr-admission" / f"s{record['sample']}-e{edge}" / "observed.json"),
                    },
                    scores=row_scores,
                    metadata={
                        "status": record.get("status"),
                        "sample": record.get("sample"),
                        "edge": edge,
                        "cpu_seconds": record.get("cpu_seconds"),
                        "peak_rss_mib": record.get("peak_rss_mib"),
                        **scalars(record.get("initialization") or {}, "initialization."),
                        "metric_limit": score.get("metric_limit"),
                    },
                    wall_ms=(record.get("ocr_seconds") or 0) * 1000,
                    name=f"{DEV}/{page}/ocr-e{edge}",
                )
            )
        scored = [r for r in rows if r.scores.get("nfkc.character_bag_recall") is not None]
        runs.append(
            Run(
                name=f"ocr-admission e{edge}",
                description=(
                    f"Native PP-OCRv6-small OCR at max edge {edge}px on four metadata-selected pages; bbox-center "
                    "block coverage and per-block character bags (not CER, not reading order)"
                ),
                rows=rows,
                metadata={"edge": edge, "run_file": rel(path), "summary_check": "not-retained"},
                scores={
                    "pages": len(rows),
                    "completed": sum(bool(r.scores["completed"]) for r in rows),
                    "covered_text_blocks": sum(r.scores.get("covered_text_blocks") or 0 for r in rows),
                    "text_blocks": sum(r.scores.get("text_blocks") or 0 for r in rows),
                    "mean_nfkc_character_bag_recall": (
                        sum(float(r.scores["nfkc.character_bag_recall"] or 0) for r in scored) / len(scored)
                        if scored
                        else None
                    ),
                    "ocr_seconds_total": sum(r.scores.get("ocr_seconds") or 0 for r in rows),
                },
                started=mtime(path),
            )
        )
    return runs


def _training(artifacts: Path) -> Experiment | None:
    directory = guard(artifacts / TRAINING)
    geometry_path = directory / "geometry-frozen.json"
    if not geometry_path.is_file():
        return None
    registry = _registry(artifacts, "omnidoc-training")
    rows = registry.get("rows", [])
    pages = read_json(geometry_path).get("pages", [])
    blocks = {page.get("id") or page.get("source_id"): len(page.get("blocks") or []) for page in pages}
    items = [
        Item(
            key=row["training_id"],
            input={
                "reference": row["id"],
                "image": ref(directory / "images" / row["id"]),
                "attributes": row.get("attributes"),
                "category_counts": row.get("category_counts"),
            },
            expected={
                "annotation": ref(directory / "annotations" / f"{row['id']}.json"),
                "geometry_sha256": row.get("geometry_sha256"),
                "geometry_blocks": blocks.get(row["id"]),
            },
            metadata={"split": "TRAINING", "license": LICENSE},
        )
        for row in rows
    ]
    known = {item.key for item in items}
    runs = []
    for label, folder, key in (("synthetic-v2", "synthetic-v3", "v2"), ("synthetic-v3", "synthetic-v3", "v3"),
                               ("synthetic-v3.1", "synthetic-v3.1", "v3")):  # fmt: skip
        manifest_path = directory / folder / "manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = read_json(manifest_path)
        audit_path = directory / label / "geometry-audit.json"
        audit = {row["training_id"]: row for row in read_json(audit_path)} if audit_path.is_file() else {}
        run_rows = []
        for row in manifest.get("rows", []):
            if row["training_id"] not in known:
                continue
            ink = (row.get("ink_comparison") or {}).get(key) or {}
            metadata = row.get("metadata") or {}
            text = [page.get("text") or {} for page in metadata.get("pages", [])]
            checked = audit.get(row["training_id"])
            current = label != "synthetic-v2"
            run_rows.append(
                Row(
                    item_key=row["training_id"],
                    output={
                        "pdf": ref(directory / label / f"{row['training_id']}.pdf"),
                        **({"pdf_sha256": row.get("pdf_sha256")} if current else {}),
                        "ink": ink,
                    },
                    scores={
                        "tile_dark_fraction_mae": ink.get("tile_dark_fraction_mae"),
                        "absolute_dark_fraction_error": ink.get("absolute_dark_fraction_error"),
                        **(
                            {
                                "suppressed_blocks": row.get("suppressed_blocks"),
                                "extracted_words": sum(t.get("word_count") or 0 for t in text),
                                "metadata_errors": len(metadata.get("errors") or []),
                                "pdf_bytes": metadata.get("file_bytes"),
                            }
                            if current
                            else {}
                        ),
                        **(
                            {
                                "outside_page_words": len(checked.get("outside_page_word_ids") or []),
                                "masked_words": len(checked.get("masked_word_ids") or []),
                            }
                            if checked
                            else {}
                        ),
                    },
                    metadata={"status": "complete", "split": "TRAINING", "version": label},
                    name=f"{TRAINING}/{row['training_id']}/{label}",
                )
            )
        if not run_rows:
            continue
        maes = [
            r.scores["tile_dark_fraction_mae"] for r in run_rows if r.scores.get("tile_dark_fraction_mae") is not None
        ]
        runs.append(
            Run(
                name=label,
                description=(
                    f"{label} reference-derived TRAINING layouts vs their OmniDocBench reference pages: coarse 16x16 "
                    "dark-ink tile MAE (lower is closer; not semantics, structure, OCR or realism)"
                ),
                rows=run_rows,
                metadata={
                    "manifest": rel(manifest_path),
                    "ink_key": key,
                    "split": "TRAINING",
                    **scalars({k: manifest.get(k) for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes")}),
                    "summary_check": "not-retained",
                },
                scores={
                    "pages": len(run_rows),
                    "mean_tile_dark_fraction_mae": sum(float(v or 0) for v in maes) / len(maes) if maes else None,
                    **{
                        name: sum(float(r.scores.get(name) or 0) for r in run_rows)
                        for name in ("extracted_words", "metadata_errors", "outside_page_words", "masked_words")
                        if any(name in r.scores for r in run_rows)
                    },
                },
                started=mtime(manifest_path),
            )
        )
    return Experiment(
        dataset=f"exp/{TRAINING}/references",
        description=(
            "TRAINING-split OmniDocBench reference pages (research-only license) and their reference-derived "
            "synthetic layout generations. Ink statistics compare coarse occupancy only. Not an evaluation set."
        ),
        items=items,
        runs=runs,
        source=rel(directory),
        labels={"split": "TRAINING", "heldout": False, "license": LICENSE},
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """OmniDocBench DEV page runs, then TRAINING derivative generations."""
    directory = guard(artifacts / DEV)
    if directory.is_dir():
        registry = _registry(artifacts, DEV)
        items, samples = _dev_items(directory, registry)
        runs = [run for run in [_baseline_run(directory)] if run] + _ocr_runs(directory, samples)
        yield Experiment(
            dataset=f"exp/{DEV}/pages",
            description=(
                "Metadata-selected OmniDocBench DEV pages (third-party, research-only; referenced, not inlined). "
                "Runs: image-carrier native baseline counts and native OCR admission at 640/1200px."
            ),
            items=items,
            runs=runs,
            source=rel(directory),
            labels={"split": "DEV", "heldout": False, "license": LICENSE, "revision": registry.get("revision")},
        )
    training = _training(artifacts)
    if training:
        yield training
