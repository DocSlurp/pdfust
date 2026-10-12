"""Isolated CPU renderer and OCR availability audit on explicit missing-text IDs."""

# Retained experiment JSON carries heterogeneous per-renderer diagnostics.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, PLR2004, C901, PLR0912
from __future__ import annotations

import argparse
import io
import json
import resource
import time
import warnings
from importlib.metadata import version
from pathlib import Path
from typing import Any

from bench.silver import guard_path, sha, write_json

IDS = ("p3537ba59f34ed944966f", "pd1a2dc76a3752f9861ee", "pfb20031e973ad29c7e43", "peb29c108f12d92347139")
DEFAULT_DPI = 150


def compare_images(first: bytes, second: bytes) -> dict[str, Any]:
    """Compare RGB rasters; retain any dimension normalization explicitly."""
    import numpy as np
    from PIL import Image

    with Image.open(io.BytesIO(first)) as original_a, Image.open(io.BytesIO(second)) as original_b:
        a, b = original_a.convert("RGB"), original_b.convert("RGB")
        dimensions = [list(a.size), list(b.size)]
        resized = a.size != b.size
        if resized:
            b = b.resize(a.size, Image.Resampling.NEAREST)
        delta = np.abs(np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16))
        return {
            "dimensions": dimensions,
            "second_nearest_resized_for_metric": resized,
            "mean_absolute_channel_difference": float(delta.mean()),
            "maximum_channel_difference": int(delta.max()),
            "different_pixel_fraction": float(np.any(delta > 0, axis=2).mean()),
            "scope": "RGB pixel difference; neither renderer is ground truth",
        }


def _png(image: Any) -> bytes:
    stream = io.BytesIO()
    image.convert("RGB").save(stream, format="PNG")
    return stream.getvalue()


