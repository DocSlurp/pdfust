"""Synthetic-fixture tests for the local-study Langfuse adapters (no network, no retained artifacts)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
from bench.langfuse_adapters import local_specialist, local_studies
from bench.langfuse_adapters.base import Experiment, validate

if TYPE_CHECKING:
    from pathlib import Path

PDF = b"%PDF-1.7 synthetic"


def _write(path: Path, value: Any) -> None:  # noqa: ANN401 - arbitrary JSON fixture.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _one(experiments: list[Experiment], dataset: str) -> Experiment:
    matches = [e for e in experiments if e.dataset == dataset]
    assert len(matches) == 1, [e.dataset for e in experiments]
    validate(matches[0])
    return matches[0]


def _run(experiment: Experiment, name: str) -> Any:  # noqa: ANN401 - Run lookup helper.
    return next(run for run in experiment.runs if run.name == name)


def test_empty_artifact_root_yields_nothing(tmp_path: Path) -> None:
    assert list(local_studies.collect(tmp_path)) == []
    assert list(local_specialist.collect(tmp_path)) == []


def test_protected_paths_are_refused(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        local_studies.ref(tmp_path / "silver-heldout-v1" / "x.pdf")


def test_encodings_rows_and_cohort_aggregates(tmp_path: Path) -> None:
    (tmp_path / "encodings").mkdir()
    (tmp_path / "encodings" / "literal.pdf").write_bytes(PDF)
    base = {
        "note": "",
        "input_sha256": "a",
        "render_sha256": "b",
        "word_count": 12,
        "table_count": 1,
        "open_extract_ms": 8.0,
        "samples_ms": [8.0],
        "page_empty_ocr_gate": False,
        "image_coverage_upper_bound": 0.0,
        "image_probe_ms": 0.1,
        "unresolved_raster_evidence": False,
        "large_raster_gate": False,
    }
    results = [
        {
            **base,
            "name": "literal",
            "cohort": "equivalent",
            "exact_grid": True,
            "matrices": [local_studies.ENCODING_REFERENCE],
        },
        {**base, "name": "pure-scan", "cohort": "ocr-routing", "exact_grid": False, "matrices": [], "word_count": 0},
    ]
    _write(tmp_path / "encodings" / "results.json", {"code_sha256": "c", "results": results})
    experiment = _one(list(local_studies.encodings(tmp_path)), "exp/encodings/routing-audit")
    assert experiment.items[0].expected == {"grid": local_studies.ENCODING_REFERENCE}
    assert "semantics" in experiment.items[1].expected
    assert experiment.items[0].input["pdf"]["bytes"] == len(PDF)
    assert experiment.items[1].input["pdf"]["missing"] is True
    run = experiment.runs[0]
    assert run.scores["equivalent.exact_grid"] == 1
    assert run.scores["ocr-routing.exact_grid"] == 0
    assert run.rows[1].scores["exact_grid"] is False


def test_semantic_controls_score_expected_outcome(tmp_path: Path) -> None:
    cell = {"text": "", "id_hex": None, "object_id": [1, 0], "mcid": 0, "role": "/TD", "scope": None}
    table = [[{**cell, "text": t} for t in row] for row in local_studies.SEMANTIC_POSITIVE]
    records = [
        {
            "name": "valid",
            "group": "synthetic",
            "bytes": 10,
            "median_ms": 1.0,
            "timings_ms": [1.0],
            "result": {"status": "ok", "tables": [table], "tagged_tables": 1, "abstentions": []},
        },
        {
            "name": "cycle",
            "group": "synthetic",
            "bytes": 10,
            "median_ms": 0.1,
            "timings_ms": [0.1],
            "result": {"status": "abstain", "tables": [], "tagged_tables": 0, "abstentions": ["tree_limit_or_cycle"]},
        },
        {
            "name": "tests/assets/none.pdf",
            "group": "corpus",
            "bytes": 10,
            "median_ms": 0.1,
            "timings_ms": [0.1],
            "result": {"status": "error", "error": "boom", "tables": []},
        },
    ]
    _write(tmp_path / "semantic" / "results.json", records)
    experiment = _one(list(local_studies.semantic(tmp_path)), "exp/semantic/tagged-tables")
    rows = {row.item_key: row for row in experiment.runs[0].rows}
    assert rows["valid"].scores["expected_outcome"] is True
    assert rows["cycle"].scores["expected_outcome"] is True
    assert rows["cycle"].metadata["outcome"] == "tree_limit_or_cycle"
    assert "expected_outcome" not in rows["tests/assets/none.pdf"].scores
    assert rows["tests/assets/none.pdf"].scores["error"] is True
    assert experiment.runs[0].scores["controls.expected_outcome"] == 2


def test_color_regions_runs_per_threshold(tmp_path: Path) -> None:
    rows = [
        {
            "case": "bands",
            "threshold": threshold,
            "expected": 2,
            "vector_hits": 2,
            "raster_hits": hits,
            "raster_extras": 1,
            "input_sha256": "x",
            "expected_boxes": [[0, 0, 1, 1]],
            "raster_regions": [],
            "vector_regions": [],
            "vector_ms": 1.0,
            "cold_render_ms": 2.0,
            "rgb_conversion_ms": 3.0,
            "segmentation_subprocess_ms": 4.0,
        }
        for threshold, hits in ((8, 2), (18, 0))
    ]
    report = {"dpi": 96, "connectivity": 4, "min_area_pixels": 300, "background_white": 248}
    _write(tmp_path / "color-regions.json", {**report, "rust_source_sha256": "r", "rows": rows})
    experiment = _one(list(local_studies.color_regions(tmp_path)), "exp/color-regions/controls")
    assert [run.name for run in experiment.runs] == ["native-paint-bounds", "raster-threshold-8", "raster-threshold-18"]
    assert _run(experiment, "raster-threshold-18").scores == {"hits": 0, "extras": 1, "expected": 2}


def test_campaign_manifest_is_single_aggregate_row(tmp_path: Path) -> None:
    manifest = {
        "created_utc": "2026-10-08T00:00:00+00:00",
        "head": "abc",
        "files": {"a": "b"},
        "validation": {"pytest_passed": 3, "ruff": "passed", "clippy": "failed", "strict_docs": ["en"]},
        "new_remote_spend_usd": 0,
    }
    _write(tmp_path / "campaign-manifest.json", manifest)
    experiment = _one(list(local_studies.campaign_manifest(tmp_path)), "exp/campaign-manifest/validation")
    scores = experiment.runs[0].rows[0].scores
    assert scores["pytest_passed"] == 3
    assert scores["ruff_passed"] is True
    assert scores["clippy_passed"] is False
    assert scores["strict_docs_locales"] == 1


def test_evidence_designs_keep_refused_pages(tmp_path: Path) -> None:
    directory = tmp_path / "evidence-designs" / "root-gate-v1"
    records = [
        {
            "id": f"page-00{i}",
            "arm": arm,
            "request": f"page-00{i}-{arm}.json",
            "sha256": "s",
            "bytes": 100 * (i + 1),
            "questions": 1,
            "source_admission_refusal": "axis_lines" if i == 1 else None,
            "source_sha256": "src",
            "page_index": i,
        }
        for arm in ("geometry", "blob")
        for i in range(2)
    ]
    _write(directory / "manifest.json", {"arms": ["geometry", "blob"], "records": records, "model": "M"})
    _write(directory / "scorer-only.json", {"page-000": "A", "page-001": "B"})
    experiment = _one(list(local_studies.evidence_designs(tmp_path)), "exp/evidence-designs/root-gate-v1")
    assert experiment.items[0].expected == {"gate_label": "A"}
    run = _run(experiment, "prepare/geometry")
    assert run.scores["source_admission_refused"] == 1
    assert run.scores["mean_request_bytes"] == 150
    assert run.rows[1].metadata["status"] == "refused-source"


def _gpu_run(boxes: dict[str, list[dict[str, Any]]], *, device: str = "cpu") -> dict[str, Any]:
    predictions = [{"id": key, "cohort": "silver-dev", "boxes": value} for key, value in boxes.items()]
    return {
        "device": device,
        "half": False,
        "configuration": {"quantize": "fp32", "device": device, "imgsz": 640},
        "cold_model_load_seconds": 0.1,
        "first_prediction_warmup_seconds": 1.0,
        "passes": [
            {"elapsed_seconds": s, "cpu_user_seconds": 1.0, "cpu_system_seconds": 0.0, "predictions": predictions}
            for s in (2.0, 1.0, 3.0)
        ],
        "peak_rss_kib": 2048,
        "peak_cuda_allocated_bytes": None if device == "cpu" else 2**20,
        "peak_cuda_reserved_bytes": None if device == "cpu" else 2**21,
    }


def test_gpu_comparison_presence_and_cpu_diff(tmp_path: Path) -> None:
    directory = tmp_path / "gpu-comparison"
    table = {"class": "Table", "confidence": 0.9, "xyxy": [0.0, 0.0, 10.0, 10.0]}
    shifted = {**table, "xyxy": [0.0, 0.0, 10.5, 10.0]}
    _write(
        directory / "labels.json", [{"id": i, "cohort": "silver-dev", "table_present": i == "p1"} for i in ("p1", "p2")]
    )
    _write(
        directory / "inputs.json",
        [{"id": i, "cohort": "silver-dev", "path": f"/x/{i}.png", "sha256": "h"} for i in ("p1", "p2")],
    )
    _write(directory / "cpu-fp32.json", _gpu_run({"p1": [table], "p2": []}))
    _write(directory / "gpu-fp32.json", _gpu_run({"p1": [shifted], "p2": []}, device="0"))
    summary = {"scores": {"cpu-fp32": {"silver-dev": {"tp": 1, "fn": 0, "fp": 0, "tn": 1}}}, "differences": {}}
    _write(directory / "summary.json", summary)
    experiment = _one(list(local_studies.gpu_comparison(tmp_path)), "exp/gpu-comparison/yolo-table-presence")
    cpu = _run(experiment, "cpu-fp32")
    assert cpu.scores["silver-dev.tp"] == 1
    assert cpu.scores["median_pass_seconds"] == 2.0
    assert cpu.metadata["report_crosscheck"] == "match summary.json"
    gpu = _run(experiment, "gpu-fp32")
    first = gpu.rows[0].scores
    assert first["topology_equal_vs_cpu"] is True
    assert first["within_tolerance_vs_cpu"] is False
    assert first["max_box_delta_px"] == pytest.approx(0.5)
    assert gpu.scores["bit_exact_pages"] == 1
    assert gpu.scores["peak_cuda_allocated_mib"] == 1.0


def _geometry_result(name: str, method: str, *, gold: bool, exact: bool, tables: int) -> dict[str, Any]:
    score: dict[str, Any] = {"gold_available": gold, "tables": tables}
    if gold:
        score |= {
            "expected_tables": 1,
            "exact": exact,
            "correct_cells": 4 if exact else 1,
            "total_cells": 4,
            "relationship_matches": 2,
            "relationship_expected": 4,
            "relationship_observed": 4,
        }
    return {
        "name": name,
        "method": method,
        "split": "development",
        "family": "solid",
        "sha256": "s",
        "output": {"tables": [], "markdown": "x", "route": "native-grid"},
        "median_ms": 1.0,
        "score": score,
        "source": {"missing_tokens": 1, "extra_tokens": 2},
        "records": {"correct": 0, "total": 0},
    }


def test_geometry_rounds_and_report_aggregation(tmp_path: Path) -> None:
    directory = tmp_path / "geometry"
    results = [
        _geometry_result("a", "native", gold=True, exact=True, tables=1),
        _geometry_result("b", "native", gold=False, exact=False, tables=0),
        {"name": "c", "method": "native", "split": "development", "family": "solid", "error": "boom"},
    ]
    _write(directory / "results.json", {"results": results})
    _write(directory / "round1-before-normalization.json", {"results": results[:1]})
    _write(directory / "a" / "labels.json", {"tables": [[["x"]]], "spans": [], "source": "s"})
    experiment = _one(list(local_studies.geometry(tmp_path)), "exp/geometry/cascade")
    assert [run.name for run in experiment.runs] == ["round1/native", "round3-final/native"]
    final = _run(experiment, "round3-final/native")
    assert final.metadata["superseded"] is False
    assert final.scores["development.exact_pages"] == 1
    assert final.scores["development.gold_pages"] == 1
    assert final.scores["development.missing_source_tokens"] == 2
    assert final.scores["errors"] == 1
    rows = {row.item_key: row for row in final.rows}
    assert "exact" not in rows["b"].scores
    assert rows["c"].metadata["status"] == "error"


def _header_case(name: str, *, abstain: bool) -> dict[str, Any]:
    outcome: dict[str, Any] = {
        "decision": {"header_rows": None if abstain else 1, "row_header_columns": 0, "reason": "r", "candidates": []},
        "edges": [],
        "tp": 0 if abstain else 2,
        "fp": 0,
        "fn": 2 if abstain else 0,
        "correct_band": not abstain,
        "by_kind": {"column": {"tp": 0 if abstain else 2, "fp": 0, "fn": 2 if abstain else 0}},
    }
    return {
        "name": name,
        "family": "simple",
        "gold_band": [1, 0],
        "gold_edges": 2,
        "table_count": 1,
        "exact_cells": True,
        "extraction_ms": 1.0,
        "methods": {"constraints": outcome},
    }


def test_headers_phases_and_encoding_audit(tmp_path: Path) -> None:
    directory = tmp_path / "headers"
    form = {"tables": 1, "pixel_sha256": "p", "input_sha256": "i"}
    audit = [{"scale": 0.8, "rotation": 0, "forms": [{**form, "coalesced": False}, {**form, "coalesced": True}]}]
    report = {"synthetic": [_header_case("a", abstain=False), _header_case("b", abstain=True)], "encoding_audit": audit}
    _write(directory / "decisions.json", report)
    _write(directory / "phase1.json", {"synthetic": [_header_case("a", abstain=True)]})
    (directory / "phase1-inputs").mkdir()
    (directory / "phase1-inputs" / "a.pdf").write_bytes(PDF)
    experiments = list(local_studies.headers(tmp_path))
    relations = _one(experiments, "exp/headers/relations")
    final = _run(relations, "final/constraints")
    assert final.scores["correct_bands"] == 1
    assert final.scores["abstained"] == 1
    assert final.scores["edge_precision"] == 1.0
    assert final.scores["edge_recall"] == 0.5
    assert final.rows[0].scores["column_tp"] == 2
    phase1 = _run(relations, "phase1/constraints")
    assert phase1.rows[0].input["pdf"]["bytes"] == len(PDF)
    encoding = _one(experiments, "exp/headers/rule-encoding")
    assert encoding.runs[0].scores == {"segmented_detected": 1, "coalesced_detected": 1, "pixels_equal": 1, "pairs": 1}


def test_matching_equivalence_and_empty_route(tmp_path: Path) -> None:
    base = {
        "saved_results_sha256": "s",
        "input_sha256": "i",
        "regions": 1,
        "error": None,
        "reference_ms": [4.0],
        "optimized_ms": [1.0],
        "reference_median_ms": 4.0,
        "optimized_median_ms": 1.0,
        "choices_equal": True,
        "html_equal": True,
        "saved_html_equal": True,
        "complete_html_equal": True,
        "peak_traced_bytes": 2048,
        "outputs": [{"matches": {}, "unassigned_ids": ["w1"]}],
    }
    results = [
        {**base, "name": "t", "route": "full", "word_count": 3, "cell_count": 2},
        {**base, "name": "t", "route": "cropped", "word_count": 0, "cell_count": 0, "outputs": []},
    ]
    report = {
        "code_sha256": "c",
        "repeats": 3,
        "chunk_words": 64,
        "provenance": {"rapid_table_version": "3", "numpy_version": "2"},
        "results": results,
    }
    _write(tmp_path / "matching" / "results.json", report)
    experiment = _one(list(local_specialist.matching(tmp_path)), "exp/matching/cell-matching")
    optimized = _run(experiment, "optimized-numpy-matcher")
    assert optimized.rows[0].scores["speedup"] == 4.0
    assert optimized.rows[0].scores["unassigned_ids"] == 1
    assert optimized.rows[1].metadata["status"] == "empty-route"
    assert "median_ms" not in optimized.rows[1].scores
    assert optimized.scores["equivalent_routes"] == 2


def _specialist_result(name: str, gold: Any, *, tables: int) -> dict[str, Any]:  # noqa: ANN401 - fixture gold.
    route = {
        "tables": [[["x"]]] * tables,
        "outputs": [],
        "complete_sha256": "c",
        "error": None,
        "inference_ms": 1.0,
        "matching_ms": 1.0,
        "region_count": tables,
        "source": {"source_tokens": 2, "matched_tokens": 2, "missing_tokens": 0, "extra_tokens": 0},
        "score": {"gold_available": gold is not None, "tables": tables}
        | ({"exact": True, "correct_cells": 1, "total_cells": 1} if gold else {}),
        "records": {"correct": 1, "total": 2} if gold is None else {"correct": 0, "total": 0},
        "total_ms": 3.0,
    }
    return {
        "name": name,
        "input_sha256": "i",
        "source": "s",
        "notes": "",
        "gold": gold,
        "word_count": 2,
        "dpi": 120,
        "render_ms": 1.0,
        "native_text_ms": 1.0,
        "routes": {"full": route, "cropped": route},
    }


def test_specialist_valid_and_invalid_runs(tmp_path: Path) -> None:
    results = [
        _specialist_result("table", [[["x"]]], tables=1),
        _specialist_result("prose", [], tables=1),
        _specialist_result("corpus", None, tables=1),
    ]
    for folder in ("specialist", "specialist-invalid-alpha-v1"):
        _write(tmp_path / folder / "manifest.json", {"metadata": {"providers": ["CPU"]}, "results": results})
    (tmp_path / "specialist-invalid-alpha-v1" / "INVALID-RUN.txt").write_text("INVALID: alpha", encoding="utf-8")
    experiments = list(local_specialist.specialist(tmp_path))
    valid = _one(experiments, "exp/specialist/slanet-plus-cpu-pilot")
    full = _run(valid, "slanet-plus-cpu/full")
    assert full.scores["exact_matrices"] == 1
    assert full.scores["prose_false_positives"] == 1
    assert full.scores["corpus_records_total"] == 2
    invalid = _one(experiments, "exp/specialist-invalid-alpha-v1/slanet-plus-cpu-pilot")
    assert invalid.labels["invalid_harness"] is True
    run = _run(invalid, "slanet-plus-cpu/full-INVALID-alpha")
    assert run.metadata["invalid_harness"] is True
    assert {row.metadata["status"] for row in run.rows} == {"invalid-harness"}


def test_specialist_resolution_sweep_and_agreement(tmp_path: Path) -> None:
    corpus_id = "corpus1"
    directory = tmp_path / "specialist-resolution-v1" / corpus_id
    pages = [
        {"id": page, "pdf_sha256": "p", "words": [{"id": "w0"}], "routes": {"page": [[0, 0, 1, 1]]}}
        for page in ("dev-000", "dev-001", "dev-002")
    ]
    _write(directory / "source-frozen.json", {"pages": pages})
    _write(directory / "model.json", {"model_sha256": "m"})
    output = {
        "id": "dev-000",
        "dpi": 72,
        "route": "page",
        "observed": {"region_count": 1, "inference_ms": 1000.0, "matching_ms": 500.0, "complete_sha256": "c"},
        "matrices": [{"values": [["a"]], "spans": []}],
        "ownership": {"unresolved_ids": []},
        "wall_seconds": 2.0,
        "cpu_seconds": 2.0,
        "model_cpu_seconds": 1.0,
        "matching_cpu_seconds": 0.5,
        "peak_rss_bytes": 2**20,
    }
    _write(directory / "outputs-frozen.json", {"rows": [output]})
    scores: dict[str, Any] = {"exact_page": True, "false_positive_page": False, "exact_cells": True}
    scores |= {"exact_spans": True, "owned_values": 1, "owned_words": 1}
    private = [
        {"id": "dev-000", "dpi": 72, "route": "page", "kind": "borderless", "scored": True, "error": False}
        | {"scores": scores, "source_conservation": True, "span_available": True},
        {"id": "dev-001", "dpi": 72, "route": "page", "kind": "ambiguous", "scored": False, "error": True}
        | {"scores": None, "source_conservation": None, "span_available": False},
    ]
    _write(directory / "private-scores.json", private)
    targets = [
        {"id": "dev-000", "kind": "borderless", "tables": [{"values": [["a"]], "row_count": 1, "col_count": 1}]},
        {"id": "dev-001", "kind": "ambiguous", "tables": []},
    ]
    _write(tmp_path / "silver-realism-v2" / corpus_id / "private-targets.json", targets)
    agreement = tmp_path / "specialist-resolution-v1" / "agreement-v1"
    cohort = {
        "config": "T005",
        "rule": "strict",
        "gate_simulated": False,
        "counts": {"accepted_correct_tables": 1},
        "rows": [{"id": "dev-000", "accepted": True, "scores": scores}],
    }
    _write(agreement / "private-evaluation.json", {"cohorts": [cohort]})
    frozen = {"id": "dev-001", "config": "T005", "rule": "strict", "accepted": True, "agreeing_candidates": 1}
    _write(agreement / "agreement-frozen.json", {"rows": [frozen]})
    experiments = list(local_specialist.specialist_resolution(tmp_path))
    sweep = _one(experiments, f"exp/specialist-resolution-v1/{corpus_id}/sweep")
    assert sweep.items[0].expected["kind"] == "borderless"
    run = _run(sweep, "slanet-plus-cpu/dpi72/page")
    assert run.scores["borderless_exact"] == 1
    assert run.scores["owned_values_total"] == 1
    assert run.scores["ambiguous_unscored"] == 1
    assert run.scores["errors"] == 1
    assert run.scores["model_wall_seconds"] == 1.0
    assert run.rows[1].metadata["status"] == "error"
    assert "exact_page" not in run.rows[1].scores
    assert [r.name for r in sweep.runs].count("slanet-plus-cpu/dpi180/crop-pad12") == 1
    result = _one(experiments, "exp/specialist-resolution-v1/agreement-v1")
    rows = {row.item_key: row for row in result.runs[0].rows}
    assert rows["dev-000"].scores["accepted"] is True
    assert rows["dev-001"].metadata["status"] == "ambiguous-unscored"
    assert rows["dev-001"].output == {"accepted": True, "agreeing_candidates": 1}
    assert rows["dev-002"].scores == {}
    assert result.runs[0].scores == {"accepted_correct_tables": 1}
