"""Independent source replay and full-cohort scoring of pinned official TATR postprocessing."""

# ruff: noqa: ANN401, EM101, TRY003, PLC0415, PLR0913, PLR0912, C901
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.silver import guard_path, sha

FROZEN_SHA = "81da8260d1a0d13ab183b5cd50d22aa9b92345005fef250331f1522cd34ba195"


def read(path: Path) -> Any:
    """Read only explicitly named, guarded files."""
    return json.loads(guard_path(path).read_bytes())


def row_inventory(rows: list[dict[str, Any]], ids: set[str], sizes: list[int], thresholds: list[float]) -> None:
    """Every declared page/treatment appears exactly once, including failures."""
    actual = [(r["id"], r["size"], r["threshold"]) for r in rows]
    expected = {(ident, size, threshold) for ident in ids for size in sizes for threshold in thresholds}
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError("Official postprocessing page/treatment inventory differs")


def analyze(directory: Path, corpus: Path, *, official_trusted_code: dict[str, str],
            trusted_code: dict[str, str], source_trusted_code: dict[str, str],
            yolo_trusted_code: dict[str, str]) -> dict[str, Any]:
    """Authenticate and replay every frozen output before opening DEV targets."""
    from bench import p003_official_tatr as official
    from bench.p003_yolo_structure_analysis import verify

    directory = guard_path(directory)
    if sha((directory / "frozen.json").read_bytes()) != FROZEN_SHA:
        raise ValueError("Announced official source-only freeze changed")
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    if set(official_trusted_code) != set(official.CODE_FILES) or frozen["code_sha256"] != official_trusted_code:
        raise ValueError("Official code differs from independent Git authority")
    for name, digest in official_trusted_code.items():
        if (sha((directory / "code" / name).read_bytes()) != digest
                or sha(Path(official.__file__).with_name(name).read_bytes()) != digest):
            raise ValueError("Archived or executed official helper differs")
    authorities = {"trusted_code": trusted_code, "source_trusted_code": source_trusted_code,
                   "yolo_trusted_code": yolo_trusted_code}
    if frozen["authorities"] != authorities:
        raise ValueError("Original source/geometry authorities differ")
    source_directory = guard_path(Path(frozen["input_directory"]))
    verified, _ = verify(source_directory, **authorities)
    if frozen["input_verification"] != verified:
        raise ValueError("Original source/geometry replay differs from frozen receipt")
    manifest = read(source_directory / "source/manifest.json")
    geometry = read(source_directory / "geometry/report.json")
    if (frozen["upstream_commit"] != official.UPSTREAM_COMMIT
            or frozen["upstream_sha256"] != official.UPSTREAM_SHA
            or frozen["license_sha256"] != official.LICENSE_SHA
            or frozen["records"] != manifest["records"]
            or frozen["sizes"] != manifest["acquisition_sizes"]
            or frozen["thresholds"] != list(official.THRESHOLDS)
            or report["frozen_sha256"] != FROZEN_SHA
            or any(frozen[k] is not False for k in ("references_read", "local_gpu_used"))
            or frozen["new_inference_calls"] != 0 or report["new_inference_calls"] != 0
            or report["references_read"] is not False):
        raise ValueError("Pinned implementation or source-only treatment declaration differs")
    module = official.load_upstream(directory)
    ids = {p["id"] for p in manifest["pages"]}
    row_inventory(report["rows"], ids, frozen["sizes"], frozen["thresholds"])
    indexed = {(r["id"], r["size"], r["threshold"]): r for r in report["rows"]}
    treatments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    errors = defaultdict(int)
    for page, measured in zip(manifest["pages"], geometry["pages"], strict=True):
        source = read(source_directory / "source" / page["source_path"])
        pools = {(size, threshold): [] for size in frozen["sizes"] for threshold in frozen["thresholds"]}
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            prediction = read(source_directory / "geometry" / receipt["path"])
            for view in prediction["views"]:
                try:
                    value = official.decode(source, crop, view, module)
                except Exception as error:
                    value = {"status": "postprocess_error", "table": None, "error_type": type(error).__name__}
                pools[(crop["acquisition_size"], view["threshold"])].append({"region_id": crop["region_id"], **value})
        for (size, threshold), proposals in pools.items():
            result = {"id": page["id"], "source": source, "size": size, "threshold": threshold,
                      "proposals": proposals, **official.compose(source, proposals)}
            result["status"] = "error" if any(p["status"] == "postprocess_error" for p in proposals) else "ok"
            row = indexed[(page["id"], size, threshold)]
            expected_path = f"{page['id']}-s{size}-t{threshold}.json"
            if (row["path"] != expected_path or sha((directory / expected_path).read_bytes()) != row["sha256"]
                    or read(directory / expected_path) != result or row["status"] != result["status"]
                    or row["tables"] != len(result["state"]["tables"])
                    or row["unresolved_words"] != len(result["state"]["unresolved_ids"])):
                raise ValueError("Official decoded output, complete source composition or report differs")
            key = f"s{size}-t{threshold}"
            errors[key] += result["status"] == "error"
            treatments[key].append({"id": page["id"], "status": result["status"], "tables": result["state"]["tables"]})
    if report["page_count"] != len(ids) or report["treatment_count"] != len(treatments):
        raise ValueError("Official full-cohort denominator differs")
    manifest_corpus, targets = load_corpus(guard_path(corpus))
    if {p["id"] for p in manifest_corpus["pages"]} != ids:
        raise ValueError("Scoring cohort differs from authenticated complete source cohort")
    return {"frozen_sha256": FROZEN_SHA, "report_sha256": sha((directory / "report.json").read_bytes()),
            "source_verification": verified, "resources": report["resources"], "postprocessing_errors": dict(errors),
            "scope": "Pinned official CPU postprocessing only; same raw model objects and owned words",
            "new_api_calls": 0, "new_inference_calls": 0, "generated_fallback_tables": 0,
            "treatments": {key: strict_scores(targets["pages"], rows) for key, rows in treatments.items()}}
