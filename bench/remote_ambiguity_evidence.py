"""Freeze measured source ambiguity evidence without copying choices or references."""

# ruff: noqa: PLR2004 - explicit fixed matrix sizes and bounded source payload arities.

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from bench import ambiguity_geometry, ambiguity_pixels
from bench.lowlevel_run import score
from bench.remote_image_sizes import verify as verify_fresh
from bench.remote_prompt_packets import _digest, _encode, _fail, _inside, _safe, transform
from bench.remote_prompt_report import aggregate, events, paired, verify_sources
from bench.remote_report import _choice, _read

EDGES = (256, 500)
PACKS = ("geometry", "pixels", "both")
PROMPTS = ("original", "identity")
MODELS = ("flash", "clef", "pplx", "intern")
EXPLORATORY_MODELS = ("qwen9",)
GEOMETRY_KEYS = (
    "font_scale",
    "baseline_gap_em",
    "ink_gap_em",
    "horizontal_overlap",
    "indent_em",
    "within_line_gap_em",
    "local_row_leading_em",
    "local_leading_variation",
    "neighboring_column_anchor_counts",
    "shared_neighbor_columns",
    "repeated_neighbor_columns",
    "rule_separator_coverage",
    "partial_rule_coverage",
    "shared_small_enclosure",
    "same_explicit_cell",
    "different_explicit_cells",
    "vertical_internal_boundary",
    "targets_distinct_lines",
    "inline_gap_em",
    "target_direction",
    "vertical_separator_coverage",
    "neighboring_row_alignment_count",
)
PIXEL_KEYS = (
    "available",
    "axis_inline",
    "vertical_whitespace_valley",
    "vertical_rule_coverage",
    "thin_vertical_rule_count",
    "horizontal_crossing_count",
    "inline_center_gap_em",
    "inline_gap_em",
    "normalization_scale",
    "scale_pixels",
    "baseline_gap_em",
    "selector_ink_gap_em",
    "horizontal_whitespace_valley",
    "within_target_band_whitespace",
    "valley_contrast",
    "horizontal_rule_coverage",
    "thin_horizontal_rule_count",
    "vertical_crossing_count",
    "broad_color_delta",
    "broad_color_transition",
    "dark_border_contact",
)
MAX_EVIDENCE_BYTES = 8192
CONFIG = {
    "schema": "source-ambiguity-evidence-v1",
    "edges": list(EDGES),
    "packs": list(PACKS),
    "prompts": list(PROMPTS),
    "models": list(MODELS),
    "exploratory_models": list(EXPLORATORY_MODELS),
    "geometry_keys": list(GEOMETRY_KEYS),
    "pixel_keys": list(PIXEL_KEYS),
    "source_count": 24,
    "pixel_supplemental_render_edge": 640,
    "scope": "supplied source selectors; pixel640 supplemental CPU evidence beyond model image256/500",
}


def _numeric(value: Any) -> bool:  # noqa: ANN401 - recursive admitted measurement validation.
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, list):
        return len(value) <= 32 and all(_numeric(item) for item in value)
    if isinstance(value, dict):
        return set(value) <= {"top", "bottom", "left", "right"} and all(_numeric(item) for item in value.values())
    return False


def evidence(geometry: dict[str, Any], pixels: dict[str, Any], pack: str) -> dict[str, Any]:
    """Whitelist measurements only; exclude all semantic choices, text and IDs."""
    if pack not in PACKS:
        _fail("Unknown source evidence pack")
    result: dict[str, Any] = {}
    if pack in ("geometry", "both"):
        result["geometry_available"] = True
        result["geometry_axis_inline"] = geometry["features"].get("relation_axis_inline")
        for key in GEOMETRY_KEYS:
            value = geometry["features"].get(key)
            if not _numeric(value):
                _fail("Geometry whitelist contains nonnumeric evidence")
            result["geometry_" + key] = value
    if pack in ("pixels", "both"):
        for key in PIXEL_KEYS:
            value = pixels["features"].get(key)
            if not _numeric(value):
                _fail("Pixel whitelist contains nonnumeric evidence")
            result["pixel_" + key] = value
        result["pixel_supplemental_render_edge"] = 640
        result["pixel_scale_from_selector_height"] = pixels["features"].get("normalization_source") == "selector_height"
    if len(_encode(result)) > MAX_EVIDENCE_BYTES:
        _fail("Compact source evidence exceeds admission")
    return result


