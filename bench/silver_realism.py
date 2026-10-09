"""Freeze authored DEV documents with source semantics and uncertainty kept separate.

This cohort repairs the cue-bearing rolling-v1 construction. It is still synthetic
and related to its predecessor; it is not an independent natural-document test.
"""

# Explicit authored layouts and heterogeneous artifact records are intentional.
# ruff: noqa: EM101, TRY003, PLC0415, PLR2004, ISC004
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.feature_cases import page_pdf, text_op
from bench.silver import canonical, guard_path, sha, write_json
from bench.silver_structure import observed_table, process_peak_rss

DESIGN: dict[str, Any] = {
    "version": 2,
    "seed": 813208,
    "table_pages": 16,
    "prose_pages": 8,
    "ambiguous_pages": 4,
    "total_rows": [2, 3, 6, 8],
    "columns": [2, 3, 5],
    "font_sizes": [8, 10, 14],
    "continuation_lines": [0, 1, 2],
    "blank_rule": "optional interior data cell; never header or row key",
    "totals_rule": "selected final records sum the preceding nonblank count values",
    "semantic_scope": "authored operational records, continuous prose, and unscored ambiguous fragments",
    "label_status": "authored DEV silver; reviewed construction, no independent human adjudication",
    "negative_scope": "continuous grammatical paragraphs; numerals occur inside sentences",
    "ambiguity_policy": "exclude ambiguous-unscored pages from binary admission and exact structure metrics",
    "source_policy": "common page furniture; opaque shuffled IDs; no labels, instructions, or gold in PDF metadata",
    "ancestry": "rolling-v1 geometry interventions; common repository PDF serializer",
    "license": "MIT",
    "provenance": "repository-authored fictional operational content; no external document source",
}

SITES = ("North", "South", "West", "East", "River", "Hill", "Port")
TITLES = ("Service review", "Depot activity", "Weekly update", "Operations digest")
HEADERS = ("Depot", "Received", "Released", "Pending", "Returned")


def _furniture(setting: int) -> list[str]:
    return [
        text_op(TITLES[setting % len(TITLES)], 48, 746, size=18, font="F2"),
        text_op("Week ending 9 October 2026", 48, 718, size=10),
        text_op("Operations office", 48, 42, size=9),
        text_op("1", 553, 42, size=9),
    ]


def _width(text: str, size: float) -> float:
    """Conservatively size authored lines; actual source bounds are checked separately."""
    # Helvetica's widest uppercase glyph is M/W at less than one em. Use a
    # conservative per-character estimate for wrapping without reading extraction.
    return sum(0.9 if char in "MW@%" else 0.28 if char in " il.,:;!'" else 0.60 for char in text) * size


