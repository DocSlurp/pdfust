"""Root-only independent synthetic relationship treatments; source-only preflight."""

# ruff: noqa: ANN401, EM101, TRY003, TRY301, C901, PLR0912, PLR0913, PLR2004, E501, PLC0415
from __future__ import annotations

import argparse
import base64
import json
import math
import resource
import shutil
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from bench import p003_synthetic_relations as evidence
from bench.decision_hosted import DECISION_MODELS, ROOT
from bench.silver import guard_path, sha, write_json

IMAGE_MODELS = (
    "perplexity/pplx-decider-v1.1-27b",
    "openai/gpt-6-luna-decisions",
    "cloudflare/clef-flash",
    "cloudflare/clef",
    "cloudflare/clef-omni",
)
SOURCE_CODE = (
    "p003_synthetic_relations.py",
    "p003_synthetic_relations_prepare.py",
    "feature_cases.py",
    "pipeline_row_evidence.py",
    "pipeline_regions.py",
    "silver.py",
)
CODE_FILES = tuple(
    dict.fromkeys(
        (
            "p003_synthetic_relations_run.py",
            *SOURCE_CODE,
            "decision_hosted.py",
            "p003_client.py",
            "decision_concurrent.py",
            "decision_gateway.py",
            "research_policy.py",
            "decision_langfuse.py",
            "reprice_model_rates.py",
            "p003_boundary_run.py",
            "pipeline_run.py",
            "generalization_run.py",
            "pipeline_frontier.py",
            "decision_p003_native.py",
            "decision_p003_boundaries.py",
            "pipeline_assembly.py",
            "pipeline_source_order.py",
            "pipeline_repair.py",
        )
    )
)
RESERVATION = 0.30
ROUNDING_TOLERANCE = 0.015 + 1e-9


def configuration(
    model: str,
    *,
    mode: str = "text_geometry",
    image_edge: int = 0,
    viewport: str = "page",
    transport_concurrency: int = 3,
) -> dict[str, Any]:
    """Admit registered native OpenRouter models only; treatments never change providers."""
    if model not in DECISION_MODELS or mode not in evidence.MODES or viewport not in {"page", "crop"}:
        raise ValueError("Registered model and explicit evidence/viewport required")
    if (
        type(image_edge) is not int
        or image_edge not in {0, *evidence.EDGES}
        or (image_edge and model not in IMAGE_MODELS)
    ):
        raise ValueError("Only five declared image models and edges0/128/512 admitted")
    if type(transport_concurrency) is not int or transport_concurrency not in {1, 3}:
        raise ValueError("Transport concurrency must be1or3; no Gateway parallel transport")
    return {
        "campaign": "P003",
        "processor": "p003_synthetic_relations",
        "provider": "openrouter",
        "model": model,
        "mode": mode,
        "image_edge": image_edge,
        "viewport": viewport,
        "transport_concurrency": transport_concurrency,
        "run_hosted": True,
        "replay": False,
        "retry": False,
        "model_fallback": False,
        "source_assignments": False,
        "gold_accessed": False,
        "first_transport_failure": "stop remaining cases; malformed answers continue distinct cases",
        "scope": "One local relationship question per authored page; no complete table/page extraction",
    }


def _path(root: Path, name: str) -> Path:
    parts = Path(name).parts
    if len(parts) != 2 or parts[0] not in {"pdfs", "sources", "packets", "images"} or parts[1] in {".", ".."}:
        raise ValueError("Only explicit source artifacts admitted; labels or arbitrary paths refused")
    return guard_path(root / name)


