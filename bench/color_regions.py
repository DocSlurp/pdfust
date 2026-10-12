"""CPU-only experimental color-region extraction, independent of the public API.

Raster thresholds compare adjacent RGB Euclidean distance and Rec. 709 luminance
on encoded sRGB values (not perceptual Lab). Connected regions can contain text
holes. Border-connected components with near-white mean color are omitted; enclosed white spaces
are retained. A component is geometric evidence, never an inferred table/cell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pdfust import Page, Pixmap

ROOT = Path(__file__).resolve().parents[1]


def build_executable(destination: Path | None = None) -> Path:
    """Compile only the standalone std Rust executable; never rebuild the wheel."""
    source = ROOT / "bench/color_regions.rs"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    output = destination or Path(tempfile.gettempdir()) / f"pdf-master-color-regions-{digest}"
    if output.exists():
        return output
    compiler = os.environ.get("COLOR_REGIONS_RUSTC") or shutil.which("rustc")
    if not compiler:
        message = "Rust compiler required; set COLOR_REGIONS_RUSTC"
        raise RuntimeError(message)
    result = subprocess.run(  # noqa: S603 - explicit local compiler or compiled executable.
        [compiler, "--edition=2021", "-O", str(source), "-o", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return output


def extract_regions(  # noqa: PLR0913 - explicit independent experimental controls.
    rgb: bytes,
    width: int,
    height: int,
    *,
    color_distance: int = 18,
    luminance_distance: int = 18,
    connectivity: int = 4,
    min_area: int = 64,
    background_white: int = 248,
    max_pixels: int = 4_000_000,
    max_components: int = 65_536,
    max_regions: int = 4096,
    executable: Path | None = None,
) -> list[dict[str, Any]]:
    """Return exclusive pixel boxes, area/color and darker-boundary evidence.

    Complete extraction is rejected on any limit; no partial regions are returned.
    ``background_white=256`` retains white backgrounds. Set connectivity explicitly
    to 8 when corner-touching pixels should belong to one component.
    """
    parameters = {
        "width": width,
        "height": height,
        "color-distance": color_distance,
        "luminance-distance": luminance_distance,
        "connectivity": connectivity,
        "min-area": min_area,
        "background-white": background_white,
        "max-pixels": max_pixels,
        "max-components": max_components,
        "max-regions": max_regions,
    }
    if any(type(value) is not int or value < 0 for value in parameters.values()):
        message = "parameters must be nonnegative integers"
        raise ValueError(message)
    if width * height > max_pixels:
        message = "pixel limit"
        raise ValueError(message)
    if len(rgb) != width * height * 3:
        message = "RGB payload size mismatch"
        raise ValueError(message)
    if color_distance > 442 or luminance_distance > 255 or background_white > 256:  # noqa: PLR2004 - RGB domain limits.
        message = "threshold out of range"
        raise ValueError(message)
    if connectivity not in (4, 8):
        message = "connectivity must be 4 or 8"
        raise ValueError(message)
    command = [str(executable or build_executable())]
    for name, value in parameters.items():
        command.extend((f"--{name}", str(value)))
    result = subprocess.run(  # noqa: S603 - explicit compiled local executable.
        command, input=rgb, capture_output=True, check=False
    )
    if result.returncode:
        raise ValueError(result.stderr.decode().strip())
    return json.loads(result.stdout)


def vector_regions(  # noqa: C901, PLR0912 - bounded candidate comparison and union.
    page: Page,
    *,
    color_distance: float = 18,
    gap: float = 0.5,
    min_area: float = 16,
    max_candidates: int = 1024,
) -> list[dict[str, Any]]:
    """Group touching same-color fill boxes and closed stroke boxes.

    Boxes are native paint bounds, not exact polygon connectivity or visibility.
    Patterns are skipped. Opacity and fill/stroke kind must agree before grouping.
    The candidate cap also bounds the quadratic comparison pass.
    """
    if type(max_candidates) is not int or not 0 <= max_candidates <= 1024:  # noqa: PLR2004 - hard experiment comparison cap.
        message = "max_candidates must be between 0 and 1024"
        raise ValueError(message)
    if not math.isfinite(min_area) or min_area < 0:
        message = "invalid vector minimum area"
        raise ValueError(message)
    if not math.isfinite(color_distance) or color_distance < 0 or not math.isfinite(gap) or gap < 0:
        message = "invalid vector threshold"
        raise ValueError(message)
    candidates: list[dict[str, Any]] = []
    for drawing in page.get_drawings():
        for kind, paint, opacity in (
            ("fill", drawing["fill"], drawing["fill_opacity"]),
            ("stroke", drawing["color"], drawing["stroke_opacity"]),
        ):
            if paint is None or (kind == "stroke" and not drawing["closePath"]):
                continue
            box = list(drawing["rect"])
            if (box[2] - box[0]) * (box[3] - box[1]) < min_area:
                continue
            if len(candidates) >= max_candidates:
                message = "vector candidate limit"
                raise ValueError(message)
            candidates.append({"bbox": box, "mean_rgb": [v * 255 for v in paint], "kind": kind, "opacity": opacity})
    parents = list(range(len(candidates)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for i, a in enumerate(candidates):
        for j in range(i):
            b = candidates[j]
            if a["kind"] != b["kind"] or a["opacity"] != b["opacity"]:
                continue
            if sum((x - y) ** 2 for x, y in zip(a["mean_rgb"], b["mean_rgb"], strict=True)) > color_distance**2:
                continue
            ab, bb = a["bbox"], b["bbox"]
            if ab[0] <= bb[2] + gap and bb[0] <= ab[2] + gap and ab[1] <= bb[3] + gap and bb[1] <= ab[3] + gap:
                parents[find(i)] = find(j)
    groups: dict[int, dict[str, Any]] = {}
    for i, candidate in enumerate(candidates):
        key = find(i)
        if key not in groups:
            groups[key] = {**candidate, "bbox": candidate["bbox"][:], "paint_count": 1}
        else:
            group = groups[key]
            a, b = group["bbox"], candidate["bbox"]
            group["bbox"] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
            group["paint_count"] += 1
    return list(groups.values())


def pixmap_rgb(pixmap: Pixmap) -> bytes:
    """Drop alpha from an opaque RGBA pixmap; render with a white background."""
    samples = pixmap.samples
    if samples[3::4].count(255) != pixmap.width * pixmap.height:
        message = "pixmap must be opaque; render with background=(255, 255, 255)"
        raise ValueError(message)
    rgb = bytearray(pixmap.width * pixmap.height * 3)
    rgb[0::3], rgb[1::3], rgb[2::3] = samples[0::4], samples[1::4], samples[2::4]
    return bytes(rgb)


def display_boxes(regions: list[dict[str, Any]], *, scale: float) -> list[list[float]]:
    """Map render pixel bounds to the PDF's rotation-resolved display coordinates."""
    if not math.isfinite(scale) or scale <= 0:
        message = "scale must be positive and finite"
        raise ValueError(message)
    return [[coordinate / scale for coordinate in region["bbox"]] for region in regions]


