"""P003 table-structure evaluations (``pipeline-p003``) as Langfuse experiments.

P003 is the decision-model research campaign. Most of its queues (candidate
choice, gate admission, topology/ownership, boundary repair, header, geometry
diagram, acquisition, transcription screens, confirmation and complete276
pipelines) were independently re-verified and scored into ``evaluation*.json``
files that share one page-level schema (``runs[].page_scores``). This adapter
turns every such retained evaluation into rows; it never reads raw request or
response bodies.

- Dataset ``exp/pipeline-p003/<queue>/<gold>``: one per queue and gold page
  set. ``<queue>`` is the top-level queue directory (``parallel-*``,
  ``complete276-v1``...), ``transcription-screen-v1`` for the arms listed in
  ``transcription-screen-v1-status.json``, or ``standalone`` for other
  single-study directories and top-level files. ``<gold>`` names the frozen
  reference set by its ``dataset_sha256`` alias and page count
  (``screen-16p``, ``confirmation-48p``, ``random-40p``, ``corpus-r2-64p``,
  ``corpus-r2-276p``). Items are pages: identity as input, the reference
  table/cell/character counts and positive/negative label as expected output.
- Runs: one per arm evaluation file; variant files (``evaluation-<variant>``)
  are separate runs because each re-scores a different scope. The
  ``evaluation-cost-reconciled`` sidecar only overlays reconciled cost fields
  onto its primary run. Copies under ``history/`` or ``baseline/`` are skipped.
- Rows: the evaluator's own page counters (booleans as 1/0), plus the two
  per-page terms the evaluator averages into ``positive_macro``
  (``strict_exact_cell_recall`` and ``complete_table_recall``, positive pages
  only) and ``exact_positive_page``. Error, malformed and unscored pages stay
  in the run with ``metadata["status"]``.
- Run scores repeat the evaluator totals, ``positive_macro``, rates, CPU/RSS
  and costs. Provider-reported charges are emitted as
  ``provider_reported_usd`` only when every ledger attempt was
  provider-reported; otherwise the subtotal is ``provider_reported_partial_usd``
  next to ``missing_provider_charge_count``. A null effective cost is omitted,
  never written as zero. ``metadata["aggregate_check"]`` records whether the
  page rows re-sum to the reported totals.

Files that are missing, partially written or not yet scored (the campaign is
still active) are skipped and counted in the dataset labels.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import ROOT, Experiment, Item, Row, Run, digest, guard

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

NAME = "pipeline-p003"
CAMPAIGN = "pipeline-p003"
PREFIX = f"exp/{CAMPAIGN}"
TRANSCRIPTION_STATUS = "transcription-screen-v1-status.json"
GOLD_ALIASES = {
    "68d1800d": "screen",
    "6a950699": "confirmation",
    "c8b22181": "random",
    "e0a86f71": "corpus-r2",
}
EXPECTED_KEYS = ("expected_tables", "expected_cells", "reference_characters", "positive_page", "negative_page")
SKIP_ROW_KEYS = {"id", "matches", "geometry_expected_tables", *EXPECTED_KEYS}
TOTAL_KEYS = (
    "error",
    "malformed",
    "detected_tables",
    "matched_tables",
    "missing_tables",
    "false_positive_tables",
    "predicted_cells",
    "correct_structure_cells",
    "correct_text_cells",
    "complete_tables",
    "exact_page",
    "strict_exact_cells",
    "text_edit_distance",
)
COUNT_TOLERANCE = 1e-6
RATIO_TOLERANCE = 1e-9
COPY_PARTS = {"history", "baseline", "code"}
# Question-level evaluations owned by pipeline_p003_synthetic / pipeline_p003_micro.
OTHER_ADAPTERS = ("synthetic", "micro-evaluation")
CONFIG_META = (
    "model",
    "generation_model",
    "gate_review_model",
    "preset",
    "processor",
    "policy",
    "image_edge",
    "image_mode",
    "layout_detector",
    "assembly_method",
    "transport_concurrency",
)


def number(value: object) -> float | None:
    """Return a finite number (booleans as 1/0), otherwise None."""
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    return None


def mapping(value: object) -> dict[str, Any]:
    """Return a dict value, or an empty dict for any other retained shape."""
    return value if isinstance(value, dict) else {}


def rel(path: Path) -> str:
    """Repository-relative path when possible."""
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def load(path: Path) -> Any | None:  # noqa: ANN401 - arbitrary retained JSON.
    """Read guarded JSON; return None for missing, partial or undecodable files (active campaign)."""
    try:
        return json.loads(guard(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def cost_scores(costs: dict[str, Any] | None, prefix: str = "") -> dict[str, float | None]:
    """Separate exact provider-reported charges, partial subtotals, effective totals and reservations.

    ``provider_reported_usd`` is emitted only when every ledger attempt has the
    plain ``provider-reported USD`` basis. Mixed bases keep the retained subtotal
    as ``provider_reported_partial_usd``. BYOK, catalog-estimate and reserved
    attempts are counted separately; the effective total is omitted when null.
    """
    if not isinstance(costs, dict):
        return {}
    attempts = number(costs.get("ledger_attempts"))
    bases = mapping(costs.get("cost_bases"))
    exact = number(bases.get("provider-reported USD")) or 0.0
    byok = sum(number(v) or 0.0 for k, v in bases.items() if "BYOK" in str(k))
    subtotal = number(costs.get("provider_reported_usd", costs.get("provider_reported_subtotal_usd")))
    partial = number(costs.get("known_partial_provider_reported_usd", subtotal))
    out: dict[str, float | None] = {
        f"{prefix}ledger_attempts": attempts,
        f"{prefix}missing_provider_charge_count": number(costs.get("missing_provider_charge_count")),
        f"{prefix}effective_usd": number(costs.get("effective_api_usd", costs.get("effective_usd"))),
        f"{prefix}accounted_usd_including_reservations": number(
            costs.get("accounted_usd_including_reservations", costs.get("accounted_usd"))
        ),
        f"{prefix}unresolved_reserved_usd": number(costs.get("unresolved_reserved_usd")),
    }
    if bases:
        out[f"{prefix}provider_reported_attempts"] = exact
        out[f"{prefix}byok_provider_reported_attempts"] = byok
        out[f"{prefix}catalog_estimate_attempts"] = number(bases.get("catalog estimate")) or 0.0
        out[f"{prefix}reserved_attempts"] = number(bases.get("reserved")) or 0.0
    if subtotal is not None and attempts and exact == attempts:
        out[f"{prefix}provider_reported_usd"] = subtotal
    elif partial is not None and exact:
        out[f"{prefix}provider_reported_partial_usd"] = partial
    return {k: v for k, v in out.items() if v is not None}


def resource_scores(resources: dict[str, Any] | None) -> dict[str, float | None]:
    """Parent-process CPU/RSS/wall measurements as reported (worker peaks are not added)."""
    if not isinstance(resources, dict):
        return {}
    return {
        "cpu_seconds": number(resources.get("cpu_seconds")),
        "cpu_utilization_percent": number(resources.get("cpu_utilization_percent")),
        "peak_sampled_rss_bytes": number(resources.get("peak_sampled_rss_bytes")),
        "wall_seconds": number(resources.get("wall_seconds")),
    }


def page_terms(page: dict[str, Any]) -> dict[str, float | None]:
    """Per-page counters plus the terms the evaluator averages into positive_macro.

    Diagnostic pages (``structural_scored`` false) are excluded from the
    evaluator's structural totals, so they keep only their outcome flags.
    """
    if page.get("structural_scored") is False:
        return {k: number(page.get(k)) for k in ("structural_scored", "error", "malformed") if k in page}
    scores: dict[str, float | None] = {k: number(v) for k, v in page.items() if k not in SKIP_ROW_KEYS}
    positive = bool(page.get("positive_page"))
    scores["exact_positive_page"] = float(bool(page.get("exact_page")) and positive)
    cells, tables = number(page.get("expected_cells")), number(page.get("expected_tables"))
    if positive and cells:
        scores["strict_exact_cell_recall"] = (number(page.get("strict_exact_cells")) or 0.0) / cells
    if positive and tables:
        scores["complete_table_recall"] = (number(page.get("complete_tables")) or 0.0) / tables
    return {k: v for k, v in scores.items() if v is not None}


def page_status(page: dict[str, Any]) -> str:
    """Classify one page outcome as the evaluator does."""
    if page.get("error"):
        return "error"
    if page.get("malformed"):
        return "malformed"
    if page.get("structural_scored") is False:
        return "diagnostic"
    return "scored"


def aggregate_check(run: dict[str, Any]) -> str:
    """Re-sum page rows and compare with reported totals and positive_macro."""
    pages = run.get("page_scores") or []
    scored = [p for p in pages if p.get("structural_scored") is not False]
    totals = run.get("scores") or {}
    problems = []
    checks = [(k, k, scored) for k in TOTAL_KEYS] + [("all_page_errors", "error", pages)]
    for key, field, subset in checks:
        if key in totals and number(totals[key]) is not None:
            summed = sum(number(p.get(field)) or 0.0 for p in subset)
            if abs(summed - float(totals[key])) > COUNT_TOLERANCE:
                problems.append(f"{key}: rows {summed:g} != reported {totals[key]}")
    macro = run.get("positive_macro") or {}
    positive = [p for p in pages if p.get("positive_page")]
    if positive and number(macro.get("strict_exact_cell_recall")) is not None:
        mean = sum(page_terms(p).get("strict_exact_cell_recall") or 0.0 for p in positive) / len(positive)
        if abs(mean - float(macro["strict_exact_cell_recall"])) > RATIO_TOLERANCE:
            problems.append(
                f"strict_exact_cell_recall: rows {mean:.6f} != reported {macro['strict_exact_cell_recall']}"
            )
    if len(pages) != number(run.get("intended_pages")) and run.get("intended_pages") is not None:
        problems.append(f"rows {len(pages)} != intended_pages {run.get('intended_pages')}")
    return "ok" if not problems else "; ".join(problems)


def discover(artifacts: Path) -> Iterator[tuple[str, str, Path]]:
    """Yield (queue, arm, path) for every primary evaluation file without walking raw artifacts."""
    root = guard(artifacts / CAMPAIGN)
    if not root.is_dir():
        return
    status = load(root / TRANSCRIPTION_STATUS)
    transcription = {a.get("name") for a in (status or {}).get("arms", []) if isinstance(a, dict)}
    for path in sorted(root.glob("*.json")):
        if "evaluation" in path.name or path.name == "eval-smoke.json":
            yield "standalone", path.stem, path
    for study in sorted(p for p in root.iterdir() if p.is_dir()):
        if study.name in COPY_PARTS:
            continue
        own = sorted(study.glob("*evaluation*.json"))
        queue = "transcription-screen-v1" if study.name in transcription else "standalone"
        for path in own:
            yield queue, study.name, path
        for arm in sorted(p for p in study.iterdir() if p.is_dir() and p.name not in COPY_PARTS):
            for path in sorted(arm.glob("*evaluation*.json")):
                if not any(part in path.name for part in OTHER_ADAPTERS):
                    yield study.name, arm.name, path


def variant(path: Path) -> str:
    """Return the evaluation variant suffix ('' for the primary file)."""
    stem = path.stem
    if stem in {"evaluation", "eval-smoke"}:
        return ""
    return stem.replace("evaluation-", "").replace("-evaluation", "")


def gold_label(sha: str, pages: list[str]) -> str:
    """Readable name for a frozen gold page set."""
    return f"{GOLD_ALIASES.get(sha[:8], 'gold-' + sha[:8])}-{len(pages)}p"


def run_scores(run: dict[str, Any]) -> dict[str, float | None]:
    """Run-level aggregates as reported by the evaluator."""
    scores: dict[str, float | None] = {
        f"total_{k}": number(v) for k, v in (run.get("scores") or {}).items() if number(v) is not None
    }
    for key, value in (run.get("positive_macro") or {}).items():
        scores[f"positive_macro_{key}"] = number(value)
    for key in (
        "intended_pages",
        "operational_pages",
        "errors",
        "exact_positive_pages",
        "pages_per_minute",
        "intended_pages_per_minute",
        "pages_per_api_usd",
        "exact_positive_pages_per_minute",
        "incremental_attempted_pages_per_minute",
        "incremental_attempted_pages_per_api_usd",
        "incremental_ranking_pages_processed_per_minute",
        "incremental_ranking_pages_processed_per_api_usd",
        "reconciled_pages_per_api_usd",
    ):
        scores[key] = number(run.get(key))
    scores.update(cost_scores(run.get("costs")))
    scores.update(resource_scores(run.get("resources")))
    scores.update(cost_scores(run.get("verified_all_attempt_costs"), "verified_all_attempts_"))
    reconciliation = run.get("cost_reconciliation")
    if isinstance(reconciliation, dict):
        scores.update(cost_scores(reconciliation.get("reconciled"), "reconciled_"))
    return {k: v for k, v in scores.items() if v is not None}


def run_metadata(queue: str, arm: str, path: Path, run: dict[str, Any]) -> dict[str, Any]:
    """Scalar run configuration and provenance."""
    config = mapping(run.get("config"))
    meta: dict[str, Any] = {
        "campaign": "P003",
        "queue": queue,
        "arm": arm,
        "evaluation_name": run.get("name"),
        "variant": variant(path) or "primary",
        "source": rel(path),
        "evaluation_scope": run.get("evaluation_scope"),
        "cohort": run.get("cohort"),
        "dataset_sha256": run.get("dataset_sha256"),
        "report_sha256": run.get("report_sha256"),
        "cost_scope": (run.get("costs") or {}).get("scope"),
        "cost_bases": json.dumps((run.get("costs") or {}).get("cost_bases") or {}, sort_keys=True),
        "resource_scope": (run.get("resources") or {}).get("measurement"),
        "failure_categories": json.dumps(run.get("failure_categories") or {}, sort_keys=True),
        "aggregate_check": aggregate_check(run),
    }
    meta.update({f"config_{k}": config.get(k) for k in CONFIG_META if k in config})
    return meta


def rows_for(run: dict[str, Any], directory: Path) -> list[Row]:
    """One row per page score, keeping failed and unscored pages."""
    artifacts = {a.get("id"): a for a in run.get("artifacts") or [] if isinstance(a, dict)}
    config = mapping(run.get("config"))
    rows = []
    for page in run.get("page_scores") or []:
        page_id = str(page.get("id"))
        artifact = artifacts.get(page_id, {})
        markdown = directory / f"{page_id}.md"
        output: dict[str, Any] = {
            "operational": artifact.get("operational"),
            "markdown": {"path": rel(markdown), "sha256": artifact.get("markdown_sha256")}
            if artifact.get("markdown_sha256") and markdown.is_file()
            else None,
            "result_sha256": artifact.get("result_sha256"),
            "matches": len(page.get("matches") or []),
        }
        rows.append(
            Row(
                item_key=page_id,
                output=output,
                scores=dict(page_terms(page)),
                metadata={
                    "status": page_status(page),
                    "model": config.get("model"),
                    "generation_model": config.get("generation_model"),
                    "evaluation_scope": run.get("evaluation_scope"),
                },
                name=f"{run.get('name')}/{page_id}",
            )
        )
    return rows


def treatment_runs(value: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize offline treatment grids (``treatments`` dict or list) to the evaluation run shape."""
    treatments = value.get("treatments")
    if isinstance(treatments, dict):
        named = list(treatments.items())
    elif isinstance(treatments, list):
        named = []
        for index, entry in enumerate(treatments):
            profile = entry.get("profile") if isinstance(entry, dict) else None
            label = "-".join(f"{k}{v}" for k, v in sorted(profile.items())) if isinstance(profile, dict) else ""
            named.append((label or f"treatment-{index}", entry))
    else:
        return []
    runs = []
    for name, entry in named:
        if not isinstance(entry, dict):
            continue
        pages = entry.get("pages", entry.get("page_scores"))
        runs.append(
            {
                "name": str(name),
                "page_scores": pages,
                "scores": entry.get("totals", entry.get("scores")),
                "positive_macro": entry.get("positive_macro"),
                "evaluation_scope": value.get("scope"),
                "dataset_sha256": value.get("dataset_sha256"),
                "intended_pages": len(pages) if isinstance(pages, list) else None,
                "status_counts": entry.get("status_counts"),
            }
        )
    return runs


