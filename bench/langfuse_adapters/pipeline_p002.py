"""P002 broad generalization wave (``pipeline-p002``) as Langfuse experiments.

Three datasets, keyed by the frozen corpus identity each run attests:

- ``exp/pipeline-p002/natural16``: the second predeclared OmniDocBench screen
  (12 positive, 4 negative natural pages; ``screens/natural16``).
- ``exp/pipeline-p002/full276-r2``: the 276-page DEV corpus revision r2
  (``corpus-r2``; 156 authored, 64 OmniDocBench, 56 native diagnostic pages).
- ``exp/pipeline-p002/full276-r1``: the original r1 snapshot, used only by the
  historical ``native-full-r1`` baseline (12 authored carriers differ from r2).

Primary runs come from each run directory's ``verified-evaluation.json``: its
per-page ``page_scores`` become row scores and its totals, costs, and resources
become run scores. ``report.json`` supplies per-page status, errors, wall/CPU
time, and retained call charges. Offline secondary analyses are separately
named runs whose names start with their analysis label and carry
``metadata["secondary"] = True``: partial-table salvage, retained-response
format-repair counterfactuals, placement-free cell inventory, and logical
native-orientation replay. They never change primary scores, charges, or
failures. The interrupted ``natural16-generate-haiku`` run has no verified
evaluation; its rows carry operational status only, with 12 missing pages.

Provider-reported charges, estimates, and reservations are kept apart. The
verified ``costs`` block states that estimate/reservation amounts are
unavailable, so those zeros are not exported; ``effective_usd`` is omitted
when the evaluation marks it unknown.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import ROOT, Experiment, Item, Row, Run, digest, file_ref, guard, read_json
from bench.langfuse_adapters.pipeline_p001 import compact_table, number, pdf_ref, row_metadata

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "pipeline_p002"
CAMPAIGN = "pipeline-p002"
CORPORA = (
    ("natural16", "screens/natural16"),
    ("full276-r2", "corpus-r2"),
    ("full276-r1", "."),
)
DESCRIPTIONS = {
    "natural16": (
        "P002 natural16 screen: 16 metadata-selected OmniDocBench DEV pages (6 multiple-table, 6 single-table, "
        "4 no-table; 53 reference tables, 2333 anchor cells) with official public table annotations."
    ),
    "full276-r2": (
        "P002 full DEV corpus r2 (white-alpha carrier fix): 276 pages = 156 authored stress pages, 64 OmniDocBench "
        "raster carriers, 56 native diagnostic pages (unscored structurally); 249 reference tables, 8897 cells."
    ),
    "full276-r1": (
        "P002 full DEV corpus r1 (original snapshot; 12 authored RGBA carriers flattened onto black). "
        "Same page IDs and references as r2; used only by the historical native-full-r1 baseline."
    ),
}
_SKIP_SCORE_KEYS = {"id", "structural_scored", "matches"}
_COST_KEYS = {
    "provider_reported_subtotal_usd": "provider_reported_usd",
    "missing_provider_charge_count": "missing_provider_charge_count",
    "accounted_usd_including_reservations": "accounted_usd_including_reservations",
    "ledger_attempts": "ledger_attempts",
    "successful_calls": "successful_calls",
}
_COHORT_KEYS = {
    "positive": (
        "scored_pages",
        "exact_page",
        "complete_tables",
        "correct_text_cells",
        "expected_cells",
        "error",
        "all_page_errors",
    ),
    "negative": (
        "scored_pages",
        "exact_page",
        "false_positive_page",
        "false_positive_tables",
        "error",
        "all_page_errors",
    ),
}
_RATE_KEYS = (
    "pages_per_minute",
    "pages_per_dollar",
    "exact_pages_per_minute",
    "exact_pages_per_dollar",
    "exact_positive_pages_per_minute",
    "exact_positive_pages_per_dollar",
)


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _numeric(scores: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Keep numeric and boolean fields of a retained score mapping."""
    return {
        prefix + key: value
        for key, value in scores.items()
        if key not in _SKIP_SCORE_KEYS and (isinstance(value, bool) or number(value) is not None)
    }


def _page_scores(page: dict[str, Any]) -> dict[str, Any]:
    scores = _numeric(page)
    expected = number(page.get("expected_cells"))
    if page.get("structural_scored") and expected:
        scores["text_cell_recall"] = page.get("correct_text_cells", 0) / expected
        scores["structure_cell_recall"] = page.get("correct_structure_cells", 0) / expected
    return scores


