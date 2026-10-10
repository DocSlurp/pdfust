"""Authenticate and freeze independent header menus before any hosted decisions."""

# ruff: noqa: EM101, TRY003, SLF001, C901, PLR0912, E501, PLR2004, PLR0913
from __future__ import annotations

import argparse
import base64
import json
import os
import resource
import time
from pathlib import Path
from typing import Any

import pylopdf
from bench import generalization_vision_regions as regions
from bench import p003_candidate_run as baseline
from bench import p003_header_packets as packets
from bench import p003_header_proposals as headers
from bench import pipeline_vision_transcription as strict
from bench.silver import guard_path, sha, write_json

MODELS = (
    "perplexity/pplx-decider-v1.1-27b",
    "openai/gpt-6-luna-decisions",
    "cloudflare/clef-omni",
    "typesafe/jev-1.13",
)
CODE_FILES = (
    "p003_header_packets.py",
    "p003_header_packets_prepare.py",
    "p003_header_proposals.py",
    "pipeline_vision_transcription.py",
    "pipeline_frontier.py",
    "generalization_vision_regions.py",
    "p003_candidate_run.py",
    "generalization_report.py",
    "silver.py",
)


def authenticate(
    header_directory: Path, header_trust: Path, generation_directory: Path, generation_trust: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Use external code authorities, authenticate original responses and replay every archived plan."""
    directory, trust, generation, gen_trust = [
        guard_path(p) for p in (header_directory, header_trust, generation_directory, generation_trust)
    ]
    frozen = json.loads((directory / "frozen.json").read_bytes())
    approved = json.loads(trust.read_bytes())
    if not approved or not frozen["code_sha256"]:
        raise ValueError("Independent header archive code authority required")
    for name, digest in frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or approved.get(name) != digest
            or sha((directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Archived header helper differs from external code approval")
    for name in ("p003_header_proposals.py", "pipeline_vision_transcription.py", "pipeline_frontier.py"):
        if sha(Path(__file__).with_name(name).read_bytes()) != approved.get(name):
            raise ValueError("Current literal hypothesis decoder differs from external authority")
    original_frozen, report, _ = baseline.authenticate(generation, json.loads(gen_trust.read_bytes()))
    if (
        frozen["records"] != original_frozen["records"]
        or len(frozen["records"]) != 16
        or frozen["baseline_config"] != original_frozen["config"]
        or Path(frozen["baseline_directory"]) != generation
        or frozen["baseline_frozen_sha256"] != sha((generation / "frozen.json").read_bytes())
        or frozen["baseline_report_sha256"] != sha((generation / "report.json").read_bytes())
    ):
        raise ValueError("Header archive and separately authenticated original generation differ")
    original = {r["id"]: r for r in report["results"]}
    plans = []
    for record in frozen["records"]:
        ident = record["id"]
        path = directory / f"{ident}-header-plan.json"
        if sha(path.read_bytes()) != frozen["plan_sha256"][ident]:
            raise ValueError("Archived header plan changed")
        plan = json.loads(path.read_bytes())
        page = original[ident]
        pdf = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(pdf) != record["pdf_sha256"]:
            raise ValueError("Original PDF bytes changed")
        with pylopdf.open(stream=pdf) as doc:
            source = doc[record["page_number"]]
            if list(source.rect) != page["viewport"] or source.rotation != page["original_rotation"]:
                raise ValueError("Original PDF display geometry changed")
        expected = regions.proposals(page["layout_detection"], page["viewport"])
        keys = ("index", "request_index", "viewport", "detector_box")
        if [{k: c[k] for k in keys} for c in expected] != [
            {k: c[k] for k in keys} for c in page["transcription_regions"]
        ]:
            raise ValueError("Original detector crop inventory changed")
        refusal = None
        for crop in page["transcription_regions"]:
            request_path = generation / f"{ident}-request-{crop['request_index']}.json"
            if not request_path.exists():
                refusal = "Missing complete original request; no unauthenticated hypothesis"
                continue
            body = json.loads(request_path.read_bytes())
            url, image = baseline._crop_bytes(body)
            rebuilt = strict.request(body["model"], url, crop["viewport"], body["max_tokens"])
            provider = original_frozen["config"].get("generation_provider")
            if provider:
                rebuilt["provider"] = {"only": [provider], "allow_fallbacks": False, "require_parameters": True}
            if (
                body["model"] != original_frozen["config"]["generation_model"]
                or rebuilt != body
                or sha(json.dumps(rebuilt, separators=(",", ":")).encode()) != crop["request"]["body_sha256"]
                or sha(image) != crop["image"]["image_sha256"]
                or len(image) != crop["image"]["image_bytes"]
                or crop["image"]["image_viewport"] != crop["viewport"]
            ):
                raise ValueError("Original request/pixel bytes or generation identity changed")
        replay = headers.freeze_page(page, input_refusal=refusal)
        replay["record"] = record
        if replay != plan:
            raise ValueError("Complete source-only header proposal replay differs from archive")
        plans.append(plan)
    return original_frozen, plans


def prepare(
    header_directory: Path,
    header_trust: Path,
    generation_directory: Path,
    generation_trust: Path,
    output: Path,
    *,
    seed: int = 20261010,
) -> dict[str, Any]:
    """Freeze all16 original outputs, four factorized menus and separate full/local text+image treatments."""
    started, cpu = time.perf_counter(), time.process_time()
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Require fresh header evidence freeze path")
    original_frozen, plans = authenticate(header_directory, header_trust, generation_directory, generation_trust)
    output.mkdir(parents=True)
    for name in ("code", "pages", "menus", "trust"):
        (output / name).mkdir()
    code = {}
    for name in CODE_FILES:
        data = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(data)
        code[name] = sha(data)
    receipts = []
    for name, directory, trust in (
        ("header", header_directory, header_trust),
        ("generation", generation_directory, generation_trust),
    ):
        (output / "trust" / f"{name}.json").write_bytes(trust.read_bytes())
        receipts.append(
            {
                "kind": name,
                "directory": str(directory),
                "trusted_code": str(trust),
                "trusted_code_sha256": sha(trust.read_bytes()),
                "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
                "report_sha256": sha((directory / "report.json").read_bytes()),
            }
        )
    frozen = {
        "schema": 1,
        "processor": "p003_header_packets",
        "records": original_frozen["records"],
        "code_sha256": code,
        "source_trust_receipts": receipts,
        "models": list(MODELS),
        "seed": seed,
        "evidence_modes": list(packets.MODES),
        "image_edges": [0, *packets.EDGES],
        "packet_cap_bytes": packets.MAX_PACKET_BYTES,
        "references_read": False,
        "fresh_confirmation_accessed": False,
        "hosted_calls": 0,
        "source_conserved": False,
        "original_failures_immutable": True,
        "fixed_tables_model_only_credit": False,
    }
    write_json(output / "frozen.json", frozen)
    pages, inventory = [], []
    for plan in plans:
        ident = plan["id"]
        menus = packets.menu_records(plan, seed)
        page_path = f"pages/{ident}.json"
        write_json(
            output / page_path,
            {"id": ident, "plan": plan, "menus": menus, "no_decision_control": packets.compose(plan, menus, {})},
        )
        pages.append(
            {
                "id": ident,
                "path": page_path,
                "sha256": sha((output / page_path).read_bytes()),
                "original_status": plan["original_page_status"],
                "menu_ids": [m["id"] for m in menus],
                "no_question_reason": None
                if menus
                else "No admitted ambiguous header menu; original output retained separately",
            }
        )
        for menu in menus:
            folder = output / "menus" / menu["id"]
            folder.mkdir()
            write_json(folder / "menu.json", menu)
            request_index = plan["original_page"]["transcription_regions"][menu["crop_index"]]["request_index"]
            original = json.loads((generation_directory / f"{ident}-request-{request_index}.json").read_bytes())
            original_url, _ = baseline._crop_bytes(original)
            image_variants: dict[int, str | None] = {0: None}
            variants = []
            for edge in packets.EDGES:
                url, image_metadata = packets.image_variant(
                    original_url, menu["crop_viewport"], menu["table_bbox"], edge
                )
                image_variants[edge] = url
                (folder / f"image-{edge}.png").write_bytes(base64.b64decode(url.split(",", 1)[1]))
                write_json(folder / f"image-{edge}.json", image_metadata)
            for mode in packets.MODES:
                for edge, variant_url in image_variants.items():
                    for model_index, model in enumerate(MODELS):
                        if model_index == 3 and edge:
                            continue
                        body, metadata = packets.request(menu, model, variant_url, mode)
                        prefix = f"{mode}-{edge}-m{model_index}"
                        write_json(folder / f"{prefix}-evidence.json", metadata)
                        entry = {
                            "mode": mode,
                            "image_edge": edge,
                            "model": model,
                            "evidence_path": f"menus/{menu['id']}/{prefix}-evidence.json",
                            "question_status": metadata["question_status"],
                            "evidence_sha256": metadata["evidence_sha256"],
                            "evidence_utf8_bytes": metadata["evidence_utf8_bytes"],
                            "request_path": None,
                        }
                        if body is not None:
                            body_path = folder / f"{prefix}-request.json"
                            write_json(body_path, body)
                            entry.update(
                                request_path=str(body_path.relative_to(output)),
                                request_sha256=sha(body_path.read_bytes()),
                                body_sha256=sha(json.dumps(body, separators=(",", ":")).encode()),
                            )
                        variants.append(entry)
            inventory.append(
                {
                    "menu_id": menu["id"],
                    "page_id": ident,
                    "crop_index": menu["crop_index"],
                    "table_index": menu["table_index"],
                    "option_count": len(menu["options"]),
                    "menu_path": f"menus/{menu['id']}/menu.json",
                    "menu_sha256": sha((folder / "menu.json").read_bytes()),
                    "variants": variants,
                }
            )
    report = {
        "page_count": len(pages),
        "menu_count": len(inventory),
        "pages": pages,
        "menus": inventory,
        "frozen_sha256": sha((output / "frozen.json").read_bytes()),
        "hosted_calls": 0,
        "references_read": False,
        "scope": "Factorized header selection over immutable generated literals; selected primary, fixed controls separate",
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "process perf_counter/process_time; getrusage lifetime peak includes imports, timed scope excludes imports",
            "process_scope": "one Python process, no child workers or model inference",
            "sampling_interval_seconds": None,
            "thread_environment": {
                n: os.environ.get(n) for n in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
            },
            "actual_native_thread_count": "unmeasured",
            "concurrency": "one CPU-only preparer; other campaign workers may contend",
        },
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run CPU-only preparation with explicit source archive and independent code maps."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "header_directory",
        "header_trusted_code",
        "generation_directory",
        "generation_trusted_code",
        "output",
    ):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261010)
    args = parser.parse_args()
    report = prepare(
        args.header_directory,
        args.header_trusted_code,
        args.generation_directory,
        args.generation_trusted_code,
        args.output,
        seed=args.seed,
    )
    print(json.dumps({k: v for k, v in report.items() if k not in ("pages", "menus")}, indent=2))


if __name__ == "__main__":
    main()
