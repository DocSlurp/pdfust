"""R001 atomic source ownership, candidate ceiling and scorer-only gold checks."""

from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest
from bench.decision_context_cases import context_cases
from bench.decision_rows import (
    build_request,
    materialize_assignments,
    parse_response,
    pilot_case,
    project_input,
    score_response,
)


@pytest.fixture(scope="module")
def pilots() -> list[dict]:
    """Adapt only existing authored thirty-case DEV PDFs, without inference."""
    return [pilot_case(case) for case in context_cases()]


def response(pilot: dict, assignments: dict | None = None) -> dict:
    """Create a native choice response selecting exactly the specified assignments."""
    assignments = pilot["expected_assignments"] if assignments is None else assignments
    body = build_request(pilot["input"], "test-model")
    answers = {}
    for index, fragment in enumerate(pilot["input"]["fragments"]):
        slot = assignments[fragment["id"]]
        chosen = "unassigned" if slot is None else f"slot{fragment['allowed_slots'].index(slot)}"
        answers[f"q{index}"] = {
            "type": "choice",
            "choice": chosen,
            "probabilities": {key: float(key == chosen) for key in body["questions"][f"q{index}"]["criteria"]},
        }
    return {"answers": answers}


def test_all_thirty_candidates_cover_existing_gold(pilots: list[dict]) -> None:
    for pilot in pilots:
        result = score_response(pilot, response(pilot))
        assert result["candidate_coverage"] == 1.0
        assert result["candidate_complete"]
        assert result["selector_exact"]
        assert result["region_exact"]
        assert result["record_f1"] == 1.0
        assert result["source_conservation"]
        assert result["headers_immutable"]


def test_gold_and_private_metadata_cannot_enter_model_body(pilots: list[dict]) -> None:
    pilot = pilots[0]
    body = build_request(pilot["input"], "test-model")
    altered = deepcopy(pilot)
    altered["expected_assignments"] = {"private": "GOLD_SENTINEL"}
    altered["original_case"]["gold"] = {"private": "GOLD_SENTINEL"}
    altered["case_id"] = "GOLD_SENTINEL"
    altered["input"]["gold"] = "GOLD_SENTINEL"
    for word in altered["input"]["words"]:
        word["gold"] = "GOLD_SENTINEL"
    assert body == build_request(altered["input"], "test-model")
    assert "GOLD_SENTINEL" not in json.dumps(body)
    assert set(body["questions"]) == {"q0", "q1", "q2"}
    assert all(len(question["criteria"]) == 5 for question in body["questions"].values())


def test_wrap_and_separate_records(pilots: list[dict]) -> None:
    joined = score_response(pilots[0], response(pilots[0]))["assembly"]
    split = score_response(pilots[1], response(pilots[1]))["assembly"]
    assert len(joined["records"]) == 1
    assert len(split["records"]) == 2
    assert (
        joined["records"][0]["row_key_ids"]
        == pilots[0]["input"]["fragments"][0]["source_ids"] + pilots[0]["input"]["fragments"][1]["source_ids"]
    )
    assert split["records"][1]["value_ids"] == []
    assert joined["records"][0]["header_path"] == [pilots[0]["input"]["headers"][1]["source_ids"]]


@pytest.mark.parametrize(
    "mutation", ["duplicate-word", "duplicate-fragment-source", "unknown-source", "header-move", "unknown-header"]
)
def test_invalid_source_and_header_mutations_rejected(pilots: list[dict], mutation: str) -> None:
    spec = deepcopy(pilots[0]["input"])
    if mutation == "duplicate-word":
        spec["words"].append(deepcopy(spec["words"][0]))
    elif mutation == "duplicate-fragment-source":
        spec["fragments"][1]["source_ids"].append(spec["fragments"][0]["source_ids"][0])
    elif mutation == "unknown-source":
        spec["fragments"][0]["source_ids"][0] = 99999
    elif mutation == "header-move":
        source = spec["headers"][0]["source_ids"].pop()
        spec["fragments"][0]["source_ids"].append(source)
    else:
        spec["columns"][1]["header_path"] = [[99999]]
    with pytest.raises(ValueError, match=r"source|header|Source"):
        build_request(spec, "test-model")


def test_unassigned_conserves_every_source_and_preserves_headers(pilots: list[dict]) -> None:
    spec = pilots[0]["input"]
    assembly = materialize_assignments(spec, dict.fromkeys([f["id"] for f in spec["fragments"]]))
    assert assembly["records"] == []
    assert assembly["headers_immutable"]
    owned = [source for cell in assembly["cells"] for source in cell["source_ids"]] + assembly["unresolved_ids"]
    assert Counter(owned) == Counter(word["id"] for word in spec["words"])
    assert spec == pilots[0]["input"]


