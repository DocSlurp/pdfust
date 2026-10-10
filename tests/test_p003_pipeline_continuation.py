"""Offline continuation admission and accounting invariants."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_pipeline_continuation as continuation
from bench.silver import sha, write_json


def segment(tmp_path: Path, name: str, records: list[dict], *, code: bytes = b"# frozen\n") -> tuple[Path, Path]:
    directory = tmp_path / name
    directory.mkdir()
    (directory / "code").mkdir()
    (directory / "code" / "pipeline_run.py").write_bytes(code)
    frozen = {
        "config": {"campaign": "P003", "workers": 1, "processor": "regions", "model": "model-a", "run_id": name},
        "records": records,
        "code_sha256": {"pipeline_run.py": sha(code)},
        "manifest_sha256": "pending",
    }
    write_json(directory / "frozen.json", frozen)
    trusted = tmp_path / (name + "-trusted.json")
    write_json(trusted, frozen["code_sha256"])
    return directory, trusted


def records(tmp_path: Path) -> list[dict]:
    pdf = tmp_path / "input.pdf"
    pdf.write_bytes(b"original PDF identity")
    return [
        {"id": ident, "pdf_path": str(pdf), "pdf_sha256": sha(pdf.read_bytes()), "page_number": index}
        for index, ident in enumerate(("a", "b", "c", "d"))
    ]


def result(directory: Path, ident: str, status: str) -> dict:
    row = {
        "id": ident,
        "status": status,
        "calls": [],
        "tables": [],
        "error_type": "OriginalError" if status == "error" else None,
    }
    write_json(directory / (ident + "-result.json"), row)
    return row


def manifest(tmp_path: Path, directory: Path, rows: list[dict]) -> Path:
    path = tmp_path / "manifest.json"
    write_json(path, {"split": "DEV", "schema": 1, "pages": rows})
    frozen = json.loads((directory / "frozen.json").read_bytes())
    frozen["manifest_sha256"] = sha(path.read_bytes())
    write_json(directory / "frozen.json", frozen)
    return path


def test_prepare_only_unattempted_preserves_errors_and_invalid_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = records(tmp_path)
    directory, trust = segment(tmp_path, "original", rows)
    result(directory, "a", "error")
    result(directory, "b", "ok")
    write_json(directory / "c-request-0.json", {"state": "retained interrupted evidence"})
    source_manifest = manifest(tmp_path, directory, rows)

    def invalid(*_args: object, **_kwargs: object) -> None:
        message = "Source ownership mismatch"
        raise ValueError(message)

    monkeypatch.setattr(continuation, "verify_output", invalid)
    summary = continuation.prepare(directory, trust, source_manifest, tmp_path / "plan")
    assert summary["remaining_ids"] == ["d"]
    assert summary["blocked_ids"] == ["b", "c"]
    assert summary["status_counts"] == {
        "completed_error": 1,
        "invalid_completed_output": 1,
        "interrupted_artifacts": 1,
        "clean_missing": 1,
    }
    subset = json.loads((tmp_path / "plan" / "manifest.json").read_bytes())
    assert [{key: row[key] for key in continuation.FIELDS} for row in subset["pages"]] == [rows[3]]
    plan = json.loads((tmp_path / "plan" / "plan.json").read_bytes())
    assert plan["original"]["pages"][0]["result"]["error_type"] == "OriginalError"
    assert plan["no_paid_calls"]
    assert not plan["automatic_retries"]
    with pytest.raises(FileExistsError):
        continuation.prepare(directory, trust, source_manifest, tmp_path / "plan")


def test_authentication_rejects_source_code_and_manifest_changes(tmp_path: Path) -> None:
    rows = records(tmp_path)
    directory, trust = segment(tmp_path, "original", rows)
    source_manifest = manifest(tmp_path, directory, rows)
    with pytest.raises(ValueError, match="trusted"):
        continuation.authenticate(directory, {"pipeline_run.py": "untrusted"})
    Path(rows[0]["pdf_path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="PDF"):
        continuation.authenticate(directory, json.loads(trust.read_bytes()))
    Path(rows[0]["pdf_path"]).write_bytes(b"original PDF identity")
    source_manifest.write_bytes(b'{"split":"DEV","pages":[]}')
    with pytest.raises(ValueError, match="manifest"):
        continuation.prepare(directory, trust, source_manifest, tmp_path / "plan")


def test_original_and_continuation_bytes_costs_unknown_and_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = records(tmp_path)[:2]
    first, first_trust = segment(tmp_path, "first", rows)
    second, second_trust = segment(tmp_path, "second", rows[1:])
    old = result(first, "a", "error")
    good = result(second, "b", "ok")
    (second / "b.md").write_bytes(b"literal retained markdown\n")
    monkeypatch.setattr(continuation, "verify_output", lambda *_a, **_k: {"operational": True})
    specs = [
        {"directory": str(first), "trusted_code": str(first_trust)},
        {"directory": str(second), "trusted_code": str(second_trust)},
    ]
    combined = continuation.combine(specs, tmp_path / "combined")
    assert combined["results"] == [old, good]
    assert combined["effective_usd"] is None
    assert combined["metrics"]["cpu_seconds"] is None
    assert combined["pages_per_minute"] is None
    assert combined["continuation_status"] == "complete"
    assert (tmp_path / "combined" / "a-result.json").read_bytes() == (first / "a-result.json").read_bytes()
    assert (tmp_path / "combined" / "b.md").read_bytes() == (second / "b.md").read_bytes()
    with pytest.raises(ValueError, match="Duplicate segment"):
        continuation.combine([specs[0], specs[0]], tmp_path / "duplicated")
    result(second, "a", "error")  # Outside frozen source inventory is not adopted.
    third, third_trust = segment(tmp_path, "retry", rows[:1])
    result(third, "a", "ok")
    with pytest.raises(ValueError, match="repeated"):
        continuation.combine(
            [*specs, {"directory": str(third), "trusted_code": str(third_trust)}], tmp_path / "retry-out"
        )


def test_explicit_segment_measurements_sum_once_peak_max_and_model_fixed(tmp_path: Path) -> None:
    rows = records(tmp_path)[:2]
    specs = []
    for index, row in enumerate(rows):
        directory, trusted = segment(tmp_path, "segment" + str(index), rows if index == 0 else [row])
        result(directory, row["id"], "error")
        specs.append(
            {
                "directory": str(directory),
                "trusted_code": str(trusted),
                "measurement": {
                    "source": "root measured terminated segment",
                    "metrics": {
                        "wall_seconds": 10 + index,
                        "cpu_seconds": 2 + index,
                        "peak_sampled_rss_bytes": 100 + index,
                    },
                    "effective_usd": 0.1 + index,
                    "accounted_usd": 0.2 + index,
                },
            }
        )
    report = continuation.combine(specs, tmp_path / "out")
    assert report["metrics"]["wall_seconds"] == 21
    assert report["metrics"]["cpu_seconds"] == 5
    assert report["metrics"]["peak_sampled_rss_bytes"] == 101
    assert report["effective_usd"] == pytest.approx(1.2)
    changed = Path(specs[1]["directory"]) / "frozen.json"
    frozen = json.loads(changed.read_bytes())
    frozen["config"]["model"] = "another-model"
    write_json(changed, frozen)
    with pytest.raises(ValueError, match="model or treatment"):
        continuation.combine(specs, tmp_path / "wrong-model")


def test_interrupted_page_cannot_be_silently_retried(tmp_path: Path) -> None:
    rows = records(tmp_path)[:1]
    first, trusted_first = segment(tmp_path, "interrupted", rows)
    second, trusted_second = segment(tmp_path, "later", rows)
    write_json(first / "a-request-0.json", {"state": "not completed"})
    result(second, "a", "error")
    with pytest.raises(ValueError, match="Interrupted page"):
        continuation.combine(
            [
                {"directory": str(first), "trusted_code": str(trusted_first)},
                {"directory": str(second), "trusted_code": str(trusted_second)},
            ],
            tmp_path / "out",
        )


def proof_for(tmp_path: Path, directory: Path, trust: Path, ident: str, entries: list[dict]) -> Path:
    original = continuation.authenticate(directory, json.loads(trust.read_bytes()))
    page = next(p for p in original["pages"] if p["record"]["id"] == ident)
    captured = tmp_path / "captured-ledger.json"
    write_json(captured, {"requests": entries})
    path = tmp_path / "root-attestation.json"
    write_json(
        path,
        {
            "schema": 1,
            "kind": "root_prepared_never_transmitted",
            "root_reviewed": True,
            "audit_description": "Root captured stopped ledger and verified no admission for exact page prefix",
            "segment_directory": str(directory.resolve()),
            "run_id": original["frozen"]["config"]["run_id"],
            "frozen_sha256": original["artifact_sha256"]["frozen.json"],
            "code_sha256": original["frozen"]["code_sha256"],
            "ledger_snapshot": {"path": str(captured), "sha256": sha(captured.read_bytes())},
            "pages": [
                {
                    "id": ident,
                    "record": page["record"],
                    "artifacts": page["artifacts"],
                    "tag_prefix": f"P003/{directory.name}/{ident}/",
                    "ledger_entry_count": 0,
                }
            ],
        },
    )
    return path


def test_known_unsupported_completed_and_explicit_never_transmitted(tmp_path: Path) -> None:
    rows = records(tmp_path)
    directory, trust = segment(tmp_path, "original", rows)
    result(directory, "a", "unsupported_no_text")
    write_json(directory / "b-request-0.json", {"model": "model-a", "state": "literal"})
    source_manifest = manifest(tmp_path, directory, rows)
    assert (
        continuation.authenticate(directory, json.loads(trust.read_bytes()))["pages"][0]["status"] == "completed_error"
    )
    proof = proof_for(tmp_path, directory, trust, "b", [])
    plan = continuation.prepare(directory, trust, source_manifest, tmp_path / "approved", never_transmitted=proof)
    assert plan["remaining_ids"] == ["b", "c", "d"]
    assert plan["status_counts"]["prepared_never_transmitted"] == 1
    assert not plan["automatic_retries"]


@pytest.mark.parametrize("mutation", ["entry", "response", "source", "snapshot", "prefix", "request"])
def test_never_transmitted_proof_rejects_admission_or_identity_changes(tmp_path: Path, mutation: str) -> None:
    rows = records(tmp_path)
    directory, trust = segment(tmp_path, "original", rows)
    write_json(directory / "b-request-0.json", {"state": "literal"})
    proof = proof_for(tmp_path, directory, trust, "b", [{"tag": "P003/original/b/0"}] if mutation == "entry" else [])
    data = json.loads(proof.read_bytes())
    if mutation == "response":
        write_json(directory / "b-response-0.json", {"answers": {}})
    elif mutation == "source":
        data["pages"][0]["record"]["page_number"] = 99
    elif mutation == "snapshot":
        Path(data["ledger_snapshot"]["path"]).write_text('{"requests": [{"tag": "new"}]}')
    elif mutation == "prefix":
        data["pages"][0]["tag_prefix"] = "P003/another/b/"
    elif mutation == "request":
        write_json(directory / "b-request-0.json", {"state": "changed"})
    write_json(proof, data)
    with pytest.raises(ValueError, match=r"proof|identity"):
        continuation.authenticate(directory, json.loads(trust.read_bytes()), never_transmitted=proof)


def test_combine_requires_revalidated_never_transmitted_proof(tmp_path: Path) -> None:
    rows = records(tmp_path)
    original, trust = segment(tmp_path, "original", rows)
    write_json(original / "b-request-0.json", {"state": "literal"})
    proof = proof_for(tmp_path, original, trust, "b", [])
    later, later_trust = segment(tmp_path, "later", [rows[1]])
    result(later, "b", "error")
    specs = [
        {"directory": str(original), "trusted_code": str(trust)},
        {"directory": str(later), "trusted_code": str(later_trust)},
    ]
    with pytest.raises(ValueError, match="Interrupted"):
        continuation.combine(specs, tmp_path / "blocked")
    specs[0]["never_transmitted"] = str(proof)
    combined = continuation.combine(specs, tmp_path / "combined")
    assert combined["results"][0]["id"] == "b"
