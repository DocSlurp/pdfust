"""Bounded source-selected DEV evidence screen; labels are read only for reporting."""

# Research artifact records have heterogeneous fields; this module never applies decisions.
# ruff: noqa: ANN401, EM101, TRY003, E501
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bench.decision_context_prompts import parse_assembly_response
from bench.decision_hosted import ARTIFACTS, RESERVATION, DecisionClient, checkpoint, exclusive_lock
from bench.reprice_model_rates import request_cost
from bench.silver import guard_path

MODEL = "perplexity/pplx-decider-v1.1-27b"
ARMS = ("geometry", "neighbors", "blob")
LIMIT = 0.50
TAG = "evidence-screen-v1/"


def encode(value: Any) -> bytes:
    """Match shared client serialization."""
    return json.dumps(value, separators=(",", ":")).encode()


def prepare(source: Path, output: Path) -> dict[str, Any]:
    """Choose six grid and six dense non-grid observations from source evidence only."""
    source, output = guard_path(source), guard_path(output)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "manifest.json").exists():
        return json.loads((output / "manifest.json").read_text())
    manifest = json.loads((source / "manifest.json").read_text())
    ranked: dict[bool, list[tuple[int, str]]] = {True: [], False: []}
    records = {(r["id"], r["arm"]): r for r in manifest["records"]}
    for record in manifest["records"]:
        if record["arm"] != "hybrid" or record["source_admission_refusal"]:
            continue
        data = (source / record["request"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError("Input changed after freeze")
        state = json.loads(data)["state"]
        ranked[bool(state["vector_grid_prior"])].append((-len(state["words"]), record["id"]))
    selected = [page for group in (True, False) for _, page in sorted(ranked[group])[:6]]
    frozen = []
    for page in selected:
        for arm in ARMS:
            record = records[page, arm]
            data = (source / record["request"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError("Input changed after freeze")
            body = json.loads(data)
            body["model"] = MODEL
            data = encode(body)
            name = f"{page}-{arm}.json"
            (output / name).write_bytes(data)
            frozen.append({"id": page, "arm": arm, "request": name, "sha256": hashlib.sha256(data).hexdigest()})
    result = {
        "schema": 1,
        "model": MODEL,
        "selection": "six most words with source grid + six most words without; ID tie-break",
        "selected": selected,
        "records": frozen,
        "source": str(source),
        "limit_usd": LIMIT,
    }
    checkpoint(output / "manifest.json", result)
    return result


def run(output: Path) -> None:
    """Execute already-frozen requests under shared and incremental reservation gates."""
    output = guard_path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    result_path = output / "results.json"
    results = json.loads(result_path.read_text()) if result_path.exists() else {"records": []}
    done = {(r["id"], r["arm"]) for r in results["records"]}
    client = DecisionClient()
    with exclusive_lock(ARTIFACTS / "run.lock"):
        for record in manifest["records"]:
            if (record["id"], record["arm"]) in done:
                continue
            data = (output / record["request"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError("Frozen request changed")
            ledger = json.loads(client.ledger.read_text())["requests"]
            charged = sum(r["accounted_usd"] for r in ledger if r["tag"].startswith(TAG))
            if charged + RESERVATION > manifest["limit_usd"]:
                results["stop"] = "incremental reservation limit"
                break
            response = None
            try:
                response = client.request(json.loads(data), tag=TAG + record["request"], max_body_bytes=750_000)
                answer = parse_assembly_response(response["result"], 1)[0]
                row = {**record, "status": "ok", "answer": answer, "response": response}
            except (RuntimeError, ValueError, OSError, KeyError) as error:
                failure = {**record, "status": "failed", "error": str(error)}
                if response is not None:
                    failure["response"] = response
                else:
                    charged_entries = json.loads(client.ledger.read_text())["requests"]
                    charged = next(
                        (entry for entry in charged_entries if entry["request_sha256"] == record["sha256"]), None
                    )
                    if charged is not None:
                        failure["entry"] = charged
                results["records"].append(failure)
                results["stop"] = "first request failure; investigation required"
                checkpoint(result_path, results)
                break
            results["records"].append(row)
            checkpoint(result_path, results)
        checkpoint(result_path, results)


def report(output: Path, destination: Path) -> None:
    """Score the frozen screen, keeping unknowns in class denominators."""
    manifest = json.loads((output / "manifest.json").read_text())
    results = json.loads((output / "results.json").read_text())
    gold = json.loads((Path(manifest["source"]) / "scorer-only.json").read_text())
    catalog = json.loads((ARTIFACTS / "langfuse/catalog-prices.json").read_text())
    rows = {(r["id"], r["arm"]): r for r in results["records"]}
    lines = [
        "# D001 source-selected evidence screen",
        "",
        f"Model: `{MODEL}`. Twelve DEV pages chosen only by source-grid presence and descending word count (six per stratum). Three arms, frozen before calls; no independent validation claim.",
        "",
        "| Arm | Correct / total | TP | FP | FN | TN | Unresolved | Effective USD | API ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    summaries = []
    for arm in ARMS:
        tp = fp = fn = tn = unresolved = 0
        cost, elapsed = 0.0, 0.0
        unknown_cost = False
        for page in manifest["selected"]:
            row = rows.get((page, arm), {})
            choice = row.get("answer", {}).get("choice", "unresolved")
            expected = gold[page]
            tp += expected == "A" and choice == "A"
            fp += expected == "B" and choice == "A"
            fn += expected == "A" and choice != "A"
            tn += expected == "B" and choice == "B"
            unresolved += choice == "unresolved"
            if "response" in row or "entry" in row:
                response = row.get("response", {})
                entry = response.get("entry", row.get("entry"))
                quote = request_cost(
                    entry, response.get("result", {}).get("usage", {}), catalog["prices"].get(MODEL, {})
                )
                value = quote["effective_usd"]
                unknown_cost |= value is None
                cost += value or 0
                elapsed += entry.get("elapsed_ms", 0)
        summaries.append(
            {
                "arm": arm,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "unresolved": unresolved,
                "effective_usd": None if unknown_cost else cost,
                "api_ms": elapsed,
            }
        )
        lines.append(
            f"| {arm} | {tp + tn} / {len(manifest['selected'])} | {tp} | {fp} | {fn} | {tn} | {unresolved} | {'unknown' if unknown_cost else f'{cost:.6f}'} | {elapsed:.0f} |"
        )
    agreement = sum(
        all(rows.get((page, arm), {}).get("status") == "ok" for arm in ARMS)
        and len({rows[(page, arm)]["answer"]["choice"] for arm in ARMS}) == 1
        for page in manifest["selected"]
    )
    lines.extend(
        [
            "",
            f"All-three answer agreement: **{agreement}/{len(manifest['selected'])}**. This screen measures ruled-table presence, not cell recovery. Missing/failed inputs remain unresolved; unresolved negatives do not count as true negatives. Provider probabilities are not calibrated correctness.",
            "",
            "No automatic all-corpus expansion. Stop at this screen and prioritize candidate assembly unless a concrete evidence-dependent error warrants a separately frozen follow-up.",
            "",
        ]
    )
    destination.write_text("\n".join(lines))
    checkpoint(output / "summary.json", {"rows": summaries, "agreement": agreement})


def main() -> None:
    """Prepare locally, opt in to inference, or report retained responses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ARTIFACTS.parent / "evidence-designs/root-gate-v1")
    parser.add_argument("--output", type=Path, default=ARTIFACTS / "evidence-screen-v1")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare(args.source, args.output)
    if args.run_hosted:
        run(args.output)
    if args.run_hosted or args.report_only:
        report(args.output, Path("bench/results/evidence-screen.md"))


if __name__ == "__main__":
    main()
