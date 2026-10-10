"""Tiny inputs retain complete words and exact native choices without assignment fallback."""

import json
from copy import deepcopy

import pytest
from bench import p003_micro_relations as micro


def source(text: str = "Complete word") -> dict:
    return {
        "page_size": [100, 100],
        "words": [
            {"id": "original-a", "text": text, "bbox": [10, 10, 40, 20]},
            {"id": "original-b", "text": "literal B", "bbox": [45, 10, 60, 20]},
            {"id": "original-c", "text": "next line", "bbox": [10, 30, 60, 40]},
        ],
    }


def test_all_kinds_compact_and_verbose_have_identical_words_and_questions() -> None:
    plan = micro.freeze(source())
    assert {p["kind"] for p in plan["pairs"]} == set(micro.KINDS)
    for pair in plan["pairs"]:
        compact = micro.body(plan, pair["id"], "convaiinnovations/laya")
        verbose = micro.body(plan, pair["id"], "convaiinnovations/laya", mode="verbose")
        assert len(compact["state"].encode()) <= 768
        a, b = json.loads(compact["state"]), json.loads(verbose["state"])
        assert compact["questions"] == verbose["questions"]
        assert a["p"] == b["source_page_size"]
        for alias, ident in zip(("a", "b"), pair["source_ids"], strict=True):
            assert a["words"][alias] == [plan["word_inventory"][ident]["text"], plan["word_inventory"][ident]["bbox"]]
            assert a["words"][alias][0] == b["words"][alias]["text"]
        assert "other words" in a["omit"]
        assert "image" not in compact


def test_utf8_capacity_whole_word_refusal_and_empty_unknown_source_ids() -> None:
    plan = micro.freeze(source("語" * 300))
    with pytest.raises(micro.CapacityError, match="without truncation"):
        micro.body(plan, "q0", "liquid/d1")
    verbose = micro.body(plan, "q0", "liquid/d1", mode="verbose")
    assert "語" * 300 in verbose["state"]
    with pytest.raises(ValueError, match="identity"):
        micro.body(plan, "invented", "liquid/d1")


def test_sample_scope_explicit_complete_local_inventory_and_digest_tampering() -> None:
    plan = micro.freeze(source(), max_pairs=2)
    assert len(plan["word_inventory"]) == 3
    assert len(plan["pairs"]) == 2
    assert plan["omitted_candidate_pair_count"] > 0
    changed = deepcopy(plan)
    changed["word_inventory"]["original-a"]["text"] = "invented"
    with pytest.raises(ValueError, match="changed"):
        micro.body(changed, "q0", "convaiinnovations/laya")


def test_native_probabilities_and_fail_closed_no_geometry_receipt() -> None:
    plan = micro.freeze(source())
    request = micro.body(plan, "q0", "convaiinnovations/laya")
    answer = {
        "answers": {
            "q0": {
                "type": "choice",
                "choice": "same",
                "probabilities": {"same": 0.8, "separate": 0.1, "unresolved": 0.1},
                "confidence": 0.8,
            }
        }
    }
    result = micro.receipt(plan, "q0", request, answer)
    assert result["pure_model"]
    assert not result["assignment_applied"]
    assert result["decision"]["raw_probabilities"]["same"] == 0.8
    assert result["source_ids"] == plan["pairs"][0]["source_ids"]
    malformed = deepcopy(answer)
    malformed["answers"]["q0"]["choice"] = "invented"
    with pytest.raises(ValueError, match="raw maximum"):
        micro.receipt(plan, "q0", request, malformed)
    with pytest.raises(ValueError, match="identities"):
        micro.receipt(plan, "q0", request, {"answers": {}})
    assert "geometric_fallback" not in result


def test_pure_outcome_counts_abstentions_errors_without_fallback_or_retries() -> None:
    plan = micro.freeze(source())
    model = "convaiinnovations/laya"
    request = micro.body(plan, "q0", model)
    result = micro.receipt(
        plan,
        "q0",
        request,
        {
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": "unresolved",
                    "probabilities": {"same": 0, "separate": 0, "unresolved": 1},
                }
            }
        },
    )
    attempts = [
        {"pair_id": "q0", "mode": "micro", "model": model, "status": "valid", "receipt": result},
        {"pair_id": "q1", "mode": "micro", "model": model, "status": "transport_error"},
    ]
    summary = micro.outcomes(plan, attempts, model=model)
    assert summary["valid_abstention"] == 1
    assert summary["transport_error"] == 1
    assert summary["fallback_decisions"] == 0
    assert not summary["correctness_measured"]
    with pytest.raises(ValueError, match="no retries"):
        micro.outcomes(plan, attempts * 2, model=model)
