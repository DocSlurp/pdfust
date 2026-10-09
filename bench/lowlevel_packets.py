"""Freeze and verify L004 lossless packets from an existing DEV source freeze.

L004 is a distinct experiment, never a retry of an earlier failed body. Existing
raw baselines are contextual comparisons, not matched compression controls.
"""

# ruff: noqa: ANN401
from __future__ import annotations

import argparse
import hashlib
import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.lowlevel_compact import adaptive_requests, compact, encoded, expand, relation_hint
from bench.lowlevel_evidence import MODELS
from bench.lowlevel_evidence import request as original_request
from bench.lowlevel_evidence import verify as verify_parent
from bench.lowlevel_prompts import transform
from bench.silver import guard_path

EXPERIMENT = "L004"
ARMS = ("canonicalcompact", "vectorscompact", "vectorshintcompact", "operatorscompact")
MAX_BODY_BYTES = 32000
MAX_BATCH = 3
MAX_PAGES = 4096
SOURCE_ARMS = {
    "canonicalcompact": "canonical",
    "vectorscompact": "vectors",
    "vectorshintcompact": "vectors",
    "operatorscompact": "operators",
}


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file(directory: Path, name: str) -> Path:
    if not isinstance(name, str) or Path(name).name != name:
        message = "L004 artifact name must be a basename"
        raise ValueError(message)
    candidate = (directory / name).resolve()
    if not candidate.is_relative_to(directory.resolve()):
        message = "L004 artifact escapes admitted directory"
        raise ValueError(message)
    return guard_path(candidate)


def _write(path: Path, value: Any) -> str:
    raw = encoded(value)
    path.write_bytes(raw)
    return _digest(raw)


def _body(observations: list[dict[str, Any]], model: str, arm: str) -> dict[str, Any]:
    if model not in MODELS or arm not in ARMS or not 1 <= len(observations) <= MAX_BATCH:
        message = "L004 model, arm or batch is unadmitted"
        raise ValueError(message)
    result: dict[str, Any] = {}
    for index, observation in enumerate(observations):
        single = transform(original_request([observation], model, SOURCE_ARMS[arm]), [observation], "both")
        if index == 0:
            result = deepcopy(single)
            result["state"] = {"observations": {}}
            result["questions"] = {}
        source = single["state"]["observations"]["q0"]
        packet = compact(source)
        if encoded(expand(packet)) != encoded(source):
            message = "L004 source packet failed exact JSON round trip"
            raise ValueError(message)
        if arm == "vectorshintcompact":
            packet = compact(relation_hint(source))
        key = f"q{index}"
        result["state"]["observations"][key] = packet
        question = deepcopy(single["questions"]["q0"])
        prefix = "Consider ONLY observations.q0."
        if not question["instructions"].startswith(prefix):
            message = "L004 source question has an unrecognized scope"
            raise ValueError(message)
        question["instructions"] = f"Consider ONLY observations.{key}." + question["instructions"][len(prefix) :]
        result["questions"][key] = question
    return result


def request(observations: list[dict[str, Any]], model: str, arm: str) -> dict[str, Any]:
    """Build a complete source-preserving native body below the L004 byte cap."""
    body = _body(observations, model, arm)
    if len(encoded(body)) > MAX_BODY_BYTES:
        message = "L004 body exceeds 32000 bytes; prepare smaller complete batches"
        raise ValueError(message)
    return body


