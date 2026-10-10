"""Root-invoked native selection from strictly valid retained whole-crop pools."""

# ruff: noqa: SLF001, EM101, TRY003, PLC0415, PLR2004, PLR0913, PLR0917, C901, PLR0912, ANN401, TRY301
from __future__ import annotations

import argparse
import json
import shutil
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_candidate_choice as chooser
from bench import p003_candidate_diff as differences
from bench import p003_candidate_regions as admission
from bench import p003_candidate_regions_run as offline
from bench import p003_candidate_run as candidate
from bench import pipeline_run
from bench.p003_boundary_run import _charges, _entries, _error, _identifier, _reserve_wave
from bench.silver import guard_path, sha, write_json


def process(
    record: dict[str, Any],
    frozen: dict[str, Any],
    first_directory: Path,
    output: Path,
    config: dict[str, Any],
    client: Any,
    *,
    image_factory: Any = None,
) -> dict[str, Any]:
    """Select every complete crop, then commit one page; failures retain original bytes."""
    started, cpu = time.perf_counter(), time.process_time()
    first = deepcopy(frozen["generation_provenance"][0]["page"])
    identifier = _identifier(record["id"])
    result = deepcopy(first)
    result.update(
        ranking_status="not_applicable",
        ranking_regions=[],
        ranking_calls=[],
        ranking_errors=[],
        original_baseline_status=first["status"],
        admission_snapshot_sha256=frozen["snapshot_sha256"],
    )
    for suffix in ("-structure.json", ".md"):
        path = first_directory / f"{identifier}{suffix}"
        if path.exists():
            shutil.copyfile(path, output / path.name)
    selected = {}
    stage = "complete_crop_admission"
    try:
        if (
            sha(chooser.canonical_json({k: v for k, v in frozen.items() if k != "snapshot_sha256"}))
            != frozen["snapshot_sha256"]
        ):
            raise ValueError("Frozen valid-region admission changed before selector calls")
        if not frozen["complete_crop_coverage"]:
            raise ValueError("At least one detector crop lacks a complete valid candidate")
        for item in frozen["crops"]:
            index = item["index"]
            info = {
                "index": index,
                "viewport": item["viewport"],
                "valid_baseline_indexes": item["valid_baseline_indexes"],
                "invalid_baseline_indexes": [a["baseline_index"] for a in item["attempts"] if not a["valid"]],
                "unique_valid_count": item["unique_valid_count"],
                "ranking_status": "deterministic_sole_state",
            }
            result["ranking_regions"].append(info)
            # Deterministic fallback is fixed before looking at model outputs or quality references.
            origin = min(item["valid_baseline_indexes"])
            selected[index] = origin
            if item["unique_valid_count"] < 2:
                info["selected_baseline_index"] = origin
                continue
            stage = f"crop/{index}/exact_pool"
            valid = [json.loads(a["canonical_json"]) for a in item["attempts"] if a["valid"]]
            pool = chooser.freeze_pool(item["viewport"], valid, seed=item["seed"])
            if chooser.pool_record(pool) != item["pool"]:
                raise ValueError("Native selector pool differs from frozen valid-state inventory")
            attempt = next(a for a in item["attempts"] if a["baseline_index"] == origin)
            url, _ = candidate._crop_bytes(attempt["request"])
            image = {"image_edge": 0, "source_pixels_supplied": False, "original_crop_sha256": item["image_sha256"]}
            if config["image_edge"]:
                url, image = (image_factory or candidate._rerender)(
                    record, first, attempt["crop"], config["image_edge"]
                )
                actual_url, pixels = candidate._crop_bytes(
                    {"messages": [{"content": [{"type": "image_url", "image_url": {"url": url}}]}]}
                )
                if (
                    sha(pixels) != image["image_sha256"]
                    or len(pixels) != image["image_bytes"]
                    or image["image_viewport"] != item["viewport"]
                    or image["image_edge"] != config["image_edge"]
                ):
                    raise ValueError("Selector image differs from recorded exact crop provenance")
                url = actual_url
            info["selector_image"] = image
            stage = f"crop/{index}/native_request"
            body = candidate._body(
                pool,
                config["model"],
                url,
                config["image_edge"],
                evidence_mode=config.get("evidence_mode", "whole"),
                evidence_max_bytes=config.get("evidence_max_bytes", differences.DEFAULT_MAX_BYTES),
            )
            stem = f"{identifier}-selector-{index}"
            write_json(output / f"{stem}-request.json", body)
            _reserve_wave(client)
            response = client.request(
                body,
                tag=f"P003/{config['run_id']}/{identifier}/{index}",
                replay=False,
                reservation_usd=0.30,
                max_body_bytes=750_000,
            )
            write_json(output / f"{stem}-response.json", response)
            result["ranking_calls"].append(
                {
                    "entry": response["entry"],
                    "usage": response["result"].get("usage", {}),
                    "replayed": response.get("replayed"),
                    "crop_index": index,
                }
            )
            if response.get("replayed"):
                raise ValueError("Valid-region ranking requires fresh selector calls")
            stage = f"crop/{index}/native_selection"
            answer = chooser.parse(pool, response["result"])
            state_bytes, audit = chooser.select(pool, answer)
            info["audit"] = audit
            info["ranking_status"] = "unresolved_first_valid_fallback" if state_bytes is None else "staged"
            if state_bytes is not None:
                valid_index = audit["original_input_indexes"][0]
                origin = item["valid_baseline_indexes"][valid_index]
                attempt = next(a for a in item["attempts"] if a["baseline_index"] == origin)
                if state_bytes.decode() != attempt["canonical_json"]:
                    raise ValueError("Selected bytes differ from one complete valid original candidate")
                selected[index] = origin
                info["selected_sha256"] = sha(state_bytes)
            info["selected_baseline_index"] = selected[index]
        stage = "atomic_complete_page_composition"
        composed = admission.compose_selection(frozen, selected)
        write_json(output / f"{identifier}-structure.json", composed["state"])
        (output / f"{identifier}.md").write_text(composed["markdown"])
        result.update(
            status="ok",
            tables=composed["state"]["tables"],
            transcription_regions=composed["transcription_regions"],
            source_conserved=False,
            text_provenance="model-transcribed; complete retained crop selections",
            ranking_status="completed" if frozen["crops"] else "not_applicable_no_crops",
            selected_origins={str(k): v for k, v in selected.items()},
        )
        for key in ("error", "error_type", "error_stage"):
            result.pop(key, None)  # Original errors stay immutable in generation_provenance and copied baselines.
        for info in result["ranking_regions"]:
            if info["ranking_status"] == "staged":
                info["ranking_status"] = "selected"
    except Exception as error:
        result["ranking_status"] = "failed_retained_first"
        result["ranking_errors"].append(_error(error, stage))
        result.update(
            status=first["status"],
            tables=deepcopy(first["tables"]),
            transcription_regions=deepcopy(first["transcription_regions"]),
        )
        result.pop("selected_origins", None)
        for key in ("error", "error_type", "error_stage"):
            if key in first:
                result[key] = deepcopy(first[key])
        # Restore original outputs even if filesystem/Markdown writing failed after composition.
        for suffix in ("-structure.json", ".md"):
            source = first_directory / f"{identifier}{suffix}"
            target = output / source.name
            if source.exists():
                shutil.copyfile(source, target)
            elif target.exists():
                target.unlink()
        for info in result["ranking_regions"]:
            if info["ranking_status"] in {
                "staged",
                "selected",
                "deterministic_sole_state",
                "unresolved_first_valid_fallback",
            }:
                info["ranking_status"] = "discarded_atomic_failure"
    result.update(ranking_wall_seconds=time.perf_counter() - started, ranking_cpu_seconds=time.process_time() - cpu)
    write_json(output / f"{identifier}-result.json", result)
    return result


