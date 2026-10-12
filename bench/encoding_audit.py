"""CPU metamorphic audit of PDF encodings and selective OCR routing blind spots."""

from __future__ import annotations

import hashlib
import json
import random
import statistics
import time
import zlib
from dataclasses import dataclass
from pathlib import Path

import pdfust
from bench.feature_cases import raw_pdf, stream_object

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts/encodings"
_LARGE_RASTER_AREA = 0.2
REFERENCE = (("Item", "Qty", "Amount"), ("Alpha", "2", "12.00"), ("Beta", "3", "9.00"), ("Total", "5", "21.00"))


@dataclass(frozen=True)
class EncodingCase:
    """An encoding intervention with independently declared expected semantics."""

    name: str
    data: bytes
    cohort: str = "equivalent"
    note: str = ""


def _operators(mode: str) -> tuple[list[str], list[str]]:
    rules = [f"40 {y} m 550 {y} l S" for y in (700, 660, 620, 580, 540)]
    rules += [f"{x} 540 m {x} 700 l S" for x in (40, 210, 380, 550)]
    runs = []
    for row, values in enumerate(REFERENCE):
        for col, text in enumerate(values):
            x, y = 50 + col * 170, 675 - row * 40
            if mode == "glyph-tj":
                show = " ".join(f"({char}) Tj" for char in text)
            elif mode == "array-tj":
                show = "[" + " 0 ".join(f"({char})" for char in text) + "] TJ"
            elif mode == "hex":
                show = f"<{text.encode().hex()}> Tj"
            else:
                show = f"({text}) Tj"
            runs.append(f"BT /F1 12 Tf 1 0 0 1 {x} {y} Tm {show} ET")
    if mode == "shuffled":
        random.Random(72631).shuffle(runs)  # noqa: S311 - reproducible fixture order, not security.
    return rules, runs


def encoded_pdf(mode: str = "literal") -> bytes:
    """Produce one identical visible grid through distinct PDF representations."""
    rules, runs = _operators(mode)
    content = "\n".join(rules + runs).encode()
    resources = "<< /Font << /F1 5 0 R >> >>"
    page_resources = f"/Resources {resources}"
    parent_resources = ""
    extra_page = ""
    contents = "4 0 R"
    extras: list[bytes | str] = []
    stream = stream_object(content)
    if mode == "flate":
        stream = stream_object(zlib.compress(content), "/Filter /FlateDecode")
    elif mode == "contents-array":
        stream = stream_object("\n".join(rules))
        extras = [stream_object("\n".join(runs))]
        contents = "[4 0 R 6 0 R]"
    elif mode == "inherited-resources":
        page_resources = ""
        parent_resources = f"/Resources {resources}"
    elif mode == "form-xobject":
        stream = stream_object("q /Table Do Q")
        extras = [stream_object(content, f"/Type /XObject /Subtype /Form /BBox [0 0 612 792] /Resources {resources}")]
        page_resources = "/Resources << /XObject << /Table 6 0 R >> >>"
    elif mode == "translated-crop":
        stream = stream_object(b"q 1 0 0 1 30 20 cm\n" + content + b"\nQ")
        extra_page = "/CropBox [30 20 642 812]"
    elif mode == "clip-empty":
        stream = stream_object(b"q 0 0 1 1 re W n\n" + content + b"\nQ")
    elif mode == "white-cover":
        stream = stream_object(content + b"\n1 1 1 rg 0 0 612 792 re f")
    elif mode == "invisible-text":
        stream = stream_object(("\n".join(rules) + "\n3 Tr\n" + "\n".join(runs)).encode())
    elif mode == "duplicate-paint":
        stream = stream_object(content + b"\n" + "\n".join(runs).encode())
    return raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            f"<< /Type /Pages /Kids [3 0 R] /Count 1 {parent_resources} >>",
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 650 820] {extra_page} "
                f"/Contents {contents} {page_resources} >>"
            ),
            stream,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
            *extras,
        ]
    )


def cases() -> list[EncodingCase]:
    """Freeze interventions before observing extractor results."""
    result = [
        EncodingCase(mode, encoded_pdf(mode))
        for mode in (
            "literal",
            "glyph-tj",
            "array-tj",
            "hex",
            "shuffled",
            "flate",
            "contents-array",
            "inherited-resources",
            "form-xobject",
        )
    ]
    result.append(
        EncodingCase(
            "translated-crop",
            encoded_pdf("translated-crop"),
            note="Different page dimensions; logical cells should agree.",
        )
    )
    for rotation in (90, 180, 270):
        with pdfust.open(stream=encoded_pdf()) as doc:
            doc[0].set_rotation(rotation)
            result.append(EncodingCase(f"rotation-{rotation}", doc.tobytes()))
    result.extend(
        EncodingCase(mode, encoded_pdf(mode), "visibility", "Text-layer content is not proof of visible content.")
        for mode in ("clip-empty", "white-cover", "invisible-text", "duplicate-paint")
    )
    with pdfust.open(stream=encoded_pdf()) as source:
        pixmap = source[0].get_pixmap(dpi=96)
        for mixed in (False, True):
            with pdfust.open() as doc:
                page = doc.new_page(width=650, height=820)
                page.insert_image(page.rect, pixmap=pixmap)
                if mixed:
                    page.insert_text((40, 35), "Digital title over a scanned table")
                result.append(EncodingCase("mixed-scan" if mixed else "pure-scan", doc.tobytes(), "ocr-routing"))
    illustration = raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 650 820] /Contents 4 0 R >>",
            stream_object("0.3 0.5 0.7 rg 0 0 650 820 re f 0.8 0.6 0.2 rg 80 80 450 620 re f"),
        ]
    )
    with pdfust.open(stream=illustration) as source:
        pixmap = source[0].get_pixmap(dpi=72)
        for name, box in (("logo", (20, 20, 70, 70)), ("raster-illustration", (0, 0, 650, 820))):
            with pdfust.open() as doc:
                page = doc.new_page(width=650, height=820)
                page.insert_image(box, pixmap=pixmap)
                page.insert_text((40, 35), "A page with no table")
                result.append(EncodingCase(name, doc.tobytes(), "ocr-negative"))
    return result


