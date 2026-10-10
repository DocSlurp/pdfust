"""Freeze fresh metadata-selected confirmation inputs without reading natural answers."""

# Frozen source contracts intentionally use heterogeneous JSON dictionaries.
# ruff: noqa: C901, EM101, TRY003, PLC0415, PLR0912, PLR2004, E501, PERF401
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from bench.feature_cases import page_pdf, text_op
from bench.generalization_corpus import image_pdf, parent_group
from bench.omnidoc_sample import REVISION, SOURCE, fetch
from bench.pipeline_corpus import _table
from bench.silver import canonical, guard_path, sha, write_json

ROOT = Path("/home/dan/code/oss/pylopdf")
P002 = ROOT / "bench/results/pdf-master-artifacts/pipeline-p002"
SEED = "jev-pdf-p003-fresh-confirmation-20261010-v1"
FAMILIES = (
    "wrapped",
    "merged",
    "column-prose",
    "prose-negative",
    "math-inset",
    "multi-table",
    "blank-cells",
    "borderless",
)
EXCLUSIONS = (
    ROOT / "bench/omnidoc-dev/registry.json",
    ROOT / "bench/omnidoc-training/registry.json",
    P002 / "selection-frozen.json",
    P002 / "corpus-r2/manifest.json",
    P002 / "ocr-evidence/selection-frozen.json",
    P002 / "private-provenance.json",
    P002 / "corpus-r2/private-provenance.json",
)


def metadata(raw: bytes) -> list[dict[str, Any]]:
    """Project only page metadata and category counts; never inspect HTML/poly/text."""
    result = []
    for row in json.loads(raw):
        info = row["page_info"]
        identifier = info["image_path"]
        if not isinstance(identifier, str) or Path(identifier).name != identifier:
            raise ValueError("Expected a basename source identifier")
        result.append(
            {
                "source_id": identifier,
                "source_parent_group": parent_group(identifier),
                "width": info["width"],
                "height": info["height"],
                "attributes": info["page_attribute"],
                "category_counts": dict(Counter(b["category_type"] for b in row["layout_dets"])),
            }
        )
    if len({r["source_id"] for r in result}) != len(result):
        raise ValueError("Duplicate public source identifiers")
    return result


def exclusions(paths: tuple[Path, ...] = EXCLUSIONS) -> dict[str, Any]:
    """Use only authorized unprotected ID mappings, with OCR subset proof."""
    identifiers: set[str] = set()
    groups: set[str] = set()
    files = []
    corpus_ids: set[str] = set()
    ocr_ids: set[str] = set()
    opaque: set[str] = set()
    pdf_hashes: set[str] = set()
    for path in paths:
        raw = guard_path(path).read_bytes()
        value = json.loads(raw)
        files.append({"path": str(path), "sha256": sha(raw)})
        if isinstance(value, list):
            for row in value:
                source_id = row.get("source_id")
                if source_id:
                    identifiers.add(source_id)
                group = row.get("source_parent_group")
                if group:
                    groups.add(group)
                source_case = row.get("source_case", "")
                if source_case.startswith("omni/"):
                    identifiers.add(source_case[5:])
        else:
            identifiers.update(value.get("source_ids", []))
            identifiers.update(r["id"] for r in value.get("rows", []))
            for row in value.get("pages", []):
                opaque.add(row["id"])
                pdf_hashes.add(row["pdf_sha256"])
                if path.parent.name == "corpus-r2":
                    corpus_ids.add(row["id"])
                if path.parent.name == "ocr-evidence":
                    ocr_ids.add(row["id"])
                if row.get("source_id"):
                    identifiers.add(row["source_id"])
                if row.get("source_parent_group"):
                    groups.add(row["source_parent_group"])
    if not ocr_ids <= corpus_ids:
        raise ValueError("OCR selection not covered by authorized corpus provenance")
    groups.update(g for identifier in identifiers if (g := parent_group(identifier)) is not None)
    return {
        "source_ids": sorted(identifiers),
        "source_parent_groups": sorted(groups),
        "opaque_page_ids": sorted(opaque),
        "pdf_hashes": sorted(pdf_hashes),
        "files": files,
        "ocr_subset_verified": True,
    }


def features(row: dict[str, Any]) -> set[str]:
    """Balance declared classification metadata only."""
    attr, cats = row["attributes"], row["category_counts"]
    return {
        *(f"{k}:{attr.get(k, 'unknown')}" for k in ("data_source", "language", "layout")),
        *(f"category:{k}" for k in cats),
        f"math-density:{min(3, cats.get('equation_isolated', 0))}",
    }


