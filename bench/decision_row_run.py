"""Freeze and optionally run the prespecified bounded R001 row-decision pilot."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from statistics import mean
from typing import Any

from bench.decision_context_cases import context_cases
from bench.decision_hosted import ARTIFACTS, RESERVATION, DecisionClient, accounted_cost, checkpoint, exclusive_lock
from bench.decision_image_matrix import VariantCache
from bench.decision_rows import build_request, score_response
from bench.decision_rows import pilot_case as adapt_case
from bench.reprice_model_rates import request_cost
from bench.silver import rss_bytes

MODELS = ("openai/gpt-6-luna-decisions", "perplexity/pplx-decider-v1.1-27b")
ARMS = ("geometry", "image128", "image512", "image1200")
WAVE_LIMIT = 0.50
MAX_BODY_BYTES = 750_000
DEFAULT_DIRECTORY = ARTIFACTS / "row-decisions-r001"
DEFAULT_REPORT = Path("bench/results/row-decisions-r001.md")


def encode(body: dict[str, Any]) -> bytes:
    """Use the shared client's exact encoding for stable replay identity."""
    return json.dumps(body, separators=(",", ":")).encode()


def selected_indices(cases: list[dict[str, Any]], *, all30: bool = False) -> list[int]:
    """Cover every template once, rotating vocabulary families without looking at gold."""
    if all30:
        return list(range(len(cases)))
    families = list(dict.fromkeys(case["family"] for case in cases))
    variants = sorted({case["id"].rsplit("-", 1)[1] for case in cases})
    return [
        next(
            index
            for index, case in enumerate(cases)
            if case["family"] == families[offset % len(families)] and case["id"].rsplit("-", 1)[1] == variant
        )
        for offset, variant in enumerate(variants)
    ]


def prepare(  # noqa: PLR0913
    directory: Path,
    models: list[str],
    arms: list[str],
    *,
    all30: bool = False,
    scope: str = "page",
    prices_path: Path | None = None,
) -> dict[str, Any]:
    """Freeze source candidates, scorer-only gold and every body before hosted opt-in."""
    if scope not in {"page", "region"}:
        message = "R001 image scope must be page or region"
        raise ValueError(message)
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if (
            manifest["models"] != models
            or manifest["arms"] != arms
            or manifest["all30"] != all30
            or manifest["scope"] != scope
        ):
            message = "Existing R001 freeze has different configuration; use a new directory"
            raise ValueError(message)
        verify_manifest(directory, manifest)
        return manifest
    start, cpu = time.perf_counter(), time.process_time()
    cases = context_cases()
    indices = selected_indices(cases, all30=all30)
    cache = VariantCache(directory / "images")
    records = []
    targets = {}
    for index in indices:
        case = cases[index]
        pilot = adapt_case(case)
        original = pilot["original_case"]
        # The scorer needs source-backed assemblies, not the raw PDF or unrelated provenance.
        private = {key: value for key, value in pilot.items() if key != "original_case"}
        private["original_case"] = {"evidence": original["evidence"], "gold": original["gold"]}
        private["local_to_original_source_ids"] = {
            str(key): value for key, value in private["local_to_original_source_ids"].items()
        }
        targets[str(index)] = private
        for arm in arms:
            image = (
                None
                if arm == "geometry"
                else cache.make_variant(
                    case["pdf_bytes"],
                    None if scope == "page" else case["evidence"]["current_region"],
                    edge=int(arm.removeprefix("image")),
                    mode="rgb8",
                )
            )
            for model in models:
                body = build_request(pilot["input"], model, image=image)
                data = encode(body)
                key = hashlib.sha256(data).hexdigest()
                path = directory / f"request-{key}.json"
                path.write_bytes(data)
                records.append(
                    {
                        "case_index": index,
                        "case_id": case["id"],
                        "model": model,
                        "arm": arm,
                        "source_sha256": pilot["source_sha256"],
                        "request_sha256": key,
                        "request_file": path.name,
                        "request_bytes": len(data),
                        "image": {k: v for k, v in image.items() if k != "data"} if image else None,
                    }
                )
    prices = json.loads(prices_path.read_text()) if prices_path is not None and prices_path.exists() else {}
    paths = [
        Path(__file__),
        Path("bench/decision_rows.py"),
        Path("bench/decision_context_cases.py"),
        Path("bench/decision_image_matrix.py"),
        Path("bench/decision_records.py"),
        Path("bench/reprice_model_rates.py"),
    ]
    manifest = {
        "schema": 1,
        "experiment": "R001",
        "models": models,
        "arms": arms,
        "all30": all30,
        "scope": scope,
        "indices": indices,
        "targets": targets,
        "records": records,
        "selection": "Prespecified one representative per template, vocabulary families rotating in source order; no gold selection",
        "prices": prices.get("prices", {}),
        "pricing_provenance": {k: v for k, v in prices.items() if k != "prices"},
        "code_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "targets_sha256": hashlib.sha256(json.dumps(targets, sort_keys=True).encode()).hexdigest(),
        "preparation": {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "serial CPU current process; perf_counter/process_time; current-exec VmHWM bytes; no sampling",
        },
    }
    checkpoint(manifest_path, manifest)
    return manifest


