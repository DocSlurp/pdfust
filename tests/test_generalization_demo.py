"""Offline gallery keeps failures, exact outputs, and escaped transcription content."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_demo as demo
from bench import generalization_run, pipeline_run
from bench import pipeline_vision_transcription as vision
from test_generalization_report import hybrid_prediction
from test_pipeline_run import config, record

import pylopdf


def retained(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, processor: str = "whole") -> tuple[Path, Path, Path]:
    source = record(tmp_path)
    run = tmp_path / "run"
    run.mkdir()
    settings = {**config("native"), "processor": processor, "ocr_empty": False, "run_id": "demo-run"}
    if processor in {"vision", "vision_regions"}:
        raw = {
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
                                                "matrix": [
                                                    [
                                                        '<script>alert("bad")</script><img src="https://external.invalid/x">'
                                                    ]
                                                ],
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
        state = vision.parse(raw, [0, 0, 340, 300])
        result = {
            "id": source["id"],
            "status": "ok",
            "tables": state["tables"],
            "calls": [],
            "unresolved_ids": [],
            "source_conserved": False,
            "route": "vision_transcription",
            "viewport": [0, 0, 340, 300],
            "transcription_response": raw,
        }
        if processor == "vision_regions":
            result.pop("transcription_response")
            result.update(
                route="vision_transcription_regions",
                coverage="unverified",
                proposal_count=1,
                transcription_regions=[
                    {
                        "index": 0,
                        "request_index": 0,
                        "status": "ok",
                        "viewport": result["viewport"],
                        "transcription_response": raw,
                        "tables": state["tables"],
                    }
                ],
            )
        if processor == "vision_regions":
            box = {"label": "Table", "confidence": 0.9, "bbox": result["viewport"]}
            result["transcription_regions"][0]["detector_box"] = box
            result["layout_detection"] = {
                "type": "result",
                "device": "cpu",
                "viewport": result["viewport"],
                "boxes": [box],
            }
        (run / f"{source['id']}-result.json").write_text(json.dumps(result))
        (run / f"{source['id']}-structure.json").write_text(json.dumps(state))
        (run / f"{source['id']}.md").write_text(vision.markdown(state))
    else:
        process = generalization_run.process if processor == "regions" else pipeline_run.process
        result = process(source, settings, run, None)
        assert result["status"] == "ok"
    missing = {**source, "id": "missing-page"}
    failed = {**source, "id": "failed-page"}
    failure = {"id": failed["id"], "status": "error", "tables": [], "calls": [], "error": "<script>bad()</script>"}
    (run / "failed-page-result.json").write_text(json.dumps(failure))
    records = [source, missing, failed]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"split": "DEV", "pages": records}))
    frozen = {"config": settings, "records": records, "manifest_sha256": demo.sha(manifest.read_bytes())}
    report = {"config": settings, "results": [result, failure], "complete_output_pages": 1}
    (run / "frozen.json").write_text(json.dumps(frozen))
    (run / "report.json").write_text(json.dumps(report))
    artifacts = tmp_path / "artifacts"
    monkeypatch.setattr(demo, "ARTIFACT_ROOT", artifacts)
    monkeypatch.setattr(demo, "verify_code", lambda *_args, **_kwargs: {"archive_hashes_verified": True})
    return manifest, run, artifacts / "gallery"


@pytest.mark.parametrize("processor", ["whole", "regions", "vision", "vision_regions"])
def test_gallery_verifies_all_screen_pages_and_preserves_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, processor: str
) -> None:
    manifest, run, output = retained(tmp_path, monkeypatch, processor)
    result = demo.build(manifest, run, output, image_edge=512)
    assert result["page_count"] == 3
    assert [page["status"] for page in result["pages"]] == ["ok", "missing", "error"]
    assert result["pages"][0]["complete_output_verified"]
    assert not result["pages"][1]["complete_output_verified"]
    assert not result["pages"][2]["complete_output_verified"]
    for ident in ("opaque-page", "missing-page", "failed-page"):
        assert (output / "images" / f"{ident}.png").exists()
    assert (output / "outputs/opaque-page.md").read_bytes() == (run / "opaque-page.md").read_bytes()
    assert (output / "outputs/opaque-page-structure.json").read_bytes() == (
        run / "opaque-page-structure.json"
    ).read_bytes()
    html = (output / "index.html").read_text()
    assert "<script>" not in html
    assert "&lt;script&gt;bad()&lt;/script&gt;" in html
    assert "missing-page" in html
    assert "failed-page" in html
    if processor in {"vision", "vision_regions"}:
        assert "model-transcribed; no source ownership" in html
        assert '<img src="https://external.invalid/x">' not in html
        assert "&lt;script&gt;alert" in html
    else:
        assert "source-owned; complete retained-source conservation" in html


def test_source_hash_changes_and_successful_output_tampering_refuse_gallery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, run, output = retained(tmp_path, monkeypatch)
    (run / "opaque-page.md").write_text("altered output")
    with pytest.raises(ValueError, match="trusted exact rendering"):
        demo.build(manifest, run, output)
    # Use a fresh output path because construction may have created the rejected gallery directory.
    records = json.loads(manifest.read_text())["pages"]
    Path(records[0]["pdf_path"]).write_bytes(b"changed PDF")
    with pytest.raises(ValueError, match="source PDF hash"):
        demo.build(manifest, run, output.parent / "hash-rejected")


def test_optional_verified_evaluation_is_offline_and_identity_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, run, output = retained(tmp_path, monkeypatch)
    frozen = json.loads((run / "frozen.json").read_text())
    evaluation = tmp_path / "evaluation.json"
    evaluation.write_text(
        json.dumps(
            {
                "config": frozen["config"],
                "manifest_sha256": frozen["manifest_sha256"],
                "code_verification": {"archive_hashes_verified": True},
                "operational_pages": 1,
                "page_scores": [{"id": "opaque-page", "exact_page": False}],
            }
        )
    )
    demo.build(manifest, run, output, evaluation_path=evaluation)
    assert "Offline evaluation" in (output / "index.html").read_text()
    data: dict[str, Any] = json.loads(evaluation.read_text())
    data["manifest_sha256"] = "wrong"
    evaluation.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="identify this frozen run"):
        demo.build(manifest, run, output.parent / "wrong-evaluation", evaluation_path=evaluation)


def test_screen_bounds_and_output_destination_are_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, run, output = retained(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="ignored"):
        demo.build(manifest, run, tmp_path / "public-output")
    data = json.loads(manifest.read_text())
    data["pages"] *= 7
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="twenty pages"):
        demo.build(manifest, run, output)


def test_relative_pdf_record_is_rejected_before_resolution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, run, output = retained(tmp_path, monkeypatch)
    data = json.loads(manifest.read_text())
    frozen = json.loads((run / "frozen.json").read_text())
    for row in data["pages"]:
        row["pdf_path"] = "source.pdf"
    for row in frozen["records"]:
        row["pdf_path"] = "source.pdf"
    manifest.write_text(json.dumps(data))
    (run / "frozen.json").write_text(json.dumps(frozen))
    with pytest.raises(ValueError, match="paths must be absolute"):
        demo.build(manifest, run, output)


@pytest.mark.parametrize("processor", ["vision", "vision_regions"])
def test_vision_gallery_preserves_original_rotation_despite_assembly_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, processor: str
) -> None:
    manifest, run, output = retained(tmp_path, monkeypatch, processor)
    records = json.loads(manifest.read_text())["pages"]
    pdf = Path(records[0]["pdf_path"])
    with pylopdf.open(stream=pdf.read_bytes()) as document:
        document[0].set_rotation(90)
        data = document.tobytes()
    pdf.write_bytes(data)
    for item in records:
        item["pdf_sha256"] = demo.sha(data)
    manifest.write_text(json.dumps({"split": "DEV", "pages": records}))
    frozen = json.loads((run / "frozen.json").read_text())
    frozen.update(records=records, manifest_sha256=demo.sha(manifest.read_bytes()))
    frozen["config"]["normalize_rotation"] = True
    (run / "frozen.json").write_text(json.dumps(frozen))
    report = json.loads((run / "report.json").read_text())
    report["config"] = frozen["config"]
    prediction = report["results"][0]
    prediction.update(effective_rotation=0, rotation_normalized=True)
    (run / "opaque-page-result.json").write_text(json.dumps(prediction))
    (run / "report.json").write_text(json.dumps(report))
    result = demo.build(manifest, run, output, image_edge=512)
    assert result["pages"][0]["original_rotation"] == 90
    assert result["pages"][0]["display_viewport"] == [0, 0, 300, 340]
    assert result["pages"][0]["provenance"] == "model-transcribed; no source ownership"


def test_hybrid_gallery_keeps_mixed_provenance_and_atomic_parent_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = tmp_path / "run"
    run.mkdir()
    prediction = hybrid_prediction(run, monkeypatch, model_table=True)
    pdf = run / "input.pdf"
    records = [{"id": "negative", "pdf_path": str(pdf), "pdf_sha256": demo.sha(pdf.read_bytes()), "page_number": 0}]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"split": "DEV", "pages": records}))
    config = {"processor": "hybrid", "normalize_rotation": False, "run_id": "hybrid-test"}
    (run / "frozen.json").write_text(
        json.dumps(
            {
                "config": config,
                "records": records,
                "manifest_sha256": demo.sha(manifest.read_bytes()),
            }
        )
    )
    (run / "report.json").write_text(
        json.dumps({"config": config, "results": [prediction], "complete_output_pages": 1})
    )
    artifacts = tmp_path / "artifacts"
    monkeypatch.setattr(demo, "ARTIFACT_ROOT", artifacts)
    monkeypatch.setattr(demo, "verify_code", lambda *_args, **_kwargs: {"archive_hashes_verified": True})
    result = demo.build(manifest, run, artifacts / "gallery", image_edge=512)
    assert result["pages"][0]["complete_output_verified"]
    assert result["pages"][0]["provenance"] == "mixed native-source/model-transcribed; original words accounted"
    assert "MODEL literal" in (artifacts / "gallery/index.html").read_text()
