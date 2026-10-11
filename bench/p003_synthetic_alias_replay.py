"""Secondary offline exact catalog alias replay, preserving original strict outcomes."""

# ruff: noqa: EM101, TRY003, E501, TRY004
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_synthetic_relations_eval as evaluator
from bench import p003_synthetic_relations_run as runner
from bench.silver import guard_path, sha, write_json


def authority(path: Path, approved_sha256: str) -> dict[str, Any]:
    """Load only an independently approved exact model-ID attestation."""
    path = guard_path(path)
    if sha(path.read_bytes()) != approved_sha256:
        raise ValueError("Alias authority differs from independently approved SHA")
    value = evaluator.load(path)
    aliases = value.get("aliases")
    if value.get("schema") != 1 or not isinstance(aliases, dict) or not aliases:
        raise ValueError("Explicit schema1 alias map required")
    for requested, returned in aliases.items():
        if (
            not isinstance(requested, str) or not requested
            or not isinstance(returned, list) or not returned
            or any(not isinstance(name, str) or not name or any(c in name for c in "*?[]") for name in returned)
            or len(set(returned)) != len(returned)
        ):
            raise ValueError("Finite exact aliases required; wildcard matching is forbidden")
    return {"aliases": aliases, "sha256": approved_sha256, "provenance": value.get("provenance")}


def normalized_model(result: dict[str, Any], requested: str, attestation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Copy the raw envelope and change only an explicitly attested model field."""
    if not isinstance(result, dict):
        raise ValueError("Raw provider envelope must be an object")
    returned = result.get("model")
    approved = attestation["aliases"].get(requested, [])
    if "model" in result and returned != requested and returned not in approved:
        raise ValueError("Unrecognized exact alias or different requested-model fallback")
    normalized = deepcopy(result)
    if "model" in result:
        normalized["model"] = requested
    return normalized, {
        "raw_requested_model": requested,
        "raw_returned_model": returned,
        "mapped_alias": requested if "model" in result else None,
        "alias_changed": returned is not None and returned != requested,
        "alias_authority_sha256": attestation["sha256"],
    }


def replay(directory: Path, runtime_map: Path, context: dict[str, Any], alias_path: Path, alias_sha256: str) -> dict[str, Any]:
    """Authenticate original source/wire/accounting before secondary parser replay."""
    original = evaluator.verify_run(directory, runtime_map, context)
    attestation = authority(alias_path, alias_sha256)
    secondary = deepcopy(original)
    cfg = original["config"]
    changes = []
    for row, record in zip(secondary["rows"], context["records"], strict=True):
        if "response_sha256" not in row:
            continue
        path = guard_path(directory) / f"question-{row['index']}-response.json"
        if sha(path.read_bytes()) != row["response_sha256"]:
            raise ValueError("Raw response changed after original verification")
        response = evaluator.load(path)
        entry = response["entry"]
        if (
            response.get("replayed") is not False
            or entry.get("requested_model") != cfg["model"]
            or entry.get("tag") != row["tag"]
            or entry.get("request_sha256") != row["wire_encoded_sha256"]
        ):
            raise ValueError("Alias replay requires exact original fresh wire/model/tag receipt")
        normalized, receipt = normalized_model(response["result"], cfg["model"], attestation)
        body, _ = runner.rebuild_request(context["pool"], record, cfg)
        try:
            parsed = runner.parse_response(record, body, normalized, cfg)
        except (ValueError, KeyError, TypeError) as error:
            row.pop("receipt", None)
            row.update(status="malformed_response", secondary_parse_error=type(error).__name__)
        else:
            row.update(status="valid_abstention" if parsed["abstained"] else "valid_nonabstaining", receipt=parsed)
        changes.append({"index": row["index"], "id": row["id"], "original_status": original["rows"][row["index"]]["status"], "secondary_status": row["status"], **receipt})
    counts = dict(Counter(row["status"] for row in secondary["rows"]))
    secondary["status_counts"] = counts
    wall = original["reported_metrics"]["wall_seconds"]
    effective = original["charges"]["effective_usd"]
    decisive = counts.get("valid_nonabstaining", 0)
    secondary["rates"]["valid_nonabstaining_questions_per_minute"] = decisive / wall * 60 if wall else None
    secondary["rates"]["valid_nonabstaining_questions_per_dollar"] = decisive / effective if effective else None
    secondary.update(
        scope="Secondary offline catalog-alias protocol replay; original strict outcomes preserved",
        alias_authority_sha256=alias_sha256,
        alias_receipts=changes,
        new_api_calls=0,
        original_outcomes_changed=False,
        rate_scope="Original hosted operational duration/cost; secondary replay is not fresh inference throughput",
    )
    return {"original_verified": original, "secondary_verified": secondary, "new_api_calls": 0}


def main() -> None:
    """Evaluate explicit source/run/alias authorities; open gold after replay only."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("directory", "runtime-map", "source", "source-map", "aliases", "gold", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--alias-sha256", required=True)
    parser.add_argument("--gold-sha256", required=True)
    args = parser.parse_args()
    output = guard_path(args.output)
    if output.exists():
        raise ValueError("New secondary output required; retained artifacts cannot be overwritten")
    context = evaluator.source_context(args.source, args.source_map)
    result = replay(args.directory, args.runtime_map, context, args.aliases, args.alias_sha256)
    gold = evaluator.load_gold(args.gold, args.gold_sha256, context)
    result["original_scores"] = evaluator.score(result["original_verified"], gold, context)
    result["secondary_scores"] = evaluator.score(result["secondary_verified"], gold, context)
    write_json(output, result)


if __name__ == "__main__":
    main()
