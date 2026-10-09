"""Source projection, nuisance controls and frozen evidence tamper detection."""

from __future__ import annotations

import base64
import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import lowlevel_evidence as evidence
from bench.lowlevel_cases import cases
from PIL import Image


@pytest.fixture(scope="module")
def source() -> dict:
    case = cases()[0]
    return evidence.snapshot(case["pdf_bytes"], case["evidence"])


def test_projection_drops_gold_and_file_metadata(source: dict) -> None:
    contaminated = deepcopy(source)
    contaminated.update(expected="join", family="SECRET", source_file="SECRET.pdf", native_choice="SECRET")
    contaminated["selector"].update(answer="SECRET", expected_groups=["SECRET"])
    for arm in evidence.ARMS:
        assert evidence.project(source, arm) == evidence.project(contaminated, arm)
        assert "SECRET" not in str(evidence.project(contaminated, arm))


def test_canonical_arm_removes_callback_nuisance(source: dict) -> None:
    changed = deepcopy(source)
    for glyph in changed["glyphs"]:
        glyph["source_order"] = 1000 - glyph["source_order"]
    assert evidence.project(changed, "glyphs") != evidence.project(source, "glyphs")
    assert evidence.project(changed, "canonical") == evidence.project(source, "canonical")


def test_operator_arm_does_not_leak_omitted_divider_counts(source: dict) -> None:
    changed = deepcopy(source)
    changed["operators"]["operator_count"] += 100
    changed["operators"]["decoded_sha256"] = "not model evidence"
    for operator in changed["operators"]["operators"]:
        operator["operator_index"] += 100
    assert evidence.project(changed, "operators") == evidence.project(source, "operators")


def test_source_chunks_preserve_literal_characters_and_dimensions(source: dict) -> None:
    assert ["".join(g["text"] for g in chunk) for chunk in source["target_atoms"]] == ["12", "EA"]
    assert len(source["all_target_ids"]) == len(set(source["all_target_ids"])) == 4
    assert max(source["images"]["crop256"]["pixels"]) == 256
    assert max(source["images"]["crop512"]["pixels"]) == 512
    image = Image.open(io.BytesIO(base64.b64decode(source["images"]["crop512"]["png_base64"])))
    assert image.getpixel((0, 0)) == (255, 255, 255)
    assert min(image.convert("L").getdata()) < 100
    with pytest.raises(ValueError, match="Unadmitted"):
        evidence.request([source], "liquid/d1", "crop256")


def test_frozen_request_reconstruction_and_tamper_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = tmp_path / "artifacts"
    (artifacts / "langfuse").mkdir(parents=True)
    (artifacts / "langfuse/catalog-prices.json").write_text('{"prices":{}}')
    monkeypatch.setattr(evidence, "ARTIFACTS", artifacts)
    directory = tmp_path / "frozen"
    manifest = evidence.prepare(directory, cohort=cases()[:3])
    assert evidence.verify(directory) == manifest
    assert manifest["targets_sha256"] == evidence.digest((directory / "private-targets.json").read_bytes())
    record = manifest["records"][0]
    body = json.loads((directory / record["request"]).read_bytes())
    body["state"].append("unfrozen evidence")
    (directory / record["request"]).write_bytes(evidence.encode(body))
    with pytest.raises(ValueError, match="differs"):
        evidence.verify(directory)


def test_identical_text_evidence_cannot_recover_hidden_divider() -> None:
    cohort = cases()
    sources = [c for c in cohort if c["family"] == "wrap" and c["encoding"] == "runs"][:3]
    snapshots = [evidence.snapshot(c["pdf_bytes"], c["evidence"]) for c in sources]
    assert {c["expected"] for c in sources} == {"join", "split", "unresolved"}
    for arm in ("minimal", "words", "glyphs", "canonical", "operators", "rolling"):
        assert evidence.project(snapshots[0], arm) == evidence.project(snapshots[1], arm)
        assert evidence.project(snapshots[1], arm) == evidence.project(snapshots[2], arm)
    assert evidence.project(snapshots[0], "vectors") != evidence.project(snapshots[1], "vectors")
    assert len({source["images"]["crop512"]["sha256"] for source in snapshots}) == 3
