"""New seeded DEV office-value tables, isolated from every existing corpus."""

# ruff: noqa: PLR0911, EM101, TRY003, C901, PLR0912, PLR2004, E501, S311
from __future__ import annotations

import argparse
import json
import random
import re
import resource
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pylopdf
from bench.feature_cases import page_pdf, text_op
from bench.pipeline_corpus import _table
from bench.silver import canonical, guard_path, sha, write_json

SEED = "p003-random-office-values-20261011-v1"
FAMILIES = ("ruled", "borderless", "wrapped", "merged_headers", "dense", "column_pairs", "mixed_types", "continuations")
WORDS = (
    "amber",
    "birch",
    "cedar",
    "cloud",
    "cobalt",
    "coral",
    "elm",
    "fern",
    "green",
    "harbor",
    "ivory",
    "maple",
    "oak",
    "olive",
    "paper",
    "pearl",
    "pine",
    "plum",
    "silver",
    "stone",
    "teal",
    "willow",
    "yellow",
    "archive",
    "balance",
    "budget",
    "credit",
    "delivery",
    "folder",
    "invoice",
    "ledger",
    "meeting",
    "office",
    "payment",
    "receipt",
    "review",
    "service",
    "supply",
    "ticket",
    "update",
)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
HEADERS = {"word1": "Item", "word2": "Description", "usd": "Amount", "date": "Date", "mixed": "Entry"}
SOURCE_CODE = ("p003_random_values_corpus.py", "feature_cases.py", "pipeline_corpus.py", "silver.py")


def rng(stream: str, seed: str = SEED) -> random.Random:
    """Split deterministic value/layout/opaque-identity streams without deriving contents from IDs."""
    return random.Random(int(sha((seed + "/" + stream).encode()), 16))


def value(kind: str, stream: random.Random, *, mixed: bool = False) -> tuple[str, str]:
    """Draw independent office values and noise; no row counters, case IDs or arithmetic progression."""
    noise = stream.random()
    if noise < 0.14:
        chosen = stream.choice(("N/A", "NULL", "", "\u2014", "TBD", "draft", "hold", "0"))
        return chosen, "blank" if chosen == "" else "noise:" + chosen
    if mixed and stream.random() < 0.35:
        kind = stream.choice(("word1", "word2", "usd", "date"))
    if kind in {"word1", "word2", "mixed"}:
        count = 1 if kind == "word1" else 2 if kind == "word2" else stream.choice((1, 2))
        return " ".join(stream.choice(WORDS) for _ in range(count)), "english:" + str(count)
    if kind == "usd":
        cents = stream.randint(0, 9_999_999)
        if stream.random() < 0.06:
            cents = 0
        amount = f"${cents / 100:,.2f}"
        if stream.random() < 0.16 and cents:
            return "(" + amount + ")", "usd:negative"
        return amount, "usd:zero" if cents == 0 else "usd:positive"
    if kind == "date":
        day = date(2018, 1, 1) + timedelta(days=stream.randrange(14 * 365))
        style = stream.randrange(3)
        if style == 0:
            return day.isoformat(), "date:ISO"
        if style == 1:
            return f"{day.month:02d}/{day.day:02d}/{day.year}", "date:US"
        return f"{MONTHS[day.month - 1]} {day.day} {day.year}", "date:English"
    raise ValueError("Unknown value column kind")


def flavor(text: str) -> str:
    """Count actual surviving literal flavors after duplicates and covered spans are applied."""
    if text == "":
        return "blank"
    if text in {"N/A", "NULL", "\u2014", "TBD", "draft", "hold", "0"}:
        return "noise:" + text
    if text.startswith("($"):
        return "usd:negative"
    if text.startswith("$"):
        return "usd:zero" if text == "$0.00" else "usd:positive"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return "date:ISO"
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", text):
        return "date:US"
    if re.fullmatch(r"[A-Z][a-z]{2} \d{1,2} \d{4}", text):
        return "date:English"
    return "english:" + str(len(text.split()))


