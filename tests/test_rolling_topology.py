"""Short-table and corridor alternatives retain every literal source word."""

from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy

import pytest
from bench.rolling_rows import assemble
from bench.rolling_topology import Config, configs, propose, union_candidates, union_request


def source() -> dict:
    words = [
        {"id": "w0", "text": "Category", "bbox": [10, 10, 50, 20]},
        {"id": "w1", "text": "Measure", "bbox": [110, 10, 150, 20]},
        {"id": "w2", "text": "Node", "bbox": [10, 50, 35, 60]},
        {"id": "w3", "text": "12", "bbox": [170, 50, 180, 60]},
        {"id": "w4", "text": "Footer", "bbox": [10, 400, 45, 410]},
    ]
    return {"page_size": [0, 0, 300, 500], "words": words, "vector_candidates": []}


@pytest.mark.parametrize("config", configs(), ids=lambda c: c["name"])
def test_two_row_header_data_corridor_and_complete_id_inventory(config: Config) -> None:
    page = source()
    result = propose(page, config)
    exact = next(t for t in result["candidates"] if t["values"] == [["Category", "Measure"], ["Node", "12"]])
    assert exact["row_count"] == 2
    assert exact["unresolved_ids"] == ["w4"]
    assert "unknown" in exact["header_role"]
    for table in result["candidates"]:
        owned = [i for cell in table["cells"] for i in cell["source_ids"]]
        assert Counter(owned + table["unresolved_ids"]) == Counter(w["id"] for w in page["words"])


def test_seed_header_preserves_an_empty_data_column() -> None:
    page = source()
    page["words"][1]["bbox"] = [210, 10, 250, 20]
    page["words"][3]["bbox"] = [270, 50, 280, 60]
    page["words"].append({"id": "w5", "text": "Other", "bbox": [110, 10, 140, 20]})
    result = propose(page, configs()[2])
    assert any(t["values"] == [["Category", "Other", "Measure"], ["Node", "", "12"]] for t in result["candidates"])


def test_two_hanging_lines_have_a_source_owned_rolling_alternative() -> None:
    page = source()
    page["words"].extend(
        [
            {"id": "w5", "text": "tail", "bbox": [10, 65, 30, 75]},
            {"id": "w6", "text": "detail", "bbox": [10, 80, 40, 90]},
        ]
    )
    rolling = propose(page, configs()[2])
    assert any(t["values"] == [["Category", "Measure"], ["Node tail detail", "12"]] for t in rolling["candidates"])
    physical = propose(page, configs()[0])
    assert all(t["values"] != [["Category", "Measure"], ["Node tail detail", "12"]] for t in physical["candidates"])


@pytest.mark.parametrize("config", configs(), ids=lambda c: c["name"])
def test_private_metadata_cannot_change_hypotheses(config: Config) -> None:
    page = source()
    before = propose(page, config)
    altered = deepcopy(page)
    for key in ("gold", "id", "family", "expected", "kind", "template", "text_candidates"):
        altered[key] = "SECRET_LABEL"
    assert propose(altered, config) == before


def test_config_registry_is_independent_and_unknown_rules_are_refused() -> None:
    policy = configs()[0]
    policy["wrap_gap_heights"] = 99
    assert configs()[0]["wrap_gap_heights"] != 99
    with pytest.raises(ValueError, match="frozen"):
        propose(source(), policy)


def test_union_generic_ids_preserve_sources_and_exclude_policy_priors() -> None:
    page = source()
    originals = [assemble(page, v) for v in ("physical", "rolling")]
    topologies = [propose(page, c) for c in configs()]
    candidates, provenance = union_candidates(page, originals, topologies)
    assert [c["id"] for c in candidates] == [f"c{i}" for i in range(len(candidates))]
    assert len(candidates) < sum(len(a["candidates"]) for a in topologies)
    assert all(p["source_policies"] for p in provenance)
    request = union_request(page, candidates, "test-model")
    encoded = json.dumps(request)
    assert "T001" not in encoded
    assert "T002" not in encoded
    assert "T003" not in encoded
    assert set(request["questions"]["q0"]["criteria"]) == {c["id"] for c in candidates} | {"not_table", "unresolved"}
    assert request["state"]["source_words"] == page["words"]
    for candidate in candidates:
        owned = [i for cell in candidate["table"]["cells"] for i in cell["source_ids"]]
        assert Counter(owned + candidate["unresolved_ids"]) == Counter(w["id"] for w in page["words"])
