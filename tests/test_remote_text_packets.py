# ruff: noqa: ANN001, ANN201 - pytest fixture interfaces.
import base64
import hashlib
import json

import pytest
from bench.remote_nimble import MODEL_ID
from bench.remote_text_packets import prepare, project


def source_body():
    return {
        "model": "original",
        "state": [
            ' {"observations":{"q0":{"text":"a b"}},"image_pixels":[512,99]} ',
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(b"png").decode()}},
        ],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Preserve this question exactly.",
                "criteria": {"join": "Join", "split": "Split", "unresolved": "Unresolved"},
            }
        },
    }


def test_projection_preserves_literal_text_and_questions():
    original = source_body()
    derived = project(original, [b"png"])
    assert derived["state"] == original["state"][:1]
    assert derived["questions"] == original["questions"]
    assert derived["model"] == MODEL_ID
    assert len(original["state"]) == 2
    with pytest.raises(ValueError, match="differs"):
        project(original, [b"different"])


def test_unknown_evidence_cannot_be_silently_removed():
    original = source_body()
    original["state"].append({"type": "text", "text": "another fact"})
    with pytest.raises(ValueError, match="discard evidence"):
        project(original, [b"png"])


def test_prepare_manifest_and_source_hashes(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    original = json.dumps(source_body()).encode()
    (source / "body.json").write_bytes(original)
    (source / "image.png").write_bytes(b"png")
    rows = [
        {"id": "fresh-rgb-512-q0", "request_file": "body.json", "image_files": ["image.png"]},
        {"id": "excluded", "request_file": "unread.json", "image_files": ["unread.png"]},
    ]
    (source / "manifest.json").write_text(json.dumps({"records": rows}))
    output = tmp_path / "output"
    result = prepare(source / "manifest.json", output, 1)
    manifest = json.loads(result.read_bytes())
    assert set(manifest) == {"records"}
    assert manifest["records"] == [{"id": rows[0]["id"], "request_file": "requests/0000.json", "image_files": []}]
    provenance = json.loads((output / "provenance.json").read_bytes())["records"][0]
    assert provenance["source_request_sha256"] == hashlib.sha256(original).hexdigest()
    assert provenance["source_image_sha256"] == [hashlib.sha256(b"png").hexdigest()]
    assert (
        provenance["projected_request_sha256"]
        == hashlib.sha256((output / "requests/0000.json").read_bytes()).hexdigest()
    )
    with pytest.raises(FileExistsError):
        prepare(source / "manifest.json", output, 1)


def test_manifest_extra_keys_refused(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"records": [], "targets": {}}))
    with pytest.raises(ValueError, match="only records"):
        prepare(manifest, tmp_path / "output", 1)
