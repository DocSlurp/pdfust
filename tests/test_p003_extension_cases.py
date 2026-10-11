"""Fresh source isolation, literal identity and reversible repair stress checks."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from bench import p003_extension_cases as cases
from bench.generalization_report import load_corpus
from bench.pipeline_repair import validate
from bench.silver import canonical, sha


def test_independent_plan_streams_neutral_titles_and_actual_unnamed_headers() -> None:
    plans = cases.plans()
    assert plans == cases.plans()
    assert plans != cases.plans("independent-extension-seed")
    assert len({plan["id"] for plan in plans}) == 64
    assert Counter(plan["family"] for plan in plans) == dict.fromkeys(cases.FAMILIES, 8)
    assert all(plan["title"] != "Internal Notes" for plan in plans)
    assert all(not any(table["target"]["values"][0])
               for plan in plans if plan["family"] == "unnamed" for table in plan["tables"])
    wrapped = next(plan for plan in plans if plan["family"] == "wrapped")
    data, targets, _ = cases.authored(wrapped)
    renamed = {**wrapped, "id": "fresh-unrelated-page-id"}
    other_data, other_targets, _ = cases.authored(renamed)
    assert data == other_data
    assert targets == other_targets
    assert wrapped["id"].encode() not in data


def test_geometry_only_menu_preserves_repeated_literal_identity_and_wrap_stress() -> None:
    plan = next(plan for plan in cases.plans() if plan["family"] == "wrapped")
    data, _targets, _receipt = cases.authored(plan)
    source, rules, states = cases.extract_source(data, plan["id"])
    menu = cases.candidate_menu(source, states, plan["id"])
    assert menu == cases.candidate_menu(source, states, plan["id"])
    assert rules
    assert menu["references_used"] is False
    assert menu["omitted_context_counts"] == {"words": 0, "rules": 0}
    assert sha(canonical(states[0])) in {sha(canonical(candidate["state"])) for candidate in menu["candidates"]}
    for candidate in menu["candidates"]:
        validate(source, candidate["state"])
    assert len({w["id"] for w in source["words"]}) == len(source["words"])
    assert any(n > 1 for n in Counter(w["text"] for w in source["words"]).values())
    treatments = cases.stress_baselines(source, states[0], plan["id"])
    assert {item["treatment"] for item in treatments} == {
        "missing_table_value", "doubled_source_ownership", "swapped_cell_values", "wrapped_continuation_shift",
    }
    for treatment in treatments:
        assert treatment["raw_baseline"] != states[0]
        if treatment["valid_source_ownership"]:
            validate(source, treatment["raw_baseline"])
        else:
            with pytest.raises(ValueError, match="exactly one owner"):
                validate(source, treatment["raw_baseline"])


def test_complete64_source_frozen_before_separate_gold(tmp_path: Path) -> None:
    output = tmp_path / "new-extension64"
    frozen = cases.build(output)
    manifest, targets = load_corpus(output)
    assert frozen["case_count"] == len(manifest["pages"]) == len(targets["pages"]) == 64
    assert sum(not page["tables"] for page in targets["pages"]) == 8
    assert frozen["existing_corpora_read"] is False
    assert frozen["references_read_for_menus"] is False
    assert frozen["hosted_calls"] == 0
    assert frozen["synthetic_stress_counts"]["wrapped_continuation_shift"] >= 8
    for page in manifest["pages"]:
        menu = json.loads((output / "menus" / (page["id"] + ".json")).read_bytes())
        assert set(menu) == {"version", "id", "source_sha256", "baseline", "candidates", "omitted_context_counts",
                             "candidate_admission", "references_used", "source", "rules"}
        assert sha(canonical(menu["source"])) == menu["source_sha256"]
        assert "construction_cells" not in str(menu)
        assert "treatment" not in str(menu)
        assert "family" not in menu
        assert len(menu["candidates"]) <= cases.MAX_CANDIDATES
        assert len({candidate["id"] for candidate in menu["candidates"]}) == len(menu["candidates"])
        validate(menu["source"], menu["baseline"])
        for candidate in menu["candidates"]:
            validate(menu["source"], candidate["state"])
    with pytest.raises(FileExistsError, match="New versioned"):
        cases.build(output)


def test_menu_refuses_unknown_or_duplicate_ids_before_candidate_generation() -> None:
    source = {"page_size": [0, 0, 612, 792], "words": [{"id": "observed", "text": "$10.00", "bbox": [1, 1, 9, 9]}]}
    state = {"id": "c0", "tables": [], "unresolved_ids": ["observed", "observed"]}
    with pytest.raises(ValueError, match="exactly one owner"):
        cases.candidate_menu(source, [state], "opaque")
    state["unresolved_ids"] = ["missing"]
    with pytest.raises(ValueError, match="exactly one owner"):
        cases.candidate_menu(source, [state], "opaque")
