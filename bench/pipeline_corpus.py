"""Build P001 DEV inputs and private construction references before extraction."""

# Heterogeneous retained artifact schemas are intentionally explicit dictionaries.
# ruff: noqa: PLC0415, EM101, TRY003, C901
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from bench.silver import canonical, guard_path, sha, write_json
from bench.silver_structure import TABLE_FAMILIES, authored_table

LABEL = "repository-authored DEV silver; not independently adjudicated"


def _table(values: list[list[str | None]], merges: tuple[tuple[int, int, int, int], ...] = ()) -> dict[str, Any]:
    values = deepcopy(values)
    merged = {(r, c): (rs, cs) for r, c, rs, cs in merges}
    covered = set()
    for r, c, rs, cs in merges:
        for row in range(r, r + rs):
            for col in range(c, c + cs):
                if (row, col) != (r, c):
                    covered.add((row, col))
                    values[row][col] = None
    spans = []
    for r, cell_row in enumerate(values):
        for c, _value in enumerate(cell_row):
            if (r, c) not in covered:
                rs, cs = merged.get((r, c), (1, 1))
                spans.append({"row": r, "column": c, "row_span": rs, "column_span": cs})
    return {"row_count": len(values), "col_count": len(values[0]), "values": values, "spans": spans}


def build(directory: Path) -> dict[str, Any]:
    """Freeze opaque page inputs, construction targets and a result-independent pilot.

    Paths in the manifest are absolute. Family, labels and pilot membership are
    scoring metadata and must be stripped before constructing model evidence.
    """
    from bench.borderless_challenge import generate_cases as companion
    from bench.silver_layouts import generate_cases as layouts
    from bench.silver_math import generate_cases as math_cases
    from bench.structure_cases import build_structure_cases

    directory = guard_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    pdfs = directory / "pdfs"
    pdfs.mkdir(exist_ok=True)
    records: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []

    def add(data: bytes, name: str, family: str, page_count: int, tables: list[dict[str, Any]] | None) -> None:
        digest = sha(data)
        path = pdfs / (digest + ".pdf")
        if path.exists() and path.read_bytes() != data:
            raise ValueError("Existing input disagrees with its content hash")
        path.write_bytes(data)
        for page_number in range(page_count):
            opaque = "p" + sha(canonical([name, page_number]))[:20]
            scored = tables is not None
            records.append(
                {
                    "id": opaque,
                    "pdf_path": str(path),
                    "pdf_sha256": digest,
                    "page_number": page_number,
                    "family": family,
                    "label_status": LABEL if scored else "diagnostic-only incomplete references",
                }
            )
            targets.append({"id": opaque, "tables": deepcopy(tables or []), "structural_scored": scored})
            provenance.append({"id": opaque, "source_case": name})

    for case in sorted(layouts() + cast("list[dict[str, Any]]", math_cases()), key=lambda item: item["id"]):
        family = case["family"]
        tables = []
        if family in TABLE_FAMILIES:
            variant = int(case["id"].rsplit("-v", 1)[1]) - 1
            table = authored_table(variant)
            tables = [{key: table[key] for key in ("row_count", "col_count", "values", "spans")}]
        add(case["pdf"], "silver/" + case["id"], "silver/" + family, case.get("page_count", 1), tables)
    for case in companion():
        target = case["target"]
        family = "companion/" + target["kind"]
        if target["kind"] == "borderless":
            family += "-wrap" if target["wrap"] else "-plain"
        add(case["pdf"], "companion/" + case["id"], family, 1, target["tables"])
    for structure_case in build_structure_cases():
        structure_tables = (
            None
            if structure_case.tables is None
            else [_table([list(row) for row in table], structure_case.spans) for table in structure_case.tables]
        )
        add(
            structure_case.feature.data,
            "structure/" + structure_case.feature.name,
            "structure/" + structure_case.feature.name,
            1,
            structure_tables,
        )

    # Fixed construction quotas, chosen before extraction; no performance filtering.
    target_map = {target["id"]: target for target in targets}
    positive_quotas = {
        "silver/merged-table": 2,
        "silver/multilevel-table": 2,
        "companion/borderless-wrap": 4,
        "companion/borderless-plain": 4,
        "companion/ruled-control": 2,
        "structure/table-wrapped-records": 1,
        "structure/table-borderless-rotate-90": 1,
    }
    negative_quotas = {
        "silver/" + family: 1
        for family in (
            "two-column",
            "three-column",
            "headers-footers",
            "rotated-page",
            "cropped-page",
            "form-fields",
            "sidebar",
            "footnotes",
            "reading-order",
            "duplicate-overprint",
            "vector-noise",
            "mixed-panels",
        )
    }
    negative_quotas.update({"companion/prose": 2, "silver/math": 2})
    quotas = {**positive_quotas, **negative_quotas}
    for record in records:
        family = record["family"]
        target = target_map[record["id"]]
        record["pilot"] = bool(target["structural_scored"] and quotas.get(family, 0))
        if record["pilot"]:
            quotas[family] -= 1
    if any(quotas.values()):
        raise ValueError("Predefined pilot construction quotas were not filled")
    identity_records = [{key: value for key, value in row.items() if key != "pdf_path"} for row in records]
    identity = sha(canonical({"schema": 1, "pages": identity_records, "targets": targets}))
    manifest = {
        "schema": 1,
        "split": "DEV",
        "dataset_sha256": identity,
        "path_convention": "absolute",
        "pages": records,
        "pilot_policy": "fixed construction quotas: 16 positive and 16 negative pages; scoring-only membership",
        "model_fields": ["id", "pdf_path", "pdf_sha256", "page_number"],
    }
    write_json(directory / "manifest.json", manifest)
    write_json(directory / "private-targets.json", {"schema": 1, "dataset_sha256": identity, "pages": targets})
    write_json(directory / "private-provenance.json", provenance)
    return manifest


def main() -> None:
    """Build an explicit ignored DEV artifact location."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    manifest = build(args.directory)
    print(
        json.dumps(
            {
                "dataset_sha256": manifest["dataset_sha256"],
                "pages": len(manifest["pages"]),
                "pilot_pages": sum(page["pilot"] for page in manifest["pages"]),
            }
        )
    )


if __name__ == "__main__":
    main()
