"""P003 ``extension-v1`` decision arms as Langfuse experiments.

``extension-v1`` evaluates hosted decision models that edit a retained baseline
table extraction: ``screen`` arms choose among differences, ``local`` / ``l3``
/ ``wild`` arms run bounded local continuation steps. Each finished arm keeps a
root-owned score file (``score-v1.json`` or ``local-score-v1.json``) with
per-page outcomes and three page-level scorings (strict, dual-score v2 content,
wrap diagnostic) for the composed output, the model-selected-only output and
the baseline.

- Dataset ``exp/pipeline-p003/extension-v1/<families>-<n>p``: one per frozen
  page set (screen and local arms share the eight family pages). Items are
  pages: identity, corpus manifest hash and source hash as input; reference
  table/cell/character counts and positive/negative label as expected output.
- Runs: one per arm with a parseable score file; arms still running (no score
  file yet) are skipped and counted in the dataset labels.
- Rows: composed-output strict page counters (as in ``pipeline_p003``), the
  model-selected-only and baseline strict anchors, ``selected`` /
  ``model_credit`` flags and per-metric ``*_improved`` / ``*_regressed`` /
  ``*_unchanged`` change flags. Failures, abstentions and not-attempted pages
  remain rows; baseline retention is not model success (``model_credit``).
- Run scores: composed strict totals and positive macro, model-only and
  baseline strict anchors, v2 and wrap content precision/recall, per-metric
  comparison counts, costs (provider-reported kept apart from effective and
  reserved) and CPU/RSS. ``metadata["aggregate_check"]`` re-sums the page rows.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, digest
from bench.langfuse_adapters.pipeline_p003 import (
    CAMPAIGN,
    EXPECTED_KEYS,
    PREFIX,
    aggregate_check,
    cost_scores,
    load,
    number,
    page_terms,
    rel,
    resource_scores,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "pipeline-p003-extension"
STUDY = "extension-v1"
SCORE_FILES = ("local-score-v1.json", "score-v1.json")
METRICS = ("strict", "v2", "wrap")
CHANGES = ("improved", "regressed", "unchanged")


def family(arm: str) -> str:
    """Arm family token (``screen``, ``local``, ``l3``, ``wild``)."""
    parts = arm.split("-")
    return parts[2] if len(parts) > 2 else arm  # noqa: PLR2004 - extension-v1-<family>-...


def strict_pages(block: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Strict per-page scores keyed by page ID."""
    pages = ((block or {}).get("strict") or {}).get("pages") or []
    return {str(p.get("id")): p for p in pages if isinstance(p, dict)}


def changes(page: dict[str, Any]) -> dict[str, str]:
    """Per-metric change labels for screen and local score schemas."""
    if isinstance(page.get("changes"), dict):
        return {k: str(v) for k, v in page["changes"].items()}
    labels = {k: str(v) for k, v in (page.get("secondary_changes") or {}).items()}
    if page.get("strict_change") is not None:
        labels["strict"] = str(page["strict_change"])
    return labels


def row_for(arm: str, page_id: str, page: dict[str, Any], views: dict[str, Any]) -> Row:
    """One page outcome with composed, model-only and baseline anchors."""
    composed = views["composed"].get(page_id)
    model_only, baseline = views["model_only"], views["baseline"]
    status = page.get("status", page.get("effective_status", "missing"))
    scores: dict[str, Any] = dict(page_terms(composed)) if composed else {}
    for prefix, pages in (("model_only_", model_only), ("baseline_", baseline)):
        anchor = pages.get(page_id)
        if anchor and anchor.get("structural_scored") is not False:
            scores[f"{prefix}strict_exact_cells"] = number(anchor.get("strict_exact_cells"))
            scores[f"{prefix}exact_page"] = number(anchor.get("exact_page"))
            scores[f"{prefix}complete_tables"] = number(anchor.get("complete_tables"))
    scores["selected"] = status == "selected"
    if "model_credit" in page:
        scores["model_credit"] = number(page.get("model_credit"))
    if "accepted_steps" in page:
        scores["accepted_steps"] = number(page.get("accepted_steps"))
    if "model_negative_presence_correct" in page:
        scores["model_negative_presence_correct"] = number(page.get("model_negative_presence_correct"))
    labels = changes(page)
    for metric, label in labels.items():
        for change in CHANGES:
            scores[f"{metric}_{change}"] = label == change
    return Row(
        item_key=page_id,
        output={
            "status": status,
            "reported_status": page.get("reported_status"),
            "changes": labels,
            "stop_reason": page.get("stop_reason"),
            "invalid_reason": page.get("invalid_reason"),
            "selected_sha256": page.get("selected_sha256"),
        },
        scores=scores,
        metadata={
            "status": status,
            "model": views["model"],
            "failed_continuation": page.get("failed_continuation"),
            "baseline_retained": page.get("baseline_retained", page.get("baseline_retained_in_composed")),
        },
        name=f"{arm}/{page_id}",
    )