def verify_manifest(directory: Path, manifest: dict[str, Any]) -> None:
    """Validate all frozen request and private target hashes before credential access."""
    targets_hash = hashlib.sha256(json.dumps(manifest["targets"], sort_keys=True).encode()).hexdigest()
    if targets_hash != manifest["targets_sha256"]:
        message = "R001 private target hash mismatch"
        raise ValueError(message)
    for row in manifest["records"]:
        name = row["request_file"]
        if Path(name).name != name:
            message = "Frozen R001 request escapes artifact directory"
            raise ValueError(message)
        data = (directory / name).read_bytes()
        if len(data) > MAX_BODY_BYTES or hashlib.sha256(data).hexdigest() != row["request_sha256"]:
            message = "R001 frozen request hash or admission mismatch"
            raise ValueError(message)


def wave_admission(entries: list[dict[str, Any]], start: int, limit: float = WAVE_LIMIT) -> None:
    """Refuse crossing the incremental cap, including unknown-charge reservations."""
    if sum(accounted_cost(entry["accounted_usd"]) for entry in entries[start:]) + RESERVATION > limit:
        message = "R001 incremental wave budget exhausted"
        raise RuntimeError(message)


def _ledger(client: Any) -> list[dict[str, Any]]:  # noqa: ANN401
    return json.loads(client.ledger.read_text())["requests"] if client.ledger.exists() else []


def run(directory: Path, manifest: dict[str, Any], *, client: Any = None) -> dict[str, Any]:  # noqa: ANN401, C901, PLR0912
    """Run only on explicit caller opt-in, preserving failures and prior successful scores."""
    verify_manifest(directory, manifest)
    report_path = directory / "results.json"
    report: dict[str, Any] = (
        json.loads(report_path.read_text()) if report_path.exists() else {"schema": 1, "records": []}
    )
    client = DecisionClient() if client is None else client
    wave_path = client.ledger.parent / "row-decisions-r001-wave.json"
    if wave_path.exists():
        wave = json.loads(wave_path.read_text())
    else:
        wave = {"wave_start": report.get("wave_start", len(_ledger(client))), "wave_limit_usd": WAVE_LIMIT}
        checkpoint(wave_path, wave)
    report.update(wave)

    def identity(row: dict[str, Any]) -> tuple[str, str, int]:
        return row["model"], row["arm"], row["case_index"]

    old = {identity(row): row for row in report["records"]}
    stopped = {row["model"] for row in old.values() if row["status"] == "failed"}
    report["records"] = [old.get(identity(row), {**row, "status": "unattempted"}) for row in manifest["records"]]
    checkpoint(report_path, report)
    for position, frozen in enumerate(manifest["records"]):
        previous = old.get(identity(frozen))
        if previous is not None and previous["status"] in {"ok", "failed"}:
            continue
        row = {**frozen, "status": "unattempted"}
        if row["model"] in stopped or report.get("budget_exhausted"):
            row["reason"] = "model stopped after failure" if row["model"] in stopped else "wave budget exhausted"
        else:
            entries = _ledger(client)
            known = next((entry for entry in entries if entry["request_sha256"] == row["request_sha256"]), None)
            try:
                if known is not None and not known.get("response_file"):
                    message = "Previously failed identical R001 request; no retry"
                    raise RuntimeError(message)  # noqa: TRY301
                if known is None:
                    wave_admission(entries, report["wave_start"], report["wave_limit_usd"])
                body = json.loads((directory / row["request_file"]).read_text())
                response = client.request(
                    body, tag=f"R001/{row['model']}/{row['arm']}/{row['case_id']}", max_body_bytes=MAX_BODY_BYTES
                )
                row.update(
                    {
                        "entry": response["entry"],
                        "usage": response["result"].get("usage", {}),
                        "replayed": response["replayed"],
                    }
                )
                score = score_response(manifest["targets"][str(row["case_index"])], response["result"])
                if not score["valid"]:
                    message = "R001 response validation failed: " + score["error"]
                    raise ValueError(message)  # noqa: TRY301
                row.update({"status": "ok", "score": score})
            except (RuntimeError, ValueError, OSError) as error:
                row.update({"status": "failed", "error": str(error)})
                failure = next(
                    (entry for entry in _ledger(client) if entry["request_sha256"] == row["request_sha256"]), None
                )
                if failure is not None:
                    row.setdefault("entry", failure)
                if "wave budget exhausted" in str(error):
                    report["budget_exhausted"] = True
                    row["status"] = "unattempted"
                else:
                    stopped.add(row["model"])
        report["records"][position] = row
        checkpoint(report_path, report)
    return report


