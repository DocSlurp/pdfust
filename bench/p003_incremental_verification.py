"""Independent offline replay of explicitly authenticated incremental P003 artifacts."""

# Frozen heterogeneous experiment protocols and authenticated local replay helpers.
# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR0912, PLR2004
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.silver import guard_path, sha


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Incremental evidence must be a JSON object")
    return value


def _helpers(frozen: dict[str, Any], names: tuple[str, ...]) -> None:
    historical_config_keys = {
        "baseline_source_order",
        "campaign",
        "max_questions",
        "model",
        "prepare_only",
        "processor",
        "reviewed_parser_sha256",
        "run_hosted",
        "run_id",
        "scope",
        "source_conserved",
        "transport_concurrency",
        "boundary_words",
        "image",
    }
    for name in names:
        digest = frozen["code_sha256"].get(name)
        if (
            name == "p003_topology_ownership.py"
            and frozen["config"].get("image", True) is True
            and frozen["config"].get("boundary_words", "strict") == "strict"
            and set(frozen["config"]) <= historical_config_keys
            and digest == "9f5211f1051d6b39e43f0b4d8fcd0be06a52caee613b1c0b9fa80e39a3271ef8"
        ):
            continue  # Root reviewed the exact image-default bodies, criteria and collect semantics.
        if (
            name == "p003_topology_run.py"
            and frozen["config"].get("boundary_words", "strict") == "strict"
            and set(frozen["config"]) <= historical_config_keys
            and digest == "3368006228075df064d2e6cceb024ff6896817dce3e1c6b210ce4fb84b15a13f"
        ):
            continue  # Root reviewed default partition/body semantics; only cost-scope label differs.
        if digest != sha((Path(__file__).parent / name).read_bytes()):
            raise ValueError("Unsupported incremental replay helper version: " + name)


