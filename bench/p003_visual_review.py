"""Render immutable, offline DEV diagnostics from independently verified evaluations."""

# Artifact schemas are heterogeneous and diagnostic drawing uses explicit pixel bounds.
# ruff: noqa: EM101, TRY003, PLR2004, C901, PLC0415
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import resource
import time
import unicodedata
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from PIL import __version__ as pillow_version

from bench.generalization_scoring import _cells, score_page
from bench.silver import guard_path

COLORS = {"success": (28, 145, 74), "failure": (205, 46, 48), "unscored": (192, 133, 24)}
DEFAULT_IDS = (
    "p1bfa52a41a5e15015698",  # Dense newspaper, 26 annotated tables.
    "p6ef5d3c5c2edb1c109c4",  # Academic two-table page.
    "p1e230b0fd05df7dd5e23",  # Small table.
    "pe87ca2d41151f28dc44c",  # Larger single table.
    "p27ec5aaca0dd08c90360",  # Negative page.
)
FONT = Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc")
LATIN_FONT = Path("/usr/share/fonts/noto/NotoSans-Regular.ttf")
RENDER_SETTINGS = {
    "raster_width": 1600,
    "panel_width": 1800,
    "grid_width": 940,
    "maximum_grid_height": 12000,
    "source_preview_box": [780, 1450],
    "grid_preview_box": [970, 1450],
    "source_table_zoom_box": [760, 1100],
    "source_mask_alpha": 30,
    "cell_font_size": 18,
    "resampling": "Pillow BICUBIC default for RGB resize/thumbnail",
    "format": "RGB PNG",
    "pdf_background_rgb": [255, 255, 255],
    "pillow_version": pillow_version,
    "colors": COLORS,
}


def digest(data: bytes) -> str:
    """Hash an explicit diagnostic dependency."""
    return hashlib.sha256(data).hexdigest()


def read(path: Path, receipts: dict[str, str]) -> dict[str, Any]:
    """Read an explicit guarded artifact and retain its content hash."""
    path = guard_path(path.resolve())
    data = path.read_bytes()
    receipts[str(path)] = digest(data)
    return json.loads(data)


def font(size: int, value: str = "") -> ImageFont.FreeTypeFont:
    """Use a Unicode font suitable for the retained English or CJK text."""
    path = FONT if any(ord(c) >= 0x2E80 for c in value) else LATIN_FONT
    return ImageFont.truetype(str(path), size)


def verdicts(target: dict[str, Any], tables: list[dict[str, Any]], score: dict[str, Any]) -> dict[str, Any]:
    """Use retained one-to-one matches and exact normalized topology/text identities."""
    gold = [_cells(table) for table in target["tables"]]
    actual = [_cells(table) for table in tables]
    inputs = dict.fromkeys(range(len(gold)), "failure")
    outputs: dict[int, dict[tuple[int, int, int, int], str]] = {
        i: dict.fromkeys(cells, "failure") for i, cells in enumerate(actual)
    }
    for pair in score.get("matches", []):
        i, j = pair["target"], pair["prediction"]
        inputs[i] = "success" if gold[i] == actual[j] else "failure"
        outputs[j] = {
            key: "success" if key in gold[i] and gold[i][key] == value else "failure"
            for key, value in actual[j].items()
        }
    paired_predictions = {pair["prediction"] for pair in score.get("matches", [])}
    extra_boxes = {
        i: table["bbox"]
        for i, table in enumerate(tables)
        if i not in paired_predictions and table.get("bbox") is not None
    }
    return {"input_tables": inputs, "output_cells": outputs, "extra_prediction_boxes": extra_boxes}


def lines(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, width: int, size: int = 18) -> int:
    """Draw complete text with measured wrapping."""
    x, y = xy
    face = font(size, value)
    # Wrap by measured width, retaining every character without fabricated content.
    for paragraph in value.split("\n"):
        pending = ""
        for character in paragraph:
            if pending and draw.textlength(pending + character, font=face) > width:
                draw.text((x, y), pending, font=face, fill="#15202b")
                y += size + 6
                pending = ""
            pending += character
        draw.text((x, y), pending, font=face, fill="#15202b")
        y += size + 6
    return y


