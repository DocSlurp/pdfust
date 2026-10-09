"""Matched, frozen Anthropic 5.5 chat baselines for source-only PDF admission."""

# ruff: noqa: ANN401, EM101, TRY003
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from bench.decision_hosted import ROOT, DecisionClient, accounted_cost, checkpoint, exclusive_lock
from bench.reprice_model_rates import number, request_cost
from bench.rolling_topology_run import evaluate
from bench.rolling_topology_run import report as union_report
from bench.rolling_topology_run import verify as verify_parent
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss

MODELS = tuple(f"anthropic/claude-{name}-5.5" for name in ("opus", "sonnet", "haiku"))
TAG_PREFIX = "A055-baseline/"
WAVE_LIMIT = 5.0
RESERVATION = 1.25
MAX_BODY_BYTES = 750_000
REQUEST_SETTINGS = {
    "reasoning": {"effort": "medium"},
    "max_tokens": 4096,
    "provider": {
        "require_parameters": True,
        "allow_fallbacks": False,
        "max_price": {"prompt": 4, "completion": 20},
    },
}


def translate(body: dict[str, Any], model: str) -> dict[str, Any]:
    """Preserve original evidence and question exactly while changing only transport."""
    if model not in MODELS or set(body["questions"]) != {"q0"}:
        raise ValueError("Matched baseline requires a declared model and exactly q0")
    question = body["questions"]["q0"]
    if question["type"] != "choice":
        raise ValueError("Matched baseline requires an original Choice menu")
    state = body["state"]
    if isinstance(state, list):
        content = [{"type": "text", "text": item} if isinstance(item, str) else item for item in state]
    elif isinstance(state, str):
        content = state
    else:
        content = json.dumps(state, separators=(",", ":"))
    choice_schema = {
        "type": "object",
        "properties": {"choice": {"type": "string", "enum": list(question["criteria"])}},
        "required": ["choice"],
        "additionalProperties": False,
    }
    schema = {
        "type": "object",
        "properties": {
            "answers": {
                "type": "object",
                "properties": {"q0": choice_schema},
                "required": ["q0"],
                "additionalProperties": False,
            },
        },
        "required": ["answers"],
        "additionalProperties": False,
    }
    return {
        "model": model,
        **json.loads(json.dumps(REQUEST_SETTINGS)),
        "messages": [
            {"role": "system", "content": question["instructions"]},
            {
                "role": "system",
                "content": json.dumps({"q0": {"criteria": question["criteria"]}}, separators=(",", ":")),
            },
            {"role": "user", "content": content},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "pdf_admission", "strict": True, "schema": schema},
        },
    }


