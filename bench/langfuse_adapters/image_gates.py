"""Hosted image-matrix, OCR admission, and source-only table-gate experiments.

Covered artifact directories (under ``bench/results/pdf-master-artifacts/``):

- ``image-axis-context30-v1`` and ``image-anisotropic-only-v1``: context30
  assembly decisions across image size/axis/representation arms. Runs are
  model x arm; rows reuse each observation's retained ``score`` fields.
  Exact-hash geometric aliases share the canonical arm's quality only and carry
  no cost or latency, matching ``bench/image_axes_report.py``.
- ``image-axis-context30-anisotropic-v1``: request freeze only (its anisotropic
  arms were executed in ``image-anisotropic-only-v1``); items only, no runs.
- ``ocr1200-overlap05-admission-v1``: A002 admission per model plus the two
  frozen candidate-ceiling variants, scored by ``bench/rolling_row_run.py``.
- ``source-table-gate-original28-v1`` / ``source-table-gate-realistic28-v2``:
  presence gates per model x prompt, scored by ``bench/source_table_gate_run.py``.
- ``source-neutralized-dev-v1``: source-only deletion ablation freeze; it was
  never sent or scored and its private targets were deliberately never opened,
  so it yields items without expected outputs and no runs.

Request-level charges belong to the batch request. Rows record the batch's
provider-reported charge and the separately labeled effective estimate with
the batch case count; they never split or zero-fill a missing charge.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, file_ref, guard, read_json
from bench.reprice_model_rates import number, request_cost

if TYPE_CHECKING:
    from collections.abc import Iterable

NAME = "image_gates"

IMAGE_RUN_DIRS = ("image-axis-context30-v1", "image-anisotropic-only-v1")
IMAGE_FREEZE_DIRS = ("image-axis-context30-anisotropic-v1",)
OCR_DIRS = ("ocr1200-overlap05-admission-v1",)
GATE_DIRS = ("source-table-gate-original28-v1", "source-table-gate-realistic28-v2")
NEUTRALIZED_DIRS = ("source-neutralized-dev-v1",)
CONTEXT_SCORES = ("region_exact", "record_f1", "record_precision", "record_recall", "valid", "source_conservation")
ADMISSION_SCORES = ("exact_page", "exact_cells", "exact_spans", "owned_values", "owned_words", "false_positive_page")
KINDS = ("borderless", "prose", "ruled-control")
PRESENCE = {"borderless": "table_present", "prose": "not_table"}


def _slug(text: str) -> str:
    return text.replace("-", "_")


def _cost_fields(cost: dict[str, Any] | None, usage: dict[str, Any], entry: dict[str, Any], prefix: str = "") -> dict:
    """Keep provider-reported charges, tokens, and labeled estimates separate; missing stays missing."""
    fields: dict[str, Any] = {}
    reported = number(usage.get("cost", entry.get("provider_reported_usd")))
    if reported is not None:
        fields[f"{prefix}provider_reported_usd"] = reported
    for key in ("input_tokens", "output_tokens"):
        value = number(usage.get(key))
        if value is not None:
            fields[f"{prefix}{key}"] = value
    if cost is not None:
        if cost.get("effective_usd") is not None:
            fields[f"{prefix}effective_usd"] = cost["effective_usd"]
        fields[f"{prefix}cost_basis"] = cost.get("basis")
    if entry.get("cost_status") is not None:
        fields[f"{prefix}ledger_cost_status"] = entry["cost_status"]
    for key in ("served_model", "provider", "index"):
        if entry.get(key) is not None:
            fields[f"{prefix}{'ledger_index' if key == 'index' else key}"] = entry[key]
    elapsed = number(entry.get("elapsed_ms"))
    if elapsed is not None:
        fields[f"{prefix}http_elapsed_ms"] = elapsed
    return fields


def _accounting(costs: list[dict[str, Any]], elapsed: list[float | None]) -> dict[str, float | None]:
    """Total only when every unique request has a known effective cost; keep partial totals separate."""
    known = [c["effective_usd"] for c in costs if c.get("effective_usd") is not None]
    times = [t for t in elapsed if t is not None]
    return {
        "unique_requests": len(costs),
        "effective_usd": sum(known) if costs and len(known) == len(costs) else None,
        "known_partial_usd": sum(known) if costs else None,
        "unknown_cost_requests": len(costs) - len(known),
        "http_elapsed_total_ms": sum(times) if costs and len(times) == len(costs) else None,
    }


# --- context30 image matrices -------------------------------------------------


@cache
def _context_gold() -> dict[str, dict[str, Any]]:
    """Return authored context30 references keyed by source PDF SHA-256 (deterministic, CPU only)."""
    from bench.decision_context_cases import context_cases  # noqa: PLC0415 - lazy, generator import.

    gold = {}
    for case in context_cases():
        digest = hashlib.sha256(case["pdf_bytes"]).hexdigest()
        gold[digest] = {
            "id": case["id"],
            "family": case.get("family"),
            "split": case.get("split"),
            "paired_group": case.get("paired_group"),
            "evidence_modes": case.get("evidence_modes"),
            "source_words": len(case.get("source_words", [])),
            "source": case.get("source"),
            "gold": case.get("gold"),
        }
    return gold


def _source_pdf(artifacts: Path, digest: str, directory: str) -> dict[str, Any]:
    for name in (directory, *IMAGE_FREEZE_DIRS, *IMAGE_RUN_DIRS):
        path = artifacts / name / f"source-{digest}.pdf"
        if guard(path).exists():
            return file_ref(path)
    return {"sha256": digest, "path": None}


def _context_items(artifacts: Path, directory: str, sources: dict[str, str]) -> list[Item]:
    gold = _context_gold()
    items = []
    for case_id, digest in sorted(sources.items()):
        reference = gold.get(digest)
        valid = reference is not None and reference["id"] == case_id
        items.append(
            Item(
                key=case_id,
                input={
                    "case_id": case_id,
                    "source_pdf": _source_pdf(artifacts, digest, directory),
                    **(
                        {k: reference[k] for k in ("family", "paired_group", "evidence_modes", "source_words")}
                        if valid and reference
                        else {}
                    ),
                },
                expected=reference["gold"] if valid and reference else None,
                metadata={
                    "split": reference.get("split", "DEV") if valid and reference else "DEV",
                    "gold_status": "authored DEV reference (bench.decision_context_cases)"
                    if valid
                    else "unavailable: source hash not in authored factory",
                },
            )
        )
    return items


def _context_sources(manifest: dict[str, Any], directory: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    frozen = directory / "source-frozen.json"
    if guard(frozen).exists():
        sources.update({p["id"]: p["source_sha256"] for p in read_json(frozen)["pages"]})
    for batch in manifest["batches"]:
        sources.update(dict(zip(batch["case_ids"], batch["source_sha256"], strict=True)))
    return sources


def _identity(batch: dict[str, Any]) -> tuple[str, str, str, int]:
    return batch["model"], batch.get("scope", "page"), batch["arm"], batch["offset"]


def _image_ref(image: dict[str, Any] | None) -> dict[str, Any] | None:
    if not image:
        return None
    return {k: image.get(k) for k in ("sha256", "bytes", "pixels", "mode", "png_bit_depth", "png_color_type")}


def _context_rows(manifest: dict[str, Any], results: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Group declared and alias batches per model/arm, as ``image_axes_report.snapshot`` does."""
    retained = {_identity(b): b for b in results.get("batches", [])}
    canonical = {(b["model"], b["request_sha256"]): b for b in manifest["batches"]}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for declared in manifest["batches"]:
        actual = retained.get(_identity(declared), {**declared, "status": "unattempted"})
        if actual["request_sha256"] != declared["request_sha256"] or actual["case_ids"] != declared["case_ids"]:
            message = "Retained batch differs from its frozen declaration"
            raise ValueError(message)
        groups[declared["model"], declared["arm"]].append({**declared, **actual, "quality_alias": False})
    for alias in manifest.get("geometric_aliases", []):
        parent = canonical.get((alias["model"], alias["request_sha256"]))
        if parent is None or parent["case_ids"] != alias["case_ids"] or parent["arm"] != alias["canonical_arm"]:
            message = "Geometric alias lacks identical canonical request and case inventory"
            raise ValueError(message)
        actual = retained.get(_identity(parent), {"status": "unattempted"})
        configuration = {**parent.get("configuration", {}), "axis": alias["arm"].split("-")[1]}
        groups[alias["model"], alias["arm"]].append(
            {
                **parent,
                **alias,
                "status": actual["status"],
                "observations": actual.get("observations", []),
                "quality_alias": True,
                "configuration": configuration,
            }
        )
    for refused in manifest.get("refusals", []):
        if "model" in refused and "arm" in refused:
            groups.setdefault((refused["model"], refused["arm"]), [])
    return groups