def authenticate(pool: Path, trusted: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Replay complete actual source/PDF/drawing/packet/image evidence without opening or enumerating gold."""
    pool = guard_path(pool)
    frozen = json.loads((pool / "frozen.json").read_bytes())
    if trusted.get("source_frozen_sha256") != sha((pool / "frozen.json").read_bytes()):
        raise ValueError("Source frozen inventory differs from independent external authority")
    if (
        frozen.get("source_only") is not True
        or frozen.get("gold_in_prompt") is not False
        or frozen.get("intended_case_count") != 24
    ):
        raise ValueError("Explicit source-only24-case authority required")
    if set(frozen["code_sha256"]) != set(SOURCE_CODE):
        raise ValueError("Unexpected source code inventory")
    for name, digest in frozen["code_sha256"].items():
        if trusted.get(name) != digest or sha((pool / "code" / name).read_bytes()) != digest:
            raise ValueError("Source archived code differs from independent authority")
    for name in (
        "p003_synthetic_relations.py",
        "feature_cases.py",
        "pipeline_row_evidence.py",
        "pipeline_regions.py",
        "silver.py",
    ):
        if sha(Path(evidence.__file__).with_name(name).read_bytes()) != trusted[name]:
            raise ValueError("Current pure source replay dependency differs from independently approved bytes")
    for name, digest in frozen["artifact_sha256"].items():
        if sha(_path(pool, name).read_bytes()) != digest:
            raise ValueError("Frozen source artifact changed")
    identities = [r["id"] for r in frozen["records"]]
    if (
        len(identities) != 24
        or len(set(identities)) != 24
        or Counter(r["kind"] for r in frozen["records"]) != dict.fromkeys(evidence.KINDS, 8)
    ):
        raise ValueError("Complete24case/three-kind denominator required")
    records = []
    for entry in frozen["records"]:
        path = _path(pool, entry["path"])
        if sha(path.read_bytes()) != entry["sha256"]:
            raise ValueError("Source record changed")
        record = json.loads(path.read_bytes())
        if any(record[k] != entry[k] for k in ("id", "kind", "status", "pdf_sha256")):
            raise ValueError("Record identity/status changed")
        if record["status"] != "ready":
            records.append(record)
            continue
        words = record["source"]["words"]
        by_id = {w["id"]: w["text"] for w in words}
        pair = record["pair_source_ids"]
        if len(pair) != 2 or pair[0] == pair[1] or any(i not in by_id for i in pair):
            raise ValueError("Unique pair IDs required")
        pdf = _path(pool, record["pdf_path"]).read_bytes()
        literals = [by_id[i] for i in pair] + [w["text"] for w in words if w["id"] not in pair]
        source, actual_pair, drawings = evidence.extract(pdf, literals)
        if (
            sha(pdf) != record["pdf_sha256"]
            or source != record["source"]
            or actual_pair != pair
            or drawings != record["drawings"]
        ):
            raise ValueError("Actual source/PDF/drawings/pair mapping replay differs")
        if len(record["images"]) != 4 or len(record["packets"]) != 4:
            raise ValueError("Complete image and packet inventories required")
        for item in record["images"]:
            raw = evidence.image(pdf, edge=item["edge"], viewport=item["viewport"])
            if (
                raw != _path(pool, item["path"]).read_bytes()
                or sha(raw) != item["sha256"]
                or len(raw) != item["encoded_bytes"]
            ):
                raise ValueError("Actual source pixel replay differs")
        for item in record["packets"]:
            raw = evidence.dump(
                evidence.packet(record, mode=item["mode"], pixels_available=item["pixels_available"])
            ).encode()
            if (
                raw != _path(pool, item["path"]).read_bytes()
                or sha(raw) != item["sha256"]
                or len(raw) != item["utf8_bytes"]
            ):
                raise ValueError("Complete literal packet replay differs")
        records.append(record)
    return frozen, records


def rebuild_request(
    pool: Path, record: dict[str, Any], config: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Use frozen actual image bytes and explicit viewport notice in image treatments only."""
    url, receipt = None, None
    if config["image_edge"]:
        matches = [
            i for i in record["images"] if i["edge"] == config["image_edge"] and i["scope"] == config["viewport"]
        ]
        if len(matches) != 1:
            raise ValueError("Exact unique selected image receipt required")
        receipt = deepcopy(matches[0])
        raw = _path(pool, receipt["path"]).read_bytes()
        if sha(raw) != receipt["sha256"]:
            raise ValueError("Selected image changed")
        url = "data:image/png;base64," + base64.b64encode(raw).decode()
    body = evidence.request(record, config["model"], mode=config["mode"], image_url=url)
    if receipt is not None:
        # Declared framing is part of this treatment, never hidden crop/full-page equivalence.
        packet = json.loads(body["state"][0]["text"])
        packet["pixel_scope"] = {
            "scope": receipt["scope"],
            "viewport": receipt["viewport"],
            "dimensions": receipt["dimensions"],
            "encoding": receipt["encoding"],
            "coordinate_mapping": receipt["coordinate_mapping"],
            "peripheral_rules_may_be_clipped": receipt["scope"] == "crop",
        }
        body["state"][0]["text"] = evidence.dump(packet)
    return body, receipt


def parse_response(
    record: dict[str, Any], actual_body: dict[str, Any], result: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    """Strict single native choice with unchanged raw probabilities; no normalization or repair."""
    if (
        actual_body["model"] != config["model"]
        or actual_body["questions"]["q0"]["criteria"] != evidence.CRITERIA[record["kind"]]
    ):
        raise ValueError("Frozen question/model identity differs")
    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict) or set(result["answers"]) != {"q0"}:
        raise ValueError("Exact single-answer envelope required")
    if result.get("model", config["model"]) != config["model"]:
        raise ValueError("Returned model differs from requested model")
    answer = result["answers"]["q0"]
    if (
        not isinstance(answer, dict)
        or not {"type", "choice", "probabilities"} <= set(answer)
        or not set(answer) <= {"type", "choice", "probabilities", "confidence"}
        or answer["type"] != "choice"
    ):
        raise ValueError("Strict typed choice fields required")
    raw = answer["probabilities"]
    if (
        not isinstance(raw, dict)
        or set(raw) != set(evidence.CRITERIA[record["kind"]])
        or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in raw.values())
    ):
        raise ValueError("Exact finite bounded menu probabilities required")
    mass, choice = sum(raw.values()), answer["choice"]
    if (
        abs(mass - 1) > ROUNDING_TOLERANCE
        or not isinstance(choice, str)
        or choice not in raw
        or raw[choice] != max(raw.values())
    ):
        raise ValueError("Declared choice must be raw maximum with mass within existing tolerance")
    return {
        "source_ids": deepcopy(record["pair_source_ids"]),
        "kind": record["kind"],
        "choice": choice,
        "raw_probabilities": deepcopy(raw),
        "probabilities": deepcopy(raw),
        "raw_mass": mass,
        "normalization_delta": mass - 1,
        "raw_confidence": deepcopy(answer.get("confidence")),
        "uncalibrated": True,
        "abstained": choice == "unresolved",
        "request_sha256": sha(json.dumps(actual_body, separators=(",", ":"), allow_nan=False).encode()),
        "source_sha256": sha(evidence.dump(record["source"]).encode()),
        "assignment_applied": False,
    }