def _raw(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def prepare(parent: Path, directory: Path) -> dict[str, Any]:
    """Freeze every matched request before any target files or credentials are opened."""
    start, cpu = time.perf_counter(), time.process_time()
    parent, directory = guard_path(parent), guard_path(directory)
    original, _ = verify_parent(parent)
    if directory.exists():
        raise ValueError("Baseline output already exists; preserve frozen requests")
    unique: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    native = []
    for record in original["records"]:
        if record["route"] == "native_vector":
            native.append(record)
            continue
        body = json.loads((parent / record["request"]).read_bytes())
        evidence = {key: value for key, value in body.items() if key != "model"}
        if record["id"] in unique and evidence != unique[record["id"]][1]:
            raise ValueError("Parent model arms do not share exact evidence and candidate menu")
        unique[record["id"]] = (record, evidence)
    records = list(native)
    pending = []
    for page_id, (record, evidence) in unique.items():
        for model_index, model in enumerate(MODELS):
            body = translate(evidence, model)
            raw = _raw(body)
            if len(raw) > MAX_BODY_BYTES:
                raise ValueError("Frozen matched chat request exceeds byte admission")
            filename = f"{page_id}-model{model_index}.json"
            pending.append((filename, raw))
            records.append(
                {
                    "id": page_id,
                    "model": model,
                    "route": "hosted_admission",
                    "arm": "matched-chat",
                    "request": filename,
                    "sha256": _hash(raw),
                    "bytes": len(raw),
                    "choices": record["choices"],
                    "parent_request": record["request"],
                    "parent_request_sha256": record["sha256"],
                }
            )
    directory.mkdir(parents=True)
    for filename, raw in pending:
        (directory / filename).write_bytes(raw)
    rss, measurement = process_peak_rss()
    manifest = {
        "schema": 1,
        "models": list(MODELS),
        "records": records,
        "cohorts": original["cohorts"],
        "parent_directory": str(parent.resolve()),
        "parent_manifest_sha256": _hash((parent / "manifest.json").read_bytes()),
        "request_settings": REQUEST_SETTINGS,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"perf_counter/process_time; {measurement}; sequential CPU; lifetime RSS; no sampling",
    }
    (directory / "manifest.json").write_bytes(_raw(manifest))
    return {"manifest_sha256": _hash(_raw(manifest)), "requests": len(pending), "directory": str(directory)}


def verify(directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:  # noqa: C901
    """Verify parent, source, menu and exact translated body before hosted client creation."""
    directory = guard_path(directory)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    parent = guard_path(Path(manifest["parent_directory"]))
    if _hash((parent / "manifest.json").read_bytes()) != manifest["parent_manifest_sha256"]:
        raise ValueError("Parent manifest changed after baseline freeze")
    original, sources = verify_parent(parent)
    if manifest["models"] != list(MODELS) or manifest["cohorts"] != original["cohorts"]:
        raise ValueError("Baseline models or sources changed after freeze")
    if manifest["request_settings"] != REQUEST_SETTINGS:
        raise ValueError("Baseline request settings changed after freeze")
    originals = {(r.get("model"), r["id"]): r for r in original["records"]}
    parent_requests = {r["request"]: r for r in original["records"] if r["route"] == "hosted_admission"}
    expected_ids = {r["id"] for r in parent_requests.values()}
    seen = set()
    native = [r for r in original["records"] if r["route"] == "native_vector"]
    if [r for r in manifest["records"] if r["route"] == "native_vector"] != native:
        raise ValueError("Baseline native selection differs from parent")
    for record in manifest["records"]:
        if record["route"] != "hosted_admission":
            continue
        identity = (record["model"], record["id"])
        if identity in seen or identity[0] not in MODELS:
            raise ValueError("Duplicate or unknown baseline request")
        seen.add(identity)
        if Path(record["request"]).name != record["request"]:
            raise ValueError("Baseline request escapes frozen directory")
        parent_record = parent_requests[record["parent_request"]]
        if parent_record != originals[(parent_record["model"], record["id"])]:
            raise ValueError("Baseline parent request identity differs")
        if record["parent_request_sha256"] != parent_record["sha256"] or record["choices"] != parent_record["choices"]:
            raise ValueError("Baseline parent request or menu changed")
        parent_body = json.loads((parent / parent_record["request"]).read_bytes())
        raw = (directory / record["request"]).read_bytes()
        if _hash(raw) != record["sha256"] or raw != _raw(translate(parent_body, record["model"])):
            raise ValueError("Frozen baseline body changed")
    if seen != {(model, page_id) for model in MODELS for page_id in expected_ids}:
        raise ValueError("Baseline request inventory differs from frozen parent")
    return manifest, sources


def parse_choice(result: dict[str, Any], choices: set[str]) -> dict[str, str]:
    """Require one complete choice and preserve absence of model confidence."""
    responses = result["choices"]
    if len(responses) != 1 or responses[0].get("finish_reason") != "stop":
        raise ValueError("Chat response did not finish normally with exactly one answer")
    parsed = json.loads(responses[0]["message"]["content"])
    if not isinstance(parsed, dict) or set(parsed) != {"answers"}:
        raise ValueError("Unexpected chat answer fields")
    answers = parsed["answers"]
    if not isinstance(answers, dict) or set(answers) != {"q0"}:
        raise ValueError("Chat response must answer exactly q0")
    answer = answers["q0"]
    if not isinstance(answer, dict) or set(answer) != {"choice"}:
        raise ValueError("Chat answer must contain only choice")
    if not isinstance(answer["choice"], str) or answer["choice"] not in choices:
        raise ValueError("Chat choice is outside the frozen menu")
    return answer


def wave_admission(entries: list[dict[str, Any]]) -> None:
    """Admit only within this persistent prefix cap, including outstanding reservations."""
    used = sum(accounted_cost(e["accounted_usd"]) for e in entries if e.get("tag", "").startswith(TAG_PREFIX))
    if used + RESERVATION > WAVE_LIMIT + 1e-12:
        raise RuntimeError("A055 $5.00 prefix cap cannot admit the next $1.25 reservation")


def _entries(client: Any) -> list[dict[str, Any]]:
    return json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []


def reservation_bounds(directory: Path, manifest: dict[str, Any], catalog: dict[str, Any]) -> dict[str, float]:
    """Preflight all calls using UTF-8 request bytes as a conservative input-token bound."""
    bounds: dict[str, float] = {}
    for record in manifest["records"]:
        if record["route"] != "hosted_admission":
            continue
        price = catalog.get("prices", {}).get(record["model"], {})
        inputs, outputs = number(price.get("input")), number(price.get("output"))
        if inputs is None or outputs is None:
            raise ValueError("Baseline reservation preflight requires complete retained catalog rates")
        raw = (directory / record["request"]).read_bytes()
        ceiling = REQUEST_SETTINGS["provider"]["max_price"]
        inputs = max(inputs, ceiling["prompt"] / 1e6)
        outputs = max(outputs, ceiling["completion"] / 1e6)
        bound = len(raw) * inputs + REQUEST_SETTINGS["max_tokens"] * outputs
        if bound > RESERVATION:
            raise ValueError("Baseline byte/token price bound exceeds the per-request reservation")
        bounds[record["model"]] = max(bounds.get(record["model"], 0), bound)
    return bounds


def report(summary: dict[str, Any]) -> str:
    """Retain matched score and request-rate definitions with explicit chat settings."""
    text = union_report(summary).replace(
        "# T004 generic source-candidate union admission",
        "# Matched Anthropic 5.5 source-candidate admission baselines",
    )
    prices = summary.get("catalog_provenance", {}).get("prices", {})
    rates = "\n| Model | Input USD/M tokens | Output USD/M tokens |\n| --- | ---: | ---: |\n"
    for model in MODELS:
        price = prices.get(model, {})
        values = [number(price.get(key)) for key in ("input", "output")]
        rates += f"| {model} | {values[0] * 1e6 if values[0] is not None else 'unknown'} | "
        rates += f"{values[1] * 1e6 if values[1] is not None else 'unknown'} |\n"
    return (
        text
        + "\nRequest settings: "
        + json.dumps(summary.get("request_settings", REQUEST_SETTINGS), sort_keys=True)
        + "\n\n"
        + rates
        + "\nLocal execution CPU/RSS metadata: "
        + json.dumps(summary.get("execution", "unmeasured"))
        + "\n"
        + (
            "Original source text, image blocks, q0 instructions and criteria are preserved; "
            "only API transport changes. "
            "One source page per request; model confidence is unreported. "
            "First failure stops that model, without retries. "
            "Prices and provider provenance are retained in evaluation.json catalog_provenance.\n"
        )
    )


def run(  # noqa: C901, PLR0913
    directory: Path,
    target_paths: list[Path],
    client: Any,
    *,
    cohort_indices: list[int] | None = None,
    diagnostic_cohorts: set[int] | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Run explicitly selected frozen cohorts under shared lock and persistent model/failure policy."""
    manifest, sources = verify(directory)
    indices = cohort_indices if cohort_indices is not None else list(range(len(sources)))
    if len(target_paths) != len(indices) or any(i < 0 or i >= len(sources) for i in indices):
        raise ValueError("Selected union cohorts require matching private reference files")
    start, cpu = time.perf_counter(), time.process_time()
    with exclusive_lock(client.ledger.parent / "run.lock"):
        result_path = directory / "hosted-results.json"
        result = json.loads(result_path.read_bytes()) if result_path.exists() else {"calls": [], "stopped_models": []}
        calls, stopped = result["calls"], set(result["stopped_models"])
        for entry in _entries(client):
            if entry.get("tag", "").startswith(TAG_PREFIX) and not entry.get("response_file"):
                stopped.add(entry.get("requested_model"))
        done = {r["sha256"] for r in calls}
        catalog_path = client.ledger.parent / "langfuse/catalog-prices.json"
        catalog = json.loads(catalog_path.read_bytes()) if catalog_path.exists() else {"prices": {}}
        bounds = reservation_bounds(directory, manifest, catalog)
        retained_ids = {p["id"] for i in indices for p in manifest["cohorts"][i]["pages"]}
        budget_stopped = False
        for record in manifest["records"]:
            if (
                record["route"] != "hosted_admission"
                or record["id"] not in retained_ids
                or record["sha256"] in done
                or record["model"] in stopped
                or budget_stopped
            ):
                continue
            raw = (directory / record["request"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != record["sha256"]:
                raise ValueError("Frozen union body changed after verification")
            body = json.loads(raw)
            digest = hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest()
            entries = _entries(client)
            known = next((e for e in entries if e.get("request_sha256") == digest), None)
            if known is None:
                try:
                    wave_admission(entries)
                except RuntimeError:
                    budget_stopped = True
                    break
            row = {**record, "status": "pending"}
            calls.append(row)
            checkpoint(result_path, {"calls": calls, "stopped_models": sorted(stopped)})
            try:
                if known is not None and not known.get("response_file"):
                    raise RuntimeError("Prior identical union call failed; no retry")  # noqa: TRY301
                response = client.request(
                    body,
                    tag=f"{TAG_PREFIX}{record['model']}/{record['id']}",
                    max_body_bytes=MAX_BODY_BYTES,
                    reservation_usd=RESERVATION,
                )
                row.update(
                    entry=response["entry"],
                    usage=response["result"].get("usage", {}),
                    replayed=response["replayed"],
                    http_elapsed_ms=response["entry"].get("elapsed_ms"),
                )
                row["cost"] = request_cost(
                    row["entry"], row["usage"], catalog.get("prices", {}).get(record["model"], {})
                )
                row["answer"] = parse_choice(response["result"], set(record["choices"]))
                row["status"] = "ok"
            except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
                row.update(status="error", error=type(error).__name__)
                failed = next((e for e in _entries(client) if e.get("request_sha256") == digest), None)
                if failed is not None and "entry" not in row:
                    row.update(entry=failed, usage={})
                    row["cost"] = request_cost(failed, {}, catalog.get("prices", {}).get(record["model"], {}))
                stopped.add(record["model"])
            checkpoint(result_path, {"calls": calls, "stopped_models": sorted(stopped)})
        summary = evaluate(manifest, sources, calls, indices, target_paths, diagnostic_cohorts or set())
        rss, measurement = process_peak_rss()
        summary.update(
            execution={
                "wall_seconds": time.perf_counter() - start,
                "cpu_seconds": time.process_time() - cpu,
                "peak_rss_bytes": rss,
                "measurement": f"perf_counter/process_time; {measurement}; "
                "single CPU process including HTTP wait; lifetime RSS; no sampling; remote CPU/RAM unmeasured",
            },
            reservation_bounds_usd=bounds,
            reservation_usd=RESERVATION,
            tag_prefix=TAG_PREFIX,
            wave_limit_usd=WAVE_LIMIT,
            stopped_models=sorted(stopped),
            budget_stopped=budget_stopped,
            frozen_manifest_sha256=hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
            catalog_provenance=catalog,
            preparation={k: manifest[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")},
            request_settings=manifest["request_settings"],
            parent_manifest_sha256=manifest["parent_manifest_sha256"],
        )
        checkpoint(directory / "evaluation.json", summary)
        if report_path:
            report_path.write_text(report(summary))
        return summary


def main() -> None:
    """Prepare offline by default; hosted execution requires the explicit opt-in flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--targets", type=Path, nargs="+")
    parser.add_argument("--cohorts", type=int, nargs="+")
    parser.add_argument("--diagnostic-cohorts", type=int, nargs="*", default=[])
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report", type=Path, default=ROOT / "bench/results/anthropic-baseline.md")
    args = parser.parse_args()
    if args.prepare:
        if args.parent is None or args.run_hosted or args.targets:
            parser.error("Preparation requires --parent and cannot open targets or run hosted")
        print(json.dumps(prepare(args.parent, args.directory), indent=2))
        return
    manifest, sources = verify(args.directory)
    if not args.targets:
        print(
            json.dumps(
                {"verified": True, "requests": sum(r["route"] == "hosted_admission" for r in manifest["records"])}
            )
        )
        if args.run_hosted:
            parser.error("Hosted execution requires matching --targets")
        return
    indices = args.cohorts if args.cohorts is not None else list(range(len(sources)))
    if len(indices) != len(args.targets):
        parser.error("Targets must match selected cohort count")
    if args.run_hosted:
        summary = run(
            args.directory,
            args.targets,
            DecisionClient(),
            cohort_indices=indices,
            diagnostic_cohorts=set(args.diagnostic_cohorts),
            report_path=args.report,
        )
    else:
        retained_path = args.directory / "hosted-results.json"
        retained = json.loads(retained_path.read_bytes()) if retained_path.exists() else {"calls": []}
        summary = evaluate(manifest, sources, retained["calls"], indices, args.targets, set(args.diagnostic_cohorts))
        previous_path = args.directory / "evaluation.json"
        previous = json.loads(previous_path.read_bytes()) if previous_path.exists() else {}
        summary.update(
            {
                k: previous[k]
                for k in (
                    "catalog_provenance",
                    "stopped_models",
                    "budget_stopped",
                    "execution",
                    "reservation_bounds_usd",
                    "reservation_usd",
                )
                if k in previous
            }
        )
        summary.update(
            frozen_manifest_sha256=_hash((args.directory / "manifest.json").read_bytes()),
            parent_manifest_sha256=manifest["parent_manifest_sha256"],
            request_settings=manifest["request_settings"],
            preparation={k: manifest[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")},
        )
        checkpoint(args.directory / "evaluation.json", summary)
        args.report.write_text(report(summary))
    print(json.dumps({k: summary[k] for k in ("unique_requests", "effective_usd", "source_conservation")}, indent=2))


if __name__ == "__main__":
    main()
