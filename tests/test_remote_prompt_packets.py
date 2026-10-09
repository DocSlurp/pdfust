"""CPU-only blinded prompt projection tests; no targets or prior answers."""

from __future__ import annotations

import base64
import io
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import remote_prompt_packets as packets
from PIL import Image


def source(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path / "source"
    directory.mkdir()
    output = io.BytesIO()
    Image.new("RGB", (512, 64), "white").save(output, format="PNG")
    png = output.getvalue()
    body = {
        "model": "perplexity/pplx-decider-v1.1-27b",
        "state": [
            "Literal Ω text  A\nB; 10.00",
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
        ],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Original wording.",
                "criteria": {
                    "join": "Original one-cell option",
                    "split": "Original separate-row option",
                    "unresolved": "Original insufficient option",
                },
            }
        },
    }
    for index in range(2):
        (directory / f"p{index}.json").write_text(json.dumps(body, indent=2))
        (directory / f"p{index}.png").write_bytes(png)
    manifest = {
        "records": [
            {"id": f"p{index}", "request_file": f"p{index}.json", "image_files": [f"p{index}.png"]}
            for index in range(2)
        ]
    }
    (directory / "manifest.json").write_text(json.dumps(manifest))
    # These unrelated files must never influence/read the source-only builder.
    (directory / "private-targets.json").write_text("unreadable reference sentinel")
    (directory / "results.json").write_text("unreadable prior answer sentinel")
    return directory, body


def test_four_generic_variants_preserve_state_questions_and_keys(tmp_path: Path) -> None:
    _, body = source(tmp_path)
    original = deepcopy(body)
    variants = []
    for name in packets.VARIANTS:
        projected = packets.transform(body, name)
        assert projected["state"] == body["state"]
        assert projected["model"] == body["model"]
        assert projected["questions"]["q0"]["type"] == "choice"
        assert tuple(projected["questions"]["q0"]["criteria"]) == packets.CHOICES
        assert "Literal Ω" not in projected["questions"]["q0"]["instructions"]
        assert projected["questions"]["q0"]["criteria"] == packets.VARIANTS[name]["criteria"]
        variants.append(projected["questions"]["q0"]["instructions"])
    assert len(set(variants)) == 4
    assert body == original


def test_freeze_worker_schema_and_blind_source_mapping(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory, body = source(tmp_path)
    destination = tmp_path / "prepared"
    read = packets._read  # noqa: SLF001
    opened = []

    def audited_read(path: Path, limit: int) -> bytes:
        opened.append(path.name)
        if path.name in {"private-targets.json", "results.json"}:
            pytest.fail("reference/answer read is forbidden")
        return read(path, limit)

    monkeypatch.setattr(packets, "_read", audited_read)
    provenance = packets.prepare(directory, destination, limit=2)
    assert provenance["source_count"] == 2
    assert provenance["body_count"] == 8
    assert [item["variant"] for item in provenance["mapping"]] == list(packets.VARIANTS) * 2
    assert {item["source_id"] for item in provenance["mapping"]} == {"p0", "p1"}
    manifest = json.loads((destination / "manifest.json").read_text())
    assert set(manifest) == {"records"}
    assert len({row["id"] for row in manifest["records"]}) == 8
    assert all(set(row) == {"id", "request_file", "image_files"} for row in manifest["records"])
    assert all(not row["id"].startswith("p0") for row in manifest["records"])
    for row in manifest["records"]:
        projected = json.loads((destination / row["request_file"]).read_text())
        assert set(projected) == set(body)
        assert projected["state"] == body["state"]
        assert (destination / row["image_files"][0]).read_bytes() == (directory / "p0.png").read_bytes()
    assert "private-targets.json" not in opened
    assert "results.json" not in opened
    sentinel = destination / "results.json"
    sentinel.write_text("retained worker responses")
    assert packets.prepare(directory, destination, limit=2) == provenance
    assert sentinel.read_text() == "retained worker responses"


def test_original_control_exact_bytes_and_refuse_differing_freeze(tmp_path: Path) -> None:
    directory, _ = source(tmp_path)
    destination = tmp_path / "prepared"
    provenance = packets.prepare(directory, destination, limit=2, include_original=True)
    originals = [row for row in provenance["mapping"] if row["variant"] == "original"]
    assert len(originals) == 2
    for row in originals:
        assert (destination / (row["id"] + ".json")).read_bytes() == (
            directory / row["source_request_file"]
        ).read_bytes()
    before = (destination / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="differing"):
        packets.prepare(directory, destination, limit=2)
    assert (destination / "manifest.json").read_bytes() == before


@pytest.mark.parametrize("field", ["state", "model", "keys", "type", "extra"])
def test_projection_rejects_non_prompt_changes(tmp_path: Path, field: str) -> None:
    _, body = source(tmp_path)
    changed = packets.transform(body, "neutral")
    if field == "state":
        changed["state"][0] += "changed source"
    elif field == "model":
        changed["model"] = "other"
    elif field == "keys":
        changed["questions"]["q0"]["criteria"] = {"join": "one", "unresolved": "unknown", "split": "two"}
    elif field == "type":
        changed["questions"]["q0"]["type"] = "score"
    else:
        changed["expected"] = "join"
    with pytest.raises(ValueError, match="Prompt projection"):
        packets.assert_prompt_only(body, changed)


def test_non_rgb512_transport_refuses_before_destination_write(tmp_path: Path) -> None:
    directory, body = source(tmp_path)
    output = io.BytesIO()
    Image.new("RGB", (768, 64), "white").save(output, format="PNG")
    (directory / "p0.png").write_bytes(output.getvalue())
    body["state"][1]["image_url"]["url"] = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode()
    (directory / "p0.json").write_text(json.dumps(body))
    destination = tmp_path / "prepared"
    with pytest.raises(ValueError, match="RGB512"):
        packets.prepare(directory, destination, limit=2)
    assert not destination.exists()
