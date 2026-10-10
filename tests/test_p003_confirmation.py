"""Confirmation references stay separate from frozen model inputs."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import p003_confirmation as confirmation
from bench.silver import canonical, sha, write_json


def source_manifest(tmp_path: Path) -> dict[str, Any]:
    pdf = tmp_path / "page.pdf"
    pdf.write_bytes(b"fixed source PDF bytes")
    manifest = {
        "schema": 2,
        "identity_basis": confirmation.IDENTITY_BASIS,
        "split": "DEV",
        "selection_sha256": "selected independently",
        "pages": [
            {
                "id": "new-page",
                "pdf_path": str(pdf),
                "pdf_sha256": sha(pdf.read_bytes()),
                "page_number": 0,
                "cohort": "omnidoc",
            }
        ],
    }
    manifest["dataset_sha256"] = sha(
        canonical(
            {
                "schema": 2,
                "identity_basis": confirmation.IDENTITY_BASIS,
                "selection_sha256": manifest["selection_sha256"],
                "pages": [
                    {key: value for key, value in page.items() if key != "pdf_path"} for page in manifest["pages"]
                ],
            }
        )
    )
    return manifest


def test_source_identity_rejects_changed_metadata_and_pdf(tmp_path: Path) -> None:
    manifest = source_manifest(tmp_path)
    assert confirmation.validate_identity(manifest) == manifest["dataset_sha256"]
    changed = deepcopy(manifest)
    changed["pages"][0]["cohort"] = "authored"
    with pytest.raises(ValueError, match="identity changed"):
        confirmation.validate_identity(changed)
    (tmp_path / "page.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="PDF changed"):
        confirmation.validate_identity(manifest)


def test_natural_projection_preserves_spans_and_annotation_refusal() -> None:
    page = {"id": "new-page"}
    provenance = {
        "source_id": "official.png",
        "category_counts": {"table": 1},
        "annotation_to_display": {"scale_x": 0.36, "scale_y": 0.36, "offset_x": 0, "offset_y": 0, "rotation": 0},
    }
    annotation = {
        "page_info": {"image_path": "official.png"},
        "layout_dets": [
            {
                "category_type": "table",
                "poly": [0, 0, 100, 0, 100, 200, 0, 200],
                "html": '<table><tr><td colspan="2">Merged</td></tr><tr><td>A</td><td>B</td></tr></table>',
            }
        ],
    }
    reference = confirmation.natural_reference(page, provenance, annotation)
    assert reference["structural_scored"]
    assert reference["tables"][0]["bbox"] == [0, 0, 36, 72]
    assert reference["tables"][0]["values"][0] == ["Merged", None]
    annotation["layout_dets"][0]["ignore"] = True
    assert not confirmation.natural_reference(page, provenance, annotation)["structural_scored"]


def test_attachment_rebuild_detects_changed_target_not_self_attested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = source_manifest(tmp_path)
    annotation_path = tmp_path / "official.json"
    write_json(annotation_path, [{"page_info": {"image_path": "official.png"}, "layout_dets": []}])
    provenance = [
        {
            "id": "new-page",
            "source_id": "official.png",
            "category_counts": {},
            "annotation_path": str(annotation_path),
            "annotation_sha256": sha(annotation_path.read_bytes()),
            "annotation_to_display": {"scale_x": 0.36, "scale_y": 0.36, "offset_x": 0, "offset_y": 0, "rotation": 0},
        }
    ]
    write_json(tmp_path / "manifest.json", manifest)
    write_json(tmp_path / "private-provenance.json", provenance)
    write_json(tmp_path / "construction-targets.json", {"dataset_sha256": manifest["dataset_sha256"], "pages": []})
    trusted = {name: sha((tmp_path / name).read_bytes()) for name in confirmation.SOURCE_HASHES}
    monkeypatch.setattr(confirmation, "SOURCE_HASHES", trusted)
    original_manifest = (tmp_path / "manifest.json").read_bytes()
    confirmation.attach_targets(tmp_path)
    _, targets = confirmation.load_corpus(tmp_path)
    assert len(targets["pages"]) == 1
    assert (tmp_path / "manifest.json").read_bytes() == original_manifest
    targets["pages"][0]["structural_scored"] = False
    write_json(tmp_path / "private-targets.json", targets)
    receipt = confirmation.read(tmp_path / "target-attachment.json")
    receipt["targets_sha256"] = sha((tmp_path / "private-targets.json").read_bytes())
    write_json(tmp_path / "target-attachment.json", receipt)
    with pytest.raises(ValueError, match="references changed"):
        confirmation.load_corpus(tmp_path)
