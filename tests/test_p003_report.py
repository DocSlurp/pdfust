"""Independent P003 metric, accounting and paired-evaluation contracts."""

# Lazy imports keep repair-only dependencies scoped to replay tests.
# ruff: noqa: PLC0415, SLF001

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.p003_report import costs, paired_comparison, repeat_summary, strict_scores, verify_archive
from bench.silver import sha


def table(values: list[list[str | None]], spans: list[dict[str, int]] | None = None) -> dict[str, Any]:
    return {"row_count": len(values), "col_count": len(values[0]), "values": values, "spans": spans or []}


def test_strict_cells_require_anchor_span() -> None:
    gold = table([["A", None], ["B", "C"]], [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}])
    prediction = table([["A", ""], ["B", "C"]])
    result = strict_scores([{"id": "p", "tables": [gold]}], [{"id": "p", "status": "ok", "tables": [prediction]}])
    assert result["totals"]["correct_text_cells"] == 3
    assert result["totals"]["strict_exact_cells"] == 2
    assert result["totals"]["complete_tables"] == 0


def test_missing_errors_and_negative_false_positives_remain_scored() -> None:
    targets = [{"id": "positive", "tables": [table([["A"]])]}, {"id": "negative", "tables": []}]
    result = strict_scores(targets, [{"id": "negative", "status": "ok", "tables": [table([["invented"]])]}])
    assert result["totals"]["expected_cells"] == 1
    assert result["totals"]["all_page_errors"] == 1
    assert result["totals"]["false_positive_page"] == 1
    assert result["totals"]["strict_exact_cells"] == 0
    assert result["positive_macro"]["strict_exact_cell_recall"] == 0


@pytest.mark.parametrize("bases", [{"reserved": 1}, {"unknown": 1}])
def test_incomplete_cost_cannot_become_total(bases: dict[str, int]) -> None:
    result = costs(
        {"effective_usd": 1, "accounted_usd": 2, "provider_reported_usd": 0, "ledger_attempts": 1, "cost_bases": bases}
    )
    assert result["effective_api_usd"] is None
    assert result["provider_reported_subtotal_usd"] == 0
    assert result["accounted_usd_including_reservations"] == 2


def test_reported_zero_and_estimate_remain_distinct() -> None:
    result = costs(
        {"effective_usd": 0.1, "provider_reported_usd": 0, "ledger_attempts": 1, "cost_bases": {"catalog estimate": 1}}
    )
    assert result["effective_api_usd"] == 0.1
    assert result["provider_reported_subtotal_usd"] == 0


def test_archive_cannot_authenticate_its_own_digest(tmp_path: Path) -> None:
    code = tmp_path / "code"
    code.mkdir()
    (code / "unknown.py").write_bytes(b"# unreviewed\n")
    digest = sha((code / "unknown.py").read_bytes())
    frozen = {"code_sha256": {"unknown.py": digest}}
    with pytest.raises(ValueError, match="Untrusted"):
        verify_archive(tmp_path, frozen)
    assert verify_archive(tmp_path, frozen, {"unknown.py": digest}) == frozen["code_sha256"]
    (code / "unknown.py").write_bytes(b"# altered\n")
    with pytest.raises(ValueError, match="changed"):
        verify_archive(tmp_path, frozen, {"unknown.py": digest})


def matched_run(name: str, values: list[int]) -> dict[str, Any]:
    return {
        "name": name,
        "dataset_sha256": "dataset",
        "manifest_sha256": "manifest",
        "cohort": "omnidoc",
        "source_fingerprint": "same",
        "detector_evidence_fingerprint": "same",
        "source_inventory_pages": 2,
        "intended_pages": 2,
        "page_scores": [{"id": str(i), "strict_exact_cells": v, "complete_tables": 0} for i, v in enumerate(values)],
    }