def select(rows: list[dict[str, Any]], excluded: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select exact quotas with known distinct parents and deterministic hash ties."""
    ids, groups = set(excluded["source_ids"]), set(excluded["source_parent_groups"])
    eligible = [
        r
        for r in rows
        if r["source_parent_group"] is not None and r["source_id"] not in ids and r["source_parent_group"] not in groups
    ]
    coverage: set[str] = set()
    selected = []
    counts = Counter(min(2, r["category_counts"].get("table", 0)) for r in eligible)
    for density, quota in ((2, 12), (1, 12), (0, 8)):
        pool = sorted(
            (r for r in eligible if min(2, r["category_counts"].get("table", 0)) == density),
            key=lambda r: sha((SEED + r["source_id"]).encode()),
        )
        for _ in range(quota):
            candidates = [r for r in pool if r["source_parent_group"] not in groups]
            if not candidates:
                raise ValueError("Insufficient known-parent metadata quota; no relaxation permitted")
            winner = max(candidates, key=lambda r: len(features(r) - coverage))
            selected.append(winner)
            groups.add(winner["source_parent_group"])
            coverage.update(features(winner))
    return selected, {
        "eligible_density_counts": dict(counts),
        "unknown_parent_rejected": sum(r["source_parent_group"] is None for r in rows),
        "selected_distinct_parent_count": len({r["source_parent_group"] for r in selected}),
    }


def plans() -> list[dict[str, Any]]:
    """Declare new operator designs and numeric/text seeds before rendering."""
    result = []
    for family in FAMILIES:
        for variant in range(2):
            token = sha(f"{SEED}/{family}/{variant}".encode())
            result.append(
                {
                    "name": f"confirmation-{family}-{variant}",
                    "family": family,
                    "variant": variant,
                    "seed_sha256": token,
                    "label_token": "Trial " + token[:7].upper(),
                    "numeric_seed": 10000 + int(token[:16], 16) % 80000,
                    "hypothesis": {
                        "wrapped": "Physical continuation lines must stay in their logical cell.",
                        "merged": "Merged anchors must not duplicate subordinate slots.",
                        "column-prose": "Prose columns beside a table must remain outside table cells.",
                        "prose-negative": "Aligned prose and decorations must not become tables.",
                        "math-inset": "Formula inset and nearby prose must not change table membership.",
                        "multi-table": "Separate table regions must retain independent row boundaries.",
                        "blank-cells": "Blank cell positions must survive without shifting later values.",
                        "borderless": "Aligned cell geometry must work without vector dividers.",
                    }[family],
                }
            )
    return result


def authored(plan: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:
    """Render new authored operators and separate construction references."""
    family, variant, seed = plan["family"], plan["variant"], plan["numeric_seed"]
    ops = [
        text_op(plan["label_token"], 40, 752, size=16),
        text_op("Independent confirmation material", 40, 729, size=10),
    ]
    targets = []
    if family == "prose-negative":
        for column in range(2):
            for row in range(14):
                ops.append(
                    text_op(f"Observation {seed + row}: stable field", 42 + column * 275, 694 - row * 26, size=9)
                )
        ops += ["0.65 G 35 712 m 576 712 l S", "36 285 540 421 re S", "0 G"]
    else:
        count = 2 if family == "multi-table" else 1
        for table_index in range(count):
            cols, rows = (3 if family == "column-prose" else 4), 5 + variant
            left, right = 40, 340 if family == "column-prose" else 572
            top, lead = 685 - table_index * 290, 39 if family == "wrapped" else 30
            width = (right - left) / cols
            values: list[list[str | None]] = [[f"Field {c + 1}" for c in range(cols)]]
            values += [
                [
                    f"Item {seed + r}" if c == 0 else f"{seed + table_index * 977 + r * 31 + c * 17}.{(r + c) % 10}"
                    for c in range(cols)
                ]
                for r in range(1, rows)
            ]
            if family == "wrapped":
                for r in range(1, rows):
                    values[r][0] = f"Item {seed + r} continued note"
            if family == "blank-cells":
                for r in range(1, rows):
                    values[r][(r + variant) % cols] = ""
            merges = ((0, 0, 1, 2), (2, 2, 2, 1)) if family == "merged" else ()
            if merges:
                values[0][0] = f"Group {seed}"
                values[2][2] = f"Shared {seed + 61}"
            target = _table(values, merges)
            target["bbox"] = [left, 792 - top, right, 792 - top + rows * lead]
            targets.append(target)
            if family != "borderless":
                # Missing divider segments follow declared merge slots exactly.
                for r in range(rows + 1):
                    for c in range(cols):
                        if any(mr < r < mr + rs and mc <= c < mc + cs for mr, mc, rs, cs in merges):
                            continue
                        ops.append(
                            f"{left + c * width} {top - r * lead} m {left + (c + 1) * width} {top - r * lead} l S"
                        )
                for c in range(cols + 1):
                    for r in range(rows):
                        if any(mc < c < mc + cs and mr <= r < mr + rs for mr, mc, rs, cs in merges):
                            continue
                        ops.append(
                            f"{left + c * width} {top - r * lead} m {left + c * width} {top - (r + 1) * lead} l S"
                        )
            for r, cells in enumerate(target["values"]):
                for c, value in enumerate(cells):
                    if not value:
                        continue
                    fragments = value.split(" continued ") if family == "wrapped" and r and c == 0 else [value]
                    if len(fragments) == 2:
                        fragments[1] = "continued " + fragments[1]
                    for line, fragment in enumerate(fragments):
                        ops.append(text_op(fragment, left + c * width + 4, top - r * lead - 15 - line * 12, size=8))
        if family == "column-prose":
            for r in range(12):
                ops.append(text_op(f"Outside note {seed + r}", 370, 674 - r * 23, size=9))
        if family == "math-inset":
            ops += [
                "38 300 255 115 re S",
                text_op(f"Inset derivation {seed}", 46, 392, size=10),
                text_op("f(x) = a*x^2 + b*x + c", 46, 365, size=11),
                text_op("Integral limits: 0 to 1", 46, 340, size=10),
            ]
    ops.append(text_op("End of independent material.", 40, 72, size=9))
    return page_pdf("\n".join(ops)), targets


def freeze(output: Path, annotation: Path = P002 / "OmniDocBench.json") -> dict[str, Any]:
    """Freeze metadata selection and construction plans before public acquisition."""
    output = guard_path(output)
    if (output / "selection-frozen.json").exists():
        raise ValueError("Choose a new output directory; selection already frozen")
    output.mkdir(parents=True, exist_ok=True)
    raw = guard_path(annotation).read_bytes()
    excluded = exclusions()
    selected, diagnostics = select(metadata(raw), excluded)
    value = {
        "schema": 1,
        "seed": SEED,
        "split": "DEV-confirmation",
        "revision": REVISION,
        "source": SOURCE,
        "annotation_path": str(annotation),
        "annotation_sha256": sha(raw),
        "exclusions": excluded,
        "selected": selected,
        "synthetic_plans": plans(),
        "diagnostics": diagnostics,
        "recognition_answers_used": False,
        "selection_policy": "12 multi-table,12 single-table,8 negative; known disjoint filename parents; greedy metadata coverage/hash ties; reject unknown parents; no relaxation",
    }
    write_json(output / "selection-frozen.json", value)
    return value


def build(output: Path) -> dict[str, Any]:
    """Acquire at most four public images concurrently, then freeze all source bytes."""
    from PIL import Image

    import pylopdf

    output = guard_path(output)
    if (output / "manifest.json").exists():
        raise ValueError("Existing manifest frozen; do not regenerate")
    raw = (output / "selection-frozen.json").read_bytes()
    selection = json.loads(raw)
    if selection["seed"] != SEED or selection["revision"] != REVISION:
        raise ValueError("Unexpected selection policy")
    if sha(Path(selection["annotation_path"]).read_bytes()) != selection["annotation_sha256"]:
        raise ValueError("Public annotation input changed")
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(
            pool.map(
                lambda r: fetch("images/" + r["source_id"], output / "images" / r["source_id"]), selection["selected"]
            )
        )
    fetch("README.md", output / "dataset-card.md")
    (output / "pdfs").mkdir(exist_ok=True)
    pages, provenance, construction = [], [], []

    def add(data: bytes, name: str, family: str, cohort: str, details: dict[str, Any]) -> str:
        digest = sha(data)
        if digest in selection["exclusions"]["pdf_hashes"]:
            raise ValueError("New source duplicates a known input PDF")
        path = output / "pdfs" / (digest + ".pdf")
        path.write_bytes(data)
        identifier = "p" + sha(canonical([SEED, name]))[:20]
        if identifier in selection["exclusions"]["opaque_page_ids"]:
            raise ValueError("New page identity duplicates a known page")
        with pylopdf.Document(stream=data) as doc:
            size = list(doc[0].rect)
            preview = doc[0].render(dpi=72)
        (output / "previews").mkdir(exist_ok=True)
        preview_path = output / "previews" / (identifier + ".png")
        preview_path.write_bytes(preview)
        pages.append(
            {
                "id": identifier,
                "pdf_path": str(path),
                "pdf_sha256": digest,
                "page_number": 0,
                "family": family,
                "cohort": cohort,
                "input_kind": "official_page_image_in_lossless_pdf_carrier"
                if cohort == "omnidoc"
                else "authored_native_pdf",
                "label_status": "independent references pending"
                if cohort == "omnidoc"
                else "construction references separately frozen",
                "pilot": False,
                "source_display_viewport": size,
                "preview_sha256": sha(preview),
            }
        )
        provenance.append({"id": identifier, "source_case": name, **details})
        return identifier

    for row in selection["selected"]:
        image = output / "images" / row["source_id"]
        with Image.open(image) as pixels:
            if pixels.size != (row["width"], row["height"]):
                raise ValueError("Actual public image dimensions differ from metadata")
        n = row["category_counts"].get("table", 0)
        add(
            image_pdf(image, row["width"] * 0.36, row["height"] * 0.36),
            "omni/" + row["source_id"],
            "omni/" + ("multiple-table" if n > 1 else "single-table" if n else "no-table"),
            "omnidoc",
            {
                **row,
                "source": SOURCE,
                "revision": REVISION,
                "image_sha256": sha(image.read_bytes()),
                "annotation_path": selection["annotation_path"],
                "annotation_sha256": selection["annotation_sha256"],
                "annotation_to_display": {
                    "scale_x": 0.36,
                    "scale_y": 0.36,
                    "offset_x": 0,
                    "offset_y": 0,
                    "rotation": 0,
                },
                "license": "Research purposes only; not for commercial use",
                "original_native_pdf_available": False,
            },
        )
    for plan in selection["synthetic_plans"]:
        data, targets = authored(plan)
        identifier = add(
            data,
            plan["name"],
            "authored/" + plan["family"],
            "authored",
            {
                "construction_plan": plan,
                "license": "Repository-authored; repository MIT license",
                "reference_basis": "new construction operators and cell matrices",
            },
        )
        construction.append({"id": identifier, "tables": targets, "structural_scored": True})
    identity_input = {
        "schema": 2,
        "identity_basis": "source-only-confirmation-v1",
        "selection_sha256": sha(raw),
        "pages": [{k: v for k, v in p.items() if k != "pdf_path"} for p in pages],
    }
    identity = sha(canonical(identity_input))
    manifest = {
        **identity_input,
        "pages": pages,
        "dataset_sha256": identity,
        "split": "DEV",
        "path_convention": "absolute",
        "model_fields": ["id", "pdf_path", "pdf_sha256", "page_number"],
        "reference_status": "natural targets pending independent scorer; no runtime manifest mutation",
    }
    write_json(output / "manifest.json", manifest)
    write_json(output / "private-provenance.json", provenance)
    write_json(output / "construction-targets.json", {"schema": 1, "pages": construction, "dataset_sha256": identity})
    receipt = {
        "schema": 1,
        "dataset_sha256": identity,
        "manifest_sha256": sha((output / "manifest.json").read_bytes()),
        "selection_sha256": sha(raw),
        "provenance_sha256": sha((output / "private-provenance.json").read_bytes()),
        "construction_targets_sha256": sha((output / "construction-targets.json").read_bytes()),
        "helper_sha256": sha(Path(__file__).read_bytes()),
        "reference_access": "none for natural inputs; authored construction only",
        "pages": len(pages),
    }
    write_json(output / "source-freeze.json", receipt)
    return receipt


def main() -> None:
    """Run source-only freeze and optional public acquisition."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    started, cpu = time.perf_counter(), time.process_time()
    if args.freeze:
        freeze(args.output)
    if args.build:
        build(args.output)
    write_json(
        args.output / "resources.json",
        {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Linux self process getrusage lifetime RSS/process_time; up to4 public-download threads; one CPU rendering process; contended; no GPU/hosted inference; no RSS sampling",
        },
    )


if __name__ == "__main__":
    main()
