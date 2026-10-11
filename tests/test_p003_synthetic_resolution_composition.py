"""Label-free tests for all-edge composition declarations and immutable component policies."""

from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_synthetic_resolution_composition as helper
from bench import p003_synthetic_resolution_queue as queue


def components() -> tuple[list[dict], dict]:
    vector = [
        {
            "id": f"opaque{i}",
            "kind": "cell",
            "treatment": "direct_vector",
            "status": "classified" if i < 12 else "abstained",
            "choice": "same" if i < 12 else "unresolved",
        }
        for i in range(24)
    ]
    model = {
        "config": {"model": "cloudflare/clef", "image_edge": 256},
        "charges": {"effective_usd": 1.0},
        "rows": [
            {
                "id": f"opaque{i}",
                "kind": "cell",
                "status": "valid_nonabstaining",
                "receipt": {"choice": "separate", "probabilities": {"separate": 1.0}},
            }
            for i in range(24)
        ],
    }
    return vector, model


def test_all75_fixed_policies_no_winning_edge(tmp_path: Path) -> None:
    rows = queue.queue_plan(tmp_path, tmp_path, tmp_path, tmp_path)
    result = helper.arm_plan(rows)
    assert len(result) == 75
    assert len({r["name"] for r in result}) == 75
    assert sum(r["question_count"] for r in result) == 1800
    assert {r["policy"] for r in result} == set(helper.POLICIES)
    with pytest.raises(ValueError, match="Complete unique"):
        helper.arm_plan(rows[:-1])


@pytest.mark.parametrize(
    ("policy", "classified"), [("vector_first", 24), ("agreement_only", 0), ("either_evidence_conflicts_abstain", 12)]
)
def test_fixed_policies_preserve_components_and_actual_cost(policy: str, classified: int) -> None:
    vector, model = components()
    before = deepcopy((vector, model))
    result = helper.combine(vector, model, policy)
    assert sum(r["status"] == "classified" for r in result["rows"]) == classified
    assert len(result["rows"]) == 24
    assert result["actual_retained_model_charges"] == {"effective_usd": 1.0}
    assert result["hypothetical_cost_saving_usd"] is None
    assert result["new_api_calls"] == 0
    assert result["fresh_throughput"] is None
    assert (vector, model) == before
    assert all(r["probability"] is None for r in result["rows"])


def test_duplicate_or_old_control_refused() -> None:
    vector, model = components()
    model["config"]["image_edge"] = 128
    with pytest.raises(ValueError, match="new model/edge"):
        helper.combine(vector, model, "vector_first")
    model["config"]["image_edge"] = 256
    vector[-1] = vector[0]
    with pytest.raises(ValueError, match="Complete unique"):
        helper.combine(vector, model, "vector_first")
