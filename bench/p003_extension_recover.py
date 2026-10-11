"""Recover interrupted extension decisions from authenticated retained receipts only."""

# ruff: noqa: EM101, TRY003, C901, PLR0912
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from bench import extension_protocol as protocol
from bench.p003_extension_run import ROOT, read
from bench.p003_gate_run import charges
from bench.silver import canonical, sha, write_json


def recover(directory: Path, ledger_directory: Path) -> dict[str, Any]:
    """Create a separate recovery report; never transmit or rewrite historical data."""
    destination = directory / "recovered-report-v1.json"
    if destination.exists() or (directory / "report.json").exists():
        raise FileExistsError("Existing complete or recovered report must be preserved")
    frozen = read(directory / "frozen.json")
    for name, digest in frozen["code_sha256"].items():
        if Path(name).name != name or sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived code changed")
    # Parsing uses the identical authenticated pure protocol, never executes archives.
    for name in ("extension_protocol.py", "extension_registry.py", "decision_oplog_run.py", "pipeline_repair.py"):
        if sha(Path(__file__).with_name(name).read_bytes()) != frozen["code_sha256"][name]:
            raise ValueError("Recovery protocol differs from archived runtime")
    prefix = "P003/" + frozen["config"]["run_id"] + "/"
    ledger = read(ledger_directory / "ledger.json")
    entries = [r for r in ledger["requests"] if r.get("tag", "").startswith(prefix)]
    expected = {r["id"] for r in frozen["pages"]}
    by_id = {}
    for entry in entries:
        ident = entry["tag"][len(prefix) :]
        if ident not in expected or ident in by_id:
            raise ValueError("Recovery requires one exact attempt per intended page")
        if entry.get("concurrent_state") == "in_flight":
            raise ValueError("In-flight request must settle before read-only recovery")
        by_id[ident] = entry
    results = []
    for row in frozen["pages"]:
        path = directory / "pages" / (row["id"] + ".json")
        if sha(path.read_bytes()) != row["sha256"]:
            raise ValueError("Frozen source packet changed")
        page = read(path)
        result = {
            "id": row["id"],
            "baseline_state": page["baseline_state"],
            "selected_state": None,
            "status": "not_attempted",
            "error": "Coordinator/worker interrupted; no new request",
        }
        entry = by_id.get(row["id"])
        if page["preparation_status"] != "ready":
            result.update(status="preparation_error", error=page["error"])
        elif entry is not None:
            request_path = ledger_directory / f"request-{entry['index']:03d}.json"
            if sha(request_path.read_bytes()) != entry["request_sha256"]:
                raise ValueError("Retained request does not match ledger")
            if canonical(read(request_path)) != canonical(page["packet"]["body"]):
                raise ValueError("Paid request differs from frozen page body")
            result["entry"] = entry
            if entry.get("error") or not entry.get("response_file"):
                result.update(status="transport_error", error=entry.get("error", "No settled response"))
            else:
                response_path = ledger_directory / entry["response_file"]
                raw = read(response_path)
                result.update(usage=raw.get("usage", {}), response_sha256=sha(response_path.read_bytes()))
                try:
                    parsed = protocol.parse_choice(raw, page["packet"])
                    result.update(parsed, status="abstained" if parsed["abstained"] else "selected")
                    result.pop("error", None)
                except (ValueError, TypeError, KeyError) as error:
                    result.update(status="invalid", error=type(error).__name__ + ": " + str(error))
        results.append(result)
    accounting = charges(entries)
    accounting["cost_scope"] = "All original interrupted-arm attempts; recovery makes zero network calls"
    effective = accounting["effective_usd"]
    report = {
        "version": 1,
        "config": frozen["config"],
        "results": results,
        "costs": accounting,
        "intended_pages": len(results),
        "selected_pages": sum(r["status"] == "selected" for r in results),
        "resources": {
            "wall_seconds": None,
            "cpu_seconds": None,
            "peak_sampled_rss_bytes": None,
            "measurement": "Interrupted process did not finalize resource metrics; unmeasured",
            "hosted_gpu": "unmeasured",
            "local_gpu_used": False,
        },
        "rates": {
            "intended_pages_per_minute": None,
            "selected_pages_per_minute": None,
            "intended_pages_per_dollar": len(results) / effective if effective else None,
        },
        "preparation_resources": frozen["resources"],
        "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "recovery": {
            "at": time.time(),
            "new_requests": 0,
            "original_complete_report_missing": True,
            "scope": "Exact stored request and native result replay; no archived Python execution",
        },
    }
    write_json(destination, report)
    return report


def main() -> None:
    """Perform local replay of a specifically identified interrupted arm."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    report = recover(args.directory, ROOT / "bench/results/pdf-master-artifacts/decisions")
    print({"intended": report["intended_pages"], "selected": report["selected_pages"], "new_requests": 0})


if __name__ == "__main__":
    main()
