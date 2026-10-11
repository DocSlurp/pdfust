"""Check frozen mixed-selector scope and source-only authorization gates."""

import copy
from pathlib import Path

import pytest
from bench import p003_mixed_candidate_audit as audit


def inventory() -> list[dict[str, str]]:
    """Construct distinct explicit identities without reading retained artifacts."""
    return [{"name": n, "family": "candidate", "report_sha256": str(i)} for i, n in enumerate(sorted(audit.names()))]


def test_explicit_inventory() -> None:
    assert len(audit.names()) == audit.ARM_COUNT
    audit.validate_inventory(inventory())


@pytest.mark.parametrize("change", ["omission", "duplicate_name", "duplicate_report", "gate"])
def test_inventory_refuses_scope_changes(change: str) -> None:
    rows = copy.deepcopy(inventory())
    if change == "omission":
        rows.pop()
    elif change == "duplicate_name":
        rows[-1]["name"] = rows[0]["name"]
    elif change == "duplicate_report":
        rows[-1]["report_sha256"] = rows[0]["report_sha256"]
    else:
        rows[-1]["family"] = "gate"
    with pytest.raises(ValueError, match=r"required|identities"):
        audit.validate_inventory(rows)


def test_prepare_fresh_directory_before_artifact_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object) -> None:
        pytest.fail("Preparation opened artifacts before rejecting existing output")

    monkeypatch.setattr(audit, "pinned", forbidden)
    with pytest.raises(FileExistsError):
        audit.prepare(tmp_path / "queue", tmp_path / "plan", tmp_path)


def test_score_requires_external_authority_before_plan_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trust = tmp_path / "trust.json"
    trust.write_text("{}")

    def forbidden(*_args: object) -> None:
        pytest.fail("Scoring opened plan before checking external authority")

    monkeypatch.setattr(audit, "pinned", forbidden)
    with pytest.raises(ValueError, match="Independent current helper authority"):
        audit.audit(tmp_path / "plan", tmp_path / "output", plan_sha256="bad", trusted_code=trust)
