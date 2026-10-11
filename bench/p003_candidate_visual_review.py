"""Compare selected-only RGB candidate output with its frozen blank-image control."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from bench.p003_alignment_visual_review import alignment_grid
from bench.p003_content_visual_review import content_f1, quality_color
from bench.p003_visual_review import FONT, LATIN_FONT, RENDER_SETTINGS, digest, lines, read
from bench.silver import canonical, guard_path

ARMS = ("choice-pplx-512-rgb-r2-c6", "choice-pplx-512-rgb-blank-r0-c6")
CASES = (("p6ef5d3c5c2edb1c109c4", 1), ("p9f92a30432da612d1bcc", 0))
PLAN_SHA = "7ac22cbef52cd9bf3a472632f0d61633e5aa7c5038d5834009416b68d97b11e3"
RUNTIME_SHA = "206806448b0c7410b7a9e82ea9d75a4ac3e8f89568e0af32eb07e828d56369b6"


def selected_page(audit: dict[str, Any], identifier: str) -> dict[str, Any]:
    """Require the frozen primary hash; never read an inherited fallback table list."""
    predictions = audit["primary_predictions"]
    if digest(canonical(predictions)) != audit["entry"]["primary_predictions_sha256"]:
        raise ValueError("Selected-only prediction identity changed")
    return next(page for page in predictions if page["id"] == identifier)


def build(root: Path, output: Path) -> Path:
    """Render two fixed DEV examples from independently verified 64-run evidence."""
    import pylopdf

    root, output = guard_path(root.resolve()), guard_path(output.resolve())
    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    plan_path = root / "plans/incremental-rescore64-v1.json"
    runtime_path = root / "trusted-code/incremental-rescore64-v1.json"
    plan = read(plan_path, receipts)
    read(runtime_path, receipts)
    if receipts[str(plan_path)] != PLAN_SHA or receipts[str(runtime_path)] != RUNTIME_SHA:
        raise ValueError("Frozen candidate audit authority changed")
    audits, frozen = {}, {}
    for name in ARMS:
        entry = next(e for e in plan["entries"] if e["name"] == name)
        audit = read(root / "incremental-rescore64-v1" / (name + ".json"), receipts)
        if audit["entry"] != entry:
            raise ValueError("Candidate declaration changed")
        for key in ("report", "evaluation", "frozen"):
            data = read(Path(entry[key]), receipts)
            if receipts[str(Path(entry[key]).resolve())] != entry[key + "_sha256"]:
                raise ValueError("Candidate source/output authority changed")
            if key == "frozen":
                frozen[name] = data
        audits[name] = audit
    entry = audits[ARMS[0]]["entry"]
    target_path = Path(entry["corpus"]) / "private-targets.json"
    targets = read(target_path, receipts)
    if receipts[str(target_path)] != entry["targets_sha256"]:
        raise ValueError("DEV references changed")
    admitted = []
    for identifier, index in CASES:
        reference = next(p for p in targets["pages"] if p["id"] == identifier)["tables"][index]
        record = next(p for p in frozen[ARMS[0]]["records"] if p["id"] == identifier)
        other = next(p for p in frozen[ARMS[1]]["records"] if p["id"] == identifier)
        if record != other:
            raise ValueError("Matched control uses a different source")
        pdf = guard_path(Path(record["pdf_path"]).resolve())
        receipts[str(pdf)] = digest(pdf.read_bytes())
        if receipts[str(pdf)] != record["pdf_sha256"]:
            raise ValueError("Source PDF changed")
        pages = [selected_page(audits[name], identifier) for name in ARMS]
        pairs = [
            next(
                (
                    p
                    for p in next(p for p in audits[name]["secondary"]["pages"] if p["id"] == identifier)["pairs"]
                    if p["target"] == index
                ),
                None,
            )
            for name in ARMS
        ]
        admitted.append((identifier, index, reference, record, pages, pairs))
    for path in (
        FONT,
        LATIN_FONT,
        Path(__file__),
        Path(__file__).with_name("p003_alignment_visual_review.py"),
        Path(__file__).with_name("p003_content_visual_review.py"),
        Path(__file__).with_name("p003_visual_review.py"),
    ):
        receipts[str(path.resolve())] = digest(path.read_bytes())
    destination = output / ("candidate-selected-" + digest(canonical(receipts))[:20])
    if (destination / "provenance.json").exists():
        return destination
    destination.mkdir(parents=True, exist_ok=False)
    evidence = []
    for identifier, index, reference, record, pages, pairs in admitted:
        with pylopdf.Document(record["pdf_path"]) as document:
            page = document[record["page_number"]]
            scale = 2400 / page.rect.width
            pixmap = page.get_pixmap(scale=scale, background=(255, 255, 255))
            source = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples).convert("RGB")
        source.save(destination / (identifier + "-original.png"))
        box = tuple(round(v * scale) for v in reference["bbox"])
        crop = source.crop(box)
        crop.save(destination / (identifier + f"-T{index}-native-source.png"))
        factor = min(780 / crop.width, 1500 / crop.height)
        crop = crop.resize((round(crop.width * factor), round(crop.height * factor)))
        views, summaries = [], []
        for _name, predicted, pair in zip(ARMS, pages, pairs, strict=True):
            if pair:
                content = pair["content"]
                if not content["supported"]:
                    raise ValueError("Only supported trusted character witnesses can be colored")
                views.append(alignment_grid(content, reference, predicted["tables"][pair["prediction"]]))
                p, r = content["precision"], content["recall"]
                summaries.append(
                    f"P {p:.4f}, R {r:.4f}, F1 {content_f1(p, r):.4f}; "
                    f"structure accepted: {pair['strict_complete'] or pair['schema']['schema_equivalent']}"
                )
            else:
                absent = Image.new("RGB", (980, 350), "white")
                draw = ImageDraw.Draw(absent)
                draw.rectangle((10, 10, 970, 340), outline=quality_color(0), width=5)
                lines(draw, (30, 35), "NO SELECTED OUTPUT FOR THIS REFERENCE TABLE", 900, 25)
                lines(
                    draw,
                    (30, 105),
                    f"Actual selected tables on page: {len(predicted['tables'])}. "
                    "Abstention/missing selection remains missing. No fallback table credit. "
                    "Red is absence of selected output; no physical cell boxes are inferred.",
                    900,
                    21,
                )
                views.append(absent)
                summaries.append("Reference table missing from selected-only output")
        panel = Image.new("RGB", (2820, max(crop.height, *(v.height for v in views)) + 300), "#f5f7fa")
        draw = ImageDraw.Draw(panel)
        lines(
            draw,
            (20, 15),
            f"{identifier} T{index} | PPLX candidate selection, image edge 512 RGB / blank control",
            2780,
            25,
        )
        lines(
            draw,
            (20, 65),
            "DEV natural16. Partial candidate-selection experiment, NOT a complete pipeline. "
            "Actual source left; only verified model-selected complete crops middle/right. "
            "Original strict scores unchanged.",
            2780,
            21,
        )
        lines(
            draw,
            (20, 125),
            "Colors: exact trusted normalized-character group F1, red 0 / yellow 0.5 / green 1; "
            "blank-character groups gray; amber border signals changed span membership. "
            "Content is not semantic/structure correctness.",
            2780,
            20,
        )
        lines(draw, (20, 190), "Original source crop (full page separately retained)", 780, 20)
        for x, name, summary in zip((820, 1820), ARMS, summaries, strict=True):
            lines(draw, (x, 185), name, 980, 19)
            lines(draw, (x, 220), summary, 980, 18)
        panel.paste(crop, (20, 300))
        for x, view in zip((820, 1820), views, strict=True):
            panel.paste(view, (x, 300))
        panel.save(destination / (identifier + f"-T{index}-matched-control.png"))
        evidence.append(
            {
                "id": identifier,
                "target": index,
                "reference": reference,
                "selected_pages": pages,
                "pairs": pairs,
                "source_record": record,
                "source_crop_box": box,
                "resampling": "Pillow RGB BICUBIC; no content replacement",
                "scope": "Selected-only predictions; no retained baseline or duplicate credit",
            }
        )
    for name, expected in receipts.items():
        if digest(Path(name).read_bytes()) != expected:
            raise ValueError("Frozen rendering dependency changed")
    (destination / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    (destination / "provenance.json").write_text(
        json.dumps(
            {
                "receipts": receipts,
                "settings": RENDER_SETTINGS,
                "artifacts": {p.name: digest(p.read_bytes()) for p in destination.glob("*.png")},
                "resources": {
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": time.process_time() - cpu,
                    "lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                },
            },
            indent=2,
        )
        + "\n"
    )
    return destination


def main() -> None:
    """Generate this fixed selected-only diagnostic batch locally."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root, args.output))


if __name__ == "__main__":
    main()
