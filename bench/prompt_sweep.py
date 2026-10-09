"""Freeze generic q0 prompt ablations before DEV-only scoring and paid execution."""

# Frozen artifacts contain heterogeneous provider and source records.
# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bench import rolling_row_run as runner
from bench.decision_hosted import ARTIFACTS, DecisionClient, checkpoint
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss

TAG = "P001-prompt-sweep/"
LIMIT = 1.0
FAMILIES = ("structure", "minimal", "evidence")


def freeze(source: Path, output: Path, family: str) -> dict[str, Any]:
    """Change generic instructions and model only; never load private targets."""
    source, output = guard_path(source), guard_path(output)
    original = runner.verify(source)
    module = importlib.import_module(f"bench.prompt_variants_{family}")
    if (output / "sweep.json").exists():
        return json.loads((output / "sweep.json").read_bytes())
    start, cpu = time.perf_counter(), time.process_time()
    output.mkdir(parents=True, exist_ok=True)
    runs = []
    for variant in module.variants():
        directory = output / variant["name"]
        directory.mkdir()
        for name in ("source-frozen.json", "candidates-frozen.json"):
            shutil.copyfile(source / name, directory / name)
        records = [r for r in original["records"] if r["route"] == "native_vector"]
        pages: dict[str, dict[str, Any]] = {}
        for record in original["records"]:
            if record["route"] == "hosted_admission" and record["arm"] == "image512":
                pages.setdefault(record["id"], record)
        for model in runner.MODELS:
            for index, record in enumerate(pages.values()):
                before = json.loads((source / record["request"]).read_bytes())
                body = module.transform(before, variant)
                check = deepcopy(body)
                check["questions"]["q0"]["instructions"] = before["questions"]["q0"]["instructions"]
                if check != before:
                    raise ValueError("Prompt transform modified evidence, menu or metadata")
                body["model"] = model
                name = f"{len(records):04d}-{index}.json"
                raw = json.dumps(body, separators=(",", ":")).encode()
                (directory / name).write_bytes(raw)
                records.append({**record, "model": model, "request": name, "sha256": hashlib.sha256(raw).hexdigest()})
        manifest = {
            **original,
            "models": list(runner.MODELS),
            "arms": ["image512"],
            "records": records,
            "prompt_variant": variant,
            "parent_manifest_sha256": hashlib.sha256((source / "manifest.json").read_bytes()).hexdigest(),
        }
        checkpoint(directory / "manifest.json", manifest)
        runner.verify(directory)
        runs.append(str(directory.resolve()))
    rss, measurement = process_peak_rss()
    result = {
        "family": family,
        "runs": runs,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "rss_measurement": measurement,
        "resource_scope": "source-only prompt preparation; perf_counter/process_time/current-process lifetime RSS",
    }
    checkpoint(output / "sweep.json", result)
    return result