def _context_run(  # noqa: C901 - mirrors image_axes_report grouping in one pass.
    model: str,
    arm: str,
    batches: list[dict[str, Any]],
    refusals: list[dict[str, Any]],
    prices: dict[str, Any],
) -> Run:
    rows: list[Row] = []
    costs, elapsed, started = [], [], []
    for batch in batches:
        observations = {o["case_id"]: o for o in batch.get("observations", [])}
        entry, usage = batch.get("entry", {}), batch.get("usage", {})
        alias = batch["quality_alias"]
        batch_meta: dict[str, Any] = {
            "request_sha256": batch["request_sha256"],
            "batch_case_count": len(batch["case_ids"]),
            "quality_alias": alias,
            "replayed": batch.get("replayed", False),
        }
        if alias:
            batch_meta["canonical_arm"] = batch.get("canonical_arm")
            batch_meta["cost_note"] = "geometric alias: quality shared, cost/latency unmeasured"
        elif entry:
            cost = request_cost(entry, usage, entry.get("catalog_rates") or prices.get(model, {}))
            if not batch.get("replayed", False):
                costs.append(cost)
                elapsed.append(number(entry.get("elapsed_ms")))
            batch_meta.update(_cost_fields(cost, usage, entry, "batch_"))
        if number(entry.get("started_at")) is not None and not alias:
            started.append(float(entry["started_at"]))
        images = batch.get("images", [])
        for position, case_id in enumerate(batch["case_ids"]):
            observation = observations.get(case_id)
            status = batch["status"] if observation else f"{batch['status']}:unmeasured"
            image = images[position] if position < len(images) else None
            meta = {
                "model": model,
                "arm": arm,
                **batch.get("configuration", {}),
                "status": status,
                **batch_meta,
            }
            if image:
                meta["image_sha256"] = image.get("sha256")
                meta["image_bytes"] = image.get("bytes")
            if observation is None:
                rows.append(Row(case_id, {"status": status}, {}, meta, input={"image": _image_ref(image)}))
                continue
            answer, assembly, score = (
                observation.get("answer", {}),
                observation.get("assembly", {}),
                observation["score"],
            )
            scores: dict[str, Any] = {k: score[k] for k in CONTEXT_SCORES if k in score}
            scores["unresolved"] = answer.get("choice") == "unresolved"
            rows.append(
                Row(
                    case_id,
                    {
                        "choice": answer.get("choice"),
                        "raw_choice": answer.get("raw_choice"),
                        "probabilities": answer.get("probabilities"),
                        "records": assembly.get("records"),
                        "unresolved_ids": assembly.get("unresolved_ids"),
                    },
                    scores,
                    meta,
                    input={"image": _image_ref(image)},
                    started=float(entry["started_at"]) if number(entry.get("started_at")) is not None else None,
                    name=f"{model}/{arm}/{case_id}",
                )
            )
    rows.extend(
        Row(
            case_id,
            {"status": "refused", "reason": refused.get("reason")},
            {},
            {"model": model, "arm": arm, "status": "refused", "stage": refused.get("stage")},
        )
        for refused in refusals
        for case_id in ([refused["case_id"]] if "case_id" in refused else refused.get("case_ids", []))
    )
    declared = {r.item_key for r in rows}
    measured = [r for r in rows if r.scores]
    run_scores: dict[str, Any] = {
        "declared_cases": len(declared),
        "measured_cases": len(measured),
        "unmeasured_cases": len(declared) - len(measured),
        "alias_cases": sum(r.metadata.get("quality_alias", False) for r in measured),
        "unresolved_cases": sum(bool(r.scores.get("unresolved")) for r in measured),
    }
    for key in CONTEXT_SCORES:
        values = [float(v) for r in measured if (v := r.scores.get(key)) is not None]
        if values:
            run_scores[f"{key}_sum"] = sum(values)
            run_scores[f"{key}_mean"] = sum(values) / len(values)
    if "region_exact_sum" in run_scores and declared:
        run_scores["region_exact_per_declared"] = run_scores["region_exact_sum"] / len(declared)
    run_scores.update({k: v for k, v in _accounting(costs, elapsed).items() if v is not None})
    configuration = batches[0].get("configuration", {}) if batches else {}
    return Run(
        name=f"{model}/{arm}",
        description=f"{model} on context30 image arm {arm}; aliases share canonical quality only.",
        rows=rows,
        metadata={
            "model": model,
            "arm": arm,
            **{f"config_{k}": v for k, v in configuration.items()},
            "quality_reference_arms": sorted({b["canonical_arm"] for b in batches if b["quality_alias"]}),
        },
        scores=run_scores,
        started=min(started) if started else None,
    )