def summarize(manifest: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Report source safety and quality separately from deduplicated usage and costs."""
    rows = []
    unique = {row["entry"]["index"]: row for row in report["records"] if "entry" in row}
    costs = [
        request_cost(row["entry"], row.get("usage", {}), manifest["prices"].get(row["model"], {}))
        for row in unique.values()
    ]
    for model in manifest["models"]:
        for arm in manifest["arms"]:
            cohort = [row for row in report["records"] if row["model"] == model and row["arm"] == arm]
            successful = [row for row in cohort if row["status"] == "ok"]
            scores = [row["score"] for row in successful]
            entries = {row["entry"]["index"]: row for row in cohort if "entry" in row}
            arm_costs = [
                request_cost(row["entry"], row.get("usage", {}), manifest["prices"].get(model, {}))
                for row in entries.values()
            ]
            elapsed = sum(row["entry"].get("elapsed_ms", 0) for row in entries.values())
            effective = (
                None
                if not arm_costs or any(c["effective_usd"] is None for c in arm_costs)
                else sum(c["effective_usd"] for c in arm_costs)
            )
            fragments = sum(len(score["selector_by_fragment"]) for score in scores)
            correct = sum(sum(score["selector_by_fragment"].values()) for score in scores)
            oracle_total = sum(len(manifest["targets"][str(row["case_index"])]["input"]["fragments"]) for row in cohort)
            oracle_covered = sum(
                sum(
                    target["expected_assignments"][fragment["id"]] is None
                    or target["expected_assignments"][fragment["id"]] in fragment["allowed_slots"]
                    for fragment in target["input"]["fragments"]
                )
                for row in cohort
                for target in [manifest["targets"][str(row["case_index"])]]
            )
            transmitted = [row for row in successful if not row.get("replayed")]
            rows.append(
                {
                    "model": model,
                    "arm": arm,
                    "inputs": len(cohort),
                    "scored": len(successful),
                    "errors": sum(row["status"] == "failed" for row in cohort),
                    "unattempted": sum(row["status"] == "unattempted" for row in cohort),
                    "fragments": fragments,
                    "correct_fragments": correct,
                    "fragment_accuracy": correct / fragments if fragments else None,
                    "region_exact": sum(score["region_exact"] for score in scores),
                    "record_f1": mean(score["record_f1"] for score in scores) if scores else None,
                    "lost_source": sum(not score["source_conservation"] for score in scores),
                    "unresolved_fragments": sum(
                        sum(value is None for value in score["assignments"].values()) for score in scores
                    ),
                    "candidate_oracle_covered": oracle_covered,
                    "candidate_oracle_total": oracle_total,
                    "input_tokens": sum(
                        row.get("usage", {}).get("input_tokens", row.get("usage", {}).get("prompt_tokens", 0))
                        for row in entries.values()
                    ),
                    "output_tokens": sum(
                        row.get("usage", {}).get("output_tokens", row.get("usage", {}).get("completion_tokens", 0))
                        for row in entries.values()
                    ),
                    "api_elapsed_ms": elapsed,
                    "request_bytes": sum(row["request_bytes"] for row in entries.values()),
                    "effective_usd": effective,
                    "cost_estimated": any(c["basis"] == "catalog estimate" for c in arm_costs),
                    "unique_requests": len(entries),
                    "replayed_inputs": sum(row.get("replayed", False) for row in successful),
                    "pages_per_usd": len(successful) / effective if effective is not None and effective > 0 else None,
                    "transmitted_pages_per_api_minute": len(transmitted) * 60_000 / elapsed if elapsed > 0 else None,
                }
            )
    return {
        "rows": rows,
        "costs": costs,
        "unique_requests": len(unique),
        "effective_usd": None
        if not costs or any(c["effective_usd"] is None for c in costs)
        else sum(c["effective_usd"] for c in costs),
    }


def write_report(directory: Path, path: Path) -> dict[str, Any]:
    """Write a compact result table without raw requests, images or responses."""
    manifest = json.loads((directory / "manifest.json").read_text())
    report = json.loads((directory / "results.json").read_text())
    summary = summarize(manifest, report)
    lines = [
        "# R001 row-at-a-time DEV pilot",
        "",
        "Ten correlated templates across three vocabulary families. The prespecified default rotates vocabulary across templates; --all30 adds correlated repetitions. These observations do not establish real-world extraction quality.",
        "",
        "Source-backed headers are fixed. Fragment choices form complete records; invalid responses return no assembly. Candidate oracle coverage is a harness ceiling, separate from fragment selection and record correctness. Full-source targets include convention notes omitted from region images; transformed-image evidence exactness is not validated.",
        "",
        f"Image scope: `{manifest['scope']}`. Full-page images expose source convention notes; region crops omit them. Match scope and resolution before comparing R001 with R002.",
        "",
        f"Selected case indices: `{manifest['indices']}`. Unique charged/replayed request identities: {summary['unique_requests']}; effective USD: {summary['effective_usd']}.",
        "",
        "Positive provider-reported charges take precedence; other costs use retained token/catalog estimates with cache assumptions preserved in JSON. Reservations remain budget admissions. Local replay is not a new provider request. API-only pages/min excludes local preprocessing and is not end-to-end throughput. Lost-source counts cover validated outputs; failures and unattempted inputs are reported separately.",
        "",
        "| Model | Arm | Inputs / scored | Errors / unattempted | Fragment accuracy | Exact regions | Record F1 | Lost source | Unassigned fragments | Oracle fragments | Tokens in / out | Effective USD | Pages/USD | API-only pages/min |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["rows"]:

        def fmt(key: str, digits: int = 3, values: dict[str, Any] = row) -> str:
            value = values[key]
            return "unknown" if value is None else f"{value:.{digits}f}"

        cost = ("~" if row["cost_estimated"] else "") + fmt("effective_usd", 6)
        lines.append(
            f"| {row['model']} | {row['arm']} | {row['inputs']} / {row['scored']} | {row['errors']} / {row['unattempted']} | {fmt('fragment_accuracy')} | {row['region_exact']} | {fmt('record_f1')} | {row['lost_source']} | {row['unresolved_fragments']} | {row['candidate_oracle_covered']} / {row['candidate_oracle_total']} | {row['input_tokens']} / {row['output_tokens']} | {cost} | {fmt('pages_per_usd', 0)} | {fmt('transmitted_pages_per_api_minute', 1)} |"
        )
    lines.extend(["", "Preparation resources: `" + json.dumps(manifest["preparation"], sort_keys=True) + "`.", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    checkpoint(directory / "summary.json", summary)
    return summary


def main() -> None:
    """Prepare without credentials and require explicit hosted opt-in for paid inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--all30", action="store_true")
    parser.add_argument("--scope", choices=["page", "region"], default="page")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--prices", type=Path, default=ARTIFACTS / "langfuse/catalog-prices.json")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    if args.report_only:
        write_report(args.directory, args.report)
        return
    manifest = prepare(
        args.directory, args.models, args.arms, all30=args.all30, scope=args.scope, prices_path=args.prices
    )
    print(
        json.dumps(
            {"requests": len(manifest["records"]), "indices": manifest["indices"], "directory": str(args.directory)}
        )
    )
    if args.run_hosted:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(ARTIFACTS / "run.lock"):
            run(args.directory, manifest)
        write_report(args.directory, args.report)


if __name__ == "__main__":
    main()
