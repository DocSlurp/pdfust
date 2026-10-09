"""Pinned, disjoint OmniDocBench TRAINING references and authored layout derivatives."""

# ruff: noqa: EM101, TRY003, E501, PLC0415, C901, PLR0912
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import textwrap
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

REVISION = "aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec"
SOURCE = "https://huggingface.co/datasets/opendatalab/OmniDocBench"
SEED = "jev-pdf-omnidoc-training-layout-v1"
LICENSE = "Research purposes only; not for commercial use; inherited by reference-derived synthetic pages"


def digest(data: bytes) -> str:
    """Return a content identity."""
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    """Serialize frozen contracts deterministically."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def parent_group(identifier: str) -> str | None:
    """Infer a filename parent only for an explicit numbered-page suffix."""
    match = re.match(r"^(.*?)_page_\d+\.[^.]+$", identifier)
    return match[1] if match else None


def features(row: dict[str, Any]) -> set[str]:
    """Select by genre/layout/category density; recognition answers are never used."""
    info = row["page_info"]
    attr = info["page_attribute"]
    cats = Counter(b["category_type"] for b in row["layout_dets"])
    return {
        *(f"{k}:{attr.get(k, 'unknown')}" for k in ("data_source", "language", "layout")),
        *(f"category:{k}" for k in cats),
        f"math-density:{min(3, cats['equation_isolated'])}",
        f"table-density:{min(3, cats['table'])}",
        f"blocks:{min(3, len(row['layout_dets']) // 15)}",
    }


def select_rows(rows: list[dict[str, Any]], excluded: set[str], count: int = 16) -> list[dict[str, Any]]:
    """Exclude known DEV parents and prefer disjoint known parents within TRAINING."""
    excluded_groups = {parent_group(i) for i in excluded} - {None}
    remaining = sorted(
        [
            r
            for r in rows
            if r["page_info"]["image_path"] not in excluded
            and parent_group(r["page_info"]["image_path"]) not in excluded_groups
        ],
        key=lambda r: digest((SEED + r["page_info"]["image_path"]).encode()),
    )
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()
    groups: set[str] = set()
    while len(selected) < count:
        eligible = [r for r in remaining if parent_group(r["page_info"]["image_path"]) not in groups]
        if not eligible:
            raise ValueError("Insufficient disjoint source rows")
        row = max(eligible, key=lambda r: len(features(r) - covered))
        selected.append(row)
        remaining.remove(row)
        covered |= features(row)
        group = parent_group(row["page_info"]["image_path"])
        if group is not None:
            groups.add(group)
    return selected


def geometry(row: dict[str, Any]) -> dict[str, Any]:
    """Project only categories, geometry and correspondence; exclude recognition text."""
    info = row["page_info"]
    width, height = info["width"], info["height"]
    blocks = []
    for index, block in enumerate(row["layout_dets"]):
        poly = block["poly"]
        box = [min(poly[::2]), min(poly[1::2]), max(poly[::2]), max(poly[1::2])]
        blocks.append(
            {
                "source_block_id": block.get("anno_id", f"block-{index}"),
                "category": block["category_type"],
                "bbox": box,
                "normalized_bbox": [box[0] / width, box[1] / height, box[2] / width, box[3] / height],
                "order": block.get("order"),
                "ignored": bool(block.get("ignore", False)),
            }
        )
    return {"source_id": info["image_path"], "split": "TRAINING", "width": width, "height": height, "blocks": blocks}


def fetch(path: str, destination: Path) -> bytes:
    """Read only public pinned HTTPS assets, or reuse retained bytes."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with urlopen(f"{SOURCE}/resolve/{REVISION}/{quote(path, safe='/')}", timeout=45) as response:  # noqa: S310
            data = response.read()
        destination.write_bytes(data)
    return destination.read_bytes()


