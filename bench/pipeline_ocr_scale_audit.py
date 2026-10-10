"""Offline native OCR scale audit using frozen, constructed raster sources."""

# Heterogeneous retained experiment dictionaries and explicit validation messages.
# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

import pylopdf
from bench.ocr import _cer
from bench.pipeline_layout_detector import _Measure

SCALES = (0.5, 1.0, 2.0)
ARMS = ("dpi150", "edge2048")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "bench/results/pdf-master-artifacts/pipeline-p002/ocr-scale-audit"


def digest(data: bytes) -> str:
    """Hash retained bytes."""
    return hashlib.sha256(data).hexdigest()


def dpi_for(arm: str, viewport: list[float]) -> float:
    """Return the frozen resolution for a display viewport."""
    if len(viewport) != 4 or viewport[2] <= viewport[0] or viewport[3] <= viewport[1]:
        raise ValueError("Positive display viewport required")
    if arm == "dpi150":
        return 150.0
    if arm == "edge2048":
        return 72.0 * 2048 / max(viewport[2] - viewport[0], viewport[3] - viewport[1])
    raise ValueError("Unknown frozen arm")


def sources() -> list[dict[str, Any]]:
    """Construct independent raster text, geometry and negative controls."""
    image = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=24)
    cells = []
    rows = [["ITEM", "UNITS", "RATE", "TOTAL"]]
    rows.extend([[f"Part {i:02d}", str(10 + i), f"{i + 2}.50", f"{(10 + i) * (i + 2)}.00"] for i in range(1, 21)])
    for ri, row in enumerate(rows):
        y = 100 + ri * 60
        for ci, text in enumerate(row):
            x = 60 + ci * 270
            box = list(draw.textbbox((x + 12, y + 16), text, font=font))
            draw.text((x + 12, y + 16), text, font=font, fill="black")
            draw.rectangle((x, y, x + 270, y + 60), outline="black", width=2)
            cells.append({"text": text, "pixel_bbox": box})
    target = "\n".join(" ".join(row) for row in rows)
    rotated = image.transpose(Image.Transpose.ROTATE_270)
    rotated_cells = [
        {
            "text": c["text"],
            "pixel_bbox": [
                1600 - c["pixel_bbox"][3],
                c["pixel_bbox"][0],
                1600 - c["pixel_bbox"][1],
                c["pixel_bbox"][2],
            ],
        }
        for c in cells
    ]
    negative = Image.new("RGB", (1200, 1600), "white")
    nd = ImageDraw.Draw(negative)
    nd.rectangle((150, 220, 1000, 700), fill=(150, 190, 220))
    nd.ellipse((220, 900, 920, 1450), fill=(210, 150, 80))
    return [
        {"id": "english-table", "image": image, "target": target, "cells": cells, "rotation": 0},
        {"id": "english-table-rotated90", "image": rotated, "target": target, "cells": rotated_cells, "rotation": 270},
        {"id": "negative-graphic", "image": negative, "target": "", "cells": [], "rotation": 0},
    ]


def encoded(image: Image.Image) -> bytes:
    """Encode a source image without resampling."""
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def normalize(box: list[float], viewport: list[float]) -> list[float]:
    """Map a display box into unit-page geometry."""
    x0, y0, x1, y1 = viewport
    return [(box[0] - x0) / (x1 - x0), (box[1] - y0) / (y1 - y0), (box[2] - x0) / (x1 - x0), (box[3] - y0) / (y1 - y0)]


def freeze(output: Path) -> dict[str, Any]:
    """Retain immutable sources and the experiment plan before recognition."""
    output.mkdir(parents=True, exist_ok=True)
    if (output / "plan.json").exists():
        return json.loads((output / "plan.json").read_text())
    plan = {
        "schema": 1,
        "scales": list(SCALES),
        "arms": list(ARMS),
        "edge": 2048,
        "controls": {"threads": 4, "max_concurrent": 1, "tile_size": 1408, "overlap": 192, "min_confidence": 0.5},
        "purpose": (
            "Test arbitrary PDF physical scale with identical embedded source pixels; "
            "fixed arms chosen before outcomes."
        ),
        "source_font": "Pillow packaged Aileron Regular via ImageFont.load_default(size=24)",
        "cases": [],
    }
    for source in sources():
        name = source["id"]
        payload = encoded(source["image"])
        (output / f"{name}.png").write_bytes(payload)
        construction = {k: v for k, v in source.items() if k != "image"}
        construction.update(pixel_size=list(source["image"].size), source_png_sha256=digest(payload))
        (output / f"{name}-construction.json").write_text(json.dumps(construction, indent=2) + "\n")
        cases = []
        for scale in SCALES:
            pdf_path = output / f"{name}-scale{scale:g}.pdf"
            with pylopdf.open() as doc:
                page = doc.new_page(
                    width=source["image"].width * 0.5 * scale, height=source["image"].height * 0.5 * scale
                )
                page.insert_image(page.rect, stream=payload)
                doc.save(pdf_path)
            cases.append({"scale": scale, "pdf": str(pdf_path.resolve()), "sha256": digest(pdf_path.read_bytes())})
        plan["cases"].append({**construction, "pdfs": cases})
    plan_path = output / "plan.json"
    if plan_path.exists() and json.loads(plan_path.read_text()) != plan:
        raise ValueError("Existing plan differs; use a new output directory")
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    return plan


def measurement(m: _Measure) -> dict[str, Any]:
    """Describe resource measurements in the audit process scope."""
    result = dict(m.result)
    result["measurement"] = (
        "Audit process and native Rust OCR threads; process_time CPU; "
        "/proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS. "
        "No other processes included."
    )
    return result


