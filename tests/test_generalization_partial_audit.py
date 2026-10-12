"""Retained identity and source-only escaped-gallery checks without inference."""

import hashlib
import json
from pathlib import Path

import pytest
from bench.generalization_partial_audit import CONTROLS, audit, gallery
from bench.pipeline_vision_partial import salvage

import pdfust


def write(path: Path, value: dict) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value).encode()
    path.write_bytes(data)
    return data


@pytest.mark.parametrize(
    "failure",
    ["missing_report", "missing_identity", "changed_report", "changed_corpus", "missing_prediction", "missing_score"],
)
def test_audit_rejects_missing_or_changed_identity_and_incomplete_coverage(tmp_path: Path, failure: str) -> None:
    ids = [f"page{i}" for i in range(16)]
    corpus = tmp_path / "screens/natural16"
    manifest_bytes = write(
        corpus / "manifest.json", {"split": "DEV", "dataset_sha256": "fixture", "pages": [{"id": i} for i in ids]}
    )
    write(
        corpus / "private-targets.json", {"dataset_sha256": "fixture", "pages": [{"id": i, "tables": []} for i in ids]}
    )
    run = tmp_path / CONTROLS[0]
    report = {"results": [{"id": i} for i in ids]}
    if failure == "missing_prediction":
        report["results"].pop()
    encoded = write(run / "report.json", report)
    scores = [{"id": i} for i in ids]
    if failure == "missing_score":
        scores.pop()
    evaluation = {
        "report_sha256": hashlib.sha256(encoded).hexdigest(),
        "page_scores": scores,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "dataset_sha256": "fixture",
    }
    if failure == "missing_identity":
        evaluation.pop("report_sha256")
    if failure == "changed_corpus":
        evaluation["dataset_sha256"] = "different"
    write(run / "verified-evaluation.json", evaluation)
    expected: type[Exception]
    match: str | None
    if failure == "missing_report":
        (run / "report.json").unlink()
        expected, match = FileNotFoundError, None
    else:
        expected, match = ValueError, "coverage"
    if failure == "changed_report":
        (run / "report.json").write_bytes(encoded + b" ")
        match = "Changed report identity"
    if failure == "missing_identity":
        match = "Changed report identity"
    if failure == "changed_corpus":
        match = "corpus identity"
    with pytest.raises(expected, match=match):
        audit(tmp_path, tmp_path / "output")
    assert not (tmp_path / "output" / "audit.json").exists()


def test_gallery_uses_source_pdf_and_escapes_transcription_status_and_diagnostics(tmp_path: Path) -> None:
    with pdfust.Document() as document:
        document.new_page(width=80, height=120)
        data = document.tobytes()
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(data)
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "answers": {
                                "q0": {
                                    "tables": [
                                        {
                                            "bbox": [0, 0, 1000, 1000],
                                            "matrix": [["<script>& literal"]],
                                            "mergedspans": [],
                                        }
                                    ]
                                }
                            }
                        }
                    )
                },
            }
        ]
    }
    partial = salvage([{"viewport": [0, 0, 80, 120], "response": response}], [0, 0, 80, 120])
    partial.update(id="fixture", baseline_status="<broken>")
    partial["quarantined"].append({"detail": '<img onerror="unsafe">'})
    manifest = {
        "pages": [
            {"id": "fixture", "pdf_path": str(pdf), "pdf_sha256": hashlib.sha256(data).hexdigest(), "page_number": 0}
        ]
    }
    result = gallery(manifest, [partial], tmp_path / "gallery")
    markup = Path(result["path"]).read_text()
    assert "PARTIAL" in markup
    assert "&lt;script&gt;&amp; literal" in markup
    assert "&lt;broken&gt;" in markup
    assert "&lt;img onerror=" in markup
    assert "<script>" not in markup
    assert (tmp_path / "gallery" / "fixture.png").exists()
    assert result["pages"] == 1
    assert pdf.read_bytes() == data