def _items(artifacts: Path, manifest: dict[str, Any], targets: dict[str, Any]) -> list[Item]:
    target_map = {page["id"]: page for page in targets["pages"]}
    items = []
    for record in manifest["pages"]:
        target = target_map.get(record["id"], {})
        expected: dict[str, Any] = {
            "structural_scored": target.get("structural_scored", True),
            "table_count": len(target.get("tables", []) or []),
            "tables": [compact_table(table) for table in target.get("tables", []) or []],
        }
        if target.get("annotation_path"):
            expected["annotation"] = str(target["annotation_path"]).split("pdf-master-artifacts/", 1)[-1]
            expected["annotation_errors"] = target.get("annotation_errors")
        items.append(
            Item(
                key=record["id"],
                input={
                    "page_id": record["id"],
                    "cohort": record.get("cohort"),
                    "family": record.get("family"),
                    "input_kind": record.get("input_kind"),
                    "label_status": record.get("label_status"),
                    "pilot": record.get("pilot"),
                    "diversity": record.get("diversity"),
                    "pdf": pdf_ref(artifacts, record),
                },
                expected=expected,
                metadata={
                    "campaign": "P002",
                    "cohort": record.get("cohort"),
                    "family": record.get("family"),
                    "structural_scored": bool(expected["structural_scored"]),
                    "positive_page": bool(expected["table_count"]),
                },
            )
        )
    return items


def _output(directory: Path, prediction: dict[str, Any]) -> dict[str, Any]:
    status = prediction.get("status", "missing")
    output: dict[str, Any] = {
        "status": status,
        "tables": [compact_table(table) for table in prediction.get("tables", []) or []],
        "unresolved_words": len(prediction.get("unresolved_ids", []) or []),
    }
    if prediction.get("text_provenance"):
        output["text_provenance"] = prediction["text_provenance"]
    markdown = directory / f"{prediction.get('id')}.md"
    if status == "ok" and markdown.is_file():
        output["markdown"] = file_ref(markdown)
    return output


def _pick(source: dict[str, Any] | None, names: dict[str, str]) -> dict[str, Any]:
    """Copy finite numeric fields under new names, omitting unknown values rather than zeroing them."""
    source = source or {}
    return {target: source[key] for key, target in names.items() if number(source.get(key)) is not None}


def _verified_scores(evaluation: dict[str, Any]) -> dict[str, Any]:
    """Return run aggregates from a verified evaluation; unknown values are omitted, never zeroed."""
    run_scores = _numeric(evaluation["scores"])
    for prefix, keys in _COHORT_KEYS.items():
        run_scores.update(_pick(evaluation.get(prefix), {key: f"{prefix}_{key}" for key in keys}))
    macro = ("exact_cell_recall", "complete_table_recall")
    run_scores.update(_pick(evaluation.get("positive_macro"), {key: f"positive_macro_{key}" for key in macro}))
    top = ("intended_pages", "operational_pages", "all_errors", "markdown_bytes_verified_pages", "conserved_pages")
    run_scores.update(_pick(evaluation, {key: key for key in (*top, *_RATE_KEYS)}))
    run_scores.update(_pick(evaluation.get("costs"), {**_COST_KEYS, "effective_usd": "effective_usd"}))
    resources = ("wall_seconds", "cpu_seconds", "peak_sampled_rss_bytes", "cpu_utilization_percent")
    run_scores.update(_pick(evaluation.get("resources"), {key: key for key in resources}))
    return run_scores


