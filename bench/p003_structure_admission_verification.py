"""Independent replay of pure model admissions over immutable source-owned geometry."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415, TRY301
from __future__ import annotations

import base64
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bench.silver import guard_path, sha


def read(path: Path) -> dict[str, Any]:
    """Read an explicit guarded artifact."""
    return json.loads(guard_path(path).read_bytes())


def verify_decisions(
    directory: Path,
    selected: list[dict[str, Any]],
    config: dict[str, Any],
    decisions: list[dict[str, Any]],
    *,
    initialization_failed: bool,
) -> None:
    """Reparse every returned raw answer and enforce fresh distinct attempts and first-error stop."""
    from bench import p003_structure_admission as admission
    from bench import p003_structure_admission_run as runner

    if len(decisions) != len(selected):
        raise ValueError("Incomplete admission decision inventory")
    stopped, entry_indexes = initialization_failed, set()
    for item, row in zip(selected, decisions, strict=True):
        index = item["index"]
        if {k: row.get(k) for k in ("index", "candidate_id", "page_id", "model")} != {
            "index": index,
            "candidate_id": item["candidate"]["id"],
            "page_id": item["page_id"],
            "model": config["model"],
        }:
            raise ValueError("Decision identity/model differs from frozen candidate")
        if read(directory / f"candidate-{index}-result.json") != row:
            raise ValueError("Decision result differs from report")
        path = directory / f"candidate-{index}-response.json"
        status = row["status"]
        if item["body"] is None:
            if status != "no_question_refusal" or path.exists():
                raise ValueError("Oversized complete question was attempted")
        elif stopped:
            if status != "not_attempted" or path.exists():
                raise ValueError("Admission continued after first transport failure")
        elif status == "transport_error":
            if path.exists() or not row.get("error"):
                raise ValueError("Transport failure has a returned answer or lacks error provenance")
            stopped = True
        else:
            response = read(path)
            if response.get("entry") != row.get("entry") or response.get("replayed") != row.get("replayed"):
                raise ValueError("Response receipt differs from retained decision")
            entry = response.get("entry")
            if not isinstance(entry, dict):
                raise ValueError("Returned decision lacks request attribution")
            encoded = json.dumps(item["body"], separators=(",", ":"), allow_nan=False).encode()
            if (
                entry.get("request_sha256") != sha(encoded)
                or entry.get("requested_model") != config["model"]
                or entry.get("tag") != f"P003/{config['run_id']}/structure-admission/{index}"
                or type(entry.get("index")) is not int
                or entry.get("index") in entry_indexes
            ):
                raise ValueError("Returned decision request hash/model/tag/index differs")
            entry_indexes.add(entry.get("index"))
            try:
                if response.get("replayed"):
                    raise ValueError("Fresh admission contains replayed result")
                parsed = runner.receipt(response["result"])
            except (ValueError, KeyError, TypeError):
                if status != "malformed_response" or not row.get("error"):
                    raise ValueError("Invalid native answer was credited as successful admission") from None
            else:
                if status not in admission.CHOICES or status != parsed["choice"] or row.get("receipt") != parsed:
                    raise ValueError("Admission decision differs from exact raw native parsing")
            result = response.get("result")
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            if row.get("usage") != usage:
                raise ValueError("Decision usage differs from retained response")


def verify_structure_admission(
    directory: Path, report: dict[str, Any], frozen: dict[str, Any], trusted: dict[str, dict[str, str]] | None
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Authenticate original evidence, reconstruct all bodies, then replay no-fallback whole pages."""
    from bench import p003_structure_admission as admission
    from bench import p003_structure_admission_run as runner
    from bench.p003_boundary_run import _charges
    from bench.p003_gate_run import authenticate

    if not trusted or set(trusted) != {"pool", "source"}:
        raise ValueError("Independent pool and source maps required under pool/source keys")
    config = frozen["config"]
    declared = runner.configuration(
        config["model"],
        config["acquisition"],
        config["threshold"],
        config["image_edge"],
        config["transport_concurrency"],
    )
    if config != {**declared, "run_id": config["run_id"]} or report["config"] != config:
        raise ValueError("Unsupported structure-admission treatment or changed configuration")
    for name in (
        "p003_structure_admission_run.py",
        "p003_structure_admission.py",
        "p003_structure_geometry.py",
        "p003_structure_acquisition_infer.py",
        "p003_structure_density_infer.py",
        "pipeline_assembly.py",
        "pipeline_repair.py",
        "pipeline_run.py",
        "p003_topology_ownership.py",
    ):
        if frozen["code_sha256"].get(name) != sha(Path(runner.__file__).with_name(name).read_bytes()):
            raise ValueError("Unsupported frozen structure-admission replay helper version")
    if frozen.get("all_inputs_frozen_before_client") is not True or frozen.get("references_read") is not False:
        raise ValueError("Admission inputs were not declared frozen before hosted answers")
    for name, digest in frozen["artifact_sha256"].items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or sha(guard_path(directory / relative).read_bytes()) != digest
        ):
            raise ValueError("Copied immutable admission evidence changed")
    pool = directory / "pool"
    if (
        sha((pool / "frozen.json").read_bytes()) != frozen["pool"]["frozen_sha256"]
        or sha((pool / "report.json").read_bytes()) != frozen["pool"]["report_sha256"]
        or frozen["pool"]["trusted_code"] != trusted["pool"]
        or frozen["source_trusted_code"] != trusted["source"]
    ):
        raise ValueError("Admission pool/source provenance differs from external authority")
    prepared = runner.authenticate_pool(pool, trusted["pool"], trusted["source"])
    records = [p["record"] for p in prepared["pages"].values()]
    if records != frozen["records"] or len(records) != config["full_page_denominator"]:
        raise ValueError("Admission source inventory differs")
    for index, (original_path, original) in enumerate(prepared["baselines"].items()):
        receipt = frozen["baselines"][index]
        copied = directory / "baselines" / str(index)
        if receipt["archive"] != f"baselines/{index}" or receipt["directory"] != str(original_path):
            raise ValueError("Copied baseline identity changed")
        actual = authenticate(copied, trusted["source"])
        if (
            actual != original
            or sha((copied / "frozen.json").read_bytes()) != receipt["frozen_sha256"]
            or sha((copied / "report.json").read_bytes()) != receipt["report_sha256"]
        ):
            raise ValueError("Copied baseline differs from authenticated original")
    selected = []
    for entry in prepared["report"]["entries"]:
        if entry["arm"] != config["acquisition"] or entry["threshold"] != config["threshold"]:
            continue
        candidate = read(pool / entry["folder"] / "candidate.json")
        variant = next(v for v in entry["variants"] if v["treatment"] == config["treatment"])
        candidate["question_status"] = variant["packet"]["status"]
        body = None
        if candidate["question_status"] == "prepared":
            text = (pool / entry["folder"] / (config["treatment"] + "-packet.json")).read_text()
            url = None
            if config["image_edge"]:
                raw = (pool / entry["folder"] / (config["treatment"] + ".png")).read_bytes()
                url = "data:image/png;base64," + base64.b64encode(raw).decode()
            body = admission.request(config["model"], text, url)
        index = len(selected)
        selected.append(
            {"page_id": entry["page_id"], "candidate": candidate, "variant": variant, "index": index, "body": body}
        )
        if body is not None:
            encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
            if (
                read(directory / f"candidate-{index}-request.json") != body
                or (directory / f"candidate-{index}-wire.json").read_bytes() != encoded
            ):
                raise ValueError("Admission request differs from complete frozen source/pixels")
        elif (directory / f"candidate-{index}-request.json").exists() or (
            directory / f"candidate-{index}-wire.json"
        ).exists():
            raise ValueError("Refused complete evidence has a request")
    if [{k: v for k, v in s.items() if k != "body"} for s in selected] != frozen["selected"]:
        raise ValueError("Selected candidate inventory differs from source-only reconstruction")
    decisions = report["decisions"]
    if read(directory / "decision-results.json") != {"decisions": decisions}:
        raise ValueError("Checkpointed decision inventory differs")
    verify_decisions(
        directory,
        selected,
        config,
        decisions,
        initialization_failed=report.get("client_initialization_error") is not None,
    )
    attempted = sum(r["status"] not in {"not_attempted", "no_question_refusal"} for r in decisions)
    if report.get("attempted_question_count") != attempted:
        raise ValueError("Admission attempted-question count differs")
    charges = report["incremental_admission"]["charges"]
    entries = charges["entries"]
    ledger_indexes = set()
    selected_by_index = {str(s["index"]): s for s in selected}
    prefix = f"P003/{config['run_id']}/structure-admission/"
    for entry in entries:
        tag = entry.get("tag", "")
        item = selected_by_index.get(tag.removeprefix(prefix)) if tag.startswith(prefix) else None
        if item is None or item["body"] is None or entry.get("requested_model") != config["model"]:
            raise ValueError("Unattributed or refused admission ledger attempt")
        digest = sha(json.dumps(item["body"], separators=(",", ":"), allow_nan=False).encode())
        if entry.get("request_sha256") != digest or entry.get("index") in ledger_indexes:
            raise ValueError("Duplicate or changed admission ledger request")
        ledger_indexes.add(entry.get("index"))
    expected_charges = _charges(entries)
    expected_charges["cost_scope"] = (
        "Incremental structure-admission API attempts only, including failures; "
        "excludes OCR/TATR and historical baseline costs"
    )
    if attempted and not entries:
        expected_charges.update(
            effective_usd=None, provider_reported_usd=None, accounting_status="unmeasured missing attempts"
        )
    if charges != expected_charges:
        raise ValueError("Admission accounting differs from retained attempt inventory")
    verified = {}
    expected_results = []
    for ident, page in prepared["pages"].items():
        items = [s for s in selected if s["page_id"] == ident]
        rows = [r for r in decisions if r["page_id"] == ident]
        failed = any(r["status"] not in admission.CHOICES for r in rows)
        choices = {
            r["candidate_id"]: r["status"] if r["status"] in admission.CHOICES and not failed else None for r in rows
        }
        applied = admission.apply(page["source"], [s["candidate"] for s in items], choices)
        state = applied["state"]
        result = {
            "id": ident,
            "status": "error" if failed else "ok",
            "source": page["source"],
            "state": state,
            "tables": state["tables"],
            "unresolved_ids": state["unresolved_ids"],
            "admission_receipts": applied["admission_receipts"],
            "decision_results": rows,
            "decision_status": "failed_closed" if failed else "evaluated" if rows else "no_candidate",
            "source_conserved": True,
            "baseline_credit": False,
            "model": config["model"],
            "pure_model": True,
            "predicted_table_count": len(state["tables"]),
        }
        if (
            read(directory / f"{ident}-result.json") != result
            or read(directory / f"{ident}-state.json") != state
            or read(directory / f"{ident}-structure.json") != state["tables"]
            or (directory / f"{ident}.md").read_bytes() != runner.markdown(page["source"], state).encode()
        ):
            raise ValueError("Admission page differs from exact source-conserving no-fallback assembly")
        expected_results.append(result)
        verified[ident] = {"operational": not failed, "conserved": True}
    if (
        expected_results != report["results"]
        or report["decision_status_counts"] != dict(Counter(r["status"] for r in decisions))
        or report["page_status_counts"] != dict(Counter(r["status"] for r in expected_results))
    ):
        raise ValueError("Admission report outcome counts differ from replay")
    for key, value in {
        "model_fallbacks": 0,
        "retries": 0,
        "baseline_credit": False,
        "references_read": False,
        "intended_page_count": len(records),
        "valid_completed_page_count": sum(v["operational"] for v in verified.values()),
    }.items():
        if report.get(key) != value:
            raise ValueError("Admission scope/completion claims differ from replay")
    return {
        "scope": "Historical source extraction only; excluded from incremental admission cost/quality",
        "source_baselines": frozen["baselines"],
        "pool_sha256": frozen["pool"]["frozen_sha256"],
    }, verified
