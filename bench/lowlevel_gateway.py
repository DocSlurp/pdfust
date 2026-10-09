"""L009 Gateway-only model and vision-route controls over frozen DEV evidence."""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import Any

from bench.decision_gateway_catalog import MODELS
from bench.lowlevel_control_freeze import begin, encoded_body, finish, sources, verify_control
from bench.lowlevel_evidence import request as original_request
from bench.lowlevel_packets import _digest, _file, _write
from bench.lowlevel_packets import request as compact_request
from bench.lowlevel_prompts import transform
from bench.silver import guard_path, rss_bytes

TEXT_ARMS = ("minimal-resolved", "words-resolved", "canonical-compact")
D1 = "liquid/d1"
TEXT_CAP = 7500
BODY_CAP = 200000
SUPPORTED_ARMS = ("minimal-resolved", "words-resolved")


def inventory(kind: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Keep each predeclared compatibility cohort distinct from the failed matrices."""
    if kind == "text-supported":
        return MODELS[:2], SUPPORTED_ARMS, "L012"
    if kind == "text-serialized":
        return MODELS, tuple(arm + "-serialized" for arm in TEXT_ARMS), "L010"
    if kind == "text":
        return MODELS, TEXT_ARMS, "L009"
    if kind == "vision":
        return (D1,), image_arms(), "L009"
    message = "Unknown Gateway control kind"
    raise ValueError(message)


def image_arms() -> tuple[str, ...]:
    """Match every focus image treatment without claiming a new checkpoint."""
    return tuple(f"focus-{mode}-{edge}" for mode in ("rgb", "gray", "lowbit") for edge in (64, 128, 256, 400, 500, 512))


def request(observations: list[dict[str, Any]], model: str, arm: str) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Translate transport only; never project target labels or local source identities."""
    if len(observations) != 1 or model not in MODELS:
        message = "L009 requires an admitted singleton Gateway model"
        raise ValueError(message)
    serialized = arm.endswith("-serialized")
    base_arm = arm.removesuffix("-serialized")
    if base_arm in TEXT_ARMS:
        body = (
            compact_request(observations, D1, "canonicalcompact")
            if base_arm == "canonical-compact"
            else transform(original_request(observations, D1, base_arm.split("-", 1)[0]), observations, "both")
        )
        body["model"] = model
        if serialized:
            body["state"] = json.dumps(body["state"], separators=(",", ":"), allow_nan=False)
        if model.startswith("convaiinnovations/"):
            body["providerOptions"] = {"gateway": {"only": ["boundless"]}}
        if len(encoded_body(body)) > TEXT_CAP:
            message = "L009 text evidence exceeds conservative context admission; refuse without truncation"
            raise ValueError(message)
    elif arm in image_arms() and model == D1:
        from bench.lowlevel_images import request as image_request  # noqa: PLC0415 - optional image controls.

        body = image_request(observations, "perplexity/pplx-decider-v1.1-27b", arm)
        text_parts, image_parts = [], []
        for part in body["state"]:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "image_url":
                image_parts.append(part["image_url"]["url"])
            else:
                message = "Unsupported image-state part; preserve source rather than silently drop it"
                raise ValueError(message)
        if len(image_parts) != 1 or not text_parts:
            message = "L009 vision requires one retained image and literal text state"
            raise ValueError(message)
        body.update(model=model, state="\n".join(text_parts), images=image_parts)
    else:
        message = "Unsupported Gateway model/arm combination"
        raise ValueError(message)
    if len(encoded_body(body)) > BODY_CAP:
        message = "Gateway body exceeds admission"
        raise ValueError(message)
    return body


def prepare(parent: Path, directory: Path, catalog: Path, *, kind: str = "text") -> dict[str, Any]:
    """Freeze complete source-based requests before copying scorer-only references."""
    started, cpu = time.perf_counter(), time.process_time()
    parent, original, observations = sources(parent)
    models, arms, experiment = inventory(kind)
    bodies = [
        (page["id"], model, arm, request([observations[page["id"]]], model, arm))
        for page in original["pages"]
        for model in models
        for arm in arms
    ]
    raw_catalog = guard_path(catalog).read_bytes()
    rates = json.loads(raw_catalog)["prices"]
    if not all(model in rates for model in models):
        message = "Gateway rates missing from frozen catalog"
        raise ValueError(message)
    directory = begin(parent, directory, original["pages"])
    _file(directory, "catalog-prices.json").write_bytes(raw_catalog)
    records: list[dict[str, Any]] = []
    for ident, model, arm, body in bodies:
        name = f"request-{len(records):04d}.json"
        records.append(
            {
                "request": name,
                "sha256": _write(_file(directory, name), body),
                "model": model,
                "arm": arm,
                "page_ids": [ident],
                "body_bytes": len(encoded_body(body)),
            }
        )
    random.Random(17449).shuffle(records)  # noqa: S311 - reproducible experimental schedule.
    manifest = {
        "schema": 1,
        "experiment": experiment,
        "gateway": "vercel",
        "kind": kind,
        "models": list(models),
        "arms": list(arms),
        "pages": original["pages"],
        "records": records,
        "parent_directory": str(parent),
        "parent_manifest_sha256": _digest(_file(parent, "manifest.json").read_bytes()),
        "catalog_sha256": _digest(raw_catalog),
        "encoding_comparison": original.get("encoding_comparison", True),
        "request_settings": {"max_body_bytes": BODY_CAP, "max_text_body_bytes": TEXT_CAP, "batch_size": 1},
        "code_sha256": {"bench/lowlevel_gateway.py": _digest(Path(__file__).read_bytes())},
        "preparation": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "serial current process counters and VmHWM; no sampling; no provider call",
        },
        "limitations": (
            "Gateway routes and promotional aliases are not independent model architectures; no fallback models"
        ),
    }
    return finish(parent, directory, manifest)


def verify(directory: Path) -> dict[str, Any]:
    """Verify exact Gateway translation, complete inventory, lineage and catalog."""
    manifest = json.loads(_file(guard_path(directory), "manifest.json").read_bytes())
    kind = manifest.get("kind")
    if not isinstance(kind, str) or manifest.get("gateway") != "vercel":
        message = "Invalid Gateway freeze policy"
        raise ValueError(message)
    models, arms, experiment = inventory(kind)
    return verify_control(
        directory,
        experiment=experiment,
        models=models,
        arms=arms,
        builder=request,
        max_bytes=BODY_CAP,
    )


def main() -> None:
    """Prepare locally; inference remains in the explicitly metered runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--kind", choices=("text", "text-serialized", "text-supported", "vision"), default="text")
    args = parser.parse_args()
    manifest = prepare(args.parent, args.directory, args.catalog, kind=args.kind)
    verify(args.directory)
    print(
        json.dumps(
            {"pages": len(manifest["pages"]), "requests": len(manifest["records"]), "models": manifest["models"]}
        )
    )


if __name__ == "__main__":
    main()
