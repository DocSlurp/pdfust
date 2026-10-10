"""Reconcile explicit P003 BYOK responses without rewriting frozen run reports."""

from __future__ import annotations

import argparse
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.decision_hosted import checkpoint, exclusive_lock
from bench.reprice_model_rates import request_cost
from bench.silver import guard_path, sha, write_json

FIELDS = ("accounted_usd", "cost_status", "provider_reported_usd")
ACCOUNTING_TOLERANCE = 1e-10


def reconcile(run: Path, ledger_path: Path, output: Path) -> dict[str, Any]:
    """Resolve only evidenced upstream amounts under the shared accounting lock."""
    run, ledger_path, output = (guard_path(path) for path in (run, ledger_path, output))
    report_bytes = (run / "report.json").read_bytes()
    report = json.loads(report_bytes)
    config = report["config"]
    if config.get("campaign") != "P003" or config.get("run_id") != run.name:
        message = "Reconciliation requires an explicit P003 run identity"
        raise ValueError(message)
    output.mkdir(parents=True, exist_ok=False)
    prefix = f"P003/{run.name}/"
    sidecar: dict[str, Any] = {
        "schema": 1, "original_report_sha256": sha(report_bytes), "run_tag_prefix": prefix,
        "entries": [], "code_sha256": sha(Path(__file__).read_bytes()),
    }
    with exclusive_lock(ledger_path.parent / "ledger.lock"):
        ledger = json.loads(ledger_path.read_bytes())
        entries = [entry for entry in ledger["requests"] if entry.get("tag", "").startswith(prefix)]
        if len(entries) != report["ledger_attempts"] or len({entry["index"] for entry in entries}) != len(entries):
            message = "Run request inventory differs from frozen report"
            raise ValueError(message)
        original_total = sum(entry["accounted_usd"] for entry in entries)
        if abs(original_total - report["accounted_usd"]) > ACCOUNTING_TOLERANCE:
            message = "Accounting already changed; investigate rather than overwrite original history"
            raise ValueError(message)
        for entry in entries:
            original = {key: deepcopy(entry[key]) for key in FIELDS if key in entry}
            request_name = f"request-{entry['index']:03d}.json"
            request_bytes = guard_path(ledger_path.parent / request_name).read_bytes()
            if sha(request_bytes) != entry["request_sha256"]:
                message = "Original request bytes do not match the ledger"
                raise ValueError(message)
            (output / request_name).write_bytes(request_bytes)
            row: dict[str, Any] = {
                "ledger_index": entry["index"], "request_sha256": entry["request_sha256"],
                "request_path": request_name, "response_path": None, "response_sha256": None,
                "original_accounting": original, "reconciled_accounting": deepcopy(original),
            }
            response_name = entry.get("response_file")
            if response_name:
                if Path(response_name).name != response_name:
                    message = "Response artifact must be a direct filename"
                    raise ValueError(message)
                response_bytes = guard_path(ledger_path.parent / response_name).read_bytes()
                response = json.loads(response_bytes)
                (output / response_name).write_bytes(response_bytes)
                row.update(response_path=response_name, response_sha256=sha(response_bytes))
                quote = request_cost(entry, response.get("usage", {}), {})
                if quote.get("upstream_inference_usd") is not None and quote["effective_usd"] is not None:
                    reconciled = {
                        **original, "accounted_usd": quote["effective_usd"], "effective_usd": quote["effective_usd"],
                        "cost_status": quote["basis"], "gateway_reported_usd": quote["gateway_reported_usd"],
                        "upstream_reported_usd": quote["upstream_inference_usd"],
                    }
                    entry.setdefault("accounting_revisions", []).append({
                        "at": time.time(), "reason": "P003 retained BYOK upstream plus gateway reconciliation",
                        "original": original, "reconciled": deepcopy(reconciled),
                        "response_sha256": sha(response_bytes), "sidecar": str(output / "costs.json"),
                    })
                    entry.update(reconciled)
                    row["reconciled_accounting"] = reconciled
            sidecar["entries"].append(row)
        write_json(output / "costs.json", sidecar)
        checkpoint(ledger_path, ledger)
    return sidecar


def main() -> None:
    """Apply one explicitly named completed run's offline accounting correction."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sidecar = reconcile(args.run, args.ledger, args.output)
    print(json.dumps({"attempts": len(sidecar["entries"]), "sidecar": str(args.output / "costs.json")}))


if __name__ == "__main__":
    main()
