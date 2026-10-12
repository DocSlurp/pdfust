"""Independent source/crop authentication and immutable full16 proposal preparation."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import pytest
from bench import p003_header_proposals_prepare as prepare
from bench import pipeline_vision_transcription as strict
from bench.silver import sha, write_json
from PIL import Image
from test_p003_header_proposals import page, table

import pdfust


def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    directory = tmp_path / "baseline"
    directory.mkdir()
    pdf = tmp_path / "source.pdf"
    with pdfust.open() as doc:
        doc.new_page(width=100, height=100)
        doc.save(pdf)
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(buffer, format="PNG")
    raw = buffer.getvalue()
    url = "data:image/png;base64," + base64.b64encode(raw).decode()
    records, pages = [], []
    for i in range(16):
        ident = f"p{i}"
        row = page([table(1 if i == 0 else 4, 4)])
        row.update(id=ident, original_rotation=0, layout_detection={})
        if i:
            row["status"] = "ok"
        crop = row["transcription_regions"][0]
        crop["detector_box"] = [0, 0, 100, 100]
        body = strict.request("openai/gpt-6-luna", url, crop["viewport"])
        crop["request"] = {"body_sha256": sha(json.dumps(body, separators=(",", ":")).encode())}
        crop["image"] = {"image_sha256": sha(raw), "image_bytes": len(raw), "image_viewport": crop["viewport"]}
        write_json(directory / (ident + "-request-0.json"), body)
        pages.append(row)
        records.append({"id": ident, "pdf_path": str(pdf), "pdf_sha256": sha(pdf.read_bytes()), "page_number": 0})
    frozen = {
        "records": records,
        "manifest_sha256": "original-source",
        "config": {"processor": "vision_regions", "generation_model": "openai/gpt-6-luna"},
    }
    report = {"results": pages, "config": frozen["config"]}
    write_json(directory / "frozen.json", frozen)
    write_json(directory / "report.json", report)
    trusted = tmp_path / "root-trusted.json"
    write_json(trusted, {"independent": "root"})
    monkeypatch.setattr(prepare.baseline, "authenticate", lambda *_a: (frozen, report, {}))
    monkeypatch.setattr(
        prepare.regions,
        "proposals",
        lambda *_a: [{"index": 0, "request_index": 0, "viewport": [0, 0, 100, 100], "detector_box": [0, 0, 100, 100]}],
    )
    return directory, trusted


def test_full16_authentication_freeze_and_no_baseline_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory, trust = fixture(tmp_path, monkeypatch)
    original = (directory / "report.json").read_bytes()
    output = tmp_path / "proposals"
    report = prepare.prepare(directory, trust, output)
    assert report["page_count"] == 16
    assert report["status_counts"] == {"header_proposals": 1, "unchanged_valid": 15}
    assert report["complete_alternative_count"] == 18
    assert (directory / "report.json").read_bytes() == original
    frozen = json.loads((output / "frozen.json").read_bytes())
    assert frozen["no_default_parser_repair"] is True
    assert frozen["references_read"] is False
    for ident, digest in frozen["plan_sha256"].items():
        assert sha((output / (ident + "-header-plan.json")).read_bytes()) == digest
    with pytest.raises(FileExistsError):
        prepare.prepare(directory, trust, output)


def test_missing_request_refused_and_changed_pixels_authentication_abort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory, trust = fixture(tmp_path, monkeypatch)
    (directory / "p0-request-0.json").unlink()
    output = tmp_path / "refused"
    report = prepare.prepare(directory, trust, output)
    assert report["status_counts"] == {"refused": 1, "unchanged_valid": 15}
    plan = json.loads((output / "p0-header-plan.json").read_bytes())
    assert plan["complete_page_alternatives"] == []
    request = json.loads((directory / "p1-request-0.json").read_bytes())
    request["max_tokens"] += 1
    write_json(directory / "p1-request-0.json", request)
    with pytest.raises(ValueError, match="provenance"):
        prepare.prepare(directory, trust, tmp_path / "corrupt")
