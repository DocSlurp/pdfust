"""Independent fresh admission replay conditional on authenticated frozen generation."""

# Retained heterogeneous experiment schemas and explicitly authenticated pure helpers.
# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR0912
from __future__ import annotations

from pathlib import Path
from typing import Any

from bench.p003_incremental_verification import _helpers, _read, imported_baseline
from bench.silver import canonical, guard_path, sha


def verify_gate(
    directory: Path,
    report: dict[str, Any],
    frozen: dict[str, Any],
    trusted: dict[str, dict[str, str]] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Rebuild literal source packets/pixels and admit only frozen or fallback states."""
    import pylopdf
    from bench import generalization_run as regions
    from bench import p003_gate_run as runner
    from bench.p003_gate_image import transform

    if trusted is None or set(trusted) != {"baseline"}:
        raise ValueError("Gate replay requires an independent frozen-generation baseline trust map")
    _helpers(
        frozen,
        (
            "p003_gate_run.py",
            "p003_gate_image.py",
            "p003_gate_packet.py",
            "p003_prompt_variants.py",
            "pipeline_assembly.py",
            "pipeline_regions.py",
            "pipeline_source_order.py",
            "generalization_run.py",
            "pipeline_frontier.py",
            "decision_oplog_run.py",
        ),
    )
    config = frozen["config"]
    provider = config.get("gate_provider", "openrouter")
    if provider not in {"openrouter", "vercel"}:
        raise ValueError("Unknown frozen gate provider")
    if provider == "vercel":
        _helpers(frozen, ("p003_transport.py", "decision_gateway.py", "decision_gateway_vision.py"))
        if config.get("transport_concurrency", 1) != 1 or config["model"] not in {
            "liquid/d1",
            "convaiinnovations/laya",
            "convaiinnovations/laya-free",
        }:
            raise ValueError("Gateway gate replay differs from the serial declared route")
        if (
            sha((directory / "gateway-prices.json").read_bytes()) != frozen["gateway_pricing_sha256"]
            or _read(directory / "gateway-prices.json") != frozen["gateway_pricing"]
        ):
            raise ValueError("Frozen Gateway price/endpoint evidence changed")
    copied, original_frozen, original_report = imported_baseline(
        directory, frozen, "baseline", "baseline", trusted["baseline"]
    )
    runner.authenticate(copied, trusted["baseline"])
    if report["baseline_report"] != original_report or config["baseline_source_order"] != original_frozen["config"].get(
        "source_order", "legacy"
    ):
        raise ValueError("Fresh gate changed historical generation provenance")
    originals = {p["id"]: p for p in original_report["results"]}
    records = {r["id"]: r for r in frozen["records"]}
    artifacts = report["fresh_response_artifacts"]
    entries = {entry["index"]: entry for entry in report["incremental_gate"]["entries"]}
    for name, metadata in artifacts.items():
        if Path(name).name != name or sha((directory / name).read_bytes()) != metadata["sha256"]:
            raise ValueError("Fresh gate provider response bytes changed")
        entry = entries[metadata["ledger_index"]]
        if (
            entry["request_sha256"] != metadata["request_sha256"]
            or entry["response_file"] != metadata["original_response_file"]
        ):
            raise ValueError("Fresh gate response attribution changed")
    verified = {}
    for page in report["results"]:
        ident = page["id"]
        original = originals[ident]
        if _read(directory / f"{ident}-result.json") != page or page["historical_calls"] != original.get("calls", []):
            raise ValueError("Fresh gate changed original result/call provenance")
        if page["baseline_result_sha256"] != sha((copied / f"{ident}-result.json").read_bytes()):
            raise ValueError("Fresh gate baseline result hash changed")
        if original["status"] != "ok":
            if page["status"] != "error" or page["gate_status"] != "baseline_failed" or page["calls"]:
                raise ValueError("Failed generation baseline incorrectly admitted by fresh gate")
            verified[ident] = {"operational": False}
            continue
        if page["source"] != original["source"] or page["region_plan"] != original["region_plan"]:
            raise ValueError("Fresh gate changed frozen source or region plan")
        old_infos = {info["id"]: info for info in original["regions"]}
        original_regions = original["region_plan"]["regions"]
        if len(page["regions"]) > len(original_regions):
            raise ValueError("Fresh gate added a source region")
        states, consumed = {}, []
        with pylopdf.open(stream=guard_path(Path(records[ident]["pdf_path"])).read_bytes()) as document:
            pdf_page = document[records[ident]["page_number"]]
            if pdf_page.rotation != original["original_rotation"]:
                raise ValueError("Fresh gate source rotation changed")
            if pdf_page.rotation != original["effective_rotation"]:
                pdf_page.set_rotation(original["effective_rotation"])
            for region, info in zip(original_regions, page["regions"], strict=False):
                old = old_infos[region["id"]]
                fallback = runner.fallback_state(region["source"])
                if (
                    info["id"] != region["id"]
                    or info["bbox"] != region["bbox"]
                    or info["boundary"] != region["boundary"]
                    or info["original_route"] != old["route"]
                    or info["original_state_sha256"] != sha(canonical(old["state"]))
                    or info["fallback_state_sha256"] != sha(canonical(fallback))
                ):
                    raise ValueError("Fresh gate region provenance changed")
                reason = runner.bypass_reason(region, original_frozen["config"])
                if reason:
                    if (
                        info["route"] != "baseline_bypass"
                        or info["admission_reason"] != reason
                        or info["request_index"] is not None
                    ):
                        raise ValueError("Fresh gate altered frozen source-policy bypass")
                    selected = old["state"]
                else:
                    if old["route"] != "generated":
                        raise ValueError("Fresh gate lacks frozen generation for its eligible region")
                    if info["request_index"] is None:
                        if page["status"] == "ok" or page.get("error_stage") not in {"image", "packet"}:
                            raise ValueError("Fresh gate region silently omitted a required decision")
                        continue
                    if config["gate_image"]:
                        url, image = regions.region_image(pdf_page, region["bbox"], config["gate_image_edge"])
                        url, image = transform(url, image, config["gate_image_mode"])
                    else:
                        url, image = None, {"image": "none", "gate_image_mode": "rgb"}
                    body, evidence = runner.gate_request(region, config, url)
                    step = info["request_index"]
                    if (
                        step != len(consumed)
                        or info["image"] != image
                        or info["evidence"] != evidence
                        or _read(directory / f"{ident}-request-{step}.json") != body
                    ):
                        raise ValueError("Fresh gate body, pixels or source packet differs from replay")
                    filename = f"{ident}-response-{step}.json"
                    metadata = artifacts.get(filename)
                    expected_hash = evidence.get("request_identity_sha256", evidence["request_sha256"])
                    if info["admission_reason"] == "pending":
                        if page["status"] != "error" or page["gate_status"] != "failed_atomic":
                            raise ValueError("Pending fresh gate decision incorrectly produces a complete page")
                        if metadata is not None and metadata["request_sha256"] != expected_hash:
                            raise ValueError("Failed fresh gate body attribution changed")
                        continue
                    if metadata is None or len(page["calls"]) <= step:
                        raise ValueError("Fresh gate admission lacks exact provider response evidence")
                    call = page["calls"][step]
                    answer = runner.parse_gate_response(body, _read(directory / filename), config)
                    if (
                        call["entry"]["index"] != metadata["ledger_index"]
                        or metadata["request_sha256"] != expected_hash
                        or call.get("replayed") is not False
                        or info["admission"] != answer
                        or call["answer"] != answer
                        or call["entry"]["tag"] != f"P003/{config['run_id']}/{ident}/{region['id']}/{step}"
                    ):
                        raise ValueError("Fresh gate response or run attribution differs from replay")
                    consumed.append(step)
                    choice = answer["choice"]
                    selected = old["state"] if choice == "table" else fallback
                    if info["admission_reason"] != choice or info["route"] != (
                        "frozen_generated" if choice == "table" else "gated_out"
                    ):
                        raise ValueError("Fresh gate choice disposition changed")
                if info["state"] != selected or info["selected_state_sha256"] != sha(canonical(selected)):
                    raise ValueError("Fresh gate selected a state outside frozen generation and native fallback")
                states[region["id"]] = selected
        if len(consumed) != len(page["calls"]):
            raise ValueError("Fresh gate call inventory differs from retained admission receipts")
        if page["status"] == "ok":
            if len(page["regions"]) != len(original_regions) or page["gate_status"] != "complete":
                raise ValueError("Fresh gate complete output omits source regions")
            state, markdown = runner.compose_selected(original, states, config["baseline_source_order"])
            if (
                page["tables"] != state["tables"]
                or page["unresolved_ids"] != state["unresolved_ids"]
                or not page["source_conserved"]
            ):
                raise ValueError("Fresh gate composition differs from selected frozen states")
            if (
                _read(directory / f"{ident}-structure.json") != state
                or (directory / f"{ident}.md").read_text() != markdown
            ):
                raise ValueError("Fresh gate complete structure/Markdown differs from replay")
        elif page["tables"] or page["source_conserved"] or page["gate_status"] != "failed_atomic":
            raise ValueError("Failed fresh gate incorrectly exposes partial complete output")
        verified[ident] = {"operational": page["status"] == "ok", "scope": "conditional frozen generation admission"}
    return {
        "report_sha256": sha((copied / "report.json").read_bytes()),
        "conditional_on_frozen_generation": True,
    }, verified
