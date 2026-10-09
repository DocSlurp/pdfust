"""Offline image-axis progress and quality, separating geometric aliases from paid transmissions."""

# ruff: noqa: ANN401, EM101, TRY003
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from statistics import mean
from typing import Any

from bench.reprice_model_rates import number, request_cost
from bench.silver import guard_path


def _identity(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return row["model"], row.get("scope", "page"), row["arm"], row["offset"]


def _range(values: list[int]) -> list[int] | None:
    return [min(values), max(values)] if values else None


def transmission_stats(rows: list[dict[str, Any]], prices: dict[str, Any]) -> dict[str, Any]:
    """Charge each original ledger entry once, retaining missing usage/rates/timing as unknown."""
    unique = {r["entry"]["index"]: r for r in rows if "entry" in r and not r.get("replayed", False)}
    costs = []
    for row in unique.values():
        entry = row["entry"]
        rates = entry.get("catalog_rates") or prices.get(row["model"], {})
        cost = request_cost(entry, row.get("usage", {}), rates)
        costs.append({**cost, "model": row["model"], "arm": row["arm"], "catalog_rates": rates})
    elapsed = [number(r["entry"].get("elapsed_ms")) for r in unique.values()]
    pages = sum(len(r["case_ids"]) for r in unique.values())
    total = sum(c["effective_usd"] for c in costs) if all(c["effective_usd"] is not None for c in costs) else None
    http_ms = sum(v for v in elapsed if v is not None) if all(v is not None for v in elapsed) else None
    return {
        "unique_requests": len(unique),
        "requested_pages": pages,
        "effective_usd": total if unique else None,
        "known_partial_usd": sum(c["effective_usd"] for c in costs if c["effective_usd"] is not None),
        "unknown_cost_requests": sum(c["effective_usd"] is None for c in costs),
        "http_elapsed_ms": http_ms if unique else None,
        "pages_per_usd": pages / total if total is not None and total > 0 else None,
        "pages_per_http_minute": pages * 60000 / http_ms if http_ms is not None and http_ms > 0 else None,
        "request_bytes": sum(r.get("request_bytes", r["entry"].get("request_bytes", 0)) for r in unique.values()),
        "input_tokens": sum(
            v
            for r in unique.values()
            if (v := number(r.get("usage", {}).get("input_tokens", r.get("usage", {}).get("prompt_tokens"))))
            is not None
        )
        if all(
            number(r.get("usage", {}).get("input_tokens", r.get("usage", {}).get("prompt_tokens"))) is not None
            for r in unique.values()
        )
        and unique
        else None,
        "output_tokens": sum(
            v
            for r in unique.values()
            if (v := number(r.get("usage", {}).get("output_tokens", r.get("usage", {}).get("completion_tokens"))))
            is not None
        )
        if all(
            number(r.get("usage", {}).get("output_tokens", r.get("usage", {}).get("completion_tokens"))) is not None
            for r in unique.values()
        )
        and unique
        else None,
        "costs": costs,
    }


def snapshot(directory: Path) -> dict[str, Any]:
    """Expand exact-hash aliases only into quality observations; never duplicate provider measurements."""
    directory = guard_path(directory)
    manifest_raw = (directory / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    result_path = directory / "results.json"
    result_raw = result_path.read_bytes() if result_path.exists() else b'{"batches":[]}'
    result = json.loads(result_raw)
    retained = {_identity(r): r for r in result["batches"]}
    canonical = {(r["model"], r["request_sha256"]): r for r in manifest["batches"]}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for declared in manifest["batches"]:
        actual = retained.get(_identity(declared), {**declared, "status": "unattempted"})
        if actual["request_sha256"] != declared["request_sha256"] or actual["case_ids"] != declared["case_ids"]:
            raise ValueError("Retained batch differs from its frozen declaration")
        groups[declared["model"], declared["arm"]].append({**declared, **actual, "quality_alias": False})
    for alias in manifest.get("geometric_aliases", []):
        parent = canonical.get((alias["model"], alias["request_sha256"]))
        if parent is None or parent["case_ids"] != alias["case_ids"] or parent["arm"] != alias["canonical_arm"]:
            raise ValueError("Geometric alias lacks identical canonical request and case inventory")
        actual = retained.get(_identity(parent), {"status": "unattempted"})
        configuration = deepcopy(parent.get("configuration", {}))
        configuration["axis"] = alias["arm"].split("-")[1]
        groups[alias["model"], alias["arm"]].append(
            {
                **parent,
                **alias,
                "status": actual["status"],
                "observations": actual.get("observations", []),
                "quality_alias": True,
                "configuration": configuration,
            }
        )
    refusals: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for refused in manifest.get("refusals", []):
        refusals[refused["model"], refused["arm"]].append(refused)
        groups.setdefault((refused["model"], refused["arm"]), [])
    output = []
    for (model, arm), batches in sorted(groups.items()):
        declared_ids = {i for b in batches for i in b["case_ids"]}
        declared_ids.update(i for r in refusals[model, arm] for i in r.get("case_ids", []))
        observations = [o for b in batches for o in b.get("observations", [])]
        if len({o["case_id"] for o in observations}) != len(observations):
            raise ValueError("Duplicate case observation within a declared arm")
        if any(o["case_id"] not in declared_ids for o in observations):
            raise ValueError("Observation is outside frozen arm inventory")
        fields = {key for o in observations for key in o["score"]}
        metrics = {}
        for key in sorted(fields):
            values = [o["score"][key] for o in observations if isinstance(o["score"].get(key), (bool, int, float))]
            metrics[key] = {"n": len(values), "sum": sum(values), "mean": mean(values) if values else None}
        images = [im for b in batches for im in b.get("images", []) if im is not None]
        configurations = [b.get("configuration", {}) for b in batches]
        dimensions = sorted({tuple(im["pixels"]) for im in images})
        transmissions = transmission_stats([b for b in batches if not b["quality_alias"]], manifest.get("prices", {}))
        failed_ids = {i for b in batches if b["status"] == "failed" for i in b["case_ids"]}
        refused_ids = {i for r in refusals[model, arm] for i in r.get("case_ids", [])}
        output.append(
            {
                "model": model,
                "arm": arm,
                "configuration": configurations[0] if configurations else {},
                "declared_cases": len(declared_ids),
                "measured_cases": len(observations),
                "unmeasured_cases": len(declared_ids) - len(observations),
                "failed_cases": len(failed_ids),
                "refused_cases": len(refused_ids),
                "refusal_records": len(refusals[model, arm]),
                "alias_cases": sum(len(b.get("observations", [])) for b in batches if b["quality_alias"]),
                "replayed_cases": sum(len(b.get("observations", [])) for b in batches if b.get("replayed", False)),
                "quality_reference_arms": sorted({b["canonical_arm"] for b in batches if b["quality_alias"]}),
                "unresolved_cases": sum(o.get("answer", {}).get("choice") == "unresolved" for o in observations),
                "metrics": metrics,
                "dimensions": dimensions,
                "pixel_range": _range([im.get("total_pixels", im["pixels"][0] * im["pixels"][1]) for im in images]),
                "image_bytes_range": _range([im["bytes"] for im in images]),
                "png_bit_depths": sorted({im["png_bit_depth"] for im in images if "png_bit_depth" in im}),
                "png_color_types": sorted({im["png_color_type"] for im in images if "png_color_type" in im}),
                "transmissions": transmissions,
            }
        )
    declared_batch_ids = {_identity(b) for b in manifest["batches"]}
    all_actual = [r for r in result["batches"] if _identity(r) in declared_batch_ids]
    return {
        "directory": str(directory),
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "results_sha256": hashlib.sha256(result_raw).hexdigest(),
        "snapshot_unix_seconds": time.time(),
        "models": manifest["models"],
        "declared_sizes": manifest.get("declared_sizes", []),
        "declared_axes": manifest.get("declared_axes", []),
        "declared_representations": manifest.get("declared_representations", []),
        "planned_unique_batches": len(manifest["batches"]),
        "declared_alias_batches": len(manifest.get("geometric_aliases", [])),
        "completed_unique_batches": sum(r["status"] == "ok" for r in all_actual),
        "failed_unique_batches": sum(r["status"] == "failed" for r in all_actual),
        "rows": output,
        "provider_observations": transmission_stats(all_actual, manifest.get("prices", {})),
        "preparation": manifest.get("preparation"),
        "pricing_provenance": manifest.get("pricing_provenance"),
    }


def curves(rows: list[dict[str, Any]]) -> list[str]:
    """Show all size observations in each representation/axis without pooling aliases as repetitions."""
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        config = row["configuration"]
        grouped[
            row["model"], config.get("mode", "unknown"), config.get("axis", "unknown"), str(config.get("fixed_partner"))
        ].append(row)
    lines = [
        "",
        "Size curves (exact/declared with measured count; shared aliases marked `alias`):",
        "",
        "| Model | Representation / axis / fixed partner | Size: exact/declared (measured) |",
        "| --- | --- | --- |",
    ]
    for (model, mode, axis, partner), selected in sorted(grouped.items()):
        selected.sort(key=lambda r: r["configuration"].get("target", 0))
        points = []
        for row in selected:
            exact = row["metrics"].get("region_exact", {}).get("sum", 0)
            point = (
                f"{row['configuration'].get('target', '?')}: {exact}/{row['declared_cases']} "
                f"({row['measured_cases']} measured)"
            )
            if row["quality_reference_arms"]:
                point += " alias"
            points.append(point)
        lines.append(f"| {model} | {mode} / {axis} / {partner} | {'; '.join(points)} |")
    return lines


def _fmt(value: Any) -> str:
    return "unmeasured" if value is None else f"{value:.6g}" if isinstance(value, float) else str(value)


def markdown(snapshots: list[dict[str, Any]]) -> str:
    """Keep every axis, size and representation visible; incomplete snapshots do not select winners."""
    lines = [
        "# DEV image-axis retained progress",
        "",
        (
            "Exact request-hash geometric aliases share quality only. "
            "Their cost and latency are unmeasured, not fresh transmissions or provider-cache evidence. "
            "Rates count original transmitted page inputs; HTTP minutes sum retained request durations, "
            "not end-to-end throughput. Missing tokens/rates remain unknown. No best arm is selected."
        ),
        "",
    ]
    for snapshot_data in snapshots:
        totals = snapshot_data["provider_observations"]
        lines.extend(
            [
                f"Artifact: `{snapshot_data['directory']}`.",
                (
                    f"Manifest SHA256 `{snapshot_data['manifest_sha256']}`; "
                    f"results SHA256 `{snapshot_data['results_sha256']}`."
                ),
                (
                    f"Snapshot {snapshot_data['snapshot_unix_seconds']}; completed unique batches "
                    f"{snapshot_data['completed_unique_batches']}/{snapshot_data['planned_unique_batches']}; "
                    f"failed {snapshot_data['failed_unique_batches']}; "
                    f"aliases {snapshot_data['declared_alias_batches']}."
                ),
                (
                    f"Actual paid unique requests {totals['unique_requests']}; "
                    f"effective USD {_fmt(totals['effective_usd'])}; "
                    f"known partial USD {_fmt(totals['known_partial_usd'])}; "
                    f"unknown costs {totals['unknown_cost_requests']}."
                ),
                "",
                (
                    "| Model | Arm | Actual W×H | Pixels range | Image bytes range | "
                    "Measured/declared | Exact/declared | "
                    "Record F1 | Source conserved | Unresolved | Failed/refused/unmeasured | Alias cases | "
                    "Paid requests/pages | USD | Pages/USD | Pages/HTTP min |"
                ),
                (
                    "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | "
                    "---: | --- | ---: | --- | ---: | ---: | ---: |"
                ),
            ]
        )
        for row in snapshot_data["rows"]:
            metrics = row["metrics"]
            paid = row["transmissions"]
            dimensions = ",".join(f"{w}×{h}" for w, h in row["dimensions"])
            exact = metrics.get("region_exact", {}).get("sum", 0)
            source = metrics.get("source_conservation", {})
            lines.append(
                f"| {row['model']} | {row['arm']} | {dimensions} | {row['pixel_range']} | {row['image_bytes_range']} | "
                f"{row['measured_cases']}/{row['declared_cases']} | {exact}/{row['declared_cases']} | "
                f"{_fmt(metrics.get('record_f1', {}).get('mean'))} | {source.get('sum', 'unmeasured')}/"
                f"{source.get('n', 'unmeasured')} | {row['unresolved_cases']} | "
                f"{row['failed_cases']}/{row['refused_cases']}/{row['unmeasured_cases']} | {row['alias_cases']} | "
                f"{paid['unique_requests']}/{paid['requested_pages']} | {_fmt(paid['effective_usd'])} | "
                f"{_fmt(paid['pages_per_usd'])} | {_fmt(paid['pages_per_http_minute'])} |"
            )
        lines.extend(curves(snapshot_data["rows"]))
        lines.extend(
            [
                "",
                f"Local preparation metadata: {snapshot_data['preparation']}.",
                (
                    "All retained numeric score fields and their own denominators, PNG bit depths/color types, "
                    "pricing provenance and request-level cost bases are preserved in the ignored JSON sidecar."
                ),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    """Create an offline repeatable snapshot without credentials, generation or hosted requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    args = parser.parse_args()
    snapshots = [snapshot(d) for d in args.directories]
    report_path, json_path = guard_path(args.output), guard_path(args.json_output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown(snapshots))
    json_path.write_text(json.dumps({"snapshots": snapshots}, indent=2))
    print(
        json.dumps(
            [{k: s[k] for k in ("directory", "completed_unique_batches", "planned_unique_batches")} for s in snapshots],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
