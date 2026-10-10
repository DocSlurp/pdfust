"""Authenticate and prepare matched selector geometry diagrams without hosted calls."""

# ruff: noqa: EM101, TRY003, PLR0913, PLR0917, C901, PLR0912, PLR2004, E501, SLF001
from __future__ import annotations

import argparse
import base64
import json
import os
import resource
import time
from pathlib import Path
from typing import Any

from bench import p003_candidate_choice as chooser
from bench import p003_candidate_run as candidate_run
from bench import p003_geometry_diagram as diagram
from bench import pipeline_vision_transcription as transcription
from bench.p003_gate_run import authenticate as authenticate_source
from bench.silver import canonical, guard_path, sha, write_json

REVIEWED_PARSER = "8188aca8439f7c4bf455bf81b55a7a3e9f0789ca3590abbd3042d050b784591e"


def _archive(directory: Path, frozen: dict[str, Any], external: Path) -> None:
    trusted = json.loads(external.read_bytes())
    if not trusted or not frozen["code_sha256"]:
        raise ValueError("An independent nonempty archive code map is required")
    for name, digest in frozen["code_sha256"].items():
        if Path(name).name != name or not name.endswith(".py") or trusted.get(name) != digest:
            raise ValueError("Archive code identity differs from external approval")
        if sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archive code bytes changed")


