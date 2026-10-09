"""Derive separately labeled source-only text packets from staged image requests.

Only image parts are removed; literal text strings and questions are untouched.
Output preserves the strict remote worker manifest schema. Provenance is separate
and contains original request/image hashes, not labels or scoring references.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.remote_nimble import MODEL_ID, native_request

MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_REQUEST_BYTES = 2 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_RECORDS = 4096


def _read(path: Path, bound: int) -> bytes:
    with path.open("rb") as stream:
        payload = stream.read(bound + 1)
    if len(payload) > bound:
        message = "Source packet exceeds its admission bound"
        raise ValueError(message)
    return payload


def _path(directory: Path, name: str) -> Path:
    if not isinstance(name, str) or Path(name).is_absolute():
        message = "Source packet paths must be relative"
        raise ValueError(message)
    result = (directory / name).resolve(strict=True)
    if not result.is_relative_to(directory) or not result.is_file():
        message = "Source packet path escapes its manifest directory"
        raise ValueError(message)
    return result


def project(body: dict[str, Any], images: list[bytes]) -> dict[str, Any]:
    """Remove only verified canonical image parts and override the model route."""
    result = deepcopy(body)
    state = result.get("state")
    if not isinstance(state, list):
        message = "Expected canonical ordered text/image state parts"
        raise TypeError(message)
    retained = []
    image_parts = []
    for part in state:
        if isinstance(part, dict) and part.get("type") == "image_url":
            image_parts.append(part)
        elif isinstance(part, str):
            retained.append(part)
        else:
            message = "Unsupported state part; text projection must not discard evidence"
            raise ValueError(message)
    if not retained or len(image_parts) != len(images) or not images:
        message = "Expected literal source text and matching staged images"
        raise ValueError(message)
    for part, image in zip(image_parts, images, strict=True):
        url = part.get("image_url", {}).get("url", "")
        if not isinstance(url, str) or not url.startswith("data:image/png;base64,"):
            message = "Expected frozen canonical PNG data URI"
            raise ValueError(message)
        if base64.b64decode(url.split(",", 1)[1], validate=True) != image:
            message = "Staged image differs from the canonical request"
            raise ValueError(message)
    result["state"] = retained
    result["model"] = MODEL_ID
    native_request(result, [])  # Refuse hidden image evidence or unsupported questions.
    return result


def prepare(packets: str | Path, output: str | Path, limit: int = 24) -> Path:
    """Freeze the first explicitly staged records without reading scorer references."""
    if not 1 <= limit <= MAX_RECORDS:
        message = "Packet limit is outside admission"
        raise ValueError(message)
    source = Path(packets).resolve(strict=True)
    raw_manifest = _read(source, MAX_MANIFEST_BYTES)
    manifest = json.loads(raw_manifest)
    if not isinstance(manifest, dict) or set(manifest) != {"records"}:
        message = "Source worker manifest must contain only records"
        raise ValueError(message)
    records = manifest["records"]
    if not isinstance(records, list) or not limit <= len(records) <= MAX_RECORDS:
        message = "Source packet inventory cannot satisfy the requested limit"
        raise ValueError(message)
    prepared = []
    identities = set()
    for row in records[:limit]:
        if not isinstance(row, dict) or set(row) != {"id", "request_file", "image_files"}:
            message = "Source record must use the strict worker packet schema"
            raise ValueError(message)
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in identities:
            message = "Source IDs must be nonempty and unique"
            raise ValueError(message)
        identities.add(row["id"])
        if not isinstance(row["image_files"], list) or len(row["image_files"]) != 1:
            message = "Initial text ablation requires one source crop per packet"
            raise ValueError(message)
        original = _read(_path(source.parent, row["request_file"]), MAX_REQUEST_BYTES)
        images = [_read(_path(source.parent, name), MAX_IMAGE_BYTES) for name in row["image_files"]]
        body = json.loads(original)
        projected = project(body, images)
        payload = (json.dumps(projected, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()
        prepared.append((row, body, projected, original, images, payload))
    directory = Path(output).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "requests").mkdir()
    emitted = []
    provenance = []
    for number, (row, body, projected, original, images, payload) in enumerate(prepared):
        request_file = f"requests/{number:04d}.json"
        (directory / request_file).write_bytes(payload)
        emitted.append({"id": row["id"], "request_file": request_file, "image_files": []})
        provenance.append(
            {
                "id": row["id"],
                "source_request_file": row["request_file"],
                "source_request_sha256": hashlib.sha256(original).hexdigest(),
                "source_image_files": row["image_files"],
                "source_image_sha256": [hashlib.sha256(image).hexdigest() for image in images],
                "projected_request_sha256": hashlib.sha256(payload).hexdigest(),
                "source_model": body.get("model"),
                "projected_model": MODEL_ID,
                "text_projection_fields": {
                    "state": "literal strings retained in source order",
                    "questions": "unchanged",
                    "removed": "image_url state parts only",
                },
                "literal_state_sha256": [hashlib.sha256(part.encode()).hexdigest() for part in projected["state"]],
            }
        )
    (directory / "manifest.json").write_text(json.dumps({"records": emitted}, indent=2) + "\n")
    (directory / "provenance.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "ablation": "text-geometry",
                "source_manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
                "selection": "first explicitly staged records",
                "limit": limit,
                "records": provenance,
            },
            indent=2,
        )
        + "\n"
    )
    return directory / "manifest.json"


def main() -> None:
    """Prepare a source-only worker packet derivative."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=24)
    args = parser.parse_args()
    print(prepare(args.packets, args.output, args.limit))


if __name__ == "__main__":
    main()
