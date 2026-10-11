from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
from bench import langfuse_backfill
from bench.langfuse_adapters import (
    corpus_borderless,
    corpus_ocr_rolling,
    corpus_omnidoc,
    corpus_realism,
    corpus_silver_tables,
    corpus_wild_ocr,
    discover,
)
from bench.langfuse_adapters.base import Experiment, export, validate
from bench.langfuse_adapters.corpus_common import ref

if TYPE_CHECKING:
    from pathlib import Path

ADAPTERS = (
    corpus_borderless,
    corpus_silver_tables,
    corpus_realism,
    corpus_omnidoc,
    corpus_ocr_rolling,
    corpus_wild_ocr,
)
ZERO = {"exact_cells": False, "exact_page": False, "exact_spans": False, "false_positive_page": False}
HIT = {"exact_cells": True, "exact_page": True, "exact_spans": True, "false_positive_page": False}


def write(path: Path, value: Any) -> Path:  # noqa: ANN401 - arbitrary fixture JSON.
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        path.write_bytes(value)
    else:
        path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture
def artifacts(tmp_path: Path) -> Path:
    return tmp_path / "bench" / "results" / "pdf-master-artifacts"


def only(experiments: list[Experiment], dataset: str) -> Experiment:
    matches = [e for e in experiments if e.dataset == dataset]
    assert len(matches) == 1, [e.dataset for e in experiments]
    return matches[0]


def runs(experiment: Experiment) -> dict[str, Any]:
    return {run.name: run for run in experiment.runs}


def borderless_corpus(artifacts: Path) -> Path:
    version = artifacts / "borderless-dev-v1" / "v1"
    write(
        version / "manifest.json", {"cases": [{"id": "case-000", "pdf_path": "pdfs/case-000.pdf"}, {"id": "case-001"}]}
    )
    write(version / "pdfs" / "case-000.pdf", b"%PDF-1.4 a")
    write(version / "pdfs" / "case-001.pdf", b"%PDF-1.4 b")
    write(
        version / "private-targets.json",
        [{"id": "case-000", "kind": "borderless", "tables": []}, {"id": "case-001", "kind": "prose", "tables": []}],
    )
    return version


def test_borderless_runs_keep_errors_and_cross_check(artifacts: Path) -> None:
    version = borderless_corpus(artifacts)
    observed = [{"row_count": 2, "col_count": 2, "values": [["a", "1"], ["b", "2"]], "cells": [[0, 0, 1, 1]] * 4}]
    write(
        version / "run-a" / "private-scores.json",
        [
            {"id": "case-000", "route": "raw-text", "status": "ok", "observed": observed,
             "scores": {**HIT, "owned_values": 4, "owned_words": 4}},
            {"id": "case-001", "route": "raw-text", "status": "error", "error": "boom"},
        ],
    )  # fmt: skip
    summary: dict[str, Any] = {
        "runner_sha256": "r",
        "resources": {"wall_seconds": 1.5, "peak_rss_bytes": 10},
        "results": {
            "raw-text": {
                "errors": 1,
                "pages": 2,
                "borderless": {"exact_cells": 1, "exact_page": 1, "owned_values": 4, "pages": 1},
                "prose": {"exact_cells": 0, "false_positive_page": 0, "pages": 1},
            }
        },
    }
    write(version / "run-a" / "summary.json", summary)
    write(version / "run-a" / "case-000.png", b"png")
    experiment = only(list(corpus_borderless.collect(artifacts)), "exp/borderless-dev-v1/v1")
    assert validate(experiment)["rows"] == 2
    run = runs(experiment)["run-a raw-text"]
    ok, failed = run.rows
    assert ok.scores["exact_cells"] is True
    assert ok.scores["completed"] is True
    assert ok.output["tables"] == [{"rows": 2, "columns": 2, "values": [["a", "1"], ["b", "2"]]}]
    assert failed.scores == {"completed": False}
    assert failed.metadata["status"] == "error"
    assert run.scores["borderless.exact_cells"] == 1
    assert run.metadata["summary_check"] == "match"
    assert run.metadata["resources.wall_seconds"] == 1.5
    assert experiment.items[0].input["pdf"]["sha256"]
    summary["results"]["raw-text"]["borderless"]["exact_cells"] = 2
    write(version / "run-a" / "summary.json", summary)
    run = runs(next(iter(corpus_borderless.collect(artifacts))))["run-a raw-text"]
    assert run.metadata["summary_check"] == "mismatch"
    assert "borderless.exact_cells" in run.metadata["summary_mismatches"]


