"""Shared CPU-only source-copy mechanics for L005 and L006 controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench.lowlevel_packets import _digest, _file, _write, verify_parent
from bench.silver import guard_path

if TYPE_CHECKING:
    from collections.abc import Callable


def sources(parent: Path) -> tuple[Path, dict[str, Any], dict[str, dict[str, Any]]]:
    """Verify a retained source freeze without interpreting target labels."""
    parent = guard_path(parent).resolve()
    manifest = verify_parent(parent)
    observations = {
        page["id"]: json.loads(_file(parent, page["observation_file"]).read_bytes()) for page in manifest["pages"]
    }
    return parent, manifest, observations


def begin(parent: Path, directory: Path, pages: list[dict[str, Any]]) -> Path:
    """Copy selected complete immutable sources and catalog before any target access."""
    directory = guard_path(directory).resolve()
    if directory.exists():
        message = "Preserve existing control freeze; choose a new destination"
        raise ValueError(message)
    directory.mkdir(parents=True)
    for page in pages:
        for key, hash_key in (("source_file", "source_sha256"), ("observation_file", "observation_sha256")):
            raw = _file(parent, page[key]).read_bytes()
            if _digest(raw) != page[hash_key]:
                message = "Control source changed during copy"
                raise ValueError(message)
            _file(directory, page[key]).write_bytes(raw)
    _file(directory, "catalog-prices.json").write_bytes(_file(parent, "catalog-prices.json").read_bytes())
    return directory


def finish(parent: Path, directory: Path, manifest: dict[str, Any], *, selected: bool = False) -> dict[str, Any]:
    """Write scorer metadata only after all source requests have been frozen."""
    if _digest(_file(parent, "manifest.json").read_bytes()) != manifest["parent_manifest_sha256"]:
        message = "Control parent manifest changed during preparation"
        raise ValueError(message)
    raw = _file(parent, "private-targets.json").read_bytes()
    parent_manifest = json.loads(_file(parent, "manifest.json").read_bytes())
    if _digest(raw) != parent_manifest["targets_sha256"]:
        message = "Control scorer targets changed"
        raise ValueError(message)
    if selected:
        retained = {page["id"] for page in manifest["pages"]}
        targets = [target for target in json.loads(raw) if target["id"] in retained]
        if {target["id"] for target in targets} != retained or len(targets) != len(retained):
            message = "Selected control targets do not cover source inventory"
            raise ValueError(message)
        manifest["targets_sha256"] = _write(_file(directory, "private-targets.json"), targets)
    else:
        _file(directory, "private-targets.json").write_bytes(raw)
        manifest["targets_sha256"] = _digest(raw)
    _write(_file(directory, "manifest.json"), manifest)
    return manifest


def verify_control(  # noqa: C901, PLR0912, PLR0913 - verify every source and body under explicit frozen policy.
    directory: Path,
    *,
    experiment: str,
    models: tuple[str, ...],
    arms: tuple[str, ...],
    builder: Callable[[list[dict[str, Any]], str, str], dict[str, Any]],
    max_bytes: int,
    selected: bool = False,
) -> dict[str, Any]:
    """Reconstruct complete singleton bodies and reject missing source observations."""
    directory = guard_path(directory).resolve()
    manifest = json.loads(_file(directory, "manifest.json").read_bytes())
    if (
        manifest.get("experiment") != experiment
        or manifest.get("models") != list(models)
        or manifest.get("arms") != list(arms)
    ):
        message = "Control experiment inventory changed"
        raise ValueError(message)
    parent = guard_path(Path(manifest["parent_directory"])).resolve()
    if _digest(_file(parent, "manifest.json").read_bytes()) != manifest["parent_manifest_sha256"]:
        message = "Control parent manifest changed"
        raise ValueError(message)
    original = verify_parent(parent)
    by_id = {page["id"]: page for page in original["pages"]}
    pages = manifest["pages"]
    if (
        not pages
        or len({page["id"] for page in pages}) != len(pages)
        or any(by_id.get(page["id"]) != page for page in pages)
    ):
        message = "Control copied source inventory differs from parent"
        raise ValueError(message)
    if not selected and pages != original["pages"]:
        message = "Control omitted parent source pages"
        raise ValueError(message)
    if _digest(_file(directory, "catalog-prices.json").read_bytes()) != manifest["catalog_sha256"]:
        message = "Control catalog changed"
        raise ValueError(message)
    observations = {}
    for page in pages:
        for key, hash_key in (("source_file", "source_sha256"), ("observation_file", "observation_sha256")):
            if _digest(_file(directory, page[key]).read_bytes()) != page[hash_key]:
                message = "Control copied source changed"
                raise ValueError(message)
        observations[page["id"]] = json.loads(_file(directory, page["observation_file"]).read_bytes())
    seen, filenames = set(), set()
    for record in manifest["records"]:
        if len(record["page_ids"]) != 1 or record["request"] in filenames:
            message = "Control singleton request inventory is invalid"
            raise ValueError(message)
        filenames.add(record["request"])
        ident = record["page_ids"][0]
        identity = (record["model"], record["arm"], ident)
        if ident not in observations or identity in seen:
            message = "Control repeats or invents a source observation"
            raise ValueError(message)
        seen.add(identity)
        raw = _file(directory, record["request"]).read_bytes()
        if (
            len(raw) > max_bytes
            or len(raw) != record["body_bytes"]
            or _digest(raw) != record["sha256"]
            or raw != encoded_body(builder([observations[ident]], record["model"], record["arm"]))
        ):
            message = "Control body differs from source reconstruction"
            raise ValueError(message)
    if seen != {(model, arm, ident) for model in models for arm in arms for ident in observations}:
        message = "Control request inventory is incomplete"
        raise ValueError(message)
    return manifest


def encoded_body(body: dict[str, Any]) -> bytes:
    """Match frozen compact body JSON serialization."""
    return json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