def _image_experiment(artifacts: Path, directory: str) -> Experiment | None:
    base = guard(artifacts / directory)
    if not (base / "manifest.json").exists():
        return None
    manifest = read_json(base / "manifest.json")
    results_path = base / "results.json"
    has_results = results_path.exists()
    results = read_json(results_path) if has_results else {"batches": []}
    sources = _context_sources(manifest, base)
    items = _context_items(artifacts, directory, sources)
    runs: list[Run] = []
    if has_results:
        refusals: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for refused in manifest.get("refusals", []):
            if "model" in refused and "arm" in refused:
                refusals[refused["model"], refused["arm"]].append(refused)
        for (model, arm), batches in sorted(_context_rows(manifest, results).items()):
            runs.append(_context_run(model, arm, batches, refusals[model, arm], manifest.get("prices", {})))
    description = (
        f"{manifest.get('task')} image arms over {len(items)} authored DEV context cases; "
        f"{manifest.get('dev_status')}. Conditional synthetic convention-reading probes."
    )
    if not has_results:
        description += " Request freeze only; anisotropic arms were executed in image-anisotropic-only-v1."
    return Experiment(
        dataset=f"exp/{directory}/context30",
        description=description,
        items=items,
        runs=runs,
        source=f"bench/results/pdf-master-artifacts/{directory}",
    )


