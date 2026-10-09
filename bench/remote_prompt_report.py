"""Verify approved prompt-only projections before root-local authored DEV scoring.

No inference or reference transfer occurs. Missing/failed responses remain in
planned denominators. Paired comparisons require valid responses on both sides.
"""

# ruff: noqa: C901, PLR0912, PLR0913, PLR0917, PLR2004 - explicit bounded artifact verification.
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from bench.lowlevel_run import parse_response, score
from bench.remote_prompt_packets import VARIANTS, assert_prompt_only, transform
from bench.remote_report import _dev, _json, _jsonl, _path, _read, _verified


def _fail(message: str) -> None:
    raise ValueError(message)


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_sources(source: Path, index_path: Path, packets: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify L015 inventory, PDFs, observations, original requests and crops."""
    manifest = _json(source / "manifest.json")
    if manifest.get("experiment") != "L015":
        _fail("Expected frozen L015 source")
    index = _json(index_path)
    frozen = {row["request"]: row for row in manifest["records"]}
    pages = {row["id"]: row for row in manifest["pages"]}
    inventory = _json(packets)
    if set(inventory) != {"records"}:
        _fail("Original worker manifest differs from source-only schema")
    staged = {row["id"]: row for row in inventory["records"]}
    if len(staged) != len(inventory["records"]) or len(index) != len(staged):
        _fail("Original staged/source inventory differs")
    verified: dict[str, Any] = {}
    observations = {}
    for row in index:
        original_row = frozen[row["request"]]
        for key in ("sha256", "model", "arm", "page_ids", "image_file", "image_sha256"):
            if row[key] != original_row[key]:
                _fail("Source index differs from frozen L015 inventory")
        if row["id"] in verified or len(row["page_ids"]) != 1:
            _fail("Source index identity is duplicated or nonsingleton")
        raw = _verified(_path(source, row["request"]), row["sha256"])
        image = _verified(_path(source, row["image_file"]), row["image_sha256"])
        stage = staged[row["id"]]
        if set(stage) != {"id", "request_file", "image_files"} or len(stage["image_files"]) != 1:
            _fail("Original worker record schema differs")
        if _read(_path(packets.parent, stage["request_file"])) != raw:
            _fail("Original staged request differs from L015")
        if _read(_path(packets.parent, stage["image_files"][0])) != image:
            _fail("Original staged image differs from L015")
        page_id = row["page_ids"][0]
        if page_id not in observations:
            page = pages[page_id]
            _verified(_path(source, page["source_file"]), page["source_sha256"])
            observations[page_id] = json.loads(
                _verified(_path(source, page["observation_file"]), page["observation_sha256"])
            )
        verified[row["id"]] = {
            "row": row,
            "body": json.loads(raw),
            "raw": raw,
            "image": image,
            "stage": stage,
            "sha256": row["sha256"],
        }
    if set(verified) != set(staged):
        _fail("Original source ID inventory differs")
    return verified, observations


def verify_prompts(directory: Path, packets: Path, originals: dict[str, Any]) -> dict[str, Any]:
    """Admit only the exact frozen transform and its unchanged source evidence."""
    provenance = _json(directory / "provenance.json")
    manifest_raw = _verified(directory / "manifest.json", provenance["worker_manifest_sha256"])
    _verified(packets, provenance["source_manifest_sha256"])
    if provenance["variant_definitions"] != VARIANTS or provenance.get("include_original"):
        _fail("Prompt variants differ from approved definitions")
    selected = list(originals)[:24]
    if [row["id"] for row in _json(packets)["records"][:24]] != selected:
        _fail("Prompt source order differs from original first24")
    if len(selected) != 24 or any(originals[key]["row"]["arm"] != "fresh-rgb-512" for key in selected):
        _fail("Prompt screen requires first24 original RGB512 sources")
    manifest = json.loads(manifest_raw)
    if set(manifest) != {"records"}:
        _fail("Prompt worker manifest must contain only records")
    staged = {row["id"]: row for row in manifest["records"]}
    mapping = provenance["mapping"]
    if len(mapping) != 24 * len(VARIANTS) or len(staged) != len(mapping):
        _fail("Prompt screen must retain four variants times24 sources")
    verified = {}
    pairs = set()
    for entry in mapping:
        source_id, variant = entry["source_id"], entry["variant"]
        if source_id not in selected or variant not in VARIANTS or (source_id, variant) in pairs:
            _fail("Prompt selection/variant identity differs")
        pairs.add((source_id, variant))
        original = originals[source_id]
        stage = staged[entry["id"]]
        if set(stage) != {"id", "request_file", "image_files"} or stage["image_files"] != [entry["image_file"]]:
            _fail("Prompt worker image identity differs")
        if entry["source_request_file"] != original["stage"]["request_file"]:
            _fail("Prompt original request path differs")
        if entry["source_image_file"] != original["stage"]["image_files"][0]:
            _fail("Prompt original image path differs")
        if entry["source_request_sha256"] != _digest(original["raw"]):
            _fail("Prompt original request hash differs")
        if entry["image_pixels"] != original["row"]["pixels"]:
            _fail("Prompt recorded pixels differ from frozen L015")
        image = _verified(_path(directory, entry["image_file"]), entry["image_sha256"])
        if image != original["image"]:
            _fail("Prompt image differs from verified L015 source")
        raw = _verified(_path(directory, stage["request_file"]), entry["projected_request_sha256"])
        body = json.loads(raw)
        assert_prompt_only(original["body"], body)
        if body != transform(original["body"], variant):
            _fail("Prompt wording differs from exact approved transform")
        state = json.dumps(body["state"], separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
        if entry["state_sha256"] != _digest(state):
            _fail("Prompt literal state hash differs")
        verified[entry["id"]] = {"source_id": source_id, "variant": variant, "sha256": _digest(raw)}
    if set(verified) != set(staged):
        _fail("Prompt manifest identity differs")
    return verified


def events(directory: Path, verified: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate every returned attempt/hash before scorer-reference admission."""
    status = _json(directory / "status.json")
    path = directory / "attempts.jsonl"
    rows, tail = (
        _jsonl(path, allow_incomplete_tail=status.get("status") != "complete") if path.exists() else ([], False)
    )
    started, completed = set(), {}
    for row in rows:
        identity = row["id"]
        if identity not in verified:
            _fail("Returned ID is outside verified source inventory")
        if row["event"] == "attempt_started":
            if identity in started:
                _fail("Duplicate source attempt/retry")
            started.add(identity)
        elif row["event"] == "attempt_completed":
            if identity not in started or identity in completed:
                _fail("Completion lacks unique prior start")
            if row.get("request_sha256") != verified[identity]["sha256"]:
                _fail("Returned request hash differs from verified bytes")
            completed[identity] = row
        else:
            _fail("Unknown returned event")
    return completed, {
        "worker_status": status,
        "started": len(started),
        "completed": len(completed),
        "incomplete_tail": tail,
    }


def scored_case(event: dict[str, Any] | None, observation: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Keep malformed/failing/missing responses explicit without reducing denominators."""
    if event is None:
        return {"status": "missing", "expected": target["expected"]}
    if event.get("status") != "ok":
        return {"status": "worker_error", "expected": target["expected"], "event": event}
    try:
        answer = parse_response(event["response"], 1)[0]
        return {
            "status": "ok",
            "expected": target["expected"],
            "parsed": answer,
            "score": score(observation, target, answer["choice"]),
            "event": event,
        }
    except (ValueError, TypeError, KeyError) as error:
        return {"status": "schema_error", "expected": target["expected"], "error": str(error), "event": event}


def aggregate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate complete quality denominators and explicitly scoped measurements."""
    good = [case for case in cases if case["status"] == "ok"]
    known = [case for case in cases if case["expected"] != "unresolved"]
    ambiguous = [case for case in cases if case["expected"] == "unresolved"]
    result = {
        "planned": len(cases),
        "known_denominator": len(known),
        "ambiguous_denominator": len(ambiguous),
        "completed": len(good),
        "known_correct": sum(case["score"]["answerable"] and case["score"]["choice_correct"] for case in good),
        "choice_correct": sum(case["score"]["choice_correct"] for case in good),
        "partition_exact": sum(case["score"]["description_partition_exact"] for case in good),
        "ambiguous_abstentions": sum(case["score"]["ambiguous_abstention"] for case in good),
        "known_abstentions": sum(
            case["parsed"]["choice"] == "unresolved" and case["score"]["answerable"] for case in good
        ),
        "tie_abstentions": sum(case["parsed"]["tie_abstention"] for case in good),
        "conservation": sum(case["score"]["output"]["conservation"] for case in good),
        "candidate_oracle": sum(case["score"]["candidate_oracle"] for case in good),
        "failures": {
            kind: sum(case["status"] == kind for case in cases) for kind in ("missing", "worker_error", "schema_error")
        },
    }
    measured = [case for case in cases if "event" in case]
    for field in ("inference_wall_seconds", "inference_cpu_seconds"):
        values = [case["event"].get(field) for case in measured]
        valid = [
            float(value)
            for value in values
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
        ]
        result[field] = sum(valid) if len(valid) == len(values) == len(cases) else None
        result[field + "_known_component"] = sum(valid)
    result["peak_rss_bytes"] = max((case["event"].get("peak_rss_bytes", 0) for case in good), default=None)
    for key in ("peak_allocated_bytes", "peak_reserved_bytes"):
        values = [case["event"].get("cuda", {}).get(key) for case in good]
        result["cuda_" + key] = max((value for value in values if value is not None), default=None)
    return result


def paired(baseline: list[dict[str, Any]], variant: list[dict[str, Any]]) -> dict[str, int]:
    """Report gains/losses only for matched valid answers, with ambiguity separate."""
    keys = (
        "paired_known",
        "known_gains",
        "known_losses",
        "paired_ambiguous",
        "abstention_gains",
        "abstention_losses",
        "choice_changes",
        "unpaired",
    )
    result = dict.fromkeys(keys, 0)
    for before, after in zip(baseline, variant, strict=True):
        if before["status"] != "ok" or after["status"] != "ok":
            result["unpaired"] += 1
            continue
        result["choice_changes"] += before["parsed"]["choice"] != after["parsed"]["choice"]
        ambiguous = before["expected"] == "unresolved"
        result["paired_ambiguous" if ambiguous else "paired_known"] += 1
        metric = "ambiguous_abstention" if ambiguous else "choice_correct"
        previous, current = before["score"][metric], after["score"][metric]
        result[("abstention" if ambiguous else "known") + "_gains"] += current and not previous
        result[("abstention" if ambiguous else "known") + "_losses"] += previous and not current
    return result


def evaluate(
    source_dir: Path,
    source_index: Path,
    packets: Path,
    prompt_dir: Path,
    runs: dict[str, Path],
    baselines: dict[str, Path],
) -> dict[str, Any]:
    """Verify all models and variants before the first local DEV target read."""
    source, index, original, prompts = map(_dev, (source_dir, source_index, packets, prompt_dir))
    originals, observations = verify_sources(source, index, original)
    prompt_inventory = verify_prompts(prompts, original, originals)
    returned = {}
    for model, path in runs.items():
        if model not in baselines:
            _fail("Every prompt model requires an independent original baseline")
        returned[model] = (events(_dev(path), prompt_inventory), events(_dev(baselines[model]), originals))
    # First scorer-reference access: all source/projection/returned hashes are verified above.
    manifest = _json(source / "manifest.json")
    targets = {
        row["id"]: row for row in json.loads(_verified(source / "private-targets.json", manifest["targets_sha256"]))
    }
    selected = list(originals)[:24]
    models = {}
    for model, ((attempts, status), (base_attempts, base_status)) in returned.items():
        baseline = [
            scored_case(
                base_attempts.get(identity),
                observations[originals[identity]["row"]["page_ids"][0]],
                targets[originals[identity]["row"]["page_ids"][0]],
            )
            for identity in selected
        ]
        variants = {}
        for variant in VARIANTS:
            identities = {
                entry["source_id"]: key for key, entry in prompt_inventory.items() if entry["variant"] == variant
            }
            cases = [
                scored_case(
                    attempts.get(identities[identity]),
                    observations[originals[identity]["row"]["page_ids"][0]],
                    targets[originals[identity]["row"]["page_ids"][0]],
                )
                for identity in selected
            ]
            variants[variant] = {"metrics": aggregate(cases), "paired": paired(baseline, cases)}
        models[model] = {
            "baseline": aggregate(baseline),
            "variants": variants,
            "status": status,
            "baseline_status": base_status,
        }
    return {
        "experiment": "approved-native-prompt-screen",
        "models": models,
        "source_manifest_sha256": _digest(_read(source / "manifest.json")),
        "prompt_provenance_sha256": _digest(_read(prompts / "provenance.json")),
        "scope": "24 authored DEV regions; target-description grouping only; candidate oracle",
    }


def markdown(report: dict[str, Any]) -> str:
    """Render matched baseline and variant quality/resource measurements."""
    lines = [
        "# Remote GPU prompt screen",
        "",
        (
            "Four generic prompt variants were frozen before inference. "
            "Each retains the original RGB512 image and literal source state. All source, projection and returned "
            "request hashes were verified before local DEV references were opened. No case-specific wording was tuned."
        ),
        "",
        (
            "| Model / prompt | Valid/planned | Known correct | Ambiguous abstention | Known abstentions | "
            "Partition exact | Conserved | Inference s | CPU s | Peak RSS MiB |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        for variant, entry in {"original RGB512": {"metrics": row["baseline"]}, **row["variants"]}.items():
            metric = entry["metrics"]

            def number(key: str, metric: dict[str, Any] = metric) -> str:
                value = metric[key]
                return "unknown" if value is None else f"{value:.3f}"

            rss = metric["peak_rss_bytes"]
            lines.append(
                f"| {model} / {variant} | {metric['completed']}/{metric['planned']} | "
                f"{metric['known_correct']}/{metric['known_denominator']} | "
                f"{metric['ambiguous_abstentions']}/{metric['ambiguous_denominator']} | "
                f"{metric['known_abstentions']} | "
                f"{metric['partition_exact']}/{metric['planned']} | {metric['conservation']}/{metric['completed']} | "
                f"{number('inference_wall_seconds')} | {number('inference_cpu_seconds')} | "
                f"{'unknown' if rss is None else f'{rss / 2**20:.1f}'} |"
            )
    lines += [
        "",
        "| Model / variant | Known gains / losses | Ambiguous abstention gains / losses | Choice changes | Unpaired |",
        "|---|---:|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        for variant, entry in row["variants"].items():
            pair = entry["paired"]
            lines.append(
                f"| {model} / {variant} | {pair['known_gains']} / {pair['known_losses']} | "
                f"{pair['abstention_gains']} / {pair['abstention_losses']} | "
                f"{pair['choice_changes']} | {pair['unpaired']} |"
            )
    lines += [
        "",
        "| Model / prompt | Tie abstentions | Missing / failed / malformed | CUDA allocated / reserved GiB |",
        "|---|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        for variant, entry in {"original RGB512": {"metrics": row["baseline"]}, **row["variants"]}.items():
            metric = entry["metrics"]
            peaks = [metric["cuda_peak_allocated_bytes"], metric["cuda_peak_reserved_bytes"]]
            gpu = " / ".join("unknown" if value is None else f"{value / 2**30:.2f}" for value in peaks)
            failure = metric["failures"]
            lines.append(
                f"| {model} / {variant} | {metric['tie_abstentions']} | "
                f"{failure['missing']} / {failure['worker_error']} / {failure['schema_error']} | {gpu} |"
            )
    lines += [
        "",
        (
            "Known and ambiguous denominators remain planned counts, including missing or malformed responses. "
            "Tied native maxima conservatively become unresolved; confidence calibration is unvalidated. "
            "Partitions and conservation use the source-candidate contract; "
            "amount/header/cell reconstruction is unmeasured."
        ),
        "",
        (
            "Inference wall/CPU covers adapter preprocessing and native prediction. "
            "RSS is process-lifetime high water for "
            "the inference process; baseline and screen use separate processes. "
            "Loading is excluded from per-request time. "
            "Regions run serially. CUDA allocation/reservation peaks are retained in JSON when reported; "
            "device-wide utilization is outside this table. No inference cost is inferred from latency."
        ),
        "",
        (
            f"Source manifest SHA256: `{report['source_manifest_sha256']}`. "
            f"Prompt provenance SHA256: `{report['prompt_provenance_sha256']}`."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Score explicit local artifacts only."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-dir", "source-index", "packets", "prompt-dir", "markdown", "json"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--run", action="append", required=True, help="model-label=output-directory")
    parser.add_argument("--baseline", action="append", required=True, help="model-label=output-directory")
    args = parser.parse_args()
    runs = {name: Path(path) for name, path in (value.split("=", 1) for value in args.run)}
    baselines = {name: Path(path) for name, path in (value.split("=", 1) for value in args.baseline)}
    report = evaluate(args.source_dir, args.source_index, args.packets, args.prompt_dir, runs, baselines)
    args.json.write_text(json.dumps(report, indent=2) + "\n")
    args.markdown.write_text(markdown(report))


if __name__ == "__main__":
    main()
