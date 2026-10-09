"""Source provenance and abstention gates for the optional visual experiment."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import pytest
from bench.lowlevel_ocr_alignment import (
    MAX_TEXT_BYTES,
    VisualFixture,
    _digest,
    build_evidence,
    character_edits,
    comparison_text,
    fixtures,
    score_action,
    validate_action,
)


def _evidence() -> dict[str, Any]:
    value: dict[str, Any] = {
        "fixture_id": "review",
        "source": {"path": "original.pdf", "sha256": "unused", "page": 0, "bbox": [0, 0, 10, 10]},
        "source_ids": [4, 5, 6],
        "source_text": "ED IS ON,",
        "native_words_text": "ED IS ON,",
        "allowed_actions": ["retain_source", "propose_visual_transcription", "abstain"],
    }
    value["evidence_sha256"] = _digest(value)
    return value


def _action(evidence: dict[str, Any], **changes: object) -> dict[str, Any]:
    value = {
        "fixture_id": evidence["fixture_id"],
        "evidence_sha256": evidence["evidence_sha256"],
        "source_ids": list(evidence["source_ids"]),
        "decision": "abstain",
        "proposed_text": None,
        "reason": "Scan is ambiguous.",
    }
    value.update(changes)
    return value


def test_visual_proposal_retains_source_without_replacement() -> None:
    evidence = _evidence()
    before = copy.deepcopy(evidence)
    result = validate_action(
        evidence,
        _action(
            evidence,
            decision="propose_visual_transcription",
            proposed_text="EDISON.",
            reason="Reviewed visible heading.",
        ),
    )
    assert evidence == before
    assert result["original_source_text"] == "ED IS ON,"
    assert result["visual_text_proposal"] == "EDISON."
    assert result["source_ids"] == [4, 5, 6]
    assert result["source_modified"] is False
    result["source_ids"].clear()
    result["source"]["path"] = "changed"
    result["source"]["bbox"][0] = 99
    assert evidence == before


@pytest.mark.parametrize(
    "changes",
    [
        {"source_ids": [4, 6]},
        {"source_ids": [6, 5, 4]},
        {"source_ids": [4, 5, True]},
        {"evidence_sha256": "stale"},
        {"fixture_id": "another"},
        {"decision": "replace_source"},
        {"decision": "retain_source", "proposed_text": "replacement"},
        {"proposed_text": "replacement"},
        {"decision": "propose_visual_transcription", "proposed_text": ""},
        {"decision": "propose_visual_transcription", "proposed_text": "字" * MAX_TEXT_BYTES},
        {"reason": ""},
        {"reason": "x" * (MAX_TEXT_BYTES + 1)},
        {"unexpected": True},
    ],
)
def test_refuse_unbound_partial_or_unbounded_action(changes: dict[str, Any]) -> None:
    evidence = _evidence()
    with pytest.raises(ValueError, match=r"action|source ID|evidence|visual proposal"):
        validate_action(evidence, _action(evidence, **changes))


def test_fingerprint_detects_evidence_tampering() -> None:
    evidence = _evidence()
    action = _action(evidence)
    evidence["source_text"] = "EDISON."
    with pytest.raises(ValueError, match="fingerprint"):
        validate_action(evidence, action)


@pytest.mark.parametrize("decision", ["retain_source", "abstain", "propose_visual_transcription"])
def test_unavailable_review_never_becomes_correctness(decision: str) -> None:
    evidence = _evidence()
    fixture = VisualFixture("review", "unused.pdf", "unused", 0, (0, 0, 10, 10), None, "Unreadable ink.")
    action = _action(evidence, decision=decision, proposed_text="guess" if decision.startswith("propose") else None)
    result = score_action(evidence, fixture, action)
    assert result["reference_status"] == "unavailable"
    assert result["proposal_exact_match"] is None
    assert result["source_character_edits"] is None


def test_whitespace_policy_does_not_hide_ocr_punctuation_or_case() -> None:
    assert comparison_text("  A\n B\t") == "A B"
    assert character_edits("ED IS ON,", "EDISON.") == 3
    assert character_edits("188O", "1880") == 1
    assert character_edits("A", "a") == 1
    assert character_edits("ﬁ", "fi") == 2
    with pytest.raises(ValueError, match="metric bound"):
        character_edits("x" * 1025, "x")


def test_wrong_reference_identity_is_refused() -> None:
    evidence = _evidence()
    fixture = VisualFixture("another", "unused.pdf", "unused", 0, (0, 0, 10, 10), "EDISON.", "Visible.")
    with pytest.raises(ValueError, match="different fixture"):
        score_action(evidence, fixture, _action(evidence))


def test_real_crop_is_independently_bound_and_keeps_invisible_spaces(tmp_path: Path) -> None:
    fixture = fixtures()[0]
    evidence = build_evidence(fixture, tmp_path)
    assert "visual_text" not in evidence
    assert "review_note" not in evidence
    assert evidence["source"]["sha256"] == fixture.source_sha256
    assert hashlib.sha256(Path(evidence["source"]["path"]).read_bytes()).hexdigest() == fixture.source_sha256
    assert "ED IS ON," in evidence["source_text"]
    assert all(row[9] == "invisible" for row in evidence["source_glyph_rows"])
    assert evidence["source_ids"] == [row[0] for row in evidence["source_glyph_rows"]]
    assert Path(evidence["image"]["path"]).is_file()
    result = score_action(
        evidence,
        fixture,
        _action(
            evidence,
            decision="propose_visual_transcription",
            proposed_text=fixture.visual_text,
            reason="Single reviewer demo.",
        ),
    )
    assert result["proposal_exact_match"] is True
    assert result["words_character_edits"] == 3
    assert "ED IS ON," in result["original_source_text"]


def test_wrong_visual_proposal_is_not_scored_as_repair() -> None:
    evidence = _evidence()
    fixture = VisualFixture("review", "unused.pdf", "unused", 0, (0, 0, 10, 10), "EDISON.", "Visible heading.")
    result = score_action(
        evidence,
        fixture,
        _action(
            evidence, decision="propose_visual_transcription", proposed_text="EDISON,", reason="Wrong punctuation demo."
        ),
    )
    assert result["proposal_exact_match"] is False
    assert result["original_source_text"] == evidence["source_text"]


def test_changed_natural_source_is_refused_before_interpretation(tmp_path: Path) -> None:
    original = fixtures()[0]
    changed = VisualFixture(
        original.id,
        original.filename,
        "0" * 64,
        original.page,
        original.bbox,
        original.visual_text,
        original.review_note,
    )
    with pytest.raises(ValueError, match="source hash changed"):
        build_evidence(changed, tmp_path)
    assert not list(tmp_path.iterdir())


def test_reference_hash_is_bound_beyond_fixture_label() -> None:
    evidence = _evidence()
    fixture = VisualFixture("review", "unused.pdf", "different", 0, (0, 0, 10, 10), "EDISON.", "Visible.")
    with pytest.raises(ValueError, match="reference provenance"):
        score_action(evidence, fixture, _action(evidence))
