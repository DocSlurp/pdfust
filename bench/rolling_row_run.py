"""A002 opt-in source-candidate admission with shared ledger and frozen private scoring."""

# ruff: noqa: EM101, TRY003, ANN401
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from bench.borderless_challenge import score
from bench.decision_hosted import RESERVATION, ROOT, DecisionClient, accounted_cost, checkpoint, exclusive_lock
from bench.decision_oplog_run import parse_choice
from bench.reprice_model_rates import request_cost
from bench.rolling_rows import freeze_admission, selected_candidate
from bench.silver import guard_path

MODELS = ("perplexity/pplx-decider-v1.1-27b", "openai/gpt-6-luna-decisions")
TAG_PREFIX = "A002-rolling-admission/"
WAVE_LIMIT = 0.50


def verify(directory: Path) -> dict[str, Any]:
    """Check complete frozen body/source/candidate hashes before client construction or scoring."""
    directory = guard_path(directory)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    for name, key in (("source-frozen.json", "source_sha256"), ("candidates-frozen.json", "frozen_candidates_sha256")):
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != manifest[key]:
            raise ValueError("Frozen source or candidate identity changed")
    if not manifest["models"] or not set(manifest["models"]) <= set(MODELS):
        raise ValueError("Only declared PPLX/Luna native decision models are admitted")
    for record in manifest["records"]:
        if record["route"] != "hosted_admission":
            continue
        filename = record["request"]
        if Path(filename).name != filename:
            raise ValueError("Frozen request escapes admission directory")
        raw = (directory / filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("Frozen request body changed")
        body = json.loads(raw)
        if body["model"] != record["model"] or set(body["questions"]["q0"]["criteria"]) != set(record["choices"]):
            raise ValueError("Frozen request model/menu changed")
    return manifest


def wave_admission(entries: list[dict[str, Any]]) -> None:
    """Apply persistent prefix accounting independently of the shared $15 campaign policy."""
    used = sum(accounted_cost(e["accounted_usd"]) for e in entries if e.get("tag", "").startswith(TAG_PREFIX))
    if used + RESERVATION > WAVE_LIMIT + 1e-12:
        raise RuntimeError("A002 persistent $0.50 cap cannot admit the next $0.30 reservation")


def _entries(client: Any) -> list[dict[str, Any]]:
    return json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []


def evaluate(directory: Path, targets_path: Path, calls: list[dict[str, Any]]) -> dict[str, Any]:  # noqa: C901
    """Score frozen complete alternatives and chosen tables; references never enter model bodies."""
    manifest = verify(directory)
    sources = {p["id"]: p for p in json.loads((directory / "source-frozen.json").read_bytes())["pages"]}
    alternatives = {
        p["id"]: p["alternatives"] for p in json.loads((directory / "candidates-frozen.json").read_bytes())["pages"]
    }
    targets = {p["id"]: p for p in json.loads(guard_path(targets_path).read_bytes())}
    if set(sources) != set(targets):
        raise ValueError("Scorer target cohort differs from frozen sources")
    native = {r["id"]: r for r in manifest["records"] if r["route"] == "native_vector"}
    call_map = {(r["model"], r["arm"], r["id"]): r for r in calls}
    cohorts, ceiling_rows = {}, []
    for variant in ("physical", "rolling"):
        for page_id, alts in alternatives.items():
            tables = next(a for a in alts if a["variant"] == variant)["candidates"]
            expected_groups = Counter(
                tuple(value.split())
                for table in targets[page_id]["tables"]
                for row in table["values"]
                for value in row
                if value
            )
            actual_groups = Counter(
                tuple(value.split()) for table in tables for row in table["values"] for value in row if value
            )
            alt = next(a for a in alts if a["variant"] == variant)
            owned = [i for t in tables for cell in t["cells"] for i in cell["source_ids"]]
            conserved = Counter(owned + alt["unresolved_ids"]) == Counter(w["id"] for w in sources[page_id]["words"])
            if not conserved:
                raise ValueError("Frozen alternative inventory is not conserved")
            ceiling_rows.append(
                {
                    "id": page_id,
                    "source_conservation": conserved,
                    "owned_source_ids": len(owned),
                    "unresolved_source_ids": len(alt["unresolved_ids"]),
                    "text_group_exact": bool(expected_groups) and expected_groups == actual_groups,
                    "matched_text_groups": sum((expected_groups & actual_groups).values()),
                    "expected_text_groups": sum(expected_groups.values()),
                    "variant": variant,
                    "kind": targets[page_id]["kind"],
                    "scores": score(targets[page_id], tables),
                }
            )
    for model in manifest["models"]:
        for arm in manifest.get("arms", ["text", "image512"]):
            rows = []
            for page_id, page in sources.items():
                if page_id in native:
                    selected = native[page_id]["native_selection"]
                    selection_status = "native_vector"
                else:
                    call = call_map.get((model, arm, page_id))
                    choice = call.get("answer", {}).get("choice", "unresolved") if call else "unresolved"
                    selected = selected_candidate(page, alternatives[page_id], choice)
                    selection_status = choice if call and call["status"] == "ok" else "unmeasured_or_failed"
                if page_id not in native:
                    owners = [i for table in selected["tables"] for cell in table["cells"] for i in cell["source_ids"]]
                else:
                    owners = [i for cell in selected["word_ownership"] for i in cell["source_ids"]]
                conserved = Counter(owners + selected["unresolved_ids"]) == Counter(w["id"] for w in page["words"])
                if not conserved:
                    raise ValueError("Selected source inventory is not conserved")
                scored = score(targets[page_id], selected["tables"])
                rows.append(
                    {
                        "id": page_id,
                        "kind": targets[page_id]["kind"],
                        "selection": selection_status,
                        "scores": scored,
                        "conservation": conserved,
                        "owned_source_ids": len(owners),
                        "unresolved_source_ids": len(selected["unresolved_ids"]),
                    }
                )
            cohorts[f"{model}/{arm}"] = {
                "pages": len(rows),
                "native_zero_call_pages": len(native),
                "rows": rows,
                "slices": {
                    kind: {
                        "pages": sum(r["kind"] == kind for r in rows),
                        "expected_values": sum(
                            bool(value)
                            for t in targets.values()
                            if t["kind"] == kind
                            for table in t["tables"]
                            for row in table["values"]
                            for value in row
                        ),
                        "expected_words": sum(
                            len(value.split())
                            for t in targets.values()
                            if t["kind"] == kind
                            for table in t["tables"]
                            for row in table["values"]
                            for value in row
                            if value
                        ),
                        **{
                            key: sum(r["scores"][key] for r in rows if r["kind"] == kind)
                            for key in (
                                "exact_page",
                                "exact_cells",
                                "exact_spans",
                                "owned_values",
                                "owned_words",
                                "false_positive_page",
                            )
                        },
                        "unresolved_or_unmeasured": sum(
                            r["selection"] in ("unresolved", "unmeasured_or_failed") for r in rows if r["kind"] == kind
                        ),
                    }
                    for kind in ("borderless", "prose", "ruled-control")
                },
            }
    unique = {r["entry"]["index"]: r for r in calls if "entry" in r}
    costs = [r["cost"] for r in unique.values()]
    http_times = [r["http_elapsed_ms"] for r in unique.values() if r.get("http_elapsed_ms") is not None]
    return {
        "cohorts": cohorts,
        "candidate_ceiling_rows": ceiling_rows,
        "unique_requests": len(unique),
        "http_elapsed_median_ms": median(http_times) if http_times else None,
        "http_elapsed_total_seconds": sum(http_times) / 1000 if http_times and len(http_times) == len(unique) else None,
        "http_elapsed_measured_requests": len(http_times),
        "effective_usd": sum(c["effective_usd"] for c in costs)
        if all(c["effective_usd"] is not None for c in costs)
        else None,
        "known_partial_usd": sum(c["effective_usd"] for c in costs if c["effective_usd"] is not None),
        "unknown_cost_requests": sum(c["effective_usd"] is None for c in costs),
        "source_conservation": True,
        "limits": "Authored DEV only; candidate ceiling is not achieved selection. "
        "Missing source-ID gold makes textual ownership a proxy.",
    }


def render_report(summary: dict[str, Any]) -> str:
    """Render all fixed cohort denominators beside costs and metric limitations."""
    first = next(iter(summary["cohorts"].values()))
    lines = [
        "# Frozen rolling candidate admission",
        "",
        (
            f"All {first['pages']} DEV pages remain in each cohort: "
            f"{first['native_zero_call_pages']} native vector routes use zero model calls; "
            f"{first['pages'] - first['native_zero_call_pages']} pages require admission."
        ),
        "",
        "| Model / arm | Borderless exact | Prose false table | Controls exact | Unresolved borderless | Unresolved prose |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, cohort in summary["cohorts"].items():
        slices = cohort["slices"]
        lines.append(
            f"| {key} | {slices['borderless']['exact_page']}/{slices['borderless']['pages']} | "
            f"{slices['prose']['false_positive_page']}/{slices['prose']['pages']} | "
            f"{slices['ruled-control']['exact_page']}/{slices['ruled-control']['pages']} | "
            f"{slices['borderless']['unresolved_or_unmeasured']}/{slices['borderless']['pages']} | "
            f"{slices['prose']['unresolved_or_unmeasured']}/{slices['prose']['pages']} |"
        )
    lines += [
        "",
        "| Model / arm | Intended borderless values | Intended borderless words | Source IDs conserved |",
        "| --- | ---: | ---: | --- |",
    ]
    for key, cohort in summary["cohorts"].items():
        positive = cohort["slices"]["borderless"]
        conserved = all(row["conservation"] for row in cohort["rows"])
        lines.append(
            f"| {key} | {positive['owned_values']}/{positive['expected_values']} | "
            f"{positive['owned_words']}/{positive['expected_words']} | {conserved} |"
        )
    lines += [
        "",
        (
            f"HTTP median ms: {summary['http_elapsed_median_ms']}; "
            f"complete summed HTTP seconds: {summary['http_elapsed_total_seconds']}; "
            f"elapsed measurements: {summary['http_elapsed_measured_requests']} requests. "
            "Missing elapsed measurements remain unmeasured."
        ),
        (
            f"Unique retained requests: {summary['unique_requests']}; "
            f"complete effective USD: {summary['effective_usd']}; "
            f"known partial USD: {summary['known_partial_usd']}; "
            f"unknown-cost requests: {summary['unknown_cost_requests']}."
        ),
        "",
        (
            "Positive provider charges take precedence; zero/missing charges use catalog token rates when complete. "
            "Reservations are admission accounting. Missing prices/tokens remain unknown. "
            "API elapsed and CPU preparation remain separate."
        ),
        "",
        (
            "Source IDs are conserved by every selection, including abstention. "
            "Textual slot ownership uses authored silver references; "
            "it is not independently annotated source-ID gold. "
            "Candidate coverage and automatic admission are distinct. "
            "No model confidence is calibrated correctness; no real-world or heldout claim."
        ),
        "",
    ]
    prep = summary.get("preparation")
    if prep:
        lines += [
            (
                f"CPU preparation: wall {prep['wall_seconds']:.3f}s; CPU {prep['cpu_seconds']:.3f}s; "
                f"peak RSS {prep['peak_rss_bytes']} bytes. Measurement: {prep['measurement']}."
            ),
            "",
        ]
    return "\n".join(lines)


def run(directory: Path, targets_path: Path, client: Any, *, report_path: Path | None = None) -> dict[str, Any]:  # noqa: C901
    """Execute only explicitly requested frozen requests, stopping each model on its first failure."""
    manifest = verify(directory)
    with exclusive_lock(client.ledger.parent / "run.lock"):
        result_path = directory / "hosted-results.json"
        retained = json.loads(result_path.read_bytes()) if result_path.exists() else {"calls": [], "stopped_models": []}
        calls, stopped = retained["calls"], set(retained["stopped_models"])
        prior = _entries(client)
        for entry in prior:
            if entry.get("tag", "").startswith(TAG_PREFIX) and not entry.get("response_file"):
                stopped.add(entry.get("requested_model"))
        done = {r["sha256"] for r in calls}
        prices_path = client.ledger.parent / "langfuse/catalog-prices.json"
        catalog = json.loads(prices_path.read_bytes()) if prices_path.exists() else {"prices": {}}
        budget_stopped = False
        for record in manifest["records"]:
            if (
                record["route"] != "hosted_admission"
                or record["sha256"] in done
                or record["model"] in stopped
                or budget_stopped
            ):
                continue
            raw = (directory / record["request"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != record["sha256"]:
                raise ValueError("Frozen request changed after initial verification")
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
            checkpoint(
                result_path,
                {
                    "calls": calls,
                    "stopped_models": sorted(stopped),
                    "tag_prefix": TAG_PREFIX,
                    "wave_limit_usd": WAVE_LIMIT,
                },
            )
            try:
                if known is not None and not known.get("response_file"):
                    raise RuntimeError("Prior identical request failed; no retry")  # noqa: TRY301
                response = client.request(
                    body, tag=f"{TAG_PREFIX}{record['model']}/{record['arm']}/{record['id']}", max_body_bytes=750_000
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
                    row.update(entry=failed, usage={}, http_elapsed_ms=failed.get("elapsed_ms"))
                    row["cost"] = request_cost(failed, {}, catalog.get("prices", {}).get(record["model"], {}))
                stopped.add(record["model"])
            checkpoint(
                result_path,
                {
                    "calls": calls,
                    "stopped_models": sorted(stopped),
                    "tag_prefix": TAG_PREFIX,
                    "wave_limit_usd": WAVE_LIMIT,
                },
            )
        summary = evaluate(directory, targets_path, calls)
        summary.update(
            tag_prefix=TAG_PREFIX,
            wave_limit_usd=WAVE_LIMIT,
            stopped_models=sorted(stopped),
            budget_stopped=budget_stopped,
            frozen_manifest_sha256=hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
            catalog_provenance=catalog,
            preparation={k: manifest[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")},
            code_sha256={
                str(p.name): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (
                    Path(__file__),
                    Path(__file__).with_name("rolling_rows.py"),
                    Path(__file__).with_name("decision_hosted.py"),
                )
            },
        )
        checkpoint(directory / "evaluation.json", summary)
        if report_path:
            report_path.write_text(render_report(summary))
        return summary


def main() -> None:
    """Prepare by default; network access requires explicit --run-hosted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--models", nargs="+", default=list(MODELS))
    parser.add_argument("--arms", nargs="+", choices=["text", "image512"], default=["text", "image512"])
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report", type=Path, default=ROOT / "bench/results/rolling-admission.md")
    args = parser.parse_args()
    if not (args.directory / "manifest.json").exists():
        if args.source is None or args.candidates is None:
            parser.error("Preparation requires --source and --candidates")
        print(
            json.dumps(
                freeze_admission(args.source, args.candidates, args.directory, args.models, arms=tuple(args.arms)),
                indent=2,
            )
        )
    verify(args.directory)
    if args.run_hosted:
        if args.targets is None:
            parser.error("Hosted evaluation requires --targets after source requests are frozen")
        result = run(args.directory, args.targets, DecisionClient(), report_path=args.report)
        print(
            json.dumps(
                {k: result[k] for k in ("unique_requests", "effective_usd", "stopped_models", "budget_stopped")},
                indent=2,
            )
        )
    elif args.targets:
        retained_path = args.directory / "hosted-results.json"
        calls = json.loads(retained_path.read_text())["calls"] if retained_path.exists() else []
        summary = evaluate(args.directory, args.targets, calls)
        manifest = verify(args.directory)
        summary["preparation"] = {
            k: manifest[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")
        }
        checkpoint(args.directory / "offline-evaluation.json", summary)
        args.report.write_text(render_report(summary))


if __name__ == "__main__":
    main()