def test_silver_structure_and_routes_share_one_page_dataset(artifacts: Path) -> None:
    version = artifacts / "silver-v1" / "v1"
    write(version / "manifest.json", {"cases": [{"id": "doc", "pdf_path": "pdfs/doc.pdf"}]})
    write(version / "pdfs" / "doc.pdf", b"%PDF")
    table = {"row_count": 1, "values": [["x"]]}
    targets = {
        "pages": [{"id": "doc", "page_number": n, "family": "f", "tables": t} for n, t in ((0, []), (1, [table]))]
    }
    page = {"cell_slots": 0, "exact_cells": None, "exact_page": True, "false_positive_page": False, "owned_values": 0}
    hit = {
        **page,
        "cell_slots": 1,
        "correct_cell_slots": 1,
        "exact_cells": True,
        "exact_spans": True,
        "owned_values": 1,
    }
    structure = version / "structure-runs" / "s1"
    write(structure / "targets.json", targets)
    (structure / "pages.jsonl").write_text(
        "\n".join(
            json.dumps({"id": "doc", "page_number": n, "strategy": "lines", "status": "ok", "scores": s,
                        "observed": [], "wall_ms": 2.0, "cpu_ms": 1.0})
            for n, s in ((0, page), (1, hit))
        )
    )  # fmt: skip
    write(structure / "summary.json", {"totals": {"lines": {"exact_table_cells": 1, "exact_page": 2, "errors": 0}}})
    routes = version / "corpus-route-runs" / "r1"
    write(routes / "targets.json", targets)
    (routes / "pages.jsonl").write_text(
        json.dumps({"id": "doc", "page_number": 0, "route": "none", "status": "ok", "scores": page, "observed": []})
        + "\n"
        + json.dumps({"id": "doc", "page_number": 1, "route": "none", "status": "error", "observed": []})
    )
    write(routes / "summary.json", {"totals": {"none": {"exact_page": 1, "errors": 1, "pages": 2}}})
    (experiment,) = corpus_silver_tables.collect(artifacts)
    assert experiment.dataset == "exp/silver-v1/v1/tables"
    assert [item.key for item in experiment.items] == ["doc#p0", "doc#p1"]
    found = runs(experiment)
    assert set(found) == {"structure s1 lines", "routes r1 none"}
    lines = found["structure s1 lines"]
    assert "exact_cells" not in lines.rows[0].scores  # None stays unscored.
    assert lines.rows[0].wall_ms == 2.0
    assert lines.metadata["summary_check"] == "match"
    assert found["routes r1 none"].rows[1].scores == {"completed": False}
    assert found["routes r1 none"].metadata["summary_check"] == "match"


def test_realism_cohorts_keep_ambiguous_pages_unscored(artifacts: Path) -> None:
    version = artifacts / "silver-realism-v2" / "v2"
    write(version / "manifest.json", {"cases": [{"id": "dev-000"}, {"id": "dev-001"}]})
    write(
        version / "private-targets.json",
        [{"id": "dev-000", "kind": "borderless"}, {"id": "dev-001", "kind": "ambiguous"}],
    )
    unscored = dict.fromkeys(HIT)
    evaluation = {
        "cohorts": {
            "m/x/image512": {
                "pages": 2,
                "ambiguous_unscored_pages": 1,
                "rows": [
                    {"id": "dev-000", "kind": "borderless", "truth_status": "authored-silver", "selection": "rolling",
                     "scores": {**HIT, "owned_values": 3}, "conservation": True, "owned_source_ids": 3},
                    {"id": "dev-001", "kind": "ambiguous", "truth_status": "ambiguous-unscored",
                     "selection": "rolling", "scores": unscored, "conservation": True},
                ],
                "slices": {"borderless": {"pages": 1, "exact_cells": 1, "owned_values": 3, "expected_values": 9}},
            }
        },
        "candidate_ceiling_rows": [
            {"id": "dev-000", "variant": "rolling", "kind": "borderless", "scores": HIT, "source_conservation": True}
        ],
    }  # fmt: skip
    write(version / "admission-image512" / "evaluation.json", evaluation)
    cost = {"effective_usd": 0.5, "basis": "provider-reported USD"}
    call = {"model": "m/x", "id": "dev-000", "status": "ok", "http_elapsed_ms": 12.0, "cost": cost}
    write(version / "admission-image512" / "hosted-results.json", {"calls": [call]})
    (experiment,) = corpus_realism.collect(artifacts)
    assert experiment.dataset == "exp/silver-realism-v2/v2/admission-image512"
    cohort = runs(experiment)["admission-image512 m/x/image512"]
    assert cohort.rows[0].scores["exact_cells"] is True
    assert cohort.rows[0].scores["effective_usd"] == 0.5
    assert "exact_cells" not in cohort.rows[1].scores
    assert cohort.rows[1].metadata["status"] == "missing-call"
    assert cohort.scores["effective_usd"] == 0.5
    assert cohort.metadata["summary_check"] == "match"
    ceiling = runs(experiment)["admission-image512 candidate-ceiling rolling"]
    assert ceiling.scores["borderless.exact_cells"] == 1


