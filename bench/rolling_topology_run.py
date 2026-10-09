"""T004 opt-in generic union admission with persistent shared-ledger bounds."""

# ruff: noqa: ANN401, EM101, TRY003
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bench.borderless_challenge import score
from bench.decision_hosted import RESERVATION, ROOT, DecisionClient, accounted_cost, checkpoint, exclusive_lock
from bench.decision_oplog_run import parse_choice
from bench.reprice_model_rates import request_cost
from bench.silver import guard_path

MODELS = {"perplexity/pplx-decider-v1.1-27b", "openai/gpt-6-luna-decisions"}
TAG_PREFIX = "T004-generic-union/"
WAVE_LIMIT = 0.50


def verify(directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Verify all source and request identities before constructing a hosted client."""
    directory = guard_path(directory)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    if not manifest["models"] or not set(manifest["models"]) <= MODELS:
        raise ValueError("Union models must be the declared Luna/PPLX IDs")
    sources = []
    for cohort in manifest["cohorts"]:
        raw = guard_path(Path(cohort["source_path"])).read_bytes()
        if hashlib.sha256(raw).hexdigest() != cohort["source_sha256"]:
            raise ValueError("Union source changed after freeze")
        sources.append({p["id"]: p for p in json.loads(raw)["pages"]})
    for record in manifest["records"]:
        if record["route"] != "hosted_admission":
            continue
        if Path(record["request"]).name != record["request"]:
            raise ValueError("Request filename escapes frozen directory")
        raw = (directory / record["request"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("Frozen union request changed")
        body = json.loads(raw)
        if body["model"] != record["model"] or set(body["questions"]) != {"q0"}:
            raise ValueError("Frozen union model/question mismatch")
        if set(body["questions"]["q0"]["criteria"]) != set(record["choices"]):
            raise ValueError("Frozen union candidate menu mismatch")
    return manifest, sources


def wave_admission(entries: list[dict[str, Any]]) -> None:
    """Keep prior reservations/effective charges under the fixed persistent wave prefix cap."""
    used = sum(accounted_cost(e["accounted_usd"]) for e in entries if e.get("tag", "").startswith(TAG_PREFIX))
    if used + RESERVATION > WAVE_LIMIT + 1e-12:
        raise RuntimeError("T004 $0.50 prefix cap cannot admit the next $0.30 reservation")


def _entries(client: Any) -> list[dict[str, Any]]:
    return json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []


def materialize(page: dict[str, Any], candidates: list[dict[str, Any]], choice: str) -> dict[str, Any]:
    """Select one complete candidate or retain the full source inventory outside tables."""
    if choice in ("not_table", "unresolved"):
        return {"tables": [], "unresolved_ids": [w["id"] for w in page["words"]], "status": choice}
    found = next((c for c in candidates if c["id"] == choice), None)
    if found is None:
        raise ValueError("Selected generic candidate is not in the frozen source menu")
    owned = [i for cell in found["table"]["cells"] for i in cell["source_ids"]]
    if Counter(owned + found["unresolved_ids"]) != Counter(w["id"] for w in page["words"]):
        raise ValueError("Selected union candidate violates source conservation")
    return {"tables": [found["table"]], "unresolved_ids": found["unresolved_ids"], "status": choice}


def evaluate(  # noqa: PLR0913, PLR0917
    manifest: dict[str, Any],
    sources: list[dict[str, Any]],
    calls: list[dict[str, Any]],
    cohort_indices: list[int],
    target_paths: list[Path],
    diagnostic_cohorts: set[int],
) -> dict[str, Any]:
    """Open private references only after bodies freeze; separate wrong accepts from abstention/missing."""
    native = {r["id"]: r["native_selection"] for r in manifest["records"] if r["route"] == "native_vector"}
    lookup = {(r["model"], r["id"]): r for r in calls}
    cohorts: dict[str, Any] = {}
    for cohort_index, target_path in zip(cohort_indices, target_paths, strict=True):
        targets = {t["id"]: t for t in json.loads(guard_path(target_path).read_bytes())}
        if set(targets) != set(sources[cohort_index]):
            raise ValueError("Union private reference cohort differs from frozen sources")
        for model in manifest["models"]:
            rows = []
            for retained in manifest["cohorts"][cohort_index]["pages"]:
                page = sources[cohort_index][retained["source_id"]]
                target = targets[retained["source_id"]]
                call = lookup.get((model, retained["id"]))
                if retained["id"] in native:
                    selected = native[retained["id"]]
                    status = "native_vector"
                    owned = [i for c in selected["word_ownership"] for i in c["source_ids"]]
                else:
                    choice = (
                        call.get("answer", {}).get("choice", "unresolved")
                        if call and call["status"] == "ok"
                        else "unresolved"
                    )
                    selected = materialize(page, retained["candidates"], choice)
                    status = choice if call and call["status"] == "ok" else "unmeasured_or_failed"
                    owned = [i for table in selected["tables"] for cell in table["cells"] for i in cell["source_ids"]]
                if Counter(owned + selected["unresolved_ids"]) != Counter(w["id"] for w in page["words"]):
                    raise ValueError("Union selected state lost source inventory")
                eligible = (
                    target.get("binary_admission_eligible", True)
                    and target["kind"] != "ambiguous"
                    and cohort_index not in diagnostic_cohorts
                )
                scored = score(target, selected["tables"]) if eligible else None
                accepted = bool(selected["tables"])
                candidate_scores = [score(target, [c["table"]]) for c in retained["candidates"]] if eligible else []
                rows.append(
                    {
                        "id": retained["id"],
                        "source_id": retained["source_id"],
                        "kind": target["kind"],
                        "eligible": eligible,
                        "selection": status,
                        "accepted": accepted,
                        "scores": scored,
                        "accepted_wrong_table": bool(
                            scored is not None and target["tables"] and accepted and not scored["exact_page"]
                        ),
                        "candidate_ceiling_exact": bool(eligible and any(s["exact_page"] for s in candidate_scores)),
                        "source_conservation": True,
                        "owned_source_ids": len(owned),
                        "unresolved_source_ids": len(selected["unresolved_ids"]),
                    }
                )
            slices = {}
            for kind in ("borderless", "prose", "ruled-control", "ambiguous"):
                selected_rows = [r for r in rows if r["kind"] == kind]
                eligible_rows = [r for r in selected_rows if r["eligible"]]
                slices[kind] = {
                    "pages": len(selected_rows),
                    "scored_pages": len(eligible_rows),
                    "accepted_pages": sum(r["accepted"] for r in selected_rows),
                    "accepted_wrong_table": sum(r["accepted_wrong_table"] for r in eligible_rows),
                    "not_table": sum(r["selection"] == "not_table" for r in selected_rows),
                    "unresolved": sum(r["selection"] == "unresolved" for r in selected_rows),
                    "unmeasured_or_failed": sum(r["selection"] == "unmeasured_or_failed" for r in selected_rows),
                    "candidate_ceiling_exact": sum(r["candidate_ceiling_exact"] for r in eligible_rows),
                    **{
                        key: sum(r["scores"][key] for r in eligible_rows)
                        for key in (
                            "exact_page",
                            "exact_cells",
                            "exact_spans",
                            "owned_values",
                            "owned_words",
                            "false_positive_page",
                        )
                    },
                }
            cohorts[f"cohort{cohort_index}/{model}"] = {
                "rows": rows,
                "slices": slices,
                "pages": len(rows),
                "diagnostic_only": cohort_index in diagnostic_cohorts,
            }
    selected_ids = {p["id"] for i in cohort_indices for p in manifest["cohorts"][i]["pages"]}
    unique = {r["entry"]["index"]: r for r in calls if "entry" in r and r["id"] in selected_ids}
    model_stats = {}
    for model in manifest["models"]:
        retained = [r for r in unique.values() if r["model"] == model]
        complete_cost = all(r["cost"]["effective_usd"] is not None for r in retained)
        effective = sum(r["cost"]["effective_usd"] for r in retained) if complete_cost else None
        elapsed = (
            sum(r["http_elapsed_ms"] for r in retained)
            if all(r.get("http_elapsed_ms") is not None for r in retained)
            else None
        )
        model_stats[model] = {
            "requested_pages": len(retained),
            "successful_requests": sum(r["status"] == "ok" for r in retained),
            "planned_requests": sum(
                r["route"] == "hosted_admission" and r["model"] == model and r["id"] in selected_ids
                for r in manifest["records"]
            ),
            "effective_usd": effective,
            "http_elapsed_ms": elapsed,
            "requested_pages_per_usd": len(retained) / effective if effective is not None and effective > 0 else None,
            "requested_pages_per_http_minute": len(retained) * 60000 / elapsed
            if elapsed is not None and elapsed > 0
            else None,
        }
    costs = [r["cost"] for r in unique.values()]
    return {
        "cohorts": cohorts,
        "model_stats": model_stats,
        "unique_requests": len(unique),
        "effective_usd": sum(c["effective_usd"] for c in costs)
        if all(c["effective_usd"] is not None for c in costs)
        else None,
        "known_partial_usd": sum(c["effective_usd"] for c in costs if c["effective_usd"] is not None),
        "unknown_cost_requests": sum(c["effective_usd"] is None for c in costs),
        "source_conservation": True,
        "api_http_elapsed_ms": sum(r.get("http_elapsed_ms") or 0 for r in unique.values())
        if all(r.get("http_elapsed_ms") is not None for r in unique.values())
        else None,
        "label_warning": (
            "Ambiguous and diagnostic cohorts are excluded from binary/exact model claims. "
            "Earlier fresh class-cue admission results are invalid for primary claims."
        ),
    }


def report(summary: dict[str, Any]) -> str:
    """Show correct structures, wrong accepts and unresolved/missing states separately."""
    lines = [
        "# T004 generic source-candidate union admission",
        "",
        summary["label_warning"],
        "",
        (
            "| Cohort/model | Eligible tables exact | Accepted wrong tables | Eligible prose false table | "
            "Table unresolved / missing | Ambiguous proposals |"
        ),
        "| --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for label, cohort in summary["cohorts"].items():
        s = cohort["slices"]
        tables = [s["borderless"], s["ruled-control"]]
        lines.append(
            f"| {label} | {sum(t['exact_page'] for t in tables)}/{sum(t['scored_pages'] for t in tables)} | "
            f"{sum(t['accepted_wrong_table'] for t in tables)} | "
            f"{s['prose']['false_positive_page']}/{s['prose']['scored_pages']} | "
            f"{sum(t['unresolved'] for t in tables)} / {sum(t['unmeasured_or_failed'] for t in tables)} | "
            f"{s['ambiguous']['accepted_pages']} |"
        )
    lines += [
        "",
        (
            f"Unique requests {summary['unique_requests']}; complete effective USD {summary['effective_usd']}; "
            f"known partial USD {summary['known_partial_usd']}; "
            f"unknown charge requests {summary['unknown_cost_requests']}."
        ),
        "",
        (
            "Positive reported charges take precedence; zero/missing charges use retained "
            "complete catalog token rates. "
            "Reservations remain admission accounting. Missing tokens/rates stay unknown. "
            "No inference occurs by default."
        ),
        "",
        (
            "All selected and unresolved source IDs are conserved. Candidate oracle coverage "
            "is not achieved selection; "
            "authored DEV outcomes are not independent generalization or calibrated confidence."
        ),
        "",
    ]
    lines += [
        "| Model | Requested / planned pages | Successful requests | Effective USD | Pages/USD | Pages/HTTP minute |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model, stats in summary["model_stats"].items():
        lines.append(
            f"| {model} | {stats['requested_pages']}/{stats['planned_requests']} | "
            f"{stats['successful_requests']} | {stats['effective_usd']} | "
            f"{stats['requested_pages_per_usd']} | {stats['requested_pages_per_http_minute']} |"
        )
    lines += [
        "",
        (
            "Rates count paid requested pages; native zero-call pages are excluded. "
            "HTTP-minute rates use summed request durations, not end-to-end throughput."
        ),
        f"API HTTP elapsed milliseconds (complete measured sum): {summary['api_http_elapsed_ms']}.",
        f"Local preparation CPU/RSS metadata: {summary.get('preparation', 'not retained')}.",
        "HTTP durations describe provider requests; they do not measure remote CPU/RAM.",
        "",
    ]
    return "\n".join(lines)


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
                    body, tag=f"{TAG_PREFIX}{record['model']}/{record['id']}", max_body_bytes=750_000
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
                row["answer"] = parse_choice(response["result"], set(body["questions"]["q0"]["criteria"]))
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
        summary.update(
            tag_prefix=TAG_PREFIX,
            wave_limit_usd=WAVE_LIMIT,
            stopped_models=sorted(stopped),
            budget_stopped=budget_stopped,
            frozen_manifest_sha256=hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
            catalog_provenance=catalog,
            preparation={k: manifest[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")},
        )
        checkpoint(directory / "evaluation.json", summary)
        if report_path:
            report_path.write_text(report(summary))
        return summary


def main() -> None:
    """Require explicit hosted execution; offline verification never constructs the client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--targets", type=Path, nargs="+", required=True)
    parser.add_argument("--cohorts", type=int, nargs="+")
    parser.add_argument("--diagnostic-cohorts", type=int, nargs="*", default=[])
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report", type=Path, default=ROOT / "bench/results/rolling-topology-admission.md")
    args = parser.parse_args()
    manifest, sources = verify(args.directory)
    if args.run_hosted:
        summary = run(
            args.directory,
            args.targets,
            DecisionClient(),
            cohort_indices=args.cohorts,
            diagnostic_cohorts=set(args.diagnostic_cohorts),
            report_path=args.report,
        )
    else:
        indices = args.cohorts if args.cohorts is not None else list(range(len(sources)))
        if len(indices) != len(args.targets):
            parser.error("Targets must match selected cohort count")
        retained_path = args.directory / "hosted-results.json"
        retained = json.loads(retained_path.read_bytes()) if retained_path.exists() else {"calls": []}
        summary = evaluate(manifest, sources, retained["calls"], indices, args.targets, set(args.diagnostic_cohorts))
        previous_path = args.directory / "evaluation.json"
        previous = json.loads(previous_path.read_bytes()) if previous_path.exists() else {}
        summary.update(
            {k: previous[k] for k in ("catalog_provenance", "stopped_models", "budget_stopped") if k in previous}
        )
        summary.update(
            frozen_manifest_sha256=hashlib.sha256((args.directory / "manifest.json").read_bytes()).hexdigest(),
            preparation={k: manifest[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")},
        )
        args.report.write_text(report(summary))
    print(json.dumps({k: summary[k] for k in ("unique_requests", "effective_usd", "source_conservation")}, indent=2))


if __name__ == "__main__":
    main()
