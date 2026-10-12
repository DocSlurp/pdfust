"""Independent DEV ceiling over frozen complete literal-preserving header hypotheses."""

# ruff: noqa: EM101, TRY003, C901, PLC0415, SLF001
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from PIL import Image

import pdfust
from bench import generalization_vision_regions as regions
from bench import p003_candidate_run as baseline
from bench import p003_header_proposals as headers
from bench import p003_valid_regions_oracle as oracle
from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.p003_reviewed_compatibility import reviewed_precount_helper
from bench.silver import guard_path, sha


def read(path: Path) -> Any:  # noqa: ANN401
    """Read explicitly supplied guarded evidence."""
    return json.loads(guard_path(path).read_bytes())


def verify_page_inputs(
    directory: Path, record: dict[str, Any], page: dict[str, Any], config: dict[str, Any]
) -> str | None:
    """Regenerate crop pixels and exact frozen treatment bodies, including failed-page responses."""
    from bench import pipeline_vision_transcription as transcription

    raw = guard_path(Path(record["pdf_path"])).read_bytes()
    if sha(raw) != record["pdf_sha256"]:
        raise ValueError("Original header-hypothesis PDF changed")
    expected = regions.proposals(page["layout_detection"], page["viewport"])
    keys = ("index", "request_index", "viewport", "detector_box")
    if [{k: c[k] for k in keys} for c in page["transcription_regions"]] != [{k: c[k] for k in keys} for c in expected]:
        raise ValueError("Header hypotheses changed original acquisition inventory")
    refusal = None
    with pdfust.open(stream=raw) as document:
        source = document[record["page_number"]]
        if list(source.rect) != page["viewport"] or source.rotation != page["original_rotation"]:
            raise ValueError("Original header source display geometry changed")
        image = None
        if expected:
            pixels = source.render(
                scale=(regions.RENDER_EDGE - 1) / max(source.rect.width, source.rect.height), background=(255, 255, 255)
            )
            with Image.open(io.BytesIO(pixels)) as opened:
                image = opened.convert("RGB")
        for crop in page["transcription_regions"]:
            index = crop["request_index"]
            request_path = directory / f"{record['id']}-request-{index}.json"
            if not request_path.exists():
                refusal = "Missing complete original request; no unauthenticated hypothesis"
                continue
            url, metadata = regions._crop(
                image,
                page["viewport"],
                crop["viewport"],
                config.get("image_edge", regions.CROP_EDGE),
                config.get("jpeg_quality", regions.JPEG_QUALITY),
            )
            if metadata != crop["image"]:
                raise ValueError("Header crop pixels differ from source PDF reconstruction")
            body = transcription.request(
                config["generation_model"], url, crop["viewport"], max_tokens=config.get("generation_tokens", 16384)
            )
            if config.get("generation_provider"):
                body["provider"] = {
                    "only": [config["generation_provider"]],
                    "allow_fallbacks": False,
                    "require_parameters": True,
                }
            encoded = json.dumps(body, separators=(",", ":")).encode()
            if (
                read(request_path) != body
                or crop["request"]["body_sha256"] != sha(encoded)
                or crop["request"]["body_bytes"] != len(encoded)
            ):
                raise ValueError("Header request differs from frozen model/pixels/token policy")
            if read(directory / f"{record['id']}-response-{index}.json") != crop["transcription_response"]:
                raise ValueError("Header literal response differs from original archive")
            indexes = crop["call_indexes"]
            if len(indexes) != 1:
                raise ValueError("Header response lacks unique original call attribution")
            call = page["calls"][indexes[0]]
            entry = call["entry"]
            if (
                call.get("replayed")
                or entry.get("request_sha256") != sha(encoded)
                or entry.get("requested_model") != config["generation_model"]
            ):
                raise ValueError("Header response original model/request attribution differs")
    return refusal