def _wrap(text: str, width: float, size: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if current and _width(candidate, size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _table(setting: int, rng: random.Random) -> dict[str, Any]:
    rows = DESIGN["total_rows"][setting % 4]
    columns = DESIGN["columns"][setting % 3]
    size = DESIGN["font_sizes"][(setting // 2) % 3]
    wraps = DESIGN["continuation_lines"][setting % 3]
    total = setting % 4 in (2, 3)
    blank = setting % 3 == 2 and rows > 2
    right = [False, *[bool(rng.getrandbits(1)) for _ in range(columns - 1)]]
    xs = [48 + col * (510 / columns) for col in range(columns)]
    lead = max(38, (wraps + 1) * (size + 4) + 10)
    values = [list(HEADERS[:columns])]
    for row in range(1, rows):
        label = " ".join([SITES[row - 1], "collection", "annex"][: wraps + 1])
        values.append([label, *[str(rng.randint(12, 180)) for _ in range(columns - 1)]])
    if blank:
        values[1][-1] = ""
    if total:
        values[-1] = [
            "Total",
            *[str(sum(int(values[row][col] or 0) for row in range(1, rows - 1))) for col in range(1, columns)],
        ]
    ops = _furniture(setting)
    slots = []
    for row, cells in enumerate(values):
        for col, value in enumerate(cells):
            if not value:
                continue
            lines = value.split() if col == 0 and row > 0 else [value]
            for line_index, line in enumerate(lines):
                x = xs[col]
                if col and right[col] and row:
                    x += (510 / columns) * 0.78 - len(line) * size * 0.556
                y = 662 - row * lead - line_index * (size + 4)
                ops.append(text_op(line, x, y, size=size))
                slots.append({"row": row, "column": col, "baseline": 792 - y, "x": x, "text": line, "size": size})
    target = {
        "kind": "borderless",
        "truth_status": "authored-table",
        "binary_admission_eligible": True,
        "semantic_basis": "one depot per record and named count measures across columns",
        "tables": [
            {
                "row_count": rows,
                "col_count": columns,
                "values": values,
                "spans": [
                    {"row": row, "column": col, "row_span": 1, "column_span": 1}
                    for row in range(rows)
                    for col in range(columns)
                ],
            }
        ],
        "authored_slots": slots,
        "setting": setting,
        "wrap": wraps,
        "font_size": size,
        "row_count": rows,
        "columns": columns,
        "blank_cell": blank,
        "total_row": total,
        "numeric_alignment": right,
    }
    return {"pdf": page_pdf("\n".join(ops)), "target": target}


def _paragraphs(setting: int, col: int) -> list[str]:
    site = SITES[(setting + col) % len(SITES)]
    other = SITES[(setting + col + 2) % len(SITES)]
    units = 24 + setting * 7 + col * 11
    stories = [
        [
            f"At the {site} depot, {units} parcels arrived after the morning vehicle had left. "
            "The team kept the sealed containers in the covered loading area while the dispatcher arranged "
            f"a second collection. By 14:30, the driver had signed for all but {3 + col} of them. "
            "Those remaining parcels needed new address labels before they could travel.",
            f"The supervisor called the {other} office after checking the labels against the delivery notes. "
            f"Two addresses had changed during the previous {2 + setting % 3} weeks, but the sender had used "
            "the older details. Staff corrected the routing information and attached a copy of the confirmation "
            "to each container. No goods were damaged during the delay.",
            f"Next week, the {site} team will check incoming labels before the first collection. "
            f"The office expects this check to take about {8 + col * 3} minutes each morning. "
            "The dispatcher will review the arrangement after the final departure on Friday and report any "
            "unresolved addresses to the supervisor.",
        ],
        [
            f"Heavy rain closed the loading entrance at {site} on Tuesday. Staff moved {units} containers "
            f"through the rear gate while a contractor cleared the drain. The repair took {2 + setting % 3} hours, "
            "and the first afternoon vehicle waited outside until the water had receded. Its driver then "
            "used the temporary route to complete the collection without unloading on the road.",
            f"The contractor found leaves beneath the metal cover near bay {3 + col}. The maintenance team "
            "removed the blockage and checked the remaining covers before reopening the entrance. "
            f"A similar inspection is planned at {other} next week because both sites share the same drainage design. "
            "Staff will photograph any damage and send the images with their maintenance request.",
            f"The {site} manager has moved the weekly inspection to Monday morning. The new checklist "
            "includes the rear gate so that it remains available if the main entrance closes again. "
            f"The office has allowed {15 + col * 5} minutes for this work before the first scheduled arrival. "
            "The team will review that allowance after a month.",
        ],
        [
            f"During the stock check at {site}, the team counted {units} reusable containers in the covered store. "
            f"The register listed {units + 4}, so the supervisor traced the most recent transfers. "
            f"Four containers had gone to {other} on Thursday and had not yet been signed back in. "
            "The receiving team confirmed their location before the afternoon count was closed.",
            "The discrepancy came from a delivery note that had been filed with the outgoing paperwork. "
            "Staff attached its copy to the register and added the transfer date. The receiving office "
            "will now confirm each transfer by email before the end of the shift. This change leaves "
            "a record even when the original note travels with the driver.",
            f"The next count at {site} is scheduled for 16 October. Staff will compare the register with "
            "the transfer confirmations before entering the store. Any difference will be recorded with "
            "the container number and the last known location, so the following shift can continue "
            "the search without repeating the full count.",
        ],
    ]
    return stories[col % len(stories)]


def _prose(setting: int) -> dict[str, Any]:
    columns = 2 + setting % 2
    size = DESIGN["font_sizes"][setting % 3]
    width = (510 - (columns - 1) * 22) / columns
    ops = _furniture(setting)
    authored_columns = []
    for col in range(columns):
        paragraphs = _paragraphs(setting, col)
        if size == 14:
            paragraphs = paragraphs[: 1 if columns == 3 else 2]
        elif size == 10:
            paragraphs = paragraphs[:2]
        authored_columns.append(paragraphs)
        y = 662.0
        for paragraph in paragraphs:
            for line in _wrap(paragraph, width, size):
                ops.append(text_op(line, 48 + col * (width + 22), y, size=size))
                y -= size + 3
            y -= size * 0.7
        if y < 80:
            raise ValueError("Authored prose exceeds its page; shorten content before freezing")
    return {
        "pdf": page_pdf("\n".join(ops)),
        "target": {
            "kind": "prose",
            "truth_status": "authored-continuous-prose",
            "binary_admission_eligible": True,
            "semantic_basis": "complete sentences continue within each column across physical lines",
            "tables": [],
            "authored_slots": [],
            "authored_columns": authored_columns,
            "setting": setting,
            "columns": columns,
            "font_size": size,
        },
    }


def _ambiguous(setting: int) -> dict[str, Any]:
    ops = _furniture(setting)
    columns = 2 + setting % 2
    for col in range(columns):
        for row in range(4):
            # These could be compact records, independent lists, or unfinished
            # notes. Construction intent cannot settle the visible relationship.
            ops.append(
                text_op(
                    f"{SITES[(row + col) % len(SITES)]} {24 + row * 7 + col}",
                    48 + col * (510 / columns),
                    662 - row * 32,
                    size=10,
                )
            )
    return {
        "pdf": page_pdf("\n".join(ops)),
        "target": {
            "kind": "ambiguous",
            "truth_status": "ambiguous-unscored",
            "binary_admission_eligible": False,
            "semantic_basis": "aligned label/value fragments permit multiple plausible relationships",
            "tables": [],
            "authored_slots": [],
            "setting": setting,
        },
    }


def generate_cases() -> list[dict[str, Any]]:
    """Declare all PDF content and private references without consulting extraction."""
    rng = random.Random(DESIGN["seed"])  # noqa: S311 - deterministic fixture authoring
    cases = [_table(setting, rng) for setting in range(DESIGN["table_pages"])]
    cases.extend(_prose(setting) for setting in range(DESIGN["prose_pages"]))
    cases.extend(_ambiguous(setting) for setting in range(DESIGN["ambiguous_pages"]))
    rng.shuffle(cases)
    for index, case in enumerate(cases):
        case["id"] = f"dev-{index:03}"
        case["target"]["id"] = case["id"]
    return cases


def freeze(directory: Path) -> Path:
    """Freeze inputs and references, then source evidence; never run a semantic scorer."""
    import pylopdf

    directory = guard_path(directory)
    started, cpu = time.perf_counter(), time.process_time()
    cases = generate_cases()
    producer_files = ("silver_realism.py", "feature_cases.py", "silver.py", "silver_structure.py")
    generator_hashes = {name: sha(Path(__file__).with_name(name).read_bytes()) for name in producer_files}
    identity = sha(
        canonical(
            {
                "design": DESIGN,
                "pdfs": [sha(case["pdf"]) for case in cases],
                "targets": [case["target"] for case in cases],
                "generator_hashes": generator_hashes,
            }
        )
    )
    output = directory / identity[:16]
    output.mkdir(parents=True, exist_ok=False)
    (output / "pdfs").mkdir()
    (output / "generator").mkdir()
    for name in producer_files:
        (output / "generator" / name).write_bytes(Path(__file__).with_name(name).read_bytes())
    write_json(output / "design.json", {"design": DESIGN, "generator_sha256": generator_hashes})
    write_json(output / "private-targets.json", [case["target"] for case in cases])
    for case in cases:
        (output / "pdfs" / (case["id"] + ".pdf")).write_bytes(case["pdf"])
    write_json(
        output / "manifest.json",
        {
            "split": "DEV",
            "dataset_sha256": identity,
            "label_status": DESIGN["label_status"],
            "source_kind": "generated",
            "license": "MIT",
            "cases": [
                {"id": case["id"], "split": "DEV", "pdf_path": f"pdfs/{case['id']}.pdf", "pdf_sha256": sha(case["pdf"])}
                for case in cases
            ],
        },
    )
    # Every input, reference, and generator byte above exists before interpretation.
    sources, observations = [], []
    for case in cases:
        with pylopdf.open(stream=case["pdf"]) as document:
            page = document[0]
            words = [
                {"id": f"w{index}", "text": word[4], "bbox": list(word[:4])}
                for index, word in enumerate(page.get_text("words"))
            ]
            image_path = output / (case["id"] + ".png")
            image_path.write_bytes(page.render(dpi=120, background=(255, 255, 255)))
            sources.append(
                {
                    "id": case["id"],
                    "words": words,
                    "page_size": list(page.rect),
                    "image_path": str(image_path),
                    "vector_candidates": [observed_table(table) for table in page.find_tables()],
                    "text_candidates": [observed_table(table) for table in page.find_tables(strategy="text")],
                }
            )
            observations.append(
                {
                    "id": case["id"],
                    "word_count": len(words),
                    "outside_page_word_ids": [
                        word["id"]
                        for word in words
                        if word["bbox"][0] < 0 or word["bbox"][1] < 0 or word["bbox"][2] > 612 or word["bbox"][3] > 792
                    ],
                }
            )
    write_json(output / "source-evidence.json", {"pages": sources})
    rss, tool = process_peak_rss()
    write_json(
        output / "freeze-audit.json",
        {
            "dataset_sha256": identity,
            "source_sha256": sha((output / "source-evidence.json").read_bytes()),
            "counts": dict(Counter(case["target"]["kind"] for case in cases)),
            "scoring_performed": False,
            "source_observations": observations,
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss,
            "measurement": f"perf_counter/process_time; {tool}; sequential CPU; lifetime RSS; no sampling",
        },
    )
    return output


def main() -> None:
    """Write a new immutable DEV cohort without candidate selection or scoring."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({"corpus": str(freeze(args.output)), "scoring_performed": False}, indent=2))


if __name__ == "__main__":
    main()
