"""A003 fresh authored DEV topology variations evaluated against frozen A001 rules."""

# ruff: noqa: EM101, TRY003, PLC0415, PLR2004
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path
from typing import Any, TypedDict

from bench.borderless_challenge import score
from bench.feature_cases import text_op
from bench.rolling_rows import assemble
from bench.silver import canonical, guard_path, sha, write_json
from bench.silver_layouts import _pdf
from bench.silver_structure import observed_table, process_peak_rss


class RobustnessDesign(TypedDict):
    """Concrete declared generator inputs retained in the pre-extraction manifest."""

    version: int
    seed: int
    table_pages: int
    prose_pages: int
    total_rows: list[int]
    columns: list[int]
    font_sizes: list[int]
    continuation_lines: list[int]
    blank_rule: str
    totals_rule: str
    semantic_scope: str


DESIGN: RobustnessDesign = {
    "version": 1,
    "seed": 813207,
    "table_pages": 16,
    "prose_pages": 8,
    "total_rows": [2, 3, 6, 8],
    "columns": [2, 3, 5],
    "font_sizes": [8, 10, 14],
    "continuation_lines": [0, 1, 2],
    "blank_rule": "optional interior data cell; never header or row key",
    "totals_rule": "last physical record on selected pages is a literal Total record",
    "semantic_scope": "source-visible table/narrative instructions; authored DEV only; no merged span claims",
}


