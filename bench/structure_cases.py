"""Explicit table references and adversarial derivatives for recovery studies."""

from __future__ import annotations

from dataclasses import dataclass

import pdfust
from bench.feature_cases import FeatureCase, build_cases, page_pdf, text_op

# Visual spot checks on bundled source pages; these are not full corpus gold grids.
RECORD_REFERENCES: dict[str, dict[str, dict[int, str]]] = {
    "corpus-nics-background-checks-2015-11": {
        "Alabama": {0: "Alabama", 1: "18,870", 2: "23,022", 3: "22,650", 4: "859", 5: "1,178", 24: "71,137"},
        "Totals": {0: "Totals", 1: "804,006", 2: "671,330", 3: "636,903", 24: "2,236,457"},
    },
    "corpus-senate-expenditures": {
        "DHAW20190001": {
            0: "DHAW20190001",
            1: "05/03/2019",
            2: "CITIBANK - TRAVEL CBA CARD",
            3: "03/04/2019",
            4: "03/06/2019",
            6: "920.68",
        },
        "DHAW20190002": {
            0: "DHAW20190002",
            1: "05/24/2019",
            2: "CITIBANK - TRAVEL CBA CARD",
            3: "03/10/2019",
            4: "05/15/2019",
            6: "907.96",
        },
        "DHAW20190003": {
            0: "DHAW20190003",
            1: "05/03/2019",
            2: "CITIBANK - TRAVEL CBA CARD",
            3: "03/01/2019",
            4: "03/02/2019",
            6: "737.94",
        },
        "DHAW20190070": {0: "DHAW20190070", 1: "09/09/2019", 3: "08/12/2019", 4: "08/14/2019", 6: "411.49"},
    },
}


@dataclass(frozen=True)
class StructureCase:
    """One page input with optional independently specified logical cells."""

    feature: FeatureCase
    tables: tuple[tuple[tuple[str, ...], ...], ...] | None = None
    spans: tuple[tuple[int, int, int, int], ...] = ()


def build_structure_cases() -> list[StructureCase]:
    """Reuse corpus bytes and add rotations, scans, wrapping, and prose controls."""
    simple = (("Left", "Center", "Right"), ("Alpha", "A|B", "42"), ("Beta", "C\\D", ""))
    references = {
        "table-bordered": (simple,),
        "table-borderless": (simple,),
        "table-merged": ((("Merged header", "Merged header", "Right"), ("Alpha", "A|B", "42"), ("Beta", "C\\D", "")),),
        "table-borderless-aligned": ((("Name", "Amount"), ("Alpha", "42"), ("Beta", "7"), ("Gamma", "16")),),
        "two-column-order": (),
        "rotated-columns": (),
        "text-structure-and-literals": (),
        "positioned-math": (),
        "math-actualtext": (),
        "footnotes-and-page-furniture": (),
    }
    cases = [
        StructureCase(case, references.get(case.name), ((0, 0, 1, 2),) if case.name == "table-merged" else ())
        for case in build_cases()
    ]
    base = next(case for case in cases if case.feature.name == "table-borderless")
    for rotation in (90, 180, 270):
        with pdfust.open(stream=base.feature.data) as document:
            document[0].set_rotation(rotation)
            data = document.tobytes()
        cases.append(
            StructureCase(
                FeatureCase(
                    f"table-borderless-rotate-{rotation}",
                    data,
                    ("tables", "rotation"),
                    f"The ragged borderless fixture with page rotation {rotation}.",
                    base.feature.expected_text,
                ),
                base.tables,
            )
        )
    with pdfust.open(stream=base.feature.data) as source, pdfust.open() as scanned:
        page = scanned.new_page(width=612, height=792)
        page.insert_image(page.rect, pixmap=source[0].get_pixmap(dpi=150))
        cases.append(
            StructureCase(
                FeatureCase(
                    "table-borderless-scanned",
                    scanned.tobytes(),
                    ("tables", "scan"),
                    "Raster-only derivative; source text anchoring is unavailable.",
                    base.feature.expected_text,
                ),
                base.tables,
            )
        )
    rows = (
        ("Item", "Description", "Amount"),
        ("Alpha", "First line continuation", "42.00"),
        ("Beta", "Second line continuation", "7.00"),
        ("Gamma", "Short", "16.00"),
    )
    ops = [text_op("Wrapped records", 40, 740, size=20)]
    for row, (name, description, amount) in enumerate(rows):
        y = 680 - row * 50
        ops.extend((text_op(name, 40, y), text_op(amount, 480, y)))
        if " continuation" in description:
            first, _second = description.split(" continuation")
            ops.extend((text_op(first, 200, y), text_op("continuation", 200, y - 16)))
        else:
            ops.append(text_op(description, 200, y))
    cases.append(
        StructureCase(
            FeatureCase(
                "table-wrapped-records",
                page_pdf("\n".join(ops)),
                ("tables", "wrapped cells"),
                "Explicit record starts with an indented continuation in the description column.",
            ),
            (rows,),
        )
    )
    return cases