def test_omnidoc_references_third_party_files_and_labels_training(artifacts: Path) -> None:
    dev = artifacts / "omnidoc-dev"
    write(dev / "images" / "p.jpg", b"jpeg")
    write(dev / "annotations" / "p.jpg.json", {"layout_dets": []})
    write(
        artifacts.parents[1] / "omnidoc-dev" / "registry.json",
        {"revision": "abc", "rows": [{"sample": 1, "id": "p.jpg"}]},
    )
    write(dev / "baseline.json", {"pylopdf_version": "0.1", "rows": [{"id": "p.jpg", "native_text_characters": 0}]})
    bags = {"nfkc": {"character_bag_recall": 0.5}, "strict": {"character_bag_recall": 0.25}}
    score = {"text_blocks": 2, "spatially_covered_text_blocks": 1, "character_bags": bags}
    write(dev / "ocr-admission" / "scores.json", [{"sample": 1, "edge": 640, "status": "complete", "score": score}])
    training = artifacts / "omnidoc-training-v1"
    write(training / "geometry-frozen.json", {"pages": [{"source_id": "t.jpg", "blocks": [{}, {}]}]})
    write(training / "images" / "t.jpg", b"jpeg")
    write(
        artifacts.parents[1] / "omnidoc-training" / "registry.json",
        {"rows": [{"training_id": "training-000", "id": "t.jpg"}]},
    )
    ink = {"v2": {"tile_dark_fraction_mae": 0.2}, "v3": {"tile_dark_fraction_mae": 0.1}}
    manifest = {
        "rows": [
            {"training_id": "training-000", "ink_comparison": ink, "metadata": {"pages": [{"text": {"word_count": 7}}]}}
        ]
    }
    write(training / "synthetic-v3.1" / "manifest.json", manifest)
    write(
        training / "synthetic-v3.1" / "geometry-audit.json",
        [{"training_id": "training-000", "outside_page_word_ids": ["w"]}],
    )
    dev_experiment, training_experiment = corpus_omnidoc.collect(artifacts)
    assert dev_experiment.dataset == "exp/omnidoc-dev/pages"
    item = dev_experiment.items[0]
    assert set(item.input["image"]) == {"path", "bytes", "sha256"}
    assert set(item.expected["annotation"]) == {"path", "bytes", "sha256"}
    ocr = runs(dev_experiment)["ocr-admission e640"]
    assert ocr.rows[0].scores["nfkc.character_bag_recall"] == 0.5
    assert ocr.rows[0].scores["text_block_coverage"] == 0.5
    assert training_experiment.labels["split"] == "TRAINING"
    generation = runs(training_experiment)["synthetic-v3.1"]
    assert generation.rows[0].scores["tile_dark_fraction_mae"] == 0.1
    assert generation.rows[0].scores["outside_page_words"] == 1
    assert generation.scores["extracted_words"] == 7


def test_ocr_rolling_arms_and_overlap_runs(artifacts: Path) -> None:
    corpus = borderless_corpus(artifacts)
    version = artifacts / "ocr-rolling-v1" / corpus.name
    write(version / "inputs.json", {"pages": [{"id": c, "edge": 640} for c in ("case-000", "case-001")]})
    pure = {**HIT, "owned_values": 2}
    rows = [
        {"id": "case-000", "edge": 640, "variant": "rolling", "status": "complete", "pure": pure, "hybrid": pure,
         "original_token_recall": {"recall": 1.0}, "ocr_ids_conserved": True, "ocr_seconds": 0.5},
        {"id": "case-001", "edge": 640, "variant": "rolling", "status": "refused", "ocr_ids_conserved": False},
    ]  # fmt: skip
    write(version / "scores.json", rows)
    overlap = [{"id": "case-000", "edge": 640, "allowance": "0.5", "wrap": True, "pure": pure, "hybrid": pure,
                "conserved": True}]  # fmt: skip
    write(version / "overlap-a004-v1" / "scores.json", overlap)
    (experiment,) = corpus_ocr_rolling.collect(artifacts)
    assert experiment.dataset == "exp/ocr-rolling-v1/v1"
    assert experiment.items[0].expected == {"id": "case-000", "kind": "borderless", "tables": []}
    arm = runs(experiment)["e640 rolling"]
    assert arm.rows[0].scores["pure.exact_cells"] is True
    assert arm.rows[1].scores["completed"] is False
    assert "pure.exact_cells" not in arm.rows[1].scores
    assert arm.scores["refused_or_missing"] == 1
    assert arm.scores["pure.borderless.exact_cells"] == 1
    ablation = runs(experiment)["overlap-a004 e640 allowance-0.5"]
    assert ablation.scores["pure.wrapped.exact_cells"] == 1