def prepare(pool: Path, trusted_code: Path, output: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Authenticate all source variants and freeze24 canonical wire requests before client construction."""
    pool, trusted_code, output = [guard_path(p) for p in (pool, trusted_code, output)]
    if output.exists():
        raise FileExistsError("New independent treatment directory required")
    trusted = json.loads(trusted_code.read_bytes())
    frozen, records = authenticate(pool, trusted)
    requests = []
    for index, record in enumerate(records):
        row = {"index": index, "id": record["id"], "kind": record["kind"], "question_status": "source_refused"}
        if record["status"] == "ready":
            body, image_receipt = rebuild_request(pool, record, config)
            encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
            if len(encoded) > 750_000:
                row.update(question_status="capacity_refused", reason="Whole request exceeds750000B; no truncation")
            else:
                row.update(
                    question_status="ready",
                    canonical=body,
                    wire=body,
                    encoded=encoded,
                    image_receipt=image_receipt,
                    wire_encoded_sha256=sha(encoded),
                    request_bytes=len(encoded),
                    source_ids=record["pair_source_ids"],
                )
        requests.append(row)
    output.mkdir(parents=True)
    (output / "code").mkdir()
    (output / "source").mkdir()
    code = {}
    for name in CODE_FILES:
        path = Path(__file__).with_name(name)
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    artifacts = {}
    # Copy only the explicit source authority and enumerated source artifact names. Never copytree pool.
    shutil.copyfile(pool / "frozen.json", output / "source/frozen.json")
    shutil.copyfile(trusted_code, output / "source/trusted-code.json")
    (output / "source/code").mkdir()
    for name in frozen["code_sha256"]:
        shutil.copyfile(pool / "code" / name, output / "source/code" / name)
    for name in frozen["artifact_sha256"]:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_path(pool, name), target)
        artifacts[str(target.relative_to(output))] = sha(target.read_bytes())
    for row in requests:
        if row["question_status"] == "ready":
            for kind in ("canonical", "wire"):
                path = output / f"question-{row['index']}-{kind}-request.json"
                write_json(path, row[kind])
                artifacts[path.name] = sha(path.read_bytes())
            path = output / f"question-{row['index']}-wire-encoded.json"
            path.write_bytes(row["encoded"])
            artifacts[path.name] = sha(row["encoded"])
    retained = {
        "config": config,
        "source_pool": {
            "directory": str(pool.resolve()),
            "frozen_sha256": sha((pool / "frozen.json").read_bytes()),
            "external_map_path": str(trusted_code.resolve()),
            "external_map_sha256": sha(trusted_code.read_bytes()),
            "trusted_code": trusted,
        },
        "records": frozen["records"],
        "selected": [{k: v for k, v in r.items() if k not in {"canonical", "wire", "encoded"}} for r in requests],
        "code_sha256": code,
        "artifact_sha256": artifacts,
        "gold_read_or_copied": False,
        "references_read": False,
        "question_count": 24,
    }
    write_json(output / "frozen.json", retained)
    return {"frozen": retained, "records": records, "requests": requests}


def client_for(config: dict[str, Any], _prepared: dict[str, Any]) -> Any:
    """Construct root shared-ledger/$50 client only after complete frozen preparation."""
    from bench.p003_client import P003ConcurrentClient, P003DecisionClient

    return P003ConcurrentClient(ROOT) if config["transport_concurrency"] == 3 else P003DecisionClient(ROOT)


def read_entries(client: Any, prefix: str) -> list[dict[str, Any]]:
    """Root runtime accounting seam; never used during source preparation."""
    from bench.p003_boundary_run import _entries

    return _entries(client, prefix)


def run(
    pool: Path,
    trusted_code: Path,
    output: Path,
    *,
    model: str,
    mode: str = "text_geometry",
    image_edge: int = 0,
    viewport: str = "page",
    transport_concurrency: int = 3,
    run_hosted: bool = False,
    client_factory: Callable[..., Any] = client_for,
    entries_reader: Callable[..., list[dict[str, Any]]] = read_entries,
) -> dict[str, Any]:
    """One fresh attempt/case; first transport failure stops, malformed answers continue distinct cases."""
    from bench.p003_boundary_run import _charges, _error, _identifier
    from bench.pipeline_run import Resources

    if not run_hosted:
        raise ValueError("Explicit root --run-hosted required; preparation never constructs a client")
    config = configuration(
        model, mode=mode, image_edge=image_edge, viewport=viewport, transport_concurrency=transport_concurrency
    )
    config["run_id"] = _identifier(output.name)
    began, cpu = time.perf_counter(), time.process_time()
    prepared = prepare(pool, trusted_code, output, config)
    preprocessing = {
        "wall_seconds": time.perf_counter() - began,
        "cpu_seconds": time.process_time() - cpu,
        "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "measurement": "Unsampled parent lifetime RSS includes imports; source validation/render replay/request freezing excluded from API rates",
    }
    initialization_error = None
    try:
        client = client_factory(config, prepared)
    except Exception as error:
        client = None
        initialization_error = _error(error, "client_initialization")
    prefix = f"P003/{config['run_id']}/synthetic-relations/"
    stopped = initialization_error is not None
    results = []
    with Resources() as resources:
        for request, record in zip(prepared["requests"], prepared["records"], strict=True):
            row = {
                "index": request["index"],
                "id": record["id"],
                "kind": record["kind"],
                "model": model,
                "provider": "openrouter",
                "status": "not_attempted",
                "wire_encoded_sha256": request.get("wire_encoded_sha256"),
                "tag": prefix + str(request["index"]),
            }
            if request["question_status"] != "ready":
                row.update(
                    status=request["question_status"], reason=request.get("reason", "Frozen source no-question refusal")
                )
            elif stopped:
                row["reason"] = "First transport/client initialization failure stopped remaining distinct cases"
            else:
                start, start_cpu = time.perf_counter(), time.process_time()
                try:
                    response = client.request(
                        request["wire"],
                        tag=row["tag"],
                        replay=False,
                        reservation_usd=RESERVATION,
                        max_body_bytes=750_000,
                    )
                except Exception as error:
                    row.update(status="transport_error", error=_error(error, "transport"))
                    stopped = True
                else:
                    write_json(output / f"question-{request['index']}-response.json", response)
                    row.update(
                        entry=response.get("entry"),
                        replayed=response.get("replayed"),
                        usage=response["result"].get("usage", {}) if isinstance(response.get("result"), dict) else {},
                    )
                    try:
                        entry = response["entry"]
                        if (
                            response.get("replayed") is not False
                            or entry["requested_model"] != model
                            or entry["request_sha256"] != request["wire_encoded_sha256"]
                            or entry["tag"] != row["tag"]
                        ):
                            raise ValueError("Fresh exact model/tag/wire receipt required")
                        receipt = parse_response(record, request["canonical"], response["result"], config)
                        row.update(
                            status="valid_abstention" if receipt["abstained"] else "valid_nonabstaining",
                            receipt=receipt,
                        )
                    except (ValueError, KeyError, TypeError) as error:
                        row.update(status="malformed_response", error=_error(error, "parse"))
                row.update(
                    client_wall_seconds=time.perf_counter() - start, client_cpu_seconds=time.process_time() - start_cpu
                )
            results.append(row)
            write_json(output / f"question-{request['index']}-result.json", row)
            write_json(output / "results.json", {"results": results})
    entries = entries_reader(client, prefix) if client is not None else []
    charges = _charges(entries)
    counts = Counter(r["status"] for r in results)
    attempted = sum(
        r["status"] in {"valid_nonabstaining", "valid_abstention", "malformed_response", "transport_error"}
        for r in results
    )
    if attempted and not entries:
        charges.update(
            effective_usd=None,
            provider_reported_usd=None,
            accounting_status="Missing attempt accounting; costs unknown",
        )
    charges["cost_scope"] = (
        "Fresh synthetic question API attempts only, including failed/unresolved reservations; local preparation separate"
    )
    metrics = resources.summary()
    wall, effective = metrics["wall_seconds"], charges["effective_usd"]
    report = {
        "config": config,
        "client_initialization_error": initialization_error,
        "results": results,
        "status_counts": dict(counts),
        "question_count": 24,
        "attempted_question_count": attempted,
        "classified_question_count": counts["valid_nonabstaining"],
        "preprocessing": preprocessing,
        "metrics": metrics,
        "charges": charges,
        "attempted_questions_per_minute": attempted / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_minute": counts["valid_nonabstaining"] / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_dollar": counts["valid_nonabstaining"] / effective
        if effective and effective > 0
        else None,
        "question_rate_scope": "One question per synthetic page, not complete extraction",
        "pages_per_minute": None,
        "pages_per_dollar": None,
        "full_pipeline_rate": None,
        "correctness_measured": False,
        "gold_read": False,
        "source_assignments_applied": 0,
        "model_fallbacks": 0,
        "retries": 0,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Prepare by default; root alone opts into hosted runs and shared ledger admission."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=DECISION_MODELS, required=True)
    parser.add_argument("--evidence", choices=evidence.MODES, default="text_geometry")
    parser.add_argument("--image-edge", choices=(0, 128, 512), type=int, default=0)
    parser.add_argument("--viewport", choices=("page", "crop"), default="page")
    parser.add_argument("--transport-concurrency", choices=(1, 3), type=int, default=3)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    config = configuration(
        args.model,
        mode=args.evidence,
        image_edge=args.image_edge,
        viewport=args.viewport,
        transport_concurrency=args.transport_concurrency,
    )
    if args.run_hosted:
        result = run(
            args.input,
            args.trusted_code,
            args.output,
            model=args.model,
            mode=args.evidence,
            image_edge=args.image_edge,
            viewport=args.viewport,
            transport_concurrency=args.transport_concurrency,
            run_hosted=True,
        )
        print(evidence.dump({k: v for k, v in result.items() if k != "results"}))
    else:
        prepared = prepare(args.input, args.trusted_code, args.output, config)
        print(
            evidence.dump({"prepared_question_count": len(prepared["requests"]), "hosted_calls": 0, "gold_read": False})
        )


if __name__ == "__main__":
    main()