def measured_wrap(value: str, width: float) -> list[str]:
    """Wrap retained strings by actual font width, keeping short numbers intact."""
    face = font(18, value)
    chunks, pending = [], ""
    for character in value:
        if character == "\n":
            chunks.append(pending)
            pending = ""
            continue
        pending += character
        if face.getlength(pending) <= width or len(pending) == 1:
            continue
        boundary = pending[:-1].rfind(" ") + 1
        boundary = boundary or len(pending) - 1
        chunks.append(pending[:boundary])
        pending = pending[boundary:]
    chunks.append(pending)
    return chunks


def output_grid(
    tables: list[dict[str, Any]],
    marks: dict[str, Any],
    width: int = 940,
    table_indexes: list[int] | None = None,
) -> Image.Image:
    """Draw the actual extracted values and merged spans; these are schematic boxes."""
    face = font(18)
    layouts = []
    total_height = 90
    for index, table in enumerate(tables):
        cells = _cells(table)
        col_width = (width - 30) / table["col_count"]
        heights = [34] * table["row_count"]
        wrapped = {}
        for key in cells:
            r, c, rs, cs = key
            value = table["values"][r][c]
            chunks = measured_wrap(value, col_width * cs - 14)
            wrapped[key] = chunks
            required_height = len(chunks) * 24 + 12
            available_height = sum(heights[r : r + rs])
            if required_height > available_height:
                heights[r] += required_height - available_height
        layouts.append((index, table, col_width, heights, wrapped))
        total_height += sum(heights) + 75
    if total_height > 12000:
        raise ValueError("Extracted table grid exceeds bounded diagnostic canvas")
    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)
    lines(draw, (15, 10), "Actual extracted tables | schematic cells, not physical page boxes", width - 30)
    y = 70
    if not tables:
        lines(draw, (15, y), "No extracted tables. No inferred or invented output.", width - 30)
    for index, table, cw, heights, wrapped in layouts:
        original_index = table_indexes[index] if table_indexes is not None else index
        draw.text(
            (15, y),
            f"Prediction T{original_index}: {table['row_count']} rows x {table['col_count']} columns",
            font=face,
            fill="#15202b",
        )
        y += 34
        offsets = [y]
        for height in heights:
            offsets.append(offsets[-1] + height)
        for key, chunks in wrapped.items():
            r, c, rs, cs = key
            box = (15 + c * cw, offsets[r], 15 + (c + cs) * cw, offsets[r + rs])
            state = marks["output_cells"][index][key]
            color = COLORS[state]
            pale = tuple(round(v * 0.15 + 255 * 0.85) for v in color)
            draw.rectangle(box, fill=pale, outline=color, width=2)
            for row_index, chunk in enumerate(chunks):
                draw.text((box[0] + 5, box[1] + 4 + row_index * 24), chunk, font=font(18, chunk), fill="#15202b")
        y = offsets[-1] + 40
    return image


def paginated_output(tables: list[dict[str, Any]], marks: dict[str, Any]) -> tuple[list[Image.Image], list[list[int]]]:
    """Keep whole actual matrices and original indexes in bounded output pages."""
    try:
        return [output_grid(tables, marks)], [list(range(len(tables)))]
    except ValueError as exc:
        if str(exc) != "Extracted table grid exceeds bounded diagnostic canvas":
            raise
    pages, indexes = [], []
    pieces: list[Image.Image] = []
    current: list[int] = []
    height = 0

    def finish() -> None:
        page = Image.new("RGB", (940, height), "white")
        y = 0
        for piece in pieces:
            page.paste(piece, (0, y))
            y += piece.height
        pages.append(page)
        indexes.append(list(current))

    for index, table in enumerate(tables):
        subset = {"output_cells": {0: marks["output_cells"][index]}}
        piece = output_grid([table], subset, table_indexes=[index])
        if pieces and height + piece.height > RENDER_SETTINGS["maximum_grid_height"]:
            finish()
            pieces, current, height = [], [], 0
        pieces.append(piece)
        current.append(index)
        height += piece.height
    if pieces:
        finish()
    return pages, indexes


def lexical_tokens(value: str) -> list[str]:
    """Retain ordered letter runs, digit runs and punctuation without joining digits."""
    return re.findall(r"[^\W\d_]+|\d+|[^\w\s]|_", unicodedata.normalize("NFC", value))


