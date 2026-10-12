"""Fresh DEV sources and reversible source-owned repair menus; no target reads."""

# ruff: noqa: EM101, TRY003, PLR2004, SLF001, E501
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from statistics import median
from typing import Any

import pdfust
from bench import p003_random_values_corpus as random_values
from bench.decision_evidence_designs import fragments
from bench.pipeline_assembly import _clean_table, _native
from bench.pipeline_corpus import _table
from bench.pipeline_repair import _sources, validate
from bench.rolling_rows import assemble
from bench.silver import canonical, guard_path, sha, write_json

SEED = "p003-extension-inventor-source-ownership-20261011-v1"
FAMILIES = ("ruled", "borderless", "wrapped", "unnamed", "merged_headers", "mixed", "column_pairs", "negative")
MAX_CANDIDATES = 24


def plans(seed: str = SEED) -> list[dict[str, Any]]:
    """Predeclare 64 fresh layouts, values and opaque identities in separate streams."""
    layouts = random_values.rng("layouts", seed)
    values = random_values.rng("values", seed)
    identities = random_values.rng("identities", seed)
    result = []
    for family in FAMILIES:
        for index in range(8):
            identity = "e" + f"{identities.getrandbits(96):024x}"
            title = " ".join(values.choice(random_values.WORDS) for _ in range(2)).title()
            if family == "negative":
                result.append({"id": identity, "family": family, "title": title, "tables": [],
                               "negative_kind": ("prose", "forms", "decorative", "prose_columns")[index % 4],
                               "paragraphs": [" ".join(values.choice(random_values.WORDS) for _ in range(9)) + "." for _ in range(12)],
                               "fields": [random_values.value(values.choice(("word2", "usd", "date")), values)[0] for _ in range(8)]})
                continue
            renderer_family = "ruled" if family in {"mixed", "unnamed"} else family
            tables = [random_values.table_plan(renderer_family, layouts, values) for _ in range(2 if family == "column_pairs" else 1)]
            for table in tables:
                # Bound height before drawing, without adapting to extraction or model results.
                rows = min(table["target"]["row_count"], 10 if family == "wrapped" else 12)
                if table["merges"]:
                    rows = table["target"]["row_count"]
                matrix = table["target"]["values"][:rows]
                if family == "unnamed":
                    matrix[0] = [""] * len(matrix[0])
                if family == "wrapped":
                    table["row_height"] = 55.0
                    description = table["kinds"].index("word2")
                    for row in matrix[1:]:
                        row[description] = " ".join(values.choice(random_values.WORDS) for _ in range(4))
                table["target"] = _table(matrix, table["merges"])
            result.append({"id": identity, "family": family, "title": title, "tables": tables, "negative_kind": None,
                           "prose": [" ".join(values.choice(random_values.WORDS) for _ in range(12)) + "." for _ in range(3)]})
    return result


def authored(plan: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]], dict[str, Any]]:
    """Render freshly authored values; construction targets remain separate from source evidence."""
    data, targets, receipt = random_values.authored(plan)
    if plan["family"] == "mixed":
        bottom = max(t["bbox"][3] for t in targets)
        with pdfust.Document(stream=data) as document:
            page = document[0]
            for index, paragraph in enumerate(plan["prose"]):
                top = bottom + 18 + index * 38
                if page.insert_textbox([42, top, 570, top + 34], paragraph, fontsize=9, lineheight=1.1) < 0:
                    raise ValueError("Complete mixed-page prose must fit")
            data = document.tobytes()
    return data, targets, receipt