def project(original: dict[str, Any], measured: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Keep literal original state/image and append one separate evidence object."""
    if prompt not in PROMPTS or len(original.get("state", [])) != 2:
        _fail("Unexpected source prompt/state inventory")
    result = transform(original, prompt)
    result["state"].append(_encode({"supplemental_evidence": measured}).decode())
    return result


def _code_hashes() -> dict[str, str]:
    import bench.remote_prompt_packets as prompts  # noqa: PLC0415

    result = {
        key: _digest(_read(Path(module.__file__)))
        for key, module in (
            ("geometry", ambiguity_geometry),
            ("pixels", ambiguity_pixels),
            ("prompt_transform", prompts),
        )
        if module.__file__ is not None
    }
    result["matrix_builder"] = _digest(_read(Path(__file__)))
    return result


def _selected(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [row for row in source["mapping"] if row["arm"] in {f"fresh-rgb-{edge}" for edge in EDGES}]
    sources = {row["source_id"] for row in rows}
    pairs = {(row["source_id"], row["requested_edge"]) for row in rows}
    if len(sources) != 24 or len(rows) != 48 or pairs != {(identity, edge) for identity in sources for edge in EDGES}:
        _fail("Evidence source RGB256/500 matrix differs")
    return rows


def _features(source: dict[str, Any]) -> dict[str, Any]:
    directory = Path(source["source_directory"])
    manifest = json.loads(_read(directory / "manifest.json"))
    pages = {row["id"]: row for row in manifest["pages"]}
    result = {}
    for row in _selected(source):
        if row["source_id"] in result:
            continue
        page = pages[row["page_id"]]
        raw = _read(_inside(directory, page["observation_file"]))
        if _digest(raw) != page["observation_sha256"]:
            _fail("Observation differs from source freeze")
        selector = json.loads(raw)["selector"]
        pdf = _inside(directory, page["source_file"])
        geometry = ambiguity_geometry.extract(pdf, selector["target"]["boxes"], scope_bbox=selector["bbox"])
        pixels = ambiguity_pixels.extract(
            pdf,
            selector["target"]["boxes"],
            scope_bbox=selector["bbox"],
            font_scale=geometry["features"].get("font_scale"),
        )
        result[row["source_id"]] = {"geometry": geometry, "pixels": pixels}
    return result


def prepare(fresh: Path, output: Path) -> dict[str, Any]:
    """Verify all504 then freeze measurements, config and288 source-only bodies."""
    fresh, output = _safe(fresh), _safe(output)
    source = verify_fresh(fresh)
    rows = _selected(source)
    measured = _features(source)
    inventory = {row["id"]: row for row in json.loads(_read(fresh / "manifest.json"))["records"]}
    output.mkdir(parents=True, exist_ok=False)
    features_raw = _encode(measured)
    (output / "source-features.json").write_bytes(features_raw)
    (output / "config.json").write_bytes(_encode(CONFIG))
    records, mapping = [], []
    for row in rows:
        original = inventory[row["id"]]
        body = json.loads(_read(_inside(fresh, original["request_file"])))
        image_file = row["id"] + ".png"
        (output / image_file).write_bytes(_read(_inside(fresh, original["image_files"][0])))
        for pack in PACKS:
            compact = evidence(**measured[row["source_id"]], pack=pack)
            for prompt in PROMPTS:
                raw = _encode(project(body, compact, prompt))
                identity = _digest(_encode([row["id"], pack, prompt, _digest(raw)]))[:24]
                request_file = identity + ".json"
                (output / request_file).write_bytes(raw)
                records.append({"id": identity, "request_file": request_file, "image_files": [image_file]})
                mapping.append(
                    {
                        **row,
                        "fresh_id": row["id"],
                        "id": identity,
                        "pack": pack,
                        "prompt": prompt,
                        "fresh_request_sha256": row["projected_request_sha256"],
                        "projected_request_sha256": _digest(raw),
                        "image_file": image_file,
                        "evidence_sha256": _digest(_encode(compact)),
                    }
                )
    manifest = _encode({"records": records})
    (output / "manifest.json").write_bytes(manifest)
    provenance = {
        "experiment": "source-ambiguity-evidence-v1",
        "fresh_directory": str(fresh),
        "config": CONFIG,
        "config_sha256": _digest(_encode(CONFIG)),
        "feature_code_sha256": _code_hashes(),
        "geometry_config": ambiguity_geometry.CONFIG,
        "pixel_policy": ambiguity_pixels.POLICY,
        "features_sha256": _digest(features_raw),
        "worker_manifest_sha256": _digest(manifest),
        "fresh_manifest_sha256": _digest(_read(fresh / "manifest.json")),
        "fresh_provenance_sha256": _digest(_read(fresh / "provenance.json")),
        "mapping": mapping,
    }
    (output / "provenance.json").write_bytes(_encode(provenance))
    return provenance


def verify(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Recompute all source measurements and require exact frozen projections."""
    directory = _safe(directory)
    provenance = json.loads(_read(directory / "provenance.json"))
    fresh = _safe(Path(provenance["fresh_directory"]))
    source = verify_fresh(fresh)
    if (
        provenance["config"] != CONFIG
        or provenance["config_sha256"] != _digest(_encode(CONFIG))
        or provenance["feature_code_sha256"] != _code_hashes()
        or provenance["geometry_config"] != ambiguity_geometry.CONFIG
        or provenance["pixel_policy"] != ambiguity_pixels.POLICY
    ):
        _fail("Frozen source feature policy/code differs")
    for filename, key in (("manifest.json", "fresh_manifest_sha256"), ("provenance.json", "fresh_provenance_sha256")):
        if _digest(_read(fresh / filename)) != provenance[key]:
            _fail("Fresh parent hash differs")
    measured_raw = _read(directory / "source-features.json")
    measured = json.loads(measured_raw)
    if (
        _digest(measured_raw) != provenance["features_sha256"]
        or measured != _features(source)
        or _read(directory / "config.json") != _encode(CONFIG)
    ):
        _fail("Frozen measured source evidence differs")
    raw_manifest = _read(directory / "manifest.json")
    manifest = json.loads(raw_manifest)
    expected = [(row, pack, prompt) for row in _selected(source) for pack in PACKS for prompt in PROMPTS]
    if (
        _digest(raw_manifest) != provenance["worker_manifest_sha256"]
        or set(manifest) != {"records"}
        or len(manifest["records"]) != len(expected)
        or len(provenance["mapping"]) != len(expected)
    ):
        _fail("Frozen evidence inventory differs")
    originals = {row["id"]: row for row in json.loads(_read(fresh / "manifest.json"))["records"]}
    admitted = {}
    for row, entry, (source_row, pack, prompt) in zip(
        manifest["records"], provenance["mapping"], expected, strict=True
    ):
        original = originals[source_row["id"]]
        body = json.loads(_read(_inside(fresh, original["request_file"])))
        compact = evidence(**measured[source_row["source_id"]], pack=pack)
        raw = _read(_inside(directory, row["request_file"]))
        identity = _digest(_encode([source_row["id"], pack, prompt, _digest(raw)]))[:24]
        image_file = source_row["id"] + ".png"
        expected_entry = {
            **source_row,
            "fresh_id": source_row["id"],
            "id": identity,
            "pack": pack,
            "prompt": prompt,
            "fresh_request_sha256": source_row["projected_request_sha256"],
            "projected_request_sha256": _digest(raw),
            "image_file": image_file,
            "evidence_sha256": _digest(_encode(compact)),
        }
        if (
            raw != _encode(project(body, compact, prompt))
            or entry != expected_entry
            or identity in admitted
            or row != {"id": identity, "request_file": identity + ".json", "image_files": [image_file]}
            or _read(directory / image_file) != _read(_inside(fresh, original["image_files"][0]))
        ):
            _fail("Evidence projection changed source/measurements/question/image")
        admitted[identity] = {**entry, "sha256": _digest(raw)}
    return source, admitted


def scored_case(event: dict[str, Any] | None, observation: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Admit native probabilities or stock generated labels without inventing calibration."""
    if event is None:
        return {"status": "missing", "expected": target["expected"]}
    if event.get("status") != "ok":
        return {"status": "worker_error", "expected": target["expected"], "event": event}
    try:
        parsed = _choice(event["response"])
        parsed.setdefault("tie_abstention", False)
        return {
            "status": "ok",
            "expected": target["expected"],
            "parsed": parsed,
            "score": score(observation, target, parsed["choice"]),
            "event": event,
        }
    except (ValueError, TypeError, KeyError) as error:
        return {"status": "schema_error", "expected": target["expected"], "error": str(error), "event": event}


def metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Mark stock tie diagnostics unavailable and retain planned denominators."""
    result = aggregate(cases)
    if any(case.get("parsed", {}).get("probabilities") is None for case in cases if case["status"] == "ok"):
        result["tie_abstentions"] = None
    return result


def evaluate(directory: Path, runs: dict[str, Path], baselines: dict[str, Path] | None = None) -> dict[str, Any]:
    """Verify all sources and runs before opening local DEV scorer references."""
    source, admitted = verify(directory)
    if set(runs) - {*MODELS, *EXPLORATORY_MODELS} or (baselines is not None and set(baselines) != set(runs)):
        _fail("Evidence report model/baseline inventory differs")
    originals, observations = verify_sources(
        Path(source["source_directory"]), Path(source["source_index"]), Path(source["source_packets"]) / "manifest.json"
    )
    returned = {model: events(_safe(path), admitted) for model, path in runs.items()}
    fresh_inventory = {row["id"]: {**row, "sha256": row["projected_request_sha256"]} for row in source["mapping"]}
    before = {model: events(_safe(path), fresh_inventory) for model, path in (baselines or {}).items()}
    # First reference access after all source measurements/projections and returned hashes pass.
    source_dir = Path(source["source_directory"])
    manifest = json.loads(_read(source_dir / "manifest.json"))
    raw_targets = _read(source_dir / "private-targets.json")
    if _digest(raw_targets) != manifest["targets_sha256"]:
        _fail("Local DEV references differ")
    targets = {row["id"]: row for row in json.loads(raw_targets)}
    models = {}
    for model, (attempts, status) in returned.items():
        groups = {}
        for edge in EDGES:
            for pack in PACKS:
                for prompt in PROMPTS:
                    entries = [
                        row
                        for row in admitted.values()
                        if row["requested_edge"] == edge and row["pack"] == pack and row["prompt"] == prompt
                    ]
                    cases, baseline = [], []
                    for row in entries:
                        page = originals[row["source_id"]]["row"]["page_ids"][0]
                        cases.append(scored_case(attempts.get(row["id"]), observations[page], targets[page]))
                        if model in before:
                            baseline.append(
                                scored_case(before[model][0].get(row["fresh_id"]), observations[page], targets[page])
                            )
                    entry = {"metrics": metrics(cases)}
                    if baseline:
                        entry.update(baseline=metrics(baseline), paired=paired(baseline, cases))
                    groups[f"rgb-{edge}/{pack}/{prompt}"] = entry
        models[model] = {"groups": groups, "status": status, "exploratory": model in EXPLORATORY_MODELS}
    return {
        "experiment": "source-ambiguity-evidence-v1",
        "models": models,
        "scope": "24 authored DEV regions repeated across two images/three measured packs/two fixed prompts",
        "supplemental_pixel_edge": 640,
        "packet_provenance_sha256": _digest(_read(directory / "provenance.json")),
    }


def markdown(report: dict[str, Any]) -> str:
    """Render conservative grouping denominators; all measurements remain in JSON."""
    lines = [
        "# Remote GPU measured ambiguity evidence",
        "",
        report["scope"],
        "",
        (
            "Pixel measurements use a supplemental source render640 regardless of the model image resolution. "
            "All source features, exact images and projections were verified before root-local DEV scoring. "
            "No extractor semantic choice, labels, IDs or treatment names enter supplemental model evidence."
        ),
        "",
        (
            "| Model / treatment | Valid/planned | Known correct | Ambiguous abstention | "
            "Known abstentions | Exact partition | Conserved |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        for group, entry in row["groups"].items():
            m = entry["metrics"]
            lines.append(
                f"| {model} / {group} | {m['completed']}/{m['planned']} | "
                f"{m['known_correct']}/{m['known_denominator']} | "
                f"{m['ambiguous_abstentions']}/{m['ambiguous_denominator']} | {m['known_abstentions']} | "
                f"{m['partition_exact']}/{m['planned']} | {m['conservation']}/{m['completed']} |"
            )
    lines += [
        "",
        (
            "Missing/failed/schema-invalid inputs remain in planned denominators. This experiment combines "
            "additional measured source evidence and approved generic wording; original-image baselines isolate "
            "the evidence effect only for original wording. Stock generated labels have no native probabilities "
            "or calibration. CPU/RSS/CUDA and paired gains/losses, when matched baseline runs are supplied, "
            "remain in the JSON artifact."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Prepare or verify source-only packets; score only verified local DEV artifacts."""
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
    report.add_argument("--json-output", type=Path, required=True)
    report.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.fresh, args.output)
        print(json.dumps({"requests": len(result["mapping"]), "output": str(args.output)}))
    elif args.command == "verify":
        _, inventory = verify(args.packets)
        print(json.dumps({"verified": len(inventory)}))
    else:
        runs = {key: Path(value) for key, value in (item.split("=", 1) for item in args.run)}
        baselines = {key: Path(value) for key, value in (item.split("=", 1) for item in args.baseline)}
        result = evaluate(args.packets, runs, baselines or None)
        _safe(args.json_output).write_bytes(_encode(result))
        _safe(args.markdown_output).write_text(markdown(result))


if __name__ == "__main__":
    main()