def benchmark(output: Path, executable: Path | None = None) -> dict[str, Any]:
    """Measure controlled grouping evidence and prose false positives on CPU."""
    import pdfust  # noqa: PLC0415 - only the PDF benchmark requires the extension.
    from bench.feature_cases import page_pdf, text_op  # noqa: PLC0415

    cases = []
    for name, bands in (
        ("invoice-bands", [(40, 650, 520, 34), (40, 550, 520, 34)]),
        ("scientific-headers", [(40, 650, 240, 34), (310, 650, 250, 34)]),
        ("financial-rows", [(40, y, 520, 24) for y in (650, 602, 554, 506)]),
        ("outlined-spaces", [(40, 650, 240, 34), (310, 650, 250, 34)]),
        ("prose-negative", []),
    ):
        operations = [
            (
                f"0 0 0 RG 1 w {x} {y} {w} {h} re S"
                if name == "outlined-spaces"
                else f"0.90 0.94 0.98 rg {x} {y} {w} {h} re f"
            )
            for x, y, w, h in bands
        ]
        for i in range(12):
            y = 660 - i * 24
            operations.append("0 0 0 rg " + text_op(f"Row {i + 1}: description and amount 123.45", 50, y))
        expected = [[x, 792 - y - h, x + w, 792 - y] for x, y, w, h in bands]
        cases.append((name, page_pdf("\n".join(operations)), expected))
    rows = []
    binary = executable or build_executable()
    for name, data, expected in cases:
        document = pdfust.Document(stream=data)
        page = document[0]
        start = time.perf_counter()
        vector = vector_regions(page)
        vector_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        pixmap = page.get_pixmap(dpi=96, background=(255, 255, 255))
        render_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        rgb = pixmap_rgb(pixmap)
        conversion_ms = (time.perf_counter() - start) * 1000
        for threshold in (8, 18, 36):
            timings = []
            for _ in range(3):
                start = time.perf_counter()
                regions = extract_regions(
                    rgb,
                    pixmap.width,
                    pixmap.height,
                    color_distance=threshold,
                    luminance_distance=threshold,
                    min_area=300,
                    executable=binary,
                )
                timings.append((time.perf_counter() - start) * 1000)
            boxes = display_boxes(regions, scale=96 / 72)

            def near(a: Sequence[float], b: Sequence[float]) -> bool:
                return max(abs(x - y) for x, y in zip(a, b, strict=True)) <= 2  # noqa: PLR2004 - display-pixel tolerance.

            vector_hits = sum(any(near(b, r["bbox"]) for r in vector) for b in expected)
            raster_hits = sum(any(near(b, r) for r in boxes) for b in expected)
            extras = sum(not any(near(b, r) for b in expected) for r in boxes)
            rows.append(
                {
                    "case": name,
                    "threshold": threshold,
                    "expected": len(expected),
                    "vector_hits": vector_hits,
                    "raster_hits": raster_hits,
                    "raster_extras": extras,
                    "input_sha256": hashlib.sha256(data).hexdigest(),
                    "expected_boxes": expected,
                    "raster_regions": regions,
                    "vector_regions": vector,
                    "vector_ms": round(vector_ms, 3),
                    "cold_render_ms": round(render_ms, 3),
                    "rgb_conversion_ms": round(conversion_ms, 3),
                    "segmentation_subprocess_ms": round(sorted(timings)[1], 3),
                }
            )
        document.close()
    result = {
        "pdfust_version": pdfust.__version__,
        "dpi": 96,
        "min_area_pixels": 300,
        "connectivity": 4,
        "background_white": 248,
        "rust_source_sha256": hashlib.sha256((ROOT / "bench/color_regions.rs").read_bytes()).hexdigest(),
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    """Run the controlled CPU-only experiment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "bench/results/pdf-master-artifacts/color-regions.json")
    args = parser.parse_args()
    print(json.dumps(benchmark(args.output), indent=2))


if __name__ == "__main__":
    main()