def column_partition_audit(reference: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    """Describe one fixed contiguous column partition preserving every row and header."""
    result: dict[str, Any] = {"verified": False, "scope": "descriptive lexical audit; primary strict scores unchanged"}
    n, m = reference["col_count"], actual["col_count"]
    if n >= m or m > 12 or reference["row_count"] != actual["row_count"]:
        return result
    # Merged cells require a separate equivalence treatment, not matrix flattening.
    if any(cell is None for row in reference["values"] + actual["values"] for cell in row):
        return result
    for cuts in itertools.combinations(range(1, m), n - 1):
        bounds = (0, *cuts, m)
        groups = [list(range(bounds[i], bounds[i + 1])) for i in range(n)]
        if all(
            lexical_tokens(expected[c]) == lexical_tokens(" ".join(observed[j] for j in group))
            for expected, observed in zip(reference["values"], actual["values"], strict=True)
            for c, group in enumerate(groups)
        ):
            return {
                **result,
                "verified": True,
                "prediction_column_groups": groups,
                "verified_rows_including_header": reference["row_count"],
                "reference_columns": n,
                "prediction_columns": m,
            }
    return result


def differences(target: dict[str, Any], tables: list[dict[str, Any]], score: dict[str, Any]) -> list[dict[str, Any]]:
    """Describe strict mismatches without declaring their semantic importance."""
    result = []
    paired = {pair["target"]: pair["prediction"] for pair in score.get("matches", [])}
    for i, table in enumerate(target["tables"]):
        expected = _cells(table)
        actual = _cells(tables[paired[i]]) if i in paired else {}
        for key in sorted(expected.keys() | actual.keys()):
            a, b = expected.get(key), actual.get(key)
            if a == b:
                continue
            if a is None or b is None:
                reason = "missing table/cell or different span topology"
            elif lexical_tokens(a) == lexical_tokens(b):
                reason = "whitespace-only strict mismatch"
            elif ("$" in a or "\\text" in a) and not ("$" in b or "\\text" in b):
                reason = "reference math markup versus literal output"
            elif a.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")) == b.translate(
                str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
            ):
                reason = "subscript-versus-baseline digit"
            elif "".join(c for c in a if not unicodedata.category(c).startswith("P")) == "".join(
                c for c in b if not unicodedata.category(c).startswith("P")
            ):
                reason = "punctuation-only strict mismatch"
            else:
                reason = "other exact text mismatch"
            result.append(
                {
                    "target_table": i,
                    "prediction_table": paired.get(i),
                    "anchor": key,
                    "expected": a,
                    "actual": b,
                    "reason": reason,
                }
            )
    matched_predictions = set(paired.values())
    for i, table in enumerate(tables):
        if i in matched_predictions:
            continue
        for key, value in sorted(_cells(table).items()):
            result.append(
                {
                    "target_table": None,
                    "prediction_table": i,
                    "anchor": key,
                    "expected": None,
                    "actual": value,
                    "reason": "extra unmatched predicted table",
                }
            )
    return result


def difference_image(rows: list[dict[str, Any]]) -> Image.Image:
    """Show a bounded exact-difference preview; complete details remain in JSON."""
    image = Image.new("RGB", (1500, 130 + min(len(rows), 12) * 140), "white")
    draw = ImageDraw.Draw(image)
    lines(draw, (20, 12), f"Strict mismatch details: {len(rows)} total; first {min(len(rows), 12)} shown", 1460, 24)
    lines(
        draw, (20, 54), "Red means strict reference disagreement. These reasons do not measure semantic severity.", 1460
    )
    for i, row in enumerate(rows[:12]):
        y = 130 + i * 140
        lines(draw, (20, y), f"Gold T{row['target_table']} anchor {row['anchor']} | {row['reason']}", 1460)
        lines(draw, (20, y + 32), f"Expected: {row['expected']!r}", 1460)
        lines(draw, (20, y + 66), f"Actual:   {row['actual']!r}", 1460)
    return image