def test_wild_ocr_policies_join_reports_and_base_levels(artifacts: Path) -> None:
    wild = artifacts / "wild-v1"
    write(wild / "docs" / "d1" / "truth.json", {"family": "ruled", "outline": [1, 2]})
    write(wild / "docs" / "d1" / "source.pdf", b"%PDF")
    base = {"doc_id": "d1", "level": "L8_mixed", "text": {"f1": 0.5}, "markdown": {"f1": 0.4}, "tables": []}
    fill = {
        "doc_id": "d1",
        "level": "L8_mixed+ocr-fill",
        "text": {"f1": 0.75},
        "markdown": {"f1": 0.7},
        "tables": [{"matched": True, "exact": False, "cell_recall": 0.5}],
        "metadata": {"title_match": True},
        "outline": {"found": 0},
    }
    failed = {"doc_id": "d1", "level": "L4_raster+ocr", "error": "PdfError: x"}
    summary = {"L8_mixed+ocr-fill": {"documents": 1, "text_f1": 0.75, "table_cell_recall": 0.5, "table_exact": 0}}
    write(wild / "audit.json", {"manifest": {"doc_ids": ["d1"]}, "audits": [base, fill, failed], "summary": summary})
    write(wild / "ocr-fill-report.json", {"documents": {"d1/L8_mixed": {"recognized": 9, "inserted": 3}}, "dpi": 200})
    write(wild / "repair-v1" / "manifest.json", {"pages": [{"id": "x1", "doc_id": "d1", "level": "L0_tagged"}]})
    write(wild / "repair-v1" / "frozen.json", {"menus": [{"id": "x1", "candidate_count": 4, "truth_table_count": 1}]})
    policies, repair = corpus_wild_ocr.collect(artifacts)
    assert policies.dataset == "exp/wild-v1/ocr-policies"
    found = runs(policies)
    assert {name.split(" @ ")[0] for name in found} == {"L8_mixed+ocr-fill", "L4_raster+ocr"}
    run = next(run for name, run in found.items() if name.startswith("L8_mixed+ocr-fill"))
    row = run.rows[0]
    assert row.scores["text.f1"] == 0.75
    assert row.scores["base.text.f1"] == 0.5
    assert row.scores["ocr.inserted"] == 3
    assert row.scores["ocr.replaced_pages"] == 0
    assert run.metadata["summary_check"] == "match"
    raster = next(run for name, run in found.items() if name.startswith("L4_raster+ocr"))
    assert raster.rows[0].metadata["status"] == "error"
    assert raster.rows[0].scores["text.f1"] == 0.0
    assert raster.metadata["ocr_report_entries"] == 0
    assert repair.dataset == "exp/wild-v1/repair-v1"
    assert repair.runs[0].rows[0].scores["candidate_count"] == 4
    assert corpus_wild_ocr.split_level("L5_raster_ocr") == ("L5_raster_ocr", None)


def test_adapters_are_discovered_namespaced_and_exportable(artifacts: Path) -> None:
    names = {module.NAME for module in discover()}
    assert {module.NAME for module in ADAPTERS} <= names
    borderless_corpus(artifacts)
    for module in ADAPTERS:
        for experiment in module.collect(artifacts):
            assert experiment.dataset.startswith("exp/")
            validate(experiment)


def test_export_posts_items_runs_and_scores(artifacts: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    version = borderless_corpus(artifacts)
    write(
        version / "run-a" / "private-scores.json", [{"id": "case-000", "route": "none", "status": "ok", "scores": HIT}]
    )
    write(version / "run-a" / "summary.json", {"results": {"none": {"errors": 0}}})
    monkeypatch.setattr(langfuse_backfill, "MARKERS", tmp_path / "markers")
    sent: list[tuple[str, Any]] = []

    class Fake(langfuse_backfill.Client):
        def post(self, path: str, body: object) -> dict[str, Any]:
            sent.append((path, body))
            return {}

        def get(self, path: str) -> dict[str, Any]:
            return {"id": "run-1"} if "/runs/" in path else {"data": [], "meta": {"totalPages": 1}}

    (experiment,) = corpus_borderless.collect(artifacts)
    status = export(Fake({"LANGFUSE_BASE_URL": "https://example.test"}), experiment, force=True)
    assert status["runs_exported"] == 1
    assert any(path == "/api/public/dataset-run-items" for path, _ in sent)


def test_protected_heldout_paths_are_refused(artifacts: Path) -> None:
    (artifacts / "silver-heldout-v1").mkdir(parents=True)
    with pytest.raises(PermissionError):
        ref(artifacts / "silver-heldout-v1" / "manifest.json")