def test_paired_bootstrap_keeps_page_deltas_and_rejects_source_changes() -> None:
    left, right = matched_run("a", [1, 2]), matched_run("b", [3, 1])
    result = paired_comparison(left, right, samples=100)
    assert result["strict_exact_cell_delta"] == 1
    assert result["paired_page_bootstrap_95_interval"] == [-2, 4]
    assert result == paired_comparison(left, right, samples=100)
    changed = deepcopy(right)
    changed["source_fingerprint"] = "different"
    with pytest.raises(ValueError, match="source_fingerprint"):
        paired_comparison(left, changed)
    changed = deepcopy(right)
    changed["source_inventory_pages"] = 1
    with pytest.raises(ValueError, match="complete retained"):
        paired_comparison(left, changed)


def test_repeat_summary_keeps_worst_and_best_without_selection() -> None:
    runs = [matched_run("r1", [1, 2]), matched_run("r2", [3, 1]), matched_run("r3", [0, 0])]
    for run in runs:
        run["config"] = {"model": "fixed"}
        run["scores"] = {"strict_exact_cells": sum(p["strict_exact_cells"] for p in run["page_scores"])}
    summary = repeat_summary(runs)
    assert summary["metrics"]["strict_exact_cells"]["observations"] == [3, 4, 0]
    assert summary["metrics"]["strict_exact_cells"]["median"] == 3
    assert summary["metrics"]["strict_exact_cells"]["minimum"] == 0
    runs[2]["config"] = {"model": "changed"}
    with pytest.raises(ValueError, match="identical treatment"):
        repeat_summary(runs)


def test_repeat_administration_and_defaults_do_not_change_treatment() -> None:
    left, right = matched_run("r0", [1, 2]), matched_run("r1", [2, 3])
    left["config"] = {"run_id": "r0", "repeat_index": 0, "order_seed": 1, "model": "gate", "image_edge": 512}
    right["config"] = {
        "run_id": "r1",
        "repeat_index": 1,
        "order_seed": 2,
        "model": "gate",
        "image_edge": 512,
        "gate_image": True,
        "source_order": "legacy",
    }
    for run in (left, right):
        run["scores"] = {"strict_exact_cells": sum(p["strict_exact_cells"] for p in run["page_scores"])}
    assert repeat_summary([left, right])["administrative_fields"][1]["order_seed"] == 2
    for field, value in (("model", "different_gate"), ("image_edge", 1024), ("gate_image", False)):
        changed = deepcopy(right)
        changed["config"][field] = value
        with pytest.raises(ValueError, match="identical treatment"):
            repeat_summary([left, changed])
    right["code_sha256"] = {"helper.py": "new"}
    with pytest.raises(ValueError, match="operator semantic review"):
        repeat_summary([left, right])
    assert repeat_summary([left, right], reviewed_code_changes=True)["operator_reviewed_code_changes"]


def test_paired_image_changes_are_explicit() -> None:
    left, right = matched_run("a", [1, 2]), matched_run("b", [2, 3])
    left["config"] = {"gate_image": True}
    right["config"] = {"gate_image": False}
    left["request_image_inventory"] = [{"data_url_sha256": ["image"]}]
    right["request_image_inventory"] = []
    result = paired_comparison(left, right, samples=10)
    assert result["gate_image_configuration_equal"] is False
    assert result["request_image_hash_sets_equal"] is False
    assert result["treatment_changes"]["gate_image"] == [True, False]