def table_plan(family: str, layout: random.Random, values: random.Random) -> dict[str, Any]:
    """Freeze a complete literal matrix and source-only layout without consulting extraction/model outputs."""
    rows = layout.randint(8, 24)
    cols = layout.randint(3, 4) if family == "column_pairs" else layout.randint(3, 6)
    if family == "dense":
        rows = layout.randint(20, 24)
        cols = layout.randint(5, 6)
    kinds = ["word2", "usd", "date"] + [
        layout.choice(("word1", "word2", "usd", "date", "mixed")) for _ in range(cols - 3)
    ]
    layout.shuffle(kinds)
    matrix: list[list[str | None]] = [[HEADERS[k] for k in kinds]]
    flavors: Counter[str] = Counter()
    for _ in range(rows - 1):
        row: list[str | None] = []
        for kind in kinds:
            text, flavor = value(kind, values, mixed=family == "mixed_types" or kind == "mixed")
            row.append(text)
            flavors[flavor] += 1
        matrix.append(row)
    merges: tuple[tuple[int, int, int, int], ...] = ()
    if family == "merged_headers":
        column = layout.randrange(cols - 1)
        matrix[0][column] = " ".join(values.choice(WORDS) for _ in range(2))
        merges = ((0, column, 1, 2),)
    if family == "continuations":
        continuation_row, column = layout.randint(1, rows - 2), kinds.index("word2")
        matrix[continuation_row][column] = " ".join(values.choice(WORDS) for _ in range(2))
        merges = ((continuation_row, column, 2, 1),)
    target = _table(matrix, merges)
    # Copy a nonempty literal between distinct surviving anchors in the same column.
    eligible = [(c, [r for r in range(1, rows) if target["values"][r][c] not in (None, "")]) for c in range(cols)]
    column, anchors = values.choice([(c, rs) for c, rs in eligible if len(rs) >= 2])
    first, second = values.sample(anchors, 2)
    target["values"][second][column] = target["values"][first][column]
    size = 7.0 if family == "dense" else 7.5 if family == "column_pairs" else 8.0
    lead = 20.0 if family == "dense" else 25.0
    weights = [
        0.60 if kind == "word2" and family in {"wrapped", "continuations"} else 1.3 if kind in {"usd", "date"} else 1.0
        for kind in kinds
    ]
    return {
        "target": target,
        "kinds": kinds,
        "merges": merges,
        "font_size": size,
        "row_height": lead,
        "weights": weights,
        "flavors": dict(flavors),
        "deliberate_duplicate": {"column": column, "first_row": first, "second_row": second},
        "ruled": family != "borderless",
    }


def plans(seed: str = SEED) -> list[dict[str, Any]]:
    """Declare 32 table pages and eight negatives using independent random streams."""
    layouts, values, identities = rng("layouts", seed), rng("values", seed), rng("opaque-ids", seed)
    result: list[dict[str, Any]] = []
    for family in FAMILIES:
        for _ in range(4):
            identity = "r" + f"{identities.getrandbits(96):024x}"
            tables = [table_plan(family, layouts, values) for _ in range(2 if family == "column_pairs" else 1)]
            title = " ".join(values.choice(WORDS) for _ in range(2)).title()
            result.append({"id": identity, "family": family, "title": title, "tables": tables, "negative_kind": None})
    for index in range(8):
        identity = "r" + f"{identities.getrandbits(96):024x}"
        kind = ("prose", "forms", "decorative", "prose_columns")[index % 4]
        paragraphs = [" ".join(values.choice(WORDS) for _ in range(values.randint(8, 14))) + "." for _ in range(12)]
        fields = [value(values.choice(("word2", "usd", "date")), values)[0] for _ in range(8)]
        result.append(
            {
                "id": identity,
                "family": "negative/" + kind,
                "title": "Internal Notes",
                "tables": [],
                "negative_kind": kind,
                "paragraphs": paragraphs,
                "fields": fields,
            }
        )
    return result


