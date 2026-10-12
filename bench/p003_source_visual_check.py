"""Inspect source transparency and render immutable white-background DEV copies."""

# ruff: noqa: EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from bench.p003_visual_review import LATIN_FONT, digest, lines, read
from bench.silver import guard_path


def onto_white(image: Image.Image) -> Image.Image:
    """Composite original alpha over explicit opaque white, preserving its pixels."""
    rgba = image.convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")


def run(corpus: Path, output: Path, identifiers: list[str]) -> Path:  # noqa: C901
    """Read source paths/families only; never load targets or modify frozen sources."""
    import pdfust

    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    manifest = read(corpus / "manifest.json", receipts)
    records = {r["id"]: r for r in manifest["pages"]}
    if not 1 <= len(identifiers) <= 6 or len(set(identifiers)) != len(identifiers):
        raise ValueError("Select one through six distinct explicit source IDs")
    selected = []
    for identifier in identifiers:
        row = records[identifier]
        record = {k: row[k] for k in ("id", "family", "pdf_path", "pdf_sha256", "page_number")}
        pdf = guard_path(Path(record["pdf_path"]).resolve())
        image = guard_path((corpus / "images" / f"{identifier}.png").resolve())
        receipts[str(pdf)] = digest(pdf.read_bytes())
        receipts[str(image)] = digest(image.read_bytes())
        if receipts[str(pdf)] != record["pdf_sha256"]:
            raise ValueError("Source PDF differs from frozen manifest")
        selected.append((record, image))
    for path in (Path(__file__), Path(__file__).with_name("p003_visual_review.py"), LATIN_FONT):
        receipts[str(path.resolve())] = digest(path.read_bytes())
    settings = {
        "pdf_width": 1800,
        "background": "opaque white (255,255,255)",
        "scope": "source-only diagnostic; no model output, gold or quality verdicts",
        "native_pdf_render": "pdfust get_pixmap RGBA, explicit Pillow alpha composite",
        "source_png_copy": "exact original RGBA over white; no resizing",
    }
    identity = digest(
        json.dumps({"receipts": receipts, "ids": identifiers, "settings": settings}, sort_keys=True).encode()
    )
    batch = guard_path(output.resolve()) / identity[:20]
    if (batch / "provenance.json").exists():
        return batch
    batch.mkdir(parents=True, exist_ok=False)
    panels, findings = [], []
    for record, image_path in selected:
        directory = batch / record["id"]
        directory.mkdir()
        with Image.open(image_path) as original:
            rgba = original.convert("RGBA")
            alpha = rgba.getchannel("A")
            stats: dict[str, Any] = {
                "mode": original.mode,
                "size": list(original.size),
                "channel_extrema": rgba.getextrema(),
                "transparent_pixels": alpha.histogram()[0],
                "total_pixels": original.width * original.height,
                "corner_rgba": rgba.getpixel((0, 0)),
            }
            onto_white(original).save(directory / "frozen-png-over-white.png")
        with pdfust.Document(record["pdf_path"]) as document:
            page = document[record["page_number"]]
            pixmap = page.get_pixmap(scale=1800 / page.rect.width)
            raw = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples)
            rendered = onto_white(raw)
        rendered.save(directory / "pdf-render-over-white.png")
        panel = Image.new("RGB", (1800, rendered.height + 125), "white")
        draw = ImageDraw.Draw(panel)
        lines(draw, (20, 10), f"Actual source PDF | {record['id']} | {record['family']}", 1760, 24)
        lines(
            draw,
            (20, 55),
            "Explicit white diagnostic background. Frozen sources unchanged. Source-only: no scoring.",
            1760,
            20,
        )
        panel.paste(rendered, (0, 125))
        panel.save(directory / "source-view.png")
        panels.append(panel)
        findings.append(
            {
                **record,
                "frozen_png_statistics": stats,
                "cause": "All RGB channels black; ink visibility encoded by alpha, transparent background"
                if stats["channel_extrema"][:3] == ((0, 0), (0, 0), (0, 0))
                else "Inspect retained RGBA statistics",
            }
        )
    contact = Image.new(
        "RGB",
        (1800 * min(len(panels), 2), sum(max(p.height for p in panels[i : i + 2]) for i in range(0, len(panels), 2))),
        "white",
    )
    y = 0
    for index in range(0, len(panels), 2):
        group = panels[index : index + 2]
        for column, panel in enumerate(group):
            contact.paste(panel, (column * 1800, y))
        y += max(p.height for p in group)
    contact.save(batch / "source-contact-sheet.png")
    for receipt_path, expected in receipts.items():
        if digest(Path(receipt_path).read_bytes()) != expected:
            raise ValueError("A source or rendering dependency changed during inspection")
    provenance = {
        "batch_sha256": identity,
        "inputs": receipts,
        "settings": settings,
        "pages": findings,
        "source_files_unchanged_verified": True,
        "resources": {
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "scope": "single CPU renderer; no inference/GPU/subprocess; concurrency one",
            "tool": "monotonic/process_time/getrusage Linux lifetime peak; utilization unmeasured",
        },
    }
    (batch / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return batch


def main() -> None:
    """Run a bounded source-only visual check once."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", nargs="+", required=True)
    args = parser.parse_args()
    print(run(args.corpus, args.output, args.ids))


if __name__ == "__main__":
    main()