def incremental_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any]]:
    """Keep renderer semantics stubbed while exercising authenticated repair replay."""
    from bench import generalization_report
    from bench.decision_p003_native import apply_decision_batches, decision_batches
    from bench.decision_p003_offline import synthetic
    from bench.silver import write_json

    monkeypatch.setattr(generalization_report, "verify_output", lambda *_args, **_kwargs: {"operational": True})
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "code").mkdir()
    (baseline / "code" / "fixture.py").write_bytes(b"# independently trusted test source\n")
    baseline_config = {"processor": "regions", "source_order": "original"}
    records = [{"id": "p", "pdf_path": "/source.pdf", "pdf_sha256": "pdf", "page_number": 0}]
    page, state = synthetic(3)
    region = {"id": "r", "source": page, "state": state}
    original = {
        "id": "p",
        "status": "ok",
        "source": page,
        "region_plan": {"regions": [{"id": "r", "source": page}]},
        "regions": [region],
        "tables": state["tables"],
        "unresolved_ids": [],
        "source_conserved": True,
        "calls": [],
        "wall_seconds": 10,
        "cpu_seconds": 20,
    }
    original_report = {
        "config": baseline_config,
        "results": [original],
        "metrics": {"wall_seconds": 10},
        "ledger_attempts": 0,
        "effective_usd": 0,
        "cost_bases": {},
    }
    original_frozen = {
        "config": baseline_config,
        "records": records,
        "manifest_sha256": "manifest",
        "code_sha256": {"fixture.py": sha((baseline / "code" / "fixture.py").read_bytes())},
    }
    write_json(baseline / "report.json", original_report)
    write_json(baseline / "frozen.json", original_frozen)
    write_json(baseline / "p-result.json", original)
    write_json(baseline / "p-structure.json", state)
    (baseline / "p.md").write_text("baseline output\n")
    hashes = {
        name: sha((baseline / name).read_bytes())
        for name in ("report.json", "frozen.json", "p-result.json", "p-structure.json", "p.md")
    }
    hashes["code/fixture.py"] = sha((baseline / "code/fixture.py").read_bytes())
    menu, bodies = decision_batches(page, state, "typesafe/jev-1.13")
    responses = [
        {
            "answers": {
                ident: {
                    "type": "choice",
                    "choice": "join",
                    "probabilities": {"join": 0.9, "split": 0.1, "unresolved": 0},
                    "confidence": 0.1,
                }
                for ident in body["questions"]
            }
        }
        for body in bodies
    ]
    updated, audit = apply_decision_batches(page, state, menu, bodies, responses)
    write_json(tmp_path / "p-r-boundary-menu.json", menu)
    calls = []
    for index, (body, response) in enumerate(zip(bodies, responses, strict=True)):
        write_json(tmp_path / f"p-r-boundary-{index}-request.json", body)
        write_json(tmp_path / f"p-r-boundary-{index}-response.json", {"entry": {"id": index}, "result": response})
        calls.append({"entry": {"id": index}, "region_id": "r", "batch_index": index, "replayed": False})
    write_json(tmp_path / "p-r-updated-state.json", updated)
    prediction = {
        **deepcopy(original),
        "tables": updated["tables"],
        "regions": [{**region, "state": updated}],
        "repair_status": "completed",
        "repair_calls": calls,
        "repair_errors": [],
        "baseline_provenance": {
            "result_sha256": hashes["p-result.json"],
            "status": "ok",
            "calls": [],
            "source_order": "original",
            "wall_seconds": 10,
            "cpu_seconds": 20,
        },
        "repair_regions": [
            {"id": "r", "original_state": state, "repair_status": "completed", "updated_state": updated, "audit": audit}
        ],
    }
    module_root = Path(__file__).resolve().parents[1] / "bench"
    frozen = {
        "config": {
            "model": "typesafe/jev-1.13",
            "baseline_source_order": "original",
            "minimum_join": 0.8,
            "minimum_margin": 0.25,
        },
        "records": records,
        "manifest_sha256": "manifest",
        "code_sha256": {
            name: sha((module_root / name).read_bytes())
            for name in ("decision_p003_boundaries.py", "decision_p003_native.py")
        },
        "baseline": {
            "copied_directory": "baseline",
            "original_config": baseline_config,
            "source_order": "original",
            "file_sha256": hashes,
        },
    }
    report = {"baseline_report": original_report, "results": [prediction]}
    return report, frozen