def acquire(annotation_path: Path, dev_registry: Path, output: Path, registry_path: Path) -> dict[str, Any]:
    """Freeze additional references and geometry contracts, explicitly TRAINING."""
    raw = annotation_path.read_bytes()
    dev = json.loads(dev_registry.read_bytes())
    selected = select_rows(json.loads(raw), {r["id"] for r in dev["rows"]})
    output.mkdir(parents=True, exist_ok=True)
    if registry_path.exists():
        raise ValueError("Training registry already frozen")
    start, cpu = time.perf_counter(), time.process_time()
    entries, contracts = [], []
    for index, row in enumerate(selected):
        identifier = row["page_info"]["image_path"]
        if Path(identifier).name != identifier:
            raise ValueError("Source image identifier is not a basename")
        image = fetch("images/" + identifier, output / "images" / identifier)
        annotation = canonical(row)
        (output / "annotations").mkdir(exist_ok=True)
        (output / "annotations" / (identifier + ".json")).write_bytes(annotation)
        contract = geometry(row)
        contracts.append(contract)
        entries.append(
            {
                "training_id": f"training-{index:03}",
                "id": identifier,
                "split": "TRAINING",
                "source_parent_group": parent_group(identifier),
                "parent_group_status": "filename numbered-page inference"
                if parent_group(identifier)
                else "unknown; no document identity supplied",
                "source_url": f"{SOURCE}/resolve/{REVISION}/images/{quote(identifier)}",
                "image_sha256": digest(image),
                "image_bytes": len(image),
                "annotation_sha256": digest(annotation),
                "geometry_sha256": digest(canonical(contract)),
                "width": row["page_info"]["width"],
                "height": row["page_info"]["height"],
                "attributes": row["page_info"]["page_attribute"],
                "category_counts": dict(sorted(Counter(b["category_type"] for b in row["layout_dets"]).items())),
                "reference_pdf_metadata": {
                    "pdf_version": None,
                    "reason": "official page image; original PDF unavailable",
                },
                "derived_split": "TRAINING",
                "license": LICENSE,
            }
        )
    (output / "geometry-frozen.json").write_bytes(canonical({"schema": 1, "split": "TRAINING", "pages": contracts}))
    registry = {
        "schema": 1,
        "split": "TRAINING",
        "purpose": "reference-derived training layouts; never independent evaluation",
        "dataset": "opendatalab/OmniDocBench",
        "revision": REVISION,
        "source": SOURCE,
        "annotation_sha256": digest(raw),
        "excluded_dev_registry_sha256": digest(dev_registry.read_bytes()),
        "license": LICENSE,
        "license_source": f"{SOURCE}/blob/{REVISION}/README.md",
        "selection": {
            "seed": SEED,
            "count": len(entries),
            "recognition_text_used": False,
            "rule": "greedy metadata/category-density coverage, hashed ties, exclude DEV IDs and known filename parents",
        },
        "parent_separation_limit": "UUID-style filenames have unknown parents; document separation cannot be guaranteed",
        "geometry_sha256": digest((output / "geometry-frozen.json").read_bytes()),
        "rows": entries,
        "preparation": {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu},
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    return registry


FICTION = (
    "The harbor workshop tested a quiet sensor near the eastern pier. Its reading remained stable while the crew adjusted the copper frame. ",
    "Aster Cooperative opened a small archive beside the orchard. Volunteers compared seasonal records and repaired the shelves before the evening meeting. ",
    "The observatory team reviewed a fictional series of measurements. Clear intervals supported a revised schedule for the next instrument check. ",
    "Local planners discussed a new path through the meadow. They recorded several options and agreed to inspect drainage after the spring rain. ",
)
SYNTHETIC_DESIGN = {
    "version": 2,
    "split": "TRAINING",
    "page_width_points": 612,
    "text": "new fictional English prose; no reference recognition strings consumed",
    "tables": "authored 3-column 3-to-8-row complete vector grids inside annotated table boxes",
    "figures": "procedural RGB geometric illustrations; no reference photographs",
    "math": "authored ASCII algebra expressions; approximate geometry, not original formula transcription",
    "noise": "none injected; reference scan/font/language realism not claimed",
}


def synthetic_recipe(contract: dict[str, Any], index: int) -> dict[str, Any]:
    """Generate fresh content using only a frozen reference geometry contract."""
    scale = 612 / contract["width"]
    height = contract["height"] * scale
    blocks = []
    for n, source in enumerate(contract["blocks"]):
        box = [v * scale for v in source["bbox"]]
        x0, y0, x1, y1 = box
        if x1 <= x0 or y1 <= y0:
            continue
        category = source["category"]
        record = {"source_block_id": source["source_block_id"], "category": category, "bbox": box}
        if category == "table":
            rows = max(3, min(8, int((y1 - y0) / 15)))
            values = [["Location", "Count", "Shift"]]
            values += [[f"Pier {r}", str(17 + index + r * 3), str(2 + r)] for r in range(1, rows)]
            record.update(values=values, rows=rows, columns=3)
        elif category in ("figure", "chart_mask", "organic_chemical_formula_mask", "algorithm_mask"):
            record.update(procedural_seed=index * 1000 + n)
        else:
            size = max(3.5, min(10, (x1 - x0) / 32, (y1 - y0) * 0.65))
            if category == "title":
                text = ("Harbor dispatch", "Seasonal notes", "Instrument review")[n % 3]
                size = max(4, min(22, (y1 - y0) / 2, (x1 - x0) / 16))
            elif category.startswith("equation"):
                text = ("u(t) = 3t + 7", "a^2 + b^2 = c^2", "f(x) = x / (1 + x^2)")[n % 3]
            elif category in ("header", "footer", "page_number"):
                text = "Aster record " + str(index + 1)
            elif category.startswith("code"):
                text = "value = sample + offset; return value; " * 20
            else:
                text = FICTION[(index + n) % len(FICTION)] * 200
            if category.startswith("equation") or category in ("header", "footer", "page_number"):
                size = min(size, max(1, (x1 - x0) / (len(text) * 0.6)))
            width_chars = max(2, int((x1 - x0) / (size * 0.6)))
            max_lines = max(1, int((y1 - y0) / (size * 1.18)))
            lines = textwrap.wrap(text, width=width_chars)[:max_lines]
            record.update(lines=lines, font_size=size, leading=size * 1.18)
        blocks.append(record)
    return {
        "training_id": f"training-{index:03}",
        "source_id": contract["source_id"],
        "split": "TRAINING",
        "width": 612,
        "height": height,
        "blocks": blocks,
    }


def build(output: Path, registry_path: Path) -> dict[str, Any]:
    """Build authored derivatives after geometry freeze; retain private recipes and measurements."""
    from PIL import Image, ImageDraw

    import pylopdf
    from bench.feature_cases import text_op
    from bench.silver_layouts import _pdf
    from bench.silver_metadata import analyze_pdf
    from bench.silver_structure import process_peak_rss

    contract_raw = (output / "geometry-frozen.json").read_bytes()
    contracts = json.loads(contract_raw)["pages"]
    destination = output / "synthetic-v2"
    if destination.exists():
        raise ValueError("Synthetic version already frozen")
    destination.mkdir()
    recipes = [synthetic_recipe(contract, i) for i, contract in enumerate(contracts)]
    (destination / "design-frozen.json").write_bytes(canonical(SYNTHETIC_DESIGN))
    (destination / "private-authored-targets.json").write_bytes(canonical({"split": "TRAINING", "pages": recipes}))
    start, cpu = time.perf_counter(), time.process_time()
    rows = []
    for recipe in recipes:
        ops = []
        height = recipe["height"]
        for block in recipe["blocks"]:
            x0, y0, x1, y1 = block["bbox"]
            if "values" in block:
                row_height, col_width = (y1 - y0) / block["rows"], (x1 - x0) / 3
                ops.append("0.35 w")
                for r in range(block["rows"] + 1):
                    y = height - y0 - r * row_height
                    ops.append(f"{x0} {y} m {x1} {y} l S")
                for c in range(4):
                    x = x0 + c * col_width
                    ops.append(f"{x} {height - y0} m {x} {height - y1} l S")
                size = max(3, min(9, row_height * 0.6, col_width / 7))
                for r, cells in enumerate(block["values"]):
                    for c, value in enumerate(cells):
                        ops.append(
                            text_op(value, x0 + c * col_width + 2, height - y0 - r * row_height - size - 1, size=size)
                        )
            elif "lines" in block:
                for line, text in enumerate(block["lines"]):
                    ops.append(
                        text_op(
                            text,
                            x0,
                            height - y0 - block["font_size"] - line * block["leading"],
                            size=block["font_size"],
                        )
                    )
        with pylopdf.open(stream=_pdf(["\n".join(ops)], 0, "training", "1.4")) as document:
            page = document[0]
            page.set_mediabox((0, 0, recipe["width"], height))
            for block in recipe["blocks"]:
                if "procedural_seed" not in block:
                    continue
                image = Image.new("RGB", (320, 240), (235, 241, 244))
                draw = ImageDraw.Draw(image)
                seed = block["procedural_seed"]
                for k in range(7):
                    x, y = (seed + k * 43) % 260, (seed * 3 + k * 31) % 180
                    draw.rectangle((x, y, x + 40, y + 40), fill=(40 + k * 22, 110, 170 - k * 10))
                draw.line([(k * 16, 120 + int(65 * math.sin(k / 2))) for k in range(20)], fill=(180, 55, 65), width=4)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                page.insert_image(block["bbox"], stream=buffer.getvalue())
            pdf = document.tobytes()
            pdf_path = destination / (recipe["training_id"] + ".pdf")
            pdf_path.write_bytes(pdf)
            render = page.render(dpi=90, background=(255, 255, 255))
            (destination / (recipe["training_id"] + ".png")).write_bytes(render)
            words = [{"id": f"w{n}", "text": w[4], "bbox": list(w[:4])} for n, w in enumerate(page.get_text("words"))]
            (destination / (recipe["training_id"] + "-source.json")).write_bytes(
                canonical({"split": "TRAINING", "words": words, "page_size": list(page.rect)})
            )
        measured = analyze_pdf(pdf)
        row = {
            "training_id": recipe["training_id"],
            "source_id": recipe["source_id"],
            "split": "TRAINING",
            "pdf_sha256": digest(pdf),
            "render_sha256": digest(render),
            "blocks": len(recipe["blocks"]),
            "layout_distance": {
                "normalized_bbox_mean_absolute_error": 0.0,
                "definition": "authored block envelopes vs projected reference envelopes; not measured ink/image similarity",
                "pixel_similarity": None,
                "text_similarity": "intentionally unrelated",
            },
            "correspondence": [
                {"source_block_id": b["source_block_id"], "synthetic_bbox": b["bbox"], "category": b["category"]}
                for b in recipe["blocks"]
            ],
            "metadata": measured,
        }
        rows.append(row)
    rss, tool = process_peak_rss()
    result = {
        "split": "TRAINING",
        "parent_geometry_sha256": digest(contract_raw),
        "design": SYNTHETIC_DESIGN,
        "rows": rows,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"one sequential CPU process; {tool}; no periodic sampling",
    }
    (destination / "manifest.json").write_bytes(canonical(result))
    compact = {
        "split": "TRAINING",
        "parent_geometry_sha256": digest(contract_raw),
        "design": SYNTHETIC_DESIGN,
        "artifact_manifest_sha256": digest((destination / "manifest.json").read_bytes()),
        "rows": [{k: v for k, v in r.items() if k not in ("metadata", "correspondence")} for r in rows],
    }
    registry_path.write_text(json.dumps(compact, indent=2) + "\n")
    return result


def main() -> None:
    """Acquire training references without inference or recognition-answer sampling."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-synthetic", action="store_true")
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--dev-registry", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()
    if args.build_synthetic:
        result = build(args.output, args.registry)
    else:
        if args.annotations is None or args.dev_registry is None:
            parser.error("acquisition requires --annotations and --dev-registry")
        result = acquire(args.annotations, args.dev_registry, args.output, args.registry)
    print(
        json.dumps(
            {
                "pages": len(result["rows"]),
                "geometry_sha256": result.get("geometry_sha256", result.get("parent_geometry_sha256")),
            }
        )
    )


if __name__ == "__main__":
    main()