def _vector(table: pdfust.Table) -> dict[str, Any]:
    """Project actual source-detected boxes/anchors; discard detected text/confidence."""
    spans = []
    for anchor in sorted(set(table._cell_anchors)):
        slots = [i for i, value in enumerate(table._cell_anchors) if value == anchor]
        row, column = divmod(anchor, table.col_count)
        spans.append({"row": row, "column": column,
                      "row_span": max(i // table.col_count for i in slots) - row + 1,
                      "column_span": max(i % table.col_count for i in slots) - column + 1})
    return {"bbox": list(table.bbox), "row_count": table.row_count, "col_count": table.col_count,
            "cells": [None if box is None else list(box) for box in table.cells], "spans": spans}


def extract_source(data: bytes, identity: str) -> tuple[dict[str, Any], list[list[float]], list[dict[str, Any]]]:
    """Read only the rendered PDF and source library geometry, never authored receipts."""
    with pdfust.Document(stream=data) as document:
        page = document[0]
        words = [{"id": "w" + sha(f"{identity}/word/{i}".encode())[:16], "bbox": list(w[:4]), "text": w[4]}
                 for i, w in enumerate(page.get_text("words"))]
        rules = []
        for drawing in page.get_drawings():
            if drawing["type"] in {"s", "fs"}:
                rules.extend([*item[1], *item[2]] for item in drawing["items"] if item[0] == "l")
        native = [_vector(table) for table in page.find_tables()]
        text = [_vector(table) for table in page.find_tables(strategy="text")]
        source = {"page_size": list(page.rect), "words": words, "vector_candidates": native}
        states = []
        for vectors in (native, text):
            projected = {**source, "vector_candidates": vectors}
            tables = _native(projected, words)
            tables = [{**_clean_table(table, _sources(source)), "bbox": vector["bbox"]}
                      for table, vector in zip(tables, vectors, strict=True)]
            used = {i for table in tables for cell in table["cells"] for i in cell["source_ids"]}
            state = {"id": "c0", "tables": tables, "unresolved_ids": [w["id"] for w in words if w["id"] not in used]}
            validate(source, state)
            states.append(state)
    return source, rules, states


def _clean(source: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(state)
    result["tables"] = [{**_clean_table(table, _sources(source)), "bbox": table["bbox"]} for table in result["tables"]]
    validate(source, result)
    return result


def loose_row_states(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate admission alternatives from source-only physical and rolling rows.

    A loose two-track midpoint proposal deliberately admits aligned prose. It
    is an unaccepted geometry hypothesis, allowing false-positive rejection to
    be measured on any source with an empty detector, without family labels.
    """
    lookup = _sources(source)
    states = []
    for variant in ("physical", "rolling"):
        assembly = assemble(source, variant)
        tables = []
        for candidate in assembly["candidates"]:
            ids = [ident for cell in candidate["cells"] for ident in cell["source_ids"]]
            boxes = [lookup[ident]["bbox"] for ident in ids]
            bounds = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
            tables.append({**_clean_table(candidate, lookup), "bbox": bounds})
        state = {"id": "c0", "tables": tables, "unresolved_ids": assembly["unresolved_ids"]}
        validate(source, state)
        states.append(state)
    parts = fragments(source["words"])
    bands: dict[int, list[str]] = {}
    for part in parts:
        bands.setdefault(part["band"], []).extend(part["source_ids"])
    if len(bands) >= 3:
        split = median((word["bbox"][0] + word["bbox"][2]) / 2 for word in source["words"])
        rows = []
        for ids in bands.values():
            row: list[list[str]] = [[], []]
            for ident in ids:
                box = lookup[ident]["bbox"]
                row[int((box[0] + box[2]) / 2 >= split)].append(ident)
            rows.append(row)
        table = {"row_count": len(rows), "col_count": 2,
                 "cells": [{"source_ids": ids, "role": "unknown"} for row in rows for ids in row],
                 "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1}
                           for r in range(len(rows)) for c in range(2)]}
        boxes = [word["bbox"] for word in source["words"]]
        bounds = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
        state = {"id": "c0", "tables": [{**_clean_table(table, lookup), "bbox": bounds}], "unresolved_ids": []}
        validate(source, state)
        states.append(state)
    return states


def candidate_menu(source: dict[str, Any], states: list[dict[str, Any]], identity: str) -> dict[str, Any]:
    """Enumerate bounded source-local ownership alternatives independently of any target."""
    baseline = states[0]
    validate(source, baseline)
    inventory = [deepcopy(state) for state in states]
    inventory.append({"id": "c0", "tables": [], "unresolved_ids": [w["id"] for w in source["words"]]})
    if not baseline["tables"]:
        inventory.extend(loose_row_states(source))
    fixed_count = len(inventory)
    # One table at a time: adjacent row swaps, release-to-prose and observed orphan restoration.
    for ti, table in enumerate(baseline["tables"]):
        columns = table["col_count"]
        anchors = [s["row"] * columns + s["column"] for s in table["spans"]]
        populated = [i for i in anchors if table["cells"][i]["source_ids"]]
        for index in populated[:6]:
            adjacent = index + columns
            if adjacent in anchors and adjacent < len(table["cells"]):
                state = deepcopy(baseline)
                cells = state["tables"][ti]["cells"]
                cells[index]["source_ids"], cells[adjacent]["source_ids"] = cells[adjacent]["source_ids"], cells[index]["source_ids"]
                inventory.append(_clean(source, state))
            state = deepcopy(baseline)
            ids = state["tables"][ti]["cells"][index]["source_ids"]
            state["unresolved_ids"].extend(ids)
            state["tables"][ti]["cells"][index]["source_ids"] = []
            inventory.append(_clean(source, state))
        lookup = _sources(source)
        for ident in baseline["unresolved_ids"]:
            box = lookup[ident]["bbox"]
            bounds = table["bbox"]
            x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            if not (bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
                continue
            ranked = sorted(populated, key=lambda index: min(
                abs(y - (lookup[i]["bbox"][1] + lookup[i]["bbox"][3]) / 2) +
                abs(x - (lookup[i]["bbox"][0] + lookup[i]["bbox"][2]) / 2)
                for i in table["cells"][index]["source_ids"]))
            for index in ranked[:2]:
                state = deepcopy(baseline)
                state["unresolved_ids"].remove(ident)
                state["tables"][ti]["cells"][index]["source_ids"].append(ident)
                inventory.append(_clean(source, state))
    unique = {sha(canonical(state)): state for state in inventory}
    # Preserve full initial source-native/text states before bounding local alternatives.
    initial = list(dict.fromkeys(sha(canonical(state)) for state in inventory[:fixed_count]))
    remaining = sorted(set(unique) - set(initial), key=lambda digest: sha(f"{identity}/{digest}".encode()))
    selected = initial + remaining[:MAX_CANDIDATES - len(initial)]
    candidates = [{"id": "c" + sha(f"{identity}/candidate/{digest}".encode())[:16], "state": unique[digest]} for digest in selected]
    candidates.sort(key=lambda candidate: candidate["id"])
    return {"version": 1, "id": identity, "source_sha256": sha(canonical(source)), "baseline": deepcopy(baseline),
            "candidates": candidates, "omitted_context_counts": {"words": 0, "rules": 0},
            "candidate_admission": {"generated_count": len(unique), "retained_count": len(candidates),
                                    "omitted_count": len(unique) - len(candidates)}, "references_used": False}


def stress_baselines(source: dict[str, Any], baseline: dict[str, Any], identity: str) -> list[dict[str, Any]]:
    """Label controlled perturbations separately; select only from observed source owners."""
    options = []
    for ti, table in enumerate(baseline["tables"]):
        for index, cell in enumerate(table["cells"]):
            if cell["source_ids"]:
                options.append((ti, index))
    if not options:
        return []
    options.sort(key=lambda item: sha(f"{identity}/stress/{item}".encode()))
    ti, index = options[0]
    treatments = []
    missing = deepcopy(baseline)
    orphan = missing["tables"][ti]["cells"][index]["source_ids"].pop()
    missing["unresolved_ids"].append(orphan)
    missing = _clean(source, missing)
    treatments.append({"treatment": "missing_table_value", "raw_baseline": missing, "valid_source_ownership": True})
    doubled = deepcopy(baseline)
    doubled["tables"][ti]["cells"][index]["source_ids"].append(orphan)
    doubled["tables"][ti]["values"][index // baseline["tables"][ti]["col_count"]][index % baseline["tables"][ti]["col_count"]] += " " + _sources(source)[orphan]["text"]
    treatments.append({"treatment": "doubled_source_ownership", "raw_baseline": doubled, "valid_source_ownership": False})
    others = [(t, i) for t, i in options if t == ti and i != index]
    if others:
        _, other = min(others, key=lambda item: abs(item[1] - index))
        swapped = deepcopy(baseline)
        cells = swapped["tables"][ti]["cells"]
        cells[index]["source_ids"], cells[other]["source_ids"] = cells[other]["source_ids"], cells[index]["source_ids"]
        treatments.append({"treatment": "swapped_cell_values", "raw_baseline": _clean(source, swapped), "valid_source_ownership": True})
    # Partial source-order continuation shifted to a neighboring row, only if physically multiline.
    lookup = _sources(source)
    for t, i in options:
        table = baseline["tables"][t]
        ids = table["cells"][i]["source_ids"]
        ys = [lookup[ident]["bbox"][1] for ident in ids]
        neighbor = i + table["col_count"]
        if len(ids) > 1 and max(ys) - min(ys) > 4 and neighbor < len(table["cells"]):
            anchors = {s["row"] * table["col_count"] + s["column"] for s in table["spans"]}
            if neighbor not in anchors:
                continue
            wrapped = deepcopy(baseline)
            continuation = [ident for ident in ids if lookup[ident]["bbox"][1] > min(ys) + 4]
            cells = wrapped["tables"][t]["cells"]
            cells[i]["source_ids"] = [ident for ident in ids if ident not in continuation]
            cells[neighbor]["source_ids"].extend(continuation)
            treatments.append({"treatment": "wrapped_continuation_shift", "raw_baseline": _clean(source, wrapped), "valid_source_ownership": True})
            break
    return treatments


def build(output: Path, *, seed: str = SEED) -> dict[str, Any]:
    """Freeze sources, menus and source-native baselines before separate authored targets."""
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New versioned corpus directory required")
    start, cpu = time.perf_counter(), time.process_time()
    output.mkdir(parents=True)
    for name in ("pdfs", "sources", "images", "menus", "stress", "code"):
        (output / name).mkdir()
    pages, targets, construction, inventory, menu_counts, stress_counts = [], [], [], {}, [], Counter()
    for plan in plans(seed):
        data, tables, receipt = authored(plan)
        ident = plan["id"]
        pdf_path = output / "pdfs" / (ident + ".pdf")
        pdf_path.write_bytes(data)
        source, rules, states = extract_source(data, ident)
        write_json(output / "sources" / (ident + ".json"), {"id": ident, "source": source, "rules": rules})
        menu = candidate_menu(source, states, ident)
        write_json(output / "menus" / (ident + ".json"), {**menu, "source": source, "rules": rules})
        stress = stress_baselines(source, states[0], ident)
        stress_counts.update(item["treatment"] for item in stress)
        write_json(output / "stress" / (ident + ".json"), {"id": ident, "synthetic_stress_only": True, "treatments": stress})
        menu_counts.append({"id": ident, "native_table_count": len(states[0]["tables"]), "text_table_count": len(states[1]["tables"]),
                            "candidate_count": len(menu["candidates"]), "stress_count": len(stress)})
        with pdfust.Document(stream=data) as document:
            (output / "images" / (ident + ".png")).write_bytes(document[0].render(scale=768 / 792))
        pages.append({"id": ident, "pdf_path": str(pdf_path), "pdf_sha256": sha(data), "page_number": 0,
                      "family": "authored/extension/" + plan["family"], "cohort": "authored", "input_kind": "authored_native_pdf",
                      "label_status": "Direct fresh authored values/spans; generator references excluded from menus", "pilot": False})
        targets.append({"id": ident, "tables": tables, "structural_scored": True})
        construction.append({"id": ident, "family": plan["family"], "construction_cells": receipt["construction_cells"]})
        for name, suffix in (("pdfs", ".pdf"), ("sources", ".json"), ("images", ".png"), ("menus", ".json"), ("stress", ".json")):
            path = output / name / (ident + suffix)
            inventory[str(path.relative_to(output))] = sha(path.read_bytes())
    identity = sha(canonical({"schema": 1, "pages": [{k: v for k, v in page.items() if k != "pdf_path"} for page in pages], "targets": targets}))
    manifest = {"schema": 1, "split": "DEV", "dataset_sha256": identity, "path_convention": "absolute", "pages": pages,
                "model_fields": ["id", "pdf_path", "pdf_sha256", "page_number"], "selection_seed": seed}
    write_json(output / "manifest.json", manifest)
    write_json(output / "source-inventory.json", {"source_only": True, "artifacts": inventory, "case_count": len(pages)})
    write_json(output / "private-targets.json", {"schema": 1, "dataset_sha256": identity, "pages": targets})
    write_json(output / "private-construction.json", {"schema": 1, "dataset_sha256": identity, "pages": construction})
    code = {}
    for name in (Path(__file__).name, "p003_random_values_corpus.py", "pipeline_assembly.py", "pipeline_repair.py"):
        raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(raw)
        code[name] = sha(raw)
    gallery = "<!doctype html><meta charset='utf-8'><title>Fresh DEV source pages</title><style>body{font-family:system-ui}figure{display:inline-block;width:380px;vertical-align:top}img{width:100%}</style>"
    gallery += "".join(f"<figure><figcaption>{p['id']}</figcaption><a href='images/{p['id']}.png'><img src='images/{p['id']}.png' alt='Source page {p['id']}'></a></figure>" for p in pages)
    (output / "gallery.html").write_text(gallery)
    frozen = {"schema": 1, "seed": seed, "dataset_sha256": identity, "case_count": len(pages), "table_page_count": 56,
              "negative_page_count": 8, "menus": menu_counts, "synthetic_stress_counts": dict(stress_counts), "code_sha256": code,
              "existing_corpora_read": False, "references_read_for_menus": False, "hosted_calls": 0,
              "resources": {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu,
                            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            "measurement": "Single parent CPU generation/extraction/render; unsampled getrusage lifetime peak includes imports"}}
    write_json(output / "frozen.json", frozen)
    return frozen


def main() -> None:
    """Build a new isolated DEV directory, refusing replacement of prior artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", default=SEED)
    args = parser.parse_args()
    print(json.dumps(build(args.output, seed=args.seed), indent=2))


if __name__ == "__main__":
    main()
