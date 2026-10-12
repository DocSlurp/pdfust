"""Fresh P003 admission calls conditional on independently trusted frozen generation.

No source extraction, OCR, detector, or generation is repeated. Only root runs
hosted calls through the coordinated metered client. Complete baseline failures
remain in the denominator; a failed gate never silently admits a region.
"""

# Explicit heterogeneous experiment schemas; imports stay lazy where optional.
# ruff: noqa: ANN401, EM101, TRY003, TRY301, PLC0415, C901, PLR0912, PLR2004, SLF001
from __future__ import annotations

import argparse
import json
import platform
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import generalization_run as regions
from bench import pipeline_run as pipeline
from bench.decision_hosted import DECISION_MODELS, accounted_cost
from bench.generalization_report import verify_output
from bench.p003_gate_image import EDGES, MODES, transform
from bench.p003_gate_packet import packet
from bench.p003_report import verify_archive
from bench.pipeline_admission import admission_packet
from bench.pipeline_assembly import native_state, validate
from bench.pipeline_frontier import MODELS as CHAT_MODELS
from bench.pipeline_regions import compose
from bench.pipeline_source_order import render_source
from bench.silver import canonical, guard_path, sha, write_json

STYLES = ("legacy", "region", "visual_schema", "recall_first", "skeptical", "local_relations")
GATEWAY_MODELS = ("liquid/d1", "convaiinnovations/laya", "convaiinnovations/laya-free")
PACKETS = ("legacy", "fullwords", "compact", "sample64", "image_only", "lineflow")
TRUNCATION_RISK_MODELS = ("cloudflare/clef-flash", "cloudflare/clef")
BASELINE_CODE = (
    "generalization_run.py",
    "pipeline_run.py",
    "pipeline_regions.py",
    "pipeline_assembly.py",
    "pipeline_generation.py",
    "pipeline_index_matrix_generation.py",
    "pipeline_matrix_generation.py",
    "pipeline_generation_evidence.py",
    "pipeline_frontier.py",
    "pipeline_source_order.py",
)
EXTRA_CODE = (
    "p003_gate_run.py",
    "p003_gate_image.py",
    "p003_gate_packet.py",
    "p003_prompt_variants.py",
    "p003_client.py",
    "p003_report.py",
    "generalization_report.py",
    "decision_concurrent.py",
    "decision_gateway.py",
    "decision_langfuse.py",
    "reprice_model_rates.py",
    "research_policy.py",
    "p003_transport.py",
    "decision_gateway_vision.py",
    "decision_oplog_run.py",
    "decision_oplog.py",
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Expected an artifact JSON object")
    return value


def _identifier(value: str) -> str:
    if not isinstance(value, str) or Path(value).name != value or value in ("", ".", ".."):
        raise ValueError("Unsafe artifact identifier")
    return value


def authenticate(directory: Path, trusted_code: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Use an independently supplied code map and replay complete source ownership."""
    if not trusted_code:
        raise ValueError("Frozen generation requires an explicit independent trusted code map")
    frozen, report = _read(directory / "frozen.json"), _read(directory / "report.json")
    config = frozen["config"]
    if (
        config != report["config"]
        or config.get("processor") != "regions"
        or config.get("assembly_method") != "generate"
    ):
        raise ValueError("Gate-only experiment requires one frozen ordinal region-generation baseline")
    if config.get("generation_format") != "indices" or config.get("raster_rules"):
        raise ValueError("Gate-only baseline must use ordinal generation without raster rule candidates")
    if not set(BASELINE_CODE) <= frozen["code_sha256"].keys():
        raise ValueError("Frozen ordinal baseline lacks required source/generation/ownership dependencies")
    verify_archive(directory, frozen, trusted_code)
    records = frozen["records"]
    ids = [_identifier(record["id"]) for record in records]
    predictions = {p["id"]: p for p in report["results"]}
    if len(ids) != len(set(ids)) or len(predictions) != len(report["results"]) or set(ids) != set(predictions):
        raise ValueError("Gate baseline must retain every intended page exactly once")
    for record in records:
        if set(record) != {"id", "pdf_path", "pdf_sha256", "page_number"}:
            raise ValueError("Frozen records must contain source fields only")
        if sha(guard_path(Path(record["pdf_path"])).read_bytes()) != record["pdf_sha256"]:
            raise ValueError("Frozen gate source PDF changed")
        for step, _call in enumerate(predictions[record["id"]].get("calls", [])):
            _read(directory / f"{record['id']}-request-{step}.json")
        verify_output(
            directory,
            predictions[record["id"]],
            processor="regions",
            config=config,
            source_order=config.get("source_order", "legacy"),
        )
    return frozen, report


def fallback_state(source: dict[str, Any]) -> dict[str, Any]:
    """Construct exactly the no-table c0 alternative without building unused hypotheses."""
    state = {
        "id": "c0",
        "tables": [],
        "unresolved_ids": [word["id"] for word in source["words"]],
        "description": "No table admission; retain all source words as unresolved prose or other content.",
        "mechanism": "none",
    }
    validate(source, state)
    return state


def bypass_reason(region: dict[str, Any], config: dict[str, Any]) -> str | None:
    """Reproduce the original source-policy early routes before admission."""
    if (
        region.get("kind") == "detector_proposal"
        and not region.get("context_complete", True)
        and config.get("detector_boundary", "retain") == "retain"
    ):
        return "detector_incomplete_context_retained"
    if (
        config.get("layout_detector") == "yolo"
        and config.get("detector_residual", "retain") == "retain"
        and region.get("kind") == "residual"
    ):
        return "detector_residual_retained"
    if native_state(region["source"])["tables"] or config["policy"] == "native":
        return "native"
    return None


def gate_request(
    region: dict[str, Any],
    config: dict[str, Any],
    url: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build literal evidence and an actual body without any transmission or old answers."""
    source = region["source"]
    if config["gate_packet"] == "legacy":
        viewport = "Image viewport in global page coordinates: " + json.dumps(region["bbox"]) + ".\n" if url else ""
        prompt = viewport + admission_packet(source, premise="relational", pixels_available=bool(url))
        metadata = {
            "style": "legacy",
            "fullsource_sha256": sha(canonical(source)),
            "source_word_count": len(source["words"]),
            "text_omitted": False,
        }
    else:
        prompt, metadata = packet(source, region["bbox"], pixels_available=bool(url), style=config["gate_packet"])
    if config["gate_row_evidence"]:
        from bench.pipeline_row_context import context

        prompt += "\n" + context(source)
    body = pipeline.body(
        config["model"], prompt, regions.GATE_CHOICES, url, instructions=regions.gate_instructions(config)
    )
    if config.get("answer_tokens") and config["model"] in CHAT_MODELS:
        body["max_tokens"] = config["answer_tokens"]
    transport_metadata = {}
    if config.get("gate_provider", "openrouter") == "vercel":
        from bench.decision_gateway import ENDPOINT as TYPESAFE_ENDPOINT
        from bench.decision_gateway import request_identity
        from bench.decision_gateway_vision import ENDPOINT as NATIVE_ENDPOINT
        from bench.p003_transport import gateway_wire

        body, native = gateway_wire(body)
        endpoint = NATIVE_ENDPOINT if native else TYPESAFE_ENDPOINT
        encoded = json.dumps(body, separators=(",", ":")).encode()
        transport_metadata = {
            "gateway": "vercel",
            "endpoint": endpoint,
            "request_identity_sha256": request_identity(encoded, endpoint=endpoint),
        }
    encoded = json.dumps(body, separators=(",", ":")).encode()
    return body, {
        **transport_metadata,
        "packet": metadata,
        "evidence_utf8_bytes": len(prompt.encode()),
        "evidence_sha256": sha(prompt.encode()),
        "source_word_count": len(source["words"]),
        "request_sha256": sha(encoded),
        "request_body_bytes": len(encoded),
        "evidence_scope": "complete supplied baseline region before declared packet projection; not whole page",
        "provider_state_truncation_risk": config["model"] in TRUNCATION_RISK_MODELS,
        "provider_state_truncation_note": (
            "Provider documents silent state truncation after roughly 2000 tokens; actual tokens retained separately, "
            "no token estimate or complete delivery claim"
            if config["model"] in TRUNCATION_RISK_MODELS
            else "No assertion of absence of provider truncation"
        ),
    }


def compose_selected(
    original: dict[str, Any], states: dict[str, dict[str, Any]], source_order: str
) -> tuple[dict[str, Any], str]:
    """Use the unchanged complete ownership, bbox, and original-order rendering rules."""
    source = original["source"]
    plan = {**original["region_plan"], "words": source["words"]}
    state = compose(plan, states)
    regions._table_bounds(source, state)
    order = {word["id"]: index for index, word in enumerate(source["words"])}
    rendered = [
        (
            min((order[i] for i in region["source_ids"]), default=len(order)),
            pipeline.markdown(
                render_source(source, region) if source_order == "original" else region["source"], states[region["id"]]
            ),
        )
        for region in plan["regions"]
    ]
    return state, "\n".join(text for _, text in sorted(rendered))


def parse_gate_response(
    body: dict[str, Any],
    raw: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Replay documented raw provider envelopes without inferring alternate formats."""
    from bench.decision_oplog_run import parse_choice
    from bench.pipeline_frontier import parse as parse_chat

    if config.get("gate_provider", "openrouter") == "vercel":
        from bench.decision_gateway import normalize_response
        from bench.decision_gateway_vision import normalize_answers

        normalized = normalize_answers(raw, body) if body["model"] == "liquid/d1" else normalize_response(raw)
        return parse_choice(normalized, set(regions.GATE_CHOICES))
    if body["model"] in CHAT_MODELS:
        return parse_chat(raw, tuple(regions.GATE_CHOICES))
    return parse_choice(raw, set(regions.GATE_CHOICES))


def gateway_call(client: Any, body: dict[str, Any], tag: str) -> dict[str, Any]:
    """Make a serial root Gateway call with shared pricing, policy, and typed parsing."""
    from bench.decision_oplog_run import parse_choice

    if getattr(client, "stopped", False):
        raise RuntimeError("P003 Gateway arm stopped after a transport/admission failure")
    spent = sum(accounted_cost(entry["accounted_usd"]) for entry in _entries(client, "P003/"))
    if spent + 0.30 > pipeline.WAVE_LIMIT:
        raise RuntimeError("P003 Gateway reservation would exceed its USD50 wave cap")
    started, cpu = time.perf_counter(), time.process_time()
    try:
        response = client.request(body, tag=tag, replay=False, max_body_bytes=750_000)
        answer = parse_choice(response["result"], set(regions.GATE_CHOICES))
    except Exception:
        client.stopped = True
        raise
    return {
        "answer": answer,
        "entry": response["entry"],
        "usage": response["result"].get("usage", {}),
        "replayed": response["replayed"],
        "client_wall_seconds": time.perf_counter() - started,
        "client_cpu_seconds": time.process_time() - cpu,
    }


def process(
    record: dict[str, Any],
    config: dict[str, Any],
    output: Path,
    client: Any,
) -> dict[str, Any]:
    """Gate an authenticated copied baseline; fail atomically on missing/failed admission."""
    import pdfust

    identifier = _identifier(record["id"])
    baseline = guard_path(Path(config["baseline_directory"]))
    original = _read(baseline / f"{identifier}-result.json")
    started, cpu = time.perf_counter(), time.process_time()
    result = {
        "id": identifier,
        "status": "error",
        "tables": [],
        "unresolved_ids": [],
        "calls": [],
        "regions": [],
        "source_conserved": False,
        "route": "conditional_frozen_generation_gate",
        "output_scope": "complete_page",
        "evaluation_scope": "conditional_on_frozen_generation",
        "historical_calls": deepcopy(original.get("calls", [])),
        "baseline_result_sha256": sha((baseline / f"{identifier}-result.json").read_bytes()),
    }
    stage = "baseline"
    try:
        if original["status"] != "ok":
            result.update(
                error_type=original.get("error_type", "BaselineError"),
                gate_status="baseline_failed",
                baseline_error=original.get("error"),
            )
        else:
            result.update(
                source=deepcopy(original["source"]),
                region_plan=deepcopy(original["region_plan"]),
                original_rotation=original["original_rotation"],
                effective_rotation=original["effective_rotation"],
            )
            baseline_config = _read(baseline / "frozen.json")["config"]
            infos = {info["id"]: info for info in original["regions"]}
            states = {}
            data = guard_path(Path(record["pdf_path"])).read_bytes()
            if sha(data) != record["pdf_sha256"]:
                raise ValueError("Frozen gate source PDF changed")
            with pdfust.open(stream=data) as document:
                page = document[record["page_number"]]
                if page.rotation != original["original_rotation"]:
                    raise ValueError("Source original rotation differs from baseline")
                # Follow the independently authenticated acquisition's recorded effective rotation.
                if page.rotation != original["effective_rotation"]:
                    page.set_rotation(original["effective_rotation"])
                for region in original["region_plan"]["regions"]:
                    local = infos[region["id"]]
                    fallback = fallback_state(region["source"])
                    reason = bypass_reason(region, baseline_config)
                    info = {
                        "id": region["id"],
                        "bbox": region["bbox"],
                        "boundary": region["boundary"],
                        "original_route": local["route"],
                        "original_state_sha256": sha(canonical(local["state"])),
                        "fallback_state_sha256": sha(canonical(fallback)),
                        "request_index": None,
                    }
                    result["regions"].append(info)
                    if reason:
                        if local["route"] != reason or local["state"] != native_state(region["source"]):
                            raise ValueError("Frozen bypass output differs from source-policy native state")
                        selected = deepcopy(local["state"])
                        info.update(route="baseline_bypass", admission_reason=reason)
                    else:
                        if local["route"] != "generated":
                            raise ValueError("Frozen eligible region lacks complete generation output")
                        stage = "image"
                        if config["gate_image"]:
                            url, image = regions.region_image(page, region["bbox"], config["gate_image_edge"])
                            url, image = transform(url, image, config["gate_image_mode"])
                        else:
                            url, image = None, {"image": "none", "gate_image_mode": "rgb"}
                        stage = "packet"
                        body, evidence = gate_request(region, config, url)
                        step = len(result["calls"])
                        info.update(image=image, evidence=evidence, request_index=step, admission_reason="pending")
                        write_json(output / f"{identifier}-request-{step}.json", body)
                        stage = "gate"
                        call = gateway_call if config.get("gate_provider", "openrouter") == "vercel" else pipeline.call
                        answer = call(client, body, f"P003/{config['run_id']}/{identifier}/{region['id']}/{step}")
                        result["calls"].append(answer)
                        choice = answer["answer"]["choice"]
                        if choice not in regions.GATE_CHOICES:
                            raise ValueError("Fresh gate answer is outside declared choices")
                        selected = deepcopy(local["state"] if choice == "table" else fallback)
                        info.update(
                            route="frozen_generated" if choice == "table" else "gated_out",
                            admission_reason=choice,
                            admission=answer["answer"],
                            reported_usage=deepcopy(answer.get("usage", {})),
                        )
                    info.update(state=selected, selected_state_sha256=sha(canonical(selected)))
                    states[region["id"]] = selected
            stage = "composition"
            state, markdown = compose_selected(original, states, config["baseline_source_order"])
            write_json(output / f"{identifier}-structure.json", state)
            (output / f"{identifier}.md").write_text(markdown)
            result.update(
                status="ok",
                tables=state["tables"],
                unresolved_ids=state["unresolved_ids"],
                source_conserved=True,
                gate_status="complete",
            )
    except Exception as error:
        result.update(error_type=type(error).__name__, error_stage=stage, gate_status="failed_atomic")
        if isinstance(error, (ValueError, KeyError)):
            result["error"] = str(error)[:500]
    result.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu)
    write_json(output / f"{identifier}-result.json", result)
    return result


def _entries(client: Any, prefix: str) -> list[dict[str, Any]]:
    if client is None or not client.ledger.exists():
        return []
    return [deepcopy(e) for e in _read(client.ledger)["requests"] if e.get("tag", "").startswith(prefix)]


def archive_responses(client: Any, output: Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Copy exact provider bytes of only this run's returned or failed parse attempts."""
    artifacts = {}
    for entry in entries:
        if not entry.get("response_file"):
            continue
        parts = entry["tag"].split("/")
        if len(parts) != 5 or parts[0] != "P003" or parts[1] != output.name or not parts[4].isdigit():
            raise ValueError("Fresh gate response tag differs from declared run scope")
        identifier, step = _identifier(parts[2]), int(parts[4])
        response_name = _identifier(entry["response_file"])
        if not (output / f"{identifier}-request-{step}.json").is_file():
            raise ValueError("Returned gate response lacks its exact retained request")
        data = guard_path(client.directory / response_name).read_bytes()
        name = f"{identifier}-response-{step}.json"
        (output / name).write_bytes(data)
        artifacts[name] = {
            "sha256": sha(data),
            "ledger_index": entry["index"],
            "original_response_file": response_name,
            "request_sha256": entry["request_sha256"],
        }
    return artifacts


def charges(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve unknown charges and reservations separately from complete effective cost."""
    bases = Counter(e.get("cost_status", "unknown") for e in entries)
    resolved = [e for e in entries if e.get("cost_status") not in ("unknown", "reserved")]
    reported = [e["provider_reported_usd"] for e in entries if "provider_reported_usd" in e]
    return {
        "ledger_attempts": len(entries),
        "entries": entries,
        "cost_bases": dict(bases),
        "accounted_usd": sum(accounted_cost(e["accounted_usd"]) for e in entries),
        "effective_usd": sum(accounted_cost(e["accounted_usd"]) for e in resolved)
        if len(resolved) == len(entries)
        else None,
        "known_partial_effective_usd": sum(accounted_cost(e["accounted_usd"]) for e in resolved),
        "provider_reported_usd": sum(reported) if len(reported) == len(entries) else None,
        "known_partial_provider_reported_usd": sum(reported),
        "missing_provider_charge_count": len(entries) - len(reported),
        "unresolved_reserved_usd": sum(
            accounted_cost(e["accounted_usd"]) for e in entries if e.get("cost_status") == "reserved"
        ),
        "cost_scope": "Fresh gate API attempts only; historical generation/detector/OCR costs retained separately",
    }


def run(
    baseline_directory: Path,
    trusted_code_path: Path,
    output: Path,
    config: dict[str, Any],
    client: Any = None,
) -> dict[str, Any]:
    """Authenticate and copy all intended baseline evidence before opt-in fresh gates."""
    if not config.get("run_hosted"):
        raise ValueError("Fresh gate inference requires explicit root run_hosted opt-in")
    baseline_directory, trusted_code_path, output = map(guard_path, (baseline_directory, trusted_code_path, output))
    original_frozen, original_report = authenticate(baseline_directory, _read(trusted_code_path))
    defaults = {
        "gate_image_edge": 512,
        "gate_image_mode": "rgb",
        "gate_image": True,
        "gate_packet": "compact",
        "gate_instructions": "region",
        "gate_row_evidence": False,
        "answer_tokens": 2048,
        "transport_concurrency": 1,
    }
    config = {
        **defaults,
        **config,
        "campaign": "P003",
        "processor": "p003_gate",
        "run_id": _identifier(output.name),
        "baseline_source_order": original_frozen["config"].get("source_order", "legacy"),
    }
    provider = config.get("gate_provider", "openrouter")
    allowed_models = GATEWAY_MODELS if provider == "vercel" else (*DECISION_MODELS, *CHAT_MODELS)
    if config["model"] not in allowed_models:
        raise ValueError("Unknown frozen gate model")
    if (
        config["gate_image_edge"] not in EDGES
        or config["gate_image_mode"] not in MODES
        or config["gate_instructions"] not in STYLES
        or config["gate_packet"] not in PACKETS
        or type(config["transport_concurrency"]) is not int
        or config["transport_concurrency"] not in (1, 3)
        or type(config["gate_image"]) is not bool
        or type(config["gate_row_evidence"]) is not bool
        or (not config["gate_image"] and config["gate_image_mode"] != "rgb")
        or provider not in ("openrouter", "vercel")
        or (provider == "vercel" and config["transport_concurrency"] != 1)
        or (provider == "vercel" and config["model"] != "liquid/d1" and config["gate_image"])
    ):
        raise ValueError("Invalid gate-only treatment; Gateway requires serial d1 or text-only Laya")
    output.mkdir(parents=True, exist_ok=False)
    copied = output / "baseline"
    copied.mkdir()
    files = {"frozen.json", "report.json"}
    ids = [_identifier(record["id"]) for record in original_frozen["records"]]
    for identifier in ids:
        for suffix in ("-result.json", "-structure.json", ".md"):
            name = identifier + suffix
            if (baseline_directory / name).is_file():
                files.add(name)
    for pattern in ("*-request*.json", "*-response*.json"):
        for path in baseline_directory.glob(pattern):
            if not path.name.startswith(tuple(identifier + "-" for identifier in ids)):
                raise ValueError("Baseline request/response belongs to an unintended page")
            files.add(path.name)
    files |= {"code/" + name for name in original_frozen["code_sha256"]}
    hashes = {}
    for name in sorted(files):
        data = guard_path(baseline_directory / name).read_bytes()
        target = copied / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        hashes[name] = sha(data)
    config["baseline_directory"] = str(copied)
    root = Path(__file__).resolve().parent
    code_names = sorted(set(original_frozen["code_sha256"]) | set(EXTRA_CODE))
    (output / "code").mkdir()
    code_hashes = {}
    for name in code_names:
        data = (root / _identifier(name)).read_bytes()
        (output / "code" / name).write_bytes(data)
        code_hashes[name] = sha(data)
    frozen = {
        "config": config,
        "records": deepcopy(original_frozen["records"]),
        "manifest_sha256": original_frozen["manifest_sha256"],
        "code_sha256": code_hashes,
        "concurrency": 1,
        "transport_concurrency": config["transport_concurrency"],
        "local_replay": False,
        "runtime": pipeline.runtime_fingerprints(),
        "python": platform.python_version(),
        "baseline": {
            "directory": str(baseline_directory),
            "copied_directory": "baseline",
            "file_sha256": hashes,
            "source_order": config["baseline_source_order"],
            "original_config": original_frozen["config"],
            "trusted_code_manifest_sha256": sha(trusted_code_path.read_bytes()),
        },
    }
    write_json(output / "frozen.json", frozen)
    if client is None:
        if provider == "vercel":
            from bench.decision_gateway import GatewayDecisionClient
            from bench.decision_gateway_vision import GatewayVisionDecisionClient

            client = (GatewayVisionDecisionClient if config["model"] == "liquid/d1" else GatewayDecisionClient)()
        else:
            from bench.p003_client import P003ConcurrentClient, P003DecisionClient

            client = (P003ConcurrentClient if config["transport_concurrency"] == 3 else P003DecisionClient)()
    if provider == "vercel":
        from bench.decision_gateway import ENDPOINT as TYPESAFE_ENDPOINT
        from bench.decision_gateway_vision import ENDPOINT as NATIVE_ENDPOINT

        expected_endpoint = NATIVE_ENDPOINT if config["model"] == "liquid/d1" else TYPESAFE_ENDPOINT
        if client.endpoint != expected_endpoint:
            raise ValueError("Injected Gateway client endpoint differs from the authenticated model route")
        frozen["gateway_pricing"] = {
            "endpoint": client.endpoint,
            "gateway": "vercel",
            "catalog": deepcopy(client.catalog),
            "scope": "Gateway-specific client catalog frozen before calls; positive provider charges take precedence",
        }
        write_json(output / "gateway-prices.json", frozen["gateway_pricing"])
        frozen["gateway_pricing_sha256"] = sha((output / "gateway-prices.json").read_bytes())
        write_json(output / "frozen.json", frozen)
    prefix = f"P003/{config['run_id']}/"
    if _entries(client, prefix):
        raise ValueError("Fresh gate run ID already exists in the persistent ledger")
    with pipeline.Resources() as resources:
        results = [process(record, config, output, client) for record in frozen["records"]]
    metrics = {
        **resources.summary(),
        "scope": "incremental admission conditional on frozen generation",
        "baseline_work_repeated": False,
        "end_to_end_pipeline_measured": False,
        "baseline_freezing_resources": "unmeasured separately",
        "concurrency": 1,
        "transport_concurrency": config["transport_concurrency"],
        "transport_comparison": "contended" if config["transport_concurrency"] == 3 else "serial",
        "interval": "After authentication/copy: gate rendering, evidence, waits, decode, composition and outputs",
    }
    entries = _entries(client, prefix)
    response_artifacts = archive_responses(client, output, entries)
    report = {
        "config": config,
        "page_count": len(results),
        "results": results,
        "baseline_report": original_report,
        "complete_output_pages": sum(p["status"] == "ok" for p in results),
        "calls": sum(len(p["calls"]) for p in results),
        "metrics": metrics,
        "incremental_gate": {"metrics": metrics, **charges(entries)},
        "fresh_response_artifacts": response_artifacts,
        "measurement_scope": "conditional_on_frozen_generation; fresh gate cost/latency only",
        "pages_per_minute": None,
        "pages_per_dollar": None,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Standalone opt-in root entry point; no default hosted work."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument(
        "--model", choices=tuple(dict.fromkeys((*DECISION_MODELS, *CHAT_MODELS, *GATEWAY_MODELS))), required=True
    )
    parser.add_argument("--gate-provider", choices=("openrouter", "vercel"), default="openrouter")
    parser.add_argument("--gate-image-edge", choices=EDGES, type=int, default=512)
    parser.add_argument("--gate-image-mode", choices=MODES, default="rgb")
    parser.add_argument("--gate-packet", choices=PACKETS, default="compact")
    parser.add_argument("--gate-instructions", choices=STYLES, default="region")
    parser.add_argument("--text-gate", action="store_true")
    parser.add_argument("--gate-row-evidence", action="store_true")
    parser.add_argument("--transport-concurrency", choices=(1, 3), type=int, default=1)
    args = parser.parse_args()
    config = {
        key: value
        for key, value in vars(args).items()
        if key not in ("baseline", "trusted_code", "output", "text_gate")
    }
    config["gate_image"] = not args.text_gate
    if config["gate_provider"] == "openrouter":
        del config["gate_provider"]
    report = run(args.baseline, args.trusted_code, args.output, config)
    print(
        json.dumps({key: value for key, value in report.items() if key not in ("results", "baseline_report")}, indent=2)
    )


if __name__ == "__main__":
    main()
