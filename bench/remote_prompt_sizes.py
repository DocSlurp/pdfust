"""Source-only fixed prompt by fresh-resolution matrix and verified DEV reporting."""

# ruff: noqa: C901 - explicit complete frozen inventory verification.

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bench.lowlevel_run import score
from bench.remote_image_sizes import verify as verify_fresh
from bench.remote_prompt_packets import (
    VARIANTS,
    _digest,
    _encode,
    _fail,
    _inside,
    _safe,
    assert_prompt_only,
    transform,
)
from bench.remote_prompt_report import aggregate, events, paired, scored_case, verify_sources
from bench.remote_report import _choice, _read

EDGES = (128, 256, 400, 500, 640)
MODELS = ("flash", "clef", "pplx", "intern")
EXPLORATORY_MODELS = ("qwen9",)
SOURCE_COUNT = 24


def selection(provenance: dict[str, Any]) -> list[dict[str, Any]]:
    """Select every source at each predeclared RGB size without reading targets."""
    rows = [row for row in provenance["mapping"] if row["arm"] in {f"fresh-rgb-{edge}" for edge in EDGES}]
    pairs = {(row["source_id"], row["requested_edge"]) for row in rows}
    sources = {row["source_id"] for row in rows}
    if len(sources) != SOURCE_COUNT or len(rows) != SOURCE_COUNT * len(EDGES) or len(pairs) != len(rows):
        _fail("Fresh RGB source/size matrix differs")
    if pairs != {(source, edge) for source in sources for edge in EDGES}:
        _fail("Fresh RGB matrix is incomplete")
    return rows


def prepare(fresh: Path, output: Path) -> dict[str, Any]:
    """Verify all 504 source bodies and rerenders before freezing 480 prompt bodies."""
    fresh, output = _safe(fresh), _safe(output)
    source = verify_fresh(fresh)
    rows = selection(source)
    inventory = {row["id"]: row for row in json.loads(_read(fresh / "manifest.json"))["records"]}
    output.mkdir(parents=True, exist_ok=False)
    records, mapping = [], []
    for row in rows:
        original = inventory[row["id"]]
        body = json.loads(_read(_inside(fresh, original["request_file"])))
        image_file = row["id"] + ".png"
        image = _read(_inside(fresh, original["image_files"][0]))
        (output / image_file).write_bytes(image)
        for variant in VARIANTS:
            projected = transform(body, variant)
            assert_prompt_only(body, projected)
            raw = _encode(projected)
            identity = _digest(_encode([row["id"], variant, _digest(raw)]))[:24]
            request_file = identity + ".json"
            (output / request_file).write_bytes(raw)
            records.append({"id": identity, "request_file": request_file, "image_files": [image_file]})
            mapping.append(
                {
                    **row,
                    "fresh_id": row["id"],
                    "id": identity,
                    "variant": variant,
                    "fresh_request_sha256": row["projected_request_sha256"],
                    "projected_request_sha256": _digest(raw),
                    "image_file": image_file,
                    "state_sha256": _digest(_encode(projected["state"])),
                }
            )
    raw_manifest = _encode({"records": records})
    (output / "manifest.json").write_bytes(raw_manifest)
    provenance = {
        "schema": 1,
        "experiment": "native-prompt-resolution-screen",
        "fresh_directory": str(fresh),
        "fresh_manifest_sha256": _digest(_read(fresh / "manifest.json")),
        "fresh_provenance_sha256": _digest(_read(fresh / "provenance.json")),
        "historical_fresh_builder_sha256": source["builder_sha256"],
        "worker_manifest_sha256": _digest(raw_manifest),
        "edges": list(EDGES),
        "models": list(MODELS),
        "variant_definitions": VARIANTS,
        "source_count": SOURCE_COUNT,
        "body_count": len(records),
        "source_policy": "All 504 fresh sources verified; RGB five sizes; all four approved prompts; no scorer access.",
        "mapping": mapping,
    }
    (output / "provenance.json").write_bytes(_encode(provenance))
    return provenance


