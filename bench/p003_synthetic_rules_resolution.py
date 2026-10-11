# ruff: noqa: EM101, TRY003
"""Source rows and vector rules plus authenticated matched resolution pixels."""

from __future__ import annotations

import json
from typing import Any

from bench import p003_synthetic_resolution as pixels

VERSION = "p003-synthetic-rules-resolution-v1"
EDGES = (400, 768)
MODELS = pixels.MODELS


def request(record: dict[str, Any], model: str, item: dict[str, Any], raw: bytes) -> dict[str, Any]:
    """Preserve exact criteria/pixels; replace only the complete source packet evidence mode."""
    if model not in MODELS or item["edge"] not in EDGES:
        raise ValueError("Five explicit image models and fixed 400/768 edges required")
    plain = pixels.request(record, model, item, raw)
    body = pixels.evidence.request(record, model, mode="rows_rules", image_url=plain["state"][1]["image_url"]["url"])
    packet = json.loads(body["state"][0])
    packet["pixel_scope"] = json.loads(plain["state"][0])["pixel_scope"]
    body["state"][0] = pixels.evidence.dump(packet)
    return body
