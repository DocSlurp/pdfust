"""Offline P003 evaluation of frozen DEV decision treatments and matched repeats."""

# Artifact observations are heterogeneous; validation occurs at the file boundary.
# ruff: noqa: EM101, TRY003, C901, PLR0912, PLR2004, EM102, PLC0415, S311, PLR0913, SLF001
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.generalization_scoring import _cells, audit_model_body, score_dataset
from bench.silver import canonical, guard_path, sha, write_json

SOURCE_FIELDS = ("id", "pdf_path", "pdf_sha256", "page_number")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Expected JSON object")
    return value


def _rate(count: float, denominator: object, factor: float = 1) -> float | None:
    if isinstance(denominator, bool) or not isinstance(denominator, (int, float)):
        return None
    return count / denominator * factor if math.isfinite(denominator) and denominator > 0 else None


def strict_scores(targets: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Add span-aware exact anchors while preserving established P002 metrics."""
    result = score_dataset(targets, predictions)
    observed = {p["id"]: p for p in predictions}
    references = {p["id"]: p for p in targets}
    for page in result["pages"]:
        exact = 0
        if page.get("structural_scored") and not page["error"]:
            prediction = observed[page["id"]]
            tables = prediction.get("tables", [])
            for pair in page["matches"]:
                reference = _cells(references[page["id"]]["tables"][pair["target"]])
                actual = _cells(tables[pair["prediction"]])
                exact += sum(reference[key] == actual[key] for key in reference.keys() & actual.keys())
        page["strict_exact_cells"] = exact
    result["totals"]["strict_exact_cells"] = sum(p["strict_exact_cells"] for p in result["pages"])
    positive = [p for p in result["pages"] if p.get("positive_page")]
    result["positive_macro"] = {
        "positive_pages": len(positive),
        "strict_exact_cell_recall": statistics.mean(p["strict_exact_cells"] / p["expected_cells"] for p in positive)
        if positive
        else None,
        "complete_table_recall": statistics.mean(p["complete_tables"] / p["expected_tables"] for p in positive)
        if positive
        else None,
    }
    return result


def costs(report: dict[str, Any]) -> dict[str, Any]:
    """Never turn missing, unresolved or partially estimated charges into totals."""
    bases = report.get("cost_bases", {})
    effective = report.get("effective_usd")
    complete = report.get("ledger_attempts") is not None and not any(bases.get(k, 0) for k in ("unknown", "reserved"))
    valid = (
        not isinstance(effective, bool)
        and isinstance(effective, (int, float))
        and math.isfinite(effective)
        and effective >= 0
    )
    return {
        "effective_api_usd": effective if complete and valid else None,
        "provider_reported_subtotal_usd": report.get("provider_reported_usd"),
        "missing_provider_charge_count": report.get("missing_provider_charge_count"),
        "ledger_attempts": report.get("ledger_attempts"),
        "cost_bases": bases,
        "accounted_usd_including_reservations": report.get("accounted_usd"),
        "scope": "all attempts attributed to run, including failures; API only; zero charge retained",
    }


def verify_cost_reconciliation(directory: Path, sidecar_path: Path, ledger_path: Path) -> dict[str, Any]:
    """Verify an immutable accounting overlay against archived bodies and exact run attempts."""
    sidecar = _read(sidecar_path)
    report = _read(directory / "report.json")
    report_hash = sha(guard_path(directory / "report.json").read_bytes())
    prefix = f"P003/{report['config']['run_id']}/"
    if sidecar.get("schema") != 1 or sidecar.get("original_report_sha256") != report_hash:
        raise ValueError("Cost overlay is not bound to this immutable report")
    if sidecar.get("run_tag_prefix") != prefix:
        raise ValueError("Cost overlay run tag differs")
    ledger = _read(ledger_path)
    attempts = [e for e in ledger["requests"] if e.get("tag", "").startswith(prefix)]
    rows = sidecar["entries"]
    by_index = {e["index"]: e for e in attempts}
    overlays = {r["ledger_index"]: r for r in rows}
    if len(by_index) != len(attempts) or len(overlays) != len(rows) or set(by_index) != set(overlays):
        raise ValueError("Cost overlay must include exactly every run-attributed ledger attempt")
    if report.get("ledger_attempts") != len(rows):
        raise ValueError("Original report attempt count differs from ledger inventory")
    fields = ("accounted_usd", "cost_status", "provider_reported_usd")

    def accounting(entry: dict[str, Any]) -> dict[str, Any]:
        return {k: entry[k] for k in fields if k in entry}

    def amount(value: object) -> bool:
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0

    def close(left: object, right: object) -> bool:
        return amount(left) and amount(right) and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)

    returned = {c["entry"]["index"]: c["entry"] for page in report.get("results", []) for c in page.get("calls", [])}
    original_rows, reconciled_rows, evidence = [], [], []
    for row in rows:
        entry = by_index[row["ledger_index"]]
        original, reconciled = row["original_accounting"], row["reconciled_accounting"]
        if not amount(original.get("accounted_usd")) or not amount(reconciled.get("accounted_usd")):
            raise ValueError("Invalid overlay accounting amount")
        if any(k in original and not amount(original[k]) for k in ("provider_reported_usd",)):
            raise ValueError("Invalid original provider charge")
        if entry["request_sha256"] != row["request_sha256"] or accounting(entry) != accounting(reconciled):
            raise ValueError("Overlay request identity or reconciled ledger accounting differs")
        request_path = guard_path(sidecar_path.parent / row["request_path"])
        if sha(request_path.read_bytes()) != row["request_sha256"]:
            raise ValueError("Archived exact request bytes changed")
        if entry["index"] in returned and accounting(returned[entry["index"]]) != accounting(original):
            raise ValueError("Original returned-call accounting differs from immutable report")
        if row.get("response_path") is None:
            if entry.get("response_file") or row.get("response_sha256") is not None or reconciled != original:
                raise ValueError("Missing response cannot support changed accounting")
            response_hash = None
        else:
            response_path = guard_path(sidecar_path.parent / row["response_path"])
            response_hash = sha(response_path.read_bytes())
            if response_hash != row["response_sha256"] or response_path.name != entry.get("response_file"):
                raise ValueError("Retained provider response hash or ledger filename differs")
            response = _read(response_path)
            for name, ledger_name in (("id", "generation_id"), ("model", "served_model"), ("provider", "provider")):
                if entry.get(ledger_name) is not None and response.get(name) != entry[ledger_name]:
                    raise ValueError("Retained provider response attribution differs")
            if reconciled != original and not any(
                revision.get("original") == original
                and revision.get("reconciled") == reconciled
                and revision.get("response_sha256") == response_hash
                for revision in entry.get("accounting_revisions", [])
            ):
                raise ValueError("Changed accounting lacks preserved ledger revision history")
            usage = response.get("usage", {})
            gateway = usage.get("cost")
            if amount(gateway) and not close(original.get("provider_reported_usd"), gateway):
                raise ValueError("Original raw provider gateway charge differs from retained accounting")
            upstream = usage.get("cost_details", {}).get("upstream_inference_cost")
            byok = usage.get("is_byok") is True and amount(gateway) and amount(upstream) and upstream > 0
            if byok:
                total = gateway + upstream
                if (
                    reconciled.get("cost_status") != "provider-reported BYOK upstream plus gateway USD"
                    or not close(reconciled.get("provider_reported_usd"), gateway)
                    or not close(reconciled.get("gateway_reported_usd"), gateway)
                    or not close(reconciled.get("upstream_reported_usd"), upstream)
                    or not close(reconciled.get("accounted_usd"), total)
                    or not close(reconciled.get("effective_usd"), total)
                    or original.get("provider_reported_usd") != gateway
                ):
                    raise ValueError("BYOK overlay must preserve gateway charge and sum exact reported upstream")
            elif reconciled != original:
                raise ValueError("Only retained explicit BYOK upstream charges may change in this overlay")
        original_rows.append(original)
        reconciled_rows.append(reconciled)
        evidence.append(
            {"index": entry["index"], "request_sha256": row["request_sha256"], "response_sha256": response_hash}
        )
    if (
        not close(sum(e["accounted_usd"] for e in original_rows), report.get("accounted_usd"))
        or dict(Counter(e["cost_status"] for e in original_rows)) != report.get("cost_bases")
        or not close(sum(e.get("provider_reported_usd", 0) for e in original_rows), report.get("provider_reported_usd"))
        or sum("provider_reported_usd" not in e for e in original_rows) != report.get("missing_provider_charge_count")
    ):
        raise ValueError("Original per-attempt accounting does not reproduce immutable report totals")
    complete = all(e["cost_status"] not in {"reserved", "unknown"} for e in reconciled_rows)
    total = sum(e["accounted_usd"] for e in reconciled_rows)
    return {
        "original_report_sha256": report_hash,
        "sidecar_sha256": sha(guard_path(sidecar_path).read_bytes()),
        "ledger_sha256_at_verification": sha(guard_path(ledger_path).read_bytes()),
        "original": costs(report),
        "reconciled": {
            "effective_api_usd": total if complete else None,
            "known_partial_effective_api_usd": sum(
                e["accounted_usd"] for e in reconciled_rows if e["cost_status"] not in {"reserved", "unknown"}
            ),
            "accounted_usd_including_reservations": total,
            "provider_reported_gateway_subtotal_usd": sum(e.get("provider_reported_usd", 0) for e in reconciled_rows),
            "cost_bases": dict(Counter(e["cost_status"] for e in reconciled_rows)),
            "ledger_attempts": len(rows),
            "scope": "Exact run attempts; BYOK provider-reported upstream plus gateway, not an invoice total",
        },
        "evidence": evidence,
    }


ROOT_REVIEWED_WHOLE_CANDIDATE_RUNNER = "a22e4b5a5b88da313946f2c91a845f67207399d9c71464e5590b10c2c9b7765d"
ROOT_REVIEWED_DIFF_CANDIDATE_RUNNER = "eb5156fff571f7d784b28f5f68a366cf83a507ed7e6ace296d2c0cb451b15ba6"


def verify_candidate_helpers(frozen: dict[str, Any]) -> None:
    """Allow one root-reviewed unchanged full-evidence runner; strict difference helpers stay current."""
    mode = frozen["config"].get("evidence_mode", "whole")
    if mode not in {"whole", "differences"}:
        raise ValueError("Unknown frozen candidate evidence mode")
    image_mode = frozen["config"].get("image_mode", "rgb")
    visibility = frozen["config"].get("image_visibility", "source")
    if visibility not in {"source", "blank", "blur"} or (
        visibility != "source" and not frozen["config"].get("image_edge")
    ):
        raise ValueError("Unknown or pixel-free candidate visibility treatment")
    if image_mode not in {"rgb", "rgb_png", "grayscale8", "rgb_palette16"} or (
        image_mode != "rgb" and not frozen["config"].get("image_edge")
    ):
        raise ValueError("Unknown or pixel-free candidate image treatment")
    names = ["p003_candidate_run.py", "p003_candidate_choice.py", "pipeline_vision_transcription.py"]
    if mode == "differences":
        names.append("p003_candidate_diff.py")
    if image_mode != "rgb":
        names.append("p003_selector_image.py")
    if visibility != "source":
        names.append("p003_selector_visibility.py")
    for name in names:
        digest = frozen["code_sha256"].get(name)
        if digest == sha((Path(__file__).parent / name).read_bytes()):
            continue
        if (
            name == "p003_candidate_run.py"
            and visibility == "source"
            and digest == "a154f4b4b10d8f597fd73af8ee31a834f6d73c38cee65bda5c33d7792c6a472f"
            and frozen["config"].get("image_edge", 512) in {0, 128, 256, 400, 512, 768, 1024, 1200}
        ):
            continue  # Root reviewed exact source-visibility defaults before blank/blur controls.
        if (
            name == "p003_candidate_run.py"
            and visibility == "source"
            and image_mode == "rgb"
            and digest == "c4d1875b65fd67099eb4d2c3b4089b7492eac4576377ba91d6a7cdbf2ab5aec8"
            and frozen["config"].get("image_edge", 512) in {0, 128, 256, 400, 512, 768, 1024, 1200}
        ):
            continue  # Root reviewed exact RGB-default bytes before optional selector PNG transforms.
        if (
            name == "p003_candidate_run.py"
            and visibility == "source"
            and image_mode == "rgb"
            and frozen["config"].get("image_edge", 512) in {0, 256, 512, 768, 1024}
            and (
                digest == ROOT_REVIEWED_DIFF_CANDIDATE_RUNNER
                or (mode == "whole" and digest == ROOT_REVIEWED_WHOLE_CANDIDATE_RUNNER)
            )
        ):
            continue
        raise ValueError("Unsupported frozen candidate replay helper version: " + name)


def verify_treatment_helpers(frozen: dict[str, Any]) -> None:
    """Require exact current strict replay helpers for newly declared nonlegacy treatments."""
    config = frozen["config"]
    representation = config.get("transcription_representation", "legacy")
    if representation not in {"legacy", "matrix_strict", "atomic_cells"}:
        raise ValueError("Unknown frozen transcription representation")
    required = set()
    if representation != "legacy":
        if config.get("processor") not in {"vision_regions", "hybrid"}:
            raise ValueError("Unsupported frozen transcription representation processor")
        required |= {
            "p003_transcription_design.py",
            "generalization_vision_regions.py",
            "pipeline_vision_transcription.py",
        }
    image_mode = config.get("gate_image_mode", "rgb")
    if image_mode not in {"rgb", "grayscale8", "rgb_palette16"}:
        raise ValueError("Unknown frozen gate image mode")
    if image_mode != "rgb":
        required.add("p003_gate_image.py")
    rubric = config.get("gate_instructions", "legacy")
    semantic_rubrics = {"visual_schema", "recall_first", "skeptical", "local_relations"}
    if rubric not in {"legacy", "region", *semantic_rubrics}:
        raise ValueError("Unknown frozen gate instruction rubric")
    if rubric in semantic_rubrics:
        required.add("p003_prompt_variants.py")
    wire = config.get("transcription_wire_schema", "strict")
    if wire not in {"strict", "simple"}:
        raise ValueError("Unknown frozen transcription wire schema")
    if wire == "simple":
        if config.get("campaign") != "P003" or config.get("processor") != "vision_regions":
            raise ValueError("Simple transcription wire schema requires P003 vision_regions")
        required.add("p003_wire_schema.py")
    for name in required:
        local = Path(__file__).parent / name
        if not local.is_file() or frozen["code_sha256"].get(name) != sha(local.read_bytes()):
            raise ValueError("Unsupported frozen strict treatment replay helper version: " + name)


def transport_failures(
    predictions: list[dict[str, Any]], *, call_keys: tuple[str, ...] = ("calls", "repair_calls", "ranking_calls")
) -> dict[str, int]:
    """Retain explicit returned-call transport errors independently of page parser categories."""
    observed = {}
    unattributed = Counter()
    for page in predictions:
        for key in call_keys:
            for call in page.get(key, []):
                entry = call.get("entry", {})
                error = entry.get("error")
                if not isinstance(error, str):
                    continue
                index = entry.get("index")
                if type(index) is int:
                    observed[index] = error
                else:
                    unattributed[error] += 1
    return dict(Counter(observed.values()) + unattributed)


def verify_archive(directory: Path, frozen: dict[str, Any], trusted: dict[str, str] | None = None) -> dict[str, str]:
    """Require each archive hash to match a separately trusted local source digest."""
    hashes = frozen["code_sha256"]
    if not hashes:
        raise ValueError("Frozen code inventory is empty")
    checked = {}
    for name, digest in hashes.items():
        if Path(name).name != name or not name.endswith(".py"):
            raise ValueError("Unsafe archived source filename")
        if sha(guard_path(directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived source bytes changed")
        if trusted is None:
            local = Path(__file__).parent / name
            expected = sha(local.read_bytes()) if local.is_file() else None
        else:
            expected = trusted.get(name)
        if digest != expected:
            raise ValueError(
                f"Untrusted archived source: {name}; supply an independently reviewed source digest manifest"
            )
        checked[name] = digest
    return checked


def verify_incremental_run(
    directory: Path,
    report: dict[str, Any],
    frozen: dict[str, Any],
    baseline_trusted_code: dict[str, str] | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Replay atomic repairs and independently authenticate the historical baseline."""
    from bench.decision_p003_native import apply_decision_batches
    from bench.generalization_report import verify_output

    config = frozen["config"]
    attestation = frozen["baseline"]
    if attestation.get("copied_directory") != "baseline":
        raise ValueError("Incremental evaluation requires the complete copied baseline")
    baseline = guard_path(directory / "baseline")
    original_report = _read(baseline / "report.json")
    original_frozen = _read(baseline / "frozen.json")
    if original_report["config"] != original_frozen["config"]:
        raise ValueError("Historical baseline report and frozen config differ")
    if report.get("baseline_report") != original_report or attestation["original_config"] != original_frozen["config"]:
        raise ValueError("Copied baseline report or original config differs from provenance")
    if (
        original_frozen["records"] != frozen["records"]
        or original_frozen["manifest_sha256"] != frozen["manifest_sha256"]
    ):
        raise ValueError("Incremental inventory differs from original frozen intended inputs")
    source_order = original_frozen["config"].get("source_order", "legacy")
    if config.get("baseline_source_order") != source_order or attestation.get("source_order") != source_order:
        raise ValueError("Incremental repair changed baseline source order")
    verify_archive(baseline, original_frozen, baseline_trusted_code)
    original_predictions = {p["id"]: p for p in original_report["results"]}
    if len(original_predictions) != len(original_report["results"]):
        raise ValueError("Duplicate baseline prediction IDs")
    required = {"report.json", "frozen.json"}
    for ident, prediction in original_predictions.items():
        if Path(ident).name != ident or ident in {".", ".."}:
            raise ValueError("Unsafe baseline page ID")
        required.add(f"{ident}-result.json")
        if prediction.get("status") == "ok":
            required |= {f"{ident}-structure.json", f"{ident}.md"}
        required |= {f"{ident}-request-{step}.json" for step, _call in enumerate(prediction.get("calls", []))}
    hashes = attestation["file_sha256"]
    required |= {f"code/{name}" for name in original_frozen["code_sha256"]}
    allowed = {"report.json", "frozen.json"} | {
        f"{r['id']}{suffix}" for r in frozen["records"] for suffix in ("-result.json", "-structure.json", ".md")
    }
    allowed |= {f"code/{name}" for name in original_frozen["code_sha256"]}
    prefixes = tuple(f"{r['id']}-" for r in frozen["records"])
    for name in hashes:
        if (
            Path(name).name == name
            and name.startswith(prefixes)
            and name.endswith(".json")
            and ("-request" in name or "-response" in name)
        ):
            allowed.add(name)
    if not required <= hashes.keys() or not hashes.keys() <= allowed:
        raise ValueError("Incomplete or unexpected baseline attestation inventory")
    for name, digest in hashes.items():
        if sha(guard_path(baseline / name).read_bytes()) != digest:
            raise ValueError("Copied baseline bytes changed")
    for prediction in original_predictions.values():
        verify_output(baseline, prediction, processor="regions", source_order=source_order)
    for name in ("decision_p003_boundaries.py", "decision_p003_native.py"):
        path = Path(__file__).parent / name
        if sha(path.read_bytes()) != frozen["code_sha256"].get(name):
            raise ValueError("Repair replay helper differs from independently authenticated archived semantics")
    verified = {}
    for prediction in report["results"]:
        ident = prediction["id"]
        original = original_predictions.get(ident)
        if original is None:
            raise ValueError("Repair lacks a retained original baseline prediction")
        for key in ("source", "region_plan", "calls", "wall_seconds", "cpu_seconds"):
            if prediction.get(key) != original.get(key):
                raise ValueError(f"Repair changed immutable baseline evidence: {key}")
        provenance = prediction["baseline_provenance"]
        for key, expected in (
            ("result_sha256", hashes[f"{ident}-result.json"]),
            ("status", original["status"]),
            ("calls", original.get("calls", [])),
            ("source_order", source_order),
            ("wall_seconds", original.get("wall_seconds")),
            ("cpu_seconds", original.get("cpu_seconds")),
        ):
            if provenance.get(key) != expected:
                raise ValueError("Baseline result provenance differs from immutable originals")
        repair_status = prediction["repair_status"]
        if repair_status == "completed":
            old_regions = {r["id"]: r for r in original["regions"]}
            region_sources = {r["id"]: r["source"] for r in original["region_plan"]["regions"]}
            repairs = prediction["repair_regions"]
            if len(repairs) != len(old_regions) or {r["id"] for r in repairs} != set(old_regions):
                raise ValueError("Completed repair must retain every original region")
            rebuilt = {}
            for region in repairs:
                region_id = region["id"]
                old = old_regions[region_id]
                if region["original_state"] != old["state"]:
                    raise ValueError("Repair changed original region state provenance")
                if region["repair_status"] == "not_applicable":
                    rebuilt[region_id] = old["state"]
                    continue
                if region["repair_status"] != "completed":
                    raise ValueError("Completed page retains an incomplete region repair")
                menu = _read(directory / f"{ident}-{region_id}-boundary-menu.json")
                calls = sorted(
                    (c for c in prediction["repair_calls"] if c["region_id"] == region_id),
                    key=lambda c: c["batch_index"],
                )
                if [c["batch_index"] for c in calls] != list(range(len(calls))):
                    raise ValueError("Incomplete or duplicate retained repair batches")
                bodies, responses = [], []
                for call in calls:
                    stem = f"{ident}-{region_id}-boundary-{call['batch_index']}"
                    body = _read(directory / f"{stem}-request.json")
                    response = _read(directory / f"{stem}-response.json")
                    if body["model"] != config["model"] or response.get("replayed") or call.get("replayed"):
                        raise ValueError("Repair response uses wrong model or a replayed call")
                    if call["entry"] != response["entry"]:
                        raise ValueError("Repair call provenance differs from retained provider response")
                    bodies.append(body)
                    responses.append(response["result"])
                updated, audit = apply_decision_batches(
                    region_sources[region_id],
                    old["state"],
                    menu,
                    bodies,
                    responses,
                    minimum_join=config["minimum_join"],
                    minimum_margin=config["minimum_margin"],
                )
                if updated != region["updated_state"] or canonical(audit) != canonical(region["audit"]):
                    raise ValueError("Repair region differs from independently decoded model responses")
                if _read(directory / f"{ident}-{region_id}-updated-state.json") != updated:
                    raise ValueError("Retained updated region state changed")
                rebuilt[region_id] = updated
            expected_regions = [{**r, "state": rebuilt[r["id"]]} for r in original["regions"]]
            if prediction["regions"] != expected_regions:
                raise ValueError("Repaired region inventory differs from atomic replay")
        elif repair_status in {"not_applicable", "failed_retained_baseline", "baseline_failed_skipped"}:
            for key in ("tables", "regions", "unresolved_ids", "status", "source_conserved"):
                if prediction.get(key) != original.get(key):
                    raise ValueError("Fallback or skipped repair changed complete baseline outcome")
            for suffix in ("-structure.json", ".md"):
                name = f"{ident}{suffix}"
                if name in hashes and sha(guard_path(directory / name).read_bytes()) != hashes[name]:
                    raise ValueError("Atomic fallback bytes differ from baseline")
        else:
            raise ValueError("Unknown repair status")
        verified[ident] = verify_output(directory, prediction, processor="regions", source_order=source_order)
    return {
        "report_sha256": hashes["report.json"],
        "frozen_sha256": hashes["frozen.json"],
        "costs": costs(original_report),
        "resources": original_report.get("metrics", {}),
        "status_counts": dict(Counter(p["repair_status"] for p in report["results"])),
        "repair_error_pages": sum(bool(p.get("repair_errors")) for p in report["results"]),
        "original_request_artifacts": sum("-request" in name for name in hashes),
        "original_response_artifacts": sum("-response" in name for name in hashes),
        "original_response_scope": "Only retained raw response artifacts can be audited; original call summaries "
        "do not establish availability of every historical raw provider response",
        "scope": (
            "Original pipeline work is immutable historical provenance; incremental repairs use retained artifacts"
        ),
    }, verified


def verify_candidate_run(
    directory: Path,
    report: dict[str, Any],
    frozen: dict[str, Any],
    trusted_inputs: dict[str, dict[str, str]] | None,
    *,
    reviewed_parser_sha256: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Replay authenticated whole-crop pools and fresh selector decisions without generation."""
    from bench import generalization_vision_regions as regions
    from bench import p003_candidate_choice as chooser
    from bench import p003_candidate_run as runner
    from bench import pipeline_vision_transcription as transcription

    config = frozen["config"]
    reviewed = config.get("reviewed_parser_sha256", [])
    if (
        not isinstance(reviewed, list)
        or any(digest not in runner.ROOT_REVIEWED_PARSER_SHA256 for digest in reviewed)
        or any(digest not in runner.ROOT_REVIEWED_PARSER_SHA256 for digest in reviewed_parser_sha256)
        or not set(reviewed) <= set(reviewed_parser_sha256)
    ):
        raise ValueError("Historical candidate parser requires explicit independently supplied root-reviewed digest")
    inventories = frozen["candidate_inputs"]
    names = [f"baseline-{i}" for i in range(len(inventories))]
    if not 2 <= len(inventories) <= 4 or trusted_inputs is None or set(trusted_inputs) != set(names):
        raise ValueError("Candidate verification requires independent trust maps for every declared baseline")
    verify_candidate_helpers(frozen)
    baseline_reports, directories = [], []
    for name, inventory in zip(names, inventories, strict=True):
        if inventory["copied_directory"] != name:
            raise ValueError("Candidate copied baseline directory differs from declared input order")
        copied = directory / name
        hashes = inventory["file_sha256"]
        for filename, digest in hashes.items():
            parts = Path(filename).parts
            if not (len(parts) == 1 or (len(parts) == 2 and parts[0] == "code")) or ".." in parts:
                raise ValueError("Unsafe candidate baseline hash path")
            if sha(guard_path(copied / filename).read_bytes()) != digest:
                raise ValueError("Copied candidate baseline bytes changed")
        original_frozen = _read(copied / "frozen.json")
        baseline = _read(copied / "report.json")
        if (
            baseline["config"] != original_frozen["config"]
            or inventory["original_config"] != original_frozen["config"]
            or original_frozen["records"] != frozen["records"]
            or original_frozen["manifest_sha256"] != frozen["manifest_sha256"]
            or baseline["config"].get("transcription_representation", "legacy") != "legacy"
        ):
            raise ValueError("Candidate original configuration or source inventory changed")
        required = {"report.json", "frozen.json", *("code/" + n for n in original_frozen["code_sha256"])}
        for page in baseline["results"]:
            required.add(page["id"] + "-result.json")
            if page["status"] == "ok":
                required.update({page["id"] + "-structure.json", page["id"] + ".md"})
            required.update(
                f"{page['id']}-request-{crop['request_index']}.json" for crop in page.get("transcription_regions", [])
            )
        if not required <= set(hashes):
            raise ValueError("Candidate baseline hash inventory lacks original requests or output evidence")
        verify_archive(copied, original_frozen, trusted_inputs[name])
        runner.authenticate(copied, trusted_inputs[name], reviewed_parser_sha256=tuple(reviewed))
        directories.append(copied)
        baseline_reports.append(baseline)
    if report["candidate_generation_reports"] != baseline_reports:
        raise ValueError("Historical candidate reports differ from copied immutable originals")
    maps = [{p["id"]: p for p in baseline["results"]} for baseline in baseline_reports]
    verified = {}
    statuses = Counter()
    for prediction in report["results"]:
        ident = prediction["id"]
        if _read(directory / f"{ident}-result.json") != prediction:
            raise ValueError("Candidate result differs from complete report")
        pages = [mapping[ident] for mapping in maps]
        first = pages[0]
        provenance = [
            {
                "baseline_index": i,
                "status": page["status"],
                "calls": page.get("calls", []),
                "wall_seconds": page.get("wall_seconds"),
                "cpu_seconds": page.get("cpu_seconds"),
            }
            for i, page in enumerate(pages)
        ]
        if prediction["candidate_generation_provenance"] != provenance:
            raise ValueError("Candidate generation provenance changed")
        for key, value in first.items():
            if (
                key not in {"tables", "transcription_regions", "status", "source_conserved", "text_provenance"}
                and prediction.get(key) != value
            ):
                raise ValueError("Candidate ranking changed immutable baseline provenance")
        status = prediction["ranking_status"]
        statuses[status] += 1
        fallback = status in {"baseline_failed_skipped", "not_applicable_baseline_failure", "failed_retained_first"}
        if status == "baseline_failed_skipped" and first["status"] == "ok":
            raise ValueError("Successful candidate baseline incorrectly marked failed")
        if status == "not_applicable_baseline_failure" and all(p["status"] == "ok" for p in pages):
            raise ValueError("Candidate skip lacks a baseline failure")
        if fallback:
            if status == "failed_retained_first" and not prediction["ranking_errors"]:
                raise ValueError("Candidate atomic failure lacks explicit errors")
            for key in ("tables", "transcription_regions", "status", "source_conserved", "text_provenance"):
                if prediction.get(key) != first.get(key):
                    raise ValueError("Candidate atomic fallback differs from predeclared first baseline")
            for suffix in ("-structure.json", ".md"):
                name = ident + suffix
                if (
                    name in inventories[0]["file_sha256"]
                    and sha(guard_path(directory / name).read_bytes()) != inventories[0]["file_sha256"][name]
                ):
                    raise ValueError("Candidate fallback output bytes changed")
            verified[ident] = {"operational": first["status"] == "ok", "conserved": False}
            continue
        if (
            status not in {"completed", "not_applicable"}
            or any(p["status"] != "ok" for p in pages)
            or prediction["status"] != "ok"
            or prediction.get("source_conserved") is not False
            or prediction.get("text_provenance") != "model-transcribed"
        ):
            raise ValueError("Invalid completed candidate page or baseline status")
        proposal_keys = ("index", "request_index", "viewport", "detector_box")
        expected = [{k: crop[k] for k in proposal_keys} for crop in first["transcription_regions"]]
        if any(
            page["viewport"] != first["viewport"]
            or [{k: c[k] for k in proposal_keys} for c in page["transcription_regions"]] != expected
            for page in pages
        ):
            raise ValueError("Candidate generation crops do not match exactly")
        infos = prediction["ranking_regions"]
        if [r["index"] for r in infos] != list(range(len(expected))):
            raise ValueError("Candidate pool inventory is incomplete")
        staged, used_calls = deepcopy(first["transcription_regions"]), set()
        for index, info in enumerate(infos):
            crops = [page["transcription_regions"][index] for page in pages]
            candidates, urls, image_hashes = [], [], []
            for copied, crop in zip(directories, crops, strict=True):
                body = _read(copied / f"{ident}-request-{crop['request_index']}.json")
                url, pixels = runner._crop_bytes(body)
                expected_body = transcription.request(body["model"], url, crop["viewport"], body["max_tokens"])
                provider = _read(copied / "frozen.json")["config"].get("generation_provider")
                if provider:
                    expected_body["provider"] = {
                        "only": [provider],
                        "allow_fallbacks": False,
                        "require_parameters": True,
                    }
                if (
                    body != expected_body
                    or sha(json.dumps(expected_body, separators=(",", ":")).encode()) != crop["request"]["body_sha256"]
                ):
                    raise ValueError("Candidate original generation request changed")
                if (
                    sha(pixels) != crop["image"]["image_sha256"]
                    or crop["image"]["image_bytes"] != len(pixels)
                    or crop["image"]["image_viewport"] != crop["viewport"]
                ):
                    raise ValueError("Candidate original crop bytes or viewport changed")
                candidates.append(transcription.parse(crop["transcription_response"], crop["viewport"]))
                urls.append(url)
                image_hashes.append(sha(pixels))
            if len(set(image_hashes)) != 1 or info["original_crop_sha256"] != image_hashes[0]:
                raise ValueError("Candidate pool pixels are not identical")
            seed = int(sha(f"{config['seed']}/{ident}/{index}".encode())[:16], 16)
            pool = chooser.freeze_pool(crops[0]["viewport"], candidates, seed=seed)
            pool_record = chooser.pool_record(pool)
            if (
                info["viewport"] != crops[0]["viewport"]
                or info["pool"] != pool_record
                or _read(directory / f"{ident}-pool-{index}.json") != pool_record
            ):
                raise ValueError("Candidate frozen pool differs from original complete alternatives")
            if len(pool.candidates) < 2:
                if info["ranking_status"] != "not_applicable_duplicates":
                    raise ValueError("Duplicate-only candidate pool incorrectly selected")
                continue
            if config["image_edge"]:
                record = next(r for r in frozen["records"] if r["id"] == ident)
                url, metadata = runner._rerender(record, first, crops[0], config["image_edge"])
                from bench.p003_selector_image import transform
                from bench.p003_selector_visibility import transform as visibility_transform

                url, metadata = visibility_transform(url, metadata, config.get("image_visibility", "source"))
                url, metadata = transform(url, metadata, config.get("image_mode", "rgb"))
            else:
                url, metadata = (
                    urls[0],
                    {"image_edge": 0, "source_pixels_supplied": False, "original_crop_sha256": image_hashes[0]},
                )
            if info["selector_image"] != metadata:
                raise ValueError("Selector image differs from independently rendered declared crop")
            mode = config.get("evidence_mode", "whole")
            if mode == "differences":
                from bench import p003_candidate_diff as differences

                projection = differences.comparison(pool, max_bytes=config.get("evidence_max_bytes", 4096))
                if _read(directory / f"{ident}-selector-{index}-evidence.json") != projection:
                    raise ValueError("Candidate difference projection differs from complete frozen pool")
                expected_evidence = {
                    "mode": "differences",
                    "max_bytes": config.get("evidence_max_bytes", 4096),
                    "bytes": len(chooser.canonical_json(projection)),
                    "sha256": sha(chooser.canonical_json(projection)),
                    "differing_slots": len(projection["differing_slots"]),
                }
                if info.get("evidence") != expected_evidence:
                    raise ValueError("Candidate difference evidence metadata changed")
            body = runner._body(
                pool,
                config["model"],
                url,
                config["image_edge"],
                evidence_mode=mode,
                evidence_max_bytes=config.get("evidence_max_bytes", 4096),
            )
            retained_body = _read(directory / f"{ident}-selector-{index}-request.json")
            response = _read(directory / f"{ident}-selector-{index}-response.json")
            calls = [c for c in prediction["ranking_calls"] if c["crop_index"] == index]
            if (
                retained_body != body
                or len(calls) != 1
                or calls[0]["entry"] != response["entry"]
                or calls[0].get("replayed")
                or response.get("replayed")
                or calls[0]["usage"] != response["result"].get("usage", {})
            ):
                raise ValueError("Candidate selector request or fresh response provenance changed")
            entry = response["entry"]
            if entry.get("request_sha256") is not None and entry["request_sha256"] != sha(
                json.dumps(body, separators=(",", ":")).encode()
            ):
                raise ValueError("Candidate selector ledger request hash differs")
            if entry.get("requested_model") is not None and entry["requested_model"] != config["model"]:
                raise ValueError("Candidate selector ledger model differs")
            if entry.get("tag") != f"P003/{config['run_id']}/{ident}/{index}":
                raise ValueError("Candidate selector call belongs to another run or crop")
            used_calls.add(index)
            selected, audit = chooser.select(pool, chooser.parse(pool, response["result"]))
            if canonical(info["audit"]) != canonical(audit):
                raise ValueError("Candidate selection audit differs from raw probabilities")
            if selected is None:
                if info["ranking_status"] != "unresolved_retained_first":
                    raise ValueError("Candidate abstention does not retain first baseline")
            else:
                origin = audit["original_input_indexes"][0]
                if (
                    info["ranking_status"] != "selected"
                    or info["selected_baseline_index"] != origin
                    or info["selected_sha256"] != sha(selected)
                ):
                    raise ValueError("Candidate selected origin or exact bytes changed")
                staged[index] = {
                    **deepcopy(crops[origin]),
                    "selection_origin_baseline": origin,
                    "selection_audit": audit,
                }
        if len(used_calls) != len(prediction["ranking_calls"]) or bool(used_calls) != (status == "completed"):
            raise ValueError("Candidate ranking call inventory differs from eligible pools")
        state = regions.compose(staged, first["viewport"])
        if (
            prediction["transcription_regions"] != staged
            or prediction["tables"] != state["tables"]
            or _read(directory / f"{ident}-structure.json") != state
            or guard_path(directory / f"{ident}.md").read_bytes() != transcription.markdown(state).encode()
        ):
            raise ValueError("Candidate complete output differs from strict selected-response recomposition")
        verified[ident] = {"operational": True, "conserved": False}
    return {
        "candidate_baselines": [
            {
                "name": name,
                "report_sha256": inventory["file_sha256"]["report.json"],
                "costs": costs(baseline),
                "resources": baseline.get("metrics", {}),
            }
            for name, inventory, baseline in zip(names, inventories, baseline_reports, strict=True)
        ],
        "ranking_status_counts": dict(statuses),
        "scope": "Historical candidate generation is separate; only retained-candidate ranking is newly measured",
    }, verified


def _detector_request_order(detection: dict[str, Any]) -> dict[str, Any]:
    """Restore the authenticated detector's literal nested prompt key order."""
    detection = deepcopy(detection)
    keys = ("label", "confidence", "pixel_bbox", "normalized_bbox", "bbox")
    if any(set(box) != set(keys) for box in detection["boxes"]):
        raise ValueError("Unsupported detector box inventory for literal gate replay")
    detection["boxes"] = [{key: box[key] for key in keys} for box in detection["boxes"]]
    return detection


def verify_regions_output(
    directory: Path, prediction: dict[str, Any], frozen: dict[str, Any], record: dict[str, Any]
) -> dict[str, Any]:
    """Replay source proposals, actual gate evidence and strict atomic crop outputs."""
    import io

    from PIL import Image

    import pylopdf
    from bench import generalization_vision_regions as crops
    from bench import p003_region_candidates as candidates
    from bench import p003_regions_run as processor
    from bench import pipeline_vision_transcription as transcription
    from bench.generalization_report import verify_output

    ident, config = prediction["id"], frozen["config"]
    if Path(ident).name != ident or ident in {".", ".."}:
        raise ValueError("Unsafe page ID")
    if _read(directory / f"{ident}-result.json") != prediction:
        raise ValueError("Per-page result differs from complete report")
    if prediction.get("status") != "ok":
        if prediction.get("tables"):
            raise ValueError("Failed region page exposes partial tables")
        return {"operational": False, "conserved": False}
    for name in (
        "p003_regions_run.py",
        "p003_region_candidates.py",
        "generalization_vision_regions.py",
        "pipeline_vision_transcription.py",
    ):
        if frozen["code_sha256"].get(name) != sha((Path(__file__).parent / name).read_bytes()):
            raise ValueError("Unsupported frozen region replay helper version")
    expected_labels = {
        "route": "p003_decision_regions",
        "processor": "p003_regions",
        "source_conserved": False,
        "text_provenance": transcription.PROVENANCE,
        "output_scope": "table_only",
        "output_atomic": True,
        "coverage": "unverified",
        "unresolved_ids": [],
    }
    if any(prediction.get(key) != value for key, value in expected_labels.items()):
        raise ValueError("Region output mislabels source ownership, coverage or transcription scope")
    child = prediction["native_child"]
    if child.get("status") != "ok" or child.get("calls"):
        raise ValueError("Native source child must complete without hosted calls")
    verify_output(directory / "native", child, processor="regions", source_order=config.get("source_order", "legacy"))
    source = {key: child["source"][key] for key in ("page_size", "words")}
    if prediction["source"] != source:
        raise ValueError("Proposal source differs from verified native child")
    settings = processor._configuration(config)
    if prediction["settings"] != settings or prediction["proposal_arm"] != settings["arm"]:
        raise ValueError("Retained proposal settings differ from frozen treatment")
    data = guard_path(Path(record["pdf_path"])).read_bytes()
    if sha(data) != record["pdf_sha256"]:
        raise ValueError("Frozen proposal PDF changed")
    with pylopdf.open(stream=data) as document:
        page = document[record["page_number"]]
        viewport = list(page.rect)
        if prediction["viewport"] != viewport or prediction["original_rotation"] != page.rotation:
            raise ValueError("Proposal display geometry or page rotation changed")
        pixels = page.render(
            scale=processor.PROPOSAL_EDGE / max(page.rect.width, page.rect.height), background=(255, 255, 255)
        )
        with Image.open(io.BytesIO(pixels)) as rendered:
            image = rendered.convert("RGB")
        expected_image = {
            "edge": processor.PROPOSAL_EDGE,
            "size": list(image.size),
            "sha256": sha(pixels),
            "viewport": viewport,
        }
        if prediction["proposal_image"] != expected_image:
            raise ValueError("Proposal image differs from independently rendered frozen PDF")
        if settings["arm"] in ("yolo", "yolo_fixed2"):
            # The detector constructs these keys in this order before adding
            # display geometry. Archived JSON sorts keys, while the nested box
            # is serialized literally inside the gate's source prompt.
            detection = _detector_request_order(prediction["layout_detection"])
            plan = processor._yolo(detection, viewport, source)
            if settings["arm"] == "yolo_fixed2":
                fixed2 = candidates.propose(
                    source, image=image, max_candidates=settings["candidate_cap"], raster_grid=2
                )
                plan = candidates.union_plans(plan, fixed2, source, max_candidates=settings["candidate_cap"])
        else:
            plan = candidates.propose(
                source,
                image=image,
                max_candidates=settings["candidate_cap"],
                raster_grid=2 if settings["arm"] == "tracks_fixed2" else 0,
            )
        if (
            canonical(plan) != canonical(prediction["proposal_plan"])
            or _read(directory / f"{ident}-proposals.json") != prediction["proposal_plan"]
        ):
            raise ValueError("Proposal inventory differs from complete source-only replay")
        if prediction["proposal_count"] != len(plan["candidates"]) or len(prediction["gate_regions"]) != len(
            plan["candidates"]
        ):
            raise ValueError("Gate inventory omits or adds a source proposal")
        consumed_calls = set()
        for proposal, gate in zip(plan["candidates"], prediction["gate_regions"], strict=True):
            if any(gate.get(key) != value for key, value in proposal.items()) or gate["page_viewport"] != viewport:
                raise ValueError("Gate changed its source-only proposal evidence")
            if not settings["gate_enabled"]:
                if gate["gate_status"] != "bypassed_ordinary_yolo" or gate["gate_answer"] != {"choice": "table"}:
                    raise ValueError("Ungated YOLO control contains a semantic gate outcome")
                continue
            url = None
            if settings["gate_image"]:
                url, metadata = crops._crop(image, viewport, proposal["bbox"], processor.GATE_EDGE, 90)
                if gate["gate_image"] != metadata:
                    raise ValueError("Gate crop pixels or display extent changed")
            body = processor.gate_request(config["model"], proposal, url)
            path = directory / f"{ident}-gate-request-{proposal['id']}.json"
            if _read(path) != body:
                raise ValueError("Gate request differs from reconstructed source/image evidence")
            metadata = {
                "model": body["model"],
                "body_sha256": sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()),
                "image_supplied": url is not None,
            }
            response = _read(directory / f"{ident}-gate-response-{proposal['id']}.json")
            if (
                gate["gate_request"] != metadata
                or gate["gate_status"] != "ok"
                or response["answer"] != gate["gate_answer"]
            ):
                raise ValueError("Gate response/provenance differs from accepted choice")
            indexes = gate["gate_call_indexes"]
            if len(indexes) != 1 or indexes[0] in consumed_calls:
                raise ValueError("Gate calls are duplicate or incomplete")
            call = prediction["calls"][indexes[0]]
            if call != {
                **response,
                "kind": "region_gate",
                "status": "ok",
                "proposal_id": proposal["id"],
            } or response.get("replayed"):
                raise ValueError("Gate call differs from retained fresh response")
            consumed_calls.update(indexes)
        selection = processor.select_nonoverlapping(
            prediction["gate_regions"], policy=config.get("conflict_policy", processor.CONFLICT_POLICY)
        )
        if prediction["conflict_selection"] != selection or prediction["selected_region_count"] != len(
            selection["selected_ids"]
        ):
            raise ValueError("Accepted gate probabilities or overlap selection changed")
        selected = {p["id"]: p for p in prediction["gate_regions"]}
        regions = prediction["transcription_regions"]
        if len(regions) != len(selection["selected_ids"]):
            raise ValueError("Transcription omits an accepted crop or adds a rejected proposal")
        if regions:
            pixels = page.render(
                scale=(processor.RENDER_EDGE - 1) / max(page.rect.width, page.rect.height), background=(255, 255, 255)
            )
            with Image.open(io.BytesIO(pixels)) as rendered:
                image = rendered.convert("RGB")
            if prediction["transcription_image"] != {
                "edge_cap": processor.RENDER_EDGE,
                "size": list(image.size),
                "sha256": sha(pixels),
            }:
                raise ValueError("Transcription raster differs from frozen PDF render")
        for index, (proposal_id, region) in enumerate(zip(selection["selected_ids"], regions, strict=True)):
            if (
                region["status"] != "ok"
                or region["index"] != index
                or region["request_index"] != index
                or region["proposal_id"] != proposal_id
                or region["viewport"] != selected[proposal_id]["bbox"]
            ):
                raise ValueError("Selected crop inventory changed")
            url, metadata = crops._crop(image, viewport, region["viewport"], processor.TRANSCRIPTION_EDGE, 90)
            if region["image"] != metadata:
                raise ValueError("Transcription crop pixels changed")
            body = transcription.request(
                config.get("generation_model", "anthropic/claude-haiku-5.5"),
                url,
                region["viewport"],
                max_tokens=config.get("generation_tokens", 16384),
            )
            if config.get("generation_provider"):
                body["provider"] = {
                    "only": [config["generation_provider"]],
                    "allow_fallbacks": False,
                    "require_parameters": True,
                }
            if _read(directory / f"{ident}-request-{index}.json") != body:
                raise ValueError("Transcription request differs from selected image evidence")
            encoded = json.dumps(body, separators=(",", ":")).encode()
            request_metadata = {
                "body_sha256": sha(encoded),
                "body_bytes": len(encoded),
                "max_body_bytes": 750000,
                "model": body["model"],
                "max_tokens": body["max_tokens"],
                "replay": False,
            }
            if region["request"] != request_metadata:
                raise ValueError("Transcription request hash/admission metadata changed")
            indexes = region["call_indexes"]
            if len(indexes) != 1 or indexes[0] in consumed_calls:
                raise ValueError("Crop call inventory is duplicate or incomplete")
            if prediction["calls"][indexes[0]].get("kind") != "vision_transcription" or prediction["calls"][
                indexes[0]
            ].get("replayed"):
                raise ValueError("Crop response is not a fresh transcription call")
            consumed_calls.update(indexes)
            if _read(directory / f"{ident}-response-{index}.json") != region["transcription_response"]:
                raise ValueError("Raw transcription response differs from retained crop response")
            parsed = transcription.parse(region["transcription_response"], region["viewport"])
            if parsed["tables"] != region["tables"]:
                raise ValueError("Crop tables differ from strict raw response parsing")
        if consumed_calls != set(range(len(prediction["calls"]))):
            raise ValueError("Successful region page contains unattributed calls")
    state = crops.compose(regions, viewport)
    if _read(directory / f"{ident}-structure.json") != state or state["tables"] != prediction["tables"]:
        raise ValueError("Whole-page table output differs from complete crop composition")
    if guard_path(directory / f"{ident}.md").read_bytes() != transcription.markdown(state).encode():
        raise ValueError("Table-only Markdown differs from trusted exact rendering")
    return {"operational": True, "conserved": False}


def score_run(
    directory: Path,
    corpus: Path,
    *,
    manifest_path: Path | None = None,
    cohort: str | None = None,
    trusted_code: dict[str, str] | None = None,
    baseline_trusted_code: dict[str, str] | None = None,
    candidate_trusted_code: dict[str, dict[str, str]] | None = None,
    incremental_trusted_code: dict[str, dict[str, str]] | None = None,
    reviewed_parser_sha256: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Validate existing runner artifacts without calling inference or executing archives."""
    # The existing offline verifier reconstructs source ownership and Markdown.
    from bench.generalization_report import _bounds, load_corpus, verify_output

    directory = guard_path(directory)
    manifest, targets = load_corpus(corpus)
    manifest_path = manifest_path or corpus / "manifest.json"
    selected_manifest = _read(manifest_path)
    if selected_manifest.get("split") != "DEV" or selected_manifest.get("dataset_sha256") != manifest["dataset_sha256"]:
        raise ValueError("Selected source manifest must identify the same explicit DEV corpus")
    records = [r for r in manifest["pages"] if cohort is None or r.get("cohort") == cohort]
    report = _read(directory / "report.json")
    frozen = _read(directory / "frozen.json")
    if report["config"] != frozen["config"] or frozen["manifest_sha256"] != sha(guard_path(manifest_path).read_bytes()):
        raise ValueError("Frozen configuration or selected manifest changed")
    if cohort is None and report["config"].get("pilot"):
        records = [r for r in records if r["pilot"]]
    expected = [{k: r[k] for k in SOURCE_FIELDS} for r in records]
    frozen_records = frozen["records"]
    if len(frozen_records) != len(expected) or {r["id"]: r for r in frozen_records} != {r["id"]: r for r in expected}:
        raise ValueError("Frozen inventory differs from complete predeclared cohort")
    selected_rows = selected_manifest["pages"]
    selected_by_id = {r["id"]: {k: r[k] for k in SOURCE_FIELDS} for r in selected_rows}
    if len(selected_by_id) != len(selected_rows) or any(selected_by_id.get(r["id"]) != r for r in expected):
        raise ValueError("Selected source manifest does not contain intended corpus inputs")
    code = verify_archive(directory, frozen, trusted_code)
    verify_treatment_helpers(frozen)
    predictions = report["results"]
    ids = [p["id"] for p in predictions]
    intended = {r["id"] for r in expected}
    if len(ids) != len(set(ids)) or not set(ids) <= intended:
        raise ValueError("Duplicate or unknown result page ID")
    processor = report["config"].get("processor", "whole")
    required = {"pipeline_run.py", "pipeline_assembly.py"}
    if processor == "regions":
        required |= {"generalization_run.py", "pipeline_regions.py"}
    elif processor == "hybrid":
        required |= {"generalization_hybrid_run.py", "pipeline_hybrid_composition.py"}
    elif processor in {"vision", "vision_regions", "vision_multiscale"}:
        required = {"generalization_vision_run.py", "pipeline_vision_transcription.py"}
    elif processor == "p003_regions":
        required |= {
            "p003_regions_run.py",
            "p003_region_candidates.py",
            "pipeline_vision_transcription.py",
            "generalization_vision_regions.py",
        }
    elif processor == "p003_candidate_choice":
        required = {
            "p003_candidate_run.py",
            "p003_candidate_choice.py",
            "pipeline_vision_transcription.py",
            "generalization_vision_regions.py",
        }
    elif processor == "p003_boundary_repair":
        required |= {
            "p003_boundary_run.py",
            "decision_p003_boundaries.py",
            "decision_p003_native.py",
            "pipeline_regions.py",
        }
    elif processor == "p003_topology_source":
        required |= {"p003_topology_run.py", "p003_topology_ownership.py", "pipeline_regions.py"}
    elif processor == "p003_gate":
        required |= {"p003_gate_run.py", "p003_gate_image.py", "p003_gate_packet.py", "pipeline_regions.py"}
    elif processor != "whole":
        raise ValueError("Unsupported frozen processor")
    if not required <= code.keys():
        raise ValueError("Frozen code lacks required processor dependencies")
    incremental = processor in {"p003_boundary_repair", "p003_candidate_choice", "p003_topology_source", "p003_gate"}
    if processor == "p003_gate":
        from bench.p003_gate_verification import verify_gate

        baseline_provenance, repair_verified = verify_gate(directory, report, frozen, incremental_trusted_code)
    elif processor == "p003_topology_source":
        from bench.p003_incremental_verification import verify_topology

        baseline_provenance, repair_verified = verify_topology(
            directory, report, frozen, incremental_trusted_code, reviewed_parser_sha256=reviewed_parser_sha256
        )
    elif processor == "p003_candidate_choice":
        baseline_provenance, repair_verified = verify_candidate_run(
            directory, report, frozen, candidate_trusted_code, reviewed_parser_sha256=reviewed_parser_sha256
        )
    elif incremental:
        baseline_provenance, repair_verified = verify_incremental_run(directory, report, frozen, baseline_trusted_code)
    else:
        baseline_provenance, repair_verified = None, {}
    incremental_key = {
        "p003_candidate_choice": "incremental_ranking",
        "p003_topology_source": "incremental_ownership",
        "p003_gate": "incremental_gate",
    }.get(processor, "incremental_repair")
    artifacts = []
    operational = 0
    for prediction in predictions:
        if processor == "p003_regions":
            verified = verify_regions_output(
                directory, prediction, frozen, next(r for r in records if r["id"] == prediction["id"])
            )
        else:
            verified = (
                repair_verified[prediction["id"]]
                if incremental
                else verify_output(directory, prediction, processor=processor)
            )
        operational += int(verified["operational"])
        record = {
            "id": prediction["id"],
            "result_sha256": sha((directory / f"{prediction['id']}-result.json").read_bytes()),
            "tables_sha256": sha(canonical(prediction.get("tables", []))),
            "source_sha256": sha(canonical(prediction["source"])) if prediction.get("source") is not None else None,
            "operational": verified["operational"],
            "detector_evidence_sha256": sha(
                canonical(
                    {
                        key: {
                            k: v
                            for k, v in prediction[key].items()
                            if k not in {"metrics", "parent_cpu_seconds", "parent_wall_seconds"}
                        }
                        for key in (
                            "layout_detector",
                            "layout_detection",
                            "raw_layout_detection",
                            "filtered_layout_detection",
                        )
                        if isinstance(prediction.get(key), dict)
                    }
                )
            ),
        }
        if verified["operational"]:
            record["markdown_sha256"] = sha(guard_path(directory / f"{prediction['id']}.md").read_bytes())
        artifacts.append(record)
    if report.get("complete_output_pages", operational) != operational:
        raise ValueError("Report complete output count differs from independently verified count")
    scoring_predictions = deepcopy(predictions)
    for prediction in scoring_predictions:
        if prediction.get("status") == "ok" and prediction.get("source") is not None:
            _bounds(prediction["source"], {"tables": [t for t in prediction["tables"] if "bbox" not in t]})
    reference_pages = [p for p in targets["pages"] if p["id"] in intended]
    scoring = strict_scores(reference_pages, scoring_predictions)
    audits = []
    request_images = []
    request_paths = set(directory.glob("**/*-request-*.json")) | set(directory.glob("**/*-request.json"))
    for request in sorted(request_paths):
        body = _read(request)
        audit = audit_model_body(body)
        stack = [body]
        image_hashes = []
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, str) and node.startswith("data:image/"):
                image_hashes.append(sha(node.encode()))
        request_images.append(
            {
                "path": str(request.relative_to(directory)),
                "model": body.get("model"),
                "data_url_sha256": sorted(image_hashes),
            }
        )
        if not audit["explicit_reference_fields_absent"]:
            raise ValueError("Private-reference field in retained request")
        audits.append({"path": str(request.relative_to(directory)), "sha256": sha(request.read_bytes()), **audit})
    accounting = costs(report[incremental_key] if incremental else report)
    attempt_report = report[incremental_key] if incremental else report
    attempt_entries = attempt_report.get("entries", [])
    metrics = dict(report.get("metrics", {}))
    if report.get("layout_detector_initialization") is not None:
        metrics["layout_detector_worker"] = {
            "initialization": report["layout_detector_initialization"],
            "requests": [
                {"id": p["id"], "metrics": p[key]["metrics"]}
                for p in predictions
                for key in ("layout_detector", "layout_detection")
                if isinstance(p.get(key), dict) and "metrics" in p[key]
            ],
            "scope": "Separate CPU worker subprocess; parent process CPU/RSS excludes worker. "
            "Do not sum RSS peaks or overlapping parent per-page CPU intervals.",
        }
    source_fingerprint = sha(
        canonical(sorted([{k: a[k] for k in ("id", "source_sha256")} for a in artifacts], key=lambda a: a["id"]))
    )
    errors = Counter(
        p.get("error_category", p.get("error", "unclassified")) for p in predictions if p.get("status") != "ok"
    )
    if len(predictions) < len(expected):
        errors["missing"] += len(expected) - len(predictions)
    return {
        "name": directory.name,
        "evaluation_scope": (
            "incremental ranking on retained candidates"
            if processor == "p003_candidate_choice"
            else "incremental ownership conditional on frozen topology and source"
            if processor == "p003_topology_source"
            else "incremental admission conditional on frozen generation"
            if processor == "p003_gate"
            else "incremental repair on retained artifacts"
        )
        if incremental
        else "complete pipeline",
        "baseline_provenance": baseline_provenance,
        "dataset_sha256": manifest["dataset_sha256"],
        "manifest_sha256": frozen["manifest_sha256"],
        "report_sha256": sha((directory / "report.json").read_bytes()),
        "cohort": cohort,
        "config": report["config"],
        "frozen_runtime": {k: frozen.get(k) for k in ("runtime", "python", "platform", "logical_cpus", "concurrency")},
        "intended_pages": len(expected),
        "operational_pages": operational,
        "errors": len(expected) - operational,
        "failure_categories": dict(errors),
        "attempt_transport_failures": {
            "counts": transport_failures([{"calls": [{"entry": entry} for entry in attempt_entries]}]),
            "retained_attempt_entries": len(attempt_entries),
            "declared_attempts": attempt_report.get("ledger_attempts"),
            "complete_attempt_inventory": len(attempt_entries) == attempt_report.get("ledger_attempts"),
            "scope": "Explicit archived run-attributed attempts, including failures without returned responses",
        },
        "returned_call_transport_failures": transport_failures(
            predictions,
            call_keys=("ranking_calls",)
            if processor == "p003_candidate_choice"
            else ("topology_calls",)
            if processor == "p003_topology_source"
            else ("calls",)
            if processor == "p003_gate"
            else ("repair_calls",)
            if incremental
            else ("calls",),
        ),
        "scores": scoring["totals"],
        "page_scores": scoring["pages"],
        "positive_macro": scoring["positive_macro"],
        "exact_positive_pages": sum(
            p.get("exact_page", False) and p.get("positive_page", False) for p in scoring["pages"]
        ),
        "costs": accounting,
        "resources": metrics,
        "code_sha256": code,
        "artifacts": artifacts,
        "request_audits": audits,
        "request_image_inventory": request_images,
        "source_fingerprint": source_fingerprint,
        "source_inventory_pages": sum(a["source_sha256"] is not None for a in artifacts),
        "detector_evidence_fingerprint": sha(
            canonical(
                sorted(
                    [{k: a[k] for k in ("id", "detector_evidence_sha256")} for a in artifacts], key=lambda a: a["id"]
                )
            )
        ),
        "pages_per_minute": None if incremental else _rate(operational, metrics.get("wall_seconds"), 60),
        "intended_pages_per_minute": None if incremental else _rate(len(expected), metrics.get("wall_seconds"), 60),
        "pages_per_api_usd": None if incremental else _rate(operational, accounting["effective_api_usd"]),
        "incremental_attempted_pages_per_minute": _rate(
            sum(p.get("incremental_repair", {}).get("attempted", False) for p in predictions),
            metrics.get("wall_seconds"),
            60,
        )
        if processor == "p003_boundary_repair"
        else None,
        "incremental_attempted_pages_per_api_usd": _rate(
            sum(p.get("incremental_repair", {}).get("attempted", False) for p in predictions),
            accounting["effective_api_usd"],
        )
        if processor == "p003_boundary_repair"
        else None,
        "incremental_ranking_pages_processed_per_minute": _rate(len(predictions), metrics.get("wall_seconds"), 60)
        if processor == "p003_candidate_choice"
        else None,
        "incremental_ranking_pages_processed_per_api_usd": _rate(len(predictions), accounting["effective_api_usd"])
        if processor == "p003_candidate_choice"
        else None,
        "exact_positive_pages_per_minute": None
        if incremental
        else _rate(
            sum(p.get("exact_page", False) and p.get("positive_page", False) for p in scoring["pages"]),
            metrics.get("wall_seconds"),
            60,
        ),
    }


def paired_comparison(left: dict[str, Any], right: dict[str, Any], *, samples: int = 2000) -> dict[str, Any]:
    """Paired page bootstrap diagnostic; repeated calls require separate repeat rows."""
    for key in ("dataset_sha256", "manifest_sha256", "cohort", "source_fingerprint", "detector_evidence_fingerprint"):
        if left[key] != right[key]:
            raise ValueError(f"Unmatched paired evaluation: {key}")
    if (
        left["source_inventory_pages"] != left["intended_pages"]
        or right["source_inventory_pages"] != right["intended_pages"]
    ):
        raise ValueError("Source-matched decision comparison requires complete retained sources")
    a, b = {p["id"]: p for p in left["page_scores"]}, {p["id"]: p for p in right["page_scores"]}
    if set(a) != set(b):
        raise ValueError("Paired evaluation requires identical page IDs")
    deltas = [b[k]["strict_exact_cells"] - a[k]["strict_exact_cells"] for k in sorted(a)]
    if not deltas or samples < 1:
        raise ValueError("Bootstrap requires pages and positive sample count")
    rng = random.Random(3003)
    totals = sorted(sum(rng.choices(deltas, k=len(deltas))) for _ in range(samples))
    left_config, right_config = treatment_config(left.get("config", {})), treatment_config(right.get("config", {}))
    changes = {
        key: [left_config.get(key), right_config.get(key)]
        for key in left_config.keys() | right_config.keys()
        if left_config.get(key) != right_config.get(key)
    }

    def image_inventory(run: dict[str, Any]) -> list[str]:
        return sorted(
            {digest for record in run.get("request_image_inventory", []) for digest in record["data_url_sha256"]}
        )

    return {
        "left": left["name"],
        "treatment_changes": changes,
        "gate_image_configuration_equal": left_config["gate_image"] == right_config["gate_image"],
        "request_image_hash_sets_equal": image_inventory(left) == image_inventory(right),
        "image_scope": "Serialized data-URL assets across actual requests; routing changes may change request "
        "inventory. Source/detector equality alone does not prove gate pixel equality.",
        "right": right["name"],
        "strict_exact_cell_delta": sum(deltas),
        "paired_page_bootstrap_95_interval": [
            totals[int(samples * 0.025)],
            totals[min(samples - 1, int(samples * 0.975))],
        ],
        "seed": 3003,
        "samples": samples,
        "scope": "DEV page sampling diagnostic, not independent hosted-repeat uncertainty or heldout inference",
        "page_deltas": [
            {
                "id": key,
                "strict_exact_cells": b[key]["strict_exact_cells"] - a[key]["strict_exact_cells"],
                "complete_tables": b[key].get("complete_tables", 0) - a[key].get("complete_tables", 0),
            }
            for key in sorted(a)
        ],
    }


def treatment_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize documented defaults and remove only declared run administration."""
    normalized = {key: value for key, value in config.items() if key not in {"run_id", "repeat_index", "order_seed"}}
    normalized.setdefault("gate_image", True)
    normalized.setdefault("source_order", "legacy")
    return normalized


def repeat_summary(runs: list[dict[str, Any]], *, reviewed_code_changes: bool = False) -> dict[str, Any]:
    """Keep fresh-repeat variation visible without treating pages as hosted repeats."""
    if not runs:
        raise ValueError("Repeat summary requires runs")
    fields = (
        "dataset_sha256",
        "manifest_sha256",
        "cohort",
        "source_fingerprint",
        "detector_evidence_fingerprint",
    )
    for run in runs[1:]:
        if any(run[key] != runs[0][key] for key in fields) or treatment_config(run["config"]) != treatment_config(
            runs[0]["config"]
        ):
            raise ValueError("Repeat summary requires identical treatment, inputs and retained evidence")
    code_identical = len({sha(canonical(run.get("code_sha256", {}))) for run in runs}) == 1
    if not code_identical and not reviewed_code_changes:
        raise ValueError(
            "Repeat code snapshots differ; independent authentication plus operator semantic review required"
        )
    metrics = {}
    for key in ("strict_exact_cells", "complete_tables", "false_positive_page", "all_page_errors"):
        values = [r["scores"].get(key, 0) for r in runs]
        metrics[key] = {
            "observations": values,
            "minimum": min(values),
            "median": statistics.median(values),
            "maximum": max(values),
            "sample_standard_deviation": statistics.stdev(values) if len(values) > 1 else None,
        }
    return {
        "runs": [r["name"] for r in runs],
        "repeat_count": len(runs),
        "administrative_fields": [
            {"name": run["name"], **{key: run["config"].get(key) for key in ("run_id", "repeat_index", "order_seed")}}
            for run in runs
        ],
        "code_snapshots_identical": code_identical,
        "operator_reviewed_code_changes": reviewed_code_changes,
        "code_semantics_scope": "Every snapshot independently authenticated; digest variation is visible and "
        "requires operator review before attributing variation only to fresh model responses",
        "metrics": metrics,
        "scope": "Fresh complete run repetitions of one fixed treatment; no best-repeat selection. "
        "Small repeat count does not establish calibrated confidence.",
    }


def markdown_report(runs: list[dict[str, Any]]) -> str:
    """Render every run independently with complete cost and resource scope."""
    lines = [
        "# P003 frozen DEV evaluation",
        "",
        (
            "All intended pages and errors remain in quality denominators. Pages/min and pages/API USD use "
            "independently verified output pages. API-zero or incomplete costs have undefined pages/API USD. "
            "Strict cells require exact text and anchor span; the P002 text-cell metric ignores spans."
        ),
        "",
        (
            "| Run | Outputs / intended | Errors | Complete tables / expected | Strict cells / expected "
            "| P002 text cells "
            "| Negative FP pages / negatives | Extra tables | Pages/min | Pages/API USD | Effective API USD |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def fmt(value: object) -> str:
        return "unmeasured" if value is None else f"{value:.6g}" if isinstance(value, float) else str(value)

    for run in runs:
        s = run["scores"]
        row = [
            run["name"],
            f"{run['operational_pages']}/{run['intended_pages']}",
            run["errors"],
            f"{s.get('complete_tables', 0)}/{s.get('expected_tables', 0)}",
            f"{s['strict_exact_cells']}/{s.get('expected_cells', 0)}",
            s.get("correct_text_cells", 0),
            f"{s.get('false_positive_page', 0)}/{s.get('negative_page', 0)}",
            s.get("false_positive_tables", 0),
            run["pages_per_minute"],
            run["pages_per_api_usd"],
            run["costs"]["effective_api_usd"],
        ]
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    for run in runs:
        lines += [
            "",
            f"## {run['name']}",
            "",
            (
                f"Evaluation scope: {run.get('evaluation_scope', 'complete pipeline')}.\n\n"
                f"Dataset `{run['dataset_sha256']}`; manifest `{run['manifest_sha256']}`; "
                f"report `{run['report_sha256']}`."
            ),
            "",
            "Positive-page macro recall: `" + json.dumps(run["positive_macro"], sort_keys=True) + "`.",
            "",
            "Failure categories: `" + json.dumps(run["failure_categories"], sort_keys=True) + "`.",
            "",
            "Resources (run interval; local preprocessing remains distinct from API inference): `"
            + json.dumps(run["resources"], sort_keys=True)
            + "`.",
            "",
            "All-attempt API accounting: `" + json.dumps(run["costs"], sort_keys=True) + "`.",
        ]
    for run in runs:
        if run.get("cost_reconciliation") is not None:
            lines += [
                "",
                "Verified immutable accounting overlay: `"
                + json.dumps(run["cost_reconciliation"], sort_keys=True)
                + "`.",
                "",
                "Reconciled pages/APIUSD: " + fmt(run.get("reconciled_pages_per_api_usd")) + ".",
            ]
        if run.get("baseline_provenance") is not None:
            lines += [
                "",
                "Historical baseline provenance: `" + json.dumps(run["baseline_provenance"], sort_keys=True) + "`.",
                "",
                "Incremental processing rates (repair attempts or ranking pages processed; "
                "historical generation is separate): `"
                + json.dumps(
                    {
                        key: run.get(key)
                        for key in (
                            "incremental_attempted_pages_per_minute",
                            "incremental_attempted_pages_per_api_usd",
                            "incremental_ranking_pages_processed_per_minute",
                            "incremental_ranking_pages_processed_per_api_usd",
                        )
                    },
                    sort_keys=True,
                )
                + "`.",
            ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Score existing frozen runs using private references only offline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--cohort")
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument(
        "--trusted-code",
        type=Path,
        action="append",
        help="Authenticated digest snapshot; repeat once per --run when source versions differ",
    )
    parser.add_argument(
        "--baseline-trusted-code",
        type=Path,
        action="append",
        help="Authenticated historical baseline snapshot; one shared or one per --run",
    )
    parser.add_argument(
        "--cost-reconciliation", type=Path, action="append", help="Immutable cost overlay; exactly one per --run"
    )
    parser.add_argument(
        "--candidate-trusted-code",
        type=Path,
        action="append",
        help="Independent baseline-N digest maps; one shared or one per --run",
    )
    parser.add_argument(
        "--incremental-trusted-code",
        type=Path,
        action="append",
        help="Independent copied-name baseline digest maps for gate/topology; one shared or one per --run",
    )
    parser.add_argument(
        "--reviewed-parser-sha256",
        action="append",
        default=[],
        help="Explicit root-reviewed historical candidate parser digest; archive trust still required",
    )
    parser.add_argument("--cost-ledger", type=Path, help="Explicit shared ledger JSON for cost overlay verification")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument(
        "--reviewed-repeat-code-changes",
        action="store_true",
        help="Attest operator review of authenticated source changes for repeat comparability",
    )
    parser.add_argument("--repeat-summary", action="store_true", help="Summarize identical treatment repetitions")
    parser.add_argument("--paired", action="store_true", help="Compare exactly two source-matched decision runs")
    args = parser.parse_args()

    def snapshots(paths: list[Path] | None) -> list[dict[str, str] | None]:
        if not paths:
            return [None] * len(args.run)
        if len(paths) not in {1, len(args.run)}:
            parser.error("Trusted code options require one shared snapshot or exactly one snapshot per --run")
        values = [_read(path) for path in paths]
        return values * len(args.run) if len(values) == 1 else values

    trusted = snapshots(args.trusted_code)
    baseline_trusted = snapshots(args.baseline_trusted_code)
    candidate_trusted = snapshots(args.candidate_trusted_code)
    incremental_trusted = snapshots(args.incremental_trusted_code)
    runs = [
        score_run(
            p,
            args.corpus,
            manifest_path=args.manifest,
            cohort=args.cohort,
            trusted_code=code,
            baseline_trusted_code=baseline_code,
            candidate_trusted_code=candidate_code,
            incremental_trusted_code=incremental_code,
            reviewed_parser_sha256=tuple(args.reviewed_parser_sha256),
        )
        for p, code, baseline_code, candidate_code, incremental_code in zip(
            args.run, trusted, baseline_trusted, candidate_trusted, incremental_trusted, strict=True
        )
    ]
    if args.cost_reconciliation:
        if args.cost_ledger is None or len(args.cost_reconciliation) != len(args.run):
            parser.error("Cost reconciliation requires an explicit ledger and exactly one sidecar per --run")
        for run, directory, sidecar in zip(runs, args.run, args.cost_reconciliation, strict=True):
            overlay = verify_cost_reconciliation(directory, sidecar, args.cost_ledger)
            run["cost_reconciliation"] = overlay
            run["reconciled_pages_per_api_usd"] = (
                _rate(run["operational_pages"], overlay["reconciled"]["effective_api_usd"])
                if run["evaluation_scope"] == "complete pipeline"
                else None
            )
    elif args.cost_ledger:
        parser.error("--cost-ledger requires --cost-reconciliation")
    comparison = None
    if args.paired:
        if len(runs) != 2:
            parser.error("--paired requires exactly two --run arguments")
        comparison = paired_comparison(*runs)
    output = guard_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    repeats = (
        repeat_summary(runs, reviewed_code_changes=args.reviewed_repeat_code_changes) if args.repeat_summary else None
    )
    write_json(output, {"schema": 1, "runs": runs, "paired": comparison, "repeats": repeats})
    if args.markdown:
        markdown = markdown_report(runs)
        if repeats is not None:
            markdown += "\nRepeat variation: `" + json.dumps(repeats, sort_keys=True) + "`.\n"
        if comparison is not None:
            summary = {key: value for key, value in comparison.items() if key != "page_deltas"}
            markdown += "\nPaired comparison: `" + json.dumps(summary, sort_keys=True) + "`.\n"
        guard_path(args.markdown).write_text(markdown)


if __name__ == "__main__":
    main()