def compare_geometry(rows: list[dict[str, Any]]) -> None:
    """Compare same-order output only when text sequence matches the scale-one arm."""
    for row in rows:
        base = next((r for r in rows if r["case"] == row["case"] and r["arm"] == row["arm"] and r["scale"] == 1), None)
        same = (
            base is not None
            and row.get("status", "ok") == "ok"
            and base.get("status", "ok") == "ok"
            and [w["text"] for w in row.get("words", [])] == [w["text"] for w in base.get("words", [])]
        )
        row["same_text_sequence_as_scale1"] = same
        row["max_normalized_box_delta_vs_scale1"] = (
            max(
                (
                    abs(a - b)
                    for w, v in zip(row.get("words", []), base.get("words", []) if base else [], strict=False)
                    for a, b in zip(w["normalized_bbox"], v["normalized_bbox"], strict=True)
                ),
                default=0.0,
            )
            if same
            else None
        )


def construction_cell_diagnostic(report: dict[str, Any], plan: dict[str, Any]) -> None:
    """Post-run diagnostic: compare text at nearest known construction cell centers.

    This is separate from the frozen row-major sequence CER; it does not evaluate
    inferred table structure or tune either resolution arm.
    """
    for row in report["rows"]:
        case = next(c for c in plan["cases"] if c["id"] == row["case"])
        if not case["cells"] or row["status"] != "ok":
            continue
        width, height = case["pixel_size"]
        boxes = [normalize(c["pixel_bbox"], [0, 0, width, height]) for c in case["cells"]]
        centers = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in boxes]
        groups: list[list[str]] = [[] for _ in boxes]
        for word in row["words"]:
            b = word["normalized_bbox"]
            center = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            nearest = min(
                range(len(centers)), key=lambda i: (center[0] - centers[i][0]) ** 2 + (center[1] - centers[i][1]) ** 2
            )
            groups[nearest].append(word["text"])
        edits = sum(_cer(c["text"], " ".join(g), nfkc=False)[2] for c, g in zip(case["cells"], groups, strict=True))
        expected = sum(len("".join(c["text"].split())) for c in case["cells"])
        row["post_run_constructed_cell_diagnostic"] = {
            "expected_characters": expected,
            "edits": edits,
            "cer": edits / expected,
            "empty_cells": sum(not g for g in groups),
            "multiply_assigned_cells": sum(len(g) > 1 for g in groups),
            "method": (
                "Nearest known source text-box center in normalized page coordinates; "
                "post-run reading-order diagnostic, not table-quality evaluation."
            ),
        }


def run(output: Path) -> dict[str, Any]:
    """Recognize every frozen case and arm without selecting outcomes."""
    plan = json.loads((output / "plan.json").read_text())
    if plan["scales"] != list(SCALES) or plan["arms"] != list(ARMS):
        raise ValueError("Unrecognized frozen plan")
    with _Measure() as init:
        engine = pylopdf.OcrEngine(threads=4, max_concurrent=1)
    report = {
        "plan_sha256": digest((output / "plan.json").read_bytes()),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "engine_initialization": measurement(init),
        "rows": [],
    }
    for case in plan["cases"]:
        for pdf in case["pdfs"]:
            path = Path(pdf["pdf"])
            if digest(path.read_bytes()) != pdf["sha256"]:
                raise ValueError("Frozen source PDF hash mismatch")
            with pylopdf.open(path) as doc:
                page = doc[0]
                viewport = list(page.rect)
                for arm in ARMS:
                    row = {
                        "case": case["id"],
                        "scale": pdf["scale"],
                        "arm": arm,
                        "viewport": viewport,
                        "dpi": dpi_for(arm, viewport),
                        "rotation": case["rotation"],
                    }
                    stem = f"{case['id']}-scale{pdf['scale']:g}-{arm}"
                    try:
                        with _Measure() as render:
                            pix = page.get_pixmap(dpi=row["dpi"])
                            png = pix.tobytes()
                            (output / f"{stem}-render.png").write_bytes(png)
                        row.update(
                            render=measurement(render),
                            render_size=[pix.width, pix.height],
                            render_png_sha256=digest(png),
                            render_rgba_sha256=digest(pix.samples),
                        )
                        with _Measure() as recognition:
                            words = page.get_text_ocr(
                                dpi=row["dpi"],
                                engine=engine,
                                tile_size=1408,
                                overlap=192,
                                min_confidence=0.5,
                                rotation=case["rotation"],
                            )
                        row["recognition"] = measurement(recognition)
                        row["words"] = [
                            {
                                "text": w["text"],
                                "bbox": list(w["bbox"]),
                                "normalized_bbox": normalize(list(w["bbox"]), viewport),
                                "confidence": w["confidence"],
                            }
                            for w in words
                        ]
                        actual = "\n".join(w["text"] for w in words)
                        (output / f"{stem}-ocr.txt").write_text(actual + "\n")
                        row["actual_text"] = actual
                        row["strict"] = _cer(case["target"], actual, nfkc=False) if case["target"] else None
                        row["negative_recognized_characters"] = (
                            len("".join(actual.split())) if not case["target"] else None
                        )
                        row["status"] = "ok"
                    except Exception as exc:
                        row.update(status="error", error=f"{type(exc).__name__}: {exc}")
                    report["rows"].append(row)
                    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
                    print(f"{stem}: {row['status']}, {len(row.get('words', []))} words", flush=True)
    compare_geometry(report["rows"])
    construction_cell_diagnostic(report, plan)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    """Run the source freeze or the already frozen audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--freeze", action="store_true", help="Create sources and plan without running OCR")
    args = parser.parse_args()
    if args.freeze:
        freeze(args.output)
    else:
        run(args.output)


if __name__ == "__main__":
    main()
