"""Render explicitly authorized frozen schema cases without tuning or reference edits."""

# ruff: noqa: EM101, TRY003, C901, PLC0415, PLR0912
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from PIL import Image, ImageDraw

from bench.generalization_scoring import score_page
from bench.p003_secondary_visual_review import witness_changes
from bench.p003_visual_review import (
    FONT,
    LATIN_FONT,
    RENDER_SETTINGS,
    detector_inference_size,
    digest,
    lexical_tokens,
    lines,
    output_grid,
    read,
    verdicts,
)
from bench.silver import guard_path

CASES = {
    "natural64-crops-sonnet-1024-legacy-r0-c6": {"p3f48fe087a3e6a59b8e5": [0], "pfac04ae9e9cf9e0808a7": [0]},
    "confirmation48-sonnet-1024-r0-c3": {"p0667c835fff3253fac3a": [0, 1]},
}
PLAN_SHA = "333ca142f623837c724276be383ac8006f8ae504ca632ec489c5ff3417bdf743"
RUNTIME_SHA = "da48f3a34238fe11f1a57827628b3208e7e2ce9b28893393a5c226a311e7b956"


def build(root: Path, output: Path) -> Path:
    """Replay strict selected pages and display actual pixels, matrices and witnesses."""
    import pylopdf

    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    plan_path = root / "plans/scoring-audit26-v1.json"
    plan = read(plan_path, receipts)
    if receipts[str(plan_path.resolve())] != PLAN_SHA:
        raise ValueError("Authorized declaration changed")
    runtime_path = root / "trusted-code/scoring-audit26-v2.json"
    read(runtime_path, receipts)
    if receipts[str(runtime_path.resolve())] != RUNTIME_SHA:
        raise ValueError("Trusted audit runtime changed")
    for path in (
        FONT,
        LATIN_FONT,
        Path(__file__),
        Path(__file__).with_name("p003_visual_review.py"),
        Path(__file__).with_name("p003_secondary_visual_review.py"),
    ):
        receipts[str(path.resolve())] = digest(path.read_bytes())
    admitted = []
    for name, pages in CASES.items():
        entry = next(e for e in plan["entries"] if e["name"] == name)
        audit = read(root / "scoring-audit26-v2" / (name + ".json"), receipts)
        if audit["entry"] != entry:
            raise ValueError("Audit entry differs from authorized declaration")
        authorities = {}
        for key in ("report", "evaluation", "frozen", "run_manifest"):
            authorities[key] = read(Path(entry[key]), receipts)
            if receipts[str(Path(entry[key]).resolve())] != entry[key + "_sha256"]:
                raise ValueError("Frozen run authority changed")
        corpus = Path(entry["corpus"])
        read(corpus / "manifest.json", receipts)
        if receipts[str((corpus / "manifest.json").resolve())] != entry["corpus_manifest_sha256"]:
            raise ValueError("Corpus manifest changed")
        targets = read(corpus / "private-targets.json", receipts)
        if receipts[str((corpus / "private-targets.json").resolve())] != entry["targets_sha256"]:
            raise ValueError("Frozen reference changed")
        evaluated = next(e for e in authorities["evaluation"]["runs"] if e["name"] == name)
        for identifier, indexes in pages.items():
            record = next(r for r in authorities["frozen"]["records"] if r["id"] == identifier)
            reference = next(r for r in targets["pages"] if r["id"] == identifier)
            result = next(r for r in authorities["report"]["results"] if r["id"] == identifier)
            score = next(r for r in evaluated["page_scores"] if r["id"] == identifier)
            tables = result["tables"] if not score["error"] else []
            replay = score_page(reference, tables, status=result["status"])
            if any(replay[k] != v for k, v in score.items() if k in replay):
                raise ValueError("Original strict score did not reproduce")
            pdf = guard_path(Path(record["pdf_path"]).resolve())
            receipts[str(pdf)] = digest(pdf.read_bytes())
            if receipts[str(pdf)] != record["pdf_sha256"]:
                raise ValueError("Frozen PDF changed")
            secondary = next(p for p in audit["secondary"]["pages"] if p["id"] == identifier)
            for target_index in indexes:
                pair = next(p for p in secondary["pairs"] if p["target"] == target_index)
                if not any(
                    m["target"] == target_index and m["prediction"] == pair["prediction"] for m in score["matches"]
                ):
                    raise ValueError("Secondary match differs from original strict match")
                if not pair["schema"]["schema_equivalent"]:
                    raise ValueError("Requested case is not accepted by pinned schema audit")
                actual, expected = tables[pair["prediction"]], reference["tables"][target_index]
                if (actual["row_count"], actual["col_count"]) != (expected["row_count"], expected["col_count"]):
                    raise ValueError("These four explicit cases require identical row/column counts")
                if any(
                    lexical_tokens(a) != lexical_tokens(b)
                    for ar, br in zip(actual["values"], expected["values"], strict=True)
                    for a, b in zip(ar, br, strict=True)
                ):
                    raise ValueError("Ordered lexical tokens differ in retained cells")
                edits = []
                for row in pair["content"]["row_alignment"]:
                    for cell in row["cells"]:
                        changes = witness_changes(cell)
                        if changes:
                            edits.append(
                                {
                                    "reference_row": row["reference_row"],
                                    "prediction_row": row["prediction_row"],
                                    "reference_text": cell["reference_text"],
                                    "prediction_text": cell["prediction_text"],
                                    "changes": changes,
                                }
                            )
                admitted.append((name, entry, authorities, identifier, record, reference, score, tables, pair, edits))
    identity = digest(
        json.dumps({"receipts": receipts, "cases": CASES, "renderer": RENDER_SETTINGS}, sort_keys=True).encode()
    )
    batch = guard_path(output.resolve()) / ("schema-source-" + identity[:20])
    if (batch / "provenance.json").exists():
        return batch
    batch.mkdir(parents=True, exist_ok=False)
    evidence = []
    contact_panels = []
    for name, entry, authorities, identifier, record, reference, score, tables, pair, edits in admitted:
        key = identifier + "-T" + str(pair["target"])
        folder = batch / key
        folder.mkdir()
        with pylopdf.Document(record["pdf_path"]) as document:
            page = document[record["page_number"]]
            scale = 2400 / page.rect.width
            pixmap = page.get_pixmap(scale=scale, background=(255, 255, 255))
            original = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples).convert("RGB")
        original.save(folder / "original.png")
        expected, actual = reference["tables"][pair["target"]], tables[pair["prediction"]]
        crop = original.crop(tuple(round(v * scale) for v in expected["bbox"]))
        crop.save(folder / "source-table.png")
        factor = min(760 / crop.width, 1400 / crop.height)
        crop = crop.resize((round(crop.width * factor), round(crop.height * factor)))
        strict = verdicts(reference, tables, score)["output_cells"][pair["prediction"]]
        for policy, cells in (("strict", strict), ("accepted-schema", dict.fromkeys(strict, "success"))):
            grid = output_grid([actual], {"output_cells": {0: cells}}, table_indexes=[pair["prediction"]])
            panel = Image.new("RGB", (1800, max(crop.height, grid.height) + 245), "#f5f7fa")
            draw = ImageDraw.Draw(panel)
            lines(
                draw,
                (20, 10),
                f"Actual source {identifier} T{pair['target']} | actual prediction T{pair['prediction']}",
                1760,
                24,
            )
            scope = (
                "Frozen confirmation audit; no tuning"
                if entry["corpus_kind"] == "confirmation"
                else "Natural64 DEV frozen audit"
            )
            lines(
                draw,
                (20, 50),
                f"{scope} | {name} | detector {detector_inference_size(authorities['frozen'], authorities['report'])}",
                1760,
                18,
            )
            legend = (
                "GREEN: accepted ordered-token schema; not strict reference coordinates. "
                "Whole-table source outline only."
                if policy == "accepted-schema"
                else "STRICT: green exact reference cell; red reference disagreement. "
                "Representation mismatch is not automatically business-value loss."
            )
            lines(draw, (20, 86), legend, 1760, 18)
            counts = pair["content"]["counts"]
            lines(
                draw,
                (20, 125),
                f"All {actual['row_count']} rows and {actual['col_count']} columns preserve ordered cell tokens. "
                f"Alignment units: {counts['matched']} equal, {counts['missing']} missing, "
                f"{counts['substituted']} substituted, {counts['extra']} extra.",
                1760,
                18,
            )
            lines(
                draw,
                (20, 170),
                "Actual source pixels remain intact; output cells are schematic. "
                "Quoted reference/actual strings and changed characters retained separately; no reference rewrite.",
                1760,
                18,
            )
            panel.paste(crop, (20, 235))
            panel.paste(grid, (810, 235))
            if policy == "accepted-schema":
                draw.rectangle((20, 235, 20 + crop.width, 235 + crop.height), outline=(28, 145, 74), width=4)
            panel.save(folder / (policy + ".png"))
            if policy == "accepted-schema":
                contact_panels.append(panel)
        texts = [
            f"R{e['reference_row']} / P{e['prediction_row']}: reference {e['reference_text']!r}; "
            f"actual {e['prediction_text']!r}\n"
            + "; ".join(f"{c['operation']}: {c['reference']!r} -> {c['prediction']!r}" for c in e["changes"])
            for e in edits
        ]
        canvas = Image.new("RGB", (1800, 120 + sum(120 + len(t) // 140 * 24 for t in texts)), "white")
        draw = ImageDraw.Draw(canvas)
        y = (
            lines(
                draw,
                (20, 10),
                "Pinned literal character witnesses; quotes expose spaces. "
                "Alignment units include declared join separators.",
                1760,
                22,
            )
            + 25
        )
        for text in texts:
            y = lines(draw, (20, y), text, 1760, 18) + 16
        canvas.crop((0, 0, 1800, y + 20)).save(folder / "character-witnesses.png")
        evidence.append(
            {
                "case": key,
                "entry": entry,
                "pair": pair,
                "reference_values": expected["values"],
                "actual_values": actual["values"],
                "literal_changes": edits,
                "source_review_status": "Image review pending; no semantic acceptance inferred from tokens alone",
            }
        )
    for path, expected_hash in receipts.items():
        if digest(Path(path).read_bytes()) != expected_hash:
            raise ValueError("Dependency changed during rendering")
    contact = Image.new("RGB", (1800, sum(p.height for p in contact_panels) + 100), "white")
    lines(
        ImageDraw.Draw(contact),
        (20, 10),
        "Four frozen source audits: actual PDF pixels and actual extracted matrices. "
        "Green is accepted ordered-token schema; strict scores and references remain unchanged.",
        1760,
        22,
    )
    offset = 100
    for panel in contact_panels:
        contact.paste(panel, (0, offset))
        offset += panel.height
    contact.save(batch / "four-case-contact-sheet.png")
    (batch / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    (batch / "provenance.json").write_text(
        json.dumps(
            {
                "receipts": receipts,
                "renderer": RENDER_SETTINGS,
                "source_raster_width": 2400,
                "resources": {
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": time.process_time() - cpu,
                    "lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                    "scope": "Single CPU diagnostic process; no inference or tuning",
                },
            },
            indent=2,
        )
        + "\n"
    )
    return batch


def main() -> None:
    """Render four explicit frozen cases from two authorized plan entries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root, args.output))


if __name__ == "__main__":
    main()
