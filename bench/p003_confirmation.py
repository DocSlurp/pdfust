"""Independent references for the frozen source-only P003 confirmation corpus."""

# ruff: noqa: EM101, EM102, TRY003, PLR2004, ANN401, C901, PLR0912
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bench.generalization_scoring import _cells, parse_annotation_html
from bench.silver import canonical, guard_path, sha, write_json

IDENTITY_BASIS = "source-only-confirmation-v1"
# Independently announced source freeze, before reference access or model calls.
SOURCE_HASHES = {
    "manifest.json": "2548256a5289d64e1a0a5d0de1683c6e068fa8db295fce64814f3bb134664b99",
    "private-provenance.json": "7126a8bd175e71784e4ff6907972b6c3a3d307a86e753ab0e568287d1b07a0ac",
    "construction-targets.json": "49c515968c92bb4665f4888dbcd7930ef9084814fe22b12a8088c4fa86f8d1b2",
}


def read(path: Path) -> Any:
    """Read a guarded explicit artifact path."""
    return json.loads(guard_path(path).read_bytes())


def validate_identity(manifest: dict[str, Any]) -> str:
    """Validate source identity without any scoring references."""
    if manifest.get("schema") != 2 or manifest.get("identity_basis") != IDENTITY_BASIS:
        raise ValueError("Unsupported confirmation source identity")
    if manifest.get("split") != "DEV":
        raise ValueError("Only explicit DEV confirmation sources may be scored")
    pages = manifest["pages"]
    ids = [page["id"] for page in pages]
    if not pages or len(ids) != len(set(ids)):
        raise ValueError("Confirmation source IDs must be unique")
    identity = sha(
        canonical(
            {
                "schema": 2,
                "identity_basis": IDENTITY_BASIS,
                "selection_sha256": manifest["selection_sha256"],
                "pages": [{key: value for key, value in page.items() if key != "pdf_path"} for page in pages],
            }
        )
    )
    if identity != manifest["dataset_sha256"]:
        raise ValueError("Confirmation source identity changed")
    for page in pages:
        path = guard_path(Path(page["pdf_path"]))
        if not path.is_absolute() or sha(path.read_bytes()) != page["pdf_sha256"]:
            raise ValueError("Confirmation source PDF changed")
    return identity


def natural_reference(page: dict[str, Any], provenance: dict[str, Any], annotation: dict[str, Any]) -> dict[str, Any]:
    """Project only selected official annotations after the source freeze."""
    if annotation["page_info"]["image_path"] != provenance["source_id"]:
        raise ValueError("Selected annotation source differs")
    transform = provenance["annotation_to_display"]
    if transform != {"offset_x": 0, "offset_y": 0, "rotation": 0, "scale_x": 0.36, "scale_y": 0.36}:
        raise ValueError("Unsupported frozen annotation transform")
    blocks = [block for block in annotation["layout_dets"] if block["category_type"] == "table"]
    if len(blocks) != provenance["category_counts"].get("table", 0):
        raise ValueError("Selected table metadata differs from frozen source selection")
    tables, errors = [], []
    for block in blocks:
        parsed = parse_annotation_html(block.get("html", ""))
        if not parsed["structural_scored"] or block.get("ignore", False):
            errors.extend(parsed["annotation_errors"] or ["Ignored table annotation"])
        poly = block["poly"]
        if len(poly) < 8 or len(poly) % 2:
            raise ValueError("Invalid selected table polygon")
        for table in parsed["tables"]:
            table["bbox"] = [
                min(poly[::2]) * 0.36,
                min(poly[1::2]) * 0.36,
                max(poly[::2]) * 0.36,
                max(poly[1::2]) * 0.36,
            ]
            _cells(table)
            tables.append(table)
    return {
        "id": page["id"],
        "structural_scored": not errors,
        "tables": tables,
        "annotation_errors": errors,
        "annotation_source_sha256": sha(canonical(annotation)),
        "reference_basis": "selected official HTML and polygons, projected by frozen source transform",
    }