def matrix(table: pdfust.SpatialTable) -> tuple[tuple[str, ...], ...]:
    """Expand slots by stable cell identity, preserving empty cells."""
    cells = {cell.id: cell.text for cell in table.cells}
    return tuple(
        tuple(cells[table.slots[r * table.col_count + c]] for c in range(table.col_count))
        for r in range(table.row_count)
    )


def evaluate(case: EncodingCase, *, repetitions: int = 5) -> dict[str, object]:
    """Measure opening plus extraction separately from CPU render and image decoding."""
    elapsed = []
    matrices: list[tuple[tuple[str, ...], ...]] = []
    for _ in range(repetitions):
        start = time.perf_counter_ns()
        with pdfust.open(stream=case.data) as doc:
            layout = doc[0].get_layout()
            matrices = [matrix(table) for table in layout.tables]
        elapsed.append((time.perf_counter_ns() - start) / 1e6)
    with pdfust.open(stream=case.data) as doc:
        page = doc[0]
        layout = page.get_layout()
        image_start = time.perf_counter_ns()
        images = page.get_images()
        image_ms = (time.perf_counter_ns() - image_start) / 1e6
        # Spatially uncovered portions of images need further detection. Any text
        # on the page or within the image is insufficient to suppress that work.
        image_area = sum((i["bbox"][2] - i["bbox"][0]) * (i["bbox"][3] - i["bbox"][1]) for i in images)
        raster = page.get_pixmap(dpi=72).tobytes()
    return {
        "name": case.name,
        "cohort": case.cohort,
        "note": case.note,
        "input_sha256": hashlib.sha256(case.data).hexdigest(),
        "render_sha256": hashlib.sha256(raster).hexdigest(),
        "exact_grid": matrices == [REFERENCE],
        "matrices": matrices,
        "word_count": len(layout.words),
        "table_count": len(layout.tables),
        "open_extract_ms": statistics.median(elapsed),
        "samples_ms": elapsed,
        "page_empty_ocr_gate": not layout.words,
        "image_coverage_upper_bound": min(1, image_area / (layout.width * layout.height)),
        "image_probe_ms": image_ms,
        "unresolved_raster_evidence": bool(images) and not layout.tables,
        "large_raster_gate": image_area / (layout.width * layout.height) >= _LARGE_RASTER_AREA and not layout.tables,
    }


def main() -> None:
    """Retain full inputs/decisions locally and write a compact failure-inclusive report."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    results = []
    for case in cases():
        (ARTIFACTS / f"{case.name}.pdf").write_bytes(case.data)
        result = evaluate(case)
        results.append(result)
    report = {"code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "results": results}
    (ARTIFACTS / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# PDF encoding and routing audit",
        "",
        "One grid, 13 equivalent encodings, four visibility controls, two scans and two raster negatives.",
        (
            "This is metamorphic coverage, not independent document-family accuracy. Five CPU repetitions "
            "include open, extraction, Python materialization and close; render/image inspection excluded."
        ),
        "",
        "| Case | Cohort | Exact source grid | Words | Open + extract ms |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    lines += [
        f"| {r['name']} | {r['cohort']} | {r['exact_grid']} | {r['word_count']} | {r['open_extract_ms']:.3f} |"
        for r in results
    ]
    lines += [
        "",
        (
            "Visibility controls have deliberately different visible semantics. Exact source-grid recovery "
            "on those controls is not correctness: clipping, covering paint and invisible text need separate "
            "policy."
        ),
        "Duplicate paint must remain observable; blanket deduplication can erase legitimate overprints.",
        "",
        (
            "The mixed-scan control has digital text but no extracted table. A page-empty OCR gate skips it. "
            "Image presence routes both scans but also both raster negatives. A fixed 20% area gate "
            "rejects the small logo but still routes a full-page illustration. These are work-routing "
            "signals, not table detections; a regional detector or other evidence is still needed."
        ),
        (
            "Image area is a capped sum, not an overlap-aware coverage measure. `get_images()` currently "
            "decodes image payloads; its probe timings are in the full report and are not a cheap "
            "metadata-only route."
        ),
        "",
        "Inputs, output matrices, hashes and all timing samples remain in ignored `pdf-master-artifacts/encodings/`.",
        "Reproduce: `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m bench.encoding_audit`.",
    ]
    (ROOT / "bench/results/encoding-audit.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "equivalent_exact": sum(r["exact_grid"] for r in results if r["cohort"] == "equivalent"),
                "equivalent_total": sum(r["cohort"] == "equivalent" for r in results),
                "cases": len(results),
            }
        )
    )


if __name__ == "__main__":
    main()
