"""Freeze and optionally execute bounded DEV image ablations with provider-aware batches."""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import time
from copy import deepcopy
from pathlib import Path
from statistics import mean
from typing import Any

from PIL import Image

from bench.decision_context_cases import context_cases
from bench.decision_context_prompts import parse_assembly_response
from bench.decision_hosted import ARTIFACTS, RESERVATION, DecisionClient, accounted_cost, checkpoint, exclusive_lock
from bench.decision_image_matrix import VariantCache, build_request, default_arms
from bench.decision_records import materialize, score_records
from bench.reprice_model_rates import request_cost
from bench.silver import rss_bytes
from bench.silver_image_cases import model_question, silver_image_cases

MODELS = (
    "openai/gpt-6-luna-decisions",
    "perplexity/pplx-decider-v1.1-27b",
    "cloudflare/clef-flash",
    "cloudflare/clef",
)
BATCH_SIZE = 6
MAX_BODY_BYTES = 750_000
CLEF_TEXT_BYTES = 4000
CLEF_IMAGE_CHARACTERS = 200_000
CLEF_PNG_BYTES = 145_000
WAVE_LIMIT = 2.0
DEFAULT_DIRECTORY = ARTIFACTS / "image-resolution-matrix"
DEFAULT_REPORT = Path("bench/results/image-resolution-matrix.md")


def encode(body: dict[str, Any]) -> bytes:
    """Use the shared client's exact canonical encoding for frozen identity."""
    return json.dumps(body, separators=(",", ":")).encode()


def batch_request(
    cases: list[dict[str, Any]], model: str, variants: list[dict[str, Any] | None], *, native: bool = False
) -> dict[str, Any]:
    """Isolate independent observations using matching question markers and instructions."""
    if not 1 <= len(cases) <= BATCH_SIZE or len(variants) != len(cases):
        message = "Image matrix batches require one to six matching observations"
        raise ValueError(message)
    state: list[Any] = []
    questions = {}
    for index, (case, variant) in enumerate(zip(cases, variants, strict=True)):
        singleton = build_request(case, model, variant, native=native)
        marker = f"q{index}"
        observation = singleton["state"]
        state.append(f"Observation {marker}: consider only this observation for question {marker}.")
        state.extend(observation if isinstance(observation, list) else [json.dumps(observation, separators=(",", ":"))])
        state.append(f"End observation {marker}.")
        question = deepcopy(singleton["questions"]["q0"])
        question["instructions"] = (
            f"Consider only corresponding observation {marker}; other observations are independent. "
            + question["instructions"]
        )
        questions[marker] = question
    body = {"model": model, "state": state, "questions": questions}
    if len(encode(body)) > MAX_BODY_BYTES:
        message = "Image matrix batch exceeds request byte admission"
        raise ValueError(message)
    return body


def silver_batch_request(variants: list[dict[str, Any]], model: str) -> dict[str, Any]:
    """Ask fixed image-only table presence for each opaque observation marker."""
    state: list[Any] = []
    questions = {}
    fixed = model_question()
    for index, variant in enumerate(variants):
        marker = f"q{index}"
        state.extend(
            [
                f"Observation {marker}: whole page image, independent of all other observations.",
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:"
                        + variant.get("mime", "image/png")
                        + ";base64,"
                        + base64.b64encode(variant["data"]).decode("ascii"),
                        "detail": "high",
                    },
                },
                f"End observation {marker}.",
            ]
        )
        questions[marker] = {
            "type": "choice",
            "instructions": f"Consider only corresponding observation {marker}. " + fixed["question"],
            "criteria": fixed["choices"],
        }
    body = {"model": model, "state": state, "questions": questions}
    if not 1 <= len(variants) <= BATCH_SIZE or len(encode(body)) > MAX_BODY_BYTES:
        message = "Silver batch exceeds observation or byte admission"
        raise ValueError(message)
    return body


