"""Independent exact replay of model-selected complete synthetic-diagram crop states."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415, TRY301
from __future__ import annotations

import base64
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bench.silver import guard_path, sha

BODY_CAP = 750_000


def read(path: Path) -> Any:  # noqa: ANN401
    """Read explicitly supplied guarded evidence."""
    return json.loads(guard_path(path).read_bytes())


def verify_decisions(
    directory: Path,
    selected: list[dict[str, Any]],
    config: dict[str, Any],
    decisions: list[dict[str, Any]],
    *,
    initialization_failed: bool,
) -> None:
    """Strictly replay native choices and preserve first-error stop without fallback or retries."""
    from bench import p003_candidate_choice as chooser

    if len(selected) != len(decisions):
        raise ValueError("Incomplete diagram decision inventory")
    stopped, indexes = initialization_failed, set()
    for item, row in zip(selected, decisions, strict=True):
        index = item["index"]
        if {k: row.get(k) for k in ("index", "page_id", "crop_index", "model")} != {
            "index": index,
            "page_id": item["page_id"],
            "crop_index": item["crop_index"],
            "model": config["model"],
        } or read(directory / f"crop-{index}-result.json") != row:
            raise ValueError("Diagram decision identity/model/result differs")
        path = directory / f"crop-{index}-response.json"
        if item["body"] is None:
            if row["status"] != item["status"] or path.exists():
                raise ValueError("Diagram no-question crop was attempted or credited")
        elif stopped:
            if row["status"] != "not_attempted" or path.exists():
                raise ValueError("Diagram admission continued after first transport failure")
        elif row["status"] == "transport_error":
            if path.exists() or not row.get("error"):
                raise ValueError("Diagram transport error has an answer or lacks provenance")
            stopped = True
        else:
            response = read(path)
            entry = response.get("entry")
            if (
                not isinstance(entry, dict)
                or entry != row.get("entry")
                or response.get("replayed") != row.get("replayed")
                or entry.get("request_sha256") != item["request_sha256"]
                or entry.get("requested_model") != config["model"]
                or entry.get("tag") != f"P003/{config['run_id']}/geometry-diagram/{index}"
                or type(entry.get("index")) is not int
                or entry["index"] in indexes
            ):
                raise ValueError("Diagram response request/model/tag/index attribution differs")
            indexes.add(entry["index"])
            try:
                if response.get("replayed"):
                    raise ValueError("Fresh diagram decision cannot replay answers")
                parsed = chooser.parse(item["pool"], response["result"])
                chosen, audit = chooser.select(item["pool"], parsed)
            except (ValueError, KeyError, TypeError):
                if row["status"] != "malformed_response" or not row.get("error"):
                    raise ValueError("Malformed diagram receipt was credited as selection") from None
            else:
                if row["status"] != audit["selection_status"] or row.get("audit") != audit:
                    raise ValueError("Diagram choice differs from exact native receipt")
                if chosen is None:
                    if "selected_canonical_json" in row or "selected_sha256" in row:
                        raise ValueError("Abstention contains selected candidate bytes")
                elif row.get("selected_canonical_json") != chosen.decode() or row.get("selected_sha256") != sha(chosen):
                    raise ValueError("Diagram selected state differs from immutable complete candidate")
            raw = response.get("result")
            if row.get("usage") != (raw.get("usage", {}) if isinstance(raw, dict) else {}):
                raise ValueError("Diagram usage differs from retained response")


def quality_predictions(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Credit disjoint selected complete crops on partial error pages; preserve operational errors separately."""
    return [
        {
            **p,
            "status": "ok" if p["selection_status"] == "selected_partial_crops" else p["status"],
            "selected_model_regions": p["accepted_crop_count"],
        }
        for p in report["results"]
    ]


