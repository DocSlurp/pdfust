"""Fresh bounded decision-route compatibility probes from a frozen source request."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bench.decision_hosted import DECISION_MODELS, ROOT, DecisionClient
from bench.decision_oplog_run import parse_choice
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json


def evidence(body: dict[str, Any], mode: str) -> dict[str, Any]:
    """Preserve all source text while explicitly omitting images in the text arm."""
    value = json.loads(json.dumps(body))
    if set(value["questions"]) != {"q0"} or value["questions"]["q0"].get("type") != "choice":
        message = "Compatibility template requires exactly one q0 choice"
        raise ValueError(message)
    if mode == "text" and isinstance(value["state"], list):
        pieces = [
            part if isinstance(part, str) else part["text"] for part in value["state"]
            if isinstance(part, str) or (isinstance(part, dict) and part.get("type") == "text")
        ]
        value["state"] = "\n".join(pieces)
    return value


def main() -> None:
    """Run each declared route once and preserve failures without retrying."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", nargs="+", choices=DECISION_MODELS, required=True)
    parser.add_argument("--evidence", choices=("text", "image"), required=True)
    args = parser.parse_args()
    template_bytes = guard_path(args.request_json).read_bytes()
    template = evidence(json.loads(template_bytes), args.evidence)
    output = guard_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "frozen.json", {
        "template_sha256": sha(template_bytes), "mode": args.evidence, "models": args.models,
        "code_sha256": {name: sha((ROOT / "bench" / name).read_bytes()) for name in (
            "p003_probe.py", "research_policy.py", "decision_hosted.py", "decision_oplog_run.py",
        )},
        "quality_scope": "Transport/parser compatibility only; no extraction-quality or page-throughput claim",
    })
    client = DecisionClient()
    rows = []
    with Resources() as resources:
        for index, model in enumerate(args.models):
            body = {**template, "model": model}
            write_json(output / f"request-{index}.json", body)
            row: dict[str, Any] = {
                "model": model, "status": "error",
                "request_sha256": sha(json.dumps(body, separators=(",", ":")).encode()),
            }
            tag = f"P003/{output.name}/{index}"
            began = time.perf_counter()
            try:
                response = client.request(body, tag=tag, replay=False, max_body_bytes=750_000)
                row.update(entry=response["entry"], usage=response["result"].get("usage", {}))
                write_json(output / f"response-{index}.json", response["result"])
                row["answer"] = parse_choice(response["result"], set(body["questions"]["q0"]["criteria"]))
                row["status"] = "ok"
            except Exception as error:
                row["error_type"] = type(error).__name__
                entries = json.loads(client.ledger.read_bytes())["requests"]
                row["attempts"] = [entry for entry in entries if entry.get("tag") == tag]
            row["wall_seconds"] = time.perf_counter() - began
            rows.append(row)
            write_json(output / "results.json", {"results": rows})
            print(json.dumps({"model": model, "status": row["status"]}), flush=True)
    write_json(output / "report.json", {"results": rows, "metrics": resources.summary()})


if __name__ == "__main__":
    main()