def test_incremental_replay_uses_responses_and_rejects_invented_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bench.p003_report import verify_incremental_run

    report, frozen = incremental_fixture(tmp_path, monkeypatch)
    trusted = {"fixture.py": sha((tmp_path / "baseline/code/fixture.py").read_bytes())}
    summary, verified = verify_incremental_run(tmp_path, report, frozen, trusted)
    assert verified["p"]["operational"]
    assert summary["resources"]["wall_seconds"] == 10
    altered = deepcopy(report)
    altered["results"][0]["repair_regions"][0]["updated_state"]["tables"][0]["values"][0][0] = "invented"
    with pytest.raises(ValueError, match="independently decoded"):
        verify_incremental_run(tmp_path, altered, frozen, trusted)
    (tmp_path / "baseline/p.md").write_text("changed baseline\n")
    with pytest.raises(ValueError, match="baseline bytes changed"):
        verify_incremental_run(tmp_path, report, frozen, trusted)


def test_complete_incremental_runner_replays_renderer_and_copied_requests(tmp_path: Path) -> None:
    from bench import p003_boundary_run
    from bench.p003_report import verify_incremental_run
    from bench.silver import write_json
    from test_p003_boundary_run import MockClient, baseline, configuration

    original_directory = tmp_path / "original"
    baseline(original_directory)
    import json

    original_frozen = json.loads((original_directory / "frozen.json").read_bytes())
    original_report = json.loads((original_directory / "report.json").read_bytes())
    original_report["config"] = deepcopy(original_frozen["config"])
    original_names = (
        "pipeline_run.py",
        "pipeline_assembly.py",
        "generalization_run.py",
        "pipeline_regions.py",
        "pipeline_source_order.py",
    )
    module_root = Path(__file__).resolve().parents[1] / "bench"
    code = original_directory / "code"
    code.mkdir()
    authenticated = {}
    for name in original_names:
        data = (module_root / name).read_bytes()
        (code / name).write_bytes(data)
        authenticated[name] = sha(data)
    original_frozen["code_sha256"] = authenticated
    write_json(original_directory / "frozen.json", original_frozen)
    write_json(original_directory / "report.json", original_report)
    write_json(original_directory / "p0-request-0.json", {"model": "synthetic-baseline", "state": "literal source"})
    write_json(original_directory / "p0-response-0.json", {"synthetic": True})
    output = tmp_path / "repaired"
    p003_boundary_run.run(original_directory, output, configuration(), MockClient(tmp_path))
    report = json.loads((output / "report.json").read_bytes())
    frozen = json.loads((output / "frozen.json").read_bytes())
    summary, verified = verify_incremental_run(output, report, frozen, authenticated)
    assert summary["original_request_artifacts"] == 1
    assert summary["original_response_artifacts"] == 1
    assert verified["p0"]["operational"]
    assert report["results"][0]["tables"][0]["row_count"] == 2
    assert report["pages_per_minute"] is None
    (output / "baseline/p0-request-0.json").write_text("{}")
    with pytest.raises(ValueError, match="baseline bytes changed"):
        verify_incremental_run(output, report, frozen, authenticated)


