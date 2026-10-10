"""Independent DEV necessary-character availability over immutable source-only bags."""

# ruff: noqa: EM101, TRY003, C901
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_segment_topology as segments
from bench import p003_source_availability as availability
from bench.generalization_report import load_corpus
from bench.generalization_scoring import normalize_text
from bench.p003_gate_run import authenticate
from bench.silver import canonical, guard_path, sha

SUBSETS = ("full_page", "detector_owned_union", "geometry_control_assigned")


def read(path: Path) -> Any:  # noqa: ANN401
    """Read explicitly supplied guarded evidence."""
    return json.loads(guard_path(path).read_bytes())


def authenticate_archive(directory: Path, trusted: dict[str, str], *, unused: tuple[str, ...]) -> dict[str, Any]:
    """Require independent authority for every archived byte and current executed helper."""
    frozen = read(directory / "frozen.json")
    for name, digest in frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or trusted.get(name) != digest
            or sha((directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Source availability archive lacks independent code authority")
        if name not in unused and sha(Path(__file__).with_name(name).read_bytes()) != digest:
            raise ValueError("Current source availability replay helper differs")
    return frozen


def verify(
    directory: Path, trusted: dict[str, str], source_trusted: dict[str, str], geometry_trusted: dict[str, str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Rebuild all source plans, 1,190 alternatives, controls and complete bags before target loading."""
    directory = guard_path(directory)
    frozen = authenticate_archive(directory, trusted, unused=("p003_source_availability_prepare.py",))
    if (
        frozen["references_read"] is not False
        or frozen["fresh_confirmation_accessed"] is not False
        or frozen["inference_calls"] != 0
        or frozen["subsets"] != list(SUBSETS)
    ):
        raise ValueError("Expected immutable source-only availability inventory")
    baseline = guard_path(Path(frozen["source_baseline"]))
    original_frozen, original_report = authenticate(baseline, source_trusted)
    geometry = guard_path(Path(frozen["geometry_control_directory"]))
    gf = authenticate_archive(geometry, geometry_trusted, unused=("p003_segment_topology_prepare.py",))
    gr, report = read(geometry / "report.json"), read(directory / "report.json")
    if (
        sha((baseline / "frozen.json").read_bytes()) != frozen["source_frozen_sha256"]
        or original_frozen["records"] != frozen["records"]
        or gf["records"] != frozen["records"]
        or sha((geometry / "frozen.json").read_bytes()) != frozen["geometry_frozen_sha256"]
        or sha((geometry / "report.json").read_bytes()) != frozen["geometry_report_sha256"]
        or report["frozen_sha256"] != sha((directory / "frozen.json").read_bytes())
        or gr["frozen_sha256"] != frozen["geometry_frozen_sha256"]
        or read(directory / "trust/source.json") != source_trusted
        or read(directory / "trust/geometry.json") != geometry_trusted
    ):
        raise ValueError("Availability source/control provenance changed")
    ids = [r["id"] for r in frozen["records"]]
    if [p["id"] for p in report["pages"]] != ids or [p["id"] for p in gr["pages"]] != ids:
        raise ValueError("Availability intended pages dropped or reordered")
    originals = {p["id"]: p for p in original_report["results"]}
    pages = []
    for record, row, geom in zip(frozen["records"], report["pages"], gr["pages"], strict=True):
        original = originals[record["id"]]
        source = original["source"]
        if (
            sha(guard_path(Path(record["pdf_path"])).read_bytes()) != record["pdf_sha256"]
            or read(geometry / geom["source_path"]) != source
            or sha((geometry / geom["source_path"]).read_bytes()) != geom["source_sha256"]
            or sha(canonical(source)) != geom["source_identity_sha256"]
            or sha((baseline / f"{record['id']}-result.json").read_bytes()) != geom["baseline_result_sha256"]
        ):
            raise ValueError("Availability original source identity changed")
        detector = [r for r in original["region_plan"]["regions"] if r["kind"] == "detector_proposal"]
        if [c["region_id"] for c in geom["crops"]] != [r["id"] for r in detector]:
            raise ValueError("Availability acquisition inventory changed")
        states = []
        for crop, region in zip(geom["crops"], detector, strict=True):
            folder = geometry / crop["folder"]
            plan = segments.freeze(source, region["source_ids"], region["bbox"])
            candidates = segments.candidates(source, plan)
            if (
                crop["source_ids"] != region["source_ids"] or crop["bbox"] != region["bbox"]
                or sha((folder / "plan.json").read_bytes()) != crop["plan_sha256"]
                or sha((folder / "candidates.json").read_bytes()) != crop["candidates_sha256"]
                or read(folder / "plan.json") != plan or read(folder / "candidates.json") != candidates
            ):
                raise ValueError("Availability source-only topology inventory changed")
            states.append(candidates[0]["state"])
        control = segments.compose(source, states)
        if (
            read(geometry / geom["geometry_control_path"]) != control
            or sha((geometry / geom["geometry_control_path"]).read_bytes()) != geom["geometry_control_sha256"]
        ):
            raise ValueError("Availability assigned control differs")
        expected = {
            "id": record["id"], "record": record, "source": source, "detector_regions": detector,
            "geometry_control": control,
            "audit": availability.audit(source, original["region_plan"]["regions"], control),
        }
        page = read(directory / row["path"])
        if sha((directory / row["path"]).read_bytes()) != row["sha256"] or page != expected:
            raise ValueError("Availability literal bags/geometry receipts differ from reconstruction")
        pages.append(page)
    return frozen, pages


def characters(text: str) -> Counter[str]:
    """Exclude freely assembled whitespace; retain NFC case, punctuation and multiplicity."""
    return Counter(c for c in normalize_text(text) if not c.isspace())


def necessary_counts(target: dict[str, Any], bag: dict[str, Any]) -> dict[str, int]:
    """Independent per-cell necessary condition permits reuse and arbitrary character rearrangement."""
    available = Counter(dict(bag["nonspace_character_bag"]))
    required: Counter[str] = Counter()
    cells = supported = blanks = possible_tables = 0
    for table in target["tables"]:
        table_possible = True
        for row in table["values"]:
            for value in row:
                if value is None:
                    continue
                chars = characters(value)
                cells += 1
                blanks += not chars
                possible = not (chars - available)
                supported += possible
                table_possible &= possible
                required.update(chars)
        possible_tables += table_possible
    return {
        "reference_cells": cells, "blank_reference_cells": blanks,
        "independently_character_possible_cells": supported,
        "character_impossible_cells": cells - supported,
        "all_cells_independently_possible_tables": possible_tables,
        "reference_nonspace_characters": required.total(),
        "aggregate_available_reference_characters": (required & available).total(),
        "aggregate_missing_reference_characters": (required - available).total(),
        "source_words": bag["word_count"],
    }


def analyze(
    directory: Path, corpus: Path, *, trusted_code: dict[str, str], source_trusted_code: dict[str, str],
    geometry_trusted_code: dict[str, str]
) -> dict[str, Any]:
    """Report optimistic text necessities separately from achieved cell/geometry quality."""
    frozen, pages = verify(directory, trusted_code, source_trusted_code, geometry_trusted_code)
    manifest, targets = load_corpus(guard_path(corpus))
    refs = {p["id"]: p for p in targets["pages"]}
    if set(refs) != {p["id"] for p in pages}:
        raise ValueError("Availability scoring must preserve the exact intended DEV inventory")
    rows = [
        {"id": p["id"], "subsets": {s: necessary_counts(refs[p["id"]], p["audit"]["subsets"][s]["bag"])
                                     for s in SUBSETS}}
        for p in pages
    ]
    dense_ids = {"p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"}
    totals = {}
    for label, selected in (("all16", rows), ("dense2", [r for r in rows if r["id"] in dense_ids]),
                            ("other14", [r for r in rows if r["id"] not in dense_ids])):
        totals[label] = {s: dict(sum((Counter(r["subsets"][s]) for r in selected), Counter())) for s in SUBSETS}
    return {
        "scope": "DEV optimistic necessary-character availability; not attainable cells/tables or model quality",
        "frozen_sha256": sha((guard_path(directory) / "frozen.json").read_bytes()),
        "code_sha256": frozen["code_sha256"], "dataset_sha256": manifest["dataset_sha256"],
        "intended_pages": len(rows), "totals": totals, "pages": rows,
        "independent_cell_text_reuse_allowed": True, "character_rearrangement_allowed": True,
        "geometry_order_complete_word_atomicity_ignored": True, "new_api_calls": 0,
    }
