"""CPU-only orientation/normalization ablation on independent DEV image sources."""

# ruff: noqa: PLC0415
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.generalization_native_audit import _raster
from bench.pipeline_ocr_orientation import recognize
from bench.silver_structure import process_peak_rss


def source_cases() -> list[dict[str, Any]]:
    """Construct compensated display-upright and physically sideways scans."""
    import pylopdf

    cases = []
    specifications = [(f"compensated-{rotation}", rotation, 0, False) for rotation in (90, 180, 270)]
    specifications += [(f"physical-{rotation}", 0, rotation, False) for rotation in (90, 180, 270)]
    specifications += [("mixed-physical-90", 0, 90, True), ("upright-control", 0, 0, False)]
    for identifier, page_rotation, image_rotation, native in specifications:
        with pylopdf.Document() as document:
            page = document.new_page(width=600, height=800)
            page.set_rotation(page_rotation)
            if native:
                page.insert_text((30, 40), "Native header")
            # Display-coordinate insertion compensates the image CTM for /Rotate.
            rect = (100, 150, 500, 330) if image_rotation in (0, 180) else (100, 150, 280, 550)
            page.insert_image(rect, stream=_raster(), rotate=image_rotation)
            cases.append({"id": identifier, "pdf": document.tobytes()})
    return cases


def construction_references() -> dict[str, Any]:
    """Return authored text and corrective angles separately after selection."""
    values = Counter(["Region", "Total", "North", "12", "South", "34"])
    return {
        **{
            f"compensated-{rotation}": {"text": values, "preserved_correction": 0, "normalized_correction": rotation}
            for rotation in (90, 180, 270)
        },
        **{
            f"physical-{rotation}": {
                "text": values,
                "preserved_correction": (-rotation) % 360,
                "normalized_correction": (-rotation) % 360,
            }
            for rotation in (90, 180, 270)
        },
        "mixed-physical-90": {"text": values, "preserved_correction": 270, "normalized_correction": 270},
        "upright-control": {"text": values, "preserved_correction": 0, "normalized_correction": 0},
    }


def run(directory: Path) -> dict[str, Any]:
    """Run all candidate costs before joining independent construction references."""
    import pylopdf

    sources = source_cases()
    directory.mkdir(parents=True, exist_ok=True)
    for source in sources:
        (directory / (source["id"] + ".pdf")).write_bytes(source["pdf"])
    start, cpu = time.perf_counter(), time.process_time()
    engine = pylopdf.OcrEngine(threads=1)
    rows = []
    for source in sources:
        for normalize in (False, True):
            with pylopdf.Document(stream=source["pdf"]) as document:
                original = document.tobytes()
                with pylopdf.Document() as owned:
                    owned.insert_pdf(document)
                    page = owned[0]
                    if normalize:
                        page.set_rotation(0)
                    image = page.get_images()[0]
                    trial = recognize(page, dpi=150, engine=engine, clip=image["bbox"])
                    rows.append(
                        {
                            "id": source["id"],
                            "normalize_rotation": normalize,
                            **trial,
                            "caller_preserved": document.tobytes() == original,
                        }
                    )
            (directory / "progress.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    # Frozen selection has completed before authored expectations are visible.
    references = construction_references()
    for row in rows:
        reference = references[row["id"]]
        expected = reference["normalized_correction" if row["normalize_rotation"] else "preserved_correction"]
        row["expected_correction"] = expected
        row["selected_matches_construction"] = row["selected_rotation"] == expected
        for candidate in row["candidates"]:
            actual = Counter(token for word in candidate["words"] for token in word["text"].split())
            candidate["authored_token_recall"] = sum((actual & reference["text"]).values()) / sum(
                reference["text"].values()
            )
    peak, tool = process_peak_rss()
    result = {
        "schema": 1,
        "scope": "authored DEV orientation; text recall is exact construction comparison",
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": peak,
        "rss_tool": tool,
        "workers": 1,
        "ocr_threads": 1,
        "dpi": 150,
        "rows": rows,
    }
    (directory / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main() -> None:
    """Write the opt-in retained audit without networking or GPU usage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.output)


if __name__ == "__main__":
    main()