def authored(plan: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]], dict[str, Any]]:
    """Draw literal cells with actual library textbox wrapping and currency right alignment."""
    ops = [text_op(plan["title"], 42, 748, size=15)]
    targets, cell_receipts = [], []
    specifications = []
    for index, table in enumerate(plan["tables"]):
        left, right = (40.0 + index * 278, 290.0 + index * 278) if len(plan["tables"]) == 2 else (42.0, 570.0)
        top = 92.0
        widths = [(right - left) * w / sum(table["weights"]) for w in table["weights"]]
        xs = [left]
        for width in widths:
            xs.append(xs[-1] + width)
        rows = table["target"]["row_count"]
        ys = [top + r * table["row_height"] for r in range(rows + 1)]
        if ys[-1] > 710:
            raise ValueError("Declared table exceeds fixed page body bounds")
        if table["ruled"]:
            ops.append("0 G 0.45 w")
            for row, y in enumerate(ys):
                missing = [(c, cs) for r, c, rs, cs in table["merges"] if r < row < r + rs]
                cursor = left
                for column, span in sorted(missing):
                    if xs[column] > cursor:
                        ops.append(f"{cursor} {792 - y} m {xs[column]} {792 - y} l S")
                    cursor = xs[column + span]
                if cursor < right:
                    ops.append(f"{cursor} {792 - y} m {right} {792 - y} l S")
            for column, x in enumerate(xs):
                missing = [(r, rs) for r, c, rs, cs in table["merges"] if c < column < c + cs]
                cursor = top
                for row, span in sorted(missing):
                    if ys[row] > cursor:
                        ops.append(f"{x} {792 - cursor} m {x} {792 - ys[row]} l S")
                    cursor = ys[row + span]
                if cursor < ys[-1]:
                    ops.append(f"{x} {792 - cursor} m {x} {792 - ys[-1]} l S")
        target = {**table["target"], "bbox": [left, top, right, ys[-1]]}
        targets.append(target)
        specifications.append((table, target, xs, ys))
    kind = plan["negative_kind"]
    if kind in {"forms", "decorative"}:
        ops += ["0.7 G 0.6 w 38 690 m 573 690 l S", "0 G"]
    if kind == "decorative":
        ops += ["0.7 G 0.8 w 40 140 530 530 re S", "70 155 m 150 665 l S", "450 170 m 525 680 l S", "0 G"]
    ops.append(text_op("Figures pending review.", 42, 30, size=9))
    with pylopdf.Document(stream=page_pdf("\n".join(ops))) as document:
        page = document[0]
        for table_index, (table, target, xs, ys) in enumerate(specifications):
            for span in target["spans"]:
                row, column, rs, cs = (span[k] for k in ("row", "column", "row_span", "column_span"))
                literal = target["values"][row][column]
                if literal is None:
                    raise ValueError("Anchor cannot contain covered-slot null")
                rect = [xs[column] + 3, ys[row] + 2.5, xs[column + cs] - 3, ys[row + rs] - 2.5]
                align = pylopdf.TEXT_ALIGN_RIGHT if row and table["kinds"][column] == "usd" else pylopdf.TEXT_ALIGN_LEFT
                remaining = page.insert_textbox(
                    rect, literal, fontsize=table["font_size"], fontname="helv", align=align, lineheight=1.1
                )
                if remaining < -1e-6:
                    raise ValueError("Complete authored literal does not fit; no truncated or font-shrunk substitute")
                cell_receipts.append(
                    {
                        "table": table_index,
                        **span,
                        "literal": literal,
                        "rect": rect,
                        "font_size": table["font_size"],
                        "align": align,
                        "unused_vertical_space": remaining,
                    }
                )
        if kind is not None:
            if kind == "forms":
                for index, text in enumerate(plan["fields"]):
                    y = 128 + index * 58
                    page.insert_text(
                        (52, y),
                        ("Contact", "Office", "Date", "Budget", "Review", "Status", "Notes", "Owner")[index],
                        fontsize=10,
                    )
                    if text:
                        page.insert_text((230 + (index % 2) * 20, y + 10), text, fontsize=10)
            else:
                columns = 2 if kind == "prose_columns" else 1
                for index, paragraph in enumerate(plan["paragraphs"]):
                    column = index // 6 if columns == 2 else 0
                    local = index % 6 if columns == 2 else index
                    x = 52 + column * 265
                    y = 130 + local * (78 if columns == 2 else 43)
                    right = x + (240 if columns == 2 else 500)
                    if page.insert_textbox([x, y, right, y + 38], paragraph, fontsize=9, lineheight=1.1) < 0:
                        raise ValueError("Negative prose does not fit; no silent loss")
        data = document.tobytes()
        words = [{"id": f"w{i}", "bbox": list(w[:4]), "text": w[4]} for i, w in enumerate(page.get_text("words"))]
        source = {"page_size": list(page.rect), "words": words}
    return data, targets, {"source": source, "construction_cells": cell_receipts}