def content_scores(prefix: str, block: dict[str, Any] | None) -> dict[str, float | None]:
    """Strict totals plus v2/wrap content precision and recall for one scoring view."""
    out: dict[str, float | None] = {}
    block = block or {}
    strict = block.get("strict") or {}
    totals = strict.get("totals") or {}
    for key in (
        "strict_exact_cells",
        "complete_tables",
        "exact_page",
        "expected_cells",
        "error",
        "false_positive_page",
    ):
        out[f"{prefix}total_{key}"] = number(totals.get(key))
    for key, value in (strict.get("positive_macro") or {}).items():
        out[f"{prefix}positive_macro_{key}"] = number(value)
    for metric in ("v2", "wrap"):
        part = block.get(metric) or {}
        for key in ("full_content_precision", "full_content_recall", "covered_content_precision"):
            out[f"{prefix}{metric}_{key}"] = number(part.get(key))
        out[f"{prefix}{metric}_covered_content_recall"] = number(part.get("covered_content_recall"))
    return out


def run_for(arm: Path, path: Path, score: dict[str, Any]) -> Run:
    """Build one run from an extension arm score file."""
    config = score.get("config") or {}
    pages = {str(p.get("id")): p for p in score.get("pages") or [] if isinstance(p, dict)}
    ids = [str(i) for i in config.get("page_ids") or pages]
    views = {
        "composed": strict_pages(score.get("composed_with_baseline_retention")),
        "model_only": strict_pages(score.get("terminal_model_selected_only") or score.get("model_selected_only")),
        "baseline": strict_pages(score.get("native_baseline") or score.get("baseline")),
        "model": config.get("model"),
    }
    rows = [row_for(arm.name, page_id, pages.get(page_id, {"status": "missing"}), views) for page_id in ids]
    composed = score.get("composed_with_baseline_retention") or {}
    strict = composed.get("strict") or {}
    check = aggregate_check(
        {
            "page_scores": strict.get("pages") or [],
            "scores": strict.get("totals") or {},
            "positive_macro": strict.get("positive_macro") or {},
            "intended_pages": score.get("intended_pages"),
        }
    )
    problems = [] if check == "ok" else [check]
    for metric, counts in (score.get("comparisons_by_metric") or {}).items():
        for change in CHANGES:
            summed = sum(float(bool(r.scores.get(f"{metric}_{change}"))) for r in rows)
            if change in counts and summed != counts[change]:
                problems.append(f"{metric}.{change}: rows {summed:g} != reported {counts[change]}")
    scores: dict[str, float | None] = {
        f"total_{k}": number(v) for k, v in (strict.get("totals") or {}).items() if number(v) is not None
    }
    for key, value in (strict.get("positive_macro") or {}).items():
        scores[f"positive_macro_{key}"] = number(value)
    scores.update(content_scores("", {k: v for k, v in composed.items() if k != "strict"}))
    scores.update(
        content_scores("model_only_", score.get("terminal_model_selected_only") or score.get("model_selected_only"))
    )
    scores.update(content_scores("baseline_", score.get("native_baseline") or score.get("baseline")))
    for metric, counts in (score.get("comparisons_by_metric") or {}).items():
        for key, value in counts.items():
            scores[f"{metric}_{key}_pages"] = number(value)
    for key, value in (score.get("status_counts") or {}).items():
        scores[f"status_{key}_pages"] = number(value)
    scores["intended_pages"] = number(score.get("intended_pages"))
    scores.update(cost_scores(score.get("costs")))
    scores.update(resource_scores(score.get("run_resources") or score.get("resources")))
    return Run(
        name=f"{STUDY}/{arm.name}",
        description=f"P003 extension-v1 arm {arm.name} ({config.get('model')}); {rel(path)}",
        rows=rows,
        metadata={
            "campaign": "P003",
            "queue": STUDY,
            "arm": arm.name,
            "family": family(arm.name),
            "source": rel(path),
            "scope": score.get("scope"),
            "cost_scope": (score.get("costs") or {}).get("cost_scope"),
            "corpus_dataset_sha256": ((score.get("receipts") or {}).get("corpus") or {}).get("dataset_sha256"),
            "aggregate_check": "ok" if not problems else "; ".join(problems),
            **{f"config_{k}": v for k, v in config.items() if isinstance(v, (str, int, float, bool))},
        },
        scores={k: v for k, v in scores.items() if v is not None},
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Group finished extension arms by frozen page set, holding one score file in memory at a time."""
    root = artifacts / CAMPAIGN / STUDY / "runs"
    if not root.is_dir():
        return
    groups: dict[str, dict[str, Any]] = {}
    skipped = 0
    for arm in sorted(p for p in root.iterdir() if p.is_dir()):
        score, path = None, None
        for name in SCORE_FILES:
            candidate = arm / name
            value = load(candidate) if candidate.is_file() else None
            if isinstance(value, dict) and isinstance(value.get("pages"), list):
                score, path = value, candidate
                break
        if score is None or path is None:
            skipped += 1
            continue
        ids = sorted(str(i) for i in (score.get("config") or {}).get("page_ids") or [])
        group = groups.setdefault(
            digest(ids, 12),
            {"ids": ids, "runs": [], "families": set(), "observed": {}, "source": {}, "corpus": None, "dataset": None},
        )
        group["runs"].append(run_for(arm, path, score))
        group["families"].add(family(arm.name))
        for page_id, page in strict_pages(score.get("composed_with_baseline_retention")).items():
            expected = json.dumps({k: page.get(k) for k in EXPECTED_KEYS}, sort_keys=True)
            group["observed"].setdefault(page_id, Counter())[expected] += 1
        frozen = load(arm / "frozen.json") or {}
        group["corpus"] = group["corpus"] or frozen.get("corpus")
        for page in frozen.get("pages") or []:
            if isinstance(page, dict):
                group["source"].setdefault(str(page.get("id")), page.get("sha256"))
        group["dataset"] = group["dataset"] or ((score.get("receipts") or {}).get("corpus") or {}).get("dataset_sha256")
        del score
    for group in sorted(groups.values(), key=lambda g: (len(g["ids"]), sorted(g["families"]))):
        label = f"{'+'.join(sorted(group['families']))}-{len(group['ids'])}p"
        observed = group["observed"]
        corpus = "/".join(str(group["corpus"]).split("/")[-3:]) if group["corpus"] else None
        items = [
            Item(
                key=page_id,
                input={
                    "page_id": page_id,
                    "source_sha256": group["source"].get(page_id),
                    "corpus": corpus,
                    "corpus_dataset_sha256": group["dataset"],
                },
                expected=json.loads(observed[page_id].most_common(1)[0][0]) if page_id in observed else None,
                metadata={"expected_variants": len(observed.get(page_id, ()))},
            )
            for page_id in group["ids"]
        ]
        yield Experiment(
            dataset=f"{PREFIX}/{STUDY}/{label}",
            description=(
                "P003 extension-v1: hosted decision models editing retained baseline extractions. "
                "Rows score the composed output; model credit, baseline anchors and change flags are separate."
            ),
            items=items,
            runs=group["runs"],
            source=rel(root),
            labels={"split": "DEV", "heldout": False, "campaign": "P003", "skipped_unscored_arms": skipped},
        )
