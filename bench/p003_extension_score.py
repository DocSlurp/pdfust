"""Pinned offline evaluation of frozen extension64 source menus and decision runs."""

# ruff: noqa: EM101, TRY003, E501, C901, TRY301, PLR0912
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.generalization_scoring import _cells
from bench.p003_report import strict_scores
from bench.p003_scoring_audit import dual_scores
from bench.p003_wrap_content import compare_wrap_content
from bench.pipeline_repair import validate
from bench.silver import canonical, guard_path, sha, write_json

PINS = {
    "manifest.json": "5669c7610bfc51e17717b56ef09a9ce01f6cd4da40e0ac2e0575dc9b777f8c3a",
    "frozen.json": "96c4530b45d92d7920f2a2becb1dce4622ed7ac4961fc05c93f528e17e542463",
    "source-inventory.json": "843eae3425ce060de3df20ee8a0272d67509b6bee8103691639e76f1d2156547",
    "private-targets.json": "f93a9b6dea989a1b89aeb35e38fcc9e73c9f0d47eba4b8a7fd35df0c150a93a9",
}
STATUSES = {"selected", "abstained", "invalid", "transport_error", "preparation_error", "not_attempted"}


def _read(path: Path, expected: str) -> dict[str, Any]:
    raw = guard_path(path).read_bytes()
    if sha(raw) != expected:
        raise ValueError("Frozen evaluation artifact changed: " + path.name)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("Expected object artifact")
    return value


def state_key(value: dict[str, Any]) -> str:
    """Ignore transport ID/annotations; retain exact source ownership, text and geometry."""
    tables = []
    for table in value["tables"]:
        item = {key: table[key] for key in ("row_count", "col_count", "values", "spans")}
        item["cells"] = [{"source_ids": cell["source_ids"], "role": cell.get("role", "unknown")} for cell in table["cells"]]
        if "bbox" in table:
            item["bbox"] = table["bbox"]
        tables.append(item)
    return sha(canonical({"tables": tables, "unresolved_ids": value["unresolved_ids"]}))


def load_frozen(corpus: Path) -> dict[str, Any]:
    """Authenticate every source/menu/stress byte before opening the pinned fresh targets."""
    corpus = guard_path(corpus)
    manifest = _read(corpus / "manifest.json", PINS["manifest.json"])
    frozen = _read(corpus / "frozen.json", PINS["frozen.json"])
    inventory = _read(corpus / "source-inventory.json", PINS["source-inventory.json"])
    if manifest["split"] != "DEV" or not inventory["source_only"] or frozen["references_read_for_menus"]:
        raise ValueError("Frozen source-only DEV corpus required")
    source_receipts = {}
    for name, digest in inventory["artifacts"].items():
        relative = Path(name)
        path = guard_path(corpus / relative)
        if relative.is_absolute() or ".." in relative.parts or not path.is_relative_to(corpus):
            raise ValueError("Source receipt escapes corpus")
        if sha(path.read_bytes()) != digest:
            raise ValueError("Frozen source artifact changed: " + name)
        source_receipts[name] = digest
    menus, stress = {}, {}
    for page in manifest["pages"]:
        ident = page["id"]
        menu = _read(corpus / "menus" / (ident + ".json"), source_receipts[f"menus/{ident}.json"])
        treatment = _read(corpus / "stress" / (ident + ".json"), source_receipts[f"stress/{ident}.json"])
        if menu["id"] != ident or sha(canonical(menu["source"])) != menu["source_sha256"] or menu["references_used"]:
            raise ValueError("Frozen source menu provenance differs")
        if len({c["id"] for c in menu["candidates"]}) != len(menu["candidates"]):
            raise ValueError("Duplicate frozen candidate IDs")
        validate(menu["source"], menu["baseline"])
        for candidate in menu["candidates"]:
            validate(menu["source"], candidate["state"])
        menus[ident], stress[ident] = menu, treatment
    # This is intentionally the first private-target read in this function.
    targets = _read(corpus / "private-targets.json", PINS["private-targets.json"])
    target_ids = [page["id"] for page in targets["pages"]]
    if len(target_ids) != len(set(target_ids)) or set(target_ids) != set(menus):
        raise ValueError("Complete unique target inventory required")
    identity = sha(canonical({"schema": 1, "pages": [{k: v for k, v in page.items() if k != "pdf_path"} for page in manifest["pages"]], "targets": targets["pages"]}))
    if identity != manifest["dataset_sha256"] or identity != targets["dataset_sha256"] or identity != frozen["dataset_sha256"]:
        raise ValueError("Source/target dataset identity differs")
    return {"manifest": manifest, "targets": targets["pages"], "menus": menus, "stress": stress,
            "receipts": {"pins": dict(PINS), "source_artifacts": source_receipts,
                         "dataset_sha256": identity, "source_admitted_before_target_read": True,
                         "menus_modified": False}}


