"""Synthetic image-transport controls, explicitly separate from PDF quality scores."""

from __future__ import annotations

import base64
import hashlib
import io
from typing import Any

from PIL import Image, ImageDraw

from bench.decision_gateway_vision import MODEL, translate

EDGE = 512


def controls() -> list[dict[str, Any]]:
    """Return identical-prompt circle/square/blank/no-image protocol controls.

    The control name and expected shape stay local. Each native wire request is
    derived losslessly from the same canonical body used by the old protocol.
    This tests transport consumption; these are not PDF extraction test scores.
    """
    records = []
    for control in ("circle", "square", "blank", "no-image"):
        body: dict[str, Any] = {
            "model": MODEL,
            "state": "Inspect the provided image.",
            "questions": {
                "q0": {
                    "type": "choice",
                    "instructions": "What large black shape is visible? Use unresolved when no shape can be seen.",
                    "criteria": {"circle": "A circle", "square": "A square", "unresolved": "No visible shape"},
                }
            },
        }
        raster = None
        if control != "no-image":
            bitmap = Image.new("RGB", (EDGE, EDGE), "white")
            painter = ImageDraw.Draw(bitmap)
            bounds = (EDGE // 4, EDGE // 4, EDGE * 3 // 4, EDGE * 3 // 4)
            if control == "circle":
                painter.ellipse(bounds, fill="black")
            elif control == "square":
                painter.rectangle(bounds, fill="black")
            output = io.BytesIO()
            bitmap.save(output, format="PNG", optimize=True)
            raster = output.getvalue()
            body["images"] = ["data:image/png;base64," + base64.b64encode(raster).decode()]
        records.append(
            {
                "control": control,
                "expected": control if control in {"circle", "square"} else "unresolved",
                "scope": "synthetic image transport validation; not PDF quality",
                "pixels": [EDGE, EDGE] if raster is not None else None,
                "png_bytes": len(raster) if raster is not None else None,
                "png_sha256": hashlib.sha256(raster).hexdigest() if raster is not None else None,
                "canonical_body": body,
                "native_body": translate(body),
            }
        )
    return records
