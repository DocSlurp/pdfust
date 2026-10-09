"""Run explicitly authorized DEV evidence ablations through the shared ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from statistics import mean, median
from typing import Any

from bench.decision_context_cases import context_cases, evidence_modes, native_choice
from bench.decision_context_compact import make_fact_request, make_request
from bench.decision_context_prompts import LUNA, PERPLEXITY, assembly_request, parse_assembly
from bench.decision_hosted import ARTIFACTS, RESERVATION, DecisionClient, accounted_cost, checkpoint, exclusive_lock
from bench.decision_images import ImageCache, digest, image_part
from bench.decision_records import materialize, score_records

WAVE_START = 1350
WAVE_LIMIT = 1.0
WAVE_CALLS = 1000
VISIBLE_CUE_VARIANTS = 8
CASE_COUNT = 30
ARMS = (
    "current",
    "prior",
    "context",
    "native",
    "native-summary",
    "prior-summary",
    "prior-both",
    "image64",
    "image128",
    "image256",
    "image512",
    "blur128",
    "blank128",
    "native-image128",
    "native-reverse",
    "native-local",
    "fact-native",
    "compact-current",
    "compact-native",
    "derived-native",
    "compact-image128",
    "compact-image512",
)


def wave_admission() -> None:
    """Bound the complete evidence/retrieval wave, including unknown charges."""
    ledger = json.loads((ARTIFACTS / "ledger.json").read_text())
    new = ledger["requests"][WAVE_START:]
    if len(new) >= WAVE_CALLS or sum(accounted_cost(row["accounted_usd"]) for row in new) + RESERVATION > WAVE_LIMIT:
        message = "Evidence/retrieval wave admission exhausted"
        raise RuntimeError(message)


def run(models: list[str], arms: list[str], indices: list[int], *, hosted: bool, suffix: str = "") -> dict[str, Any]:
    """Persist exact source/config identities and per-region reconstructed scores."""
    code_sha256 = digest(
        {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path("bench/decision_context_cases.py"),
                Path("bench/decision_context_prompts.py"),
                Path("bench/decision_context_compact.py"),
                Path("bench/decision_records.py"),
                Path("bench/decision_images.py"),
            )
        }
    )
    cases = context_cases()
    cache = ImageCache(ARTIFACTS / "images")
    client = DecisionClient() if hosted else None
    records = []
    for model in models:
        for arm in arms:
            for index in indices:
                case = cases[index]
                mode = (
                    arm.split("-")[0] if arm.split("-")[0] in ("current", "prior", "context", "native") else "current"
                )
                representation = "summary" if arm.endswith("summary") else "both" if arm.endswith("both") else "raw"
                body = assembly_request(
                    evidence_modes(case, mode), model, representation, reverse_candidates=arm.endswith("reverse")
                )
                if arm.startswith(("compact", "derived")):
                    mode = "native" if arm.endswith("native") else "current"
                    body = make_request(evidence_modes(case, mode), model, derived=arm.startswith("derived"))
                if arm == "fact-native":
                    mode = "native"
                    body = make_fact_request(evidence_modes(case, mode), model)
                image_meta = None
                expected = case["gold"]["mode_choices"][mode]
                if "image" in arm or arm in ("blur128", "blank128"):
                    edge = int("".join(c for c in arm if c.isdigit()))
                    crop = cache.crop(
                        case["pdf_bytes"],
                        case["evidence"]["current_region"],
                        edge=edge,
                        blur=1.2 if arm == "blur128" else 0,
                        blank=arm == "blank128",
                    )
                    text = json.dumps(body["state"], separators=(",", ":"))
                    text += (
                        "\nThe attached image maps display rectangle "
                        + json.dumps(crop["bbox"])
                        + " to pixels "
                        + json.dumps(crop["pixels"])
                        + ". Use visible cell boundaries with exact source words."
                    )
                    body["state"] = [text, image_part(crop)]
                    image_meta = {k: v for k, v in crop.items() if k != "data"}
                    if arm != "blank128" and index % 10 < VISIBLE_CUE_VARIANTS:
                        expected = case["gold"]["choice"]
                if arm == "native-local":
                    body["questions"]["q0"]["instructions"] += (
                        " Compare the vertical interval between description lines with native horizontal separators "
                        "and fill extents. A separator between them supports separate rows; one enclosing band "
                        "supports one wrapped row. Literal page conventions can resolve cases without boundaries. "
                        "No previous pattern or ellipsis alone establishes a wrap."
                    )
                record = {
                    "case_id": case["id"],
                    "family": case["family"],
                    "model": model,
                    "arm": arm,
                    "pdf_sha256": hashlib.sha256(case["pdf_bytes"]).hexdigest(),
                    "request_sha256": hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest(),
                    "expected_document": case["gold"]["choice"],
                    "expected_evidence": expected,
                    "image": image_meta,
                    "native_choice": native_choice(case, mode),
                }
                if client is not None:
                    wave_admission()
                    response = client.request(body, tag=f"context{suffix}/{model}/{arm}/{case['id']}")
                    answer = parse_assembly(response["result"])
                    assembled = materialize(case, answer["choice"])
                    score = score_records(case, assembled)
                    scoped = deepcopy(case)
                    scoped["gold"]["mode_choices"]["scoped"] = expected
                    record.update(
                        {
                            "answer": answer,
                            "assembly": assembled,
                            "score": score,
                            "evidence_score": score_records(scoped, assembled, "scoped"),
                            "entry": response["entry"],
                            "replayed": response["replayed"],
                            "usage": response["result"].get("usage", {}),
                        }
                    )
                records.append(record)
                name = f"context{suffix}-{model.split('/')[-1]}-{arm}-{index:02d}.json"
                checkpoint(ARTIFACTS / name, record)
            print(model, arm, len(indices), "completed", flush=True)
    report = {
        "schema": 1,
        "evidence_status": "DEV, ten correlated templates x three vocabularies",
        "records": records,
        "code_sha256": code_sha256,
        "arms": arms,
        "models": models,
        "indices": indices,
    }
    checkpoint(ARTIFACTS / f"context-run{suffix}.json", report)
    return report


def summarize(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Aggregate successes without silently dropping failed or ambiguous regions."""
    output = []
    for model in report["models"]:
        for arm in report["arms"]:
            rows = [r for r in report["records"] if r["model"] == model and r["arm"] == arm and "score" in r]
            if rows:
                output.append(
                    {
                        "model": model,
                        "arm": arm,
                        "n": len(rows),
                        "document_exact": sum(r["score"]["region_exact"] for r in rows),
                        "evidence_exact": sum(r["evidence_score"]["region_exact"] for r in rows),
                        "record_f1": mean(r["score"]["record_f1"] for r in rows),
                        "median_http_ms": median(r["entry"]["elapsed_ms"] for r in rows),
                        "reported_usd": sum(r["entry"]["accounted_usd"] for r in rows),
                        "median_request_bytes": median(r["entry"]["request_bytes"] for r in rows),
                        "median_input_tokens": median(r["usage"].get("input_tokens", 0) for r in rows),
                    }
                )
    return output


def main() -> None:
    """Default dry run has no credential access or paid calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=[LUNA, PERPLEXITY], default=[LUNA, PERPLEXITY])
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=["current", "native", "image128"])
    parser.add_argument("--indices", nargs="+", type=int, default=list(range(30)))
    parser.add_argument("--suffix", default="")
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    if any(not 0 <= i < CASE_COUNT for i in args.indices):
        parser.error("indices must lie in [0,30)")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(ARTIFACTS / "run.lock"):
        report = run(args.models, args.arms, args.indices, hosted=args.run_hosted, suffix=args.suffix)
    print(json.dumps(summarize(report), indent=2))


if __name__ == "__main__":
    main()