def provider_transport(variant: dict[str, Any] | None, model: str) -> dict[str, Any] | None:
    """Preserve pixels with lossless WebP when Clef's base64 admission requires it."""
    if variant is None or not model.startswith("cloudflare/clef") or len(variant["data"]) <= CLEF_PNG_BYTES:
        return variant
    with Image.open(io.BytesIO(variant["data"])) as opened:
        original = opened.convert("RGB")
        buffer = io.BytesIO()
        original.save(buffer, format="WEBP", lossless=True, method=6)
    data = buffer.getvalue()
    with Image.open(io.BytesIO(data)) as decoded:
        if original.tobytes() != decoded.convert("RGB").tobytes():
            message = "Lossless transport changed decoded pixels"
            raise ValueError(message)
    return {
        **variant,
        "data": data,
        "mime": "image/webp",
        "bytes": len(data),
        "source_png_bytes": len(variant["data"]),
        "transport_codec": "WebP lossless",
        "transport_sha256": hashlib.sha256(data).hexdigest(),
        "decoded_pixels_equal": True,
    }


def admitted_batches(
    cases: list[dict[str, Any]],
    variants: list[dict[str, Any] | None],
    model: str,
    *,
    silver: bool,
    native: bool = False,
) -> list[tuple[int, list[dict[str, Any]], list[dict[str, Any] | None], dict[str, Any]]]:
    """Bound Clef images/text and split batches before transmission.

    Clef supports at most four images and truncates long source text. Its
    batches additionally cap source text and base64 image bytes conservatively.
    Other models retain up to six observations, split when encoded bytes require it.
    """
    output = []
    variants = [provider_transport(variant, model) for variant in variants]
    offset = 0
    while offset < len(cases):
        count = min(4 if model.startswith("cloudflare/clef") else BATCH_SIZE, len(cases) - offset)
        while True:
            chosen = cases[offset : offset + count]
            images = variants[offset : offset + count]
            try:
                body = (
                    silver_batch_request([v for v in images if v is not None], model)
                    if silver
                    else batch_request(chosen, model, images, native=native)
                )
            except ValueError:
                if count == 1:
                    raise
                count = max(1, count // 2)
                continue
            if model.startswith("cloudflare/clef"):
                text_bytes = sum(len(item.encode()) for item in body["state"] if isinstance(item, str))
                image_characters = sum(
                    len(item["image_url"]["url"])
                    for item in body["state"]
                    if isinstance(item, dict) and "image_url" in item
                )
                if text_bytes > CLEF_TEXT_BYTES or image_characters > CLEF_IMAGE_CHARACTERS:
                    if count == 1:
                        message = "Clef source text or image transport exceeds provider admission"
                        raise ValueError(message)
                    count = max(1, count // 2)
                    continue
            break
        output.append((offset, chosen, images, body))
        offset += count
    return output


def arm_name(configuration: dict[str, Any]) -> str:
    """Name one declared condition independently of case labels."""
    if "edge" not in configuration:
        return "native" if configuration["native"] else "current"
    return f"{configuration['mode']}-{configuration['edge']}" + ("-blank" if configuration["blank"] else "")


def prepare(
    directory: Path,
    models: list[str],
    scope: str,
    *,
    prices_path: Path | None = None,
    silver_directory: Path | None = None,
) -> dict[str, Any]:
    """Freeze every body before constructing any credential-bearing hosted client."""
    directory.mkdir(parents=True, exist_ok=True)
    frozen = directory / "manifest.json"
    if frozen.exists():
        manifest = json.loads(frozen.read_text())
        if (
            manifest["models"] != models
            or manifest["scope"] != scope
            or manifest.get("silver_directory") != (str(silver_directory) if silver_directory else None)
        ):
            message = "Existing frozen matrix has different models or scope; choose a new directory"
            raise ValueError(message)
        verify_manifest(directory, manifest)
        return manifest
    start, cpu = time.perf_counter(), time.process_time()
    cases = silver_image_cases(silver_directory) if silver_directory is not None else context_cases()
    cache = VariantCache(directory / "images")
    batches = []
    scopes = ["page"] if silver_directory is not None else ["region", "page"] if scope == "both" else [scope]
    for selected_scope in scopes:
        configurations = (
            default_arms(full_page=True)
            if silver_directory is not None
            else [{"native": False}, {"native": True}, *default_arms(full_page=selected_scope == "page")]
        )
        for configuration in configurations:
            arm = arm_name(configuration)
            for offset in range(0, len(cases), BATCH_SIZE):
                selected = cases[offset : offset + BATCH_SIZE]
                variants = [
                    cache.make_variant(
                        case["pdf_bytes"],
                        None if selected_scope == "page" else case["evidence"]["current_region"],
                        edge=configuration["edge"],
                        mode=configuration["mode"],
                        blank=configuration["blank"],
                        page_index=case.get("page_index", 0),
                    )
                    if "edge" in configuration
                    else None
                    for case in selected
                ]
                for model in models:
                    for relative, chosen, images, body in admitted_batches(
                        selected,
                        variants,
                        model,
                        silver=silver_directory is not None,
                        native=bool(configuration.get("native", False)),
                    ):
                        data = encode(body)
                        key = hashlib.sha256(data).hexdigest()
                        request_path = directory / f"request-{key}.json"
                        request_path.write_bytes(data)
                        batches.append(
                            {
                                "model": model,
                                "scope": selected_scope,
                                "arm": arm,
                                "configuration": configuration,
                                "offset": offset + relative,
                                "case_indices": list(range(offset + relative, offset + relative + len(chosen))),
                                "case_ids": [case["id"] for case in chosen],
                                "source_sha256": [hashlib.sha256(case["pdf_bytes"]).hexdigest() for case in chosen],
                                "expected_document": [
                                    case["expected_document"]
                                    if silver_directory is not None
                                    else case["gold"]["choice"]
                                    for case in chosen
                                ],
                                "request_sha256": key,
                                "request_file": request_path.name,
                                "request_bytes": len(data),
                                "images": [
                                    {k: v for k, v in image.items() if k != "data"} if image else None
                                    for image in images
                                ],
                            }
                        )
    prices = json.loads(prices_path.read_text()) if prices_path is not None and prices_path.exists() else {}
    paths = [
        Path(__file__),
        Path("bench/decision_image_matrix.py"),
        Path("bench/decision_context_compact.py"),
        Path("bench/decision_context_cases.py"),
        Path("bench/decision_records.py"),
        Path("bench/decision_context_prompts.py"),
        Path("bench/reprice_model_rates.py"),
    ]
    manifest = {
        "schema": 1,
        "models": models,
        "scope": scope,
        "silver_directory": str(silver_directory) if silver_directory else None,
        "task": "silver-table-presence" if silver_directory else "context-assembly",
        "batches": batches,
        "prices": prices.get("prices", {}),
        "pricing_provenance": {k: v for k, v in prices.items() if k != "prices"},
        "code_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "preparation": {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "current process, serial CPU; perf_counter/process_time; VmHWM lifetime RSS bytes; no sampling",
        },
        "evidence_exact": "not validated for transformed images; full-source recovery only",
        "dev_status": "125 physical DEV silver pages; authored gate labels; 10 positives and 115 negatives"
        if silver_directory
        else "30 DEV cases; ten correlated templates across three vocabularies",
    }
    checkpoint(frozen, manifest)
    return manifest


def verify_manifest(directory: Path, manifest: dict[str, Any]) -> None:
    """Verify all frozen bodies and bounded sizes before any paid call."""
    for batch in manifest["batches"]:
        name = batch["request_file"]
        if Path(name).name != name:
            message = "Frozen request path escapes artifact directory"
            raise ValueError(message)
        data = (directory / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != batch["request_sha256"] or len(data) > MAX_BODY_BYTES:
            message = "Frozen request hash or byte admission mismatch"
            raise ValueError(message)


def wave_admission(entries: list[dict[str, Any]], start: int, *, limit: float = WAVE_LIMIT) -> None:
    """Count retained reservations and refuse the next crossing request before transmission."""
    if sum(accounted_cost(entry["accounted_usd"]) for entry in entries[start:]) + RESERVATION > limit:
        message = "Image matrix incremental wave budget exhausted"
        raise RuntimeError(message)


def run(  # noqa: C901, PLR0912
    directory: Path,
    manifest: dict[str, Any],
    *,
    client: Any = None,  # noqa: ANN401
    wave_name: str = "image-resolution-wave.json",
) -> dict[str, Any]:
    """Opt-in execution; retain failures and mark all stopped-model batches unattempted."""
    verify_manifest(directory, manifest)
    if Path(wave_name).name != wave_name or not wave_name.endswith(".json"):
        message = "Wave accounting name must be a local JSON filename"
        raise ValueError(message)
    cases = (
        silver_image_cases(Path(manifest["silver_directory"])) if manifest.get("silver_directory") else context_cases()
    )
    result_path = directory / "results.json"
    report: dict[str, Any] = (
        json.loads(result_path.read_text()) if result_path.exists() else {"schema": 1, "batches": []}
    )
    client = DecisionClient() if client is None else client
    entries = json.loads(client.ledger.read_text())["requests"] if client.ledger.exists() else []
    wave_path = client.ledger.parent / wave_name
    if wave_path.exists():
        wave = json.loads(wave_path.read_text())
    else:
        wave = {"wave_start": report.get("wave_start", len(entries)), "wave_limit_usd": WAVE_LIMIT}
        checkpoint(wave_path, wave)
    report["wave_start"] = wave["wave_start"]
    report["wave_limit_usd"] = wave["wave_limit_usd"]
    completed = {(r["model"], r["scope"], r["arm"], r["offset"]): r for r in report["batches"]}
    stopped = {r["model"] for r in report["batches"] if r["status"] == "failed"}
    report["batches"] = [
        completed.get((b["model"], b["scope"], b["arm"], b["offset"]), {**b, "status": "unattempted"})
        for b in manifest["batches"]
    ]
    checkpoint(result_path, report)
    for position, batch in enumerate(manifest["batches"]):
        identity = (batch["model"], batch["scope"], batch["arm"], batch["offset"])
        old = completed.get(identity)
        if old is not None and old["status"] in {"ok", "failed"}:
            continue
        row = {**batch, "status": "unattempted"}
        if batch["model"] in stopped or report.get("budget_exhausted"):
            row["reason"] = "model stopped after failure" if batch["model"] in stopped else "wave budget exhausted"
        else:
            entries = json.loads(client.ledger.read_text())["requests"] if client.ledger.exists() else []
            known = next((entry for entry in entries if entry["request_sha256"] == batch["request_sha256"]), None)
            try:
                if known is not None and not known.get("response_file"):
                    message = "Previously failed identical request; no retry"
                    raise RuntimeError(message)  # noqa: TRY301
                if known is None:
                    wave_admission(entries, report["wave_start"], limit=report["wave_limit_usd"])
                body = json.loads((directory / batch["request_file"]).read_text())
                response = client.request(
                    body,
                    tag=f"image-matrix/{batch['scope']}/{batch['model']}/{batch['arm']}/{batch['offset']}",
                    max_body_bytes=MAX_BODY_BYTES,
                )
                row.update(
                    {
                        "entry": response["entry"],
                        "usage": response["result"].get("usage", {}),
                        "replayed": response["replayed"],
                    }
                )
                answers = parse_assembly_response(response["result"], len(batch["case_indices"]))
                observations = []
                for index, answer in zip(batch["case_indices"], answers, strict=True):
                    if manifest.get("silver_directory"):
                        expected = cases[index]["expected_document"]
                        observations.append(
                            {
                                "case_id": cases[index]["id"],
                                "answer": answer,
                                "expected_document": expected,
                                "score": {"region_exact": answer["choice"] == expected, "record_f1": None},
                            }
                        )
                    else:
                        assembly = materialize(cases[index], answer["choice"])
                        observations.append(
                            {
                                "case_id": cases[index]["id"],
                                "answer": answer,
                                "assembly": assembly,
                                "score": score_records(cases[index], assembly),
                            }
                        )
                row.update({"status": "ok", "observations": observations})
            except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
                row.update({"status": "failed", "error": str(error)})
                retained = json.loads(client.ledger.read_text())["requests"] if client.ledger.exists() else []
                failed_entry = next((e for e in retained if e["request_sha256"] == batch["request_sha256"]), None)
                if failed_entry is not None:
                    row.setdefault("entry", failed_entry)
                if "wave budget exhausted" in str(error):
                    report["budget_exhausted"] = True
                    row["status"] = "unattempted"
                else:
                    stopped.add(batch["model"])
        report["batches"][position] = row
        checkpoint(result_path, report)
    checkpoint(result_path, report)
    return report


def summarize(manifest: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Deduplicate API charges and pair image/blank observations by exact case ID."""
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    unique = {}
    for row in report["batches"]:
        groups.setdefault((row["model"], row["scope"], row["arm"]), []).append(row)
        if "entry" in row:
            unique[row["entry"]["index"]] = row
    costs = [
        request_cost(
            row["entry"],
            row.get("usage", {}),
            row["entry"].get("catalog_rates") or manifest["prices"].get(row["model"], {}),
        )
        for row in unique.values()
    ]
    summary = []
    for (model, scope, arm), batches in groups.items():
        observations = [obs for batch in batches for obs in batch.get("observations", [])]
        by_case = {obs["case_id"]: obs for obs in observations}
        blank_rows = groups.get((model, scope, arm + "-blank"), [])
        blanks = {obs["case_id"]: obs for batch in blank_rows for obs in batch.get("observations", [])}
        paired = set(by_case) & set(blanks)
        entries = {batch["entry"]["index"]: batch for batch in batches if "entry" in batch}
        arm_costs = [
            request_cost(b["entry"], b.get("usage", {}), manifest["prices"].get(model, {})) for b in entries.values()
        ]
        summary.append(
            {
                "model": model,
                "scope": scope,
                "arm": arm,
                "n": len(observations),
                "errors": sum(batch["status"] == "failed" for batch in batches),
                "unattempted": sum(len(batch["case_indices"]) for batch in batches if batch["status"] == "unattempted"),
                "exact": sum(obs["score"]["region_exact"] for obs in observations),
                "record_f1": mean(obs["score"]["record_f1"] for obs in observations)
                if observations and not manifest.get("silver_directory")
                else None,
                "paired_blank_n": len(paired),
                "paired_blank_exact_delta": sum(
                    int(by_case[key]["score"]["region_exact"]) - int(blanks[key]["score"]["region_exact"])
                    for key in paired
                ),
                "request_bytes": sum(batch["request_bytes"] for batch in entries.values()),
                "api_elapsed_ms": sum(batch["entry"].get("elapsed_ms", 0) for batch in entries.values()),
                "input_tokens": sum(
                    b.get("usage", {}).get("input_tokens", b.get("usage", {}).get("prompt_tokens", 0))
                    for b in entries.values()
                ),
                "output_tokens": sum(
                    b.get("usage", {}).get("output_tokens", b.get("usage", {}).get("completion_tokens", 0))
                    for b in entries.values()
                ),
                "effective_usd": None
                if not arm_costs or any(c["effective_usd"] is None for c in arm_costs)
                else sum(c["effective_usd"] for c in arm_costs),
                "cost_estimated": any(c["basis"] == "catalog estimate" for c in arm_costs),
            }
        )
    if manifest.get("silver_directory"):
        for row in summary:
            observations = [
                obs
                for batch in groups[(row["model"], row["scope"], row["arm"])]
                for obs in batch.get("observations", [])
            ]
            tp = sum(o["expected_document"] == "A" and o["answer"]["choice"] == "A" for o in observations)
            fp = sum(o["expected_document"] == "B" and o["answer"]["choice"] == "A" for o in observations)
            fn = sum(o["expected_document"] == "A" and o["answer"]["choice"] != "A" for o in observations)
            tn = sum(o["expected_document"] == "B" and o["answer"]["choice"] == "B" for o in observations)
            negatives = sum(o["expected_document"] == "B" for o in observations)
            row.update(
                {
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "tn": tn,
                    "precision": tp / (tp + fp) if tp + fp else None,
                    "recall": tp / (tp + fn) if tp + fn else None,
                    "specificity": tn / negatives if negatives else None,
                    "unresolved": sum(o["answer"]["choice"] == "unresolved" for o in observations),
                }
            )
    return {
        "rows": summary,
        "unique_requests": len(unique),
        "costs": costs,
        "effective_usd": None
        if not costs or any(c["effective_usd"] is None for c in costs)
        else sum(c["effective_usd"] for c in costs),
    }


def write_report(directory: Path, path: Path) -> dict[str, Any]:
    """Write compact Markdown from retained local scores and pricing only."""
    manifest = json.loads((directory / "manifest.json").read_text())
    report = json.loads((directory / "results.json").read_text())
    summary = summarize(manifest, report)
    if "declared_axes" in manifest:
        from bench.image_axes_report import markdown, snapshot  # noqa: PLC0415

        path.write_text(markdown([snapshot(directory)]))
        return summary
    lines = [
        "# DEV image resolution matrix",
        "",
        manifest["dev_status"] + ". These results do not establish real-world quality or generalization.",
        "",
        "**Image conditions:** RGB8, grayscale8 and indexed color4, each at 128, 512 and 1200 px. Every image has a matched blank. Batch sizes depend on provider limits and request size; cross-observation influence remains possible.",
        "",
        "Full-source exact recovery is scored through complete record materialization. Transformed-image evidence exactness is not validated. Optional monochrome conversion can erase pale fills; it is excluded from this matrix. Region crops exclude convention notes, while full-page images include them.",
        "",
        f"Unique completed/charged requests: {summary['unique_requests']}; effective USD: {summary['effective_usd']}. Positive provider-reported costs win; other effective costs use retained catalog token rates when available. Reservations remain admission accounting, and missing prices/usage remain unknown.",
        "",
    ]
    for model in dict.fromkeys(row["model"] for row in summary["rows"]):
        rows = [row for row in summary["rows"] if row["model"] == model]
        lines.extend(
            [
                "",
                f"## `{model}`",
                "",
                "**Quality and completion**",
                "",
                "| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in rows:
            f1 = "—" if row["record_f1"] is None else f"{row['record_f1']:.3f}"
            lines.append(
                f"| {row['scope']} | {row['arm']} | {row['n']} | {row['errors']} | {row['unattempted']} | {row['exact']} | {f1} | {row['paired_blank_n']} / {row['paired_blank_exact_delta']:+d} |"
            )
        lines.extend(
            [
                "",
                "**Usage and cost**",
                "",
                "| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |",
                "| --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in rows:
            cost = row["effective_usd"]
            formatted_cost = "unknown" if cost is None else ("~" if row["cost_estimated"] else "") + f"{cost:.6f}"
            lines.append(
                f"| {row['scope']} | {row['arm']} | {row['input_tokens']} / {row['output_tokens']} | {row['request_bytes']} | {row['api_elapsed_ms']:.0f} | {formatted_cost} |"
            )
    if manifest.get("silver_directory"):
        lines.extend(
            [
                "",
                "Silver scores measure authored ruled-table presence only, not transcription or structure. Unresolved positives count as false negatives; unresolved negatives reduce specificity.",
                "",
                "| Model | Arm | TP | FP | FN | TN | Precision | Recall | Specificity | Unresolved |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in summary["rows"]:
            metrics = ["unknown" if row[k] is None else f"{row[k]:.3f}" for k in ("precision", "recall", "specificity")]
            lines.append(
                f"| {row['model']} | {row['arm']} | {row['tp']} | {row['fp']} | {row['fn']} | {row['tn']} | {' | '.join(metrics)} | {row['unresolved']} |"
            )
    lines.extend(
        [
            "",
            "## Local preparation resources",
            "",
            "```json",
            json.dumps(manifest["preparation"], sort_keys=True, indent=2),
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    checkpoint(directory / "summary.json", summary)
    return summary


def main() -> None:
    """Prepare and report without credentials; require explicit opt-in for hosted calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--scope", choices=["region", "page", "both"], default="both")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--prices", type=Path, default=ARTIFACTS / "langfuse/catalog-prices.json")
    parser.add_argument("--silver-directory", type=Path)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    if args.report_only:
        write_report(args.directory, args.report)
        return
    manifest = prepare(
        args.directory, args.models, args.scope, prices_path=args.prices, silver_directory=args.silver_directory
    )
    print(
        json.dumps(
            {
                "batches": len(manifest["batches"]),
                "observations": sum(len(b["case_indices"]) for b in manifest["batches"]),
            }
        )
    )
    if args.run_hosted:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(ARTIFACTS / "run.lock"):
            run(args.directory, manifest)
        write_report(args.directory, args.report)


if __name__ == "__main__":
    main()
