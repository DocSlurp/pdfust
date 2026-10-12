"""Pinned, disjoint OmniDocBench TRAINING references and authored layout derivatives."""

# ruff: noqa: EM101, TRY003, E501, PLC0415, C901, PLR0912, ANN401, PLR2004, PLR0911, ISC004, PERF401
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
from functools import lru_cache
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


def build_v2(output: Path, registry_path: Path) -> dict[str, Any]:
    """Build authored derivatives after geometry freeze; retain private recipes and measurements."""
    from PIL import Image, ImageDraw

    import pdfust
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
        with pdfust.open(stream=_pdf(["\n".join(ops)], 0, "training", "1.4")) as document:
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


REALISM_DESIGN = {
    "version": "3.1",
    "split": "TRAINING",
    "authoring_inputs": "frozen envelopes, categories, language/genre, image-only line/grid/color measurements",
    "excluded_inputs": "recognition text, HTML, LaTeX, source prose, source photographs, model outputs",
    "masks": "all *_mask, need_mask, ignored and abandon blocks retained as correspondence but not painted",
    "typography": "measured line density; serif/sans/mono; subset-embedded Noto CJK; upright vertical CJK chains",
    "tables": "image-projection divider hypotheses and authored values; internal structure is approximate",
    "figures": "procedural vector charts and illustrations; no source pixels embedded",
    "limitations": "no handwriting, photograph, exact font, curved baseline or scan-noise reproduction",
    "metrics": "all-page measured dark-ink and nonwhite density differences; not semantic quality",
    "license": LICENSE,
}
CJK_FONT = Path("/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc")


def suppressed(category: str, *, ignored: bool = False) -> bool:
    """Masked answer regions and discarded annotations are not visible content."""
    return ignored or category.endswith("_mask") or category in ("abandon", "need_mask")


def _bands(values: Any, threshold: float) -> list[tuple[int, int]]:
    selected = [int(index) for index, value in enumerate(values) if value > threshold]
    result: list[tuple[int, int]] = []
    for index in selected:
        if result and index <= result[-1][1] + 2:
            result[-1] = (result[-1][0], index)
        else:
            result.append((index, index))
    return result


def reference_style(image: Any, contract: dict[str, Any], attributes: dict[str, Any]) -> dict[str, Any]:
    """Measure pixels as geometry/color only, without OCR or annotation answer fields."""
    import numpy as np

    rgb = np.asarray(image.convert("RGB"))
    scale = 612 / contract["width"]
    blocks = []
    for block in contract["blocks"]:
        x0, y0, x1, y1 = [round(value) for value in block["bbox"]]
        crop = rgb[max(0, y0) : max(y0 + 1, y1), max(0, x0) : max(x0 + 1, x1)]
        if not crop.size:
            blocks.append({"source_block_id": block["source_block_id"], "line_count": 0})
            continue
        gray = crop.mean(axis=2)
        threshold = min(185, float(np.percentile(gray, 85)) - 40)
        ink = gray < threshold
        runs = _bands(ink.mean(axis=1), 0.014)
        # Merge detached accents and punctuation within one projected text line.
        heights = [end - start + 1 for start, end in runs]
        median_height = float(np.percentile(heights, 75)) if heights else 4 / scale
        merged: list[tuple[int, int]] = []
        for start, end in runs:
            detached = end - start + 1 < median_height * 0.45
            previous_detached = bool(merged) and merged[-1][1] - merged[-1][0] + 1 < median_height * 0.45
            if merged and (detached or previous_detached) and start - merged[-1][1] <= max(2, median_height * 0.42):
                merged[-1] = (merged[-1][0], end)
            else:
                merged.append((start, end))
        horizontal = _bands(ink.mean(axis=1), 0.50)
        vertical = _bands(ink.mean(axis=0), 0.55)
        column_ink = ink.copy()
        for start, end in horizontal:
            column_ink[start : end + 1] = False
        column_runs = _bands(column_ink.mean(axis=0), 0.035)
        groups: list[tuple[int, int]] = []
        for start, end in column_runs:
            if groups and start - groups[-1][1] < median_height * 0.75:
                groups[-1] = (groups[-1][0], end)
            else:
                groups.append((start, end))
        dark = crop[ink]
        foreground = np.median(dark, axis=0).tolist() if len(dark) else [30, 30, 30]
        background = np.percentile(crop.reshape(-1, 3), 80, axis=0).tolist()
        blocks.append(
            {
                "source_block_id": block["source_block_id"],
                "line_count": len(merged),
                "line_height_points": median_height * scale,
                "line_centers": [(start + end) * scale / 2 for start, end in merged],
                "horizontal_rules": [(start + end) / 2 / crop.shape[0] for start, end in horizontal],
                "vertical_rules": [(start + end) / 2 / crop.shape[1] for start, end in vertical],
                "column_group_count": len(groups),
                "ink_fraction": float(ink.mean()),
                "foreground": foreground,
                "background": background,
            }
        )
    edge_pixels = np.concatenate(
        (rgb[:3].reshape(-1, 3), rgb[-3:].reshape(-1, 3), rgb[:, :3].reshape(-1, 3), rgb[:, -3:].reshape(-1, 3))
    )
    background = np.median(edge_pixels, axis=0).tolist()
    if min(background) > 220 and max(background) - min(background) < 50:
        background = [255, 255, 255]
    return {
        "source_id": contract["source_id"],
        "genre": attributes.get("data_source", "unknown"),
        "language": attributes.get("language", "unknown"),
        "background": background,
        "blocks": blocks,
        "recognition_used": False,
        "method": "RGB projections and robust color summaries; no OCR",
    }


