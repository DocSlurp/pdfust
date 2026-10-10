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


def _response_identity(body: dict[str, Any], response: dict[str, Any]) -> None:
    digest = sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode())
    if response.get("entry", {}).get("request_sha256") != digest:
        raise ValueError("Ownership response attribution differs from exact serialized request")


def _transcript_origin(
    directory: Path, report: dict[str, Any], frozen: dict[str, Any], trusted: dict[str, str]
) -> Path:
    from bench.p003_report import verify_archive
    from bench.p003_topology_replay import authenticate

    origin = frozen["transcript_origin"]
    if report.get("transcript_origin") != origin or origin["copied_directory"] != "original-ownership-run":
        raise ValueError("Transcript original provenance differs from frozen record")
    if origin["new_api_calls"] != 0 or origin["original_failures_preserved"] is not True:
        raise ValueError("Transcript provenance does not preserve original failures and zero new calls")
    copied = directory / origin["copied_directory"]
    for name, digest in origin["file_sha256"].items():
        parts = Path(name).parts
        if not (len(parts) == 1 or (len(parts) == 2 and parts[0] == "code")) or ".." in parts:
            raise ValueError("Unsafe transcript evidence path")
        if sha(guard_path(copied / name).read_bytes()) != digest:
            raise ValueError("Retained original transcript bytes changed")
    original_frozen, original = authenticate(copied, trusted)
    verify_archive(copied, original_frozen, trusted)
    if original != origin["original_report"] or original_frozen["records"] != frozen["records"]:
        raise ValueError("Transcript original report or source inventory changed")
    for key in ("source_baseline", "topology_baseline"):
        if original_frozen[key]["file_sha256"] != frozen[key]["file_sha256"]:
            raise ValueError("Transcript imported generation evidence differs from original")
    required = {"report.json", "frozen.json", *("code/" + n for n in original_frozen["code_sha256"])}
    required.update(f"{r['id']}-result.json" for r in original["results"])
    for retained in origin["retained_responses"]:
        stem = retained["stem"]
        if Path(stem).name != stem:
            raise ValueError("Unsafe retained transcript request stem")
        required.update({f"{stem}-request.json", f"{stem}-response.json"})
    if not required <= set(origin["file_sha256"]):
        raise ValueError("Transcript origin omits required original artifacts")
    return copied