def build(output: Path, *, seed: str = SEED) -> dict[str, Any]:
    """Freeze 40 new sources and complete source gallery before writing separate authored gold."""
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New versioned corpus directory required")
    began, cpu = time.perf_counter(), time.process_time()
    authored_plans = plans(seed)
    output.mkdir(parents=True)
    for name in ("pdfs", "sources", "images", "code"):
        (output / name).mkdir()
    pages, targets, receipts, inventory = [], [], [], {}
    for plan in authored_plans:
        data, tables, receipt = authored(plan)
        identifier = plan["id"]
        pdf = output / "pdfs" / (identifier + ".pdf")
        pdf.write_bytes(data)
        source_path = output / "sources" / (identifier + ".json")
        write_json(
            source_path,
            {
                "id": identifier,
                "source": receipt["source"],
                "model_confidence": None,
                "confidence_scope": "No probabilistic confidence supplied; source extraction only",
            },
        )
        with pylopdf.Document(stream=data) as document:
            image = document[0].render(scale=512 / 792)
        image_path = output / "images" / (identifier + ".png")
        image_path.write_bytes(image)
        values = [v for table in tables for row in table["values"] for v in row if v not in (None, "")]
        duplicates = sum(n - 1 for n in Counter(values).values() if n > 1)
        flavors: Counter[str] = Counter()
        for table in tables:
            flavors.update(flavor(v) for row in table["values"][1:] for v in row if v is not None)
        pages.append(
            {
                "id": identifier,
                "pdf_path": str(pdf.resolve()),
                "pdf_sha256": sha(data),
                "page_number": 0,
                "family": "authored/random-values/" + plan["family"],
                "cohort": "authored",
                "input_kind": "authored_native_pdf",
                "label_status": "Authored construction; references separate from model fields",
                "diversity": {
                    "table_count": len(tables),
                    "flavors": dict(flavors),
                    "duplicate_literal_excess": duplicates,
                    "word_count": len(receipt["source"]["words"]),
                    "rows": [t["row_count"] for t in tables],
                    "columns": [t["col_count"] for t in tables],
                },
                "pilot": False,
            }
        )
        targets.append({"id": identifier, "tables": tables, "structural_scored": True})
        receipts.append(
            {
                "id": identifier,
                "family": plan["family"],
                "construction_cells": receipt["construction_cells"],
                "reference_basis": "Direct authored values/spans and actual textbox operators; no inference or existing references",
                "license": "Repository-authored; repository MIT license",
            }
        )
        for path in (pdf, source_path, image_path):
            inventory[str(path.relative_to(output))] = sha(path.read_bytes())
    identity = sha(
        canonical(
            {"schema": 1, "pages": [{k: v for k, v in p.items() if k != "pdf_path"} for p in pages], "targets": targets}
        )
    )
    manifest = {
        "schema": 1,
        "split": "DEV",
        "dataset_sha256": identity,
        "path_convention": "absolute",
        "pages": pages,
        "model_fields": ["id", "pdf_path", "pdf_sha256", "page_number"],
        "selection_seed": seed,
        "pilot_policy": "All 40 new supplemental pages; no selection using model outcomes",
        "reference_identity_scope": "Standard schema 1 identity includes separate authored targets; no target literals in runtime manifest",
    }
    write_json(output / "manifest.json", manifest)
    write_json(
        output / "source-inventory.json",
        {
            "source_only": True,
            "artifacts": inventory,
            "case_count": 40,
            "manifest_sha256": sha((output / "manifest.json").read_bytes()),
        },
    )
    # Gold/receipts never appear in runtime sources or the source image gallery.
    write_json(output / "private-targets.json", {"schema": 1, "dataset_sha256": identity, "pages": targets})
    write_json(output / "private-construction.json", {"schema": 1, "dataset_sha256": identity, "pages": receipts})
    code = {}
    for name in SOURCE_CODE:
        raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(raw)
        code[name] = sha(raw)
    gallery = "<!doctype html><meta charset='utf-8'><title>Random office values DEV sources</title><style>body{font-family:system-ui}figure{display:inline-block;width:390px;vertical-align:top}img{width:100%}</style>"
    gallery += "".join(
        f"<figure><figcaption>{p['id']}</figcaption><a href='images/{p['id']}.png'><img src='images/{p['id']}.png' alt='Actual source page {p['id']}'></a></figure>"
        for p in pages
    )
    (output / "gallery.html").write_text(gallery)
    frozen = {
        "schema": 1,
        "seed": seed,
        "dataset_sha256": identity,
        "manifest_sha256": sha((output / "manifest.json").read_bytes()),
        "source_inventory_sha256": sha((output / "source-inventory.json").read_bytes()),
        "gold_sha256": sha((output / "private-targets.json").read_bytes()),
        "construction_sha256": sha((output / "private-construction.json").read_bytes()),
        "code_sha256": code,
        "case_count": 40,
        "table_page_count": 32,
        "negative_page_count": 8,
        "table_count": sum(len(t["tables"]) for t in targets),
        "source_only_model_fields": manifest["model_fields"],
        "existing_corpora_read": False,
        "hosted_calls": 0,
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Single parent generation/extraction/rendering; unsampled lifetime getrusage includes imports; no GPU or inference",
        },
    }
    write_json(output / "frozen.json", frozen)
    return frozen


def main() -> None:
    """Build a new explicit DEV directory; never regenerate an existing corpus."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", default=SEED)
    args = parser.parse_args()
    print(json.dumps(build(args.output, seed=args.seed), sort_keys=True))


if __name__ == "__main__":
    main()