def imported_baseline(
    directory: Path, frozen: dict[str, Any], key: str, copied_name: str, trusted: dict[str, str] | None
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Check explicit copied evidence, source identity and separate operator trust."""
    from bench.p003_report import verify_archive

    if not trusted:
        raise ValueError("Incremental baseline requires an independently supplied trusted source map")
    attestation = frozen[key]
    if attestation["copied_directory"] != copied_name:
        raise ValueError("Incremental copied directory differs from declared baseline")
    copied = guard_path(directory / copied_name)
    original_frozen, report = _read(copied / "frozen.json"), _read(copied / "report.json")
    hashes = attestation["file_sha256"]
    for name, digest in hashes.items():
        parts = Path(name).parts
        if not (len(parts) == 1 or (len(parts) == 2 and parts[0] == "code")) or ".." in parts:
            raise ValueError("Unsafe copied baseline evidence path")
        if sha(guard_path(copied / name).read_bytes()) != digest:
            raise ValueError("Copied incremental baseline evidence changed")
    if report["config"] != original_frozen["config"] or attestation["original_config"] != original_frozen["config"]:
        raise ValueError("Imported baseline configuration changed")
    if original_frozen["manifest_sha256"] != frozen["manifest_sha256"] or {
        r["id"]: r for r in original_frozen["records"]
    } != {r["id"]: r for r in frozen["records"]}:
        raise ValueError("Imported baseline source inventory changed")
    pages = {page["id"]: page for page in report["results"]}
    if len(pages) != len(report["results"]) or set(pages) != {r["id"] for r in frozen["records"]}:
        raise ValueError("Imported baseline lacks complete intended page inventory")
    required = {"report.json", "frozen.json", *("code/" + name for name in original_frozen["code_sha256"])}
    for record in frozen["records"]:
        ident = record["id"]
        if Path(ident).name != ident or ident in {"", ".", ".."}:
            raise ValueError("Unsafe baseline page identifier")
        if sha(guard_path(Path(record["pdf_path"])).read_bytes()) != record["pdf_sha256"]:
            raise ValueError("Imported baseline source PDF changed")
        page = pages[ident]
        required.add(f"{ident}-result.json")
        if _read(copied / f"{ident}-result.json") != page:
            raise ValueError("Imported baseline page result differs from report")
        if page["status"] == "ok":
            required.update({f"{ident}-structure.json", f"{ident}.md"})
        required.update(f"{ident}-request-{i}.json" for i in range(len(page.get("calls", []))))
        required.update(
            f"{ident}-request-{crop['request_index']}.json" for crop in page.get("transcription_regions", [])
        )
    if not required <= set(hashes):
        raise ValueError("Imported baseline attestation omits required source requests or outputs")
    verify_archive(copied, original_frozen, trusted)
    return copied, original_frozen, report


def _retained_output(directory: Path, copied: Path, page: dict[str, Any]) -> None:
    for suffix in ("-structure.json", ".md"):
        original = copied / (page["id"] + suffix)
        if original.exists() and (directory / original.name).read_bytes() != original.read_bytes():
            raise ValueError("Incremental fallback changed original complete output bytes")


def verify_topology(
    directory: Path,
    report: dict[str, Any],
    frozen: dict[str, Any],
    trusted: dict[str, dict[str, str]] | None,
    *,
    reviewed_parser_sha256: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Replay frozen topology/source partition, row ownership, anchors and atomic outputs."""
    from bench import p003_candidate_run as candidate
    from bench import p003_topology_ownership as ownership
    from bench import p003_topology_run as runner
    from bench import pipeline_run as pipeline
    from bench.generalization_run import _table_bounds
    from bench.pipeline_regions import compose
    from bench.pipeline_source_order import render_source

    names = {"source-baseline", "topology-baseline"}
    if trusted is None or set(trusted) != names:
        raise ValueError("Topology replay requires independent source and topology baseline trust maps")
    _helpers(
        frozen,
        (
            "p003_topology_run.py",
            "p003_topology_ownership.py",
            "pipeline_regions.py",
            "pipeline_assembly.py",
            "pipeline_source_order.py",
            "generalization_run.py",
            "pipeline_vision_transcription.py",
            "p003_transcription_design.py",
        ),
    )
    config = frozen["config"]
    reviewed = config.get("reviewed_parser_sha256", [])
    if not set(reviewed) <= set(reviewed_parser_sha256) or any(
        digest not in candidate.ROOT_REVIEWED_PARSER_SHA256 for digest in reviewed
    ):
        raise ValueError("Historical topology parser requires independently supplied root review")
    source_dir, source_frozen, source_report = imported_baseline(
        directory, frozen, "source_baseline", "source-baseline", trusted["source-baseline"]
    )
    topo_dir, topo_frozen, topo_report = imported_baseline(
        directory, frozen, "topology_baseline", "topology-baseline", trusted["topology-baseline"]
    )
    runner.authenticate_source(source_dir, trusted["source-baseline"])
    candidate.authenticate(topo_dir, trusted["topology-baseline"], reviewed_parser_sha256=tuple(reviewed))
    if report["source_generation_report"] != source_report or report["topology_generation_report"] != topo_report:
        raise ValueError("Topology historical reports changed")
    if config["baseline_source_order"] != source_frozen["config"].get("source_order", "legacy"):
        raise ValueError("Topology changed historical source rendering order")
    originals = {p["id"]: p for p in source_report["results"]}
    topologies = {p["id"]: p for p in topo_report["results"]}
    verified = {}
    for page in report["results"]:
        ident = page["id"]
        original = originals[ident]
        status = page["topology_status"]
        if _read(directory / f"{ident}-result.json") != page or page["calls"] != original["calls"]:
            raise ValueError("Topology result or historical call metadata changed")
        work = None
        if original["status"] == "ok" and topologies[ident]["status"] == "ok":
            try:
                work = runner.prepare_page(original, topologies[ident], topo_dir, topo_frozen["config"], config)
            except runner.UnsupportedError:
                if status != "unsupported_retained_baseline":
                    raise ValueError("Unsupported topology preflight was not retained explicitly") from None
        if status == "completed":
            if work is None or not work["crops"] or config.get("prepare_only"):
                raise ValueError("Topology completion lacks eligible frozen evidence")
            if _read(directory / f"{ident}-ownership-plan.json") != work["plan"]:
                raise ValueError("Topology source ownership partition changed")
            states, calls = deepcopy(work["states"]), []
            if len(page["topology_regions"]) != len(work["crops"]):
                raise ValueError("Topology crop inventory changed")
            for crop, info in zip(work["crops"], page["topology_regions"], strict=True):
                stem = f"{ident}-{crop['id']}"
                if (
                    info["id"] != crop["id"]
                    or info["crop_index"] != crop["crop_index"]
                    or info["status"] != "completed"
                ):
                    raise ValueError("Topology crop provenance changed")
                if info["snapshot_sha256"] != crop["snapshot"].sha256 or _read(
                    directory / info["snapshot_file"]
                ) != json.loads(crop["snapshot"].packet_json):
                    raise ValueError("Topology immutable source snapshot changed")
                responses = []
                if info["rows"] != [f"{stem}-row-{i}" for i in range(len(crop["row_bodies"]))]:
                    raise ValueError("Topology row request inventory changed")
                for request_stem, body in zip(info["rows"], crop["row_bodies"], strict=True):
                    if _read(directory / f"{request_stem}-request.json") != body:
                        raise ValueError("Topology row question changed")
                    response = _read(directory / f"{request_stem}-response.json")
                    calls.append(response)
                    responses.append(response["result"])
                rows = ownership.collect(crop["snapshot"], crop["row_bodies"], responses)
                if _read(directory / f"{stem}-row-receipt.json") != rows:
                    raise ValueError("Topology row receipt changed")
                bodies = ownership.batches(
                    crop["snapshot"], config["model"], crop["url"], rows=rows, max_questions=config["max_questions"]
                )
                if info["cells"] != [f"{stem}-cell-{i}" for i in range(len(bodies))]:
                    raise ValueError("Topology anchor request inventory changed")
                results = []
                for request_stem, body in zip(info["cells"], bodies, strict=True):
                    if _read(directory / f"{request_stem}-request.json") != body:
                        raise ValueError("Topology anchor question changed")
                    response = _read(directory / f"{request_stem}-response.json")
                    calls.append(response)
                    results.append(response["result"])
                audit = ownership.assemble(crop["snapshot"], crop["row_bodies"], responses, bodies, results)
                if (
                    _read(directory / f"{stem}-audit.json") != audit
                    or _read(directory / f"{stem}-updated-state.json") != audit["state"]
                ):
                    raise ValueError("Topology ownership assembly changed")
                states[crop["id"]] = audit["state"]
            composed = compose(work["plan"], states)
            _table_bounds(original["source"], composed)
            if calls != page["topology_calls"] or page["tables"] != composed["tables"] or not page["source_conserved"]:
                raise ValueError("Topology final output differs from replayed source ownership")
            expected_regions = [{"id": name, "state": state} for name, state in states.items()]
            if (
                page["regions"] != expected_regions
                or page["region_plan"] != {k: v for k, v in work["plan"].items() if k != "words"}
                or page["unresolved_ids"] != composed["unresolved_ids"]
            ):
                raise ValueError("Topology final region inventory changed")
            order = {word["id"]: i for i, word in enumerate(original["source"]["words"])}
            texts = [
                (
                    min((order[i] for i in region["source_ids"]), default=len(order)),
                    pipeline.markdown(
                        render_source(original["source"], region)
                        if config["baseline_source_order"] == "original"
                        else region["source"],
                        states[region["id"]],
                    ),
                )
                for region in work["plan"]["regions"]
            ]
            markdown = "\n".join(value for _, value in sorted(texts))
            if (
                _read(directory / f"{ident}-structure.json") != composed
                or (directory / f"{ident}.md").read_text() != markdown
            ):
                raise ValueError("Topology complete structure or Markdown differs from replay")
        else:
            if status not in {
                "prepared_retained_baseline",
                "not_applicable",
                "baseline_failed_skipped",
                "topology_baseline_failed_skipped",
                "unsupported_retained_baseline",
                "failed_retained_baseline",
            }:
                raise ValueError("Unknown topology fallback disposition")
            if any(page.get(key) != value for key, value in original.items()):
                raise ValueError("Topology fallback changed historical output metadata")
            _retained_output(directory, source_dir, original)
            if status == "prepared_retained_baseline" and not config.get("prepare_only"):
                raise ValueError("Topology prepare-only fallback lacks explicit declaration")
            if status == "not_applicable" and (work is None or work["crops"]):
                raise ValueError("Topology not-applicable status differs from frozen crop inventory")
            if status == "baseline_failed_skipped" and original["status"] == "ok":
                raise ValueError("Topology source failure disposition lacks a failed baseline")
            if status == "topology_baseline_failed_skipped" and topologies[ident]["status"] == "ok":
                raise ValueError("Topology generation failure disposition lacks a failed baseline")
            if status == "prepared_retained_baseline":
                if work is None or not work["crops"] or page["topology_calls"]:
                    raise ValueError("Topology preparation lacks eligible source evidence or contains model calls")
                if _read(directory / f"{ident}-ownership-plan.json") != work["plan"]:
                    raise ValueError("Prepared topology source partition changed")
                if len(page["topology_regions"]) != len(work["crops"]):
                    raise ValueError("Prepared topology crop inventory changed")
                for crop, info in zip(work["crops"], page["topology_regions"], strict=True):
                    stem = f"{ident}-{crop['id']}"
                    if (
                        info["status"] != "prepared"
                        or info["cells"]
                        or info["snapshot_sha256"] != crop["snapshot"].sha256
                    ):
                        raise ValueError("Prepared topology snapshot metadata changed")
                    if info["snapshot_file"] != f"{stem}-snapshot.json" or _read(
                        directory / info["snapshot_file"]
                    ) != json.loads(crop["snapshot"].packet_json):
                        raise ValueError("Prepared topology immutable source snapshot changed")
                    expected_stems = [f"{stem}-row-{i}" for i in range(len(crop["row_bodies"]))]
                    if info["rows"] != expected_stems or info["maximum_new_ownership_calls"] != 2 * len(expected_stems):
                        raise ValueError("Prepared topology row request inventory changed")
                    for request_stem, body in zip(expected_stems, crop["row_bodies"], strict=True):
                        if _read(directory / f"{request_stem}-request.json") != body:
                            raise ValueError("Prepared topology question changed")
            if status in {"unsupported_retained_baseline", "failed_retained_baseline"} and not page["topology_errors"]:
                raise ValueError("Topology failure omits its retained error")
        verified[ident] = {"operational": page["status"] == "ok", "scope": "incremental frozen topology ownership"}
    return {
        "source_report_sha256": sha((source_dir / "report.json").read_bytes()),
        "topology_report_sha256": sha((topo_dir / "report.json").read_bytes()),
    }, verified