def test_region_verifier_replays_source_prerequisite_raster_and_empty_yolo(
    tmp_path: Path,
) -> None:
    from bench import p003_regions_run as processor
    from bench import pipeline_vision_transcription as transcription
    from bench.p003_report import verify_regions_output
    from bench.silver import write_json
    from test_p003_boundary_run import baseline
    from test_p003_regions_run import record

    import pylopdf

    source_record = record(tmp_path)
    source_record["id"] = "p0"
    _record, child = baseline(tmp_path / "native")
    child["calls"] = []
    child["original_rotation"] = 0
    child["source"]["page_size"] = [600, 800]
    child["region_plan"]["page_size"] = [600, 800]
    child["region_plan"]["regions"][0]["source"]["page_size"] = [600, 800]
    write_json(tmp_path / "native/p0-result.json", child)
    config = {
        "campaign": "P003",
        "run_id": "test",
        "region_proposal_arm": "yolo",
        "gate_enabled": False,
        "source_order": "original",
    }
    settings = processor._configuration(config)
    source = {key: child["source"][key] for key in ("page_size", "words")}
    with pylopdf.open(source_record["pdf_path"]) as document:
        page = document[0]
        viewport = list(page.rect)
        pixels = page.render(
            scale=processor.PROPOSAL_EDGE / max(page.rect.width, page.rect.height), background=(255, 255, 255)
        )
        # The PDF fixture is 600 x 800: fixed1536 rendering gives 1152 x 1536.
        image = {"edge": 1536, "size": [1152, 1536], "sha256": sha(pixels), "viewport": viewport}
    plan = processor._yolo({"boxes": [], "device": "cpu", "type": "result", "viewport": viewport}, viewport, source)
    prediction = {
        "id": "p0",
        "status": "ok",
        "native_child": child,
        "source": source,
        "settings": settings,
        "proposal_arm": "yolo",
        "viewport": viewport,
        "original_rotation": 0,
        "proposal_image": image,
        "layout_detection": {"boxes": [], "device": "cpu", "type": "result", "viewport": viewport},
        "proposal_plan": plan,
        "proposal_count": 0,
        "gate_regions": [],
        "conflict_selection": processor.select_nonoverlapping([]),
        "selected_region_count": 0,
        "transcription_regions": [],
        "calls": [],
        "route": "p003_decision_regions",
        "processor": "p003_regions",
        "source_conserved": False,
        "text_provenance": transcription.PROVENANCE,
        "output_scope": "table_only",
        "output_atomic": True,
        "coverage": "unverified",
        "unresolved_ids": [],
        "tables": [],
    }
    from bench.generalization_vision_regions import compose

    write_json(tmp_path / "p0-proposals.json", plan)
    state = compose([], viewport)
    write_json(tmp_path / "p0-structure.json", state)
    (tmp_path / "p0.md").write_text(transcription.markdown(state))
    write_json(tmp_path / "p0-result.json", prediction)
    module_root = Path(__file__).resolve().parents[1] / "bench"
    frozen = {
        "config": config,
        "code_sha256": {
            name: sha((module_root / name).read_bytes())
            for name in (
                "p003_regions_run.py",
                "p003_region_candidates.py",
                "generalization_vision_regions.py",
                "pipeline_vision_transcription.py",
            )
        },
    }
    assert verify_regions_output(tmp_path, prediction, frozen, source_record)["operational"]
    malformed = deepcopy(prediction)
    malformed["proposal_image"]["sha256"] = "changed pixels"
    write_json(tmp_path / "p0-result.json", malformed)
    with pytest.raises(ValueError, match="independently rendered"):
        verify_regions_output(tmp_path, malformed, frozen, source_record)


