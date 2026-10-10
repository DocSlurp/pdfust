"""Frozen report audits count failures and reject incomplete retained outputs."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_report as module
from bench.generalization_report import (
    _bounds,
    _costs,
    _evaluate,
    _failure_taxonomy,
    _model_breakdown,
    _posthoc_density,
    _ratio,
    load_corpus,
    markdown_report,
    score_run,
    verify_code,
    verify_output,
)
from bench.pipeline_assembly import native_state
from bench.pipeline_regions import compose, split, unresolved_region
from bench.pipeline_report import _render_markdown
from bench.pipeline_vision_transcription import markdown as vision_markdown
from bench.pipeline_vision_transcription import parse as vision_parse
from bench.silver import canonical, sha


def write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


@pytest.fixture
def fixture(tmp_path: Path) -> dict[str, Any]:
    corpus, run = tmp_path / "corpus", tmp_path / "run"
    corpus.mkdir()
    (run / "code").mkdir(parents=True)
    pdf = corpus / "input.pdf"
    pdf.write_bytes(b"frozen pdf bytes; evaluator hashes but never interprets")
    pages = [
        {
            "id": ident,
            "cohort": cohort,
            "family": cohort + "/test",
            "pilot": True,
            "pdf_path": str(pdf),
            "pdf_sha256": sha(pdf.read_bytes()),
            "page_number": 0,
        }
        for ident, cohort in [("positive", "authored"), ("negative", "omni"), ("diagnostic", "native")]
    ]
    table = {"row_count": 1, "col_count": 1, "values": [["A"]], "spans": []}
    targets = {
        "schema": 1,
        "pages": [
            {"id": "positive", "tables": [table], "structural_scored": True},
            {"id": "negative", "tables": [], "structural_scored": True},
            {"id": "diagnostic", "structural_scored": False},
        ],
    }
    identity = sha(
        canonical(
            {
                "schema": 1,
                "pages": [{k: v for k, v in p.items() if k != "pdf_path"} for p in pages],
                "targets": targets["pages"],
            }
        )
    )
    manifest = {"schema": 1, "split": "DEV", "dataset_sha256": identity, "pages": pages}
    targets["dataset_sha256"] = identity
    write(corpus / "manifest.json", manifest)
    write(corpus / "private-targets.json", targets)
    config = {"pilot": False, "processor": "whole", "policy": "native"}
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "w0", "text": "hello", "bbox": [0, 0, 20, 10], "line": [0, 0]},
        ],
        "vector_candidates": [],
    }
    state = native_state(source)
    prediction = {
        "id": "negative",
        "status": "ok",
        "source": source,
        "tables": [],
        "unresolved_ids": ["w0"],
        "calls": [],
    }
    write(run / "negative-result.json", prediction)
    write(run / "negative-structure.json", state)
    (run / "negative.md").write_text(_render_markdown(source, state))
    local = Path(__file__).parents[1] / "bench"
    hashes = {}
    for name in ("pipeline_run.py", "pipeline_assembly.py"):
        data = (local / name).read_bytes()
        hashes[name] = sha(data)
        (run / "code" / name).write_bytes(data)
    frozen = {
        "config": config,
        "manifest_sha256": sha((corpus / "manifest.json").read_bytes()),
        "code_sha256": hashes,
        "records": [{k: p[k] for k in ("id", "pdf_path", "pdf_sha256", "page_number")} for p in pages],
    }
    report = {
        "config": config,
        "results": [prediction],
        "metrics": {"wall_seconds": 2, "cpu_seconds": 1, "peak_sampled_rss_bytes": 1000},
        "calls": 0,
        "ledger_attempts": 0,
        "accounted_usd": 0,
        "effective_usd": 0,
        "provider_reported_usd": 0,
        "missing_provider_charge_count": 0,
        "cost_bases": {},
    }
    write(run / "frozen.json", frozen)
    write(run / "report.json", report)
    return {
        "corpus": corpus,
        "run": run,
        "manifest": manifest,
        "targets": targets,
        "prediction": prediction,
        "frozen": frozen,
        "report": report,
    }


def test_complete_manifest_errors_groups_and_free_costs(fixture: dict[str, Any]) -> None:
    f = fixture
    manifest, targets = load_corpus(f["corpus"])
    report = score_run(f["run"], f["corpus"] / "manifest.json", manifest, targets)
    assert report["intended_pages"] == 3
    assert report["operational_pages"] == 1
    assert report["all_errors"] == 2
    assert report["statuses"] == {"ok": 1, "missing": 2}
    assert report["groups"]["cohort"]["authored"]["expected_tables"] == 1
    assert report["groups"]["cohort"]["native"]["diagnostic_pages"] == 1
    assert report["authored_legacy_exact"]["cell_slots"] == 1
    assert report["pages_per_minute"] == 30
    assert report["pages_per_dollar"] is None
    markdown = markdown_report([report])
    assert "native/test" in markdown
    assert "all ledger attempts" in markdown
    assert "unmeasured" in markdown


def test_corpus_hash_detects_pdf_and_reference_changes(fixture: dict[str, Any]) -> None:
    f = fixture
    altered = deepcopy(f["targets"])
    altered["pages"][0]["tables"][0]["values"] = [["changed"]]
    write(f["corpus"] / "private-targets.json", altered)
    with pytest.raises(ValueError, match="identity"):
        load_corpus(f["corpus"])
    write(f["corpus"] / "private-targets.json", f["targets"])
    (f["corpus"] / "input.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source PDF"):
        load_corpus(f["corpus"])


def test_outcome_selected_frozen_subset_rejected(fixture: dict[str, Any]) -> None:
    f = fixture
    frozen = deepcopy(f["frozen"])
    frozen["records"] = frozen["records"][1:2]
    write(f["run"] / "frozen.json", frozen)
    with pytest.raises(ValueError, match="complete intended"):
        score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])


def test_archived_python_is_hashed_and_never_executed(fixture: dict[str, Any]) -> None:
    f = fixture
    (f["run"] / "code" / "pipeline_run.py").write_text("raise RuntimeError('must never execute')")
    with pytest.raises(ValueError, match="Archived code"):
        verify_code(f["run"], f["frozen"], processor="whole")


def test_markdown_and_result_tampering_rejected(fixture: dict[str, Any]) -> None:
    f = fixture
    (f["run"] / "negative.md").write_text("unowned invented prose")
    with pytest.raises(ValueError, match="Markdown"):
        verify_output(f["run"], f["prediction"], processor="whole")
    altered = deepcopy(f["prediction"])
    altered["status"] = "error"
    write(f["run"] / "negative-result.json", altered)
    with pytest.raises(ValueError, match="retained result"):
        verify_output(f["run"], f["prediction"], processor="whole")


def test_region_recomposition_and_exact_markdown(tmp_path: Path) -> None:
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "w0", "text": "A", "bbox": [10, 10, 20, 20]},
            {"id": "w1", "text": "B", "bbox": [10, 70, 20, 80]},
        ],
        "vector_candidates": [],
    }
    plan = split(source)
    states = {r["id"]: unresolved_region(r) for r in plan["regions"]}
    state = compose(plan, states)
    _bounds(source, state)
    prediction = {
        "id": "regions",
        "status": "ok",
        "source": source,
        "tables": state["tables"],
        "unresolved_ids": state["unresolved_ids"],
        "region_plan": {k: v for k, v in plan.items() if k != "words"},
        "regions": [{"id": r["id"], "state": states[r["id"]]} for r in plan["regions"]],
    }
    write(tmp_path / "regions-result.json", prediction)
    write(tmp_path / "regions-structure.json", state)
    (tmp_path / "regions.md").write_text(
        "\n".join(_render_markdown(r["source"], states[r["id"]]) for r in plan["regions"])
    )
    assert verify_output(tmp_path, prediction, processor="regions")["conserved"]
    altered = deepcopy(prediction)
    altered["regions"][0]["state"]["unresolved_ids"] = []
    write(tmp_path / "regions-result.json", altered)
    with pytest.raises(ValueError, match=r"source|ownership|conservation"):
        verify_output(tmp_path, altered, processor="regions")


def test_reservations_unknown_and_zero_charges_do_not_become_totals() -> None:
    report = {
        "ledger_attempts": 3,
        "calls": 1,
        "provider_reported_usd": 0,
        "accounted_usd": 1,
        "effective_usd": 1,
        "cost_bases": {"reserved": 1, "catalog_estimate": 2},
    }
    cost = _costs(report)
    assert cost["effective_usd"] is None
    assert cost["provider_reported_subtotal_usd"] == 0
    assert cost["reservation_usd"] is None
    assert cost["estimated_usd"] is None
    report["cost_bases"] = {"unknown": 1}
    assert _costs(report)["effective_usd"] is None
    assert _ratio(1, 0) is None
    assert _ratio(1, None) is None


def test_gold_field_in_retained_request_rejected(fixture: dict[str, Any]) -> None:
    f = fixture
    report = deepcopy(f["report"])
    prediction = report["results"][0]
    prediction["calls"] = [{"entry": {}}]
    write(f["run"] / "report.json", report)
    write(f["run"] / "negative-result.json", prediction)
    write(f["run"] / "negative-request-0.json", {"payload": {"gold_tables": []}})
    with pytest.raises(ValueError, match="reference fields"):
        score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])


def test_natural_unit_spans_canonicalize_and_localization_is_separate() -> None:
    table = {"row_count": 1, "col_count": 2, "values": [["A", "B"]], "spans": [], "bbox": [0, 0, 100, 10]}
    prediction = deepcopy(table)
    prediction["spans"] = [{"row": 0, "column": c, "row_span": 1, "column_span": 1} for c in range(2)]
    result = _evaluate([{"id": "natural", "tables": [table]}], [{"id": "natural", "tables": [prediction]}])
    assert result["totals"]["exact_page"] == 1
    assert result["totals"]["localized_tables_iou_ge_0_5"] == 1
    prediction["bbox"] = [0, 0, 20, 10]
    result = _evaluate([{"id": "natural", "tables": [table]}], [{"id": "natural", "tables": [prediction]}])
    assert result["totals"]["geometry_matches"] == 1
    assert result["totals"]["localized_tables_iou_ge_0_5"] == 0


def test_failed_request_body_is_audited_without_successful_call(fixture: dict[str, Any]) -> None:
    f = fixture
    write(f["run"] / "positive-request-0.json", {"annotation_html": "private reference"})
    with pytest.raises(ValueError, match="reference fields"):
        score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])


def test_reviewed_history_allows_runner_changes_but_requires_validator_ast(
    fixture: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    f = fixture
    frozen = deepcopy(f["frozen"])
    local_region = Path(module.__file__).with_name("pipeline_regions.py").read_bytes()
    historical_region = local_region + b"\n# Reviewed historical proposal-only difference.\n"
    historical_runner = b"def process():\n    return 'reviewed historical runner'\n"
    for name, data in [("pipeline_regions.py", historical_region), ("generalization_run.py", historical_runner)]:
        (f["run"] / "code" / name).write_bytes(data)
        frozen["code_sha256"][name] = sha(data)
    with pytest.raises(ValueError, match="unreviewed"):
        verify_code(f["run"], frozen, processor="regions")
    monkeypatch.setattr(
        module,
        "TRUSTED_HISTORICAL_CODE",
        {
            "pipeline_regions.py": {sha(historical_region): "reviewed-region"},
            "generalization_run.py": {sha(historical_runner): "reviewed-runner"},
        },
    )
    verified = verify_code(f["run"], frozen, processor="regions")
    assert verified["region_validator_ast_compatible"]
    assert verified["trusted_historical_commits"]["generalization_run.py"] == "reviewed-runner"
    altered = historical_region.replace(b"MAX_PAGE_WORDS = 65_536", b"MAX_PAGE_WORDS = 65_535")
    (f["run"] / "code" / "pipeline_regions.py").write_bytes(altered)
    frozen["code_sha256"]["pipeline_regions.py"] = sha(altered)
    module.TRUSTED_HISTORICAL_CODE["pipeline_regions.py"][sha(altered)] = "reviewed-but-incompatible"
    with pytest.raises(ValueError, match="AST"):
        verify_code(f["run"], frozen, processor="regions")


def test_actual_models_and_cache_presence_do_not_follow_default_config() -> None:
    returned = [
        {
            "entry": {"requested_model": "sonnet", "provider_reported_usd": 0.1, "accounted_usd": 0.1},
            "usage": {"input_tokens": 100, "cache_read_input_tokens": 20},
        },
        {
            "entry": {"requested_model": "sonnet", "provider_reported_usd": 0, "accounted_usd": 0.01},
            "usage": {"input_tokens": 50, "cache_read_input_tokens": 0},
        },
        {"entry": {"requested_model": "sonnet"}, "usage": {}},
    ]
    predictions = [{"id": "p", "calls": returned}]
    audits = [{"path": f"p-request-{i}.json", "model": "sonnet"} for i in range(4)]
    breakdown = _model_breakdown(predictions, audits)
    model = breakdown["models"]["sonnet"]
    assert model["retained_request_bodies"] == 4
    assert model["returned_calls"] == 3
    cache = model["usage"]["cache_read_input_tokens"]
    assert cache["reported_positive"] == 1
    assert cache["reported_zero"] == 1
    assert cache["missing_or_invalid"] == 1
    assert cache["known_subtotal"] == 20
    assert cache["complete_total"] is None
    assert model["usage"]["cache_creation_input_tokens"]["missing_or_invalid"] == 3
    assert model["returned_provider_reported_usd"]["known_subtotal"] == 0.1
    assert model["returned_provider_reported_usd"]["complete_total"] is None


def test_progress_groups_reject_mixed_dataset_identities(fixture: dict[str, Any]) -> None:
    f = fixture
    report = score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])
    other = deepcopy(report)
    other["dataset_sha256"] = "different frozen dataset"
    with pytest.raises(ValueError, match="different frozen datasets"):
        module.protocol_report({"one protocol": [report, other]})
    text = module.protocol_report({"protocol A": [report], "protocol B": [other]}, pending=["pending run"])
    assert "## protocol A" in text
    assert "## protocol B" in text
    assert "pending run" in text
    assert "Exact positive pages" in text


def vision_prediction(directory: Path) -> dict[str, Any]:
    response = {"choices": [{"finish_reason": "stop", "message": {"content": '{"answers":{"q0":{"tables":[]}}}'}}]}
    viewport = [0, 0, 100, 100]
    state = vision_parse(response, viewport)
    prediction = {
        "id": "negative",
        "status": "ok",
        "route": "vision_transcription",
        "source_conserved": False,
        "viewport": viewport,
        "transcription_response": response,
        "tables": state["tables"],
        "unresolved_ids": [],
        "calls": [],
    }
    write(directory / "negative-result.json", prediction)
    write(directory / "negative-structure.json", state)
    (directory / "negative.md").write_text(vision_markdown(state))
    return prediction


def test_vision_output_is_operational_without_claiming_source_conservation(tmp_path: Path) -> None:
    prediction = vision_prediction(tmp_path)
    assert verify_output(tmp_path, prediction, processor="vision") == {"operational": True, "conserved": False}


@pytest.mark.parametrize("field", ["tables", "structure", "markdown", "raw", "source", "source_conserved", "route"])
def test_vision_reparse_rejects_tampered_output(tmp_path: Path, field: str) -> None:
    prediction = vision_prediction(tmp_path)
    if field == "tables":
        prediction["tables"] = [{"unexpected": "table"}]
    elif field == "structure":
        write(tmp_path / "negative-structure.json", {"tables": []})
    elif field == "markdown":
        (tmp_path / "negative.md").write_text("invented prose")
    elif field == "raw":
        prediction["transcription_response"]["choices"][0]["finish_reason"] = "content_filter"
    elif field == "source":
        prediction["source"] = {"words": []}
    elif field == "source_conserved":
        prediction[field] = True
    else:
        prediction[field] = "source_assembly"
    write(tmp_path / "negative-result.json", prediction)
    with pytest.raises(ValueError, match=r"transcription|Markdown|truncated|finish"):
        verify_output(tmp_path, prediction, processor="vision")


def test_vision_frozen_code_and_score_keep_all_targets_and_zero_conserved_pages(
    fixture: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    f = fixture
    local = Path(module.__file__).parent
    trusted = tmp_path / "trusted"
    trusted.mkdir()
    hashes = {}
    for name in ("pipeline_vision_transcription.py", "pipeline_frontier.py", "generalization_vision_run.py"):
        data = (
            (local / name).read_bytes() if name != "generalization_vision_run.py" else b"# Trusted local test runner.\n"
        )
        (trusted / name).write_bytes(data)
        (f["run"] / "code" / name).write_bytes(data)
        hashes[name] = sha(data)
    monkeypatch.setattr(module, "__file__", str(trusted / "generalization_report.py"))
    frozen = deepcopy(f["frozen"])
    frozen["config"]["processor"] = "vision"
    frozen["code_sha256"] = hashes
    report = deepcopy(f["report"])
    report["config"] = frozen["config"]
    report["results"] = [vision_prediction(f["run"])]
    write(f["run"] / "frozen.json", frozen)
    write(f["run"] / "report.json", report)
    result = score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])
    assert result["operational_pages"] == 1
    assert result["conserved_pages"] == 0
    assert result["intended_pages"] == 3
    assert result["all_errors"] == 2
    assert result["positive"]["expected_tables"] == 1
    assert result["positive"]["missing_tables"] == 1
    assert result["text_provenance"] == "model-transcribed"
    assert "table-only" in result["output_scope"]
    assert "table-only" in markdown_report([result])
    assert "source-conserved pages: 0/3" in module.protocol_report({"vision comparator": [result]})
    assert result["authored_legacy_exact"]["cell_slots"] == 1
    changed = b"# Unreviewed archive adapter.\n"
    (f["run"] / "code" / "pipeline_vision_transcription.py").write_bytes(changed)
    frozen["code_sha256"]["pipeline_vision_transcription.py"] = sha(changed)
    with pytest.raises(ValueError, match="differs from frozen"):
        verify_code(f["run"], frozen, processor="vision")


@pytest.mark.parametrize(
    ("finish", "error", "category"),
    [
        ("content_filter", "Response was truncated or has no normal finish", "provider_content_filter"),
        ("length", "Response was truncated or has no normal finish", "provider_output_length"),
        ("stop", "Invalid anchor cell collection", "invalid_anchor_collection"),
        ("stop", "Unknown source ID", "invalid_source_ids"),
        ("stop", "Overlapping merged spans", "invalid_table_topology"),
        (None, "Response was truncated or has no normal finish", "unclassified_completion_failure"),
        (None, "No extracted or recognized source text", "missing_source_text"),
    ],
)
def test_failure_categories_use_retained_responses_not_generic_error_messages(
    tmp_path: Path,
    finish: str | None,
    error: str,
    category: str,
) -> None:
    directory = tmp_path / "artifacts" / "pipeline-p002" / "run"
    responses = directory.parent.parent / "decisions"
    raw = {"choices": [{"finish_reason": finish, "message": {"content": None}}]}
    write(responses / "response-1.json", raw)
    prediction = {
        "id": "p",
        "status": "error",
        "error": error,
        "calls": [{"entry": {"response_file": "response-1.json"}}],
    }
    taxonomy = _failure_taxonomy(directory, [prediction])
    assert taxonomy["counts"] == {category: 1}
    observation = taxonomy["pages"][0]["response_observations"][0]
    assert observation["finish_reason"] == finish
    assert observation["sha256"] == sha((responses / "response-1.json").read_bytes())
    assert "payload" not in observation
    assert "content" not in observation


def test_failure_response_filename_may_not_escape_retained_directory(tmp_path: Path) -> None:
    prediction = {"id": "p", "status": "error", "calls": [{"entry": {"response_file": "../other.json"}}]}
    with pytest.raises(ValueError, match="Unsafe retained API"):
        _failure_taxonomy(tmp_path, [prediction])


def test_posthoc_density_preserves_all_targets_and_positive_denominators() -> None:
    dense = ["p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"]
    ids = dense + [f"p{i}" for i in range(14)]
    table = {"row_count": 1, "col_count": 1, "values": [["A"]], "spans": []}
    targets = [{"id": ident, "tables": [table] if index < 12 else []} for index, ident in enumerate(ids)]
    predictions = [{"id": ident, "tables": t["tables"]} for ident, t in zip(ids, targets, strict=True)]
    result = _posthoc_density([{"id": i} for i in ids], targets, predictions)
    assert result is not None
    groups = result["groups"]
    assert groups["two_dense_newspapers"]["pages"] == 2
    assert groups["remaining_fourteen"]["pages"] == 14
    assert groups["remaining_fourteen"]["positive_page"] == 10
    assert groups["remaining_fourteen"]["exact_positive_page"] == 10
    assert groups["remaining_fourteen"]["exact_page"] == 14
    assert sum(g["expected_tables"] for g in groups.values()) == 12
    assert _posthoc_density([{"id": "other"}], targets, predictions) is None


def test_progress_keeps_separate_detector_worker_cpu_and_rss_scope(fixture: dict[str, Any]) -> None:
    f = fixture
    raw = deepcopy(f["report"])
    raw["layout_detector_initialization"] = {"initialization": {"wall_seconds": 2, "cpu_seconds": 4}}
    raw["results"][0]["layout_detector"] = {"metrics": {"cpu_seconds": 3, "peak_sampled_rss_bytes": 2000}}
    write(f["run"] / "report.json", raw)
    write(f["run"] / "negative-result.json", raw["results"][0])
    result = score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])
    text = module.protocol_report({"CPU detector treatment": [result]})
    assert "Separate CPU detector worker" in text
    assert "request CPU total 3s" in text
    assert "2000 bytes" in text
    assert "parent CPU/RSS excludes this worker" in text
    assert "RSS peaks are not summed" in text
