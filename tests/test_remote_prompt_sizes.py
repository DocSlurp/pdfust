"""CPU-only frozen source and exact prompt matrix regression tests."""

# ruff: noqa: ANN001, ANN201, ANN202 - pytest fixtures and fixed matrix sizes.
import base64
import json

import pytest
from bench import remote_prompt_sizes as sizes
from bench.remote_prompt_packets import _digest, _encode


def fixture(tmp_path, monkeypatch):
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    records, mapping = [], []
    image = b"source PNG bytes admitted by mocked full fresh verifier"
    for number in range(24):
        for edge in sizes.EDGES:
            identity = f"fresh-{number}-{edge}"
            body = {
                "model": "original-source-model",
                "state": [
                    f"literal source {number}",
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + base64.b64encode(image).decode()},
                    },
                ],
                "questions": {
                    "q0": {
                        "type": "choice",
                        "instructions": "Original question",
                        "criteria": {"join": "same cell", "split": "different rows", "unresolved": "unknown"},
                    }
                },
            }
            raw = _encode(body)
            (fresh / (identity + ".json")).write_bytes(raw)
            (fresh / (identity + ".png")).write_bytes(image)
            records.append({"id": identity, "request_file": identity + ".json", "image_files": [identity + ".png"]})
            mapping.append(
                {
                    "id": identity,
                    "source_id": f"p{number:04d}",
                    "page_id": str(number),
                    "requested_edge": edge,
                    "arm": f"fresh-rgb-{edge}",
                    "projected_request_sha256": _digest(raw),
                    "image_sha256": _digest(image),
                    "pixels": [edge, 20],
                    "render_scale": edge / 500,
                }
            )
    source = {"mapping": mapping, "builder_sha256": "historical frozen builder"}
    (fresh / "manifest.json").write_bytes(_encode({"records": records}))
    (fresh / "provenance.json").write_bytes(_encode(source))
    calls = []

    def full_verify(path):
        calls.append(path)
        assert path == fresh
        return source

    monkeypatch.setattr(sizes, "verify_fresh", full_verify)
    output = tmp_path / "packets"
    sizes.prepare(fresh, output)
    return fresh, output, calls


def test_complete_fixed_matrix_and_exact_evidence(tmp_path, monkeypatch):
    fresh, output, calls = fixture(tmp_path, monkeypatch)
    source, admitted = sizes.verify(output)
    assert calls == [fresh, fresh]
    assert len(admitted) == 480
    assert {row["variant"] for row in admitted.values()} == set(sizes.VARIANTS)
    assert {row["requested_edge"] for row in admitted.values()} == set(sizes.EDGES)
    assert len(source["mapping"]) == 120
    assert not list(output.glob("*target*"))
    assert not list(output.glob("*reference*"))
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert set(manifest) == {"records"}
    assert len(list(output.glob("*.png"))) == 120
    entry = next(iter(admitted.values()))
    body = json.loads((output / (entry["id"] + ".json")).read_bytes())
    assert body["state"][0] == "literal source 0"
    assert body["model"] == "original-source-model"


def test_rehashed_changed_source_is_refused(tmp_path, monkeypatch):
    _, output, _ = fixture(tmp_path, monkeypatch)
    manifest = json.loads((output / "manifest.json").read_bytes())
    path = output / manifest["records"][0]["request_file"]
    body = json.loads(path.read_bytes())
    body["state"][0] = "changed evidence"
    path.write_bytes(_encode(body))
    with pytest.raises(ValueError, match="changed source"):
        sizes.verify(output)


def test_rehashed_unapproved_prompt_is_refused(tmp_path, monkeypatch):
    _, output, _ = fixture(tmp_path, monkeypatch)
    manifest = json.loads((output / "manifest.json").read_bytes())
    path = output / manifest["records"][0]["request_file"]
    body = json.loads(path.read_bytes())
    body["questions"]["q0"]["instructions"] = "Unapproved case tip"
    path.write_bytes(_encode(body))
    with pytest.raises(ValueError, match="projection/provenance"):
        sizes.verify(output)