def _verified_run(directory: Path, evaluation: dict[str, Any], dataset: str) -> Run:
    report = read_json(directory / "report.json")
    by_id = {prediction["id"]: prediction for prediction in report.get("results", [])}
    failures = {page["id"]: page.get("category") for page in evaluation.get("failure_taxonomy", {}).get("pages", [])}
    rows = []
    for page in evaluation["page_scores"]:
        prediction = by_id.get(page["id"], {"id": page["id"], "status": "missing"})
        scores = _page_scores(page)
        scores["operational_output"] = prediction.get("status") == "ok"
        meta = row_metadata(prediction)
        meta["structural_scored"] = bool(page.get("structural_scored"))
        if page["id"] in failures:
            meta["failure_category"] = failures[page["id"]]
        wall = number(prediction.get("wall_seconds"))
        rows.append(
            Row(
                item_key=page["id"],
                output=_output(directory, prediction),
                scores=scores,
                metadata=meta,
                wall_ms=wall * 1000 if wall is not None else None,
            )
        )
    run_scores = _verified_scores(evaluation)
    costs = evaluation.get("costs", {}) or {}
    resources = evaluation.get("resources", {}) or {}
    page_text = sum(
        page.get("correct_text_cells", 0) for page in evaluation["page_scores"] if page.get("structural_scored")
    )
    row_charges = sum(row.metadata.get("provider_reported_usd", 0) for row in rows)
    config = evaluation.get("config", {}) or {}
    models = evaluation.get("model_configuration", {}) or {}
    actual = sorted((evaluation.get("actual_model_breakdown", {}) or {}).get("models", {}))
    return Run(
        name=directory.name,
        description=(
            f"P002 {dataset} run {directory.name}: {evaluation.get('output_scope')}; text provenance "
            f"{evaluation.get('text_provenance')}; processor={config.get('processor')}, policy={config.get('policy')}."
        ),
        rows=rows,
        metadata={
            "campaign": "P002",
            "secondary": False,
            "output_scope": evaluation.get("output_scope"),
            "text_provenance": evaluation.get("text_provenance"),
            "processor": config.get("processor"),
            "policy": config.get("policy"),
            "assembly_method": config.get("assembly_method"),
            "model": models.get("model") or config.get("model"),
            "generation_model": models.get("generation_model") or config.get("generation_model"),
            "gate_review_model": models.get("gate_review_model") or config.get("gate_review_model"),
            "actual_models": ", ".join(actual),
            "image_edge": config.get("image_edge"),
            "layout_detector": config.get("layout_detector"),
            "ocr_dpi": config.get("ocr_dpi"),
            "statuses": str(evaluation.get("statuses")),
            "failure_taxonomy": str((evaluation.get("failure_taxonomy") or {}).get("counts")),
            "cost_scope": costs.get("scope"),
            "cost_bases": str(costs.get("cost_bases")),
            "cost_note": costs.get("breakdown_note"),
            "resource_measurement": resources.get("measurement"),
            "renderer": (evaluation.get("code_verification") or {}).get("renderer"),
            "report_sha256": evaluation.get("report_sha256"),
            "crosscheck_page_text_cells_equal_total": page_text == evaluation["scores"].get("correct_text_cells"),
            "crosscheck_retained_page_charges_usd": row_charges,
            "source": _relative(directory),
        },
        scores=run_scores,
        started=directory.joinpath("verified-evaluation.json").stat().st_mtime,
    )


def _interrupted_run(directory: Path, intended: list[str]) -> Run:
    """Status-only rows for a run that never completed or received a verified evaluation."""
    report = read_json(directory / "report.json")
    by_id = {prediction["id"]: prediction for prediction in report.get("results", [])}
    rows = []
    for ident in intended:
        prediction = by_id.get(ident, {"id": ident, "status": "missing"})
        wall = number(prediction.get("wall_seconds"))
        rows.append(
            Row(
                item_key=ident,
                output=_output(directory, prediction),
                scores={"operational_output": prediction.get("status") == "ok"},
                metadata={**row_metadata(prediction), "unscored": "interrupted run; no verified evaluation"},
                wall_ms=wall * 1000 if wall is not None else None,
            )
        )
    bases = report.get("cost_bases", {}) or {}
    scores = {
        "intended_pages": len(intended),
        "retained_complete_pages": sum(1 for row in rows if row.output["status"] == "ok"),
        "missing_pages": sum(1 for row in rows if row.output["status"] == "missing"),
        "provider_reported_usd": number(report.get("provider_reported_usd")),
        "missing_provider_charge_count": number(report.get("missing_provider_charge_count")),
        "accounted_usd_including_reservations": number(report.get("accounted_usd")),
        "ledger_attempts": number(report.get("ledger_attempts")),
        "calls": number(report.get("calls")),
        "reserved_calls": number(bases.get("reserved", 0)),
    }
    return Run(
        name=directory.name,
        description=(
            f"P002 {directory.name}: {report.get('run_status', 'incomplete')}; {report.get('recovery_note', '')}"
        )[:900],
        rows=rows,
        metadata={
            "campaign": "P002",
            "secondary": False,
            "run_status": report.get("run_status"),
            "cost_bases": str(bases),
            "effective_usd_note": "unknown: unresolved reservation; not written as zero",
            "resource_measurement": (report.get("metrics") or {}).get("measurement"),
            "source": _relative(directory),
        },
        scores={key: value for key, value in scores.items() if value is not None},
        started=directory.joinpath("report.json").stat().st_mtime,
    )