def render_page(record: dict[str, Any], target: dict[str, Any], marks: dict[str, Any], directory: Path) -> Image.Image:
    """Retain the real full-page raster and translucent gold table overlays."""
    import pylopdf

    with pylopdf.Document(record["pdf_path"]) as document:
        page = document[record["page_number"]]
        rect = page.rect
        pixmap = page.get_pixmap(scale=1600 / rect.width, background=(255, 255, 255))
        original = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples).convert("RGB")
        original.save(directory / "original.png")
        overlay = Image.new("RGBA", original.size)
        draw = ImageDraw.Draw(overlay)
        for i, table in enumerate(target["tables"]):
            box = table.get("bbox")
            if box is None:
                continue
            scaled = tuple(v * original.width / rect.width for v in box)
            color = COLORS[marks["input_tables"][i]]
            draw.rectangle(scaled, fill=(*color, 30), outline=(*color, 240), width=3)
            draw.text((scaled[0], scaled[1]), f"Gold T{i}", font=font(20), fill=(*color, 255))
            # Regional views preserve real page pixels with exactly the same table mask.
            if i < 3:
                crop = original.crop(tuple(round(v) for v in scaled))
                crop.save(directory / f"source-table-{i}.png")
        for i, box in marks["extra_prediction_boxes"].items():
            scaled = tuple(v * original.width / rect.width for v in box)
            color = COLORS["failure"]
            draw.rectangle(scaled, outline=(*color, 255), width=5)
            draw.text((scaled[0], scaled[1]), f"Extra prediction T{i}", font=font(20), fill=(*color, 255))
        marked = Image.alpha_composite(original.convert("RGBA"), overlay).convert("RGB")
        marked.save(directory / "input-overlay.png")
        return marked


def regional_views(  # noqa: PLR0913, PLR0917
    directory: Path,
    tables: list[dict[str, Any]],
    score: dict[str, Any],
    marks: dict[str, Any],
    label: str,
    audits: dict[int, dict[str, Any]] | None = None,
) -> None:
    """Keep dense table source and extracted matrix text readable in separate panels."""
    pairs = {pair["target"]: pair["prediction"] for pair in score.get("matches", [])}
    for target_index in range(3):
        path = directory / f"source-table-{target_index}.png"
        if not path.exists():
            continue
        with Image.open(path) as original:
            source = original.convert("RGB")
        scale = min(760 / source.width, 1100 / source.height)
        source = source.resize((round(source.width * scale), round(source.height * scale)))
        prediction_index = pairs.get(target_index)
        selected = [tables[prediction_index]] if prediction_index is not None else []
        subset = {"output_cells": {0: marks["output_cells"][prediction_index]}} if selected else {"output_cells": {}}
        grid = output_grid(selected, subset, table_indexes=[prediction_index] if prediction_index is not None else [])
        audit = (audits or {}).get(target_index, {})
        top = 205 if audit.get("verified") else 160
        panel = Image.new("RGB", (1800, max(source.height, grid.height) + top + 15), "#f5f7fa")
        draw = ImageDraw.Draw(panel)
        lines(
            draw, (20, 10), f"Gold table T{target_index} source zoom | matched prediction {prediction_index}", 1760, 24
        )
        lines(
            draw,
            (20, 48),
            "Actual source pixels | Green: exact reference match; red: strict reference disagreement; amber: unscored.",
            1760,
        )
        lines(draw, (20, 82), label, 1760, 16)
        if audit.get("verified"):
            lines(
                draw,
                (20, 114),
                f"Accepted alternative column granularity: {audit['reference_columns']} versus "
                f"{audit['prediction_columns']} columns. All {audit['verified_rows_including_header']} rows "
                "including header preserve ordered lexical tokens under one fixed column partition.",
                1760,
                20,
            )
        panel.paste(source, (20, top))
        color = COLORS[marks["input_tables"][target_index]]
        draw.rectangle((20, top, 20 + source.width, top + source.height), outline=color, width=4)
        panel.paste(grid, (810, top))
        panel.save(directory / f"regional-T{target_index}.png")


def detector_inference_size(frozen: dict[str, Any], report: dict[str, Any]) -> int | str:
    """Prefer actual retained worker configuration and reject declared conflicts."""
    declared = frozen["config"].get("detector_inference_size")
    observed = report.get("layout_detector_initialization", {}).get("configuration", {}).get("imgsz")
    if declared is not None and observed is not None and declared != observed:
        raise ValueError("Declared and retained detector inference sizes differ")
    return observed if observed is not None else declared if declared is not None else "unrecorded"


