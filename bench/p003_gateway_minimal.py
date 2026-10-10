"""Root-only minimal Gateway protocol controls, separate from PDF quality."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bench.decision_gateway import GatewayDecisionClient
from bench.decision_gateway_vision import GatewayVisionDecisionClient, translate
from bench.decision_hosted import ROOT
from bench.decision_oplog_run import parse_choice
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json


def bodies(image_request: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Freeze short synthetic text and one unchanged image from a failed request."""
    image = image_request["input"][0]["content"][1]
    if image.get("type") != "input_image" or not image.get("image_url", "").startswith("data:image/"):
        message = "Expected one retained native image part"
        raise ValueError(message)
    question = {"q0": {"type": "choice", "instructions": "Choose the spatial relationship.",
                       "criteria": {"left": "A is left of B.", "right": "A is right of B."}}}
    canonical = {"model": "liquid/d1", "state": "A has box [10,10,20,20]. B has box [30,10,40,20].",
                 "questions": question}
    laya = {**canonical, "model": "convaiinnovations/laya",
            "providerOptions": {"gateway": {"only": ["boundless"]}}}
    return [("laya-text", laya), ("d1-text", translate(canonical)),
            ("d1-image", translate({**canonical, "images": [image["image_url"]]}))]


def main() -> None:
    """Attempt each route once; image control requires a successful text control."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exclusive-paid-work", action="store_true")
    args = parser.parse_args()
    if not args.exclusive_paid_work:
        parser.error("Root must finish all other paid work before these serial probes")
    raw = guard_path(args.image_request).read_bytes()
    cases = bodies(json.loads(raw))
    output = guard_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    for name, body in cases:
        write_json(output / (name + "-request.json"), body)
    files = ("p003_gateway_minimal.py", "decision_gateway.py", "decision_gateway_vision.py",
             "decision_hosted.py", "research_policy.py", "decision_oplog_run.py")
    write_json(output / "frozen.json", {
        "source_request_sha256": sha(raw), "scope": "Protocol only; no PDF quality or page rates",
        "cases": [{"name": name, "request_sha256": sha(json.dumps(body, separators=(",", ":")).encode())}
                  for name, body in cases],
        "code_sha256": {name: sha((ROOT / "bench" / name).read_bytes()) for name in files},
        "image_admission": "d1 text must return a valid typed answer before image transmission",
        "retries": False,
    })
    rows: list[dict[str, Any]] = []
    text_ok = False
    with Resources() as resources:
        for name, body in cases:
            row: dict[str, Any] = {"name": name, "model": body["model"], "status": "skipped"}
            if name == "d1-image" and not text_ok:
                row["reason"] = "d1 text control failed; image arm not transmitted"
                rows.append(row)
                continue
            client = GatewayDecisionClient() if name == "laya-text" else GatewayVisionDecisionClient()
            tag = f"P003/{output.name}/{name}"
            started = time.perf_counter()
            try:
                response = client.request(body, tag=tag, replay=False, max_body_bytes=750_000)
                write_json(output / (name + "-response.json"), response)
                row.update(status="ok", entry=response["entry"],
                           answer=parse_choice(response["result"], {"left", "right"}))
                if name == "d1-text":
                    text_ok = True
            except Exception as error:
                row.update(status="error", error_type=type(error).__name__)
                row["attempts"] = [entry for entry in json.loads(client.ledger.read_bytes())["requests"]
                                   if entry.get("tag") == tag]
            row["wall_seconds"] = time.perf_counter() - started
            rows.append(row)
            write_json(output / "results.json", {"results": rows})
            print(json.dumps({"name": name, "status": row["status"]}), flush=True)
    write_json(output / "report.json", {"results": rows, "resources": resources.summary(),
                                        "scope": "Protocol controls only; no extraction-quality claim"})


if __name__ == "__main__":
    main()
