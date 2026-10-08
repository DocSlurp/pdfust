"""Resolve frozen PDF candidate IDs into literal source evidence without labels."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def project_case(case: dict[str, Any]) -> dict[str, Any]:  # noqa: C901 - explicit task projections and ID checks.
    """Expose source-derived candidate text and geometry beside complete context.

    Text follows each candidate's supplied source-ID order. Joining with spaces
    is a display convenience, not a claim about original PDF whitespace or roles.
    Missing geometry remains missing; unresolved or duplicate IDs are refused.
    Only explicit evidence fields survive the projection.
    """
    state = case["state"]
    words = [
        {key: deepcopy(word[key]) for key in ("id", "text", "bbox", "line") if key in word} for word in state["words"]
    ]
    indexed = {word["id"]: word for word in words}
    if len(indexed) != len(words):
        message = "source evidence contains duplicate IDs"
        raise ValueError(message)

    def span(ids: list[int]) -> dict[str, Any]:
        if len(set(ids)) != len(ids):
            message = "candidate repeats a source ID"
            raise ValueError(message)
        try:
            selected = [indexed[source_id] for source_id in ids]
        except KeyError:
            message = "candidate references an unknown source ID"
            raise ValueError(message) from None
        output: dict[str, Any] = {
            "source_ids": list(ids),
            "text": " ".join(word["text"] for word in selected),
        }
        if selected and all("bbox" in word for word in selected):
            boxes = [word["bbox"] for word in selected]
            output["bbox"] = [
                min(box[0] for box in boxes),
                min(box[1] for box in boxes),
                max(box[2] for box in boxes),
                max(box[3] for box in boxes),
            ]
        return output

    candidate = state["candidate"]
    task = state["task"]
    projected: dict[str, Any]
    if task == "table":
        projected = {"rows": [span(ids) for ids in candidate["rows"]]}
    elif task == "wrap":
        projected = {"from": span(candidate["from"]), "to": span(candidate["to"])}
    elif task == "header":
        projected = {"header": span(candidate["header"]), "values": [span(ids) for ids in candidate["values"]]}
    elif task == "assignment":
        projected = {
            "label": span(candidate["label"]),
            "value": span(candidate["value"]),
            "alternatives": [span(ids) for ids in candidate["alternatives"]],
        }
    else:
        message = "unsupported decision evidence task"
        raise ValueError(message)
    data = {"task": task, "candidate": projected, "words": words}
    if "page" in state:
        data["page"] = deepcopy(state["page"])
    if "context_ids" in state:
        data["context"] = span(state["context_ids"])
    return {"question": case["question"], "data": data}
