"""DEV-only whole-page oracle over independently authenticated frozen valid crop pools."""

# Retained heterogeneous experiment JSON is validated at the artifact boundary.
# ruff: noqa: EM101, TRY003, PLR0912, C901
from __future__ import annotations

import itertools
import json
import time
from pathlib import Path
from typing import Any

from bench import p003_candidate_regions as admission
from bench import p003_candidate_run as candidate
from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.silver import guard_path, sha

MAX_COMPOSITIONS = 16384
SCREEN_PAGES = 16


def _read(path: Path) -> dict[str, Any]:
    return json.loads(guard_path(path).read_bytes())


def compositions(page: dict[str, Any]) -> list[tuple[tuple[int, ...], dict[str, Any]]]:
    """Enumerate complete exact states with deterministic origin ordering, without references."""
    options = []
    for crop in page["crops"]:
        unique = {}
        for attempt in crop["attempts"]:
            if attempt["valid"]:
                unique.setdefault(attempt["canonical_json"], attempt["baseline_index"])
        options.append(sorted(unique.values()))
    count = 1
    for origins in options:
        count *= len(origins)
    if count > MAX_COMPOSITIONS:
        raise ValueError("Frozen composition inventory exceeds declared offline bound")
    completed = []
    for origins in itertools.product(*options):
        try:
            result = admission.compose_selection(page, dict(enumerate(origins)))
        except ValueError:
            continue
        completed.append((origins, {"id": page["id"], "status": "ok", "tables": result["state"]["tables"]}))
    return completed


def oracle_page(target: dict[str, Any], choices: list[tuple[tuple[int, ...], dict[str, Any]]]) -> dict[str, Any]:
    """Choose by strict cells, complete tables, fewer extras, text, then lowest origin tuple."""
    scored = [(origins, prediction, strict_scores([target], [prediction])) for origins, prediction in choices]
    if not scored:
        prediction = {"id": target["id"], "status": "missing", "tables": []}
        return {"selected": prediction, "origins": [], "maximum_complete_tables": 0, "compositions": 0}
    # Python max keeps the first tied entry; choices have lexicographic origin ordering.
    origins, prediction, score = max(
        scored,
        key=lambda entry: (
            entry[2]["totals"]["strict_exact_cells"],
            entry[2]["totals"]["complete_tables"],
            -entry[2]["totals"]["false_positive_tables"],
            entry[2]["totals"]["correct_text_cells"],
        ),
    )
    return {
        "selected": prediction,
        "origins": list(origins),
        "score": score["totals"],
        "maximum_complete_tables": max(s["totals"]["complete_tables"] for _, _, s in scored),
        "compositions": len(scored),
    }


def analyze(
    directory: Path,
    corpus: Path,
    *,
    trusted_code: dict[str, str],
    baseline_trusted_code: list[dict[str, str]],
) -> dict[str, Any]:
    """Authenticate and reproduce all source-only pools before loading separate DEV references."""
    started, cpu = time.perf_counter(), time.process_time()
    directory, corpus = guard_path(directory), guard_path(corpus)
    frozen = _read(directory / "frozen.json")
    if frozen["quality_references_used_in_freeze"] is not False or len(frozen["records"]) != SCREEN_PAGES:
        raise ValueError("Oracle requires a complete source-only natural16 freeze")
    for name, digest in frozen["code_sha256"].items():
        if Path(name).name != name or trusted_code.get(name) != digest:
            raise ValueError("Frozen pool code lacks independent source authentication")
        if sha(guard_path(directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Frozen pool archived code changed")
    if frozen["code_sha256"]["p003_candidate_regions.py"] != sha(Path(admission.__file__).read_bytes()):
        raise ValueError("Source-only admission replay helper differs from authenticated freeze")
    provenance = frozen["baseline_provenance"]
    if len(provenance) != len(baseline_trusted_code):
        raise ValueError("Provide an independent trusted map for every generation baseline")
    baselines, directories = [], []
    for index, archived in enumerate(provenance):
        if archived["copied_directory"] != f"baseline-{index}":
            raise ValueError("Unexpected copied baseline identity")
        copied = directory / archived["copied_directory"]
        for name, digest in archived["file_sha256"].items():
            if Path(name).name != name or sha(guard_path(copied / name).read_bytes()) != digest:
                raise ValueError("Frozen baseline artifact changed")
        baseline = candidate.authenticate(
            copied,
            baseline_trusted_code[index],
            reviewed_parser_sha256=tuple(frozen["reviewed_parser_sha256"]),
        )
        if baseline[0]["records"] != frozen["records"] or baseline[0]["manifest_sha256"] != frozen["manifest_sha256"]:
            raise ValueError("Baseline source inventory differs from frozen pools")
        if baseline[1] != archived["historical_generation_report"]:
            raise ValueError("Historical generation report provenance differs")
        baselines.append(baseline)
        directories.append(copied)
    pages = [{p["id"]: p for p in baseline[1]["results"]} for baseline in baselines]
    frozen_pages, inventories = [], []
    if set(frozen["valid_region_pools_sha256"]) != {r["id"] for r in frozen["records"]}:
        raise ValueError("Frozen pools omit source pages")
    for record in frozen["records"]:
        path = directory / f"{record['id']}-valid-region-pools.json"
        if sha(guard_path(path).read_bytes()) != frozen["valid_region_pools_sha256"][record["id"]]:
            raise ValueError("Frozen crop pool artifact changed")
        page = _read(path)
        rebuilt = admission.freeze_page(
            record,
            [p[record["id"]] for p in pages],
            directories,
            [b[0]["config"] for b in baselines],
            seed=frozen["seed"],
        )
        if page != rebuilt:
            raise ValueError("Frozen pool differs from independently reconstructed source evidence")
        frozen_pages.append(page)
        inventories.append(compositions(page))
    # No reference is accessed until source authentication, pool reconstruction and enumeration finish.
    _, targets = load_corpus(corpus)
    if sha((corpus / "manifest.json").read_bytes()) != frozen["manifest_sha256"]:
        raise ValueError("DEV references differ from frozen natural16 inventory")
    references = {t["id"]: t for t in targets["pages"]}
    results = [oracle_page(references[p["id"]], choices) for p, choices in zip(frozen_pages, inventories, strict=True)]
    selected = [r["selected"] for r in results]
    lowest = [
        choices[0][1] if choices else {"id": p["id"], "status": "missing", "tables": []}
        for p, choices in zip(frozen_pages, inventories, strict=True)
    ]
    return {
        "scope": "DEV-only posthoc whole-page valid-region oracle; unattainable selection ceiling, not model evidence",
        "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "code_sha256": frozen["code_sha256"],
        "scores": strict_scores(targets["pages"], selected),
        "lowest_valid_origin_scores": strict_scores(targets["pages"], lowest),
        "original_baseline_scores": [strict_scores(targets["pages"], b[1]["results"]) for b in baselines],
        "independent_complete_table_ceiling": sum(r["maximum_complete_tables"] for r in results),
        "pages": [
            {
                "id": p["id"],
                "historical_page_failure_gate_blocks": p["historical_page_failure_gate_blocks"],
                "complete_crop_coverage": p["complete_crop_coverage"],
                **r,
            }
            for p, r in zip(frozen_pages, results, strict=True)
        ],
        "no_new_api_calls": True,
        "source_conserved": False,
        "pages_per_minute": None,
        "pages_per_api_usd": None,
        "cost_scope": (
            "Original generation reports and failed attempts remain historical; oracle computation adds no API charge"
        ),
        "local_metrics": {"wall_seconds": time.perf_counter() - started, "cpu_seconds": time.process_time() - cpu},
    }
