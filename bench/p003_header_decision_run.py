"""Root-only factorized choices over literal-preserving header hypotheses."""

# ruff: noqa: ANN401, EM101, TRY003, TRY301, PLR0913, C901, PLR0912, PLR2004, E501
from __future__ import annotations

import argparse
import base64
import json
import resource
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import p003_header_packets as packets
from bench import p003_header_packets_prepare as preparer
from bench import pipeline_vision_transcription as strict
from bench.decision_hosted import ROOT
from bench.p003_boundary_run import RESERVATION, _charges, _entries, _error, _identifier
from bench.p003_client import P003ConcurrentClient, P003DecisionClient
from bench.p003_micro_relations_run import CODE_FILES as COMMON_CODE
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

if TYPE_CHECKING:
    from collections.abc import Callable

MODELS = (
    "perplexity/pplx-decider-v1.1-27b",
    "openai/gpt-6-luna-decisions",
    "cloudflare/clef-omni",
    "typesafe/jev-1.13",
)
EVIDENCE_MODES = ("full", "local_header")
EDGES = (0, 128, 512)


def read(path: Path) -> Any:
    """Read explicitly selected guarded artifacts."""
    return json.loads(guard_path(path).read_bytes())


def configuration(model: str, mode: str, edge: int, concurrency: int) -> dict[str, Any]:
    """Declare independent model and complete evidence treatment without fallback."""
    if model not in MODELS or mode not in EVIDENCE_MODES or type(edge) is not int or edge not in EDGES:
        raise ValueError("Explicit admitted header model, evidence mode and image edge required")
    if model == "typesafe/jev-1.13" and edge:
        raise ValueError("Jev header treatment is explicitly text-only")
    if type(concurrency) is not int or concurrency not in (1, 3):
        raise ValueError("Transport capacity must be 1 or 3; Gateway is unsupported")
    return {
        "processor": "p003_header_decision",
        "campaign": "P003",
        "provider": "openrouter",
        "model": model,
        "evidence_mode": mode,
        "image_edge": edge,
        "transport_concurrency": concurrency,
        "workers": 1,
        "replay": False,
        "retry": False,
        "model_fallback": False,
        "source_conserved": False,
        "model_credit_scope": "Actually selected complete header hypotheses only",
        "fixed_tables_scope": "Unchanged historical generation; composition provenance only",
        "composition_policy": "Selected complete alternatives plus separately identified fixed original tables; uncovered hypotheses receive zero credit; conflicting positive composition atomically refused",
        "full_page_denominator": 16,
        "scope": "Incremental factorized header choices over frozen generated strings; excludes generation and source acquisition",
    }


def client_for(config: dict[str, Any], _prepared: dict[str, Any]) -> Any:
    """Root constructs the shared-policy client after complete input freezing."""
    return P003ConcurrentClient(ROOT) if config["transport_concurrency"] == 3 else P003DecisionClient(ROOT)


