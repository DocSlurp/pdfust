"""Independent replay of actual complete header choices, without historical-table credit."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415, TRY301
from __future__ import annotations

import base64
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bench.silver import guard_path, sha

PAGES = 16
BODY_CAP = 750_000


def read(path: Path) -> Any:  # noqa: ANN401
    """Read explicitly selected guarded evidence."""
    return json.loads(guard_path(path).read_bytes())


def verify_decisions(
    directory: Path,
    selected: list[dict[str, Any]],
    config: dict[str, Any],
    decisions: list[dict[str, Any]],
    *,
    initialization_failed: bool,
) -> None:
    """Require exact native answer attribution and first-error stop, without fallback or retries."""
    from bench import p003_header_packets as packets

    if len(selected) != len(decisions):
        raise ValueError("Incomplete header decision inventory")
    stopped, indexes = initialization_failed, set()
    for item, row in zip(selected, decisions, strict=True):
        index = item["index"]
        if {k: row.get(k) for k in ("index", "page_id", "menu_id", "model")} != {
            "index": index,
            "page_id": item["page_id"],
            "menu_id": item["menu"]["id"],
            "model": config["model"],
        } or read(directory / f"menu-{index}-result.json") != row:
            raise ValueError("Header decision identity/model/checkpoint differs")
        path = directory / f"menu-{index}-response.json"
        if item["body"] is None:
            if row["status"] != "no_question_refusal" or row.get("refusal") != item["evidence"] or path.exists():
                raise ValueError("Header no-question refusal was attempted or credited")
        elif stopped:
            if row["status"] != "not_attempted" or path.exists():
                raise ValueError("Header admission continued after first transport failure")
        elif row["status"] == "transport_error":
            if path.exists() or not row.get("error"):
                raise ValueError("Header transport failure contains an answer or lacks provenance")
            stopped = True
        else:
            response = read(path)
            entry = response.get("entry")
            actual_sha = sha(json.dumps(item["body"], separators=(",", ":"), allow_nan=False).encode())
            if (
                not isinstance(entry, dict)
                or entry != row.get("entry")
                or response.get("replayed") != row.get("replayed")
                or entry.get("request_sha256") != actual_sha
                or entry.get("requested_model") != config["model"]
                or entry.get("tag") != f"P003/{config['run_id']}/header-decision/{index}"
                or type(entry.get("index")) is not int
                or entry["index"] in indexes
            ):
                raise ValueError("Header response request/model/tag/index attribution differs")
            indexes.add(entry["index"])
            try:
                if response.get("replayed"):
                    raise ValueError("Fresh header choices cannot replay answers")
                receipt = packets.parse(item["menu"], response["result"])
            except (ValueError, KeyError, TypeError):
                if row["status"] != "malformed_response" or not row.get("error") or row.get("receipt"):
                    raise ValueError("Malformed header answer credited as selection") from None
            else:
                expected_status = "unresolved" if receipt["choice"] == "unresolved" else "selected"
                option = next((o for o in item["menu"]["options"] if o["alias"] == receipt["choice"]), None)
                if row["status"] != expected_status or row.get("receipt") != receipt:
                    raise ValueError("Header choice differs from exact native receipt")
                if row.get("selected_table_sha256") != (option["table_sha256"] if option else None):
                    raise ValueError("Header selected table differs from frozen complete alternative")
            raw = response.get("result")
            if row.get("usage") != (raw.get("usage", {}) if isinstance(raw, dict) else {}):
                raise ValueError("Header usage differs from retained raw response")
        if row["status"] not in {"selected", "unresolved"} and (row.get("receipt") or row.get("selected_table_sha256")):
            raise ValueError("Failed header decision contains selected-table credit")


def quality_predictions(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve selected complete tables on partial pages; fixed historical tables receive no credit."""
    return [
        {
            **p,
            "status": "ok" if p["tables"] else p["status"],
            "selected_model_regions": p.get("model_credited_table_count", len(p["tables"])),
        }
        for p in report["results"]
    ]


