"""Synthetic-fixture tests for the image/gate Langfuse adapter (no network, no retained artifacts)."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

import pytest
from bench.langfuse_adapters import image_gates
from bench.langfuse_adapters.base import clean_scores, validate

if TYPE_CHECKING:
    from pathlib import Path

PDF = b"%PDF-1.7 synthetic"
PDF_SHA = hashlib.sha256(PDF).hexdigest()


def _write(path: Path, value: Any) -> None:  # noqa: ANN401 - arbitrary JSON fixture.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _observation(case_id: str, *, exact: bool, choice: str = "A") -> dict[str, Any]:
    value = 1.0 if exact else 0.0
    return {
        "case_id": case_id,
        "answer": {"choice": choice, "probabilities": {choice: 1.0}},
        "assembly": {"records": [], "unresolved_ids": []},
        "score": {
            "valid": True,
            "source_conservation": True,
            "region_exact": exact,
            "record_precision": value,
            "record_recall": value,
            "record_f1": value,
        },
    }


def _batch(model: str, arm: str, offset: int, case_ids: list[str], sha: str) -> dict[str, Any]:
    return {
        "model": model,
        "scope": "page",
        "arm": arm,
        "offset": offset,
        "case_ids": case_ids,
        "source_sha256": [PDF_SHA] * len(case_ids),
        "configuration": {"mode": "rgb8", "target": 200, "axis": arm.split("-")[1], "fixed_partner": None},
        "request_sha256": sha,
        "images": [{"sha256": f"img-{c}", "bytes": 10, "pixels": [2, 3]} for c in case_ids],
    }


@pytest.fixture
def gold(monkeypatch: pytest.MonkeyPatch) -> None:
    reference = {"id": "c0", "family": "f", "split": "DEV", "paired_group": "g", "evidence_modes": ["native"]}
    monkeypatch.setattr(
        image_gates,
        "_context_gold",
        lambda: {PDF_SHA: {**reference, "source_words": 3, "gold": {"choice": "A"}}},
    )


@pytest.mark.usefixtures("gold")
def test_context_runs_keep_aliases_failures_and_unknown_costs(tmp_path: Path) -> None:
    directory = tmp_path / "image-axis-context30-v1"
    (directory).mkdir()
    (directory / f"source-{PDF_SHA}.pdf").write_bytes(PDF)
    priced = _batch("m", "rgb8-height-200", 0, ["c0", "c1"], "r1")
    failed = _batch("m", "rgb8-width-200", 0, ["c0", "c1"], "r2")
    alias = {**priced, "arm": "rgb8-longest-200", "canonical_arm": "rgb8-height-200"}
    alias.pop("configuration")
    _write(
        directory / "manifest.json",
        {"task": "context-assembly", "batches": [priced, failed], "geometric_aliases": [alias]},
    )
    entry = {"index": 1, "accounted_usd": 0.0, "cost_status": "catalog estimate", "elapsed_ms": 5.0}
    _write(
        directory / "results.json",
        {
            "batches": [
                {
                    **priced,
                    "status": "ok",
                    "entry": entry,
                    "usage": {"input_tokens": 10, "output_tokens": 0, "cost": 0},
                    "observations": [
                        _observation("c0", exact=True),
                        _observation("c1", exact=False, choice="unresolved"),
                    ],
                },
                {**failed, "status": "failed", "observations": []},
            ]
        },
    )
    experiments = list(image_gates.collect(tmp_path))
    assert [e.dataset for e in experiments] == ["exp/image-axis-context30-v1/context30"]
    experiment = experiments[0]
    counts = validate(experiment)
    assert counts["items"] == 2
    assert counts["runs"] == 3
    items = {i.key: i for i in experiment.items}
    assert items["c0"].expected == {"choice": "A"}
    assert items["c1"].expected is None  # Case ID does not match the authored reference.
    runs = {r.name: r for r in experiment.runs}
    measured = runs["m/rgb8-height-200"]
    assert measured.scores["region_exact_sum"] == 1
    assert measured.scores["unresolved_cases"] == 1
    assert measured.scores["unique_requests"] == 1
    # Reported zero is preserved; the missing catalog rate leaves the effective cost unknown.
    assert "effective_usd" not in measured.scores
    assert measured.scores["unknown_cost_requests"] == 1
    assert measured.rows[0].metadata["batch_provider_reported_usd"] == 0
    assert "batch_effective_usd" not in measured.rows[0].metadata
    shared = runs["m/rgb8-longest-200"]
    assert shared.scores["alias_cases"] == 2
    assert shared.scores["unique_requests"] == 0
    assert all(r.metadata["quality_alias"] for r in shared.rows)
    broken = runs["m/rgb8-width-200"]
    assert len(broken.rows) == 2
    assert all(not clean_scores(r.scores) for r in broken.rows)
    assert broken.scores["unmeasured_cases"] == 2


@pytest.mark.usefixtures("gold")
def test_freeze_only_directory_yields_items_without_runs(tmp_path: Path) -> None:
    directory = tmp_path / "image-axis-context30-anisotropic-v1"
    _write(directory / "manifest.json", {"batches": [_batch("m", "rgb8-width-200", 0, ["c0"], "r")]})
    (experiment,) = image_gates.collect(tmp_path)
    assert experiment.runs == []
    assert experiment.items[0].input["source_pdf"] == {"sha256": PDF_SHA, "path": None}


def _cost(value: float | None) -> dict[str, Any]:
    return {"effective_usd": value, "basis": "provider-reported USD" if value else "unknown"}


def test_ocr_admission_and_candidate_ceilings(tmp_path: Path) -> None:
    directory = tmp_path / "ocr1200-overlap05-admission-v1"
    _write(
        directory / "source-frozen.json",
        {"pages": [{"id": "p0", "words": [{"id": 0}], "vector_candidates": []}, {"id": "p1", "words": []}]},
    )
    _write(
        directory / "manifest.json",
        {"records": [{"id": "p0", "route": "hosted_admission"}, {"id": "p1", "route": "native_vector"}]},
    )
    scores = dict.fromkeys(image_gates.ADMISSION_SCORES, False)
    rows = [
        {"id": "p0", "kind": "prose", "selection": "rolling", "scores": {**scores, "false_positive_page": True}},
        {"id": "p1", "kind": "ruled-control", "selection": "native_vector", "scores": {**scores, "exact_page": True}},
    ]
    slices = {"prose": {"pages": 1, "false_positive_page": 1}}
    _write(
        directory / "evaluation.json",
        {
            "cohorts": {"m/image512": {"pages": 2, "native_zero_call_pages": 1, "rows": rows, "slices": slices}},
            "candidate_ceiling_rows": [
                {
                    "id": "p0",
                    "variant": "rolling",
                    "kind": "prose",
                    "scores": scores,
                    "owned_source_ids": 1,
                    "unresolved_source_ids": 0,
                }
            ],
        },
    )
    call = {
        "id": "p0",
        "model": "m",
        "arm": "image512",
        "status": "ok",
        "entry": {"index": 3, "provider_reported_usd": 0.5},
        "usage": {"input_tokens": 4, "output_tokens": 1, "cost": 0.5},
        "cost": _cost(0.5),
        "http_elapsed_ms": 2.0,
    }
    _write(directory / "hosted-results.json", {"calls": [call]})
    (experiment,) = image_gates.collect(tmp_path)
    validate(experiment)
    runs = {r.name: r for r in experiment.runs}
    assert set(runs) == {"m/image512", "candidate-ceiling/rolling"}
    hosted = runs["m/image512"]
    assert hosted.scores["prose_false_positive_page"] == 1
    assert hosted.scores["effective_usd"] == 0.5
    assert hosted.rows[0].metadata["provider_reported_usd"] == 0.5
    assert hosted.rows[1].metadata["status"] == "native_vector"
    assert runs["candidate-ceiling/rolling"].scores["prose_pages"] == 1


def test_gate_keeps_unscored_pages_in_denominator(tmp_path: Path) -> None:
    directory = tmp_path / "source-table-gate-realistic28-v2"
    _write(directory / "manifest.json", {"records": [{"id": "a", "route": "hosted_presence_gate"}]})
    _write(directory / "source-frozen.json", {"pages": [{"id": i, "words": []} for i in ("a", "b", "c")]})
    rows = [
        {"id": "a", "kind": "borderless", "choice": "table_present", "scored": True, "correct": True},
        {"id": "b", "kind": "prose", "choice": "unmeasured_or_failed", "scored": True, "correct": False},
        {"id": "c", "kind": "ambiguous", "choice": "not_table", "scored": False, "correct": None},
    ]
    cohort = {
        "rows": rows,
        "slices": {"borderless": {"pages": 1, "correct": 1}},
        "ambiguous_unscored_pages": 1,
        "native_zero_call_pages": 0,
        "actual_gate_accounting": {"unique_requests": 1, "effective_usd": None, "known_partial_usd": 0.0},
    }
    _write(directory / "evaluation.json", {"cohorts": {"m/G001": cohort}})
    (experiment,) = image_gates.collect(tmp_path)
    validate(experiment)
    items = {i.key: i for i in experiment.items}
    assert items["c"].expected == {"kind": "ambiguous", "presence": None, "scored": False}
    (run,) = experiment.runs
    assert len(run.rows) == 3
    assert run.scores["scored_accuracy"] == 0.5
    assert "effective_usd" not in run.scores
    assert "correct" not in clean_scores(run.rows[2].scores)
    assert clean_scores(run.rows[1].scores)["unresolved_or_failed"] == 1.0


def test_neutralized_freeze_has_no_expected_or_runs(tmp_path: Path) -> None:
    base = tmp_path / "source-neutralized-dev-v1" / "fresh24"
    _write(base / "manifest.json", {"cases": [{"id": "fresh-000", "pdf_sha256": "x"}], "design": {"arm": "deletion"}})
    _write(base / "source-evidence.json", {"pages": [{"id": "fresh-000", "words": [1, 2]}]})
    (base / "pdfs").mkdir()
    (base / "pdfs" / "fresh-000.pdf").write_bytes(PDF)
    (experiment,) = image_gates.collect(tmp_path)
    assert experiment.runs == []
    item = experiment.items[0]
    assert item.expected is None
    assert item.input["pdf"]["sha256"] == PDF_SHA
    assert item.input["source_words"] == 2


def test_protected_paths_are_refused(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        list(image_gates.collect(tmp_path / "silver-heldout-v1"))