def audit(
    manifest_path: Path, output: Path, *, ocr: bool = False, dpi: int = DEFAULT_DPI
) -> dict[str, Any]:
    """Render only the four named diagnostics; never inspect scoring references."""
    if type(dpi) is not int or dpi not in (150, 300):
        raise ValueError("Renderer audit permits only fixed 150 or 300 DPI")
    import fitz  # type: ignore[import-untyped]
    import numpy as np
    import pypdfium2 as pdfium  # type: ignore[import-untyped]
    from PIL import Image

    import pdfust

    began, cpu = time.perf_counter(), time.process_time()
    manifest = json.loads(guard_path(manifest_path).read_bytes())
    if manifest.get("split") != "DEV":
        raise ValueError("Renderer audit requires explicit DEV manifest")
    records = {record["id"]: record for record in manifest["pages"] if record["id"] in IDS}
    if set(records) != set(IDS):
        raise ValueError("All four frozen missing-text IDs must be present")
    output.mkdir(parents=True, exist_ok=True)
    engine = None
    initialization = None
    if ocr:
        started, process_cpu = time.perf_counter(), time.process_time()
        engine = pdfust.OcrEngine(threads=4)
        initialization = {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - process_cpu,
            "threads": 4,
            "max_concurrent": 1,
        }
    pages = []
    for identifier in IDS:
        record = records[identifier]
        source = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(source) != record["pdf_sha256"]:
            raise ValueError("Frozen input PDF changed")
        row: dict[str, Any] = {"id": identifier, "family": record["family"], "pdf_sha256": sha(source), "renderers": {}}
        pixels = {}
        for name in ("hayro", "pymupdf", "pdfium"):
            started, process_cpu = time.perf_counter(), time.process_time()
            result: dict[str, Any] = {"status": "error"}
            try:
                with warnings.catch_warnings(record=True) as observed:
                    warnings.simplefilter("always")
                    if name == "hayro":
                        with pdfust.open(stream=source) as document:
                            page = document[record["page_number"]]
                            viewport = list(page.rect)
                            text = page.get_text()
                            raster = page.render(scale=dpi / 72, background=(255, 255, 255))
                            original_rotation = page.rotation
                    elif name == "pymupdf":
                        with fitz.open(stream=source, filetype="pdf") as document:
                            page = document[record["page_number"]]
                            viewport = list(page.rect)
                            text = page.get_text()
                            raster = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False).tobytes("png")
                            original_rotation = page.rotation
                    else:
                        with pdfium.PdfDocument(source) as document:
                            page = document[record["page_number"]]
                            viewport = [0, 0, *page.get_size()]
                            textpage = page.get_textpage()
                            text = textpage.get_text_range()
                            textpage.close()
                            bitmap = page.render(scale=dpi / 72, fill_color=(255, 255, 255, 255))
                            raster = _png(bitmap.to_pil())
                            bitmap.close()
                            original_rotation = page.get_rotation()
                            page.close()
                    result["warnings"] = [str(w.message) for w in observed]
                pixels[name] = raster
                (output / f"{identifier}-{name}.png").write_bytes(raster)
                (output / f"{identifier}-{name}-text.txt").write_text(text)
                with Image.open(io.BytesIO(raster)) as image:
                    rgb = np.asarray(image.convert("RGB"))
                    result.update(
                        status="ok",
                        viewport=viewport,
                        rotation=original_rotation,
                        image_size=list(image.size),
                        png_sha256=sha(raster),
                        png_bytes=len(raster),
                        text_characters=len(text),
                        nonwhite_pixel_fraction=float(np.any(rgb < 250, axis=2).mean()),
                    )
                if engine is not None:
                    ocr_started, ocr_cpu = time.perf_counter(), time.process_time()
                    # All three inputs take the same image-only surrogate route; original PDFs remain untouched.
                    with Image.open(io.BytesIO(raster)) as image, pdfust.Document() as surrogate:
                        page = surrogate.new_page(width=image.width * 72 / dpi, height=image.height * 72 / dpi)
                        page.insert_image(page.rect, stream=raster)
                        words = page.get_text_ocr(dpi=dpi, engine=engine)
                    recognized = [
                        {"text": word["text"], "bbox": list(word["bbox"]), "confidence": word["confidence"]}
                        for word in words
                    ]
                    write_json(output / f"{identifier}-{name}-ocr.json", recognized)
                    result["ocr"] = {
                        "boxes": len(words),
                        "characters": sum(len(word["text"]) for word in words),
                        "mean_confidence": sum(word["confidence"] for word in words) / len(words) if words else None,
                        "wall_seconds": time.perf_counter() - ocr_started,
                        "cpu_seconds": time.process_time() - ocr_cpu,
                        "scope": f"Matched image-only surrogate re-rendered by hayro at {dpi} DPI; "
                        "not original native source ownership",
                    }
            except Exception as error:
                result.update(error_type=type(error).__name__)
                if isinstance(error, ValueError):
                    result["error"] = str(error)[:500]
            result.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - process_cpu)
            row["renderers"][name] = result
        row["comparisons"] = {
            name: compare_images(pixels["hayro"], pixels[name])
            for name in ("pymupdf", "pdfium")
            if "hayro" in pixels and name in pixels
        }
        row["input_hash_unchanged"] = sha(guard_path(Path(record["pdf_path"])).read_bytes()) == row["pdf_sha256"]
        pages.append(row)
    result = {
        "ids": list(IDS),
        "dpi": dpi,
        "pages": pages,
        "ocr_initialization": initialization,
        "versions": {name: version(name) for name in ("PyMuPDF", "pypdfium2", "pdfust")},
        "metrics": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": "Single CPU parent process; native OCR four threads/max_concurrent1; "
            "no subprocesses or utilization sampling",
        },
    }
    write_json(output / "audit.json", result)
    return result


def main() -> None:
    """Require explicit manifest/output and explicit local OCR opt-in."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--dpi", type=int, choices=(150, 300), default=DEFAULT_DPI)
    args = parser.parse_args()
    result = audit(args.manifest, args.output, ocr=args.ocr, dpi=args.dpi)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
