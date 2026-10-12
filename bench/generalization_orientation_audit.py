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
from bench.pipeline_ocr_orientation import evidence, recognize
from bench.silver_structure import process_peak_rss


def source_cases() -> list[dict[str, Any]]:
    """Construct compensated display-upright and physically sideways scans."""
    import pdfust

    cases = []
    specifications = [(f"compensated-{rotation}", rotation, 0, False) for rotation in (90, 180, 270)]
    specifications += [(f"physical-{rotation}", 0, rotation, False) for rotation in (90, 180, 270)]
    specifications += [("mixed-physical-90", 0, 90, True), ("upright-control", 0, 0, False)]
    for identifier, page_rotation, image_rotation, native in specifications:
        with pdfust.Document() as document:
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
    import pdfust

    sources = source_cases()
    directory.mkdir(parents=True, exist_ok=True)
    for source in sources:
        (directory / (source["id"] + ".pdf")).write_bytes(source["pdf"])
    start, cpu = time.perf_counter(), time.process_time()
    engine = pdfust.OcrEngine(threads=1)
    rows = []
    for source in sources:
        for normalize in (False, True):
            with pdfust.Document(stream=source["pdf"]) as document:
                original = document.tobytes()
                with pdfust.Document() as owned:
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


DENSE_IDS = ("p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a")
DENSE_DPIS = (150, 300)


def dense_audit(manifest_path: Path, directory: Path) -> dict[str, Any]:
    """Compare fixed upright whitespace source inventories without quality labels."""
    import pdfust
    from bench.pipeline_ocr_sources import SOURCE_ADMISSION_VERSION, SourceAdmissionError, extract

    manifest = json.loads(manifest_path.read_text())
    selected = {row["id"]: row for row in manifest["pages"] if row["id"] in DENSE_IDS}
    if set(selected) != set(DENSE_IDS):
        message = "Explicit dense source IDs are missing"
        raise ValueError(message)
    directory.mkdir(parents=True, exist_ok=True)
    previous = directory / "dense-results.json"
    if (
        previous.exists()
        and json.loads(previous.read_text()).get("source_admission_version") != SOURCE_ADMISSION_VERSION
    ):
        message = "Retained dense results use another admission version; choose a separate output arm"
        raise ValueError(message)
    start, cpu = time.perf_counter(), time.process_time()
    engine = pdfust.OcrEngine(threads=1)
    rows = []
    for identifier in DENSE_IDS:
        record = selected[identifier]
        for dpi in DENSE_DPIS:
            started, consumed = time.perf_counter(), time.process_time()
            row = {
                "id": identifier,
                "dpi": dpi,
                "tokenization": "whitespace",
                "orientation": "fixed",
                "pdf_path": record["pdf_path"],
                "page_number": record.get("page_number", 0),
            }
            with pdfust.open(record["pdf_path"]) as document:
                before = document.tobytes()
                try:
                    extracted = extract(
                        document[row["page_number"]], mode="empty", dpi=dpi, engine=engine, tokenization="whitespace"
                    )
                    row["extraction"] = extracted
                    recognized = extracted["diagnostics"]["recognized"]
                    row["evidence"] = {
                        "recognized_box_count": len(recognized),
                        "source_word_count": len(extracted["source"]["words"]),
                        **evidence(recognized),
                    }
                except Exception as error:
                    row["error"] = f"{type(error).__name__}: {error}"
                    if isinstance(error, SourceAdmissionError):
                        row["before_limit_diagnostics"] = error.diagnostics
                row["caller_preserved"] = document.tobytes() == before
            row.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - consumed)
            row["process_peak_rss_bytes"], row["rss_tool"] = process_peak_rss()
            rows.append(row)
            (directory / "dense-progress.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    result = {
        "schema": 1,
        "settings": {
            "ids": DENSE_IDS,
            "dpi": DENSE_DPIS,
            "workers": 1,
            "ocr_threads": 1,
            "tokenization": "whitespace",
            "orientation": "fixed",
        },
        "source_admission_version": SOURCE_ADMISSION_VERSION,
        "scope": "source inventories only; no reference text or table recall",
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "rows": rows,
    }
    (directory / "dense-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main() -> None:
    """Write the opt-in retained audit without networking or GPU usage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dense-manifest", type=Path)
    args = parser.parse_args()
    if args.dense_manifest is None:
        run(args.output)
    else:
        dense_audit(args.dense_manifest, args.output)


if __name__ == "__main__":
    main()