def execute(
    prepared: dict[str, Any],
    output: Path,
    config: dict[str, Any],
    *,
    client_factory: Callable[..., Any] = client_for,
    entries_reader: Callable[..., list[dict[str, Any]]] = _entries,
) -> dict[str, Any]:
    """Ask each frozen table menu once; stop admission on the first transport failure."""
    prefix = f"P003/{config['run_id']}/header-decision/"
    client, initialization_error = None, None
    try:
        client = client_factory(config, prepared)
    except Exception as exc:
        initialization_error = _error(exc, "client_initialization")
    stopped, decisions = client is None, []
    with Resources() as resources:
        for item in prepared["selected"]:
            row = {
                "index": item["index"],
                "page_id": item["page_id"],
                "menu_id": item["menu"]["id"],
                "model": config["model"],
                "status": "not_attempted",
            }
            if item["body"] is None:
                row["status"] = "no_question_refusal"
                row["refusal"] = item["evidence"]
            elif not stopped:
                began, cpu_began = time.perf_counter(), time.process_time()
                try:
                    response = client.request(
                        item["body"],
                        tag=prefix + str(item["index"]),
                        replay=False,
                        reservation_usd=RESERVATION,
                        max_body_bytes=750_000,
                    )
                except Exception as exc:
                    row.update(status="transport_error", error=_error(exc, "transport"))
                    stopped = True
                else:
                    write_json(output / f"menu-{item['index']}-response.json", response)
                    try:
                        if not isinstance(response, dict):
                            raise TypeError("Invalid client response envelope")
                        entry = response.get("entry")
                        result = response.get("result")
                        row.update(
                            entry=entry,
                            usage=result.get("usage", {}) if isinstance(result, dict) else {},
                            admission_wait_seconds=response.get(
                                "admission_wait_seconds",
                                entry.get("admission_wait_seconds") if isinstance(entry, dict) else None,
                            ),
                            replayed=response.get("replayed"),
                        )
                        if response.get("replayed"):
                            raise ValueError("Fresh factorized choices cannot replay answers")
                        receipt = packets.parse(item["menu"], result)
                        row.update(
                            status="unresolved" if receipt["choice"] == "unresolved" else "selected", receipt=receipt
                        )
                        option = next((o for o in item["menu"]["options"] if o["alias"] == receipt["choice"]), None)
                        if option is not None:
                            row["selected_table_sha256"] = option["table_sha256"]
                    except (ValueError, KeyError, TypeError) as exc:
                        row.update(status="malformed_response", error=_error(exc, "parse"))
                row.update(
                    client_wall_seconds=time.perf_counter() - began, client_cpu_seconds=time.process_time() - cpu_began
                )
            decisions.append(row)
            write_json(output / f"menu-{item['index']}-result.json", row)
            write_json(output / "decision-results.json", {"decisions": decisions})
        results = []
        for page in prepared["pages"]:
            ident = page["id"]
            items = [i for i in prepared["selected"] if i["page_id"] == ident]
            rows = [r for r in decisions if r["page_id"] == ident]
            receipts = {r["menu_id"]: r["receipt"] for r in rows if r["status"] in {"selected", "unresolved"}}
            composed = packets.compose(page["plan"], [i["menu"] for i in items], receipts)
            selected_state, fixed_state, combined_state = (
                composed[k] for k in ("selected_state", "fixed_state", "combined_state")
            )
            effective_selected = sum(r["effective_selected"] for r in composed["receipts"])
            complete = bool(rows) and composed["complete_header_selection"]
            operational_ok = complete or (not rows and page["plan"]["status"] == "unchanged_valid")
            row = {
                "id": ident,
                "record": page["record"],
                "viewport": page["plan"]["original_page"]["viewport"],
                "status": "ok" if operational_ok else "error",
                "selection_status": "composition_conflicts"
                if composed["conflicts"]
                else "selected_complete_headers"
                if complete
                else "not_applicable_no_ambiguous_header"
                if not rows and operational_ok
                else "selected_partial_headers"
                if selected_state["tables"]
                else "failed_closed",
                "original_page_status": page["plan"]["original_page_status"],
                "state": selected_state,
                "tables": selected_state["tables"],
                "fixed_state": fixed_state,
                "combined_state": combined_state,
                "composition": composed,
                "decision_results": rows,
                "selected_header_count": sum(r["status"] == "selected" for r in rows),
                "effective_selected_header_count": effective_selected,
                "uncovered_header_count": sum(r["status"] != "selected" for r in rows),
                "fixed_historical_table_count": len(fixed_state["tables"]),
                "model_credited_table_count": len(selected_state["tables"]),
                "model": config["model"],
                "decision_model": config["model"],
                "literal_generation_model": prepared.get("run_frozen", {})
                .get("literal_generation_config", {})
                .get("generation_model"),
                "baseline_credit": False,
                "source_conserved": False,
            }
            for suffix, state in (
                ("state", selected_state),
                ("fixed-state", fixed_state),
                ("combined-state", combined_state),
            ):
                write_json(output / f"{ident}-{suffix}.json", state)
            write_json(output / f"{ident}-structure.json", selected_state["tables"])
            write_json(output / f"{ident}-combined-structure.json", combined_state["tables"])
            (output / f"{ident}.md").write_text(strict.markdown(selected_state))
            (output / f"{ident}-combined.md").write_text(strict.markdown(combined_state))
            write_json(output / f"{ident}-result.json", row)
            results.append(row)
    entries = entries_reader(client, prefix) if client is not None else []
    charges = _charges(entries)
    charges["cost_scope"] = (
        "Incremental factorized header-choice API attempts including failures; excludes original generation/source/pool preparation"
    )
    attempted = sum(
        r["status"] in {"selected", "unresolved", "malformed_response", "transport_error"} for r in decisions
    )
    if attempted and not entries:
        charges.update(effective_usd=None, provider_reported_usd=None, accounting_status="unmeasured missing attempts")
    metrics = resources.summary()
    wall, cost = metrics["wall_seconds"], charges["effective_usd"]
    report = {
        "config": config,
        "results": results,
        "decisions": decisions,
        "intended_page_count": 16,
        "attempted_question_count": attempted,
        "selected_header_count": sum(r["status"] == "selected" for r in decisions),
        "decision_status_counts": dict(Counter(r["status"] for r in decisions)),
        "client_initialization_error": initialization_error,
        "historical_provenance": prepared.get("run_frozen", {}).get("historical_provenance", []),
        "literal_generation_config": prepared.get("run_frozen", {}).get("literal_generation_config"),
        "incremental_header_selection": {
            "metrics": metrics,
            "charges": charges,
            "scope": config["scope"],
            "denominator": 16,
            "intended_pages_per_minute": 960 / wall if wall else None,
            "intended_pages_per_dollar": 16 / cost if cost and cost > 0 else None,
            "attempted_questions_per_minute": attempted * 60 / wall if wall else None,
        },
        "full_pipeline_pages_per_minute": None,
        "full_pipeline_pages_per_dollar": None,
        "model_fallbacks": 0,
        "retries": 0,
        "baseline_credit": False,
        "references_read": False,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def authenticate_pool(pool: Path, pool_trust: Path, header_trust: Path, generation_trust: Path) -> dict[str, Any]:
    """Authenticate independent archives and rederive every packet and source image without archived execution."""
    pool, pool_trust, header_trust, generation_trust = (
        guard_path(p) for p in (pool, pool_trust, header_trust, generation_trust)
    )
    frozen, report = read(pool / "frozen.json"), read(pool / "report.json")
    trusted = read(pool_trust)
    if not trusted or set(frozen["code_sha256"]) != set(preparer.CODE_FILES):
        raise ValueError("Complete independent header packet code authority required")
    for name, digest in frozen["code_sha256"].items():
        if Path(name).name != name or trusted.get(name) != digest or sha((pool / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived header packet code differs from independent authority")
    for name in preparer.CODE_FILES:
        if sha(Path(__file__).with_name(name).read_bytes()) != frozen["code_sha256"][name]:
            raise ValueError("Current literal/packet decoder differs from authenticated freeze")
    if frozen.get("references_read") is not False or frozen.get("hosted_calls") != 0 or len(frozen["records"]) != 16:
        raise ValueError("Complete source-only DEV16 pool required")
    receipts = {r["kind"]: r for r in frozen["source_trust_receipts"]}
    if set(receipts) != {"header", "generation"} or len(frozen["source_trust_receipts"]) != 2:
        raise ValueError("Independent header/source and generation authorities required")
    for name, authority in (("header", header_trust), ("generation", generation_trust)):
        receipt = receipts[name]
        directory = guard_path(Path(receipt["directory"]))
        if sha(authority.read_bytes()) != receipt["trusted_code_sha256"]:
            raise ValueError("External parent authority differs")
        for kind in ("frozen", "report"):
            if sha((directory / (kind + ".json")).read_bytes()) != receipt[kind + "_sha256"]:
                raise ValueError("Original source/generation provenance changed")
    with tempfile.TemporaryDirectory(prefix="p003-header-pool-replay-", dir=pool.parent) as temp:
        rebuilt = Path(temp) / "pool"
        replay = preparer.prepare(
            Path(receipts["header"]["directory"]),
            header_trust,
            Path(receipts["generation"]["directory"]),
            generation_trust,
            rebuilt,
            seed=frozen["seed"],
        )
        actual_frozen = read(rebuilt / "frozen.json")
        if actual_frozen != frozen:
            raise ValueError("Complete frozen header evidence contract changed")
        if {k: v for k, v in replay.items() if k not in {"resources", "frozen_sha256"}} != {
            k: v for k, v in report.items() if k not in {"resources", "frozen_sha256"}
        }:
            raise ValueError("Complete source-only header inventory differs")
        for path in rebuilt.rglob("*"):
            relative = path.relative_to(rebuilt)
            if (
                path.is_file()
                and path.name not in {"frozen.json", "report.json"}
                and "code" not in relative.parts
                and path.read_bytes() != (pool / relative).read_bytes()
            ):
                raise ValueError("Header literals, packets, images or requests changed")
    pages = []
    for row in report["pages"]:
        raw = (pool / row["path"]).read_bytes()
        if sha(raw) != row["sha256"]:
            raise ValueError("Complete original page plan changed")
        page = json.loads(raw)
        page["record"] = page["plan"]["record"]
        pages.append(page)
    if len(pages) != 16 or len({p["id"] for p in pages}) != 16:
        raise ValueError("Complete unique page inventory required")
    return {"pool_frozen": frozen, "pool_report": report, "pages": pages}


def prepare(
    pool: Path, output: Path, config: dict[str, Any], *, pool_trust: Path, header_trust: Path, generation_trust: Path
) -> dict[str, Any]:
    """Freeze all four independently selected native bodies before constructing any client."""
    started, cpu_started = time.perf_counter(), time.process_time()
    pool, output = guard_path(pool), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh header decision output required")
    authenticated = authenticate_pool(pool, pool_trust, header_trust, generation_trust)
    selected = []
    for page in authenticated["pages"]:
        for retained_menu in page["menus"]:
            menu = packets.hydrate(retained_menu)
            inventory = next(m for m in authenticated["pool_report"]["menus"] if m["menu_id"] == menu["id"])
            variant = next(
                v
                for v in inventory["variants"]
                if v["mode"] == config["evidence_mode"]
                and v["image_edge"] == config["image_edge"]
                and v["model"] == config["model"]
            )
            url = None
            if config["image_edge"]:
                image = (pool / "menus" / menu["id"] / f"image-{config['image_edge']}.png").read_bytes()
                url = "data:image/png;base64," + base64.b64encode(image).decode()
            body, evidence = packets.request(menu, config["model"], url, config["evidence_mode"])
            if evidence != read(pool / variant["evidence_path"]):
                raise ValueError("Declared evidence omission or byte identity differs")
            if body is not None:
                raw = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
                if (
                    len(raw) > 750_000
                    or sha(raw) != variant["body_sha256"]
                    or body != read(pool / variant["request_path"])
                ):
                    raise ValueError("Complete selected native request differs from frozen wire or exceeds cap")
            selected.append(
                {
                    "index": len(selected),
                    "page_id": page["id"],
                    "menu": menu,
                    "body": body,
                    "evidence": evidence,
                    "variant": variant,
                    "request_sha256": sha(raw) if body is not None else None,
                }
            )
    output.mkdir(parents=True)
    shutil.copytree(pool, output / "pool")
    (output / "code").mkdir()
    code = {}
    for name in tuple(dict.fromkeys(("p003_header_decision_run.py", *preparer.CODE_FILES, *COMMON_CODE))):
        path = Path(__file__).with_name(name)
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    histories = []
    for receipt in authenticated["pool_frozen"]["source_trust_receipts"]:
        directory = guard_path(Path(receipt["directory"]))
        shutil.copytree(directory, output / "history" / receipt["kind"])
        histories.append(
            {
                **receipt,
                "archive": "history/" + receipt["kind"],
                "scope": "Historical source/header proposal and original generation only; excluded from fresh choice totals",
            }
        )
    for item in selected:
        if item["body"] is not None:
            write_json(output / f"menu-{item['index']}-request.json", item["body"])
            (output / f"menu-{item['index']}-wire.json").write_bytes(
                json.dumps(item["body"], separators=(",", ":"), allow_nan=False).encode()
            )
    frozen = {
        "config": config,
        "records": authenticated["pool_frozen"]["records"],
        "manifest_sha256": read(output / "history" / "generation" / "frozen.json")["manifest_sha256"],
        "literal_generation_config": read(output / "history" / "generation" / "frozen.json")["config"],
        "pool_frozen_sha256": sha((pool / "frozen.json").read_bytes()),
        "pool_report_sha256": sha((pool / "report.json").read_bytes()),
        "code_sha256": code,
        "historical_provenance": histories,
        "selected": [{k: v for k, v in item.items() if k != "body"} for item in selected],
        "artifact_sha256": {str(p.relative_to(output)): sha(p.read_bytes()) for p in output.rglob("*") if p.is_file()},
        "all_inputs_frozen_before_client": True,
        "references_read": False,
        "independent_authorities": {
            "pool": str(pool_trust),
            "header": str(header_trust),
            "generation": str(generation_trust),
        },
        "preparation_resources": {
            "wall_seconds": time.perf_counter() - started,
            "self_cpu_seconds": time.process_time() - cpu_started,
            "peak_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": "Independent authentication, complete evidence rederivation and archive preparation; excludes imports; lifetime peak RSS includes imports; no sampling",
        },
    }
    write_json(output / "frozen.json", frozen)
    return {**authenticated, "selected": selected, "run_frozen": frozen}


def main() -> None:
    """Prepare-only by default; root must explicitly opt in to paid execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pool", "pool-trusted-code", "header-trusted-code", "generation-trusted-code", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--evidence-mode", choices=EVIDENCE_MODES, required=True)
    parser.add_argument("--image-edge", type=int, choices=EDGES, required=True)
    parser.add_argument("--transport-concurrency", type=int, choices=(1, 3), default=3)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    config = configuration(args.model, args.evidence_mode, args.image_edge, args.transport_concurrency)
    config["run_id"] = _identifier(args.output.name)
    prepared = prepare(
        args.pool,
        args.output,
        config,
        pool_trust=args.pool_trusted_code,
        header_trust=args.header_trusted_code,
        generation_trust=args.generation_trusted_code,
    )
    if args.run_hosted:
        execute(prepared, args.output, config)
    else:
        write_json(
            args.output / "prepare-report.json",
            {
                "status": "prepared_only",
                "intended_page_count": 16,
                "prepared_question_count": sum(i["body"] is not None for i in prepared["selected"]),
                "hosted_calls": 0,
                "rates": None,
            },
        )


if __name__ == "__main__":
    main()