def reconciliation_fixture(tmp_path: Path, *, reserved: bool = False) -> tuple[Path, Path, Path]:
    """Retain gateway-zero BYOK evidence alongside a standard positive charge."""
    import json

    from bench.silver import write_json

    run, artifacts = tmp_path / "run", tmp_path / "costs"
    run.mkdir()
    artifacts.mkdir()
    original = {"accounted_usd": 0.3, "cost_status": "reserved", "provider_reported_usd": 0}
    reconciled = {
        "accounted_usd": 0.012,
        "cost_status": "provider-reported BYOK upstream plus gateway USD",
        "provider_reported_usd": 0,
        "effective_usd": 0.012,
        "gateway_reported_usd": 0,
        "upstream_reported_usd": 0.012,
    }
    standard = {"accounted_usd": 0.02, "cost_status": "provider-reported USD", "provider_reported_usd": 0.02}
    rows, ledger_entries = [], []
    for index, old, new, usage in (
        (0, original, reconciled, {"is_byok": True, "cost": 0, "cost_details": {"upstream_inference_cost": 0.012}}),
        (1, standard, standard, {"is_byok": False, "cost": 0.02, "cost_details": {"upstream_inference_cost": 7}}),
    ):
        request = json.dumps({"model": "example", "prompt": str(index)}).encode()
        request_name, response_name = f"request-{index:03d}.json", f"response-{index:03d}.json"
        (artifacts / request_name).write_bytes(request)
        write_json(artifacts / response_name, {"usage": usage})
        response_hash = sha((artifacts / response_name).read_bytes())
        row = {
            "ledger_index": index,
            "request_sha256": sha(request),
            "request_path": request_name,
            "response_path": response_name,
            "response_sha256": response_hash,
            "original_accounting": old,
            "reconciled_accounting": new,
        }
        rows.append(row)
        ledger_entries.append(
            {
                "index": index,
                "tag": f"P003/run/stage/{index}",
                "request_sha256": sha(request),
                "response_file": response_name,
                **new,
                "accounting_revisions": [{"original": old, "reconciled": new, "response_sha256": response_hash}],
            }
        )
    report = {
        "config": {"run_id": "run"},
        "ledger_attempts": 2,
        "accounted_usd": 0.32,
        "provider_reported_usd": 0.02,
        "missing_provider_charge_count": 0,
        "cost_bases": {"reserved": 1, "provider-reported USD": 1},
        "effective_usd": None,
        "results": [{"calls": [{"entry": {"index": 0, **original}}, {"entry": {"index": 1, **standard}}]}],
    }
    if reserved:
        old = {"accounted_usd": 0.5, "cost_status": "reserved"}
        (artifacts / "request-002.json").write_bytes(b"{}")
        rows.append(
            {
                "ledger_index": 2,
                "request_sha256": sha(b"{}"),
                "request_path": "request-002.json",
                "response_path": None,
                "response_sha256": None,
                "original_accounting": old,
                "reconciled_accounting": old,
            }
        )
        ledger_entries.append({"index": 2, "tag": "P003/run/failed", "request_sha256": sha(b"{}"), **old})
        report.update(ledger_attempts=3, accounted_usd=0.82, missing_provider_charge_count=1)
        report["cost_bases"]["reserved"] = 2
    write_json(run / "report.json", report)
    write_json(
        artifacts / "costs.json",
        {
            "schema": 1,
            "original_report_sha256": sha((run / "report.json").read_bytes()),
            "run_tag_prefix": "P003/run/",
            "entries": rows,
        },
    )
    write_json(tmp_path / "ledger.json", {"requests": ledger_entries})
    return run, artifacts / "costs.json", tmp_path / "ledger.json"


def test_cost_overlay_preserves_gateway_zero_without_nonbyok_double_count(tmp_path: Path) -> None:
    from bench.p003_report import verify_cost_reconciliation

    run, sidecar, ledger = reconciliation_fixture(tmp_path)
    result = verify_cost_reconciliation(run, sidecar, ledger)
    assert result["original"]["effective_api_usd"] is None
    assert result["reconciled"]["effective_api_usd"] == pytest.approx(0.032)
    assert result["reconciled"]["provider_reported_gateway_subtotal_usd"] == 0.02


def test_cost_overlay_retains_failed_reservation_as_unknown(tmp_path: Path) -> None:
    from bench.p003_report import verify_cost_reconciliation

    run, sidecar, ledger = reconciliation_fixture(tmp_path, reserved=True)
    result = verify_cost_reconciliation(run, sidecar, ledger)
    assert result["reconciled"]["effective_api_usd"] is None
    assert result["reconciled"]["known_partial_effective_api_usd"] == pytest.approx(0.032)


@pytest.mark.parametrize("mutation", ["missing_attempt", "response", "request", "history", "gateway"])
def test_cost_overlay_rejects_incomplete_or_changed_evidence(tmp_path: Path, mutation: str) -> None:
    import json

    from bench.p003_report import verify_cost_reconciliation
    from bench.silver import write_json

    run, sidecar, ledger = reconciliation_fixture(tmp_path)
    data = json.loads(sidecar.read_bytes())
    if mutation == "missing_attempt":
        data["entries"].pop()
    elif mutation == "response":
        (sidecar.parent / "response-000.json").write_text("{}")
    elif mutation == "request":
        (sidecar.parent / "request-000.json").write_text("{}")
    elif mutation == "history":
        value = json.loads(ledger.read_bytes())
        value["requests"][0]["accounting_revisions"] = []
        write_json(ledger, value)
    else:
        data["entries"][0]["reconciled_accounting"]["gateway_reported_usd"] = 0.1
    write_json(sidecar, data)
    with pytest.raises(ValueError, match=r"overlay|bytes|response|accounting"):
        verify_cost_reconciliation(run, sidecar, ledger)