def prediction(ident: str, state: dict[str, Any] | None, *, status: str = "ok") -> dict[str, Any]:
    """Map source-owned states to the established evaluation prediction contract."""
    return {"id": ident, "status": status, "tables": deepcopy(state["tables"]) if state is not None and status == "ok" else []}


def wrap_scores(targets: list[dict[str, Any]], predictions: list[dict[str, Any]], strict: dict[str, Any]) -> dict[str, Any]:
    """Retain strict table matching, omissions, extras and unsupported wrap diagnostics."""
    references, observed = ({page["id"]: page for page in rows} for rows in (targets, predictions))
    counts, reasons, pages = Counter(), Counter(), []
    for page in strict["pages"]:
        counts["pages"] += 1
        counts["error_pages"] += bool(page["error"])
        target = references[page["id"]]["tables"]
        predicted = observed[page["id"]]["tables"] if not page["error"] else []
        used_a, used_b, pairs = set(), set(), []
        for match in page["matches"]:
            a, b = match["target"], match["prediction"]
            used_a.add(a)
            used_b.add(b)
            result = compare_wrap_content(target[a], predicted[b])
            counts["matched_pairs"] += 1
            if result["supported"]:
                counts.update(result["counts"])
                counts["recovered_tables"] += result["content_recovered_with_row_order"]
            else:
                counts["unsupported_pairs"] += 1
                reasons[result["unsupported_reason"]] += 1
                counts["unmeasured_reference_characters"] += sum(map(len, _cells(target[a]).values()))
                counts["unmeasured_prediction_characters"] += sum(map(len, _cells(predicted[b]).values()))
            pairs.append({**match, "supported": result["supported"], "unsupported_reason": result["unsupported_reason"],
                          "counts": result["counts"], "recall": result["recall"], "precision": result["precision"],
                          "content_recovered_with_row_order": result["content_recovered_with_row_order"]})
        for index, table in enumerate(target):
            if index not in used_a:
                units = sum(map(len, _cells(table).values()))
                counts.update({"missing_tables": 1, "missing": units, "reference_units": units})
        for index, table in enumerate(predicted):
            if index not in used_b:
                units = sum(map(len, _cells(table).values()))
                counts.update({"extra_tables": 1, "extra": units, "prediction_units": units})
        pages.append({"id": page["id"], "error": page["error"], "pairs": pairs})
    r, p, matched = counts["reference_units"], counts["prediction_units"], counts["matched"]
    recall = matched / r if r else float(not p)
    precision = matched / p if p else float(not r)
    return {"counts": dict(counts), "unsupported_reasons": dict(reasons), "pages": pages,
            "covered_content_recall": recall, "covered_content_precision": precision,
            "full_content_recall": recall if not counts["unsupported_pairs"] else None,
            "full_content_precision": precision if not counts["unsupported_pairs"] else None,
            "diagnostic_scope": "Ordered character retention; does not establish semantic rows, headers, wrapping or schema correctness"}