def verify(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify all 504 again and admit only exact approved prompt projections."""
    directory = _safe(directory)
    provenance = json.loads(_read(directory / "provenance.json"))
    fresh = _safe(Path(provenance["fresh_directory"]))
    source = verify_fresh(fresh)
    for key, value in (("edges", list(EDGES)), ("models", list(MODELS)), ("variant_definitions", VARIANTS)):
        if provenance[key] != value:
            _fail("Predeclared prompt-resolution treatment differs")
    for filename, key in (("manifest.json", "fresh_manifest_sha256"), ("provenance.json", "fresh_provenance_sha256")):
        if _digest(_read(fresh / filename)) != provenance[key]:
            _fail("Fresh source freeze hash differs")
    if provenance["historical_fresh_builder_sha256"] != source["builder_sha256"]:
        _fail("Historical renderer provenance differs")
    selected = selection(source)
    manifest_raw = _read(directory / "manifest.json")
    if _digest(manifest_raw) != provenance["worker_manifest_sha256"]:
        _fail("Prompt-resolution manifest hash differs")
    manifest = json.loads(manifest_raw)
    expected = [(row, variant) for row in selected for variant in VARIANTS]
    if (
        set(manifest) != {"records"}
        or len(manifest["records"]) != len(expected)
        or len(provenance["mapping"]) != len(expected)
    ):
        _fail("Prompt-resolution inventory differs")
    original = {row["id"]: row for row in json.loads(_read(fresh / "manifest.json"))["records"]}
    admitted = {}
    for record, entry, (row, variant) in zip(manifest["records"], provenance["mapping"], expected, strict=True):
        body = json.loads(_read(_inside(fresh, original[row["id"]]["request_file"])))
        raw = _read(_inside(directory, record["request_file"]))
        projected = json.loads(raw)
        assert_prompt_only(body, projected)
        identity = _digest(_encode([row["id"], variant, _digest(raw)]))[:24]
        image_file = row["id"] + ".png"
        expected_entry = {
            **row,
            "fresh_id": row["id"],
            "id": identity,
            "variant": variant,
            "fresh_request_sha256": row["projected_request_sha256"],
            "projected_request_sha256": _digest(raw),
            "image_file": image_file,
            "state_sha256": _digest(_encode(projected["state"])),
        }
        if entry != expected_entry or raw != _encode(transform(body, variant)):
            _fail("Prompt projection/provenance differs")
        if (
            record != {"id": identity, "request_file": identity + ".json", "image_files": [image_file]}
            or identity in admitted
        ):
            _fail("Prompt record schema/identity differs")
        if _read(directory / image_file) != _read(_inside(fresh, original[row["id"]]["image_files"][0])):
            _fail("Prompt source image differs")
        admitted[identity] = {**entry, "sha256": _digest(raw)}
    if provenance["source_count"] != SOURCE_COUNT or provenance["body_count"] != len(expected):
        _fail("Prompt source count differs")
    return source, admitted


def _case(event: dict[str, Any] | None, observation: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    if event is None or event.get("status") != "ok" or event.get("response", {}).get("backend") != "stock-vllm-json":
        return scored_case(event, observation, target)
    try:
        parsed = _choice(event["response"])
        parsed["tie_abstention"] = False
        return {
            "status": "ok",
            "expected": target["expected"],
            "parsed": parsed,
            "score": score(observation, target, parsed["choice"]),
            "event": event,
        }
    except (ValueError, TypeError, KeyError) as error:
        return {"status": "schema_error", "expected": target["expected"], "error": str(error), "event": event}


def _metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = aggregate(cases)
    if any(case.get("event", {}).get("response", {}).get("backend") == "stock-vllm-json" for case in cases):
        # Concurrent HTTP attempt CPU windows overlap; server allocation is outside client scope.
        result.update(
            tie_abstentions=None,
            cuda_peak_allocated_bytes=None,
            cuda_peak_reserved_bytes=None,
            inference_cpu_seconds=None,
            inference_cpu_seconds_known_component=None,
            per_attempt_wall_scope="HTTP request latency; overlapping requests cannot be summed as batch elapsed",
            model_resources="unmeasured by HTTP client; separate server process-tree/device monitoring",
        )
    return result


def evaluate(
    directory: Path,
    runs: dict[str, Path],
    baselines: dict[str, Path] | None = None,
    *,
    allow_exploratory_stock: bool = False,
) -> dict[str, Any]:
    """Verify every source/result before opening local authored DEV targets."""
    source, admitted = verify(directory)
    allowed = {*MODELS, *(EXPLORATORY_MODELS if allow_exploratory_stock else ())}
    if set(runs) - allowed or (baselines is not None and set(baselines) != set(runs)):
        _fail("Model comparison differs from predeclared native models")
    originals, observations = verify_sources(
        Path(source["source_directory"]), Path(source["source_index"]), Path(source["source_packets"]) / "manifest.json"
    )
    returned = {model: events(_safe(path), admitted) for model, path in runs.items()}
    fresh_inventory = {row["id"]: {**row, "sha256": row["projected_request_sha256"]} for row in source["mapping"]}
    baseline_events = {model: events(_safe(path), fresh_inventory) for model, path in (baselines or {}).items()}
    # First scorer-reference access after all source projections and returned hashes were verified.
    source_dir = Path(source["source_directory"])
    manifest = json.loads(_read(source_dir / "manifest.json"))
    target_raw = _read(source_dir / "private-targets.json")
    if _digest(target_raw) != manifest["targets_sha256"]:
        _fail("DEV target hash differs")
    targets = {row["id"]: row for row in json.loads(target_raw)}
    models = {}
    for model, (attempts, status) in returned.items():
        groups = {}
        for edge in EDGES:
            for variant in VARIANTS:
                rows = [row for row in admitted.values() if row["requested_edge"] == edge and row["variant"] == variant]
                cases, before = [], []
                for row in rows:
                    page = originals[row["source_id"]]["row"]["page_ids"][0]
                    cases.append(_case(attempts.get(row["id"]), observations[page], targets[page]))
                    if model in baseline_events:
                        before.append(
                            _case(baseline_events[model][0].get(row["fresh_id"]), observations[page], targets[page])
                        )
                groups[f"rgb-{edge}/{variant}"] = {"metrics": _metrics(cases)}
                if before:
                    groups[f"rgb-{edge}/{variant}"].update(baseline=_metrics(before), paired=paired(before, cases))
        models[model] = {"groups": groups, "status": status, "exploratory": model in EXPLORATORY_MODELS}
    return {
        "experiment": "native-prompt-resolution-screen",
        "models": models,
        "scope": "24 authored DEV regions, repeated across five sizes and four fixed prompts; not independent pages",
        "packet_provenance_sha256": _digest(_read(directory / "provenance.json")),
    }


def markdown(report: dict[str, Any]) -> str:
    """Render planned denominators and matched fresh-original baselines if supplied."""
    lines = [
        "# Remote GPU prompt × resolution screen",
        "",
        report["scope"],
        "",
        (
            "All 504 fresh source packets and exact prompt transformations were verified before local DEV scoring. "
            "The four prompts, five RGB sizes and four native models were predeclared. "
            "No case-specific prompts were used."
        ),
        "",
        (
            "| Model / treatment | Valid/planned | Known correct | Ambiguous abstention | Known abstentions | "
            "Exact partition | Conserved | Wall s | CPU s | Peak RSS MiB |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, result in report["models"].items():
        for group, entry in result["groups"].items():
            m = entry["metrics"]

            def number(key: str, m: dict[str, Any] = m) -> str:
                value = m[key]
                return "unknown" if value is None else f"{value:.3f}"

            rss = m["peak_rss_bytes"]
            lines.append(
                f"| {model} / {group} | {m['completed']}/{m['planned']} | "
                f"{m['known_correct']}/{m['known_denominator']} | "
                f"{m['ambiguous_abstentions']}/{m['ambiguous_denominator']} | {m['known_abstentions']} | "
                f"{m['partition_exact']}/{m['planned']} | {m['conservation']}/{m['completed']} | "
                f"{number('inference_wall_seconds')} | {number('inference_cpu_seconds')} | "
                f"{'unknown' if rss is None else f'{rss / 2**20:.1f}'} |"
            )
    lines += [
        "",
        "| Model / treatment | Fresh-original known correct | Known gains/losses | Ambiguity gains/losses | Unpaired |",
        "|---|---:|---:|---:|---:|",
    ]
    for model, result in report["models"].items():
        for group, entry in result["groups"].items():
            if "paired" in entry:
                b, p = entry["baseline"], entry["paired"]
                lines.append(
                    f"| {model} / {group} | {b['known_correct']}/{b['known_denominator']} | "
                    f"{p['known_gains']}/{p['known_losses']} | "
                    f"{p['abstention_gains']}/{p['abstention_losses']} | {p['unpaired']} |"
                )
    lines += [
        "",
        (
            "Qwen9, when explicitly admitted, is an exploratory extension beyond the four predeclared native models. "
            "Stock labels have no native probabilities or tie calibration. HTTP latency overlaps at concurrency8. "
            "Its sum is not batch elapsed. Client CPU/RSS and CUDA metrics cannot price the separate model server."
        ),
        "",
        (
            "Missing, failed and malformed responses retain planned denominators. Resource measurements cover "
            "the serial native inference process; GPU device-wide utilization is separate. Absent matched "
            "fresh-original runs provide no isolated prompt-effect estimate. Full grouping metrics, failures, "
            "candidate oracle, tie abstentions and CUDA allocator peaks remain in the JSON report."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Prepare, verify or score bounded local artifacts without inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--fresh", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("verify")
    check.add_argument("--packets", type=Path, required=True)
    report = commands.add_parser("report")
    report.add_argument("--packets", type=Path, required=True)
    report.add_argument("--run", action="append", required=True, help="model=directory")
    report.add_argument("--baseline", action="append", default=[], help="model=fresh-original-directory")
    report.add_argument("--allow-exploratory-stock", action="store_true")
    report.add_argument("--json-output", type=Path, required=True)
    report.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        provenance = prepare(args.fresh, args.output)
        print(json.dumps({"body_count": provenance["body_count"], "output": str(args.output)}))
    elif args.command == "verify":
        _, inventory = verify(args.packets)
        print(json.dumps({"verified": len(inventory)}))
    else:
        runs = {key: Path(value) for key, value in (item.split("=", 1) for item in args.run)}
        baselines = {key: Path(value) for key, value in (item.split("=", 1) for item in args.baseline)}
        result = evaluate(args.packets, runs, baselines or None, allow_exploratory_stock=args.allow_exploratory_stock)
        _safe(args.json_output).write_bytes(_encode(result))
        _safe(args.markdown_output).write_text(markdown(result))


if __name__ == "__main__":
    main()