def _authored_text(index: int, block: int, language: str, category: str, needed: int) -> str:
    if category.startswith("code"):
        return "def summarize(samples):\n    total = sum(samples)\n    count = len(samples)\n    return total / max(count, 1)\nresult = summarize(readings)"
    if category == "equation_caption":
        return f"({2 + block % 7})"
    if category == "equation_explanation":
        return "(Record A)"
    if category.startswith("equation"):
        return ("q = 4t", "r = u/3", "z = 2b")[block % 3]
    if category == "page_number":
        return str(21 + index)
    if "chinese" in language or language == "en_ch_mixed":
        if category == "title":
            return "觀測工作記錄" if language == "traditional_chinese" else "观测工作记录"
        if category in ("header", "footer"):
            return "東岸資料室" if language == "traditional_chinese" else "东岸资料室"
        if "caption" in category:
            return f"图 {block + 1} 季度观测记录"
        if language == "traditional_chinese":
            sentences = (
                "東岸工坊記錄本季水位，工作人員於清晨檢查儀器。",
                "新建倉庫採用木製支架，雨後仍須逐項確認材料狀態。",
                "研究小組比較三次觀測結果，並將異常數值另行登記。",
                "本冊記載虛構村落的日常事務，各項安排由值班人員覆核。",
            )
        else:
            sentences = (
                "东岸工坊记录本季水位，工作人员于清晨检查仪器。",
                "新建仓库采用木制支架，雨后仍须逐项确认材料状态。",
                "研究小组比较三次观测结果，并将异常数值另行登记。",
                "本册记载虚构村落的日常事务，各项安排由值班人员复核。",
            )
        return "".join(sentences[(index + block + n) % len(sentences)] for n in range(max(1, needed // 20 + 1)))
    if category in ("header", "footer"):
        return ("ASTER RESEARCH OFFICE", "Field records | October 2026", "Harbor review")[block % 3]
    if category == "title":
        return ("Site review", "Field notes", "Equipment", "The harbor study")[block % 4]
    if category == "reference":
        authors = ("Avery, L. and Rowan, K.", "Ellis, N. and Vale, R.", "Morgan, S. and Lake, T.")
        return (
            f"{authors[block % 3]} ({2019 + block % 7}). Inspection records for coastal field stations: "
            "a fictional study of sampling and calibration. Aster Technical Archive, "
            f"Series B {8 + block}, 21-34. Revised working paper with observations from the summer field visit."
        )
    subjects = (
        "The harbor team",
        "A visiting engineer",
        "Staff at the eastern depot",
        "The archive committee",
        "The survey group",
        "An independent observer",
        "The evening supervisor",
        "The maintenance office",
    )
    verbs = (
        "checked the water level",
        "replaced a worn support",
        "compared the instrument readings",
        "reviewed the delivery notes",
        "inspected the covered store",
        "recorded the temperature",
        "revised the collection schedule",
        "examined the drainage channel",
    )
    endings = (
        "before the next shift arrived",
        "after the rain had stopped",
        "during the scheduled visit",
        "while the remaining equipment was being cleaned",
        "using the newly approved procedure",
        "with the earlier observations available for comparison",
        "to document the seasonal change",
        "before preparing a revised maintenance plan",
    )
    prose_sentences = []
    for n in range(max(4, needed // 65 + 1)):
        key = index * 41 + block * 17 + n
        prose_sentences.append(f"{subjects[key % 8]} {verbs[(key // 3) % 8]} {endings[(key // 7) % 8]}.")
    return " ".join(prose_sentences)


@lru_cache(maxsize=5)
def _latin_metric_font(name: str) -> Any:
    from PIL import ImageFont

    filename = {
        "helv": "LiberationSans-Regular.ttf",
        "hebo": "LiberationSans-Bold.ttf",
        "tiro": "LiberationSerif-Regular.ttf",
        "tibo": "LiberationSerif-Bold.ttf",
        "cour": "LiberationMono-Regular.ttf",
    }[name]
    return ImageFont.truetype("/usr/share/fonts/liberation/" + filename, 1000)


def _fit_latin_lines(text: str, width: float, size: float, font: str, count: int) -> list[str]:
    metric = _latin_metric_font(font)
    lines: list[str] = []
    current = ""
    for word in text.split():
        joined = (current + " " + word).strip()
        if current and metric.getlength(joined) * size / 1000 > width - 0.2:
            lines.append(current)
            current = word
            if len(lines) == count:
                break
        else:
            current = joined
    if current and len(lines) < count:
        lines.append(current)
    return lines


def realistic_recipe(contract: dict[str, Any], style: dict[str, Any], index: int) -> dict[str, Any]:
    """Create visible content using geometry-only style summaries frozen before rendering."""
    scale = 612 / contract["width"]
    profiles = {profile["source_block_id"]: profile for profile in style["blocks"]}
    blocks = []
    page_cjk = "chinese" in style["language"] or style["language"] == "en_ch_mixed"
    for number, source in enumerate(contract["blocks"]):
        box = [value * scale for value in source["bbox"]]
        x0, y0, x1, y1 = box
        width, height = x1 - x0, y1 - y0
        category = source["category"]
        cjk = page_cjk and not category.startswith(("code", "equation")) and category != "page_number"
        profile = profiles[source["source_block_id"]]
        block = {"source_block_id": source["source_block_id"], "category": category, "bbox": box}
        is_container = category == "list_group" and any(
            other["category"] == "text_block"
            and other["bbox"][0] >= source["bbox"][0] - 2
            and other["bbox"][1] >= source["bbox"][1] - 2
            and other["bbox"][2] <= source["bbox"][2] + 2
            and other["bbox"][3] <= source["bbox"][3] + 2
            for other in contract["blocks"]
        )
        if suppressed(category, ignored=source["ignored"]) or min(width, height) < 1 or is_container:
            block["paint"] = "suppressed-reference-mask-or-discard"
        elif category == "figure":
            block.update(paint="procedural-figure", seed=index * 997 + number)
        elif category == "table":
            horizontal = [v for v in profile.get("horizontal_rules", []) if 0.015 < v < 0.985]
            vertical_rules = [v for v in profile.get("vertical_rules", []) if 0.015 < v < 0.985]
            rows = min(42, max(len(horizontal) + 1, profile.get("line_count", 0), 3))
            cols = min(14, max(len(vertical_rules) + 1, min(10, profile.get("column_group_count", 3)), 2))
            # Internal grid structure is a measured hypothesis, not a transcription.
            values = [["Site", *[f"M{c}" for c in range(1, cols)]]]
            values.extend(
                [f"A{r:02}", *[str(11 + (index * 7 + r * 13 + c * 3) % 89) for c in range(1, cols)]]
                for r in range(1, rows)
            )
            block.update(
                paint="table",
                rows=rows,
                columns=cols,
                values=values,
                horizontal_rules=bool(horizontal),
                vertical_rules=bool(vertical_rules),
            )
        else:
            vertical = cjk and height > width * 4 and style["genre"] == "historical_document"
            vertical_latin = not cjk and width < 12 and height > width * 4
            line_count = min(100, max(1, profile.get("line_count", 1)))
            if vertical:
                size = min(width * 0.85, 12)
                line_count = max(1, int(height / (size * 1.2)))
                leading = size * 1.2
            else:
                leading = height / line_count
                size = min(30, leading / 1.2, max(2, profile.get("line_height_points", 4) * 1.3))
                leading = min(leading, size * 1.4)
                size = min(size, width / (1 if cjk else 1.1))
            font = (
                "cour"
                if category.startswith("code")
                else "helv"
                if style["genre"] in ("PPT2PDF", "magazine")
                else "tiro"
            )
            if category == "title":
                font = "hebo" if font == "helv" else "tibo"
            chars = max(1, int(width / (size * (1.0 if cjk else 0.49))))
            text = _authored_text(index, number, style["language"], category, chars * line_count)
            if vertical_latin:
                text = "Aster field records"
                size = min(width * 0.75, height / (len(text) * 0.58))
                leading = size * 1.2
            if style["genre"] == "PPT2PDF" and category == "header":
                text = "SEASONAL FIELD REVIEW\nHarbor Instruments and Sampling\nMaintenance and Reporting"
                line_count = 3
                size = min(height / 3.6, width / 20)
                leading = size * 1.2
            if category.startswith("equation") or category in ("header", "footer", "page_number", "title"):
                longest = max(len(line) for line in text.splitlines())
                size = min(size, width / max(1, longest * (1 if cjk else 0.58)))
                chars = max(1, int(width / (size * (1.0 if cjk else 0.49))))
            if vertical_latin:
                lines = [text]
            elif vertical:
                lines = list(text[:line_count])
            elif cjk:
                lines = [text[start : start + chars] for start in range(0, min(len(text), chars * line_count), chars)]
            elif category.startswith("code") or "\n" in text:
                lines = text.splitlines()[:line_count]
            else:
                lines = _fit_latin_lines(text, width, size, font, line_count)
            foreground = profile.get("foreground", [20, 20, 20])
            if style["genre"] == "PPT2PDF" and category == "header":
                foreground = [255, 255, 255]
            if category.startswith("code"):
                foreground = [40, 40, 40]
            block.update(
                paint="text",
                lines=lines,
                font_size=size,
                leading=leading,
                font=font,
                cjk=cjk,
                vertical=vertical,
                vertical_latin=vertical_latin,
                color=foreground,
                background=profile.get("background", [255, 255, 255]),
            )
        blocks.append(block)
    return {
        "training_id": f"training-{index:03}",
        "source_id": contract["source_id"],
        "split": "TRAINING",
        "width": 612,
        "height": contract["height"] * scale,
        "genre": style["genre"],
        "language": style["language"],
        "background": style["background"],
        "blocks": blocks,
    }


def _realism_pdf(recipe: dict[str, Any], font_bytes: bytes) -> bytes:
    import pdfust
    from bench.feature_cases import raw_pdf, stream_object, text_op

    height = recipe["height"]
    ops = []

    def rectangle(box: list[float], color: list[float]) -> None:
        x0, y0, x1, y1 = box
        ops.append(f"{' '.join(str(v / 255) for v in color)} rg {x0} {height - y1} {x1 - x0} {y1 - y0} re f 0 g")

    def ellipse(box: list[float], color: list[float]) -> None:
        x0, y0, x1, y1 = box
        cx, cy, rx, ry = (x0 + x1) / 2, height - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        k = 0.55228475
        ops.append(
            f"{' '.join(str(v / 255) for v in color)} rg {cx + rx} {cy} m "
            f"{cx + rx} {cy + k * ry} {cx + k * rx} {cy + ry} {cx} {cy + ry} c "
            f"{cx - k * rx} {cy + ry} {cx - rx} {cy + k * ry} {cx - rx} {cy} c "
            f"{cx - rx} {cy - k * ry} {cx - k * rx} {cy - ry} {cx} {cy - ry} c "
            f"{cx + k * rx} {cy - ry} {cx + rx} {cy - k * ry} {cx + rx} {cy} c f 0 g"
        )

    rectangle([0, 0, 612, height], recipe["background"])
    if recipe["genre"] == "PPT2PDF":
        rectangle([30, height * 0.25, 590, height * 0.75], [221, 221, 251])
        rectangle([238, height * 0.015, 590, height * 0.20], [41, 191, 235])
    if recipe["genre"] == "note":
        rectangle([36, height * 0.09, 580, height * 0.955], [232, 219, 194])
        for y in range(int(height * 0.12), int(height * 0.94), 22):
            ops.append(f"0.72 0.75 0.75 RG .3 w 40 {height - y} m 578 {height - y} l S 0 G")
    font_names = {"helv": "F1", "hebo": "F2", "tiro": "F3", "tibo": "F4", "cour": "F5"}
    for block in recipe["blocks"]:
        x0, y0, x1, y1 = block["bbox"]
        width, bh = x1 - x0, y1 - y0
        paint = block["paint"]
        if paint.startswith("suppressed"):
            # Masks are white in these retained official images, including pink paper.
            if block["category"].endswith("_mask") or block["category"] == "need_mask":
                rectangle(block["bbox"], [255, 255, 255])
            continue
        if paint == "table":
            rows, cols = block["rows"], block["columns"]
            rh, cw = bh / rows, width / cols
            ops.append(".25 w 0 G")
            for row in range(rows + 1):
                if block["horizontal_rules"] or row in (0, 1, rows):
                    y = height - y0 - row * rh
                    ops.append(f"{x0} {y} m {x1} {y} l S")
            if block["vertical_rules"]:
                for col in range(cols + 1):
                    x = x0 + col * cw
                    ops.append(f"{x} {height - y0} m {x} {height - y1} l S")
            size = max(1, min(rh * 0.66, cw / 4.0, 9))
            for row, values in enumerate(block["values"]):
                for col, value in enumerate(values):
                    ops.append(
                        text_op(
                            value,
                            x0 + col * cw + min(1.5, cw * 0.05),
                            height - y0 - row * rh - size,
                            size=size,
                            font="F3",
                        )
                    )
        elif paint == "procedural-figure":
            rectangle(block["bbox"], [255, 255, 255])
            seed = block["seed"]
            if recipe["genre"] == "research_report":
                if seed % 2:
                    points = [
                        (x0 + width * (0.04 + k * 0.10), y1 - bh * (0.2 + ((seed + k * 7) % 17) / 24))
                        for k in range(10)
                    ]
                    ops.append(
                        ".4 .6 .8 RG 1.2 w "
                        f"{points[0][0]} {height - points[0][1]} m "
                        + " ".join(f"{x} {height - y} l" for x, y in points[1:])
                        + " S 0 G"
                    )
                else:
                    for k in range(10):
                        left = x0 + width * (0.06 + k * 0.088)
                        top = y1 - bh * (0.2 + ((seed + k * 7) % 17) / 24)
                        rectangle([left, top, left + width * 0.042, y1 - bh * 0.12], [50, 95, 122])
            elif recipe["genre"] == "magazine":
                # An original instrument assembly drawing replaces a product photo.
                rectangle([x0 + width * 0.13, y0 + bh * 0.58, x0 + width * 0.86, y0 + bh * 0.73], [104, 125, 129])
                rectangle([x0 + width * 0.18, y0 + bh * 0.63, x0 + width * 0.78, y0 + bh * 0.67], [213, 224, 224])
                rectangle([x0 + width * 0.60, y0 + bh * 0.22, x0 + width * 0.82, y0 + bh * 0.61], [45, 67, 73])
                ellipse([x0 + width * 0.55, y0 + bh * 0.20, x0 + width * 0.70, y0 + bh * 0.45], [57, 73, 78])
                ellipse([x0 + width * 0.73, y0 + bh * 0.54, x0 + width * 0.89, y0 + bh * 0.78], [45, 67, 73])
                ellipse([x0 + width * 0.77, y0 + bh * 0.58, x0 + width * 0.85, y0 + bh * 0.74], [201, 220, 220])
                rectangle([x0 + width * 0.30, y0 + bh * 0.46, x0 + width * 0.35, y0 + bh * 0.61], [11, 136, 138])
                rectangle([x0 + width * 0.25, y0 + bh * 0.43, x0 + width * 0.40, y0 + bh * 0.47], [11, 136, 138])
                for k in range(6):
                    rectangle(
                        [
                            x0 + width * (0.62 + k * 0.026),
                            y0 + bh * 0.24,
                            x0 + width * (0.626 + k * 0.026),
                            y0 + bh * 0.52,
                        ],
                        [112, 133, 137],
                    )
            elif recipe["genre"] in ("exam_paper", "colorful_textbook"):
                for r in range(4):
                    for c in range(6):
                        left, top = x0 + c * width / 6, y0 + r * bh / 4
                        rectangle(
                            [left, top, left + width / 6 - 1, top + bh / 4 - 1],
                            [190 + (c % 3) * 20, 215, 215 - (r % 3) * 15],
                        )
                        ellipse(
                            [left + width * 0.025, top + bh * 0.04, left + width * 0.13, top + bh * 0.21],
                            [50 + c * 20, 100 + r * 20, 120],
                        )
            else:
                # New procedural architectural/equipment silhouettes, no copied pixels.
                for k in range(7):
                    left = x0 + width * k / 7
                    top = y0 + bh * (0.20 + ((seed + k * 13) % 9) / 20)
                    rectangle(
                        [left, top, min(x1, left + width * 0.13), y1 - bh * 0.08],
                        [65 + k * 12, 88 + k * 8, 100 + k * 7],
                    )
                    for floor in range(3):
                        rectangle(
                            [
                                left + width * 0.025,
                                top + (y1 - top) * (floor + 1) / 5,
                                left + width * 0.075,
                                top + (y1 - top) * (floor + 1) / 5 + bh * 0.025,
                            ],
                            [210, 222, 218],
                        )
            ops.append(f"0 G .4 w {x0} {height - y1 + bh * 0.08} m {x1} {height - y1 + bh * 0.08} l S")
        elif not block["cjk"]:
            background = block["background"]
            if max(background) - min(background) > 30 and min(background) > 200 and max(background) >= 245:
                rectangle(block["bbox"], background)
            if block.get("vertical_latin"):
                size = block["font_size"]
                ops.append(
                    f"BT /{font_names[block['font']]} {size} Tf 0 1 -1 0 "
                    f"{x1 - size * 0.2} {height - y1 + 0.2} Tm (Aster field records) Tj ET"
                )
                continue
            for n, line in enumerate(block["lines"]):
                # Clip each authored block to prevent envelope collisions.
                ops.append(f"q {x0} {height - y1} {width} {bh} re W n")
                ops.append(f"{' '.join(str(v / 255) for v in block['color'])} rg")
                ops.append(
                    text_op(
                        line,
                        x0,
                        height - y0 - block["font_size"] - n * block["leading"],
                        size=block["font_size"],
                        font=font_names[block["font"]],
                    )
                )
                ops.append("Q")
        elif block["paint"] == "text":
            background = block["background"]
            if max(background) - min(background) > 30 and min(background) > 200 and max(background) >= 245:
                rectangle(block["bbox"], background)
    data = raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 {height}] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R /F4 8 0 R /F5 9 0 R >> >> >>",
            stream_object("\n".join(ops)),
            *[
                f"<< /Type /Font /Subtype /Type1 /BaseFont /{name} /Encoding /WinAnsiEncoding >>"
                for name in ("Helvetica", "Helvetica-Bold", "Times-Roman", "Times-Bold", "Courier")
            ],
        ]
    )
    with pdfust.open(stream=data) as document:
        for block in recipe["blocks"]:
            if block["paint"] == "text" and block["cjk"] and block["lines"]:
                # One embedding per block avoids a separate font program per glyph.
                size = block["font_size"]
                document[0].insert_text(
                    (block["bbox"][0], block["bbox"][1] + size),
                    "\n".join(block["lines"]),
                    fontsize=size,
                    fontbuffer=font_bytes,
                    fontindex=2,
                    color=tuple(v / 255 for v in block["color"]),
                )
        return document.tobytes()


def ink_measure(image: Any) -> dict[str, Any]:
    """Measure actual rendered pixels; differences are diagnostics, not fidelity scores."""
    import numpy as np

    rgb = np.asarray(image.convert("RGB").resize((256, 256))).astype(float)
    gray = rgb.mean(axis=2)
    return {
        "dark_fraction": float((gray < 180).mean()),
        "nonwhite_fraction": float((gray < 245).mean()),
        "tile_dark_fraction": (gray < 180).reshape(16, 16, 16, 16).mean(axis=(1, 3)).tolist(),
    }


def compact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Retain measured comparison fields, omitting verbose font and image records."""
    return {
        **metadata,
        "content": {k: v for k, v in metadata["content"].items() if k != "font_resources"},
        "pages": [{k: v for k, v in page.items() if k != "images"} for page in metadata["pages"]],
    }


def build(output: Path, registry_path: Path) -> dict[str, Any]:
    """Freeze reviewed v3 styles and recipes, then build all derivatives and compare pixels."""
    import numpy as np
    from PIL import Image

    import pdfust
    from bench.silver_metadata import analyze_pdf
    from bench.silver_structure import process_peak_rss

    source_registry = json.loads(Path(__file__).with_name("omnidoc-training").joinpath("registry.json").read_text())
    contract_raw = (output / "geometry-frozen.json").read_bytes()
    if digest(contract_raw) != source_registry["geometry_sha256"]:
        raise ValueError("Frozen parent geometry checksum mismatch")
    if registry_path.exists():
        raise ValueError("Synthetic registry already exists; use a new version path")
    destination = output / f"synthetic-v{REALISM_DESIGN['version']}"
    destination.mkdir(exist_ok=False)
    contracts = json.loads(contract_raw)["pages"]
    font_bytes = CJK_FONT.read_bytes()
    styles, reference_measures = [], []
    start, cpu = time.perf_counter(), time.process_time()
    for contract, record in zip(contracts, source_registry["rows"], strict=True):
        path = output / "images" / contract["source_id"]
        if digest(path.read_bytes()) != record["image_sha256"]:
            raise ValueError("Retained reference image checksum mismatch")
        with Image.open(path) as image:
            styles.append(reference_style(image, contract, record["attributes"]))
            reference_measures.append(ink_measure(image))
    recipes = [
        realistic_recipe(contract, style, index)
        for index, (contract, style) in enumerate(zip(contracts, styles, strict=True))
    ]
    (destination / "generator.py").write_bytes(Path(__file__).read_bytes())
    dependencies = {}
    for filename in ("feature_cases.py", "silver_metadata.py", "silver_structure.py"):
        raw = Path(__file__).with_name(filename).read_bytes()
        (destination / filename).write_bytes(raw)
        dependencies[filename] = digest(raw)
    metric_fonts = {
        str(path): digest(path.read_bytes())
        for path in (
            Path("/usr/share/fonts/liberation") / name
            for name in (
                "LiberationSans-Regular.ttf",
                "LiberationSans-Bold.ttf",
                "LiberationSerif-Regular.ttf",
                "LiberationSerif-Bold.ttf",
                "LiberationMono-Regular.ttf",
            )
        )
    }
    (destination / "design-frozen.json").write_bytes(
        canonical(
            {
                "design": REALISM_DESIGN,
                "font_sha256": digest(font_bytes),
                "generator_sha256": digest(Path(__file__).read_bytes()),
                "dependency_sha256": dependencies,
                "metric_font_sha256": metric_fonts,
            }
        )
    )
    (destination / "style-frozen.json").write_bytes(canonical({"split": "TRAINING", "pages": styles}))
    (destination / "private-authored-targets.json").write_bytes(canonical({"split": "TRAINING", "pages": recipes}))
    rows = []
    for recipe, reference, parent in zip(recipes, reference_measures, source_registry["rows"], strict=True):
        data = _realism_pdf(recipe, font_bytes)
        name = recipe["training_id"]
        (destination / (name + ".pdf")).write_bytes(data)
        with pdfust.open(stream=data) as document:
            page = document[0]
            render = page.render(dpi=90, background=(255, 255, 255))
            (destination / (name + ".png")).write_bytes(render)
            words = [
                {"id": f"w{n}", "text": word[4], "bbox": list(word[:4])}
                for n, word in enumerate(page.get_text("words"))
            ]
            (destination / (name + "-source.json")).write_bytes(
                canonical({"split": "TRAINING", "words": words, "page_size": list(page.rect)})
            )
        current = ink_measure(Image.open(io.BytesIO(render)))
        previous = ink_measure(Image.open(output / "synthetic-v2" / (name + ".png")))
        diagnostics = {}
        for version, measurement in (("v2", previous), ("v3", current)):
            diagnostics[version] = {
                "dark_fraction": measurement["dark_fraction"],
                "nonwhite_fraction": measurement["nonwhite_fraction"],
                "absolute_dark_fraction_error": abs(reference["dark_fraction"] - measurement["dark_fraction"]),
                "tile_dark_fraction_mae": float(
                    np.abs(
                        np.array(reference["tile_dark_fraction"]) - np.array(measurement["tile_dark_fraction"])
                    ).mean()
                ),
            }
        rows.append(
            {
                "training_id": name,
                "source_id": recipe["source_id"],
                "split": "TRAINING",
                "source_parent_group": parent["source_parent_group"],
                "parent_group_status": parent["parent_group_status"],
                "pdf_sha256": digest(data),
                "render_sha256": digest(render),
                "blocks": len(recipe["blocks"]),
                "suppressed_blocks": sum(b["paint"].startswith("suppressed") for b in recipe["blocks"]),
                "font_languages": recipe["language"],
                "reference_ink": {k: v for k, v in reference.items() if k != "tile_dark_fraction"},
                "ink_comparison": diagnostics,
                "metadata": analyze_pdf(data),
            }
        )
    rss, tool = process_peak_rss()
    result = {
        "split": "TRAINING",
        "license": LICENSE,
        "parent_geometry_sha256": digest(contract_raw),
        "design": REALISM_DESIGN,
        "rows": rows,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"sequential CPU; perf_counter/process_time; {tool}; lifetime RSS; no sampling",
    }
    (destination / "manifest.json").write_bytes(canonical(result))
    compact = {
        **result,
        "artifact_manifest_sha256": digest((destination / "manifest.json").read_bytes()),
        "rows": [{**row, "metadata": compact_metadata(row["metadata"])} for row in rows],
    }
    registry_path.write_text(json.dumps(compact, indent=2) + "\n")
    return result


def main() -> None:
    """Acquire training references without inference or recognition-answer sampling."""
    parser = argparse.ArgumentParser(description=__doc__)
    build_mode = parser.add_mutually_exclusive_group()
    build_mode.add_argument("--build-synthetic", action="store_true", help="Build the selected reviewed revision")
    build_mode.add_argument("--build-synthetic-v2", action="store_true", help="Build the earlier comparison scaffold")
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--dev-registry", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()
    if args.build_synthetic_v2:
        result = build_v2(args.output, args.registry)
    elif args.build_synthetic:
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