# --- OCR1200 admission -----------------------------------------------------


def _ocr_experiment(artifacts: Path, directory: str) -> Experiment | None:  # noqa: C901, PLR0912
    base = guard(artifacts / directory)
    if not (base / "evaluation.json").exists():
        return None
    manifest = read_json(base / "manifest.json")
    evaluation = read_json(base / "evaluation.json")
    calls = read_json(base / "hosted-results.json")["calls"] if (base / "hosted-results.json").exists() else []
    sources = {p["id"]: p for p in read_json(base / "source-frozen.json")["pages"]}
    recall_path = base / "private-original-token-recall.json"
    recall = {r["id"]: r for r in read_json(recall_path)} if recall_path.exists() else {}
    kinds = {r["id"]: r["kind"] for c in evaluation["cohorts"].values() for r in c["rows"]}
    routes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in manifest["records"]:
        routes[record["id"]].append(record)
    items = []
    for page_id, page in sources.items():
        native = any(r["route"] == "native_vector" for r in routes[page_id])
        token = recall.get(page_id, {}).get("original_token_recall", {})
        image = Path(page["image_path"]) if page.get("image_path") else None
        items.append(
            Item(
                key=page_id,
                input={
                    "page_id": page_id,
                    "ocr_words": len(page["words"]),
                    "vector_candidates": len(page.get("vector_candidates", [])),
                    "route": "native_vector" if native else "hosted_admission",
                    "image": file_ref(image) if image and guard(image).exists() else page.get("image_path"),
                    "ocr_observed_sha256": page.get("ocr_observed_sha256"),
                },
                expected={"kind": kinds.get(page_id), "expected_original_tokens": token.get("expected_tokens")},
                metadata={
                    "kind": kinds.get(page_id),
                    "original_token_recall": token.get("recall"),
                    "native_zero_call": native,
                },
            )
        )
    call_map = {(c["model"], c["arm"], c["id"]): c for c in calls}
    runs = []
    for key, cohort in evaluation["cohorts"].items():
        model, _, arm = key.rpartition("/")
        rows, costs, elapsed = [], {}, {}
        for row in cohort["rows"]:
            call = call_map.get((model, arm, row["id"]))
            scores = {k: row["scores"].get(k) for k in ADMISSION_SCORES}
            scores["source_conservation"] = row.get("conservation")
            scores["unresolved_or_unmeasured"] = row["selection"] in ("unresolved", "unmeasured_or_failed")
            meta: dict[str, Any] = {
                "model": model,
                "arm": arm,
                "kind": row["kind"],
                "truth_status": row.get("truth_status", "authored-silver"),
                "selection": row["selection"],
                "status": call["status"]
                if call
                else ("native_vector" if row["selection"] == "native_vector" else "unmeasured"),
            }
            if call:
                meta.update(_cost_fields(call.get("cost"), call.get("usage", {}), call.get("entry", {})))
                meta["request_sha256"] = call.get("sha256")
                if "entry" in call:
                    costs[call["entry"]["index"]] = call.get("cost", {"effective_usd": None})
                    elapsed[call["entry"]["index"]] = number(call.get("http_elapsed_ms"))
            rows.append(
                Row(
                    row["id"],
                    {
                        "selection": row["selection"],
                        "probabilities": call.get("answer", {}).get("probabilities") if call else None,
                        "owned_source_ids": row.get("owned_source_ids"),
                        "unresolved_source_ids": row.get("unresolved_source_ids"),
                    },
                    scores,
                    meta,
                    wall_ms=number(call.get("http_elapsed_ms")) if call else None,
                    started=number(call.get("entry", {}).get("started_at")) if call else None,
                    name=f"{key}/{row['id']}",
                )
            )
        run_scores: dict[str, Any] = {
            "pages": cohort["pages"],
            "native_zero_call_pages": cohort["native_zero_call_pages"],
        }
        for kind, data in cohort["slices"].items():
            for field, value in data.items():
                run_scores[f"{_slug(kind)}_{field}"] = value
        accounting = _accounting(list(costs.values()), list(elapsed.values()))
        run_scores.update({k: v for k, v in accounting.items() if v is not None})
        runs.append(
            Run(
                name=key,
                description=f"A002 OCR1200 overlap0.5 admission, {model} {arm}; native ruled controls are zero-call.",
                rows=rows,
                metadata={"model": model, "arm": arm, "kind": "hosted admission"},
                scores=run_scores,
            )
        )
    ceilings: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evaluation.get("candidate_ceiling_rows", []):
        ceilings[row["variant"]].append(row)
    for variant, rows_data in ceilings.items():
        rows = []
        for row in rows_data:
            scores = {k: row["scores"].get(k) for k in ADMISSION_SCORES}
            scores["source_conservation"] = row.get("source_conservation")
            scores["text_group_exact"] = row.get("text_group_exact")
            scores["matched_text_groups"] = row.get("matched_text_groups")
            scores["expected_text_groups"] = row.get("expected_text_groups")
            rows.append(
                Row(
                    row["id"],
                    {
                        "owned_source_ids": row["owned_source_ids"],
                        "unresolved_source_ids": row["unresolved_source_ids"],
                    },
                    scores,
                    {"variant": variant, "kind": row["kind"], "status": "frozen candidate (no model)"},
                    name=f"candidate-ceiling/{variant}/{row['id']}",
                )
            )
        run_scores = {}
        for kind in KINDS:
            selected = [r for r in rows if r.metadata["kind"] == kind]
            if selected:
                run_scores[f"{_slug(kind)}_pages"] = len(selected)
                for field in ("exact_page", "false_positive_page", "owned_values", "owned_words"):
                    run_scores[f"{_slug(kind)}_{field}"] = sum(float(r.scores.get(field) or 0) for r in selected)
        runs.append(
            Run(
                name=f"candidate-ceiling/{variant}",
                description=f"Frozen {variant} candidate menu scored as if always accepted (ceiling, no model).",
                rows=rows,
                metadata={"variant": variant, "kind": "candidate ceiling"},
                scores=run_scores,
            )
        )
    return Experiment(
        dataset=f"exp/{directory}/pages",
        description="OCR1200 regions with frozen 0.5-height rolling candidates; hosted image512 admission per "
        "model selects a complete candidate or abstains. Authored DEV references; textual ownership is a proxy.",
        items=items,
        runs=runs,
        source=f"bench/results/pdf-master-artifacts/{directory}",
    )


