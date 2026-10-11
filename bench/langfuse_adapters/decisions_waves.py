"""Image, row, operation-log, evidence-screen, and OmniDoc presence decision waves.

Covered retained artifacts under ``decisions/``:

- ``image-context``, ``image-clef-bounded``, ``image-silver-bounded``
  (``bench/decision_image_run.py``): A/B/unresolved assembly choices or
  silver table presence over image size/mode/blank arms. Runs are
  model/scope/arm; observations reuse their retained ``score``. Cases in failed
  or unattempted batches stay as unscored rows (the retained ``n`` excludes
  them and ``errors``/``unattempted`` count them).
- ``row-decisions-r001`` and ``row-decisions-r001-parser-v2``
  (``bench/decision_row_run.py``): row-fragment selectors; runs are model/arm.
- ``oplog-pilot-512`` (``bench/decision_oplog_run.py``): multi-step operation
  sessions; one row per session with its retained final score.
- ``evidence-screen-v1`` (``bench/decision_evidence_screen.py``): ruled-table
  presence with three evidence arms; missing answers count as unresolved.
- ``omnidoc-dev-presence-*`` (``bench/omnidoc_decisions.py``): three
  presence questions (table, display math, multiple columns) per page image;
  unknown labels and non-ok requests stay unscored, as in the retained
  confusion matrices.

``image-silver`` and ``image-clef-corrected`` retain only request freezes
(no results), so they are not converted. Run scores are recomputed from rows
and compared with the retained summary or evaluation; differences are recorded
in ``metadata["retained_mismatch"]``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.decisions_common import (
    DECISION_THRESHOLD,
    average,
    catalog_prices,
    choice_scores,
    cost_fields,
    cost_summary,
    flag,
    mismatches,
    relative,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

NAME = "decisions_waves"

IMAGE_WAVES = ("image-context", "image-clef-bounded", "image-silver-bounded")
ROW_WAVES = ("row-decisions-r001", "row-decisions-r001-parser-v2")
ROW_SCORES = (
    "selector_exact",
    "selector_accuracy",
    "region_exact",
    "record_f1",
    "record_precision",
    "record_recall",
    "candidate_coverage",
    "candidate_complete",
    "valid",
    "source_conservation",
    "headers_immutable",
)
OPLOG_SCORES = (
    "source_group_exact",
    "row_column_exact",
    "placement_scored_sources",
    "placement_correct_sources",
    "pair_precision",
    "pair_recall",
    "conservation",
)
OMNIDOC_QUESTIONS = ("table", "display_math", "multiple_columns")


def _cost(root: Path, holder: Mapping[str, Any], model: str) -> dict[str, Any]:
    entry = holder.get("entry")
    return cost_fields(entry, holder.get("usage"), catalog_prices(root).get(model)) if entry else {}


def _run_cost(rows: list[Row]) -> dict[str, Any]:
    return {f"cost_{key}": value for key, value in cost_summary(row.metadata for row in rows).items()}


# Image waves -----------------------------------------------------------------------------------------------------


def _image_wave(root: Path, wave: Path) -> Experiment | None:
    results_path = wave / "results.json"
    if not results_path.exists():
        return None
    batches = read_json(results_path).get("batches", [])
    summary_path = wave / "summary.json"
    retained = (
        {(row["model"], row["scope"], row["arm"]): row for row in read_json(summary_path).get("rows", [])}
        if summary_path.exists()
        else {}
    )
    items: dict[str, Item] = {}
    groups: dict[tuple[str, str, str], list[Row]] = {}
    for batch in batches:
        model, scope, arm = batch["model"], batch["scope"], batch["arm"]
        observations = {obs["case_id"]: obs for obs in batch.get("observations", [])}
        accounting = _cost(root, batch, model)
        for index, case_id in enumerate(batch["case_ids"]):
            expected = (batch.get("expected_document") or [None] * len(batch["case_ids"]))[index]
            items.setdefault(
                case_id,
                Item(
                    key=case_id,
                    input={"case_id": case_id, "source_sha256": (batch.get("source_sha256") or [None])[index]},
                    expected={"document": expected},
                ),
            )
            obs = observations.get(case_id)
            scores: dict[str, float | None] = {}
            output: dict[str, Any] = {}
            if obs is not None:
                score = obs.get("score") or {}
                scores = {
                    "region_exact": flag(score.get("region_exact")),
                    "record_f1": flag(score.get("record_f1")),
                    **choice_scores(obs.get("answer"), obs.get("expected_document", expected)),
                }
                output = {
                    "choice": (obs.get("answer") or {}).get("choice"),
                    "probabilities": (obs.get("answer") or {}).get("probabilities"),
                }
            groups.setdefault((model, scope, arm), []).append(
                Row(
                    item_key=case_id,
                    output=output,
                    scores={key: value for key, value in scores.items() if value is not None},
                    metadata={
                        "status": batch["status"] if obs is None else "ok",
                        "batch_status": batch["status"],
                        "configuration": ", ".join(
                            f"{k}={v}" for k, v in sorted(batch.get("configuration", {}).items())
                        ),
                        **accounting,
                    },
                )
            )
    runs = []
    for (model, scope, arm), rows in groups.items():
        scored = [row for row in rows if row.metadata["status"] == "ok"]
        recount: dict[str, Any] = {
            "n": len(scored),
            "exact": sum(row.scores.get("region_exact") or 0 for row in scored),
            "unattempted": sum(row.metadata["batch_status"] == "unattempted" for row in rows),
        }
        f1 = [row.scores["record_f1"] for row in scored if "record_f1" in row.scores]
        summary = retained.get((model, scope, arm), {})
        scores = {
            **recount,
            "exact_rate": recount["exact"] / len(scored) if scored else None,
            "mean_record_f1": average(f1),
            "errors": summary.get("errors"),
            "abstained": sum(row.scores.get("abstained") or 0 for row in scored),
        }
        for key in ("tp", "fp", "fn", "tn", "precision", "recall", "specificity", "paired_blank_exact_delta"):
            if summary.get(key) is not None:
                scores[key] = summary[key]
        problems = mismatches({key: summary[key] for key in recount if key in summary}, recount) if summary else []
        runs.append(
            Run(
                name=f"{model}/{scope}/{arm}",
                description=f"{wave.name}: {model}, {scope} scope, image arm {arm}.",
                rows=rows,
                scores=scores,
                metadata={
                    "wave": wave.name,
                    "model": model,
                    "scope": scope,
                    "arm": arm,
                    "retained_effective_usd": summary.get("effective_usd"),
                    "retained_cost_estimated": summary.get("cost_estimated"),
                    "retained_mismatch": "; ".join(problems) or (None if summary else "no retained summary row"),
                    **_run_cost(rows),
                },
            )
        )
    manifest = read_json(wave / "manifest.json") if (wave / "manifest.json").exists() else {}
    return Experiment(
        dataset=f"exp/decisions/{wave.name}",
        description=f"{wave.name}: {manifest.get('task', 'image decision')}; {manifest.get('dev_status', 'DEV')}.",
        items=list(items.values()),
        runs=runs,
        source=relative(wave),
    )


# Row-fragment selector waves -------------------------------------------------------------------------------------


def _row_wave(root: Path, wave: Path) -> Experiment | None:
    if not (wave / "results.json").exists():
        return None
    records = read_json(wave / "results.json").get("records", [])
    summary_path = wave / "summary.json"
    retained = (
        {(row["model"], row["arm"]): row for row in read_json(summary_path).get("rows", [])}
        if summary_path.exists()
        else {}
    )
    items: dict[str, Item] = {}
    groups: dict[tuple[str, str], list[Row]] = {}
    for record in records:
        items.setdefault(
            record["case_id"],
            Item(
                key=record["case_id"],
                input={"case_id": record["case_id"], "source_sha256": record.get("source_sha256")},
                expected=None,
                metadata={"case_index": record.get("case_index")},
            ),
        )
        score = record.get("score") or {}
        groups.setdefault((record["model"], record["arm"]), []).append(
            Row(
                item_key=record["case_id"],
                output={
                    "assignments": score.get("assignments"),
                    "selector_by_fragment": score.get("selector_by_fragment"),
                },
                scores={name: flag(score.get(name)) for name in ROW_SCORES if flag(score.get(name)) is not None}
                if record.get("status") == "ok"
                else {},
                metadata={
                    "status": record.get("status"),
                    "replayed": bool(record.get("replayed")),
                    **_cost(root, record, record["model"]),
                },
            )
        )
    runs = []
    for (model, arm), rows in groups.items():
        summary = retained.get((model, arm), {})
        scored = [row for row in rows if row.metadata["status"] == "ok"]
        recount = {
            "scored": len(scored),
            "region_exact": sum(row.scores.get("region_exact") or 0 for row in scored),
            "inputs": len(rows),
        }
        scores: dict[str, Any] = {
            key: summary.get(key)
            for key in (
                "inputs",
                "scored",
                "errors",
                "unattempted",
                "fragments",
                "correct_fragments",
                "fragment_accuracy",
                "region_exact",
                "record_f1",
                "lost_source",
                "unresolved_fragments",
                "candidate_oracle_covered",
                "candidate_oracle_total",
            )
            if key in summary
        } or dict(recount)
        runs.append(
            Run(
                name=f"{model}/{arm}",
                description=f"{wave.name}: {model}, arm {arm}; row-fragment selector with exact region assembly.",
                rows=rows,
                scores=scores,
                metadata={
                    "wave": wave.name,
                    "model": model,
                    "arm": arm,
                    "retained_effective_usd": summary.get("effective_usd"),
                    "retained_cost_estimated": summary.get("cost_estimated"),
                    "retained_mismatch": "; ".join(
                        mismatches({key: summary[key] for key in recount if key in summary}, recount)
                    )
                    or (None if summary else "no retained summary row"),
                    **_run_cost(rows),
                },
            )
        )
    return Experiment(
        dataset=f"exp/decisions/{wave.name}",
        description=f"{wave.name}: R001 row-fragment selector decisions on authored DEV context PDFs.",
        items=list(items.values()),
        runs=runs,
        source=relative(wave),
    )


# Operation-log pilot ---------------------------------------------------------------------------------------------


def _oplog(root: Path, wave: Path) -> Experiment | None:
    if not (wave / "results.json").exists():
        return None
    results = read_json(wave / "results.json")
    manifest = read_json(wave / "manifest.json") if (wave / "manifest.json").exists() else {}
    cases = {case["index"]: case for case in manifest.get("cases", [])}
    calls: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for call in results.get("calls", []):
        calls.setdefault((call["model"], call["case_index"]), []).append(call)
    items: dict[str, Item] = {}
    groups: dict[str, list[Row]] = {}
    for session in results.get("sessions", []):
        key = f"case-{session['case_index']:02d}"
        case = cases.get(session["case_index"], {})
        score = session.get("score") or {}
        items.setdefault(
            key,
            Item(
                key=key,
                input={
                    "case_index": session["case_index"],
                    "source_sha256": case.get("source_sha256"),
                    "initial_state_sha256": case.get("initial_state_sha256"),
                    "image_sha256": case.get("image_sha256"),
                },
                expected={"assembly": score.get("expected")},
            ),
        )
        steps = calls.get((session["model"], session["case_index"]), [])
        accounting = [_cost(root, call, session["model"]) for call in steps]
        groups.setdefault(session["model"], []).append(
            Row(
                item_key=key,
                output={"selected": score.get("selected"), "steps": len(steps)},
                scores={
                    **{name: flag(score.get(name)) for name in OPLOG_SCORES if flag(score.get(name)) is not None},
                    "selected_expected": flag(score.get("selected") == score.get("expected")),
                },
                metadata={
                    "status": session.get("stop_reason"),
                    "steps": len(steps),
                    "failed_steps": sum(call.get("status") != "ok" for call in steps),
                    **{
                        f"session_{key}": value
                        for key, value in cost_summary(accounting).items()
                        if key in ("unique_requests", "provider_reported_usd", "effective_usd", "estimated_usd")
                    },
                },
            )
        )
    runs = []
    for model, rows in groups.items():
        steps = [
            _cost(root, call, model)
            for (call_model, _), members in calls.items()
            if call_model == model
            for call in members
        ]
        recall = [row.scores["pair_recall"] for row in rows if "pair_recall" in row.scores]
        runs.append(
            Run(
                name=model,
                description=f"Operation-log pilot (512 px): {model} multi-step source-ID operations per page.",
                rows=rows,
                scores={
                    "sessions": len(rows),
                    "source_group_exact": sum(row.scores.get("source_group_exact") or 0 for row in rows),
                    "row_column_exact": sum(row.scores.get("row_column_exact") or 0 for row in rows),
                    "selected_expected": sum(row.scores.get("selected_expected") or 0 for row in rows),
                    "mean_pair_recall": average(recall),
                    "finished_sessions": sum(row.metadata["status"] == "finished" for row in rows),
                },
                metadata={
                    "wave": wave.name,
                    "model": model,
                    "candidate_oracle": str(results.get("candidate_oracle")),
                    **{f"cost_{key}": value for key, value in cost_summary(steps).items()},
                },
            )
        )
    return Experiment(
        dataset=f"exp/decisions/{wave.name}",
        description="Operation-log pilot: multi-step DEV operation choices over source-ID atoms with a 512 px image.",
        items=list(items.values()),
        runs=runs,
        source=relative(wave),
    )


# Evidence screen -------------------------------------------------------------------------------------------------


def _evidence_screen(root: Path, wave: Path) -> Experiment | None:
    if not (wave / "results.json").exists() or not (wave / "manifest.json").exists():
        return None
    manifest = read_json(wave / "manifest.json")
    gold_path = root.parent / "evidence-designs" / "root-gate-v1" / "scorer-only.json"
    gold = read_json(guard(gold_path)) if gold_path.exists() else {}
    rows_by_key = {(row["id"], row["arm"]): row for row in read_json(wave / "results.json").get("records", [])}
    retained = (
        {row["arm"]: row for row in read_json(wave / "summary.json").get("rows", [])}
        if (wave / "summary.json").exists()
        else {}
    )
    model = manifest.get("model", "")
    items = [
        Item(key=page, input={"page_id": page}, expected={"document": gold.get(page)}) for page in manifest["selected"]
    ]
    runs = []
    for arm in sorted({record["arm"] for record in manifest.get("records", [])}):
        rows = []
        for page in manifest["selected"]:
            record = rows_by_key.get((page, arm), {})
            answer = record.get("answer") or {}
            choice = answer.get("choice", "unresolved")
            expected = gold.get(page)
            response = record.get("response") or {}
            entry = response.get("entry")
            usage = (response.get("result") or {}).get("usage")
            rows.append(
                Row(
                    item_key=page,
                    output={"choice": choice, "probabilities": answer.get("probabilities")},
                    scores={
                        "correct": flag(choice == expected) if expected is not None else None,
                        "unresolved": flag(choice == "unresolved"),
                        **(
                            {"p_expected": flag((answer.get("probabilities") or {}).get(expected))}
                            if expected is not None and answer.get("probabilities")
                            else {}
                        ),
                    },
                    metadata={
                        "status": record.get("status", "missing"),
                        **(cost_fields(entry, usage, catalog_prices(root).get(model)) if entry else {}),
                    },
                )
            )
        recount = {
            "tp": sum(gold.get(row.item_key) == "A" and row.output["choice"] == "A" for row in rows),
            "fp": sum(gold.get(row.item_key) == "B" and row.output["choice"] == "A" for row in rows),
            "fn": sum(gold.get(row.item_key) == "A" and row.output["choice"] != "A" for row in rows),
            "tn": sum(gold.get(row.item_key) == "B" and row.output["choice"] == "B" for row in rows),
            "unresolved": sum(row.output["choice"] == "unresolved" for row in rows),
        }
        summary = retained.get(arm, {})
        runs.append(
            Run(
                name=f"{model}/{arm}",
                description=f"D001 source-selected evidence screen, arm {arm}: ruled-table presence on 12 DEV pages.",
                rows=rows,
                scores={**recount, "correct": recount["tp"] + recount["tn"], "pages": len(rows)},
                metadata={
                    "model": model,
                    "arm": arm,
                    "retained_effective_usd": summary.get("effective_usd"),
                    "retained_mismatch": "; ".join(
                        mismatches({key: summary[key] for key in recount if key in summary}, recount)
                    )
                    or (None if summary else "no retained summary row"),
                    **_run_cost(rows),
                },
            )
        )
    return Experiment(
        dataset=f"exp/decisions/{wave.name}",
        description="D001 evidence screen: twelve DEV pages chosen by source-grid presence; three evidence arms.",
        items=items,
        runs=runs,
        source=relative(wave),
    )


# OmniDoc presence ------------------------------------------------------------------------------------------------


def _omnidoc(root: Path, wave: Path) -> Experiment | None:  # noqa: C901, PLR0912 - one retained confusion layout.
    manifest_path, labels_path = wave / "manifest.json", wave / "private-labels.json"
    if not manifest_path.exists() or not labels_path.exists():
        return None
    manifest = read_json(manifest_path)
    labels = {row["key"]: row["labels"] for row in read_json(labels_path)["observations"]}
    results = read_json(wave / "results.json").get("rows", []) if (wave / "results.json").exists() else []
    retained_rows = {row["key"]: row for row in results}
    evaluation = read_json(wave / "evaluation.json") if (wave / "evaluation.json").exists() else {}
    items: dict[str, Item] = {}
    groups: dict[str, list[Row]] = {}
    for record in manifest["requests"]:
        observation = record["key"].split("/", 1)[0]
        item_key = f"{observation}/{record['arm']}"
        expected = labels[record["key"]]
        if item_key in items and items[item_key].expected["labels"] != expected:
            message = f"{wave.name}: labels differ across models for {item_key}"
            raise ValueError(message)
        items.setdefault(
            item_key,
            Item(
                key=item_key,
                input={
                    "observation": observation,
                    "arm": record["arm"],
                    "source_sha256": record.get("source_sha256"),
                    "image_sha256": record.get("image_sha256"),
                    "mime": record.get("mime"),
                    "pixels": record.get("pixels"),
                },
                expected={"labels": expected, "questions": list(OMNIDOC_QUESTIONS)},
                metadata={"arm": record["arm"]},
            ),
        )
        row = retained_rows.get(record["key"])
        status = row["status"] if row else ("refused" if record.get("status") == "refused" else "unattempted")
        row_scores: dict[str, float | None] = {}
        probabilities = (row or {}).get("probabilities") or []
        for index, name in enumerate(OMNIDOC_QUESTIONS):
            if status == "ok" and index < len(probabilities):
                row_scores[f"p_{name}"] = probabilities[index]
                if expected[index] is not None:
                    row_scores[f"{name}_correct"] = flag(
                        (probabilities[index] >= DECISION_THRESHOLD) == expected[index]
                    )
        groups.setdefault(f"{record['model']}/{record['arm']}", []).append(
            Row(
                item_key=item_key,
                output={"probabilities": probabilities} if probabilities else {},
                scores=row_scores,
                metadata={
                    "status": status,
                    "model": record["model"],
                    "arm": record["arm"],
                    **(_cost(root, row, record["model"]) if row else {}),
                },
            )
        )
    runs = []
    for group, rows in groups.items():
        confusion = []
        for index, name in enumerate(OMNIDOC_QUESTIONS):
            cell = dict.fromkeys(("tp", "tn", "fp", "fn", "unknown", "unscored"), 0)
            for row in rows:
                label = items[row.item_key].expected["labels"][index]
                if label is None:
                    cell["unknown"] += 1
                elif row.metadata["status"] != "ok":
                    cell["unscored"] += 1
                else:
                    predicted = row.scores[f"p_{name}"] >= DECISION_THRESHOLD  # type: ignore[operator]
                    cell["tp" if predicted and label else "fp" if predicted else "fn" if label else "tn"] += 1
            confusion.append(cell)
        retained = evaluation.get("groups", {}).get(group, {})
        problems: list[str] = []
        for index, cell in enumerate(confusion):
            if index < len(retained.get("confusion", [])):
                problems.extend(f"q{index}/{item}" for item in mismatches(retained["confusion"][index], cell))
        scores: dict[str, float | None] = {
            "completed_pages": sum(row.metadata["status"] == "ok" for row in rows),
            "logical_pages": len(rows),
        }
        for name, cell in zip(OMNIDOC_QUESTIONS, confusion, strict=True):
            scores.update({f"{name}_{key}": value for key, value in cell.items()})
            scored = cell["tp"] + cell["tn"] + cell["fp"] + cell["fn"]
            scores[f"{name}_accuracy"] = (cell["tp"] + cell["tn"]) / scored if scored else None
        model, arm = group.rsplit("/", 1)
        runs.append(
            Run(
                name=group,
                description=f"{wave.name}: {model}, arm {arm}; table/display-math/multicolumn presence at p ≥ 0.5.",
                rows=rows,
                scores=scores,
                metadata={
                    "wave": wave.name,
                    "model": model,
                    "arm": arm,
                    "retained_effective_usd": retained.get("effective_usd"),
                    "retained_mismatch": "; ".join(problems) or (None if retained else "no retained group"),
                    **_run_cost(rows),
                },
            )
        )
    return Experiment(
        dataset=f"exp/decisions/{wave.name}",
        description=(
            f"{wave.name}: OmniDocBench DEV page images (research-only), presence of tables, display math and "
            "multiple columns; unknown labels unscored; public-benchmark contamination unknown."
        ),
        items=list(items.values()),
        runs=runs,
        source=relative(wave),
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield every retained results/summary decision wave."""
    root = guard(artifacts / "decisions")
    builders = [
        *((root / name, _image_wave) for name in IMAGE_WAVES),
        *((root / name, _row_wave) for name in ROW_WAVES),
        (root / "oplog-pilot-512", _oplog),
        (root / "evidence-screen-v1", _evidence_screen),
    ]
    builders.extend((path, _omnidoc) for path in sorted(root.glob("omnidoc-dev-presence-*")) if path.is_dir())
    for path, builder in builders:
        if guard(path).is_dir():
            experiment = builder(root, path)
            if experiment is not None and experiment.runs:
                yield experiment