@pytest.mark.parametrize("mode", ["selected", "selected_pinned", "abstain", "duplicate", "malformed"])
def test_candidate_verifier_replays_complete_pools_and_atomic_fallback(tmp_path: Path, mode: str) -> None:
    import json

    from bench import p003_candidate_run as runner
    from bench.p003_report import verify_candidate_run
    from test_p003_candidate_run import Client, baseline, config

    first, second = tmp_path / "first", tmp_path / "second"
    _, _, trust0 = baseline(first, "first", provider_name="example" if mode == "selected_pinned" else None)
    _, _, trust1 = baseline(
        second,
        "first" if mode == "duplicate" else "second",
        provider_name="example" if mode == "selected_pinned" else None,
    )
    output = tmp_path / "ranked"
    report = runner.run(
        [first, second],
        [trust0, trust1],
        output,
        config(),
        Client(tmp_path, abstain=mode == "abstain", malformed=mode == "malformed"),
    )
    frozen = json.loads((output / "frozen.json").read_bytes())
    trust = {"baseline-0": trust0, "baseline-1": trust1}
    provenance, verified = verify_candidate_run(output, report, frozen, trust)
    assert sum(v["operational"] for v in verified.values()) == 16
    assert len(provenance["candidate_baselines"]) == 2
    assert report["pages_per_minute"] is None
    with pytest.raises(ValueError, match="independent trust"):
        verify_candidate_run(output, report, frozen, None)
    if mode == "selected":
        changed = deepcopy(report)
        changed["results"][0]["ranking_regions"][0]["selected_sha256"] = "changed"
        from bench.silver import write_json

        write_json(output / "p0-result.json", changed["results"][0])
        with pytest.raises(ValueError, match="selected origin"):
            verify_candidate_run(output, changed, frozen, trust)


def test_reviewed_historical_candidate_parser_still_needs_external_admission_and_trust(tmp_path: Path) -> None:
    import json

    from bench import p003_candidate_run as runner
    from bench.p003_report import verify_candidate_run
    from bench.silver import write_json
    from test_p003_candidate_run import Client, baseline, config

    first, second = tmp_path / "first", tmp_path / "second"
    _, _, trust0 = baseline(first, "first")
    _, _, trust1 = baseline(second, "second")
    archived = second / "code/pipeline_vision_transcription.py"
    old = archived.read_text().replace(
        "Model is outside the admitted matched transcription controls",
        "Model is outside the matched Anthropic 5.5 controls",
    )
    archived.write_text(old)
    digest = sha(archived.read_bytes())
    assert digest in runner.ROOT_REVIEWED_PARSER_SHA256
    trust1["pipeline_vision_transcription.py"] = digest
    original = json.loads((second / "frozen.json").read_bytes())
    original["code_sha256"]["pipeline_vision_transcription.py"] = digest
    write_json(second / "frozen.json", original)
    output = tmp_path / "ranked"
    report = runner.run(
        [first, second],
        [trust0, trust1],
        output,
        config(reviewed_parser_sha256=[digest]),
        Client(tmp_path, abstain=True),
    )
    frozen = json.loads((output / "frozen.json").read_bytes())
    trust = {"baseline-0": trust0, "baseline-1": trust1}
    with pytest.raises(ValueError, match="independently supplied root-reviewed"):
        verify_candidate_run(output, report, frozen, trust)
    _, verified = verify_candidate_run(output, report, frozen, trust, reviewed_parser_sha256=(digest,))
    assert all(page["operational"] for page in verified.values())
    bad_trust = deepcopy(trust)
    bad_trust["baseline-1"]["pipeline_vision_transcription.py"] = "untrusted"
    with pytest.raises(ValueError, match="Untrusted archived"):
        verify_candidate_run(output, report, frozen, bad_trust, reviewed_parser_sha256=(digest,))