def analyze(
    directory: Path, corpus: Path, *, trusted_code: dict[str, str], baseline_trusted_code: dict[str, str]
) -> dict[str, Any]:
    """Rebuild every source-frozen complete hypothesis before loading separate DEV targets."""
    directory, corpus = guard_path(directory), guard_path(corpus)
    frozen = read(directory / "frozen.json")
    if (
        frozen["references_read"] is not False
        or frozen["hosted_calls"] != 0
        or not frozen["no_default_parser_repair"]
        or not frozen["no_original_baseline_mutation"]
    ):
        raise ValueError("Expected source-only explicit header-hypothesis freeze")
    for name, digest in frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or trusted_code.get(name) != digest
            or sha((directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Header code archive lacks independent source authentication")
        if (
            name != "p003_header_proposals_prepare.py"
            and sha(Path(headers.__file__).with_name(name).read_bytes()) != digest
        ):
            if name == "p003_candidate_run.py" and reviewed_precount_helper(
                (directory / "code" / name).read_bytes(),
                Path(headers.__file__).with_name(name).read_bytes(),
                frozen["baseline_config"],
                frozen["records"],
            ):
                continue
            raise ValueError("Current header replay helper differs from authenticated freeze")
    if frozen["external_trusted_code"] != baseline_trusted_code:
        raise ValueError("Embedded baseline map differs from external authority")
    copied = directory / "baseline"
    original_frozen, original_report, _ = baseline.authenticate(copied, baseline_trusted_code)
    if (
        sha((copied / "frozen.json").read_bytes()) != frozen["baseline_frozen_sha256"]
        or sha((copied / "report.json").read_bytes()) != frozen["baseline_report_sha256"]
        or original_frozen["records"] != frozen["records"]
        or original_frozen["manifest_sha256"] != frozen["manifest_sha256"]
        or original_frozen["config"] != frozen["baseline_config"]
    ):
        raise ValueError("Original header baseline provenance changed")
    rows = {p["id"]: p for p in original_report["results"]}
    if set(frozen["plan_sha256"]) != {r["id"] for r in frozen["records"]}:
        raise ValueError("Header inventory drops intended pages")
    inventories = []
    plans = []
    for record in frozen["records"]:
        ident = record["id"]
        page = rows[ident]
        refusal = verify_page_inputs(copied, record, page, original_frozen["config"])
        plan = headers.freeze_page(page, input_refusal=refusal)
        plan["record"] = record
        path = directory / f"{ident}-header-plan.json"
        if sha(path.read_bytes()) != frozen["plan_sha256"][ident] or read(path) != plan:
            raise ValueError("Frozen header plan differs from complete literal/pixel reconstruction")
        choices = [
            ((i,), {"id": ident, "status": "ok", "tables": item["state"]["tables"]})
            for i, item in enumerate(plan["complete_page_alternatives"])
        ]
        inventories.append(choices)
        plans.append(plan)
    # No reference participates in packet authentication, hypothesized partition generation or enumeration.
    _, targets = load_corpus(corpus)
    if sha((corpus / "manifest.json").read_bytes()) != frozen["manifest_sha256"]:
        raise ValueError("DEV references differ from frozen header source inventory")
    refs = {p["id"]: p for p in targets["pages"]}
    outcomes = [oracle.oracle_page(refs[p["id"]], c) for p, c in zip(plans, inventories, strict=True)]
    return {
        "scope": "Posthoc DEV hypothetical header ceiling; no model selection or parser-repair success claim",
        "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "code_sha256": frozen["code_sha256"],
        "original_generation_scores": strict_scores(targets["pages"], original_report["results"]),
        "scores": strict_scores(targets["pages"], [o["selected"] for o in outcomes]),
        "independent_complete_table_ceiling": sum(o["maximum_complete_tables"] for o in outcomes),
        "complete_hypotheses": sum(len(c) for c in inventories),
        "pages": [
            {
                "id": p["id"],
                "original_status": p["original_page_status"],
                "proposal_status": p["status"],
                "alternatives": len(c),
                "oracle_alternative_indexes": o["origins"],
                "score": o.get("score"),
            }
            for p, c, o in zip(plans, inventories, outcomes, strict=True)
        ],
        "original_failures_preserved": True,
        "source_conserved": False,
        "new_api_calls": 0,
    }