def verify_header_decision(
    directory: Path, report: dict[str, Any], frozen: dict[str, Any], trusted: dict[str, dict[str, str]] | None
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Rebuild all frozen menus and actual wire bytes, then replay selected/fixed compositions separately."""
    from bench import p003_header_decision_run as runner
    from bench import p003_header_packets as packets
    from bench import pipeline_vision_transcription as strict
    from bench.p003_boundary_run import _charges

    if not trusted or set(trusted) != {"pool", "header", "generation"}:
        raise ValueError("Independent pool/header/generation authorities required")
    config = frozen["config"]
    declared = runner.configuration(
        config["model"], config["evidence_mode"], config["image_edge"], config["transport_concurrency"]
    )
    if config != {**declared, "run_id": config["run_id"]} or report["config"] != config:
        raise ValueError("Unsupported header treatment/configuration")
    for name in (
        "p003_header_decision_run.py",
        "p003_header_packets.py",
        "p003_header_packets_prepare.py",
        "p003_header_proposals.py",
        "pipeline_vision_transcription.py",
    ):
        if frozen["code_sha256"].get(name) != sha(Path(runner.__file__).with_name(name).read_bytes()):
            raise ValueError("Unsupported frozen header replay helper version")
    if frozen.get("all_inputs_frozen_before_client") is not True or frozen.get("references_read") is not False:
        raise ValueError("Header evidence was not frozen before answers")
    for name, digest in frozen["artifact_sha256"].items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or sha(guard_path(directory / relative).read_bytes()) != digest
        ):
            raise ValueError("Copied immutable header evidence changed")
    paths = {k: guard_path(Path(frozen["independent_authorities"][k])) for k in trusted}
    if any(read(p) != trusted[k] for k, p in paths.items()):
        raise ValueError("Recorded header authority differs from independent map")
    pool = directory / "pool"
    if (
        sha((pool / "frozen.json").read_bytes()) != frozen["pool_frozen_sha256"]
        or sha((pool / "report.json").read_bytes()) != frozen["pool_report_sha256"]
    ):
        raise ValueError("Header source-only pool changed")
    prepared = runner.authenticate_pool(pool, paths["pool"], paths["header"], paths["generation"])
    if prepared["pool_frozen"]["records"] != frozen["records"] or len(frozen["records"]) != PAGES:
        raise ValueError("Header intended records changed")
    for receipt in frozen["historical_provenance"]:
        if receipt["archive"] != "history/" + receipt["kind"]:
            raise ValueError("Header historical archive path changed")
        for kind in ("frozen", "report"):
            if sha((directory / receipt["archive"] / (kind + ".json")).read_bytes()) != receipt[kind + "_sha256"]:
                raise ValueError("Header historical provenance changed")
    historical = read(directory / "history/generation/frozen.json")
    if (
        historical["manifest_sha256"] != frozen["manifest_sha256"]
        or historical["config"] != frozen["literal_generation_config"]
        or report["literal_generation_config"] != historical["config"]
    ):
        raise ValueError("Literal generation provenance differs from decision model")
    selected = []
    for page in prepared["pages"]:
        for retained in page["menus"]:
            menu = packets.hydrate(retained)
            inventory = next(m for m in prepared["pool_report"]["menus"] if m["menu_id"] == menu["id"])
            variant = next(
                v
                for v in inventory["variants"]
                if v["mode"] == config["evidence_mode"]
                and v["image_edge"] == config["image_edge"]
                and v["model"] == config["model"]
            )
            url = None
            if config["image_edge"]:
                image = (pool / "menus" / menu["id"] / f"image-{config['image_edge']}.png").read_bytes()
                url = "data:image/png;base64," + base64.b64encode(image).decode()
            body, evidence = packets.request(menu, config["model"], url, config["evidence_mode"])
            item = {
                "index": len(selected),
                "page_id": page["id"],
                "menu": menu,
                "body": body,
                "evidence": evidence,
                "variant": variant,
                "request_sha256": None,
            }
            if evidence != read(pool / variant["evidence_path"]):
                raise ValueError("Header evidence omissions differ from freeze")
            if body is not None:
                encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
                item["request_sha256"] = sha(encoded)
                if (
                    len(encoded) > BODY_CAP
                    or sha(encoded) != variant["body_sha256"]
                    or body != read(pool / variant["request_path"])
                    or body != read(directory / f"menu-{item['index']}-request.json")
                    or encoded != (directory / f"menu-{item['index']}-wire.json").read_bytes()
                ):
                    raise ValueError("Header actual wire differs from literal menu/image reconstruction")
            elif (directory / f"menu-{item['index']}-request.json").exists() or (
                directory / f"menu-{item['index']}-wire.json"
            ).exists():
                raise ValueError("Refused header menu contains a request")
            selected.append(item)
    if [{k: v for k, v in i.items() if k != "body"} for i in selected] != frozen["selected"]:
        raise ValueError("Header selected inventory differs")
    decisions = report["decisions"]
    if read(directory / "decision-results.json") != {"decisions": decisions}:
        raise ValueError("Header decision checkpoint differs")
    verify_decisions(
        directory,
        selected,
        config,
        decisions,
        initialization_failed=report.get("client_initialization_error") is not None,
    )
    attempted_statuses = {"selected", "unresolved", "malformed_response", "transport_error"}
    attempted = sum(r["status"] in attempted_statuses for r in decisions)
    charges = report["incremental_header_selection"]["charges"]
    entries = charges["entries"]
    prefix = f"P003/{config['run_id']}/header-decision/"
    by_index, indexes, tags = {str(i["index"]): i for i in selected}, set(), set()
    for entry in entries:
        tag = entry.get("tag", "")
        item = by_index.get(tag.removeprefix(prefix)) if tag.startswith(prefix) else None
        if (
            item is None
            or item["body"] is None
            or entry.get("requested_model") != config["model"]
            or entry.get("request_sha256") != item["request_sha256"]
            or type(entry.get("index")) is not int
            or entry["index"] in indexes
            or tag in tags
            or decisions[item["index"]]["status"] not in attempted_statuses
        ):
            raise ValueError("Unattributed or duplicate header ledger attempt")
        indexes.add(entry["index"])
        tags.add(tag)
    expected_tags = {prefix + str(r["index"]) for r in decisions if r["status"] in attempted_statuses}
    if entries and (
        tags != expected_tags
        or any(r.get("entry", {}).get("index") not in indexes for r in decisions if r.get("entry"))
    ):
        raise ValueError("Header accounting omits attempted questions")
    expected_charges = _charges(entries)
    expected_charges["cost_scope"] = (
        "Incremental factorized header-choice API attempts including failures; "
        "excludes original generation/source/pool preparation"
    )
    if attempted and not entries:
        expected_charges.update(
            effective_usd=None, provider_reported_usd=None, accounting_status="unmeasured missing attempts"
        )
    if charges != expected_charges:
        raise ValueError("Header accounting differs from exact attempts")
    results, verified = [], {}
    for page in prepared["pages"]:
        ident = page["id"]
        items = [i for i in selected if i["page_id"] == ident]
        rows = [r for r in decisions if r["page_id"] == ident]
        receipts = {r["menu_id"]: r["receipt"] for r in rows if r["status"] in {"selected", "unresolved"}}
        composed = packets.compose(page["plan"], [i["menu"] for i in items], receipts)
        state, fixed, combined = (composed[k] for k in ("selected_state", "fixed_state", "combined_state"))
        complete = bool(rows) and composed["complete_header_selection"]
        operational = complete or (not rows and page["plan"]["status"] == "unchanged_valid")
        row = {
            "id": ident,
            "record": page["record"],
            "viewport": page["plan"]["original_page"]["viewport"],
            "status": "ok" if operational else "error",
            "selection_status": "composition_conflicts"
            if composed["conflicts"]
            else "selected_complete_headers"
            if complete
            else "not_applicable_no_ambiguous_header"
            if not rows and operational
            else "selected_partial_headers"
            if state["tables"]
            else "failed_closed",
            "original_page_status": page["plan"]["original_page_status"],
            "state": state,
            "tables": state["tables"],
            "fixed_state": fixed,
            "combined_state": combined,
            "composition": composed,
            "decision_results": rows,
            "selected_header_count": sum(r["status"] == "selected" for r in rows),
            "effective_selected_header_count": sum(r["effective_selected"] for r in composed["receipts"]),
            "uncovered_header_count": sum(r["status"] != "selected" for r in rows),
            "fixed_historical_table_count": len(fixed["tables"]),
            "model_credited_table_count": len(state["tables"]),
            "model": config["model"],
            "decision_model": config["model"],
            "literal_generation_model": historical["config"].get("generation_model"),
            "baseline_credit": False,
            "source_conserved": False,
        }
        if read(directory / f"{ident}-result.json") != row:
            raise ValueError("Header model-selected/fixed composition differs")
        for suffix, value in (("state", state), ("fixed-state", fixed), ("combined-state", combined)):
            if read(directory / f"{ident}-{suffix}.json") != value:
                raise ValueError("Header primary or historical diagnostic state changed")
        for suffix, value in (("structure", state["tables"]), ("combined-structure", combined["tables"])):
            if read(directory / f"{ident}-{suffix}.json") != value:
                raise ValueError("Header table artifact differs from complete selected alternative")
        if (directory / f"{ident}.md").read_bytes() != strict.markdown(state).encode() or (
            directory / f"{ident}-combined.md"
        ).read_bytes() != strict.markdown(combined).encode():
            raise ValueError("Header Markdown differs from strict selected/fixed rendering")
        results.append(row)
        verified[ident] = {"operational": operational, "conserved": False}
    claims = {
        "intended_page_count": 16,
        "attempted_question_count": attempted,
        "selected_header_count": sum(r["status"] == "selected" for r in decisions),
        "decision_status_counts": dict(Counter(r["status"] for r in decisions)),
        "full_pipeline_pages_per_minute": None,
        "full_pipeline_pages_per_dollar": None,
        "model_fallbacks": 0,
        "retries": 0,
        "baseline_credit": False,
        "references_read": False,
        "historical_provenance": frozen["historical_provenance"],
    }
    if results != report["results"] or any(report.get(k) != v for k, v in claims.items()):
        raise ValueError("Header report scope/count claims differ")
    return {
        "scope": "Historical literal generation and source-only hypotheses; no incremental model credit or cost",
        "historical_provenance": frozen["historical_provenance"],
        "pool_sha256": frozen["pool_frozen_sha256"],
    }, verified
