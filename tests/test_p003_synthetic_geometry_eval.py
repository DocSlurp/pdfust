"""Independent geometry replay refuses corruption before evaluation labels."""
# ruff: noqa: PERF401

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from bench import p003_synthetic_geometry_eval as audit
from bench.silver import sha

MAIN = Path("/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003")
CONTROL = Path(
    "/home/dan/code/oss/jev-pdf-p003-synthetic-geometry/bench/results/pdf-master-artifacts/p003-synthetic-geometry-v2"
)
FROZEN = "fc956db68477638b347603268e6d91422236de293cfbea0d20acc38463b16691"
AUTH = MAIN / "trusted-code/synthetic-geometry-v2.json"


@pytest.fixture(scope="module")
def context() -> dict:
    return audit.evaluation.source_context(
        MAIN / "synthetic-micro-relations-v2", MAIN / "trusted-code/synthetic-micro-relations-v2.json"
    )


def test_complete_source_only_replay96(context: dict) -> None:
    verified = audit.verify(CONTROL, AUTH, FROZEN, context)
    assert len(verified["rows"]) == 96
    assert sum(r["status"] == "classified" for r in verified["rows"]) == 38
    assert verified["verification"].endswith("before gold")
    with pytest.raises(ValueError, match="separately supplied"):
        audit.verify(CONTROL, AUTH, "0" * 64, context)


def test_recomputed_freeze_hash_cannot_hide_modified_outcome(tmp_path: Path, context: dict) -> None:
    copied = tmp_path / "control"
    copied.mkdir()
    (copied / "sources").mkdir()
    (copied / "code").mkdir()
    for name in ("frozen.json", "results.json", "report.json"):
        shutil.copyfile(CONTROL / name, copied / name)
    for name in audit.CODE:
        shutil.copyfile(CONTROL / "code" / name, copied / "code" / name)
    for record in context["records"]:
        name = record["id"] + ".json"
        shutil.copyfile(CONTROL / "sources" / name, copied / "sources" / name)
    value = json.loads((copied / "results.json").read_bytes())
    value["results"][0]["choice"] = "invented"
    (copied / "results.json").write_text(json.dumps(value))
    frozen = json.loads((copied / "frozen.json").read_bytes())
    frozen["results_sha256"] = sha((copied / "results.json").read_bytes())
    (copied / "frozen.json").write_text(json.dumps(frozen))
    with pytest.raises(ValueError, match="source-only replay"):
        audit.verify(copied, AUTH, sha((copied / "frozen.json").read_bytes()), context)


def test_score_keeps_abstentions_refusals_and_unobservable_denominators() -> None:
    rows, gold = [], {}
    for index in range(24):
        identifier = "opaque" + str(index)
        gold[identifier] = {"expected_choice": "same", "evidence_limitation": index < 6}
        for treatment in audit.control.TREATMENTS:
            rows.append(
                {
                    "id": identifier,
                    "kind": ("cell", "row", "wrap")[index % 3],
                    "treatment": treatment,
                    "status": "classified" if index < 3 else "source_refused" if index == 3 else "abstained",
                    "choice": "same" if index < 2 else "separate" if index == 2 else "unresolved",
                }
            )
    context = {"frozen": {"counterfactual_twins": []}}
    report = audit.score({"rows": rows}, gold, context)
    for treatment in report["treatments"].values():
        assert treatment["all_24"]["intended_count"] == 24
        assert treatment["all_24"]["author_label_matches"] == 2
        assert treatment["all_24"]["source_refused_count"] == 1
        assert treatment["all_24"]["conditional_classified_author_label_fraction"] == 2 / 3
        assert treatment["visually_cued_18"]["intended_count"] == 18
        assert treatment["indeterminate_6"]["intended_count"] == 6
    assert report["full_pipeline_rate"] is None