def report(root: Path, destination: Path) -> None:
    """Keep old and fresh DEV cohorts separate with full fixed denominators."""
    lines = [
        "# Prompt tuning progress",
        "",
        (
            "Generic instruction-only ablations; fixed source words, images and candidate menus. "
            "All rows are DEV; heldout remains sealed. Prompts cannot recover missing candidates."
        ),
        "",
        (
            "**Quarantine:** `fresh` rows contain class-specific explanatory sentences in the source PDFs. "
            "Their admission scores are excluded from primary model conclusions. Retained for audit only. "
            "`neutral` removes those cues, but some authored prose labels become ambiguous; "
            "its binary scores are also diagnostic only. `realistic` uses the separately reviewed v2 cohort."
        ),
        "",
        (
            "| Cohort / prompt | Model | Tables exact | Prose FP | Prose unresolved | "
            "Values owned | USD | Pages/$ | API pages/min |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for path in sorted(root.glob("*/*/*/evaluation.json")):
        summary = json.loads(path.read_bytes())
        calls = json.loads((path.parent / "hosted-results.json").read_bytes())["calls"]
        for name, cohort in summary["cohorts"].items():
            model = name.rsplit("/", 1)[0]
            unique = {r["entry"]["index"]: r for r in calls if r["model"] == model and "entry" in r}
            costs = [r["cost"]["effective_usd"] for r in unique.values()]
            cost = sum(costs) if all(c is not None for c in costs) else None
            good = sum(r["status"] == "ok" for r in unique.values())
            sent = [r for r in unique.values() if not r.get("replayed")]
            seconds = sum(r.get("http_elapsed_ms") or 0 for r in sent) / 1000
            ppd = f"{good / cost:,.0f}" if cost else "unknown"
            ppm = f"{len(sent) * 60 / seconds:.1f}" if seconds else "unmeasured"
            money = f"{cost:.6f}" if cost is not None else "unknown"
            positive, negative = cohort["slices"]["borderless"], cohort["slices"]["prose"]
            label = f"{path.relative_to(root).parts[0]} / {path.parent.name}"
            lines.append(
                f"| {label} | {model} | {positive['exact_page']}/{positive['pages']} | "
                f"{negative['false_positive_page']}/{negative['pages']} | "
                f"{negative['unresolved_or_unmeasured']}/{negative['pages']} | "
                f"{positive['owned_values']}/{positive['expected_values']} | "
                f"{money} | {ppd} | {ppm} |"
            )
    lines += [
        "",
        (
            "Rates use unique provider requests; local replay adds no provider throughput. Positive reported charges "
            "win; reported zero falls back to catalog pricing with observed tokens. "
            "API time excludes local preparation. "
            "Unresolved prose is not a correct rejection. All selections conserve source IDs, "
            "which is not a correctness score."
        ),
        "",
    ]
    destination.write_text("\n".join(lines))


def main() -> None:
    """Prepare first, then execute with persistent shared budget and UTC deadline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--cohort", choices=("original", "fresh", "neutral", "realistic"), required=True)
    parser.add_argument("--family", choices=FAMILIES, required=True)
    parser.add_argument("--root", type=Path, default=ARTIFACTS / "prompt-sweep-v1")
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--deadline", default="2026-10-09T06:05:00+00:00")
    args = parser.parse_args()
    root = guard_path(args.root)
    sweep = freeze(args.source, root / args.cohort / args.family, args.family)
    if args.run_hosted:
        if args.targets is None:
            parser.error("Scoring requires private targets after all requests are frozen")
        runner.TAG_PREFIX, runner.WAVE_LIMIT = TAG, LIMIT
        client = DecisionClient()
        for directory in sweep["runs"]:
            if (
                datetime.now(UTC) >= datetime.fromisoformat(args.deadline)
                or (root / "STOP").exists()
                or (root / args.cohort / "STOP").exists()
            ):
                break
            started, cpu = time.perf_counter(), time.process_time()
            result = runner.run(Path(directory), guard_path(args.targets), client)
            rss, measurement = process_peak_rss()
            result["execution_resources"] = {
                "wall_seconds": time.perf_counter() - started,
                "cpu_seconds": time.process_time() - cpu,
                "peak_rss_bytes": rss,
                "rss_measurement": measurement,
                "scope": "current process; request orchestration plus scoring, no remote inference CPU/RAM",
                "measurement": "perf_counter/process_time/current process lifetime VmHWM; no sampling",
            }
            checkpoint(Path(directory) / "evaluation.json", result)
            report(root, Path("bench/results/prompt-tuning.md"))
            print(
                json.dumps(
                    {
                        "cohort": args.cohort,
                        "variant": Path(directory).name,
                        "requests": result["unique_requests"],
                        "usd": result["effective_usd"],
                        "stopped": result["stopped_models"],
                    }
                ),
                flush=True,
            )
            if result["budget_stopped"]:
                break
    report(root, Path("bench/results/prompt-tuning.md"))


if __name__ == "__main__":
    main()
