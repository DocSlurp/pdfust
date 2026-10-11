"""Pin literal ownership and conservation independently of candidate regeneration."""

import copy
from pathlib import Path
from typing import Any

import pytest
from bench import p003_rolling_candidate_audit as audit


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    """Include nonempty word strings to catch Counter(dict) versus Counter(keys)."""
    source = {
        "id": "case",
        "words": [{"id": "w0", "text": "North"}, {"id": "w1", "text": "depot"}, {"id": "w2", "text": "Footer"}],
    }
    alternative = {
        "source_words": copy.deepcopy(source["words"]),
        "unresolved_ids": ["w2"],
        "candidates": [
            {
                "row_count": 1,
                "col_count": 1,
                "values": [["North depot"]],
                "spans": [],
                "header_role": "unknown",
                "cells": [{"role": "unknown", "source_ids": ["w0", "w1"]}],
            }
        ],
    }
    return source, alternative


def test_exact_source_join_and_counter_keys() -> None:
    source, alternative = fixture()
    row = audit.admit_alternative(source, alternative)
    assert row["tables"][0]["values"] == [["North depot"]]
    assert row["owned_source_ids"] == 2
    assert row["unresolved_source_ids"] == 1


@pytest.mark.parametrize("change", ["duplicate", "missing", "replacement", "ordering", "foreign", "role", "source"])
def test_refuses_changed_ownership(change: str) -> None:
    source, alternative = fixture()
    candidate = alternative["candidates"][0]
    if change == "duplicate":
        alternative["unresolved_ids"].append("w0")
    elif change == "missing":
        alternative["unresolved_ids"].clear()
    elif change == "replacement":
        candidate["values"] = [["South depot"]]
    elif change == "ordering":
        candidate["cells"][0]["source_ids"].reverse()
    elif change == "foreign":
        candidate["cells"][0]["source_ids"].append("w3")
    elif change == "role":
        candidate["cells"][0]["role"] = "header"
    else:
        alternative["source_words"][0]["text"] = "Other"
    with pytest.raises(ValueError, match=r"required|differs"):
        audit.admit_alternative(source, alternative)


def test_prepare_fresh_directory_before_source_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object) -> None:
        pytest.fail("Opened original artifacts before refusing an existing output")

    monkeypatch.setattr(audit, "pinned", forbidden)
    with pytest.raises(FileExistsError):
        audit.prepare(tmp_path / "original", tmp_path / "corpus", tmp_path)


def test_score_authority_before_plan_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trust = tmp_path / "trust.json"
    trust.write_text("{}")

    def forbidden(*_args: object) -> None:
        pytest.fail("Opened plan before independent code authority")

    monkeypatch.setattr(audit, "pinned", forbidden)
    with pytest.raises(ValueError, match="Independent current helper authority"):
        audit.audit(tmp_path / "plan", tmp_path / "out", plan_sha256="bad", trusted_code=trust, targets_sha256="bad")