def run(  # noqa: PLR0912
    run_dir: Path, corpus: Path, output: Path, identifiers: list[str], *, supplemental_random40: bool = False
) -> Path:
    """Refresh a completed verified cohort once; identical provenance skips rendering."""
    admitted = "random-office-values40-v1" if supplemental_random40 else "natural16"
    if corpus.name != admitted:
        raise ValueError("Diagnostics require the explicitly admitted DEV corpus")
    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    font_receipts = {str(path): digest(path.read_bytes()) for path in (FONT, LATIN_FONT)}
    receipts.update(font_receipts)
    renderer = {"sha256": digest(Path(__file__).read_bytes()), "settings": RENDER_SETTINGS, "fonts": font_receipts}
    evaluation = read(run_dir / "evaluation.json", receipts)
    evaluated = next(row for row in evaluation["runs"] if row["name"] == run_dir.name)
    if evaluated.get("evaluation_scope") != "complete pipeline":
        raise ValueError("Initial visual workflow requires independently verified complete pipeline scope")
    report_path = guard_path((run_dir / "report.json").resolve())
    report_bytes = report_path.read_bytes()
    if digest(report_bytes) != evaluated["report_sha256"]:
        raise ValueError("Verified report changed; wait for independent re-evaluation")
    receipts[str(report_path)] = evaluated["report_sha256"]
    frozen = read(run_dir / "frozen.json", receipts)
    inference_size = detector_inference_size(frozen, json.loads(report_bytes))
    read(corpus / "manifest.json", receipts)
    targets = read(corpus / "private-targets.json", receipts)
    if (
        evaluated["dataset_sha256"] != targets["dataset_sha256"]
        or evaluated["manifest_sha256"] != receipts[str((corpus / "manifest.json").resolve())]
    ):
        raise ValueError("Evaluation corpus differs from exact supplied DEV corpus")
    if len(identifiers) > 6 or not identifiers or len(set(identifiers)) != len(identifiers):
        raise ValueError("Choose one through six DEV pages")
    records = {row["id"]: row for row in frozen["records"]}
    references = {row["id"]: row for row in targets["pages"]}
    scores = {row["id"]: row for row in evaluated["page_scores"]}
    pages = []
    for identifier in identifiers:
        result = read(run_dir / f"{identifier}-result.json", receipts)
        record, target, retained = records[identifier], references[identifier], scores[identifier]
        pdf = guard_path(Path(record["pdf_path"]).resolve())
        if digest(pdf.read_bytes()) != record["pdf_sha256"]:
            raise ValueError("Input PDF differs from frozen input")
        receipts[str(pdf)] = record["pdf_sha256"]
        tables = result.get("tables", []) if not retained["error"] else []
        replay = score_page(target, tables, status=result["status"])
        if any(replay[key] != value for key, value in retained.items() if key in replay):
            raise ValueError("Retained score differs from exact offline replay")
        pages.append((identifier, record, target, tables, retained, verdicts(target, tables, retained)))
    identity = digest(
        json.dumps({"receipts": receipts, "ids": identifiers, "renderer": renderer}, sort_keys=True).encode()
    )
    batch = guard_path(output.resolve()) / identity[:20]
    if (batch / "provenance.json").exists():
        return batch
    batch.mkdir(parents=True, exist_ok=False)
    panels = []
    findings = []
    for identifier, record, target, tables, score, marks in pages:
        directory = batch / identifier
        directory.mkdir()
        source = render_page(record, target, marks, directory)
        grids, page_indexes = paginated_output(tables, marks)
        grid = grids[0]
        grid.save(directory / "extracted-tables.png")
        for index, output_page in enumerate(grids):
            output_page.save(directory / f"extracted-tables-page-{index + 1}.png")
        (directory / "output-pages.json").write_text(json.dumps(page_indexes, indent=2) + "\n")
        diffs = differences(target, tables, score)
        (directory / "differences.json").write_text(json.dumps(diffs, indent=2) + "\n")
        difference_image(diffs).save(directory / "strict-differences.png")
        label = (
            f"DEV {corpus.name} | {run_dir.name} | "
            f"detector inference {inference_size} | "
            f"raster edge {frozen['config'].get('detector_edge')} | crop {frozen['config'].get('image_edge')}"
        )
        audits = {
            pair["target"]: column_partition_audit(target["tables"][pair["target"]], tables[pair["prediction"]])
            for pair in score.get("matches", [])
        }
        (directory / "column-partition-audit.json").write_text(json.dumps(audits, indent=2) + "\n")
        regional_views(directory, tables, score, marks, label, audits)
        panel_width = 1800
        source.thumbnail((780, 1450))
        grid.thumbnail((970, 1450))
        height = max(source.height, grid.height) + 155
        panel = Image.new("RGB", (panel_width, height), "#f5f7fa")
        draw = ImageDraw.Draw(panel)
        caption = (
            f"DEV {identifier} | exact cells {score['strict_exact_cells']}/{score['expected_cells']}"
            f" | complete tables {score['complete_tables']}/{score['expected_tables']}"
            f" | missed {score['missing_tables']} | extra {score['false_positive_tables']}"
            f" | output page 1/{len(grids)}"
        )
        lines(draw, (20, 8), caption, panel_width - 40, 22)
        source_ids = [
            identity for table in tables for cell in table.get("cells", []) for identity in cell.get("source_ids", [])
        ]
        id_label = "Source IDs absent: model-transcribed cells" if not source_ids else f"Source IDs: {source_ids[:8]}"
        if not tables:
            id_label = "No extracted cell source IDs: empty table output"
        if not target["tables"]:
            id_label = f"Negative page: exact empty-output verdict = {score['exact_page']}; no physical mask exists."
        lines(draw, (20, 80), label, panel_width - 40, 16)
        lines(draw, (20, 108), id_label, panel_width - 40, 16)
        lines(
            draw,
            (20, 50),
            "INPUT: table-level gold masks | OUTPUT: exact topology + NFC text cell verdicts | "
            "Green: exact reference match; red: strict reference disagreement; amber: unscored",
            panel_width - 40,
            18,
        )
        panel.paste(source, (20, 145))
        panel.paste(grid, (810, 145))
        panel.save(directory / "comparison.png")
        panels.append(panel)
        findings.append(
            {
                "id": identifier,
                "score": score,
                "column_partition_audit": audits,
                "output_page_prediction_indexes": page_indexes,
                "masks": marks["input_tables"],
                "source_ids": [cell.get("source_ids", []) for table in tables for cell in table.get("cells", [])],
            }
        )
    sheet = Image.new("RGB", (1800, sum(panel.height for panel in panels) + 170), "white")
    draw = ImageDraw.Draw(sheet)
    lines(draw, (20, 12), f"P003 verified DEV diagnostic | {run_dir.name}", 1760, 26)
    lines(
        draw,
        (20, 58),
        f"Model {frozen['config'].get('generation_model')} | "
        f"detector inference size {inference_size} | "
        f"raster edge {frozen['config'].get('detector_edge')} | "
        f"crop edge {frozen['config'].get('image_edge')} | complete pipeline, diagnostic only",
        1760,
        20,
    )
    lines(
        draw,
        (20, 110),
        "Full originals, regional source zooms and full extracted grids retained beside each panel. "
        "No cell boxes invented on source pages.",
        1760,
        18,
    )
    y = 170
    for panel in panels:
        sheet.paste(panel, (0, y))
        y += panel.height
    sheet.save(batch / "contact-sheet.png")
    resources = {
        "wall_seconds": time.monotonic() - started,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "tool": "time.monotonic/process_time; resource.getrusage RUSAGE_SELF Linux peak",
        "sampling_interval": "process-lifetime high-water mark; no sampled utilization",
        "process_scope": "single CPU-only renderer, no subprocesses",
        "logical_cpus": os.cpu_count(),
        "concurrency": 1,
    }
    provenance = {
        "batch_sha256": identity,
        "inputs": receipts,
        "renderer": renderer,
        "run": str(run_dir.resolve()),
        "corpus": str(corpus.resolve()),
        "detector_inference_size": inference_size,
        "detector_inference_size_basis": "retained report worker configuration, then frozen declared configuration",
        "quality_scope": (
            "complete pipeline; source masks table-level, output schematic cells strict topology and NFC text"
        ),
        "resources": resources,
        "pages": findings,
    }
    (batch / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return batch


def main() -> None:
    """Run one bounded immutable DEV refresh, without a background daemon."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ids", nargs="+", default=list(DEFAULT_IDS))
    args = parser.parse_args()
    print(run(args.run, args.corpus, args.output, args.ids))


if __name__ == "__main__":
    main()