def collect(artifacts: Path) -> Iterable[Experiment]:  # noqa: C901, PLR0912 - one grouping pass.
    """Group every primary evaluation run by queue and gold page set."""
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    skipped: Counter[str] = Counter()
    reconciled: dict[tuple[str, str], dict[str, Any]] = {}
    entries = []
    for queue, arm, path in discover(artifacts):
        value = load(path)
        if isinstance(value, dict) and "treatments" in value and "runs" not in value:
            queue = arm if queue == "standalone" else queue  # noqa: PLW2901 - one dataset per treatment grid.
            value = {"runs": treatment_runs(value)}
        elif isinstance(value, dict) and isinstance(value.get("page_scores"), list) and "runs" not in value:
            value = {"runs": [value]}  # A bare single-run evaluation (independent topology replays).
        if not isinstance(value, dict) or not isinstance(value.get("runs"), list):
            skipped[queue] += 1
            continue
        runs = [r for r in value["runs"] if isinstance(r, dict) and isinstance(r.get("page_scores"), list)]
        verified = value.get("verified_continuation_measurements")
        if isinstance(verified, dict) and isinstance(verified.get("all_attempt_costs"), dict):
            runs = [{**r, "verified_all_attempt_costs": verified["all_attempt_costs"]} for r in runs]
        if not runs:
            skipped[queue] += 1
            continue
        if variant(path) == "cost-reconciled":
            for run in runs:
                reconciled[(str(path.parent), str(run.get("name")))] = run
            continue
        entries.append((queue, arm, path, runs))
    known = {
        digest(sorted(str(p.get("id")) for p in run["page_scores"])): run["dataset_sha256"]
        for _, _, _, runs in entries
        for run in runs
        if run.get("dataset_sha256")
    }
    for queue, arm, path, runs in entries:
        for run in runs:
            overlay = reconciled.get((str(path.parent), str(run.get("name"))))
            if overlay is not None and not variant(path):
                run = {  # noqa: PLW2901 - overlay reconciled costs only.
                    **run,
                    "cost_reconciliation": overlay.get("cost_reconciliation"),
                    "reconciled_pages_per_api_usd": overlay.get("reconciled_pages_per_api_usd"),
                }
            pages = sorted(str(p.get("id")) for p in run["page_scores"])
            sha = run.get("dataset_sha256") or known.get(digest(pages)) or "unknown"
            run["dataset_sha256"] = sha
            label = gold_label(str(sha), pages)
            group_key = (queue, f"{label}|{digest(pages, 8)}")
            group = groups.setdefault(
                group_key, {"label": label, "pages": pages, "runs": [], "expected": defaultdict(list)}
            )
            name = arm if len(runs) == 1 or run.get("name") == arm else f"{arm}:{run.get('name')}"
            if queue == arm:
                name = str(run.get("name"))
            if variant(path):
                name = f"{name} [{variant(path)}]"
            group["runs"].append((name, path, run))
            for page in run["page_scores"]:
                expected = {k: page.get(k) for k in EXPECTED_KEYS}
                group["expected"][str(page.get("id"))].append(
                    (expected, run.get("dataset_sha256"), run.get("manifest_sha256"))
                )
    labels_by_queue: dict[str, list[str]] = defaultdict(list)
    for queue, key in sorted(groups):
        labels_by_queue[queue].append(key)
    for (queue, key), group in sorted(groups.items()):
        label = group["label"]
        dataset_label = label if len([k for k in labels_by_queue[queue] if k.split("|")[0] == label]) == 1 else key
        dataset_label = dataset_label.replace("|", "-")
        items = []
        for page_id in group["pages"]:
            observations = group["expected"][page_id]
            counts = Counter(json.dumps(e, sort_keys=True) for e, _, _ in observations)
            expected = json.loads(counts.most_common(1)[0][0])
            items.append(
                Item(
                    key=page_id,
                    input={"page_id": page_id, "gold_dataset_sha256": observations[0][1], "campaign": "P003"},
                    expected=expected,
                    metadata={
                        "gold": label,
                        "manifest_sha256": observations[0][2],
                        "expected_variants": len(counts),
                    },
                )
            )
        runs_out = []
        seen: Counter[str] = Counter()
        for name, path, run in sorted(group["runs"], key=lambda r: (r[0], str(r[1]))):
            seen[name] += 1
            unique = name if seen[name] == 1 else f"{name}#{seen[name]}"
            runs_out.append(
                Run(
                    name=f"{queue}/{unique}",
                    description=f"P003 {queue} arm {run.get('name')} ({run.get('evaluation_scope')}); {rel(path)}",
                    rows=rows_for(run, path.parent),
                    metadata=run_metadata(queue, name, path, run),
                    scores=dict(run_scores(run)),
                )
            )
        yield Experiment(
            dataset=f"{PREFIX}/{queue}/{dataset_label}",
            description=(
                f"P003 {queue}: independently verified table-structure evaluations on the {label} gold page set. "
                "Items are pages; runs are arms (model/configuration/treatment); all intended pages stay in rows."
            ),
            items=items,
            runs=runs_out,
            source=rel(artifacts / CAMPAIGN / ("" if queue in {"standalone", "transcription-screen-v1"} else queue)),
            labels={"split": "DEV", "heldout": False, "campaign": "P003", "skipped_files": skipped.get(queue, 0)},
        )
