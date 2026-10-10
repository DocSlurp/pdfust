"""Explicit Gateway decision wire translation for P003 source-matched gates."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from bench.decision_gateway import GatewayDecisionClient
from bench.decision_gateway_vision import GatewayVisionDecisionClient, translate
from bench.decision_oplog_run import parse_choice
from bench.silver import write_json


def gateway_wire(request: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Project unchanged literal evidence into the previously verified wire shape."""
    state = request["state"]
    parts = state if isinstance(state, list) else [state]
    text, images = [], []
    for part in parts:
        if isinstance(part, str):
            text.append(part)
        elif isinstance(part, dict) and part.get("type") == "image_url":
            images.append(part["image_url"]["url"])
        else:
            message = "Gateway gate requires literal text and inline image parts"
            raise ValueError(message)
    body: dict[str, Any] = {
        "model": request["model"], "state": "\n".join(text), "questions": request["questions"],
    }
    if images:
        body["images"] = images
    if request["model"] == "liquid/d1":
        return translate(body), True
    if request["model"] in {"convaiinnovations/laya", "convaiinnovations/laya-free"} and not images:
        body["providerOptions"] = {"gateway": {"only": ["boundless"]}}
        return body, False
    message = "P003 Gateway route requires d1 or text-only Laya"
    raise ValueError(message)


def request_gate(request: dict[str, Any], tag: str, path: Path) -> dict[str, Any]:
    """Root-only fresh call; retain actual wire bytes and normalized typed answer."""
    wire, native = gateway_wire(request)
    write_json(path, wire)
    client = GatewayVisionDecisionClient() if native else GatewayDecisionClient()
    started, cpu = time.perf_counter(), time.process_time()
    response = client.request(wire, tag=tag, replay=False, max_body_bytes=750_000)
    answer = parse_choice(response["result"], set(request["questions"]["q0"]["criteria"]))
    return {
        "answer": answer, "entry": response["entry"], "usage": response["result"].get("usage", {}),
        "replayed": response["replayed"], "client_wall_seconds": time.perf_counter() - started,
        "client_cpu_seconds": time.process_time() - cpu,
    }
