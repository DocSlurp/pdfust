"""Verify and report complete P002 natural-PDF runs offline."""

# Retained experiment schemas have heterogeneous dictionaries.
# ruff: noqa: C901, PLR0912, EM101, TRY003
from __future__ import annotations

import argparse
import ast
import json
import math
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.generalization_scoring import audit_model_body, normalize_text, score_dataset, score_page
from bench.pipeline_regions import compose, validate_composed
from bench.pipeline_report import _render_markdown, _verify_markdown_renderer
from bench.pipeline_scoring import score_dataset as authored_score_dataset
from bench.silver import canonical, guard_path, sha

LOCALIZATION_IOU = 0.5

SOURCE_FIELDS = ("id", "pdf_path", "pdf_sha256", "page_number")


# Reviewed repository sources, never digests supplied by an artifact.
# Runner 7395782 retains local region states and uses the verified baseline
# renderer, source-order sorting and a single newline between region renderings.
TRUSTED_HISTORICAL_CODE = {
    "generalization_run.py": {
        "a5bc281951becd59633a78d00bdeae125405789e09b3368617ff85ecbd191b26": "7395782",
        "3945a5efaace0c02d80866460e32f67d7f2acb1c9c35500376a32edf0f151f38": "6afe326",
    },
    "pipeline_regions.py": {
        "66c6ec07d91753ec9a8885124e18a3d0a64f929be5f29682e1050ea826894d2a": "83bd9a6",
        "f31b4e3b8579fb4676512104db7f5d6c8d81e36e3e6319272f1ea14aad82b494": "35cb3f2",
    },
}
REGION_VALIDATION_FUNCTIONS = {"_box", "_characters", "_source", "compose", "validate_composed"}
REGION_VALIDATION_CONSTANTS = {"MAX_PAGE_WORDS", "MAX_PAGE_CHARACTERS", "MAX_REGIONS"}


def _region_validation_ast(source: bytes) -> str:
    """Fingerprint only trusted composition validators and their local limits."""
    module = ast.parse(source)
    selected: list[ast.stmt] = []
    names = set()
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name in REGION_VALIDATION_FUNCTIONS:
            selected.append(node)
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            assigned = {target.id for target in node.targets if isinstance(target, ast.Name)}
            if assigned & REGION_VALIDATION_CONSTANTS:
                selected.append(node)
                names.update(assigned & REGION_VALIDATION_CONSTANTS)
    if names != REGION_VALIDATION_FUNCTIONS | REGION_VALIDATION_CONSTANTS:
        raise ValueError("Region code lacks complete trusted validation dependencies")
    return sha(ast.dump(ast.Module(body=selected, type_ignores=[])).encode())


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Expected JSON object")
    return value


def _ratio(numerator: float, denominator: object, factor: float = 1) -> float | None:
    if isinstance(denominator, bool) or not isinstance(denominator, (float, int)):
        return None
    if denominator <= 0 or not math.isfinite(denominator):
        return None
    return numerator / denominator * factor


