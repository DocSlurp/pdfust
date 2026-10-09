"""Transport-only one-text-segment derivative of verified ambiguity evidence.

Preserve the original literal text as an exact prefix; append the exact frozen
supplemental JSON with one newline, then retain the original image. No source
feature, question, model, image or threshold changes. Version1 artifacts remain
intact because presentation and native adapter admission differ.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import remote_ambiguity_evidence as parent
from bench.remote_prompt_packets import _digest, _encode, _fail, _inside, _safe
from bench.remote_report import _read

STATE_PARTS = 3


def project(body: dict[str, Any]) -> dict[str, Any]:
    """Collapse exact admitted text segments before the unchanged image."""
    state = body.get("state")
    if (
        not isinstance(state, list)
        or len(state) != STATE_PARTS
        or not isinstance(state[0], str)
        or not isinstance(state[2], str)
    ):
        _fail("Expected verified source/evidence/image presentation")
    if not isinstance(state[1], dict) or state[1].get("type") != "image_url":
        _fail("Expected unchanged canonical image part")
    supplemental = json.loads(state[2])
    if set(supplemental) != {"supplemental_evidence"}:
        _fail("Unexpected supplemental evidence object")
    result = deepcopy(body)
    result["state"] = [state[0] + "\n" + state[2], deepcopy(state[1])]
    return result


def prepare(source: Path, output: Path) -> dict[str, Any]:
    """Verify complete source matrix before freezing the transport derivative."""
    source, output = _safe(source), _safe(output)
    _, admitted = parent.verify(source)
    inventory = {row["id"]: row for row in json.loads(_read(source / "manifest.json"))["records"]}
    output.mkdir(parents=True, exist_ok=False)
    records, mapping = [], []
    for old_id, entry in admitted.items():
        row = inventory[old_id]
        raw = _encode(project(json.loads(_read(_inside(source, row["request_file"])))))
        identity = _digest(_encode([old_id, "one-text-before-image-v2", _digest(raw)]))[:24]
        image_file = row["image_files"][0]
        (output / image_file).write_bytes(_read(_inside(source, image_file)))
        (output / (identity + ".json")).write_bytes(raw)
        records.append({"id": identity, "request_file": identity + ".json", "image_files": [image_file]})
        mapping.append(
            {
                **entry,
                "parent_id": old_id,
                "id": identity,
                "parent_request_sha256": entry["sha256"],
                "sha256": _digest(raw),
                "projected_request_sha256": _digest(raw),
            }
        )
    manifest = _encode({"records": records})
    (output / "manifest.json").write_bytes(manifest)
    provenance = {
        "experiment": "source-ambiguity-evidence-transport-v2",
        "source_directory": str(source),
        "source_manifest_sha256": _digest(_read(source / "manifest.json")),
        "source_provenance_sha256": _digest(_read(source / "provenance.json")),
        "worker_manifest_sha256": _digest(manifest),
        "mapping": mapping,
        "builder_sha256": _digest(_read(Path(__file__))),
        "policy": (
            "Exact literal prefix + newline + exact supplemental JSON before unchanged image; "
            "source-only transport correction."
        ),
    }
    (output / "provenance.json").write_bytes(_encode(provenance))
    return provenance


def verify(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify every source and exact transport projection before scorer admission."""
    directory = _safe(directory)
    provenance = json.loads(_read(directory / "provenance.json"))
    source = _safe(Path(provenance["source_directory"]))
    source_provenance, admitted = parent.verify(source)
    if provenance["builder_sha256"] != _digest(_read(Path(__file__))):
        _fail("Transport builder differs from freeze")
    for filename, key in (("manifest.json", "source_manifest_sha256"), ("provenance.json", "source_provenance_sha256")):
        if _digest(_read(source / filename)) != provenance[key]:
            _fail("Transport parent hash differs")
    raw_manifest = _read(directory / "manifest.json")
    manifest = json.loads(raw_manifest)
    if (
        _digest(raw_manifest) != provenance["worker_manifest_sha256"]
        or set(manifest) != {"records"}
        or len(manifest["records"]) != len(admitted)
        or len(provenance["mapping"]) != len(admitted)
    ):
        _fail("Transport manifest inventory differs")
    originals = {row["id"]: row for row in json.loads(_read(source / "manifest.json"))["records"]}
    result = {}
    for record, entry, (old_id, original) in zip(
        manifest["records"], provenance["mapping"], admitted.items(), strict=True
    ):
        body = json.loads(_read(_inside(source, originals[old_id]["request_file"])))
        raw = _read(_inside(directory, record["request_file"]))
        identity = _digest(_encode([old_id, "one-text-before-image-v2", _digest(raw)]))[:24]
        image_file = originals[old_id]["image_files"][0]
        expected = {
            **original,
            "parent_id": old_id,
            "id": identity,
            "parent_request_sha256": original["sha256"],
            "sha256": _digest(raw),
            "projected_request_sha256": _digest(raw),
        }
        if (
            entry != expected
            or raw != _encode(project(body))
            or identity in result
            or record != {"id": identity, "request_file": identity + ".json", "image_files": [image_file]}
            or _read(directory / image_file) != _read(_inside(source, image_file))
        ):
            _fail("Transport changed source text/evidence/question/image")
        result[identity] = entry
    return source_provenance, result


def main() -> None:
    """Prepare/verify retained source-only packets without inference or references."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None:
        result = prepare(args.source, args.output)
        print(json.dumps({"records": len(result["mapping"]), "output": str(args.output)}))
    else:
        print(json.dumps({"verified": len(verify(args.source)[1])}))


if __name__ == "__main__":
    main()