def _secondary_run(  # noqa: PLR0913 - one retained secondary analysis.
    name: str,
    description: str,
    *,
    pages: list[dict[str, Any]],
    totals: dict[str, Any],
    metadata: dict[str, Any],
    page_meta: dict[str, dict[str, Any]] | None = None,
) -> Run:
    rows = [
        Row(
            item_key=page["id"],
            output={key: page[key] for key in ("status", "baseline_status") if key in page} or None,
            scores=_page_scores(page),
            metadata={"secondary": True, **(page_meta or {}).get(page["id"], {})},
        )
        for page in pages
    ]
    return Run(
        name=name,
        description=description,
        rows=rows,
        metadata={"campaign": "P002", "secondary": True, **metadata},
        scores=_numeric(totals),
    )


def _partial_runs(root: Path) -> Iterable[tuple[str, Run]]:
    seen: dict[tuple[str, str], str] = {}
    sources = [
        ("partial-salvage", root / "partial-salvage-audit.json"),
        ("partial-review", root / "partial-review/audit.json"),
        ("partial-review-wide-tables", root / "partial-review-wide-tables/audit.json"),
        ("multiscale-partial-review", root / "multiscale-partial-review/audit.json"),
        ("multiscale-partial-sonnet", root / "multiscale-partial-sonnet/audit.json"),
    ]
    for label, path in sources:
        if not path.is_file():
            continue
        audit = read_json(path)
        for run in audit.get("runs", []):
            pages = run.get("secondary_page_scores") or []
            key = (run["name"], digest(pages))
            if key in seen:
                continue
            name = f"partial-salvage/{run['name']}"
            if any(existing == run["name"] for existing, _ in seen):
                name = f"partial-salvage/{run['name']}@{label}"
            seen[key] = label
            partial = {page["id"]: page for page in run.get("partial_pages", [])}
            page_meta = {
                ident: {"status": page.get("status"), "baseline_status": page.get("baseline_status")}
                for ident, page in partial.items()
            }
            pages = [{**page, **{k: v for k, v in page_meta.get(page["id"], {}).items() if v}} for page in pages]
            totals = (run.get("groups", {}).get("all16", {}) or {}).get("secondary", {})
            yield (
                audit.get("dataset_sha256", ""),
                _secondary_run(
                    name,
                    f"Offline partial-table salvage of retained responses from {run['name']} ({label}); "
                    "always partial, never complete-page success; original charges/errors unchanged.",
                    pages=pages,
                    totals=totals,
                    metadata={
                        "analysis": label,
                        "parent_run": run["name"],
                        "source": _relative(path),
                        "spec": str(audit.get("spec"))[:900],
                    },
                    page_meta=page_meta,
                ),
            )


def _format_repair_runs(root: Path) -> Iterable[tuple[str, Run]]:
    for path in sorted(root.glob("*/counterfactual-format-repair-authoritative-scored.json")):
        data = read_json(path)
        score = data.get("counterfactual_score", {})
        evaluation = path.parent / "verified-evaluation.json"
        dataset = read_json(evaluation).get("dataset_sha256", "") if evaluation.is_file() else ""
        yield (
            dataset,
            _secondary_run(
                f"format-repair-counterfactual/{path.parent.name}",
                f"Offline frozen format-repair counterfactual on retained {path.parent.name} responses "
                "(authoritative natural-page scorer); not a live default, no new provider calls.",
                pages=score.get("pages", []),
                totals=score.get("totals", {}),
                metadata={
                    "analysis": "format-repair-counterfactual",
                    "parent_run": path.parent.name,
                    "version": data.get("version"),
                    "provider_calls": data.get("provider_calls"),
                    "source": _relative(path),
                },
            ),
        )


def _inventory_runs(root: Path) -> Iterable[tuple[str, Run]]:
    path = root / "cell-inventory-audit.json"
    if not path.is_file():
        return
    audit = read_json(path)
    for run in audit.get("runs", []):
        pages = [{**page, "admitted": bool(page.get("admitted"))} for page in run.get("pages", [])]
        yield (
            audit.get("dataset_sha256", ""),
            _secondary_run(
                f"cell-inventory/{run['name']}",
                f"Optimistic placement-free complete-cell string inventory for {run['name']}; "
                "never a primary score, inference evidence, or routing signal.",
                pages=pages,
                totals=(run.get("groups", {}) or {}).get("all16", {}),
                metadata={
                    "analysis": "cell-inventory",
                    "parent_run": run["name"],
                    "source": _relative(path),
                    "spec": str(audit.get("spec"))[:900],
                },
                page_meta={page["id"]: {"stratum": page.get("stratum")} for page in pages},
            ),
        )


