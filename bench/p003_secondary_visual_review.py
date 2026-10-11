"""Show pinned DEV strict results beside schema and character alignment evidence."""

# ruff: noqa: EM101, TRY003, C901, PLC0415, PLR0912
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from bench.p003_visual_review import (
    FONT,
    LATIN_FONT,
    RENDER_SETTINGS,
    detector_inference_size,
    digest,
    lines,
    output_grid,
    read,
    run,
    verdicts,
)
from bench.silver import guard_path

PAGE = "p1bfa52a41a5e15015698"


def witness_changes(cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Expose literal character evidence, including spaces, without semantic labels."""
    result = []
    for witness in cell["character_witness"]:
        operation = witness["operation"]
        if operation == "equal":
            if (
                cell["reference_text"][witness["reference_index"]]
                != cell["prediction_text"][witness["prediction_index"]]
            ):
                raise ValueError("Pinned equality witness contradicts retained literal text")
            continue
        result.append(
            {
                "operation": operation,
                "reference": None
                if witness["reference_index"] is None
                else cell["reference_text"][witness["reference_index"]],
                "prediction": None
                if witness["prediction_index"] is None
                else cell["prediction_text"][witness["prediction_index"]],
            }
        )
    return result


def build(audit_path: Path, output: Path) -> Path:
    """Render two explicit matched natural16 tables; retain hashes and actual values."""
    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    audit = read(audit_path, receipts)
    authority_root = audit_path.resolve().parent.parent
    declaration = authority_root / "plans" / "scoring-audit26-v1.json"
    read(declaration, receipts)
    if receipts[str(declaration)] != "333ca142f623837c724276be383ac8006f8ae504ca632ec489c5ff3417bdf743":
        raise ValueError("Pinned audit declaration changed")
    read(authority_root / "trusted-code" / "scoring-audit26-v1.json", receipts)
    entry = audit["entry"]
    if entry["corpus_kind"] != "dev" or Path(entry["corpus"]).name != "natural16":
        raise ValueError("This bounded visual review admits natural16 DEV only")
    for key in ("report", "evaluation", "frozen", "run_manifest"):
        if digest(guard_path(Path(entry[key]).resolve()).read_bytes()) != entry[key + "_sha256"]:
            raise ValueError("Pinned source authority changed: " + key)
        receipts[str(Path(entry[key]).resolve())] = entry[key + "_sha256"]
    corpus, run_dir = Path(entry["corpus"]), Path(entry["report"]).parent
    targets = read(corpus / "private-targets.json", receipts)
    if receipts[str((corpus / "private-targets.json").resolve())] != entry["targets_sha256"]:
        raise ValueError("Pinned targets changed")
    original_batch = run(run_dir, corpus, output, [PAGE])
    evaluation = read(Path(entry["evaluation"]), receipts)
    frozen = read(Path(entry["frozen"]), receipts)
    report = read(Path(entry["report"]), receipts)
    result = read(run_dir / (PAGE + "-result.json"), receipts)
    reference = next(p for p in targets["pages"] if p["id"] == PAGE)
    score = next(p for p in evaluation["runs"][0]["page_scores"] if p["id"] == PAGE)
    marks = verdicts(reference, result["tables"], score)
    secondary = next(p for p in audit["secondary"]["pages"] if p["id"] == PAGE)
    record = next(p for p in frozen["records"] if p["id"] == PAGE)
    pdf = guard_path(Path(record["pdf_path"]).resolve())
    receipts[str(pdf)] = digest(pdf.read_bytes())
    if receipts[str(pdf)] != record["pdf_sha256"]:
        raise ValueError("Frozen PDF changed")
    for path in (FONT, LATIN_FONT, Path(__file__), Path(__file__).with_name("p003_visual_review.py")):
        receipts[str(path.resolve())] = digest(path.read_bytes())
    identity = digest(
        json.dumps({"receipts": receipts, "tables": [0, 8], "settings": RENDER_SETTINGS}, sort_keys=True).encode()
    )
    batch = guard_path(output.resolve()) / ("secondary-" + identity[:20])
    if (batch / "provenance.json").exists():
        return batch
    batch.mkdir(parents=True, exist_ok=False)
    import pylopdf

    with pylopdf.Document(pdf) as document:
        page = document[record["page_number"]]
        scale = 2400 / page.rect.width
        pixmap = page.get_pixmap(scale=scale, background=(255, 255, 255))
        source = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples).convert("RGB")
    source.save(batch / "original.png")
    evidence = []
    for target_index in (0, 8):
        pair = next(p for p in secondary["pairs"] if p["target"] == target_index)
        pred = pair["prediction"]
        if not any(m["target"] == target_index and m["prediction"] == pred for m in score["matches"]):
            raise ValueError("Secondary match differs from retained strict match")
        content, schema = pair["content"], pair["schema"]
        if not content["supported"]:
            raise ValueError("Requested control is not supported by pinned content metric")
        edits = []
        for row in content["row_alignment"]:
            for cell in row["cells"]:
                changes = witness_changes(cell)
                if changes:
                    edits.append(
                        {
                            "reference_row": row["reference_row"],
                            "prediction_row": row["prediction_row"],
                            "reference_columns": cell["reference_columns"],
                            "prediction_columns": cell["prediction_columns"],
                            "reference_text": cell["reference_text"],
                            "prediction_text": cell["prediction_text"],
                            "changes": changes,
                        }
                    )
        evidence.append({"target": target_index, "prediction": pred, "pair": pair, "literal_changes": edits})
        bbox = reference["tables"][target_index]["bbox"]
        crop = source.crop(tuple(round(v * scale) for v in bbox))
        crop.save(batch / f"source-T{target_index}.png")
        factor = min(760 / crop.width, 1600 / crop.height)
        crop = crop.resize((round(crop.width * factor), round(crop.height * factor)))
        grid = output_grid(
            [result["tables"][pred]], {"output_cells": {0: marks["output_cells"][pred]}}, table_indexes=[pred]
        )
        panel = Image.new("RGB", (1800, max(crop.height, grid.height) + 275), "#f5f7fa")
        draw = ImageDraw.Draw(panel)
        lines(
            draw, (20, 10), f"Actual newspaper source T{target_index} | actual extracted prediction T{pred}", 1760, 24
        )
        lines(
            draw,
            (20, 48),
            f"{entry['name']} | detector {detector_inference_size(frozen, report)} | crop 1024 | DEV {PAGE}",
            1760,
            18,
        )
        lines(
            draw,
            (20, 85),
            "Grid colors retain strict scoring: green exact reference cell; red reference disagreement. "
            "Red alone is not extraction failure.",
            1760,
            18,
        )
        label = (
            f"Accepted 3/4-column schema: all {schema['same_position_row_token_matches']} rows including header; "
            f"fixed partition {schema['fine_column_groups']}."
            if schema["schema_equivalent"]
            else f"Partial-content control: schema equivalence false ({schema['reason']})."
        )
        lines(draw, (20, 126), label, 1760, 20)
        c = content["counts"]
        lines(
            draw,
            (20, 166),
            f"Character evidence: {c['matched']} equal, {c['missing']} missing, {c['substituted']} substituted, "
            f"{c['extra']} extra; recall {content['recall']:.5f}, precision {content['precision']:.5f}.",
            1760,
            18,
        )
        lines(
            draw,
            (20, 202),
            "Characters include retained spaces and join separators; these are representation evidence, "
            "not automatic semantic error labels. Source pixels have no invented cell masks.",
            1760,
            18,
        )
        panel.paste(crop, (20, 260))
        panel.paste(grid, (810, 260))
        panel.save(batch / f"comparison-T{target_index}.png")
        if schema["schema_equivalent"]:
            accepted = output_grid(
                [result["tables"][pred]],
                {"output_cells": {0: dict.fromkeys(marks["output_cells"][pred], "success")}},
                table_indexes=[pred],
            )
            corrected = panel.copy()
            accepted_draw = ImageDraw.Draw(corrected)
            accepted_draw.rectangle((0, 80, 1800, 123), fill="#f5f7fa")
            lines(
                accepted_draw,
                (20, 85),
                "GREEN: accepted alternative schema (not strict reference coordinates). "
                "All actual output cells belong to the verified whole-table schema; this is a separate secondary view.",
                1760,
                18,
            )
            corrected.paste(accepted, (810, 260))
            accepted_draw.rectangle((20, 260, 20 + crop.width, 260 + crop.height), outline=(28, 145, 74), width=4)
            corrected.save(batch / f"accepted-schema-T{target_index}.png")
        else:
            captioned = Image.new("RGB", (1800, panel.height + 75), "#f5f7fa")
            captioned.paste(panel, (0, 0))
            lines(
                ImageDraw.Draw(captioned),
                (20, panel.height + 10),
                "Visible business-value losses: Motor City is absent; Grand Rapids values are altered. "
                "Removed dot leaders and fraction/GB encodings also affect character counts; "
                "decoration differences are not missing business values.",
                1760,
                18,
            )
            captioned.save(batch / f"partial-content-control-T{target_index}.png")
        rows = [
            f"R{e['reference_row']} -> P{e['prediction_row']} | reference {e['reference_text']!r} | "
            f"actual {e['prediction_text']!r}\n"
            + "; ".join(f"{w['operation']}: {w['reference']!r} -> {w['prediction']!r}" for w in e["changes"])
            for e in edits
        ]
        canvas = Image.new("RGB", (1800, 150 + sum(100 + len(r) // 150 * 24 for r in rows)), "white")
        draw = ImageDraw.Draw(canvas)
        y = (
            lines(
                draw,
                (20, 15),
                f"T{target_index}: exact pinned character witnesses. "
                "Quotes expose spaces; row/column indexes are zero-based.",
                1760,
                22,
            )
            + 40
        )
        for row in rows:
            y = lines(draw, (20, y), row, 1760, 18) + 16
        canvas.crop((0, 0, 1800, y + 20)).save(batch / f"character-evidence-T{target_index}.png")
    for path, expected in receipts.items():
        if digest(Path(path).read_bytes()) != expected:
            raise ValueError("Dependency changed during rendering")
    (batch / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    (batch / "provenance.json").write_text(
        json.dumps(
            {
                "receipts": receipts,
                "original_strict_batch": str(original_batch),
                "renderer": RENDER_SETTINGS,
                "resources": {
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": time.process_time() - cpu,
                    "lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                    "scope": "single CPU process; lifetime peak RSS",
                },
            },
            indent=2,
        )
        + "\n"
    )
    return batch


def main() -> None:
    """Render one bounded pinned newspaper comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.audit, args.output))


if __name__ == "__main__":
    main()