def load_corpus(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify complete DEV identity, independent references and input PDF bytes."""
    manifest, targets = _read(directory / "manifest.json"), _read(directory / "private-targets.json")
    if manifest.get("split") != "DEV":
        raise ValueError("Only DEV may be evaluated")
    records, references = manifest["pages"], targets["pages"]
    ids, target_ids = [r["id"] for r in records], [r["id"] for r in references]
    if len(ids) != len(set(ids)) or len(target_ids) != len(set(target_ids)) or set(ids) != set(target_ids):
        raise ValueError("Manifest and reference IDs must match uniquely")
    identity_metadata: dict[str, Any] = {}
    if "source_dataset_sha256" in manifest:
        identity_metadata = {"source_dataset_sha256": manifest["source_dataset_sha256"], "screen": "natural16"}
    elif "parent_dataset_sha256" in manifest:
        identity_metadata = {"parent_dataset_sha256": manifest["parent_dataset_sha256"]}
    identity = sha(
        canonical(
            {
                "schema": manifest["schema"],
                **identity_metadata,
                "pages": [{k: v for k, v in row.items() if k != "pdf_path"} for row in records],
                "targets": [{k: v for k, v in row.items() if k != "annotation_path"} for row in references],
            }
        )
    )
    if manifest["dataset_sha256"] != identity or targets["dataset_sha256"] != identity:
        raise ValueError("Frozen dataset identity mismatch")
    checked = set()
    for record in records:
        path = guard_path(Path(record["pdf_path"]))
        if not path.is_absolute():
            raise ValueError("Source PDF path must be absolute")
        pair = (str(path), record["pdf_sha256"])
        if pair not in checked:
            if sha(path.read_bytes()) != record["pdf_sha256"]:
                raise ValueError("Frozen source PDF changed")
            checked.add(pair)
    return manifest, targets


def verify_code(directory: Path, frozen: dict[str, Any], *, processor: str) -> dict[str, Any]:
    """Hash archive bytes without importing or executing artifact Python."""
    hashes = frozen["code_sha256"]
    local = Path(__file__).parent
    comparison = {}
    required = {"pipeline_run.py", "pipeline_assembly.py"}
    if processor == "regions":
        required |= {"pipeline_regions.py", "generalization_run.py"}
        if frozen.get("config", {}).get("assembly_method") in {"generate", "gated_generate"}:
            required.add("pipeline_generation.py")
    if not required <= hashes.keys():
        raise ValueError("Frozen code lacks required verifier dependencies")
    for name, digest in hashes.items():
        if Path(name).name != name or not name.endswith(".py"):
            raise ValueError("Unsafe archived code filename")
        if sha(guard_path(directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived code hash mismatch")
        local_path = local / name
        comparison[name] = (
            "identical" if local_path.is_file() and sha(local_path.read_bytes()) == digest else "different"
        )
    # Whole-run renderer compatibility is established through its approved AST.
    renderer = _verify_markdown_renderer(directory, frozen)
    validation_modules = {"pipeline_assembly.py"}
    if processor == "regions":
        validation_modules |= {"pipeline_regions.py", "generalization_run.py"}
    trusted_history = {}
    for name in validation_modules:
        if comparison[name] != "identical":
            reviewed = TRUSTED_HISTORICAL_CODE.get(name, {}).get(hashes[name])
            if reviewed is None:
                raise ValueError("Trusted local ownership validator differs from unreviewed frozen code")
            trusted_history[name] = reviewed
    if processor == "regions":
        archived = (directory / "code" / "pipeline_regions.py").read_bytes()
        if _region_validation_ast(archived) != _region_validation_ast((local / "pipeline_regions.py").read_bytes()):
            raise ValueError("Historical region composition validators differ from trusted local AST")
    return {
        "archive_hashes_verified": True,
        "local_comparison": comparison,
        "trusted_historical_commits": trusted_history,
        "renderer": renderer,
        "region_validator_ast_compatible": processor == "regions",
    }


def _bounds(source: dict[str, Any], state: dict[str, Any]) -> None:
    lookup = {w["id"]: w for w in source["words"]}
    for table in state["tables"]:
        boxes = [lookup[i]["bbox"] for cell in table["cells"] for i in cell["source_ids"]]
        if boxes:
            table["bbox"] = [
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            ]


def verify_output(directory: Path, prediction: dict[str, Any], *, processor: str) -> dict[str, Any]:
    """Revalidate source ownership and exact retained Markdown for successful pages."""
    ident = prediction["id"]
    if not isinstance(ident, str) or Path(ident).name != ident or ident in {".", ".."}:
        raise ValueError("Unsafe page ID")
    retained = _read(directory / f"{ident}-result.json")
    if retained != prediction:
        raise ValueError("Per-page retained result differs from report")
    if prediction.get("status") != "ok":
        return {"operational": False, "conserved": False}
    source = prediction["source"]
    state = _read(directory / f"{ident}-structure.json")
    if state["tables"] != prediction["tables"] or state["unresolved_ids"] != prediction["unresolved_ids"]:
        raise ValueError("Retained complete structure differs from report")
    if processor == "regions":
        plan = {**prediction["region_plan"], "page_size": source["page_size"], "words": source["words"]}
        region_outputs = prediction["regions"]
        ids = [r["id"] for r in region_outputs]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate retained region state")
        states = {r["id"]: r["state"] for r in region_outputs}
        rebuilt = compose(plan, states)
        _bounds(source, rebuilt)
        if rebuilt != state:
            raise ValueError("Region composition differs from retained complete state")
        validate_composed(source, state)
        order = {w["id"]: i for i, w in enumerate(source["words"])}
        rendered = [
            (
                min((order[i] for i in r["source_ids"]), default=len(order)),
                _render_markdown(r["source"], states[r["id"]]),
            )
            for r in plan["regions"]
        ]
        markdown = "\n".join(text for _, text in sorted(rendered))
    else:
        markdown = _render_markdown(source, state)
    if guard_path(directory / f"{ident}.md").read_bytes() != markdown.encode():
        raise ValueError("Retained Markdown differs from trusted exact rendering")
    assigned = state["unresolved_ids"] + [i for t in state["tables"] for c in t["cells"] for i in c["source_ids"]]
    if Counter(assigned) != Counter(w["id"] for w in source["words"]):
        raise ValueError("Output does not conserve complete page source")
    return {"operational": True, "conserved": True}


def _ceiling(target: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    source = prediction.get("source")
    result: dict[str, Any] = {"source_available": source is not None, "ocr_text_recall": None}
    if source is not None and target.get("structural_scored", True):
        gold = Counter(
            "".join(normalize_text(v) for t in target.get("tables", []) for row in t["values"] for v in row if v)
        )
        words = Counter("".join(normalize_text(w["text"]) for w in source["words"]))
        result.update(
            source_character_count=sum(words.values()),
            reference_character_count=sum(gold.values()),
            source_reference_character_inventory_overlap=sum((gold & words).values()),
            source_character_inventory_scope=(
                "whole-page characters; geometry/order/cell identity ignored; not OCR recall"
            ),
        )
    candidates = prediction.get("candidates")
    if candidates:
        scores = [score_page(target, candidate["tables"]) for candidate in candidates]
        scored = [s for s in scores if s["structural_scored"]]
        result["candidate_count"] = len(candidates)
        result["candidate_exact_page_ceiling"] = max((int(s["exact_page"]) for s in scored), default=None)
        result["candidate_complete_tables_ceiling"] = max((s["complete_tables"] for s in scored), default=None)
    else:
        result["candidate_exact_page_ceiling"] = None
        result["candidate_ceiling_reason"] = "not retained, or region cross-product not enumerated"
    return result


def _evaluate(targets: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    result = score_dataset(targets, predictions)
    localized = 0
    for page in result["pages"]:
        count = sum(match["iou"] is not None and match["iou"] >= LOCALIZATION_IOU for match in page.get("matches", []))
        page["localized_tables_iou_ge_0_5"] = count
        localized += count
    result["totals"]["localized_tables_iou_ge_0_5"] = localized
    return result


def _costs(report: dict[str, Any]) -> dict[str, Any]:
    bases = report.get("cost_bases", {})
    effective = report.get("effective_usd")
    if bases.get("reserved", 0) or bases.get("unknown", 0) or report.get("ledger_attempts") is None:
        effective = None
    return {
        "scope": "all ledger attempts attributed to the run, including failed attempts; API only",
        "ledger_attempts": report.get("ledger_attempts"),
        "successful_calls": report.get("calls"),
        "provider_reported_subtotal_usd": report.get("provider_reported_usd"),
        "missing_provider_charge_count": report.get("missing_provider_charge_count"),
        "accounted_usd_including_reservations": report.get("accounted_usd"),
        "effective_usd": effective,
        "cost_bases": bases,
        "reservation_usd": None if bases.get("reserved", 0) else 0,
        "estimated_usd": None if any("estimate" in str(k) for k in bases) else 0,
        "breakdown_note": (
            "Reported zero preserved. Estimate/reservation amounts unavailable in summary; not inferred from tokens."
        ),
    }


USAGE_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "prompt_tokens_details.cached_tokens",
    "input_tokens_details.cached_tokens",
)


def _numeric_observations(values: list[Any]) -> dict[str, Any]:
    valid = [
        v for v in values if not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) and v >= 0
    ]
    return {
        "observations": len(values),
        "reported_positive": sum(v > 0 for v in valid),
        "reported_zero": sum(v == 0 for v in valid),
        "missing_or_invalid": len(values) - len(valid),
        "known_subtotal": sum(valid) if valid else None,
        "complete_total": sum(valid) if len(valid) == len(values) and values else None,
    }


def _usage_value(usage: dict[str, Any], field: str) -> object:
    value: object = usage
    for component in field.split("."):
        if not isinstance(value, dict) or component not in value:
            return None
        value = value[component]
    return value


def _model_breakdown(predictions: list[dict[str, Any]], audits: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep body model identity distinct from configuration and ledger totals."""
    requests = {a["path"]: a.get("model", "unknown") for a in audits}
    request_counts = Counter(requests.values())
    calls: dict[str, list[dict[str, Any]]] = defaultdict(list)
    discrepancies = []
    for prediction in predictions:
        for step, call in enumerate(prediction.get("calls", [])):
            body_model = requests.get(f"{prediction['id']}-request-{step}.json", "unknown")
            entry_model = call.get("entry", {}).get("requested_model")
            if entry_model is not None and entry_model != body_model:
                discrepancies.append({"page": prediction["id"], "step": step, "body": body_model, "entry": entry_model})
            calls[body_model].append(call)
    models = {}
    for model in request_counts.keys() | calls.keys():
        returned = calls[model]
        entries = [c.get("entry", {}) for c in returned]
        models[model] = {
            "retained_request_bodies": request_counts[model],
            "returned_calls": len(returned),
            "returned_provider_reported_usd": _numeric_observations([e.get("provider_reported_usd") for e in entries]),
            "returned_accounted_usd": _numeric_observations([e.get("accounted_usd") for e in entries]),
            "returned_cost_bases": dict(Counter(e.get("cost_status", "unknown") for e in entries)),
            "usage": {
                field: _numeric_observations([_usage_value(c.get("usage", {}), field) for c in returned])
                for field in USAGE_FIELDS
            },
        }
    return {
        "models": models,
        "request_entry_model_discrepancies": discrepancies,
        "scope": "Retained request bodies and returned calls, including calls on failed pages. "
        "Per-model charges are returned-call subtotals; all-attempt charges remain ledger-authoritative. "
        "A request body can represent multiple transport attempts; "
        "no missing usage/cache field is imputed zero. "
        "Provider cache fields are reported literally; there is no local inference cache.",
    }


def score_run(
    directory: Path, manifest_path: Path, manifest: dict[str, Any], targets: dict[str, Any]
) -> dict[str, Any]:
    """Include every frozen intended page; reject outcome-selected inventories."""
    report, frozen = _read(directory / "report.json"), _read(directory / "frozen.json")
    config = report["config"]
    if config != frozen["config"] or frozen["manifest_sha256"] != sha(guard_path(manifest_path).read_bytes()):
        raise ValueError("Frozen config or manifest changed")
    records = [r for r in manifest["pages"] if not config.get("pilot", False) or r["pilot"]]
    expected = {r["id"]: {k: r[k] for k in SOURCE_FIELDS} for r in records}
    actual = {r["id"]: r for r in frozen["records"]}
    if actual != expected or len(actual) != len(frozen["records"]):
        raise ValueError("Frozen records differ from complete intended manifest cohort")
    processor = config.get("processor", "whole")
    if processor not in {"whole", "regions"}:
        raise ValueError("Unsupported processor")
    code = verify_code(directory, frozen, processor=processor)
    predictions = report["results"]
    private = [t for t in targets["pages"] if t["id"] in expected]
    scoring_predictions = deepcopy(predictions)
    derived_boxes = 0
    for prediction in scoring_predictions:
        if prediction.get("status") == "ok" and prediction.get("source") is not None:
            state = {"tables": [t for t in prediction["tables"] if "bbox" not in t]}
            _bounds(prediction["source"], state)
            derived_boxes += sum("bbox" in t for t in state["tables"])
    scored = _evaluate(private, scoring_predictions)
    by_id, by_target = {p["id"]: p for p in scoring_predictions}, {t["id"]: t for t in private}
    operational = sum(verify_output(directory, p, processor=processor)["operational"] for p in predictions)
    groups: dict[str, Any] = {}
    for field in ("cohort", "family"):
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in records:
            buckets[r.get(field, "unknown")].append(by_target[r["id"]])
        groups[field] = {
            key: _evaluate(members, [by_id[t["id"]] for t in members if t["id"] in by_id])["totals"]
            for key, members in buckets.items()
        }
    authored = [by_target[r["id"]] for r in records if r.get("cohort") == "authored"]
    authored_legacy = authored_score_dataset(
        authored, [p for p in predictions if p["id"] in {t["id"] for t in authored}]
    )
    request_audits = []
    expected_requests = {
        f"{p['id']}-request-{step}.json" for p in predictions for step, _call in enumerate(p.get("calls", []))
    }
    request_paths = sorted(guard_path(directory).glob("*-request-*.json"))
    if not expected_requests <= {p.name for p in request_paths}:
        raise ValueError("Successful call lacks a retained request body")
    for body_path in request_paths:
        owner = body_path.name.rsplit("-request-", 1)[0]
        if owner not in expected:
            raise ValueError("Retained request belongs to an unknown page")
        body = _read(body_path)
        audit = audit_model_body(body)
        if not audit["explicit_reference_fields_absent"]:
            raise ValueError("Explicit reference fields in retained model body")
        request_audits.append(
            {
                "path": body_path.name,
                "sha256": sha(body_path.read_bytes()),
                "model": body.get("model", "unknown"),
                **audit,
            }
        )
    positive_targets = [t for t in private if t.get("structural_scored", True) and t.get("tables")]
    negative_targets = [t for t in private if t.get("structural_scored", True) and not t.get("tables")]
    positive = _evaluate(positive_targets, [by_id[t["id"]] for t in positive_targets if t["id"] in by_id])["totals"]
    negative = _evaluate(negative_targets, [by_id[t["id"]] for t in negative_targets if t["id"] in by_id])["totals"]
    costs = _costs(report)
    metrics = dict(report.get("metrics", {}))
    for field in ("wall_seconds", "cpu_seconds", "cpu_utilization_percent", "peak_sampled_rss_bytes", "measurement"):
        metrics.setdefault(field, None)
    if report.get("page_count", len(predictions)) != len(predictions):
        raise ValueError("Report page count differs from retained result inventory")
    if report.get("complete_output_pages", operational) != operational:
        raise ValueError("Report successful count differs from verified complete outputs")
    statuses = Counter(p.get("status", "missing") for p in predictions)
    statuses["missing"] += len(expected) - len(predictions)
    return {
        "name": directory.name,
        "config": config,
        "manifest_sha256": frozen["manifest_sha256"],
        "dataset_sha256": manifest["dataset_sha256"],
        "intended_pages": len(expected),
        "scores": scored["totals"],
        "positive": positive,
        "negative": negative,
        "page_scores": scored["pages"],
        "groups": groups,
        "authored_legacy_exact": authored_legacy["totals"],
        "statuses": dict(statuses),
        "operational_pages": operational,
        "all_errors": len(expected) - operational,
        "markdown_bytes_verified_pages": operational,
        "conserved_pages": operational,
        "source_candidate_ceilings": [{"id": t["id"], **_ceiling(t, by_id.get(t["id"], {}))} for t in private],
        "costs": costs,
        "resources": metrics,
        "frozen_runtime": {
            k: frozen.get(k)
            for k in (
                "runtime",
                "python",
                "platform",
                "logical_cpus",
                "concurrency",
                "local_replay",
            )
        },
        "pages_per_minute": _ratio(operational, metrics.get("wall_seconds"), 60),
        "resource_scope": metrics.get("measurement", "unmeasured"),
        "pages_per_dollar": _ratio(operational, costs["effective_usd"]),
        "exact_pages_per_minute": _ratio(scored["totals"].get("exact_page", 0), metrics.get("wall_seconds"), 60),
        "exact_pages_per_dollar": _ratio(scored["totals"].get("exact_page", 0), costs["effective_usd"]),
        "exact_positive_pages_per_minute": _ratio(positive.get("exact_page", 0), metrics.get("wall_seconds"), 60),
        "exact_positive_pages_per_dollar": _ratio(positive.get("exact_page", 0), costs["effective_usd"]),
        "derived_prediction_bboxes": derived_boxes,
        "localization_policy": {
            "assignment_iou_threshold": 0.1,
            "localization_iou_threshold": 0.5,
            "description": "Low-threshold correspondence is not detection recall or AP. Strict count is IoU >= 0.5.",
        },
        "code_verification": code,
        "request_body_audits": request_audits,
        "actual_model_breakdown": _model_breakdown(predictions, request_audits),
        "model_configuration": {
            k: config.get(k)
            for k in (
                "policy",
                "assembly_method",
                "model",
                "gate_review_model",
                "generation_model",
            )
        },
        "comparison_caveats": [
            "Authored DEV silver and independently annotated natural tables are reported separately.",
            "Pilot/full runs and different OCR/rotation/region policies are not matched causal comparisons.",
            (
                "Low-threshold assignments are correspondences, not detection recall or AP. "
                "Text-assisted matching is not independent geometric detection; "
                "OCR recall is unavailable without aligned OCR gold."
            ),
            "Body field audits do not prove semantic absence of leaked answers inside arbitrary strings.",
            "Legacy predicted bboxes derive from owned text extents; annotation boxes may include borders or padding.",
        ],
    }


def markdown_report(runs: list[dict[str, Any]]) -> str:
    """Render concise aggregate and cohort/family metrics with explicit limits."""
    lines = [
        "# P002 complete natural-PDF pipeline",
        "",
        "All intended pages, including missing and failed outputs, remain in denominators.",
        "OCR text recall is unmeasured without aligned OCR references. JSON null means unmeasured or undefined.",
        "",
    ]
    lines += [
        (
            "| Run | Pages | Verified outputs | Errors | Exact pages | Missing tables | "
            "Extra tables | Pages/min | Effective USD |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in runs:
        s = run["scores"]
        values = [
            run["name"],
            run["intended_pages"],
            run["operational_pages"],
            run["all_errors"],
            s.get("exact_page", 0),
            s.get("missing_tables", 0),
            s.get("false_positive_tables", 0),
            run["pages_per_minute"],
            run["costs"]["effective_usd"],
        ]
        lines.append("| " + " | ".join(_fmt(v) for v in values) + " |")
    for run in runs:
        lines += ["", f"## {run['name']}", "", "Statuses: `" + json.dumps(run["statuses"], sort_keys=True) + "`.", ""]
        lines += [
            (
                "| Group | Pages | Scored | Exact | Structure cells / expected | "
                "Text edits / reference chars | IoU >= 0.5 tables | Negative false-positive pages |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for field, groups in run["groups"].items():
            for name, s in groups.items():
                lines.append(
                    f"| {field}: {name} | {s['pages']} | {s['scored_pages']} | {s.get('exact_page', 0)} | "
                    f"{s.get('correct_structure_cells', 0)}/{s.get('expected_cells', 0)} | "
                    f"{s.get('text_edit_distance', 0)}/{s.get('reference_characters', 0)} | "
                    f"{s.get('localized_tables_iou_ge_0_5', 0)} | "
                    f"{s.get('false_positive_page', 0)}/{s.get('negative_page', 0)} |"
                )
        lines += [
            "",
            "Resources: `" + json.dumps(run["resources"], sort_keys=True) + "`.",
            "",
            "All-attempt API accounting: `" + json.dumps(run["costs"], sort_keys=True) + "`.",
            "",
        ]
        lines += [
            "",
            "Model configuration: `" + json.dumps(run["model_configuration"], sort_keys=True) + "`.",
            "",
            "| Actual request model | Retained bodies | Returned calls | Returned reported USD subtotal |",
            "|---|---:|---:|---:|",
        ]
        breakdown = run["actual_model_breakdown"]
        for model, values in breakdown["models"].items():
            subtotal = values["returned_provider_reported_usd"]["known_subtotal"]
            lines.append(
                f"| {model} | {values['retained_request_bodies']} | {values['returned_calls']} | {_fmt(subtotal)} |"
            )
            cache = {k: v for k, v in values["usage"].items() if "cache" in k}
            lines += ["", f"Provider cache fields for `{model}`: `" + json.dumps(cache, sort_keys=True) + "`.", ""]
        lines += ["", breakdown["scope"], ""]
        positive, negative = run["positive"], run["negative"]
        lines += [
            "",
            (
                f"Exact positive pages: {positive.get('exact_page', 0)}/{positive['scored_pages']}; "
                f"exact negative pages: {negative.get('exact_page', 0)}/{negative['scored_pages']}. "
                "All-page exact counts include successful empty outputs on negative pages."
            ),
            "",
        ]
        legacy = run["authored_legacy_exact"]
        lines += [
            (
                f"Authored legacy exact pages: {legacy.get('exact_page', 0)}/{legacy['scored_pages']}. "
                "This scorer is applied only to authored references."
            ),
            "",
        ]
        lines += ["- " + caveat for caveat in run["comparison_caveats"]]
    return "\n".join(lines) + "\n"


def protocol_report(protocols: dict[str, list[dict[str, Any]]], *, pending: list[str] | None = None) -> str:
    """Keep reviewed protocol datasets separate in a compact progress artifact."""
    lines = [
        "# P002 natural-PDF generalization progress",
        "",
        (
            "Only completed runs with verified frozen sources, complete retained states, exact Markdown "
            "and source ownership appear below. Missing/error pages remain in every scored denominator. "
            "Protocol groups use different frozen datasets and must not be pooled into one quality score."
        ),
        "",
    ]
    for label, runs in protocols.items():
        identities = {r["dataset_sha256"] for r in runs}
        if len(identities) > 1:
            raise ValueError("A progress protocol cannot combine different frozen datasets")
        lines += ["## " + label, "", "Dataset SHA-256: `" + next(iter(identities), "unmeasured") + "`.", ""]
        lines += [
            (
                "| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | "
                "Structure cells / expected | Exact text cells | Text edits / reference chars | IoU >= 0.5 tables | "
                "Extra tables | Effective API USD |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in runs:
            s, positive = r["scores"], r["positive"]
            cells = f"{s.get('correct_structure_cells', 0)}/{s.get('expected_cells', 0)}"
            edits = f"{s.get('text_edit_distance', 0)}/{s.get('reference_characters', 0)}"
            values = [
                r["name"],
                f"{r['operational_pages']}/{r['intended_pages']}",
                r["all_errors"],
                f"{positive.get('exact_page', 0)}/{positive['scored_pages']}",
                s.get("complete_tables", 0),
                s.get("exact_table_spans", 0),
                cells,
                s.get("correct_text_cells", 0),
                edits,
                s.get("localized_tables_iou_ge_0_5", 0),
                s.get("false_positive_tables", 0),
                r["costs"]["effective_usd"],
            ]
            lines.append("| " + " | ".join(_fmt(v) for v in values) + " |")
        for r in runs:
            lines += ["", "### " + r["name"], ""]
            config = r["config"]
            method = config.get("assembly_method", "select" if config.get("policy") == "gated" else "native")
            lines += [
                (
                    f"Policy `{config.get('policy')}`; assembly `{method}`; configured gate/selector "
                    f"`{config.get('model', 'unmeasured')}`; review `{config.get('gate_review_model', 'unmeasured')}`; "
                    f"generation `{config.get('generation_model', 'unmeasured')}`. "
                    "Actual request models are listed below; "
                    "a configured default does not prove it was called."
                ),
                "",
                (
                    "| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | "
                    "Cached prompt observations: positive / zero / missing |"
                ),
                "|---|---:|---:|---:|---:|",
            ]
            for model, data in r["actual_model_breakdown"]["models"].items():
                cache = data["usage"]["prompt_tokens_details.cached_tokens"]
                subtotal = data["returned_provider_reported_usd"]["known_subtotal"]
                lines.append(
                    f"| {model} | {data['retained_request_bodies']} | {data['returned_calls']} | {_fmt(subtotal)} | "
                    f"{cache['reported_positive']} / {cache['reported_zero']} / {cache['missing_or_invalid']} |"
                )
            if not r["actual_model_breakdown"]["models"]:
                lines.append("| No retained remote requests | 0 | 0 | unmeasured | unmeasured |")
            lines += [
                "",
                (
                    "Per-model usage/cost are returned-call observations, including calls on failed pages. "
                    "All-attempt ledger costs in the summary include failures; per-model failed-attempt charges "
                    "remain unattributed when unavailable. Provider cache fields are literal observations, "
                    "with absent fields marked missing and no local inference cache."
                ),
                "",
                (
                    "| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | "
                    "Text edits / reference chars | Negative false-positive pages |"
                ),
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
            for cohort, s in r["groups"]["cohort"].items():
                lines.append(
                    f"| {cohort} | {s['pages']}/{s['scored_pages']} | {s.get('complete_tables', 'unscored')} | "
                    f"{s.get('exact_table_spans', 'unscored')} | "
                    f"{s.get('correct_structure_cells', 'unscored')}/{s.get('expected_cells', 'unscored')} | "
                    f"{s.get('text_edit_distance', 'unscored')}/{s.get('reference_characters', 'unscored')} | "
                    f"{s.get('false_positive_page', 'unscored')}/{s.get('negative_page', 'unscored')} |"
                )
            m, costs = r["resources"], r["costs"]
            lines += [
                "",
                (
                    f"Whole-run wall {_fmt(m.get('wall_seconds'))}s; CPU {_fmt(m.get('cpu_seconds'))}s; "
                    f"sampled RSS {_fmt(m.get('peak_sampled_rss_bytes'))} bytes; "
                    f"verified output pages/min {_fmt(r['pages_per_minute'])}; "
                    f"exact positive pages/min {_fmt(r['exact_positive_pages_per_minute'])}. "
                    f"Measurement: {m.get('measurement', 'unmeasured')}. "
                    f"Per-run concurrency {_fmt(r['frozen_runtime'].get('concurrency'))}; "
                    f"logical CPUs {_fmt(r['frozen_runtime'].get('logical_cpus'))}."
                ),
                "",
                (
                    f"Ledger attempts {_fmt(costs['ledger_attempts'])}; reported USD subtotal "
                    f"{_fmt(costs['provider_reported_subtotal_usd'])}; missing reported charges "
                    f"{_fmt(costs['missing_provider_charge_count'])}; cost bases `{json.dumps(costs['cost_bases'])}`. "
                    f"Reservation amount {_fmt(costs['reservation_usd'])}; "
                    f"estimate amount {_fmt(costs['estimated_usd'])}."
                ),
                "",
            ]
    if pending:
        lines += ["## Pending completed reports", "", *["- " + name for name in pending], ""]
    lines += [
        "## Interpretation",
        "",
        (
            "Exact topology and character edits separate structural assembly from text agreement. "
            "Text edits are positional table text errors, not independent raster OCR CER; character "
            "inventory observations are diagnostics only. Low IoU >= 0.1 correspondences are not "
            "detection recall or AP. The stricter localization count uses IoU >= 0.5; legacy prediction "
            "boxes derive from owned text extents and can lie inside annotated table borders."
        ),
        "",
        (
            "Negative-page empty outputs can be exact without recovering a positive table. "
            "Authored DEV silver, independently annotated Omni pages, and unscored native diagnostics "
            "remain separate. A protocol screen is a predeclared DEV experiment, not a heldout estimate. "
            "Runs with different packet, OCR, generation, image or region settings are not isolated "
            "causal comparisons. Concurrent background workloads may affect timings."
        ),
        "",
    ]
    return "\n".join(lines) + "\n"


def _fmt(value: object) -> str:
    if value is None:
        return "unmeasured"
    return f"{value:.6g}" if isinstance(value, float) else str(value).replace("|", "\\|")


def main() -> None:
    """Score explicitly named complete runs and write private JSON plus Markdown."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output stem; writes .json and .md")
    args = parser.parse_args()
    manifest, targets = load_corpus(args.corpus)
    runs = [score_run(guard_path(path), args.corpus / "manifest.json", manifest, targets) for path in args.run]
    destination = guard_path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.with_suffix(".json").write_text(json.dumps({"schema": 1, "runs": runs}, indent=2) + "\n")
    destination.with_suffix(".md").write_text(markdown_report(runs))


if __name__ == "__main__":
    main()