# --- Source-only table-presence gates ---------------------------------------


def _gate_experiment(artifacts: Path, directory: str) -> Experiment | None:  # noqa: C901
    base = guard(artifacts / directory)
    if not (base / "evaluation.json").exists():
        return None
    manifest = read_json(base / "manifest.json")
    evaluation = read_json(base / "evaluation.json")
    calls = read_json(base / "hosted-results.json")["calls"] if (base / "hosted-results.json").exists() else []
    sources = {p["id"]: p for p in read_json(base / "source-frozen.json")["pages"]}
    native = {r["id"] for r in manifest["records"] if r["route"] == "native_vector"}
    first = next(iter(evaluation["cohorts"].values()))
    kinds = {r["id"]: r["kind"] for r in first["rows"]}
    items = []
    for page_id, page in sources.items():
        kind = kinds.get(page_id)
        image = Path(page["image_path"]) if page.get("image_path") else None
        expected_choice = PRESENCE.get(kind or "") if page_id not in native else None
        items.append(
            Item(
                key=page_id,
                input={
                    "page_id": page_id,
                    "source_words": len(page["words"]),
                    "text_candidates": len(page.get("text_candidates", [])),
                    "vector_candidates": len(page.get("vector_candidates", [])),
                    "image": file_ref(image) if image and guard(image).exists() else page.get("image_path"),
                },
                expected={"kind": kind, "presence": expected_choice, "scored": expected_choice is not None},
                metadata={"kind": kind, "native_zero_call": page_id in native},
            )
        )
    lookup = {(c["id"], c["model"], c["variant"]): c for c in calls}
    runs = []
    for key, cohort in evaluation["cohorts"].items():
        model, _, variant = key.rpartition("/")
        rows = []
        for row in cohort["rows"]:
            call = lookup.get((row["id"], model, variant))
            scores: dict[str, Any] = {
                "correct": row["correct"],
                "table_present": row["choice"] == "table_present",
                "unresolved_or_failed": row["choice"] in {"unresolved", "unmeasured_or_failed"},
            }
            meta: dict[str, Any] = {
                "model": model,
                "variant": variant,
                "kind": row["kind"],
                "scored": row["scored"],
                "status": call["status"] if call else ("native_vector" if row["id"] in native else "unmeasured"),
            }
            if call:
                meta.update(_cost_fields(call.get("cost"), call.get("usage", {}), call.get("entry", {})))
                meta["request_sha256"] = call.get("sha256")
            rows.append(
                Row(
                    row["id"],
                    {
                        "choice": row["choice"],
                        "probabilities": call.get("answer", {}).get("probabilities") if call else None,
                    },
                    scores,
                    meta,
                    wall_ms=number(call.get("http_elapsed_ms")) if call else None,
                    started=number(call.get("entry", {}).get("started_at")) if call else None,
                    name=f"{key}/{row['id']}",
                )
            )
        scored = [r for r in cohort["rows"] if r["scored"]]
        run_scores: dict[str, Any] = {
            "scored_pages": len(scored),
            "scored_correct": sum(bool(r["correct"]) for r in scored),
            "ambiguous_unscored_pages": cohort["ambiguous_unscored_pages"],
            "native_zero_call_pages": cohort["native_zero_call_pages"],
        }
        if scored:
            run_scores["scored_accuracy"] = run_scores["scored_correct"] / len(scored)
        for kind, data in cohort["slices"].items():
            for field, value in data.items():
                run_scores[f"{kind}_{field}"] = value
        accounting = cohort.get("actual_gate_accounting", {})
        for field in ("unique_requests", "effective_usd", "known_partial_usd", "unknown_cost_requests"):
            if accounting.get(field) is not None:
                run_scores[field] = accounting[field]
        if accounting.get("http_elapsed_median_ms") is not None:
            run_scores["http_elapsed_median_ms"] = accounting["http_elapsed_median_ms"]
        runs.append(
            Run(
                name=key,
                description=f"Source-only table-presence gate {variant} with {model} (image512). "
                "Presence labels scored only for borderless/prose; ambiguous and native pages unscored.",
                rows=rows,
                metadata={"model": model, "variant": variant},
                scores=run_scores,
            )
        )
    return Experiment(
        dataset=f"exp/{directory}/pages",
        description=f"Source-only table-presence gate over {len(items)} DEV pages "
        f"({manifest.get('task', 'presence gate')}); generic G001/G002 prompts, table_present/not_table/unresolved.",
        items=items,
        runs=runs,
        source=f"bench/results/pdf-master-artifacts/{directory}",
    )