def score_predictions(targets: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute unchanged strict scoring, v2 content and explicitly diagnostic wrap scoring."""
    strict = strict_scores(targets, predictions)
    return {"strict": strict, "v2": dual_scores(targets, predictions, strict), "wrap": wrap_scores(targets, predictions, strict)}


def ownership_diagnostics(source: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Inventory raw stress omissions/duplicates without silently repairing their scores."""
    known = {word["id"] for word in source["words"]}
    owners = Counter(state["unresolved_ids"])
    for table in state["tables"]:
        owners.update(ident for cell in table["cells"] for ident in cell["source_ids"])
    return {"source_words": len(known), "omitted_ids": sorted(known - owners.keys()),
            "unknown_ids": sorted(owners.keys() - known),
            "duplicate_ownership_excess": sum(count - 1 for count in owners.values() if count > 1),
            "unresolved_words": len(state["unresolved_ids"])}


def _rank(metrics: dict[str, Any], arm: str) -> tuple[float, ...]:
    if arm == "strict":
        totals = metrics["strict"]["totals"]
        return (float(totals["exact_page"]), totals["strict_exact_cells"] / max(1, totals["expected_cells"]), -totals["false_positive_tables"])
    result = metrics[arm]
    recall, precision = result["full_content_recall"], result["full_content_precision"]
    return (recall if recall is not None else -1.0, precision if precision is not None else -1.0)


def coverage(frozen: dict[str, Any]) -> dict[str, Any]:
    """Evaluate every already frozen candidate; independent ceilings are scoring-only oracles."""
    started, cpu = time.perf_counter(), time.process_time()
    targets = frozen["targets"]
    baseline = [prediction(t["id"], frozen["menus"][t["id"]]["baseline"]) for t in targets]
    best = {arm: [] for arm in ("strict", "v2", "wrap")}
    pages = []
    for target in targets:
        ident = target["id"]
        rows = []
        for candidate in frozen["menus"][ident]["candidates"]:
            predicted = prediction(ident, candidate["state"])
            metrics = score_predictions([target], [predicted])
            rows.append({"id": candidate["id"], "prediction": predicted, "metrics": metrics})
        selected = {}
        for arm, predictions in best.items():
            winner = max(rows, key=lambda row: _rank(row["metrics"], arm))
            predictions.append(winner["prediction"])
            selected[arm] = {"candidate_id": winner["id"], "rank": _rank(winner["metrics"], arm)}
        pages.append({"id": ident, "candidate_count": len(rows), "negative_page": not target["tables"],
                      "ceilings": selected, "exact_candidate_count": sum(row["metrics"]["strict"]["totals"]["exact_page"] for row in rows),
                      "candidates": [{"id": row["id"], "strict_totals": row["metrics"]["strict"]["totals"],
                                      "v2_full_recall": row["metrics"]["v2"]["full_content_recall"],
                                      "wrap_full_recall": row["metrics"]["wrap"]["full_content_recall"]} for row in rows]})
    return {"version": 1, "receipts": frozen["receipts"], "intended_pages": len(targets), "baseline": score_predictions(targets, baseline),
            "independent_candidate_ceilings": {arm: score_predictions(targets, predictions) for arm, predictions in best.items()},
            "pages": pages, "coverage_failures": [page["id"] for page in pages if not page["exact_candidate_count"]],
            "scope": "Scoring-only oracle ceiling after freeze; never a source proposal or model selector", "resources": {
                "wall_seconds": time.perf_counter() - started, "cpu_seconds": time.process_time() - cpu,
                "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "measurement": "Single parent CPU scoring, unsampled lifetime getrusage including imports; no inference/GPU"}}


def score_run(frozen: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Keep all intended outcomes; separate selected-only scores from baseline retention."""
    intended = report["config"].get("page_ids", report["config"].get("intended_ids", list(frozen["menus"])))
    if not intended or len(set(intended)) != len(intended) or not set(intended) <= set(frozen["menus"]):
        raise ValueError("Unique known intended page inventory required")
    rows = report["results"]
    if len({row["id"] for row in rows}) != len(rows) or not {row["id"] for row in rows} <= set(intended):
        raise ValueError("Duplicate or outside-intended result IDs")
    observed = {row["id"]: row for row in rows}
    references = {target["id"]: target for target in frozen["targets"]}
    targets = [references[ident] for ident in intended]
    baseline_predictions, selected_predictions, composed_predictions, outcomes = [], [], [], []
    for ident in intended:
        menu = frozen["menus"][ident]
        row = observed.get(ident, {"id": ident, "status": "not_attempted", "selected_state": None, "baseline_state": menu["baseline"]})
        status = row["status"]
        if status not in STATUSES:
            raise ValueError("Unknown run status")
        baseline_state = row["baseline_state"]
        allowed_baselines = [menu["baseline"], *[item["raw_baseline"] for item in frozen["stress"][ident]["treatments"]]]
        if state_key(baseline_state) not in {state_key(state) for state in allowed_baselines}:
            raise ValueError("Baseline differs from frozen source/stress states")
        chosen = row.get("selected_state")
        error = None
        if status == "selected":
            try:
                if chosen is None:
                    raise ValueError("Selected outcome has no state")
                validate(menu["source"], chosen)
                if state_key(chosen) not in {state_key(candidate["state"]) for candidate in menu["candidates"]}:
                    raise ValueError("Selected state is outside frozen candidate menu")
            except (KeyError, TypeError, ValueError) as exception:
                status, chosen, error = "invalid", None, str(exception)
        elif chosen is not None:
            raise ValueError("Nonselected outcome cannot expose selected state")
        baseline_predictions.append(prediction(ident, baseline_state))
        selected_predictions.append(prediction(ident, chosen, status="ok" if status == "selected" else status))
        composed_predictions.append(prediction(ident, chosen if status == "selected" else baseline_state))
        outcomes.append({"id": ident, "reported_status": row["status"], "effective_status": status, "invalid_reason": error,
                         "baseline_retained": status != "selected",
                         "baseline_ownership": ownership_diagnostics(menu["source"], baseline_state),
                         "selected_ownership": ownership_diagnostics(menu["source"], chosen) if chosen is not None else None})
    baseline = score_predictions(targets, baseline_predictions)
    selected = score_predictions(targets, selected_predictions)
    composed = score_predictions(targets, composed_predictions)
    comparisons = Counter()
    secondary_changes = {arm: Counter() for arm in ("v2", "wrap")}
    paired = []
    for outcome, before, after in zip(outcomes, baseline["strict"]["pages"], composed["strict"]["pages"], strict=True):
        # Exact cells alone cannot detect an extra table on a negative page.
        left = (before["exact_page"], before["strict_exact_cells"], -before["false_positive_tables"])
        right = (after["exact_page"], after["strict_exact_cells"], -after["false_positive_tables"])
        label = "improved" if right > left else "regressed" if right < left else "unchanged"
        comparisons[label] += 1
        comparisons["selected_" + label] += outcome["effective_status"] == "selected"
        secondary = {}
        index = len(paired)
        if outcome["effective_status"] == "selected":
            before_metrics = score_predictions([targets[index]], [baseline_predictions[index]])
            after_metrics = score_predictions([targets[index]], [composed_predictions[index]])
            for arm in secondary_changes:
                old, new = _rank(before_metrics, arm), _rank(after_metrics, arm)
                secondary[arm] = "improved" if new > old else "regressed" if new < old else "unchanged"
        else:
            secondary = dict.fromkeys(secondary_changes, "unchanged")
        for arm, change in secondary.items():
            secondary_changes[arm][change] += 1
            secondary_changes[arm]["selected_" + change] += outcome["effective_status"] == "selected"
        paired.append({**outcome, "strict_change": label, "baseline_exact_cells": before["strict_exact_cells"],
                       "composed_exact_cells": after["strict_exact_cells"], "negative_page": before["negative_page"],
                       "secondary_changes": secondary,
                       "model_negative_presence_correct": outcome["effective_status"] == "selected" and after["presence_correct"]})
    return {"version": 1, "config": deepcopy(report["config"]), "receipts": frozen["receipts"], "intended_pages": len(intended),
            "status_counts": dict(Counter(outcome["effective_status"] for outcome in outcomes)), "baseline": baseline,
            "model_selected_only": selected, "composed_with_baseline_retention": composed, "comparisons": dict(comparisons),
            "comparisons_by_metric": {"strict": dict(comparisons), **{arm: dict(counts) for arm, counts in secondary_changes.items()}},
            "pages": paired, "costs": deepcopy(report.get("costs")), "resources": deepcopy(report.get("resources")),
            "scope": "Failures/abstentions/not-attempted remain in intended denominator; baseline retention is not model success"}


def main() -> None:
    """Write a fresh scoring artifact without mutating inputs or source menus."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    output = guard_path(args.output)
    if output.exists():
        raise FileExistsError("Fresh scoring output required")
    frozen = load_frozen(args.corpus)
    report = score_run(frozen, json.loads(guard_path(args.run).read_bytes())) if args.run else coverage(frozen)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(json.dumps({"output": str(output), "intended_pages": report["intended_pages"]}))


if __name__ == "__main__":
    main()
