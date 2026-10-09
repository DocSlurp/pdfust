"""L005 matched singleton raw/compact canonical source representation control."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from bench.lowlevel_control_freeze import begin, finish, sources, verify_control
from bench.lowlevel_evidence import MODELS
from bench.lowlevel_evidence import request as original_request
from bench.lowlevel_packets import _digest, _file, _write
from bench.lowlevel_packets import request as packet_request
from bench.lowlevel_prompts import transform

EXPERIMENT = "L005"
ARMS = ("rawbothcanonical", "compactbothcanonical")
MAX_BODY_BYTES = 32000


def request(observations: list[dict[str, Any]], model: str, arm: str) -> dict[str, Any]:
    """Hold source, resolved criteria, native state and batch size fixed."""
    if len(observations) != 1 or model not in MODELS or arm not in ARMS:
        message = "L005 requires an admitted singleton model/arm"
        raise ValueError(message)
    body = (
        transform(original_request(observations, model, "canonical"), observations, "both")
        if arm == "rawbothcanonical"
        else packet_request(observations, model, "canonicalcompact")
    )
    if len(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()) > MAX_BODY_BYTES:
        message = "L005 singleton exceeds byte cap; complete freeze refuses without truncation"
        raise ValueError(message)
    return body


def prepare(parent: Path, directory: Path) -> dict[str, Any]:
    """Admit every source under both representations before publishing a freeze."""
    parent, original, observations = sources(parent)
    parent_hash = _digest(_file(parent, "manifest.json").read_bytes())
    # Preflight every singleton before creating any output. Oversized raw evidence
    # refuses the entire control, never a selectively scored subset.
    bodies = [
        (page["id"], model, arm, request([observations[page["id"]]], model, arm))
        for page in original["pages"]
        for model in MODELS
        for arm in ARMS
    ]
    directory = begin(parent, directory, original["pages"])
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
                "body_bytes": len(json.dumps(body, separators=(",", ":")).encode()),
            }
        )
    random.Random(17445).shuffle(records)  # noqa: S311 - reproducible source-control order.
    manifest = {
        "schema": 1,
        "experiment": EXPERIMENT,
        "parent_directory": str(parent),
        "parent_manifest_sha256": parent_hash,
        "models": list(MODELS),
        "arms": list(ARMS),
        "pages": original["pages"],
        "records": records,
        "catalog_sha256": original["catalog_sha256"],
        "request_settings": {"max_body_bytes": MAX_BODY_BYTES, "batch_size": 1, "schedule_seed": 17445},
        "prompt_factor": "both",
        "comparison": (
            "Matched source, criteria, native state and singleton scope; "
            "only reversible source row representation changes"
        ),
        "code_sha256": {
            f"bench/{name}": _digest(Path(__file__).with_name(name).read_bytes())
            for name in (
                "lowlevel_matched.py",
                "lowlevel_control_freeze.py",
                "lowlevel_packets.py",
                "lowlevel_compact.py",
                "lowlevel_prompts.py",
            )
        },
    }
    return finish(parent, directory, manifest)


def verify(directory: Path) -> dict[str, Any]:
    """Validate matched singleton source lineage and complete request inventory."""
    return verify_control(
        directory, experiment=EXPERIMENT, models=MODELS, arms=ARMS, builder=request, max_bytes=MAX_BODY_BYTES
    )


def main() -> None:
    """Prepare a CPU-only matched source control or verify retained bodies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        manifest = verify(args.directory)
    else:
        if args.parent is None:
            parser.error("--parent is required")
        manifest = prepare(args.parent, args.directory)
    print(json.dumps({"experiment": EXPERIMENT, "pages": len(manifest["pages"]), "requests": len(manifest["records"])}))


if __name__ == "__main__":
    main()