def prepare(parent: Path, directory: Path) -> dict[str, Any]:  # noqa: C901 - freeze all source requests before scorer copy.
    """Copy every frozen source; write requests before copying scorer targets."""
    parent, directory = guard_path(parent).resolve(), guard_path(directory).resolve()
    parent_manifest = verify_parent(parent)
    parent_raw = _file(parent, "manifest.json").read_bytes()
    pages = parent_manifest["pages"]
    if not 1 <= len(pages) <= MAX_PAGES or len({page["id"] for page in pages}) != len(pages):
        message = "L004 parent source inventory is invalid"
        raise ValueError(message)
    if directory.exists():
        message = "Preserve existing L004 freeze; choose a new destination"
        raise ValueError(message)
    directory.mkdir(parents=True)
    observations = {}
    copied_pages = []
    for page in pages:
        copied = deepcopy(page)
        for file_key, hash_key in (("source_file", "source_sha256"), ("observation_file", "observation_sha256")):
            raw = _file(parent, page[file_key]).read_bytes()
            if _digest(raw) != page[hash_key]:
                message = "L004 parent source changed during copy"
                raise ValueError(message)
            _file(directory, page[file_key]).write_bytes(raw)
        observations[page["id"]] = json.loads(_file(directory, page["observation_file"]).read_bytes())
        copied_pages.append(copied)
    catalog = _file(parent, "catalog-prices.json").read_bytes()
    if _digest(catalog) != parent_manifest["catalog_sha256"]:
        message = "L004 parent catalog changed during copy"
        raise ValueError(message)
    _file(directory, "catalog-prices.json").write_bytes(catalog)
    records: list[dict[str, Any]] = []
    inventory = [observations[page["id"]] for page in copied_pages]
    for arm in ARMS:
        for model in MODELS:

            def builder(
                batch: list[dict[str, Any]], selected_model: str = model, selected_arm: str = arm
            ) -> dict[str, Any]:
                return _body(batch, selected_model, selected_arm)

            batches = adaptive_requests(
                inventory,
                builder,
                max_bytes=MAX_BODY_BYTES,
                max_batch=MAX_BATCH,
            )
            for batch in batches:
                ids = [page["id"] for page in copied_pages[batch["start"] : batch["stop"]]]
                name = f"request-{len(records):04d}.json"
                records.append(
                    {
                        "request": name,
                        "sha256": _write(_file(directory, name), batch["body"]),
                        "model": model,
                        "arm": arm,
                        "page_ids": ids,
                        "body_bytes": batch["utf8_bytes"],
                    }
                )
    random.Random(17444).shuffle(records)  # noqa: S311 - fixed DEV experiment schedule.
    manifest = {
        "schema": 1,
        "experiment": EXPERIMENT,
        "parent_directory": str(parent),
        "parent_manifest_sha256": _digest(parent_raw),
        "records": records,
        "pages": copied_pages,
        "models": list(MODELS),
        "arms": list(ARMS),
        "catalog_sha256": _digest(catalog),
        "request_settings": {
            "max_body_bytes": MAX_BODY_BYTES,
            "batch_size": MAX_BATCH,
            "schedule_seed": 17444,
            "adaptive": True,
        },
        "prompt_factor": "both",
        "raw_baseline": "Predeclared omitted; earlier L001 baseline is contextual, not a matched compression control",
        "code_sha256": {
            f"bench/{name}": _digest(Path(__file__).with_name(name).read_bytes())
            for name in (
                "lowlevel_packets.py",
                "lowlevel_compact.py",
                "lowlevel_prompts.py",
                "lowlevel_geometry.py",
                "lowlevel_evidence.py",
            )
        },
    }
    # No labels have been parsed or projected. Targets become available only
    # after every source-derived request body and hash is frozen above.
    targets = _file(parent, "private-targets.json").read_bytes()
    if _digest(targets) != parent_manifest["targets_sha256"]:
        message = "L004 parent scorer targets changed"
        raise ValueError(message)
    _file(directory, "private-targets.json").write_bytes(targets)
    manifest["targets_sha256"] = _digest(targets)
    _write(_file(directory, "manifest.json"), manifest)
    return manifest


def verify(directory: Path) -> dict[str, Any]:  # noqa: C901, PLR0912 - complete frozen inventories must agree.
    """Validate lineage, copies and every reconstructed body without interpreting gold."""
    directory = guard_path(directory).resolve()
    manifest = json.loads(_file(directory, "manifest.json").read_bytes())
    if (
        manifest.get("experiment") != EXPERIMENT
        or manifest.get("models") != list(MODELS)
        or manifest.get("arms") != list(ARMS)
    ):
        message = "L004 manifest experiment inventory differs"
        raise ValueError(message)
    parent = guard_path(Path(manifest["parent_directory"])).resolve()
    if _digest(_file(parent, "manifest.json").read_bytes()) != manifest["parent_manifest_sha256"]:
        message = "L004 parent manifest changed"
        raise ValueError(message)
    parent_manifest = verify_parent(parent)
    if manifest["pages"] != parent_manifest["pages"]:
        message = "L004 copied source inventory differs from complete parent"
        raise ValueError(message)
    for base in (directory, parent):
        if _digest(_file(base, "catalog-prices.json").read_bytes()) != manifest["catalog_sha256"]:
            message = "L004 catalog changed"
            raise ValueError(message)
    observations = {}
    for page in manifest["pages"]:
        for key, hash_key in (("source_file", "source_sha256"), ("observation_file", "observation_sha256")):
            if _digest(_file(directory, page[key]).read_bytes()) != page[hash_key]:
                message = "L004 copied source changed"
                raise ValueError(message)
        observations[page["id"]] = json.loads(_file(directory, page["observation_file"]).read_bytes())
    seen = set()
    filenames = set()
    for record in manifest["records"]:
        ids = record["page_ids"]
        if (
            not 1 <= len(ids) <= MAX_BATCH
            or any(ident not in observations for ident in ids)
            or record["request"] in filenames
        ):
            message = "L004 request source inventory is invalid"
            raise ValueError(message)
        filenames.add(record["request"])
        raw = _file(directory, record["request"]).read_bytes()
        rebuilt = encoded(request([observations[ident] for ident in ids], record["model"], record["arm"]))
        if raw != rebuilt or _digest(raw) != record["sha256"] or len(raw) != record["body_bytes"]:
            message = "L004 body differs from frozen source reconstruction"
            raise ValueError(message)
        for ident in ids:
            identity = (record["model"], record["arm"], ident)
            if identity in seen:
                message = "L004 repeats a model/arm/source observation"
                raise ValueError(message)
            seen.add(identity)
    if seen != {(model, arm, ident) for model in MODELS for arm in ARMS for ident in observations}:
        message = "L004 request inventory omits an observation"
        raise ValueError(message)
    return manifest


def main() -> None:
    """Prepare or verify source packets; no credentials or network requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        manifest = verify(args.directory)
    else:
        if args.parent is None:
            parser.error("--parent is required for preparation")
        manifest = prepare(args.parent, args.directory)
    print(json.dumps({"experiment": EXPERIMENT, "pages": len(manifest["pages"]), "requests": len(manifest["records"])}))


if __name__ == "__main__":
    main()
