"""Local extent alternatives preserve existing source ownership and uncertainty."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy

import pytest
from bench.rolling_extent import Config, configs, propose


def source() -> dict:
    return {
        "vector_candidates": [],
        "page_size": [0, 0, 600, 800],
        "words": [
            {"id": "a", "text": "Key", "bbox": [10, 10, 40, 20]},
            {"id": "b", "text": "Amount", "bbox": [110, 10, 150, 20]},
            {"id": "c", "text": "Item", "bbox": [10, 60, 40, 70]},
            {"id": "d", "text": "17", "bbox": [110, 60, 130, 70]},
            {"id": "e", "text": "Office", "bbox": [10, 700, 40, 710]},
            {"id": "f", "text": "1", "bbox": [110, 700, 130, 710]},
        ],
    }


@pytest.mark.parametrize("policy", configs(), ids=lambda p: p["name"])
def test_detached_row_trim_inventory_and_label_invariance(policy: Config) -> None:
    page = source()
    result = propose(page, policy)
    assert any(t["values"] == [["Key", "Amount"], ["Item", "17"]] for t in result["candidates"])
    for table in result["candidates"]:
        ids = [i for c in table["cells"] for i in c["source_ids"]] + table["unresolved_ids"]
        assert Counter(ids) == Counter(w["id"] for w in page["words"])
    altered = deepcopy(page)
    altered.update(gold="secret", kind="secret", expected="secret")
    assert propose(altered, policy) == result


def test_policy_mutation_is_rejected() -> None:
    policy = configs()[0]
    policy["cap_heights"] = 99
    with pytest.raises(ValueError, match="frozen"):
        propose(source(), policy)
