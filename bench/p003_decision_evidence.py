"""Separate fresh model decisions from historical baseline outputs in verified P003 runs."""

from __future__ import annotations

from collections import Counter
from typing import Any


def decision_evidence(report: dict[str, Any]) -> dict[str, Any] | None:
    """Describe actual incremental choices; retained pipeline success is a separate observation."""
    processor = report["config"].get("processor")
    stages = {
        "p003_candidate_choice": ("incremental_ranking", "ranking_calls", "ranking_status"),
        "p003_candidate_valid_regions": ("incremental_ranking", "ranking_calls", "ranking_status"),
        "p003_gate": ("incremental_gate", "calls", "gate_status"),
        "p003_topology_source": ("incremental_ownership", "topology_calls", "topology_status"),
        "p003_boundary_repair": ("incremental_repair", "repair_calls", "repair_status"),
    }
    if processor not in stages:
        return None
    stage_key, call_key, status_key = stages[processor]
    stage = report[stage_key]
    historical_replay = report["config"].get("transcript_replay") is True
    calls = (
        []
        if historical_replay
        else [call for page in report["results"] for call in page.get(call_key, []) if call.get("replayed") is False]
    )
    entries = stage.get("entries", [])
    requested = report["config"].get("model", report["config"].get("gate_model"))
    requested_models = Counter(e.get("requested_model") for e in entries if e.get("requested_model") is not None)
    served_models = Counter(e.get("served_model") for e in entries if e.get("served_model") is not None)
    outcomes = Counter(p.get(status_key, "unrecorded") for p in report["results"])
    retained = sum(
        any(marker in str(page.get(status_key, "")) for marker in ("retained", "skipped", "not_applicable"))
        for page in report["results"]
    )
    answer = {
        "scope": "Fresh incremental model decisions; historical baseline output success is not decision success",
        "requested_model": requested,
        "requested_models_observed": dict(requested_models),
        "served_models_observed": dict(served_models),
        "requested_model_mismatch_attempts": sum(
            count for model, count in requested_models.items() if model != requested
        ),
        "unknown_request_model_attempts": len(entries) - sum(requested_models.values()),
        "explicit_retry_attempts": sum(e.get("retry_of_index") is not None for e in entries),
        "fresh_ledger_attempts": stage.get("ledger_attempts"),
        "fresh_returned_calls": len(calls),
        "attempt_transport_errors": dict(Counter(e["error"] for e in entries if isinstance(e.get("error"), str))),
        "page_status_counts": dict(outcomes),
        "retained_or_skipped_baseline_pages": retained,
        "pipeline_operational_pages": sum(p["status"] == "ok" for p in report["results"])
        if all("status" in p for p in report["results"])
        else None,
        "historical_transcript_replay": historical_replay,
        "served_model_scope": (
            "Provider-reported version identifiers; alias differences alone do not establish model substitution"
        ),
    }
    if processor in {"p003_candidate_choice", "p003_candidate_valid_regions"}:
        regions = [r for page in report["results"] for r in page.get("ranking_regions", [])]
        parsed = Counter(r.get("audit", {}).get("selection_status") for r in regions if r.get("audit"))
        committed = sum(r.get("ranking_status") == "selected" for r in regions)
        abstaining_pages = sum(
            any(r.get("audit", {}).get("selection_status") == "unresolved" for r in page.get("ranking_regions", []))
            for page in report["results"]
        )
        fully_chosen_pages = sum(
            page.get("ranking_status") == "completed"
            and any(r.get("ranking_status") == "selected" for r in page.get("ranking_regions", []))
            and not any(
                r.get("audit", {}).get("selection_status") == "unresolved" for r in page.get("ranking_regions", [])
            )
            for page in report["results"]
        )
        answer.update(
            parsed_selected_choices=parsed.get("selected", 0),
            parsed_unresolved_abstentions=parsed.get("unresolved", 0),
            committed_model_crop_choices=committed,
            pages_with_unresolved_baseline_retention=abstaining_pages,
            fully_chosen_incremental_pages=fully_chosen_pages,
            decision_status=(
                "Model abstention retains historical first output in these artifacts; it is not a chosen model output"
            ),
        )
    return answer


def confirmed_candidate_predictions(report: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Keep only committed model-selected complete regions; never credit unresolved first states."""
    if report["config"].get("processor") not in {"p003_candidate_choice", "p003_candidate_valid_regions"}:
        return None
    from bench.generalization_vision_regions import compose  # noqa: PLC0415

    predictions = []
    for page in report["results"]:
        selected = [r for r in page.get("ranking_regions", []) if r.get("ranking_status") == "selected"]
        failed = "fail" in page.get("ranking_status", "") or page["status"] != "ok"
        if failed:
            tables = []
        else:
            regions = [
                {**page["transcription_regions"][r["index"]], "index": ordinal, "request_index": ordinal}
                for ordinal, r in enumerate(selected)
            ]
            tables = compose(regions, page["viewport"])["tables"]
        predictions.append(
            {
                "id": page["id"],
                "status": "error" if failed else "ok",
                "tables": tables,
                "selected_model_regions": len(selected) if not failed else 0,
                "scope": "Model-selected complete crop states only; duplicates, abstentions and failures excluded",
            }
        )
    return predictions
