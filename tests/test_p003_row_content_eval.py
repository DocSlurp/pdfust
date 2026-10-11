"""Evaluation cannot interpret targets before source admission."""

from __future__ import annotations

from pathlib import Path

import pytest
from bench import p003_row_content_eval as evaluation


def test_incomplete_authority_refuses_before_target_access(tmp_path: Path) -> None:
    authority = tmp_path / "code.json"
    authority.write_text("{}")
    with pytest.raises(ValueError, match="current helper authority"):
        evaluation.verify(tmp_path / "no-source", "0" * 64, authority)


def test_source_refusal_stops_evaluation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(_prepared: Path, _digest: str, _authority: Path) -> None:
        message = "source refusal before targets"
        raise ValueError(message)

    monkeypatch.setattr(evaluation, "verify", refuse)
    with pytest.raises(ValueError, match="source refusal"):
        evaluation.evaluate(tmp_path / "no-source", "0" * 64, tmp_path / "no-authority", tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_existing_output_refuses_before_replay(tmp_path: Path) -> None:
    with pytest.raises(FileExistsError, match="Fresh evaluation"):
        evaluation.evaluate(tmp_path / "no-source", "0" * 64, tmp_path / "no-authority", tmp_path)
