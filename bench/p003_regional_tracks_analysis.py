"""Independent replay and fixed-treatment DEV scoring of source-owned regional tracks."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.p003_yolo_structure_analysis import read
from bench.p003_yolo_structure_analysis import verify as verify_structure
from bench.silver import guard_path, sha

FROZEN_SHA = "1bfa0c45db8ce5384f968174c5aeaa002af69beb669369d5c10596ce20104dcf"
PAGES = 16
PAGE_TREATMENTS = 576
REPORT_SHA = "6401cf440d231d23ad063318ebeb973a32fbb2a26dceac231c3f6e2ebb68759e"
EXECUTED = {
    "p003_regional_tracks.py", "p003_fullsource_tracks.py", "p003_segment_topology.py",
    "p003_structure_geometry.py", "p003_structure_place.py", "pipeline_repair.py", "silver.py",
}


def verify_rows(rows: list[dict[str, Any]], expected: set[tuple[str, int, str]]) -> None:
    """Require every fixed treatment/page, including ineffective whole-page refusals."""
    keys = [(row["id"], row["size"], row["treatment"]) for row in rows]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("Incomplete or duplicated regional full-cohort treatment inventory")


def verify(directory: Path, regional_trusted_code: dict[str, str], **input_authorities: dict[str, str]) -> tuple[
    dict[str, Any], dict[str, list[dict[str, Any]]]
]:
    """Authenticate archives and rebuild all576 effective page states before references."""
    from bench import p003_regional_tracks as regional

    directory = guard_path(directory)
    if sha((directory / "frozen.json").read_bytes()) != FROZEN_SHA:
        raise ValueError("Announced regional source freeze changed")
    if sha((directory / "report.json").read_bytes()) != REPORT_SHA:
        raise ValueError("Announced regional report changed")
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    if frozen["code_sha256"] != regional_trusted_code or not set(regional_trusted_code) >= EXECUTED:
        raise ValueError("Regional archive differs from independently supplied Git authority")
    for name, digest in regional_trusted_code.items():
        if Path(name).name != name or sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Regional archived source bytes differ")
        if name in EXECUTED and sha(Path(__file__).with_name(name).read_bytes()) != digest:
            raise ValueError("Executed regional pure helper differs from authenticated source")
    if (
        frozen["references_read"] is not False or frozen["new_api_calls"] != 0
        or frozen["local_gpu_used"] is not False or frozen["fresh_confirmation_accessed"] is not False
        or frozen["profiles"] != [list(p) for p in regional.PROFILES]
        or frozen["hybrid_thresholds"] != list(regional.HYBRID_THRESHOLDS)
        or frozen["sizes"] != [640, 1024, 1280]
        or report["frozen_sha256"] != FROZEN_SHA
        or report["intended_page_count"] != PAGES
        or report["page_treatment_count"] != PAGE_TREATMENTS
    ):
        raise ValueError("Regional source-only treatment contract changed")
    for name, key in (
        ("structure", "trusted_code"), ("detector", "yolo_trusted_code"), ("source", "source_trusted_code")
    ):
        authority = frozen["independent_authorities"][name]
        path = guard_path(Path(authority["path"]))
        if sha(path.read_bytes()) != authority["sha256"] or read(path) != input_authorities[key]:
            raise ValueError("Regional historical authority differs from independently supplied map")
    incoming = guard_path(Path(frozen["input_directory"]))
    verified_input, _ = verify_structure(incoming, **input_authorities)
    if (
        verified_input["source_manifest_sha256"] != frozen["source_manifest_sha256"]
        or verified_input["geometry_report_sha256"] != frozen["geometry_report_sha256"]
    ):
        raise ValueError("Regional input source or geometry differs")
    manifest, geometry = read(incoming / "source/manifest.json"), read(incoming / "geometry/report.json")
    if frozen["records"] != manifest["records"]:
        raise ValueError("Regional original source inventory differs")
    ids = [record["id"] for record in frozen["records"]]
    if len(ids) != PAGES or len(set(ids)) != PAGES:
        raise ValueError("Regional complete16 source inventory differs")
    treatments = [(f"gap-{gap}-support-{support}", gap, support, None) for gap, support in regional.PROFILES]
    treatments += [(f"tatr-columns-{threshold}-physical-rows", 0.5, 0.1, threshold)
                   for threshold in regional.HYBRID_THRESHOLDS]
    expected = {(ident, size, name) for ident in ids for size in frozen["sizes"] for name, *_ in treatments}
    verify_rows(report["rows"], expected)
    if frozen["output_sha256"] != {row["path"]: row["sha256"] for row in report["rows"]}:
        raise ValueError("Regional frozen output inventory differs")
    rows = {(row["id"], row["size"], row["treatment"]): row for row in report["rows"]}
    outputs, refusals = defaultdict(list), defaultdict(int)
    for page, measured in zip(manifest["pages"], geometry["pages"], strict=True):
        source = read(incoming / "source" / page["source_path"])
        topologies = {}
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            prediction = read(incoming / "geometry" / receipt["path"])
            topologies[crop["region_id"]] = {view["threshold"]: view["topology"] for view in prediction["views"]}
        for size in frozen["sizes"]:
            proposals = page["ownership_by_size"][str(size)]["proposals"]
            for name, gap, support, threshold in treatments:
                topology = None if threshold is None else {
                    p["region_id"]: topologies[p["region_id"]][threshold] for p in proposals
                }
                replay = regional.compose(source, proposals, gap, support, topology)
                payload = {"id": page["id"], "size": size, "treatment": name, "source": source, **replay}
                row = rows[page["id"], size, name]
                path = guard_path(directory / row["path"])
                if sha(path.read_bytes()) != row["sha256"] or read(path) != payload:
                    raise ValueError("Regional effective page state differs from pure reconstruction")
                if (
                    row["table_count"] != len(replay["state"]["tables"])
                    or row["page_refusal"] != replay["page_refusal"]
                ):
                    raise ValueError("Regional summary differs from effective page state")
                key = f"s{size}-{name}"
                outputs[key].append({"id": page["id"], "status": "ok", "tables": replay["state"]["tables"]})
                refusals[key] += replay["page_refusal"] is not None
    return {"frozen_sha256": FROZEN_SHA, "report_sha256": REPORT_SHA,
            "input_verification": verified_input, "resources": report["resources"],
            "page_refusals": dict(refusals)}, dict(outputs)


def analyze(
    directory: Path, corpus: Path, regional_trusted_code: dict[str, str], **authorities: dict[str, str]
) -> dict[str, Any]:
    """Score all36 fixed full16 cohorts; local refused proposals never receive credit."""
    verified, treatments = verify(directory, regional_trusted_code, **authorities)
    manifest, targets = load_corpus(guard_path(corpus))
    ids = {row["id"] for row in next(iter(treatments.values()))}
    if not ids <= {row["id"] for row in manifest["pages"]}:
        raise ValueError("Regional DEV scoring inventory differs")
    refs = [row for row in targets["pages"] if row["id"] in ids]
    return {**verified, "scope": "All36 source-frozen regional controls; complete16 denominator",
            "new_api_calls": 0, "generated_fallback_tables": 0,
            "treatments": {key: strict_scores(refs, rows) for key, rows in treatments.items()}}