def verify_geometry_diagram(
    directory: Path, report: dict[str, Any], frozen: dict[str, Any], trusted: dict[str, dict[str, str]] | None
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Reconstruct the entire independently authenticated pool, bodies, receipts and partial composition."""
    from bench import p003_geometry_diagram as diagram
    from bench import p003_geometry_diagram_run as runner
    from bench import pipeline_vision_transcription as transcription
    from bench.p003_boundary_run import _charges

    if not trusted or set(trusted) != {"pool", "selector", "source", "input-0", "input-1"}:
        raise ValueError("Independent pool/selector/source/input-0/input-1 authorities required")
    config = frozen["config"]
    declared = runner.configuration(
        config["model"], config["mode"], config["image_edge"], config["transport_concurrency"]
    )
    if config != {**declared, "run_id": config["run_id"]} or report["config"] != config:
        raise ValueError("Unsupported diagram treatment/configuration")
    for name in (
        "p003_geometry_diagram_run.py",
        "p003_geometry_diagram.py",
        "p003_geometry_diagram_prepare.py",
        "p003_candidate_choice.py",
        "pipeline_vision_transcription.py",
    ):
        if frozen["code_sha256"].get(name) != sha(Path(runner.__file__).with_name(name).read_bytes()):
            raise ValueError("Unsupported frozen diagram replay helper version")
    if frozen.get("all_inputs_frozen_before_client") is not True or frozen.get("references_read") is not False:
        raise ValueError("Diagram evidence was not frozen before answers")
    for name, digest in frozen["artifact_sha256"].items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or sha(guard_path(directory / relative).read_bytes()) != digest
        ):
            raise ValueError("Copied immutable diagram evidence changed")
    authorities = frozen["independent_authorities"]
    paths = {k: guard_path(Path(authorities[k])) for k in ("pool", "selector", "source")}
    paths.update({f"input-{i}": guard_path(Path(p)) for i, p in enumerate(authorities["inputs"])})
    if set(paths) != set(trusted) or any(read(p) != trusted[k] for k, p in paths.items()):
        raise ValueError("Recorded authority paths differ from independent maps")
    pool = directory / "pool"
    if (
        sha((pool / "frozen.json").read_bytes()) != frozen["pool_frozen_sha256"]
        or sha((pool / "report.json").read_bytes()) != frozen["pool_report_sha256"]
    ):
        raise ValueError("Diagram parent pool changed")
    prepared = runner.authenticate_pool(
        pool, paths["pool"], paths["selector"], paths["source"], [paths["input-0"], paths["input-1"]]
    )
    if prepared["frozen"]["records"] != frozen["records"]:
        raise ValueError("Diagram intended source records changed")
    for receipt in frozen["historical_provenance"]:
        if receipt["archive"] != "history/" + receipt["name"]:
            raise ValueError("Diagram historical archive changed")
        copied = directory / receipt["archive"]
        for kind in ("frozen", "report"):
            if sha((copied / (kind + ".json")).read_bytes()) != receipt[kind + "_sha256"]:
                raise ValueError("Diagram historical provenance changed")
    selected = []
    for page in prepared["report"]["pages"]:
        for crop in page["crops"]:
            item = {
                "index": len(selected),
                "page_id": page["id"],
                "crop_index": crop["index"],
                "crop": crop,
                "body": None,
                "status": crop["status"],
            }
            if crop["status"] == "prepared":
                variant = next(
                    v for v in crop["variants"] if v["edge"] == config["image_edge"] and v["style"] == config["mode"]
                )
                image = (pool / variant["image_path"]).read_bytes()
                if sha(image) != variant["image_sha256"]:
                    raise ValueError("Diagram selected image changed")
                candidates = runner.hydrate(read(pool / crop["folder"] / "pool.json"))
                body, evidence = diagram.request(
                    candidates, config["model"], "data:image/png;base64," + base64.b64encode(image).decode()
                )
                item.update(body=body, pool=candidates, evidence=evidence, status=evidence["status"], variant=variant)
            if item["body"] is not None:
                encoded = json.dumps(item["body"], separators=(",", ":"), allow_nan=False).encode()
                item["request_sha256"] = sha(encoded)
                if (
                    len(encoded) > BODY_CAP
                    or read(directory / f"crop-{item['index']}-request.json") != item["body"]
                    or (directory / f"crop-{item['index']}-wire.json").read_bytes() != encoded
                ):
                    raise ValueError("Diagram actual wire differs from source diagram/candidate reconstruction")
            elif (directory / f"crop-{item['index']}-request.json").exists():
                raise ValueError("Diagram refused crop has a request")
            selected.append(item)
    if [{k: v for k, v in i.items() if k not in {"pool", "body"}} for i in selected] != frozen["selected"]:
        raise ValueError("Diagram selected inventory changed")
    decisions = report["decisions"]
    if read(directory / "decision-results.json") != {"decisions": decisions}:
        raise ValueError("Diagram checkpoint differs from report")
    verify_decisions(
        directory,
        selected,
        config,
        decisions,
        initialization_failed=report.get("client_initialization_error") is not None,
    )
    attempted = sum(
        r["status"] in {"selected", "unresolved", "malformed_response", "transport_error"} for r in decisions
    )
    charges = report["incremental_selection"]["charges"]
    entries = charges["entries"]
    prefix = f"P003/{config['run_id']}/geometry-diagram/"
    by_index, ledger_indexes, ledger_tags = {str(i["index"]): i for i in selected}, set(), set()
    for entry in entries:
        tag = entry.get("tag", "")
        item = by_index.get(tag.removeprefix(prefix)) if tag.startswith(prefix) else None
        if (
            item is None
            or item["body"] is None
            or entry.get("requested_model") != config["model"]
            or entry.get("request_sha256") != item["request_sha256"]
            or type(entry.get("index")) is not int
            or entry["index"] in ledger_indexes
            or tag in ledger_tags
            or decisions[item["index"]]["status"]
            not in {"selected", "unresolved", "malformed_response", "transport_error"}
        ):
            raise ValueError("Unattributed/duplicate diagram ledger attempt")
        ledger_indexes.add(entry["index"])
        ledger_tags.add(tag)
    expected_tags = {
        prefix + str(r["index"])
        for r in decisions
        if r["status"] in {"selected", "unresolved", "malformed_response", "transport_error"}
    }
    if entries and ledger_tags != expected_tags:
        raise ValueError("Diagram accounting omits attempted questions or includes unattempted questions")
    if entries and any(r.get("entry", {}).get("index") not in ledger_indexes for r in decisions if r.get("entry")):
        raise ValueError("Diagram returned receipt missing from accounting inventory")
    expected_charges = _charges(entries)
    expected_charges["cost_scope"] = (
        "Incremental geometry-diagram selection API attempts including failures; "
        "excludes all historical acquisition/generation/selector costs"
    )
    if attempted and not entries:
        expected_charges.update(
            effective_usd=None, provider_reported_usd=None, accounting_status="unmeasured missing attempts"
        )
    if charges != expected_charges:
        raise ValueError("Diagram accounting differs from attempt inventory")
    results, verified = [], {}
    for page in prepared["report"]["pages"]:
        source = read(pool / page["source_path"])
        rows = [r for r in decisions if r["page_id"] == page["id"]]
        assembled = runner.assemble({**page, "source": source}, rows)
        row = {
            "id": page["id"],
            "record": page.get("record"),
            "viewport": source["page_size"],
            "original_rotation": page.get("original_rotation"),
            "effective_rotation": page.get("effective_rotation"),
            **assembled,
            "tables": assembled["state"]["tables"],
            "selection_status": assembled["decision_status"],
            "crop_count": len(page["crops"]),
            "selected_decision_crop_count": sum(r["status"] == "selected" for r in rows),
            "accepted_crop_count": sum(r["status"] == "selected" for r in rows)
            if assembled["decision_status"] in {"selected_complete_crops", "selected_partial_crops"}
            else 0,
            "complete_crop_coverage": assembled["decision_status"] in {"selected_complete_crops", "no_detector_crops"},
            "decision_results": rows,
            "model": config["model"],
            "pure_model": True,
            "baseline_credit": False,
            "source_conserved": False,
            "predicted_table_count": len(assembled["state"]["tables"]),
        }
        if (
            read(directory / f"{page['id']}-result.json") != row
            or read(directory / f"{page['id']}-state.json") != row["state"]
            or read(directory / f"{page['id']}-structure.json") != row["tables"]
            or (directory / f"{page['id']}.md").read_bytes() != transcription.markdown(row["state"]).encode()
        ):
            raise ValueError("Diagram complete/partial composition differs from exact selected crop bytes")
        results.append(row)
        verified[page["id"]] = {"operational": row["status"] == "ok", "conserved": False}
    claims = {
        "intended_page_count": len(results),
        "valid_completed_page_count": sum(v["operational"] for v in verified.values()),
        "model_credited_page_count": sum(r["predicted_table_count"] > 0 for r in results),
        "no_detector_crop_page_count": sum(r["selection_status"] == "no_detector_crops" for r in results),
        "attempted_question_count": attempted,
        "decision_status_counts": dict(Counter(r["status"] for r in decisions)),
        "full_pipeline_pages_per_minute": None,
        "full_pipeline_pages_per_dollar": None,
        "baseline_credit": False,
        "model_fallbacks": 0,
        "retries": 0,
        "references_read": False,
    }
    if results != report["results"] or any(report.get(k) != v for k, v in claims.items()):
        raise ValueError("Diagram report scope/count claims differ from replay")
    return {
        "scope": "Immutable historical acquisition/generation/selector; excluded from incremental quality/cost",
        "historical_provenance": frozen["historical_provenance"],
        "pool_sha256": frozen["pool_frozen_sha256"],
    }, verified