def _retained_response(
    directory: Path, original: Path, stem: str, body: dict[str, Any], response: dict[str, Any]
) -> dict[str, Any]:
    if _read(original / f"{stem}-request.json") != body:
        raise ValueError("Transcript reused request differs from original question")
    if (directory / f"{stem}-response.json").read_bytes() != (original / f"{stem}-response.json").read_bytes():
        raise ValueError("Transcript reused response differs from immutable original bytes")
    return {
        "stem": stem,
        "body_sha256": sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()),
        "response_sha256": sha((original / f"{stem}-response.json").read_bytes()),
        "original_entry": response["entry"],
    }


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
        uniform_config = frozen["config"]
        if (
            name == "decision_gateway.py"
            and digest == "ce182e15faf9d8bb853f2f24e7b36e56ebe188a53c4edbdfd31c02f4a5d1eefd"
            and uniform_config.get("processor") == "p003_gate"
            and uniform_config.get("gate_provider") == "vercel"
        ):
            continue  # Root reviewed unchanged wire/normalization; only fixed diagnostic hints were added.
        if (
            name == "p003_topology_run.py"
            and digest in {
                "d40fc7789a2644e1ea85e38b2adc2d6d2c9a6c2e5b897b24a69215f4adb53165",
                "dcad1cc35f0a9d2b756e00e3bb9d5c2866829871bb2b770aee55a797988159b5",
            }
            and uniform_config.get("run_hosted") is True
            and uniform_config.get("prepare_only") is False
            and uniform_config.get("image", True) is True
            and uniform_config.get("boundary_words", "strict") == "strict"
            and set(uniform_config) <= historical_config_keys
        ):
            continue  # Root reviewed exact hosted strict defaults; original failures remain failures.
        if (
            name in {"p003_topology_run.py", "p003_topology_geometry.py"}
            and uniform_config.get("chunked_inventory", False) is False
            and uniform_config.get("crossed_tables", "strict") == "strict"
            and "topology_evidence" not in uniform_config
            and set(uniform_config)
            <= historical_config_keys
            | {"geometry_only", "band_mode", "transcript_replay", "chunked_inventory", "crossed_tables"}
            and digest
            == {
                "p003_topology_run.py": "7037330072debc889bdd37225b334090da09ed4791b7f6d10e70cd279f7dbdaf",
                "p003_topology_geometry.py": "1f5d69b8a190fb4a71b003077c075b80005ca492eae0173645692558091e1d12",
            }[name]
        ):
            continue  # Root reviewed unchanged defaults before the bounded local inventory protocol.
        if (
            name == "p003_topology_run.py"
            and digest == "83ee9fb21074606db7d8020daae3c1fc5046712e97736b6139edf5a060998edf"
            and uniform_config.get("transcript_replay") is True
            and uniform_config.get("image", True) is True
            and uniform_config.get("boundary_words", "strict") == "strict"
            and uniform_config.get("band_mode", "uniform") == "uniform"
            and set(uniform_config) <= historical_config_keys | {"transcript_replay", "band_mode"}
        ):
            continue  # Root reviewed exact-body replay default semantics before source-band controls.
        if (
            name in {"p003_topology_run.py", "p003_topology_geometry.py", "p003_topology_ownership.py"}
            and uniform_config.get("geometry_only") is True
            and uniform_config.get("image", True) is True
            and uniform_config.get("band_mode", "uniform") == "uniform"
            and uniform_config.get("boundary_words") == "residual"
            and set(uniform_config) <= historical_config_keys | {"geometry_only", "band_mode"}
            and digest
            == {
                "p003_topology_run.py": "dcad1cc35f0a9d2b756e00e3bb9d5c2866829871bb2b770aee55a797988159b5",
                "p003_topology_geometry.py": "1b84661255194470c0067badd293c928a79f72e547ba7633e18d87d92a451fee",
                "p003_topology_ownership.py": "9f5211f1051d6b39e43f0b4d8fcd0be06a52caee613b1c0b9fa80e39a3271ef8",
            }.get(name)
        ):
            continue  # Root reviewed these exact default-uniform/residual control snapshots.
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
            and frozen["config"].get("image", True) is True
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
    from bench import p003_topology_chunks as chunks
    from bench import p003_topology_ownership as ownership
    from bench import p003_topology_run as runner
    from bench import pipeline_run as pipeline
    from bench.generalization_run import _table_bounds
    from bench.pipeline_regions import compose
    from bench.pipeline_source_order import render_source

    config = frozen["config"]
    if type(config.get("chunked_inventory", False)) is not bool:
        raise ValueError("Invalid topology inventory treatment")
    if config.get("topology_evidence", "compact") not in {"compact", "neighbors", "bands"} or (
        "topology_evidence" in config and not config.get("chunked_inventory")
    ):
        raise ValueError("Invalid topology local evidence treatment")
    if config.get("crossed_tables", "strict") not in {"strict", "residual_prose"}:
        raise ValueError("Invalid crossed source table treatment")
    protocol = chunks if config.get("chunked_inventory") else ownership
    names = {"source-baseline", "topology-baseline"}
    if config.get("transcript_replay"):
        names.add("original-ownership-run")
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
    if config.get("geometry_only"):
        _helpers(frozen, ("p003_topology_geometry.py",))
        if config.get("band_mode", "uniform") not in {"uniform", "source"}:
            raise ValueError("Unsupported geometry band treatment")
        if config.get("band_mode") == "source":
            _helpers(frozen, ("p003_spatial_bands.py",))
    if config.get("chunked_inventory"):
        _helpers(frozen, ("p003_topology_chunks.py", "p003_spatial_bands.py"))
    if config.get("transcript_replay"):
        _helpers(frozen, ("p003_topology_replay.py",))
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
    transcript = None
    if config.get("transcript_replay"):
        transcript = _transcript_origin(directory, report, frozen, trusted["original-ownership-run"])
    if config.get("geometry_only") or transcript is not None:
        incremental = report["incremental_ownership"]
        if (
            incremental["attempts"]
            or incremental["returned_calls"]
            or report.get("pages_per_minute") is not None
            or report.get("pages_per_dollar") is not None
        ):
            raise ValueError("Offline ownership control contains new API calls or full-pipeline rates")
    retained = []
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
            if transcript is not None:
                from bench.p003_topology_replay import _check_partition

                _check_partition(_read(transcript / f"{ident}-ownership-plan.json"), work["plan"])
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
                if config.get("geometry_only"):
                    from bench import p003_topology_geometry as geometry

                    audit = geometry.place(crop["snapshot"], band_mode=config.get("band_mode", "uniform"))
                    mechanism = "source_band_geometry" if config.get("band_mode") == "source" else "uniform_geometry"
                    if (
                        info["rows"]
                        or info["cells"]
                        or info["maximum_new_ownership_calls"]
                        or info["placement_mechanism"] != mechanism
                    ):
                        raise ValueError("Geometry control contains model questions or changed placement policy")
                    if (
                        _read(directory / f"{stem}-geometry-audit.json") != audit
                        or _read(directory / f"{stem}-updated-state.json") != audit["state"]
                    ):
                        raise ValueError("Geometry source placement audit differs from replay")
                else:
                    responses = []
                    if info["rows"] != [f"{stem}-row-{i}" for i in range(len(crop["row_bodies"]))]:
                        raise ValueError("Topology row request inventory changed")
                    for request_stem, body in zip(info["rows"], crop["row_bodies"], strict=True):
                        if _read(directory / f"{request_stem}-request.json") != body:
                            raise ValueError("Topology row question changed")
                        response = _read(directory / f"{request_stem}-response.json")
                        _response_identity(body, response)
                        if transcript is not None:
                            retained.append(_retained_response(directory, transcript, request_stem, body, response))
                        calls.append(response)
                        responses.append(response["result"])
                    rows = protocol.collect(crop["snapshot"], crop["row_bodies"], responses)
                    if _read(directory / f"{stem}-row-receipt.json") != rows:
                        raise ValueError("Topology row receipt changed")
                    bodies = protocol.batches(
                        crop["snapshot"],
                        config["model"],
                        crop["url"],
                        rows=rows,
                        max_questions=config["max_questions"],
                        image=config.get("image", True),
                        **(
                            {"evidence_mode": config.get("topology_evidence", "compact")}
                            if config.get("chunked_inventory")
                            else {}
                        ),
                    )
                    if info["cells"] != [f"{stem}-cell-{i}" for i in range(len(bodies))]:
                        raise ValueError("Topology anchor request inventory changed")
                    results = []
                    for request_stem, body in zip(info["cells"], bodies, strict=True):
                        if _read(directory / f"{request_stem}-request.json") != body:
                            raise ValueError("Topology anchor question changed")
                        response = _read(directory / f"{request_stem}-response.json")
                        _response_identity(body, response)
                        if transcript is not None:
                            retained.append(_retained_response(directory, transcript, request_stem, body, response))
                        calls.append(response)
                        results.append(response["result"])
                    audit = protocol.assemble(crop["snapshot"], crop["row_bodies"], responses, bodies, results)
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
    if transcript is not None and retained != frozen["transcript_origin"]["retained_responses"]:
        raise ValueError("Transcript retained-response inventory differs from exact replay")
    return {
        "source_report_sha256": sha((source_dir / "report.json").read_bytes()),
        "topology_report_sha256": sha((topo_dir / "report.json").read_bytes()),
    }, verified