def test_missing_size_and_changed_predeclaration_refused(tmp_path, monkeypatch):
    _, output, _ = fixture(tmp_path, monkeypatch)
    source = {"mapping": [], "builder_sha256": "historical"}
    with pytest.raises(ValueError, match="matrix differs"):
        sizes.selection(source)
    path = output / "provenance.json"
    provenance = json.loads(path.read_bytes())
    provenance["models"] = ["best observed model"]
    path.write_bytes(_encode(provenance))
    with pytest.raises(ValueError, match="Predeclared"):
        sizes.verify(output)


def test_bad_source_blocks_result_and_target_reads(tmp_path, monkeypatch):
    reads = []

    def refuse(_path):
        message = "unverified fresh source"
        raise ValueError(message)

    monkeypatch.setattr(sizes, "verify", refuse)
    monkeypatch.setattr(sizes, "_read", reads.append)
    with pytest.raises(ValueError, match="unverified"):
        sizes.evaluate(tmp_path, {"flash": tmp_path})
    assert reads == []


def test_all_returned_hashes_checked_before_target_read(tmp_path, monkeypatch):
    source = {
        "source_directory": str(tmp_path),
        "source_index": str(tmp_path / "index.json"),
        "source_packets": str(tmp_path / "original"),
        "mapping": [],
    }
    monkeypatch.setattr(sizes, "verify", lambda _: (source, {}))
    monkeypatch.setattr(sizes, "verify_sources", lambda *_: ({}, {}))
    inspected = []

    def returned(path, _inventory):
        inspected.append(path.name)
        if path.name == "clef":
            message = "Returned request hash differs"
            raise ValueError(message)
        return {}, {}

    monkeypatch.setattr(sizes, "events", returned)
    target_reads = []
    monkeypatch.setattr(sizes, "_read", target_reads.append)
    with pytest.raises(ValueError, match="request hash"):
        sizes.evaluate(tmp_path, {"flash": tmp_path / "flash", "clef": tmp_path / "clef"})
    assert inspected == ["flash", "clef"]
    assert target_reads == []


def test_missing_matrix_preserves_all_denominators(tmp_path, monkeypatch):
    _, output, _ = fixture(tmp_path, monkeypatch)
    source, inventory = sizes.verify(output)
    source.update(
        source_directory=str(tmp_path),
        source_index=str(tmp_path / "index.json"),
        source_packets=str(tmp_path / "original"),
    )
    monkeypatch.setattr(sizes, "verify", lambda _: (source, inventory))
    originals = {f"p{number:04d}": {"row": {"page_ids": [str(number)]}} for number in range(24)}
    observations = {str(number): {} for number in range(24)}
    monkeypatch.setattr(sizes, "verify_sources", lambda *_: (originals, observations))
    monkeypatch.setattr(sizes, "events", lambda *_: ({}, {"completed": 0}))
    targets = [{"id": str(number), "expected": "join" if number < 16 else "unresolved"} for number in range(24)]
    raw = _encode(targets)
    (tmp_path / "private-targets.json").write_bytes(raw)
    (tmp_path / "manifest.json").write_bytes(_encode({"targets_sha256": _digest(raw)}))
    result = sizes.evaluate(output, {"flash": tmp_path})
    groups = result["models"]["flash"]["groups"]
    assert len(groups) == 20
    for entry in groups.values():
        assert entry["metrics"]["planned"] == 24
        assert entry["metrics"]["known_denominator"] == 16
        assert entry["metrics"]["ambiguous_denominator"] == 8
        assert entry["metrics"]["failures"]["missing"] == 24
        assert entry["metrics"]["inference_wall_seconds"] is None
    assert "0/24" in sizes.markdown(result)