def prepare(
    selector: Path,
    selector_trust: Path,
    source_baseline: Path,
    source_trust: Path,
    inputs: list[Path],
    input_trust: list[Path],
    output: Path,
) -> dict[str, Any]:
    """Freeze every page and pool, keeping selector choices and fallback identity unchanged."""
    started, cpu = time.perf_counter(), time.process_time()
    selector, selector_trust, source_baseline, source_trust, output = [
        guard_path(p) for p in (selector, selector_trust, source_baseline, source_trust, output)
    ]
    inputs, input_trust = [guard_path(p) for p in inputs], [guard_path(p) for p in input_trust]
    if output.exists() and any(output.iterdir()):
        raise ValueError("Refuse to replace an existing source-only diagram freeze")
    selected_frozen = json.loads((selector / "frozen.json").read_bytes())
    selected_report = json.loads((selector / "report.json").read_bytes())
    _archive(selector, selected_frozen, selector_trust)
    if selected_frozen["code_sha256"].get("p003_candidate_choice.py") != sha(Path(chooser.__file__).read_bytes()):
        raise ValueError("Matched selector choice helper differs from current exact replay")
    config = selected_frozen["config"]
    if (
        selected_report["config"] != config
        or config["processor"] != "p003_candidate_choice"
        or config.get("seed") != 20261010
        or config.get("evidence_mode", "whole") != "whole"
        or config.get("image_mode", "rgb") != "rgb"
        or config.get("image_visibility", "source") != "source"
        or len(inputs) != 2
        or len(input_trust) != 2
    ):
        raise ValueError("Diagram control requires the exact two-input default-seed whole/RGB selector")
    source_frozen, _ = authenticate_source(source_baseline, json.loads(source_trust.read_bytes()))
    authenticated = [
        candidate_run.authenticate(p, json.loads(t.read_bytes()), reviewed_parser_sha256=(REVIEWED_PARSER,))
        for p, t in zip(inputs, input_trust, strict=True)
    ]
    if (
        any(f["records"] != selected_frozen["records"] for f, _, _ in authenticated)
        or source_frozen["records"] != selected_frozen["records"]
    ):
        raise ValueError("Diagram source and candidate records must match every intended PDF page")
    selected_rows = {p["id"]: p for p in selected_report["results"]}
    if len(selected_rows) != len(selected_report["results"]) or set(selected_rows) != {
        r["id"] for r in selected_frozen["records"]
    }:
        raise ValueError("Selector page inventory differs from all intended pages")
    maps = [{p["id"]: p for p in report["results"]} for _, report, _ in authenticated]
    inventories = selected_frozen["candidate_inputs"]
    if len(inventories) != 2:
        raise ValueError("Selector input inventory differs")
    for j, (directory, inventory) in enumerate(zip(inputs, inventories, strict=True)):
        if Path(inventory["directory"]) != directory or inventory["copied_directory"] != f"baseline-{j}":
            raise ValueError("Candidate input order or original directory changed")
        for name, digest in inventory["file_sha256"].items():
            parts = Path(name).parts
            if ".." in parts or not (len(parts) == 1 or (len(parts) == 2 and parts[0] == "code")):
                raise ValueError("Unsafe candidate input inventory")
            if (
                sha((directory / name).read_bytes()) != digest
                or sha((selector / f"baseline-{j}" / name).read_bytes()) != digest
            ):
                raise ValueError("Matched selector copies differ from original authenticated generation")
    output.mkdir(parents=True, exist_ok=True)
    for folder in ("code", "sources", "crops", "trust"):
        (output / folder).mkdir()
    code_sha256 = {}
    for name in (
        "p003_geometry_diagram.py",
        "p003_geometry_diagram_prepare.py",
        "p003_candidate_choice.py",
        "pipeline_vision_transcription.py",
        "pipeline_repair.py",
        "silver.py",
    ):
        raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(raw)
        code_sha256[name] = sha(raw)
    receipts = []
    for name, directory, trust in [
        ("selector", selector, selector_trust),
        ("source", source_baseline, source_trust),
        *[(f"input-{j}", p, t) for j, (p, t) in enumerate(zip(inputs, input_trust, strict=True))],
    ]:
        (output / "trust" / f"{name}.json").write_bytes(trust.read_bytes())
        receipts.append(
            {
                "name": name,
                "directory": str(directory),
                "external_trusted_code": str(trust),
                "external_trusted_code_sha256": sha(trust.read_bytes()),
                "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
                "report_sha256": sha((directory / "report.json").read_bytes()),
            }
        )
    frozen = {
        "schema": 1,
        "code_sha256": code_sha256,
        "records": selected_frozen["records"],
        "trust_receipts": receipts,
        "edges": diagram.EDGES,
        "styles": diagram.STYLES,
        "selector_seed": config["seed"],
        "model": config["model"],
        "fallback": config["fallback"],
        "selector_config": config,
        "source_pixels_supplied": False,
        "instruction_treatment_changed": True,
        "pure_pixel_causal_control": False,
        "notice": diagram.NOTICE,
        "source_mapping_policy": "Every retained source word with positive bbox intersection with each exact selector crop viewport; independent contextual inventories, not a disjoint page partition.",
        "references_read": False,
        "fresh_confirmation_accessed": False,
        "inference_calls": 0,
    }
    write_json(output / "frozen.json", frozen)
    pages = []
    for record in selected_frozen["records"]:
        ident = record["id"]
        selected = selected_rows[ident]
        if json.loads((selector / f"{ident}-result.json").read_bytes()) != selected:
            raise ValueError("Selector result differs from complete report")
        original = json.loads((source_baseline / f"{ident}-result.json").read_bytes())
        source = original["source"]
        source_path = f"sources/{ident}.json"
        write_json(output / source_path, source)
        frames = [mapping[ident] for mapping in maps]
        page: dict[str, Any] = {
            "id": ident,
            "record": record,
            "source_path": source_path,
            "source_sha256": sha((output / source_path).read_bytes()),
            "source_identity_sha256": sha(canonical(source)),
            "source_word_count": len(source["words"]),
            "original_rotation": original["original_rotation"],
            "effective_rotation": original["effective_rotation"],
            "crops": [],
            "matched_selector_result_sha256": sha((selector / f"{ident}-result.json").read_bytes()),
        }
        if any(f["status"] != "ok" for f in frames):
            if selected["ranking_status"] not in ("baseline_failed_skipped", "not_applicable_baseline_failure"):
                raise ValueError("Baseline failure differs from matched selector applicability")
            page["status"] = "not_applicable_baseline_failure"
            pages.append(page)
            continue
        if any(f["viewport"] != source["page_size"] or f["viewport"] != frames[0]["viewport"] for f in frames):
            raise ValueError("Source display viewport differs from candidate frame")
        keys = ("index", "request_index", "viewport", "detector_box")
        expected = [{k: c[k] for k in keys} for c in frames[0]["transcription_regions"]]
        if any([{k: c[k] for k in keys} for c in f["transcription_regions"]] != expected for f in frames[1:]):
            raise ValueError("Candidate crop inventories differ")
        if [r["index"] for r in selected["ranking_regions"]] != list(range(len(expected))):
            raise ValueError("Matched selector pool inventory is incomplete")
        for index, info in enumerate(selected["ranking_regions"]):
            crops = [f["transcription_regions"][index] for f in frames]
            parsed, pixel_hashes = [], []
            for directory, crop in zip(inputs, crops, strict=True):
                raw = json.loads((directory / f"{ident}-request-{crop['request_index']}.json").read_bytes())
                _, pixels = candidate_run._crop_bytes(raw)
                pixel_hashes.append(sha(pixels))
                parsed.append(transcription.parse(crop["transcription_response"], crop["viewport"]))
            if len(set(pixel_hashes)) != 1 or info["original_crop_sha256"] != pixel_hashes[0]:
                raise ValueError("Candidate pools were not generated from identical crop bytes")
            seed = int(sha(f"{config['seed']}/{ident}/{index}".encode())[:16], 16)
            pool = chooser.freeze_pool(crops[0]["viewport"], parsed, seed=seed)
            if (
                chooser.pool_record(pool) != info["pool"]
                or json.loads((selector / f"{ident}-pool-{index}.json").read_bytes()) != info["pool"]
            ):
                raise ValueError("Candidate content, aliases or per-crop seed changed")
            regions = [
                r
                for r in original["region_plan"]["regions"]
                if r["kind"] == "detector_proposal" and r["bbox"] == info["viewport"]
            ]
            bounds = info["viewport"]
            source_ids = [
                w["id"]
                for w in source["words"]
                if min(w["bbox"][2], bounds[2]) > max(w["bbox"][0], bounds[0])
                and min(w["bbox"][3], bounds[3]) > max(w["bbox"][1], bounds[1])
            ]
            mapping = {
                "viewport": bounds,
                "source_ids": source_ids,
                "policy": "positive bbox intersection; source-order contextual inventory",
            }
            folder = f"crops/{ident}-{index}"
            (output / folder).mkdir()
            write_json(output / folder / "pool.json", chooser.pool_record(pool))
            entry: dict[str, Any] = {
                "index": index,
                "folder": folder,
                "viewport": info["viewport"],
                "exact_matching_ordinal_region_ids": [r["id"] for r in regions],
                "source_ids": source_ids,
                "source_mapping_sha256": sha(canonical(mapping)),
                "source_mapping_policy": mapping["policy"],
                "pool_sha256": pool.snapshot_sha256,
                "pool_file_sha256": sha((output / folder / "pool.json").read_bytes()),
                "crop_seed": seed,
                "variants": [],
            }
            if len(pool.candidates) < 2:
                entry["status"] = "not_applicable_duplicates"
                page["crops"].append(entry)
                continue
            previous_body = json.loads((selector / f"{ident}-selector-{index}-request.json").read_bytes())
            previous_url = previous_body["state"][1]["image_url"]["url"]
            if chooser.request(pool, config["model"], previous_url) != previous_body:
                raise ValueError("Retained selector evidence or instructions differ from matched default")
            entry["original_selector_request_sha256"] = sha(
                (selector / f"{ident}-selector-{index}-request.json").read_bytes()
            )
            for edge in diagram.EDGES:
                for style in diagram.STYLES:
                    url, image_metadata = diagram.diagram(source, source_ids, info["viewport"], edge, style)
                    png = base64.b64decode(url.split(",", 1)[1], validate=True)
                    prefix = f"{style}-{edge}"
                    (output / folder / f"{prefix}.png").write_bytes(png)
                    write_json(output / folder / f"{prefix}-image.json", image_metadata)
                    body, evidence = diagram.request(pool, config["model"], url)
                    variant = {
                        "edge": edge,
                        "style": style,
                        "image_path": f"{folder}/{prefix}.png",
                        "image_sha256": sha(png),
                        "image_bytes": len(png),
                        "image_size": image_metadata["image_size"],
                        "image_metadata_path": f"{folder}/{prefix}-image.json",
                        "evidence": evidence,
                    }
                    if body is not None:
                        path = f"{folder}/{prefix}-request.json"
                        write_json(output / path, body)
                        variant.update(
                            request_path=path,
                            request_file_sha256=sha((output / path).read_bytes()),
                            request_sha256=sha(json.dumps(body, separators=(",", ":")).encode()),
                        )
                    entry["variants"].append(variant)
            entry["status"] = "prepared"
            page["crops"].append(entry)
        page["status"] = "prepared" if page["crops"] else "no_detector_crops"
        pages.append(page)
    report = {
        "schema": 1,
        "pages": pages,
        "intended_page_count": len(pages),
        "references_read": False,
        "inference_calls": 0,
        "source_pixels_supplied": False,
        "pure_pixel_causal_control": False,
        "frozen_sha256": sha((output / "frozen.json").read_bytes()),
        "prepared_request_count": sum(
            v["evidence"]["status"] == "prepared" for p in pages for c in p["crops"] for v in c["variants"]
        ),
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "self_cpu_seconds": time.process_time() - cpu,
            "peak_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Serial source-only Python/Pillow; authentication and preparation timed, imports excluded; lifetime RSS includes imports; no sampling; contended; native threads unmeasured.",
            "thread_environment": {
                name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
            },
        },
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Prepare diagrams and prospective native bodies; no client can be constructed here."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selector", required=True, type=Path)
    parser.add_argument("--selector-trusted-code", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--source-trusted-code", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path, action="append")
    parser.add_argument("--input-trusted-code", required=True, type=Path, action="append")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = prepare(
        args.selector,
        args.selector_trusted_code,
        args.source,
        args.source_trusted_code,
        args.input,
        args.input_trusted_code,
        args.output,
    )
    print(json.dumps({k: report[k] for k in ("intended_page_count", "prepared_request_count", "resources")}, indent=2))


if __name__ == "__main__":
    main()