def build_targets(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Authenticate the predeclared freeze and rebuild all scorer-only references."""
    directory = guard_path(directory)
    for filename, digest in SOURCE_HASHES.items():
        if sha(guard_path(directory / filename).read_bytes()) != digest:
            raise ValueError(f"Independently frozen confirmation artifact changed: {filename}")
    manifest = read(directory / "manifest.json")
    identity = validate_identity(manifest)
    provenance = {row["id"]: row for row in read(directory / "private-provenance.json")}
    construction = read(directory / "construction-targets.json")
    if construction["dataset_sha256"] != identity:
        raise ValueError("Construction targets identify different sources")
    authored = {row["id"]: row for row in construction["pages"]}
    annotations: dict[str, dict[str, Any]] = {}
    annotation_paths: dict[str, str] = {}
    targets = []
    for page in manifest["pages"]:
        detail = provenance[page["id"]]
        if page["cohort"] == "omnidoc":
            path = guard_path(Path(detail["annotation_path"]))
            key = str(path)
            if key not in annotations:
                payload = path.read_bytes()
                digest = sha(payload)
                if digest != detail["annotation_sha256"]:
                    raise ValueError("Authorized public annotation bytes changed")
                annotation_paths[key] = digest
                rows = json.loads(payload)
                annotations[key] = {row["page_info"]["image_path"]: row for row in rows}
                if len(annotations[key]) != len(rows):
                    raise ValueError("Official annotation source IDs are not unique")
            elif annotation_paths[key] != detail["annotation_sha256"]:
                raise ValueError("Inconsistent annotation provenance")
            targets.append(natural_reference(page, detail, annotations[key][detail["source_id"]]))
        elif page["cohort"] == "authored":
            reference = authored[page["id"]]
            for table in reference["tables"]:
                _cells(table)
            targets.append(reference)
        else:
            raise ValueError("Unexpected confirmation cohort")
    if set(authored) != {page["id"] for page in manifest["pages"] if page["cohort"] == "authored"}:
        raise ValueError("Construction reference inventory differs")
    return manifest, {"schema": 2, "identity_basis": IDENTITY_BASIS, "dataset_sha256": identity, "pages": targets}


def attach_targets(directory: Path) -> dict[str, Any]:
    """Write separate references and receipt, preserving the model-facing source manifest."""
    manifest, targets = build_targets(directory)
    path = directory / "private-targets.json"
    if path.exists() and read(path) != targets:
        raise ValueError("Existing confirmation references differ; refusing overwrite")
    write_json(path, targets)
    receipt = {
        "schema": 1,
        "scope": "independent scorer-only reference attachment",
        "dataset_sha256": manifest["dataset_sha256"],
        "source_sha256": SOURCE_HASHES,
        "targets_sha256": sha(path.read_bytes()),
        "pages": len(targets["pages"]),
        "structurally_scored_pages": sum(page["structural_scored"] for page in targets["pages"]),
        "tables": sum(len(page["tables"]) for page in targets["pages"]),
    }
    write_json(directory / "target-attachment.json", receipt)
    return receipt


def load_corpus(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify attached targets against independent construction and official annotations."""
    manifest, rebuilt = build_targets(directory)
    targets = read(directory / "private-targets.json")
    receipt = read(directory / "target-attachment.json")
    if targets != rebuilt or receipt["targets_sha256"] != sha((directory / "private-targets.json").read_bytes()):
        raise ValueError("Confirmation scoring references changed")
    if receipt["dataset_sha256"] != manifest["dataset_sha256"] or receipt["source_sha256"] != SOURCE_HASHES:
        raise ValueError("Confirmation target attachment provenance differs")
    return manifest, targets


def main() -> None:
    """Attach or independently verify the explicit frozen confirmation corpus."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--attach-targets", action="store_true")
    args = parser.parse_args()
    if args.attach_targets:
        print(json.dumps(attach_targets(args.directory), indent=2))
    else:
        manifest, targets = load_corpus(args.directory)
        print(json.dumps({"dataset_sha256": manifest["dataset_sha256"], "pages": len(targets["pages"])}))


if __name__ == "__main__":
    main()