def run(
    inputs: list[Path],
    maps: list[Path],
    output: Path,
    config: dict[str, Any],
    client: Any = None,
    *,
    image_factory: Any = None,
) -> dict[str, Any]:
    """Freeze all source-only pools and accounting before root-authorized native selection."""
    if not config.get("run_hosted"):
        raise ValueError("Explicit run_hosted opt-in is required")
    edge, model = config.get("image_edge", 1024), config.get("model")
    transport = config.get("transport_concurrency", 1)
    if (
        type(edge) is not int
        or edge not in candidate.EDGES
        or model not in (*candidate.DECISION_MODELS, "cloudflare/clef-omni")
        or (edge and model not in candidate.IMAGE_MODELS)
    ):
        raise ValueError("Selector model lacks admitted text/image support")
    if type(transport) is not int or transport not in (1, 3):
        raise ValueError("Transport concurrency must be 1 or 3")
    mode = config.get("evidence_mode", "whole")
    cap = config.get("evidence_max_bytes", differences.DEFAULT_MAX_BYTES)
    if (
        mode not in {"whole", "differences"}
        or ("evidence_max_bytes" in config and mode != "differences")
        or type(cap) is not int
        or not 1 <= cap <= chooser.MAX_COMPARISON_BYTES
    ):
        raise ValueError("Invalid explicit candidate evidence mode or cap")
    output = guard_path(output)
    if output.exists():
        raise ValueError("Hosted valid-region output must be fresh")
    config = {
        "seed": 3002,
        "image_edge": edge,
        **config,
        "campaign": "P003",
        "processor": "p003_candidate_valid_regions",
        "run_id": _identifier(output.name),
        "fallback": "lowest declared valid baseline index per crop; never an invalid state",
        "scope": "incremental native ranking of complete valid retained crop states",
        "source_conserved": False,
    }
    offline.run(
        inputs,
        maps,
        output / "admission",
        seed=config["seed"],
        reviewed_parser_sha256=tuple(config.get("reviewed_parser_sha256", [])),
    )
    frozen = candidate._read(output / "admission/frozen.json")
    (output / "code").mkdir()
    code = {}
    names = set(candidate.CODE_FILES) | {
        Path(__file__).name,
        "p003_candidate_regions.py",
        "p003_candidate_regions_run.py",
        "p003_candidate_diff.py",
    }
    for name in sorted(names):
        path = Path(__file__).parent / name
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    write_json(
        output / "frozen.json",
        {
            "config": config,
            "records": frozen["records"],
            "manifest_sha256": frozen["manifest_sha256"],
            "code_sha256": code,
            "admission": {
                "directory": "admission",
                "frozen_sha256": sha((output / "admission/frozen.json").read_bytes()),
                "valid_region_pools_sha256": frozen["valid_region_pools_sha256"],
            },
            "concurrency": 1,
            "local_replay": False,
        },
    )
    if client is None:
        from bench.p003_client import P003ConcurrentClient, P003DecisionClient

        client = (P003ConcurrentClient if transport == 3 else P003DecisionClient)()
    prefix = f"P003/{config['run_id']}/"
    if _entries(client, prefix):
        raise ValueError("Ranking run ID already exists in shared persistent ledger")
    with pipeline_run.Resources() as resources:
        results = [
            process(
                r,
                candidate._read(output / f"admission/{r['id']}-valid-region-pools.json"),
                output / "admission/baseline-0",
                output,
                config,
                client,
                image_factory=image_factory,
            )
            for r in frozen["records"]
        ]
    metrics = {
        **resources.summary(),
        "scope": "incremental selection after offline retained pool preparation",
        "concurrency": 1,
        "transport_concurrency": transport,
        "end_to_end_pipeline_measured": False,
        "generation_repeated": False,
        "pool_preparation_metrics": candidate._read(output / "admission/report.json")["local_metrics"],
    }
    report = {
        "config": config,
        "page_count": len(results),
        "complete_output_pages": sum(r["status"] == "ok" for r in results),
        "results": results,
        "candidate_generation_reports": [b["historical_generation_report"] for b in frozen["baseline_provenance"]],
        "candidate_generation_cost_scope": (
            "All declared generation attempts/errors retained; deduplicate overlapping historical ledgers before totals"
        ),
        "incremental_ranking": {
            "metrics": metrics,
            "returned_calls": sum(len(r["ranking_calls"]) for r in results),
            **_charges(_entries(client, prefix)),
        },
        "metrics": metrics,
        "pages_per_minute": None,
        "pages_per_dollar": None,
    }
    report["incremental_ranking"]["cost_scope"] = (
        "Incremental valid-region selector API attempts only; original generation costs remain historical"
    )
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Only root launches explicitly admitted hosted selection arms."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, action="append", required=True)
    parser.add_argument("--trusted-code", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--image-edge", type=int, choices=candidate.EDGES, default=1024)
    parser.add_argument("--evidence-mode", choices=("whole", "differences"), default="whole")
    parser.add_argument("--evidence-max-bytes", type=int)
    parser.add_argument("--transport-concurrency", type=int, choices=(1, 3), default=1)
    parser.add_argument("--seed", type=int, default=3002)
    parser.add_argument("--reviewed-parser-sha256", action="append", default=[])
    parser.add_argument("--run-hosted", action="store_true", required=True)
    args = parser.parse_args()
    config = {
        k: getattr(args, k)
        for k in ("model", "image_edge", "evidence_mode", "seed", "reviewed_parser_sha256", "run_hosted")
    }
    if args.transport_concurrency == 3:
        config["transport_concurrency"] = 3
    if args.evidence_max_bytes is not None:
        config["evidence_max_bytes"] = args.evidence_max_bytes
    report = run(args.baseline, args.trusted_code, args.output, config)
    print(
        json.dumps({k: v for k, v in report.items() if k not in {"results", "candidate_generation_reports"}}, indent=2)
    )


if __name__ == "__main__":
    main()