def test_unretained_slot_or_missing_assignment_rejected_atomically(pilots: list[dict]) -> None:
    pilot = deepcopy(pilots[0])
    spec_before = deepcopy(pilot["input"])
    assignments = deepcopy(pilot["expected_assignments"])
    assignments["tail"] = ["r999", "c0"]
    with pytest.raises(ValueError, match="unretained"):
        materialize_assignments(pilot["input"], assignments)
    assignments.pop("tail")
    with pytest.raises(ValueError, match="exactly cover"):
        materialize_assignments(pilot["input"], assignments)
    assert pilot["input"] == spec_before


@pytest.mark.parametrize("bad", ["missing", "extra", "unknown-choice", "bad-probability", "unsupported-header"])
def test_malformed_responses_are_not_partially_accepted(pilots: list[dict], bad: str) -> None:
    result = response(pilots[0])
    if bad == "missing":
        result["answers"].pop("q1")
    elif bad == "extra":
        result["answers"]["q3"] = deepcopy(result["answers"]["q0"])
    elif bad == "unknown-choice":
        result["answers"]["q0"]["choice"] = "new-row"
    elif bad == "bad-probability":
        result["answers"]["q0"]["probabilities"]["unassigned"] = float("nan")
    else:
        result["answers"]["q0"]["header_path"] = [[999]]
    score = score_response(pilots[0], result)
    assert score["valid"] is False
    assert "assembly" not in score
    with pytest.raises(ValueError, match=r"Response|response|Choice|choice|probability"):
        parse_response(pilots[0]["input"], result)


def test_candidate_ceiling_is_distinct_from_selector_accuracy(pilots: list[dict]) -> None:
    pilot = deepcopy(pilots[0])
    pilot["input"]["fragments"][1]["allowed_slots"] = [["r1", "c0"]]
    assignments = deepcopy(pilot["expected_assignments"])
    assignments["tail"] = ["r1", "c0"]
    score = score_response(pilot, response(pilot, assignments))
    assert score["candidate_complete"] is False
    assert score["candidate_coverage"] == pytest.approx(2 / 3)
    assert score["selector_accuracy"] == pytest.approx(2 / 3)
    assert score["region_exact"] is False


def test_generic_context_and_optional_png(pilots: list[dict]) -> None:
    spec = deepcopy(pilots[0]["input"])
    spec["context"] = {"notes": "Literal source convention", "gold": "PRIVATE"}
    state = project_input(spec)
    assert state["context"] == {"notes": "Literal source convention"}
    with pytest.raises(ValueError, match="PNG"):
        build_request(spec, "test-model", {"data": b"invalid"})
    with pytest.raises(ValueError, match="Image"):
        build_request(spec, "test-model", {"data": "not-bytes"})


@pytest.mark.parametrize("edge", [128, 512, 1200])
def test_optional_native_image_mapping(tmp_path: Path, pilots: list[dict], edge: int) -> None:
    from bench.decision_image_matrix import VariantCache  # noqa: PLC0415

    pilot = pilots[0]
    image = VariantCache(tmp_path).make_variant(
        pilot["original_case"]["pdf_bytes"], [40, 155, 540, 225], edge=edge, mode="rgb8"
    )
    body = build_request(pilot["input"], "test-model", image=image)
    assert body["state"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert "Image maps display rectangle" in body["state"][0]
    assert len(body["questions"]) == 3


def test_pilot_dense_ids_remove_prior_note_offset(pilots: list[dict]) -> None:
    first = build_request(pilots[8]["input"], "test-model")
    second = build_request(pilots[9]["input"], "test-model")
    assert first == second
    assert [word["id"] for word in first["state"]["words"]] == list(range(len(first["state"]["words"])))


def test_fixed_header_and_data_cell_id_collision_rejected(pilots: list[dict]) -> None:
    spec = deepcopy(pilots[0]["input"])
    spec["headers"][0]["id"] = "row0-column0"
    with pytest.raises(ValueError, match="collide"):
        project_input(spec)


@pytest.mark.parametrize("split", ["HELD_OUT", "TEST", None])
def test_pilot_adapter_rejects_non_dev_metadata(split: str | None) -> None:
    case = deepcopy(context_cases()[0])
    case["split"] = split
    with pytest.raises(ValueError, match="only explicitly labeled DEV"):
        pilot_case(case)