def generate_cases() -> list[dict[str, Any]]:  # noqa: C901, PLR0912
    """Produce immutable source PDFs and separate authored targets before extraction."""
    rng = random.Random(DESIGN["seed"])  # noqa: S311 - frozen reproducible DEV authoring
    cases: list[dict[str, Any]] = []
    for setting in range(DESIGN["table_pages"]):
        rows = DESIGN["total_rows"][setting % 4]
        columns = DESIGN["columns"][setting % 3]
        size = DESIGN["font_sizes"][(setting // 2) % 3]
        wraps = DESIGN["continuation_lines"][setting % 3]
        total = setting % 4 in (2, 3)
        blank = setting % 3 == 2
        right = [bool(rng.getrandbits(1)) for _ in range(columns)]
        xs = [48 + c * (510 / columns) for c in range(columns)]
        lead = max(42, (wraps + 1) * (size + 5) + 10)
        values = [["Station", *[f"Metric{c}" for c in range(1, columns)]]]
        for row in range(1, rows):
            label = "Total" if total and row == rows - 1 else f"Station{row}" + (" detail" * wraps)
            values.append([label, *[str(rng.randint(1, 999)) for _ in range(1, columns)]])
        if blank and rows > 2:
            values[1][columns - 1] = ""
        for positive in (True, False) if setting < 8 else (True,):
            ops = [text_op("Station observations", 48, 752, size=16)]
            statement = (
                "Read each row as one station record."
                if positive
                else "Read each column downward as an independent narrative."
            )
            ops.append(text_op(statement, 48, 718, size=10))
            authored_slots = []
            if positive:
                for row, cells in enumerate(values):
                    for col, value in enumerate(cells):
                        if not value:
                            continue
                        lines = value.split() if col == 0 and row > 0 and value != "Total" else [value]
                        baseline = 674 - row * lead
                        for line_index, line in enumerate(lines):
                            x = xs[col]
                            if col and right[col] and row:
                                x += (510 / columns) * 0.65 - len(line) * size * 0.556
                            y = baseline - line_index * (size + 5)
                            ops.append(text_op(line, x, y, size=size))
                            # Expected source ownership comes from authored slot placement, not extractor candidates.
                            authored_slots.append(
                                {"row": row, "column": col, "baseline": 792 - y, "x": x, "text": line, "size": size}
                            )
                tables = [
                    {
                        "row_count": rows,
                        "col_count": columns,
                        "values": values,
                        "spans": [
                            {"row": r, "column": c, "row_span": 1, "column_span": 1}
                            for r in range(rows)
                            for c in range(columns)
                        ],
                    }
                ]
            else:
                # Baselines and column starts match the companion table, while each column expresses its own narrative.
                for col in range(columns):
                    for row in range(rows):
                        lines = (
                            [
                                f"Station{row}" if row % 3 == 0 else str(10 + row + col),
                                "awaits review" if row % 3 == 1 else "records units",
                            ]
                            if wraps
                            else [f"Station{row} {10 + col + row}"]
                        )
                        for index, line in enumerate(lines):
                            ops.append(text_op(line, xs[col], 674 - row * lead - index * (size + 5), size=size))
                tables = []
            ops.append(text_op("Review complete", 48, 45, size=10))
            case_id = f"fresh-{len(cases):03}"
            cases.append(
                {
                    "id": case_id,
                    "pdf": _pdf(["\n".join(ops)], setting, "robustness", "1.4"),
                    "target": {
                        "id": case_id,
                        "kind": "borderless" if positive else "prose",
                        "tables": tables,
                        "authored_slots": authored_slots,
                        "setting": setting,
                        "wrap": wraps,
                        "font_size": size,
                        "row_count": rows,
                        "columns": columns,
                        "blank_cell": blank and rows > 2,
                        "total_row": total,
                        "numeric_alignment": right,
                    },
                }
            )
    return cases


def exact_source_ownership(
    target: dict[str, Any], source: dict[str, Any], candidate: dict[str, Any] | None
) -> dict[str, Any]:
    """Map uniquely authored placement lines to extracted words after source/candidates are frozen."""
    intended: dict[tuple[int, int], list[str]] = {}
    unmapped = []
    for word in source["words"]:
        matches = [
            slot
            for slot in target["authored_slots"]
            if abs(word["bbox"][1] - (slot["baseline"] - slot["size"] * 0.8)) < slot["size"] * 0.25
            and slot["x"] - 0.1 <= word["bbox"][0] <= slot["x"] + len(slot["text"]) * slot["size"]
            and word["text"] in slot["text"].split()
        ]
        if len(matches) == 1:
            key = (matches[0]["row"], matches[0]["column"])
            intended.setdefault(key, []).append(word["id"])
        elif matches:
            unmapped.append(word["id"])
    actual = (
        {
            (i // candidate["col_count"], i % candidate["col_count"]): cell["source_ids"]
            for i, cell in enumerate(candidate["cells"])
        }
        if candidate
        else {}
    )
    correct = sum(set(ids) == set(actual.get(slot, [])) for slot, ids in intended.items())
    owned = sum(len(set(ids) & set(actual.get(slot, []))) for slot, ids in intended.items())
    return {
        "intended_word_ids": sum(len(ids) for ids in intended.values()),
        "correct_slot_word_ids": owned,
        "intended_nonempty_slots": len(intended),
        "exact_nonempty_slots": correct,
        "ambiguous_mapping_word_ids": unmapped,
        "source_slot_exact": bool(intended) and correct == len(intended) and not unmapped,
    }


def run(directory: Path) -> dict[str, Any]:
    """Freeze authored inputs first, then extract source, freeze candidates, and score separately."""
    import pylopdf

    directory = guard_path(directory)
    generator_hash = sha(Path(__file__).read_bytes())
    assembler_hash = sha(Path(__file__).with_name("rolling_rows.py").read_bytes())
    cases = generate_cases()
    identity = sha(canonical({"design": DESIGN, "sources": [sha(c["pdf"]) for c in cases]}))
    output = directory / identity[:16]
    if output.exists():
        raise ValueError("Robustness corpus already frozen; retain originals and use existing artifacts")
    output.mkdir(parents=True)
    write_json(
        output / "design.json",
        {"design": DESIGN, "generator_sha256": generator_hash, "assembler_sha256": assembler_hash},
    )
    write_json(output / "private-targets.json", [c["target"] for c in cases])
    pdfs = output / "pdfs"
    pdfs.mkdir()
    for case in cases:
        (pdfs / (case["id"] + ".pdf")).write_bytes(case["pdf"])
    write_json(
        output / "manifest.json",
        {
            "split": "DEV",
            "label_status": "authored; not independently adjudicated",
            "dataset_sha256": identity,
            "cases": [{"id": c["id"], "pdf_sha256": sha(c["pdf"])} for c in cases],
        },
    )
    start, cpu = time.perf_counter(), time.process_time()
    sources, frozen_pages = [], []
    for case in cases:
        with pylopdf.open(stream=case["pdf"]) as document:
            page = document[0]
            words = [{"id": f"w{i}", "text": w[4], "bbox": list(w[:4])} for i, w in enumerate(page.get_text("words"))]
            image_path = output / (case["id"] + ".png")
            image_path.write_bytes(page.render(dpi=120, background=(255, 255, 255)))
            source = {
                "id": case["id"],
                "words": words,
                "page_size": list(page.rect),
                "image_path": str(image_path),
                "vector_candidates": [observed_table(t) for t in page.find_tables()],
                "text_candidates": [observed_table(t) for t in page.find_tables(strategy="text")],
            }
            sources.append(source)
            frozen_pages.append(
                {"id": case["id"], "alternatives": [assemble(source, v) for v in ("physical", "rolling")]}
            )
    source_payload = {"pages": sources}
    source_bytes = canonical(source_payload) + b"\n"
    (output / "source-evidence.json").write_bytes(source_bytes)
    candidate_payload = {
        "schema": 1,
        "source_sha256": sha(source_bytes),
        "pages": frozen_pages,
        "rules_source_sha256": assembler_hash,
    }
    write_json(output / "candidates-frozen.json", candidate_payload)
    # Scoring starts after all PDF/source/candidate bytes have been retained.
    results = []
    for case, source, frozen in zip(cases, sources, frozen_pages, strict=True):
        native_tables = source["vector_candidates"] + source["text_candidates"]
        native_best = max(
            [score(case["target"], [t]) for t in native_tables],
            key=lambda s: (s["exact_cells"], s["owned_values"], s["owned_words"]),
            default=score(case["target"], []),
        )
        results.append(
            {"id": case["id"], "route": "native-ceiling", "kind": case["target"]["kind"], "scores": native_best}
        )
        for alternative in frozen["alternatives"]:
            tables = alternative["candidates"]
            owned = [i for t in tables for cell in t["cells"] for i in cell["source_ids"]]
            conserved = Counter(owned + alternative["unresolved_ids"]) == Counter(w["id"] for w in source["words"])
            results.append(
                {
                    "id": case["id"],
                    "route": alternative["variant"],
                    "kind": case["target"]["kind"],
                    "scores": score(case["target"], tables),
                    "source_conservation": conserved,
                    "ownership": exact_source_ownership(case["target"], source, tables[0] if tables else None),
                }
            )
    rss, tool = process_peak_rss()
    summary = {
        "dataset_sha256": identity,
        "corpus": str(output),
        "pages": len(cases),
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"perf_counter/process_time; {tool}; sequential CPU; lifetime RSS; no sampling",
        "routes": {
            route: {
                kind: {
                    "pages": sum(r["route"] == route and r["kind"] == kind for r in results),
                    **{
                        key: sum(r["scores"][key] for r in results if r["route"] == route and r["kind"] == kind)
                        for key in (
                            "exact_page",
                            "exact_cells",
                            "exact_spans",
                            "owned_values",
                            "owned_words",
                            "false_positive_page",
                        )
                    },
                }
                for kind in ("borderless", "prose")
            }
            for route in ("native-ceiling", "physical", "rolling")
        },
    }
    write_json(output / "private-scores.json", {"rows": results})
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    """Build and score the declared CPU DEV check, with no hosted client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))


if __name__ == "__main__":
    main()
