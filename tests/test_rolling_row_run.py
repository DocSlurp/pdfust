"""Frozen source admission and persistent mock-ledger lifecycle, without credentials."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.rolling_row_run import MODELS, TAG_PREFIX, run, verify, wave_admission
from bench.rolling_rows import admission_request, assemble, freeze, freeze_admission, selected_candidate


def page() -> dict:
    words = [
        {
            "id": f"w{r}-{c}",
            "text": f"{r}{c}" if r else f"Header{c}",
            "bbox": [10 + 100 * c, 20 + 40 * r, 30 + 100 * c, 30 + 40 * r],
        }
        for r in range(4)
        for c in range(3)
    ]
    return {"id": "page0", "page_size": [0, 0, 300, 500], "words": words, "vector_candidates": []}


@pytest.fixture
def frozen(tmp_path: Path) -> tuple[Path, Path]:
    image_module = pytest.importorskip("PIL.Image")
    source = page()
    image = tmp_path / "source.png"
    image_module.new("RGB", (600, 1000), "white").save(image)
    source["image_path"] = str(image)
    path = tmp_path / "sources.json"
    path.write_text(json.dumps({"pages": [source]}))
    candidates = tmp_path / "candidates.json"
    freeze(path, candidates)
    directory = tmp_path / "admission"
    freeze_admission(path, candidates, directory, list(MODELS))
    expected = assemble(source, "rolling")["candidates"][0]
    targets = tmp_path / "scorer-only.json"
    targets.write_text(json.dumps([{"id": "page0", "kind": "borderless", "tables": [expected]}]))
    return directory, targets


class Client:
    """Keep a synthetic persistent ledger without transport or credentials."""

    def __init__(self, directory: Path, *, fail: bool = False) -> None:
        """Create an isolated mock ledger."""
        self.ledger = directory / "ledger.json"
        self.fail = fail
        self.calls = 0

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict:
        """Return a one-hot source candidate choice or retain a simulated failure."""
        self.calls += 1
        assert max_body_bytes == 750_000
        entries = json.loads(self.ledger.read_text())["requests"] if self.ledger.exists() else []
        entry = {
            "index": len(entries),
            "tag": tag,
            "requested_model": body["model"],
            "accounted_usd": 0.30,
            "cost_status": "reserved",
            "request_sha256": hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest(),
        }
        if self.fail:
            entries.append(entry)
            self.ledger.write_text(json.dumps({"requests": entries}))
            raise RuntimeError("Mock retained failure")
        entry.update(accounted_usd=0.000001, provider_reported_usd=0.000001, response_file="mock", elapsed_ms=2)
        entries.append(entry)
        self.ledger.write_text(json.dumps({"requests": entries}))
        choices = body["questions"]["q0"]["criteria"]
        result = {
            "usage": {"cost": 0.000001, "input_tokens": 1, "output_tokens": 1},
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": "rolling",
                    "probabilities": {key: float(key == "rolling") for key in choices},
                }
            },
        }
        return {"entry": entry, "result": result, "replayed": False}


def test_duplicate_physical_alias_excluded_and_selection_conserves_sources() -> None:
    source = page()
    alternatives = [assemble(source, variant) for variant in ("physical", "rolling")]
    body = admission_request(source, alternatives, MODELS[0])
    assert set(body["questions"]["q0"]["criteria"]) == {"rolling", "not_table", "unresolved"}
    result = selected_candidate(source, alternatives, "not_table")
    assert result["tables"] == []
    assert result["unresolved_ids"] == [w["id"] for w in source["words"]]
    with pytest.raises(ValueError, match="menu"):
        selected_candidate(source, alternatives, "physical")


def test_successful_fake_client_completes_cohorts(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    directory, targets = frozen
    client = Client(tmp_path)
    result = run(directory, targets, client)
    assert client.calls == 4
    assert result["unique_requests"] == 4
    assert result["effective_usd"] == pytest.approx(0.000004)
    assert result["source_conservation"]
    assert all(c["slices"]["borderless"]["exact_page"] == 1 for c in result["cohorts"].values())
    run(directory, targets, client)
    assert client.calls == 4


def test_failure_is_persistent_and_budget_never_retries(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    directory, targets = frozen
    client = Client(tmp_path, fail=True)
    result = run(directory, targets, client)
    assert client.calls == 1
    assert result["stopped_models"] == [MODELS[0]]
    assert result["budget_stopped"]
    assert result["effective_usd"] is None
    run(directory, targets, client)
    assert client.calls == 1


def test_tampered_body_refused_before_client(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    directory, targets = frozen
    manifest = verify(directory)
    path = directory / manifest["records"][0]["request"]
    path.write_text("{}")
    client = Client(tmp_path)
    with pytest.raises(ValueError, match="changed"):
        run(directory, targets, client)
    assert client.calls == 0


def test_persistent_prefix_budget_is_separate_from_other_waves() -> None:
    wave_admission([{"tag": "other-wave", "accounted_usd": 20}])
    with pytest.raises(RuntimeError, match="cap"):
        wave_admission([{"tag": TAG_PREFIX + "old", "accounted_usd": 0.21}])


def test_admission_gold_metadata_perturbation_invariance() -> None:
    source = page()
    alternatives = [assemble(source, variant) for variant in ("physical", "rolling")]
    before = admission_request(source, alternatives, MODELS[0])
    modified = deepcopy(source)
    for key in ("gold", "family", "template", "expected_document", "id"):
        modified[key] = "SECRET_ANSWER"
    assert admission_request(modified, alternatives, MODELS[0]) == before
    assert "SECRET_ANSWER" not in json.dumps(before)


def test_ambiguous_target_is_never_scored_as_a_true_negative() -> None:
    from bench.rolling_row_run import target_score  # noqa: PLC0415

    target = {"kind": "ambiguous", "tables": [], "truth_status": "ambiguous-unscored"}
    assert all(value is None for value in target_score(target, []).values())
    assert all(value is None for value in target_score(target, [{"arbitrary": "proposal"}]).values())


def test_ambiguous_cohort_records_cost_without_binary_scores(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    directory, targets = frozen
    targets.write_text(json.dumps([{"id": "page0", "kind": "ambiguous", "tables": []}]))
    result = run(directory, targets, Client(tmp_path))
    assert result["unique_requests"] == 4
    for cohort in result["cohorts"].values():
        assert cohort["ambiguous_unscored_pages"] == 1
        assert cohort["slices"]["prose"]["pages"] == 0
        assert cohort["slices"]["borderless"]["pages"] == 0
        assert cohort["rows"][0]["scores"]["exact_page"] is None
        assert cohort["rows"][0]["conservation"]
    assert all(row["text_group_exact"] is None for row in result["candidate_ceiling_rows"])
