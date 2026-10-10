"""Abstention and historical outputs do not masquerade as model decision success."""

import json

from bench.p003_decision_evidence import confirmed_candidate_predictions, decision_evidence
from bench.p003_report import strict_scores
from tests.test_p003_report import table


def test_operational_first_output_with_abstention_is_not_fully_chosen_model_page() -> None:
    report = {
        "config": {"processor": "p003_candidate_choice", "model": "judge"},
        "results": [
            {
                "status": "ok",
                "ranking_status": "completed",
                "ranking_regions": [
                    {"ranking_status": "unresolved_retained_first", "audit": {"selection_status": "unresolved"}}
                ],
                "ranking_calls": [{"replayed": False}],
            }
        ],
        "incremental_ranking": {
            "ledger_attempts": 1,
            "entries": [{"requested_model": "judge", "served_model": "judge-v1"}],
        },
    }
    evidence = decision_evidence(report)
    assert evidence is not None
    assert evidence["pipeline_operational_pages"] == 1
    assert evidence["fully_chosen_incremental_pages"] == evidence["committed_model_crop_choices"] == 0
    assert evidence["parsed_unresolved_abstentions"] == 1
    assert evidence["requested_model_mismatch_attempts"] == 0
    assert evidence["served_models_observed"] == {"judge-v1": 1}


def test_discarded_choice_and_alternative_model_request_remain_visible() -> None:
    report = {
        "config": {"processor": "p003_candidate_choice", "model": "judge"},
        "results": [
            {
                "status": "ok",
                "ranking_status": "failed_retained_first",
                "ranking_regions": [
                    {"ranking_status": "discarded_atomic_failure", "audit": {"selection_status": "selected"}}
                ],
                "ranking_calls": [{"replayed": False}],
            }
        ],
        "incremental_ranking": {
            "ledger_attempts": 2,
            "entries": [
                {"requested_model": "judge"},
                {"requested_model": "other", "retry_of_index": 1, "error": "HTTP 429"},
            ],
        },
    }
    evidence = decision_evidence(report)
    assert evidence is not None
    assert evidence["parsed_selected_choices"] == 1
    assert evidence["committed_model_crop_choices"] == 0
    assert evidence["retained_or_skipped_baseline_pages"] == 1
    assert evidence["requested_model_mismatch_attempts"] == evidence["explicit_retry_attempts"] == 1
    assert evidence["attempt_transport_errors"] == {"HTTP 429": 1}


def test_transcript_replay_never_claims_original_responses_as_fresh_decisions() -> None:
    evidence = decision_evidence(
        {
            "config": {"processor": "p003_topology_source", "model": "judge", "transcript_replay": True},
            "results": [{"status": "ok", "topology_status": "completed", "topology_calls": [{"replayed": False}]}],
            "incremental_ownership": {"ledger_attempts": 0, "entries": []},
        }
    )
    assert evidence is not None
    assert evidence["fresh_returned_calls"] == 0
    assert evidence["historical_transcript_replay"]


def test_confirmed_quality_omits_abstained_duplicate_and_discarded_tables() -> None:
    def crop(value: str) -> dict[str, object]:
        return {
            "status": "ok",
            "viewport": [0, 0, 100, 100],
            "tables": [{**table([[value]]), "bbox": [0, 0, 100, 100]}],
            "transcription_response": {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "answers": {
                                        "q0": {
                                            "tables": [
                                                {"bbox": [0, 0, 1000, 1000], "matrix": [[value]], "mergedspans": []}
                                            ]
                                        }
                                    }
                                }
                            )
                        },
                    }
                ]
            },
        }

    report = {
        "config": {"processor": "p003_candidate_choice"},
        "results": [
            {
                "id": "p",
                "status": "ok",
                "ranking_status": "completed",
                "viewport": [0, 0, 100, 100],
                "transcription_regions": [crop("A"), crop("B"), crop("C")],
                "ranking_regions": [
                    {"index": 0, "ranking_status": "selected"},
                    {"index": 1, "ranking_status": "unresolved_retained_first"},
                    {"index": 2, "ranking_status": "not_applicable_duplicates"},
                ],
            }
        ],
    }
    predictions = confirmed_candidate_predictions(report)
    assert predictions is not None
    assert predictions[0]["selected_model_regions"] == 1
    targets = [{"id": "p", "tables": [table([[value]]) for value in ("A", "B", "C")]}]
    scored = strict_scores(targets, predictions)["totals"]
    assert scored["expected_cells"] == 3
    assert scored["strict_exact_cells"] == 1
    assert scored["missing_tables"] == 2
    report["results"][0]["ranking_status"] = "failed_retained_first"
    assert confirmed_candidate_predictions(report)[0]["tables"] == []