def _orientation_runs(root: Path) -> Iterable[tuple[str, Run]]:
    for path in sorted(root.glob("native-orientation-*-replay.json")):
        replay = read_json(path)
        parent = replay.get("run")
        if not parent:
            continue
        evaluation = root / parent / "verified-evaluation.json"
        dataset = read_json(evaluation).get("dataset_sha256", "") if evaluation.is_file() else ""
        logical = replay.get("logical", {})
        resources = replay.get("resources", {}) or {}
        yield (
            dataset,
            _secondary_run(
                f"logical-orientation-replay/{parent}",
                f"Offline logical native-orientation correction replayed on retained {parent} responses; "
                "no fresh inference, charges, or throughput claim.",
                pages=logical.get("pages", []),
                totals={
                    **logical.get("totals", {}),
                    "replay_wall_seconds": resources.get("wall_seconds"),
                    "replay_cpu_seconds": resources.get("cpu_seconds"),
                },
                metadata={
                    "analysis": "logical-orientation-replay",
                    "parent_run": parent,
                    "diagnostic": replay.get("diagnostic"),
                    "original_costs_unchanged": str(replay.get("original_costs_unchanged")),
                    "replay_resource_scope": resources.get("scope"),
                    "source": _relative(path),
                },
            ),
        )


def _load_corpora(root: Path) -> tuple[dict[str, tuple[str, dict[str, Any], dict[str, Any]]], dict[str, str]]:
    """Return DEV corpora keyed by dataset identity, plus manifest-byte hashes mapped to that identity."""
    corpora: dict[str, tuple[str, dict[str, Any], dict[str, Any]]] = {}
    manifest_bytes: dict[str, str] = {}
    for label, relative in CORPORA:
        directory = root / relative
        if (directory / "manifest.json").is_file() and (directory / "private-targets.json").is_file():
            manifest = read_json(directory / "manifest.json")
            if manifest.get("split") != "DEV":
                continue
            corpora[manifest["dataset_sha256"]] = (label, manifest, read_json(directory / "private-targets.json"))
            manifest_bytes[hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()] = manifest[
                "dataset_sha256"
            ]
    return corpora, manifest_bytes


def _unevaluated_runs(
    root: Path, corpora: dict[str, tuple[str, dict[str, Any], dict[str, Any]]], manifest_bytes: dict[str, str]
) -> Iterable[tuple[str, Run]]:
    """Yield frozen runs that have a report but no verified evaluation (the interrupted run)."""
    for path in sorted(root.glob("*/report.json")):
        if (path.parent / "verified-evaluation.json").is_file():
            continue
        report_frozen = path.parent / "frozen.json"
        if not report_frozen.is_file():
            continue
        frozen = read_json(report_frozen)
        sha = manifest_bytes.get(str(frozen.get("manifest_sha256")))
        if sha is None:
            continue
        intended = [record["id"] for record in frozen.get("records", [])] or [p["id"] for p in corpora[sha][1]["pages"]]
        yield sha, _interrupted_run(path.parent, intended)


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield one experiment per P002 corpus identity that has runs."""
    root = guard(artifacts / CAMPAIGN)
    if not root.is_dir():
        return
    corpora, manifest_bytes = _load_corpora(root)
    runs: dict[str, list[Run]] = {sha: [] for sha in corpora}
    for path in sorted(root.glob("*/verified-evaluation.json"), key=lambda p: (p.stat().st_mtime_ns, p.parent.name)):
        evaluation = read_json(path)
        sha = evaluation.get("dataset_sha256", "")
        if sha not in corpora or not (path.parent / "report.json").is_file():
            continue
        runs[sha].append(_verified_run(path.parent, evaluation, corpora[sha][0]))
    for sha, run in _unevaluated_runs(root, corpora, manifest_bytes):
        runs[sha].append(run)
    for producer in (_partial_runs, _format_repair_runs, _inventory_runs, _orientation_runs):
        for sha, run in producer(root):
            if sha in corpora:
                runs[sha].append(run)
    for sha, (label, manifest, targets) in corpora.items():
        if not runs[sha]:
            continue
        yield Experiment(
            dataset=f"exp/pipeline-p002/{label}",
            description=DESCRIPTIONS[label],
            items=_items(artifacts, manifest, targets),
            runs=runs[sha],
            source=_relative(root),
            labels={"split": "DEV", "heldout": False, "campaign": "P002", "dataset_sha256": sha},
        )
