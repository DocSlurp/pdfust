"""CPU-only comparison of pinned upstream TATR postprocessing on frozen predictions."""

# ruff: noqa: ANN401, EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.p003_structure_geometry import LABELS, THRESHOLDS
from bench.p003_structure_place import intersection
from bench.pipeline_assembly import _clean_table
from bench.pipeline_repair import _sources, validate
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

UPSTREAM_COMMIT = "16d124f616109746b7785f03085100f1f6247575"
UPSTREAM_SHA = "a7b3bdf0b0f9ea4b2ccd04bb0acca4bb05b1809d120edf556526a6d976d027db"
LICENSE_SHA = "c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383"
CODE_FILES = (
    "p003_official_tatr.py", "p003_structure_geometry.py", "p003_structure_place.py",
    "pipeline_assembly.py", "pipeline_repair.py", "silver.py",
)


def load_upstream(directory: Path) -> Any:
    """Execute only the reviewed exact official source, retaining its MIT license."""
    directory = guard_path(directory)
    path = directory / "postprocess.py"
    if sha(path.read_bytes()) != UPSTREAM_SHA or sha((directory / "LICENSE").read_bytes()) != LICENSE_SHA:
        raise ValueError("Pinned upstream implementation or license differs")
    spec = importlib.util.spec_from_file_location("p003_pinned_official_tatr", path)
    if spec is None or spec.loader is None:
        raise ValueError("Pinned module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decode(source: dict[str, Any], crop: dict[str, Any], view: dict[str, Any], module: Any) -> dict[str, Any]:
    """Use identical projected objects and owned words; keep upstream output and exact source IDs."""
    lookup = _sources(source)
    ids = crop["source_ids"]
    if len(ids) != len(set(ids)) or set(ids) - set(lookup):
        raise ValueError("Unknown or duplicate crop source ownership")
    objects = [{"bbox": deepcopy(o["bbox"]), "score": o["score"], "label": LABELS.index(o["label"])}
               for o in view["objects"]]
    candidates = sorted((o for o in objects if o["label"] == 0), key=lambda o: -o["score"])
    if not candidates:
        return {"status": "no_table_object", "table": None, "source_ids": ids}
    table = {"bbox": deepcopy(candidates[0]["bbox"]), "page_num": 0}
    allowed = set(ids)
    tokens = [
        {"bbox": deepcopy(w["bbox"]), "text": w["text"], "source_id": w["id"],
         "span_num": index, "line_num": 0, "block_num": 0}
        for index, w in enumerate(source["words"])
        if w["id"] in allowed and module.iob(w["bbox"], table["bbox"]) >= 0.5
    ]
    # The official default order supplies absent block/line IDs as zero; no inferred row gold.
    structures, cells, score = module.objects_to_cells(
        table, objects, tokens, list(LABELS), dict.fromkeys(LABELS, view["threshold"]),
    )
    rows, cols = len(structures["rows"]), len(structures["columns"])
    if not cells or not rows or not cols:
        return {"status": "no_complete_structure", "table": None, "source_ids": ids,
                "upstream_structures": structures, "upstream_cells": cells}
    if rows * cols > 4096 or not math.isfinite(score):
        raise ValueError("Upstream shape or geometry score exceeds admission")
    result = {"row_count": rows, "col_count": cols, "bbox": table["bbox"],
              "cells": [{"source_ids": [], "role": "unknown"} for _ in range(rows * cols)], "spans": []}
    covered: set[tuple[int, int]] = set()
    assigned: set[str] = set()
    for cell in cells:
        rr, cc = sorted(cell["row_nums"]), sorted(cell["column_nums"])
        if (not rr or not cc or rr != list(range(rr[0], rr[-1] + 1))
                or cc != list(range(cc[0], cc[-1] + 1)) or rr[0] < 0 or cc[0] < 0
                or rr[-1] >= rows or cc[-1] >= cols):
            raise ValueError("Upstream span is nonrectangular or outside grid")
        slots = {(r, c) for r in rr for c in cc}
        if slots & covered:
            raise ValueError("Upstream cells overlap")
        covered |= slots
        words = [t["source_id"] for t in cell["spans"]]
        if len(words) != len(set(words)) or set(words) - allowed or assigned & set(words):
            raise ValueError("Upstream text assignment duplicates or invents source")
        assigned.update(words)
        result["cells"][rr[0] * cols + cc[0]]["source_ids"] = words
        result["spans"].append({"row": rr[0], "column": cc[0], "row_span": len(rr), "column_span": len(cc)})
    if len(covered) != rows * cols:
        raise ValueError("Upstream cells leave unrepresented grid slots")
    result = {**_clean_table(result, lookup), "bbox": table["bbox"]}
    return {"status": "prepared", "table": result, "source_ids": ids,
            "upstream_structures": structures, "upstream_cells": cells,
            "upstream_geometry_score": score, "score_is_probability": False,
            "literal_materialization": "Shared source-ID materializer; upstream joined text retained separately"}


def compose(source: dict[str, Any], proposals: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve source conservation, refusing all overlapping tables and unexpected page errors."""
    _sources(source)
    if any(p["status"] == "postprocess_error" for p in proposals):
        tables, conflicts = [], []
    else:
        candidates = [p["table"] for p in proposals if p["table"] is not None]
        conflicts = [i for i, a in enumerate(candidates) if any(
            i != j and intersection(a["bbox"], b["bbox"]) > 0 for j, b in enumerate(candidates))]
        tables = [t for i, t in enumerate(candidates) if i not in conflicts]
        if sum(t["row_count"] * t["col_count"] for t in tables) > 4096:
            raise ValueError("Whole-page slot admission exceeded")
    assigned = [ident for t in tables for c in t["cells"] for ident in c["source_ids"]]
    if len(assigned) != len(set(assigned)):
        raise ValueError("Cross-table source duplication")
    state = {"id": "c0", "tables": tables,
             "unresolved_ids": [w["id"] for w in source["words"] if w["id"] not in set(assigned)]}
    validate(source, state)
    return {"state": state, "conflicting_table_indices": conflicts, "source_conserved": True}


def run(directory: Path, upstream: Path, output: Path, authorities: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Authenticate all original source and model outputs, then freeze nine global treatments without gold."""
    from bench.p003_yolo_structure_analysis import verify

    directory, upstream, output = map(guard_path, (directory, upstream, output))
    if output.exists():
        raise FileExistsError("New experiment output directory required")
    verified, _ = verify(directory, **authorities)
    module = load_upstream(upstream)
    manifest = json.loads((directory / "source/manifest.json").read_bytes())
    geometry = json.loads((directory / "geometry/report.json").read_bytes())
    output.mkdir(parents=True)
    (output / "code").mkdir()
    for name in CODE_FILES:
        shutil.copyfile(Path(__file__).with_name(name), output / "code" / name)
    for name in ("postprocess.py", "LICENSE", "provenance.json"):
        shutil.copyfile(upstream / name, output / name)
    write_json(output / "frozen.json", {
        "input_directory": str(directory), "authorities": authorities, "input_verification": verified,
        "code_sha256": {n: sha((output / "code" / n).read_bytes()) for n in CODE_FILES},
        "upstream_commit": UPSTREAM_COMMIT, "upstream_sha256": UPSTREAM_SHA, "license_sha256": LICENSE_SHA,
        "thresholds": list(THRESHOLDS), "sizes": manifest["acquisition_sizes"], "records": manifest["records"],
        "references_read": False, "new_inference_calls": 0, "local_gpu_used": False,
        "scope": "Only postprocessing changes; same frozen projected objects and exact owned source words",
    })
    rows = []
    with Resources() as resources:
        for page, measured in zip(manifest["pages"], geometry["pages"], strict=True):
            source = json.loads((directory / "source" / page["source_path"]).read_bytes())
            pools = {(size, threshold): [] for size in manifest["acquisition_sizes"] for threshold in THRESHOLDS}
            for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
                prediction = json.loads((directory / "geometry" / receipt["path"]).read_bytes())
                for view in prediction["views"]:
                    try:
                        value = decode(source, crop, view, module)
                    except Exception as error:
                        value = {"status": "postprocess_error", "table": None, "error_type": type(error).__name__}
                    pools[(crop["acquisition_size"], view["threshold"])].append(
                        {"region_id": crop["region_id"], **value}
                    )
            for (size, threshold), proposals in pools.items():
                result = {"id": page["id"], "source": source, "size": size, "threshold": threshold,
                          "proposals": proposals, **compose(source, proposals)}
                result["status"] = "error" if any(p["status"] == "postprocess_error" for p in proposals) else "ok"
                path = f"{page['id']}-s{size}-t{threshold}.json"
                write_json(output / path, result)
                rows.append({"id": page["id"], "size": size, "threshold": threshold, "path": path,
                             "sha256": sha((output / path).read_bytes()), "status": result["status"],
                             "tables": len(result["state"]["tables"]),
                             "unresolved_words": len(result["state"]["unresolved_ids"])})
    report = {"rows": rows, "resources": resources.summary(), "references_read": False, "new_inference_calls": 0,
              "frozen_sha256": sha((output / "frozen.json").read_bytes()), "page_count": 16,
              "treatment_count": 9, "rate_scope": "CPU postprocessing only; excludes source auth and prior acquisition"}
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run a source-only CPU comparison; no model client or reference option exists."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--source-trusted-code", type=Path, required=True)
    parser.add_argument("--yolo-trusted-code", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.input, args.upstream, args.output, {
        name: json.loads(guard_path(getattr(args, name)).read_bytes())
        for name in ("trusted_code", "source_trusted_code", "yolo_trusted_code")
    })
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
