"""Independent source constructions for CPU-only P002 OCR admission audits.

Construction references live separately from source extraction. This measures
source discovery and caller preservation, not table correctness or OCR accuracy.
"""

# ruff: noqa: PLC0415, E501
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

from bench.feature_cases import stream_object, text_op
from bench.pipeline_ocr_sources import discover_regions, extract
from bench.silver_layouts import _serialize
from bench.silver_structure import process_peak_rss

IDS = (
    "native-only",
    "mixed-inset",
    "two-image-tables",
    "rotation-90",
    "rotation-180",
    "rotation-270",
    "crop-offset",
    "inherited-multipage",
    "japanese-raster",
    "native-intersection",
    "overlapping-images",
    "decorative-raster",
    "empty-page",
    "raster-table",
)


def _raster(*, japanese: bool = False, decoration: bool = False) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (800, 360), "white")
    draw = ImageDraw.Draw(image)
    if decoration:
        draw.ellipse((100, 70, 700, 300), outline="blue", width=12)
    else:
        font = ImageFont.truetype("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 40)
        for x in (20, 400, 780):
            draw.line((x, 20, x, 340), fill="black", width=3)
        for y in (20, 120, 230, 340):
            draw.line((20, y, 780, y), fill="black", width=3)
        for index, (left, right) in enumerate(
            (("地域", "合計"), ("東京", "12"), ("大阪", "34"))
            if japanese
            else (("Region", "Total"), ("North", "12"), ("South", "34"))
        ):
            draw.text((45, 40 + index * 105), left, font=font, fill="black")
            draw.text((425, 40 + index * 105), right, font=font, fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def source_cases() -> list[dict[str, Any]]:
    """Construct source bytes only, without extraction-derived targets."""
    import pylopdf

    output = []
    for identifier in IDS:
        with pylopdf.Document() as document:
            page = document.new_page(width=600, height=800)
            if identifier in {"native-only", "mixed-inset", "two-image-tables", "native-intersection"}:
                page.insert_text((30, 45), "Native header")
                page.insert_text((30, 760), "Native footer")
            if identifier not in {"native-only", "empty-page", "inherited-multipage"}:
                page.insert_image(
                    (100, 150, 500, 330),
                    stream=_raster(
                        japanese=identifier == "japanese-raster", decoration=identifier == "decorative-raster"
                    ),
                )
            if identifier == "two-image-tables":
                page.insert_image((100, 420, 500, 600), stream=_raster())
            if identifier == "native-intersection":
                page.insert_text((150, 220), "Already searchable")
            if identifier == "overlapping-images":
                page.insert_image((250, 220, 550, 400), stream=_raster())
            if identifier.startswith("rotation-"):
                page.set_rotation(int(identifier.rsplit("-", 1)[1]))
            if identifier == "crop-offset":
                page.set_cropbox((20, 40, 580, 780))
            data = document.tobytes()
        page_number = 0
        if identifier == "inherited-multipage":
            data = _serialize(
                [
                    "<< /Type /Catalog /Pages 2 0 R >>",
                    "<< /Type /Pages /Count 2 /Kids [3 0 R 4 0 R] /MediaBox [0 0 600 800] /CropBox [20 20 580 780] /Rotate 90 /Resources << /Font << /F1 7 0 R >> >> >>",
                    "<< /Type /Page /Parent 2 0 R /Contents 5 0 R >>",
                    "<< /Type /Page /Parent 2 0 R /Contents 6 0 R >>",
                    stream_object(text_op("Inherited header", 40, 700)),
                    stream_object(""),
                    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
                ],
                "1.7",
            )
            page_number = 1
        output.append({"id": identifier, "pdf": data, "page_number": page_number})
    return output


def construction_references() -> dict[str, dict[str, int]]:
    """Return authored discovery expectations separately from extraction."""
    counts = dict.fromkeys(IDS, 1)
    counts.update(
        {
            "native-only": 0,
            "empty-page": 0,
            "inherited-multipage": 0,
            "native-intersection": 0,
            "overlapping-images": 0,
            "two-image-tables": 2,
        }
    )
    return {identifier: {"uncovered_regions": count} for identifier, count in counts.items()}


def run(*, ocr: bool = False) -> dict[str, Any]:
    """Measure discovery or real optional OCR with one CPU engine and no mutations."""
    import pylopdf

    cases = source_cases()
    references = construction_references()
    start, cpu = time.perf_counter(), time.process_time()
    engine = pylopdf.OcrEngine(threads=1) if ocr else None
    rows = []
    for case in cases:
        with pylopdf.Document(stream=case["pdf"]) as document:
            page = document[case["page_number"]]
            before = document.tobytes()
            native = [{"text": word[4], "bbox": list(word[:4])} for word in page.get_text("words")]
            discovery = discover_regions(list(page.rect), native, [dict(image) for image in page.get_images()], 150)
            row = {
                "id": case["id"],
                "pdf_sha256": hashlib.sha256(case["pdf"]).hexdigest(),
                "page_number": case["page_number"],
                "native_words": len(native),
                "regions": discovery["regions"],
                "rejected": discovery["rejected"],
                "runs": [],
            }
            if ocr:
                for mode in ("empty", "uncovered_images"):
                    for tokenization in ("whitespace", "reextract"):
                        try:
                            result = extract(page, mode, 150, engine=engine, tokenization=tokenization)
                            row["runs"].append({"mode": mode, "tokenization": tokenization, **result})
                        except Exception as error:
                            row["runs"].append(
                                {
                                    "mode": mode,
                                    "tokenization": tokenization,
                                    "error": f"{type(error).__name__}: {error}",
                                }
                            )
            row["caller_preserved"] = document.tobytes() == before
            row["expected_regions"] = references[case["id"]]["uncovered_regions"]
            row["discovery_matches_construction"] = len(row["regions"]) == row["expected_regions"]
            rows.append(row)
    peak, tool = process_peak_rss()
    return {
        "schema": 1,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "pylopdf_version": pylopdf.__version__,
        "font": "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "scope": "authored DEV source contracts; no OCR/table quality score",
        "ocr": ocr,
        "dpi": 150,
        "workers": 1,
        "ocr_threads": 1 if ocr else None,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": peak,
        "rss_tool": tool,
        "rss_sampling": "kernel executable high-water mark",
        "process_scope": "one Python process including native OCR; source construction excluded from timing",
        "cases": rows,
    }


def main() -> None:
    """Write ignored complete results and a concise Markdown report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, default=Path("bench/results/p002-native-audit.md"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    inputs = args.output.parent / "inputs"
    inputs.mkdir(exist_ok=True)
    for case in source_cases():
        (inputs / (case["id"] + ".pdf")).write_bytes(case["pdf"])
    result = run(ocr=args.ocr)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    rows = result["cases"]
    errors = sum("error" in run for row in rows for run in row["runs"])
    args.summary.write_text(
        "# P002 native source audit\n\n"
        f"Fourteen separately constructed DEV cases: {sum(row['discovery_matches_construction'] for row in rows)}/14 "
        f"image-region inventories match authored construction; {sum(row['caller_preserved'] for row in rows)}/14 callers preserved. "
        f"Real OCR: {result['ocr']}; extraction errors: {errors}. This is a source contract audit, not OCR or table quality.\n\n"
        f"One CPU worker, OCR threads={result['ocr_threads']}, fixed 150 DPI. Wall {result['wall_seconds']:.2f}s, "
        f"process CPU {result['cpu_seconds']:.2f}s, peak RSS {result['peak_rss_bytes']} bytes via {result['rss_tool']}. "
        "Kernel high-water mark, one process including native OCR; source construction is outside elapsed/CPU timing "
        "but included in RSS. GPU and network inference were unused.\n\n"
        "| Case | Native words | Uncovered regions | Preserved | OCR errors |\n|---|---:|---:|---|---:|\n"
        + "".join(
            f"| {row['id']} | {row['native_words']} | {len(row['regions'])} | {row['caller_preserved']} | "
            f"{sum('error' in run for run in row['runs'])} |\n"
            for row in rows
        )
        + "\nReferences encode only authored region counts and are joined after extraction. Rotated pages use display "
        "coordinates; sideways OCR is intentionally uncorrected. Decorative rasters remain eligible because source "
        "discovery cannot distinguish decoration from text. Native intersection and overlapping images abstain. "
        "Whitespace uses approximate character advance; re-extracted word geometry belongs to a constructed invisible layer.\n"
    )


if __name__ == "__main__":
    main()