# --- Source-neutralized ablation freeze ------------------------------------


def _neutralized_experiment(artifacts: Path, directory: str) -> Experiment | None:
    base = guard(artifacts / directory / "fresh24")
    if not (base / "manifest.json").exists():
        return None
    manifest = read_json(base / "manifest.json")
    evidence = {p["id"]: p for p in read_json(base / "source-evidence.json")["pages"]}
    candidates_path = base / "candidates-frozen.json"
    candidates = {p["id"]: p for p in read_json(candidates_path)["pages"]} if candidates_path.exists() else {}
    admission_path = base / "admission-luna-image512" / "manifest.json"
    requests = {r["id"]: r for r in read_json(admission_path)["records"]} if admission_path.exists() else {}
    items = []
    for case in manifest["cases"]:
        case_id = case["id"]
        pdf = base / "pdfs" / f"{case_id}.pdf"
        png = base / f"{case_id}.png"
        page = evidence.get(case_id, {})
        alternatives = candidates.get(case_id, {}).get("alternatives", [])
        request = requests.get(case_id)
        items.append(
            Item(
                key=case_id,
                input={
                    "case_id": case_id,
                    "pdf": file_ref(pdf) if guard(pdf).exists() else {"sha256": case.get("pdf_sha256")},
                    "image": file_ref(png) if guard(png).exists() else None,
                    "original_pdf_sha256": case.get("original_pdf_sha256"),
                    "removed": case.get("removed"),
                    "source_words": len(page.get("words", [])),
                    "candidate_tables": {
                        a.get("variant", str(i)): len(a.get("candidates", [])) for i, a in enumerate(alternatives)
                    },
                    "frozen_request": {k: request[k] for k in ("request", "sha256", "bytes", "model")}
                    if request
                    else None,
                },
                expected=None,
                metadata={
                    "arm": manifest.get("design", {}).get("arm"),
                    "scoring": "not performed; private targets deliberately unopened",
                },
            )
        )
    return Experiment(
        dataset=f"exp/{directory}/fresh24",
        description="Source-neutralized fresh24 explanatory-band-deletion freeze. Requests frozen, never sent; "
        "no scoring and no expected outputs by design (see bench/results/source-cue-audit.md).",
        items=items,
        runs=[],
        source=f"bench/results/pdf-master-artifacts/{directory}/fresh24",
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield one experiment per retained directory in this adapter's scope."""
    builders = (
        *((d, _image_experiment) for d in (*IMAGE_RUN_DIRS, *IMAGE_FREEZE_DIRS)),
        *((d, _ocr_experiment) for d in OCR_DIRS),
        *((d, _gate_experiment) for d in GATE_DIRS),
        *((d, _neutralized_experiment) for d in NEUTRALIZED_DIRS),
    )
    for directory, build in builders:
        experiment = build(artifacts, directory)
        if experiment is not None:
            yield experiment
