"""Source-first R001 replay and conditional body-record content diagnostics."""

# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR0912
from __future__ import annotations

import argparse
import base64
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

VERSION = "p003-r001-body-content-v1"
EXPECTED_RECORDS = 80
HISTORICAL_FILES = (
    "decision_row_run.py",
    "decision_rows.py",
    "decision_context_cases.py",
    "decision_image_matrix.py",
    "decision_records.py",
    "reprice_model_rates.py",
)
CODE_FILES = (
    "p003_row_content_audit.py",
    "decision_rows.py",
    "decision_records.py",
    "decision_image_matrix.py",
    "p003_content_alignment.py",
    "p003_synthetic_alias_replay.py",
)


def _json(path: Path) -> dict[str, Any]:
    from bench.silver import guard_path

    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("JSON object required")
    return value


def body_table(spec: dict[str, Any], assembly: dict[str, Any]) -> dict[str, Any] | None:
    """Project literal record fields only; fixed headers and unresolved words earn no credit."""
    from bench.decision_rows import project_input

    source = project_input(spec)
    if [column["role"] for column in source["columns"]] != ["row_key", "value"]:
        raise ValueError("Only the original two-field R001 body is supported")
    words = {word["id"]: word["text"] for word in source["words"]}
    headers = [i for h in source["headers"] for i in h["source_ids"]]
    cell_ids = [i for cell in assembly["cells"] for i in cell["source_ids"]]
    if Counter(cell_ids + assembly["unresolved_ids"]) != Counter(list(words)):
        raise ValueError("Complete exact source conservation required")
    rows, assigned = [], []
    for record in assembly["records"]:
        if record.get("unit_ids", []):
            raise ValueError("Unit fields are outside the two-field projection")
        row = []
        for key in ("row_key_ids", "value_ids"):
            ids = record[key]
            if not isinstance(ids, list) or any(i not in words or i in headers for i in ids):
                raise ValueError("Record source identity invalid")
            assigned.extend(ids)
            row.append(" ".join(words[i] for i in ids))
        rows.append(row)
    if Counter(assigned) != Counter(i for i in cell_ids if i not in headers):
        raise ValueError("Body records duplicate or omit assigned source IDs")
    return {"row_count": len(rows), "col_count": 2, "values": rows, "spans": []} if rows else None


def compare_body(reference: dict[str, Any], prediction: dict[str, Any] | None) -> dict[str, Any]:
    """Missing whole records retain full omission counts instead of invalid empty matrices."""
    from bench.p003_content_alignment import compare_content

    if prediction is not None:
        return compare_content(reference, prediction)
    units = sum(
        len(" ".join(unicodedata.normalize("NFC", value).split())) for row in reference["values"] for value in row
    )
    return {
        "version": "p003-content-alignment-v2",
        "supported": True,
        "unsupported_reason": None,
        "counts": {
            "matched": 0,
            "substituted": 0,
            "missing": units,
            "extra": 0,
            "reference_units": units,
            "prediction_units": 0,
        },
        "content_precision": 0.0,
        "content_recall": 0.0,
        "content_recovered_with_row_order": False,
        "schema_correctness": None,
        "scope": "Entire known body omitted; no empty-table structure claim",
    }


def prepare(
    directory: Path, historical_authority: Path, aliases: Path, alias_sha256: str, output: Path
) -> dict[str, Any]:
    """Freeze source packets, exact wires/pixels/raw receipts and body outputs without target interpretation."""
    from bench import decision_rows as rows
    from bench.p003_synthetic_alias_replay import authority, normalized_model
    from bench.silver import guard_path, sha, write_json

    directory = guard_path(directory)
    if output.exists():
        raise FileExistsError("Fresh preparation output required")
    manifest = _json(directory / "manifest.json")
    authority_file = _json(historical_authority)
    history = {Path(k).name: v for k, v in authority_file["code_sha256"].items()}
    if sha((directory / "manifest.json").read_bytes()) != authority_file["manifest_sha256"]:
        raise ValueError("Root-pinned historical manifest differs")
    frozen_code = {Path(k).name: v for k, v in manifest["code_sha256"].items()}
    if {name: history.get(name) for name in HISTORICAL_FILES} != frozen_code:
        raise ValueError("External historical Git authority differs")
    for name in ("decision_rows.py", "decision_records.py", "decision_image_matrix.py"):
        if sha(Path(__file__).with_name(name).read_bytes()) != history[name]:
            raise ValueError("Executed parser/source helper differs from historical authority")
    if manifest["experiment"] != "R001" or manifest["scope"] != "page" or len(manifest["records"]) != EXPECTED_RECORDS:
        raise ValueError("Exact completed page-scope R00180 required")
    report = _json(directory / "results.json")

    def identity(r: dict[str, Any]) -> tuple[str, str, int]:
        return r["model"], r["arm"], r["case_index"]

    frozen = {identity(r): r for r in manifest["records"]}
    observed = {identity(r): r for r in report["records"]}
    if len(frozen) != EXPECTED_RECORDS or len(observed) != EXPECTED_RECORDS or set(frozen) != set(observed):
        raise ValueError("Complete unique eighty-record inventory required")
    attestation = authority(aliases, alias_sha256)
    inventory, records, ledger = {}, [], {}
    for name in ("manifest.json", "results.json"):
        path = directory / name
        inventory[str(path)] = sha(path.read_bytes())
    for declaration in manifest["records"]:
        row = observed[identity(declaration)]
        if row["status"] != "ok" or any(row.get(k) != v for k, v in declaration.items()):
            raise ValueError("Original R001 successful declaration differs")
        request_path = directory / declaration["request_file"]
        if request_path.parent != directory or sha(request_path.read_bytes()) != declaration["request_sha256"]:
            raise ValueError("Actual transmitted request changed")
        body = _json(request_path)
        state = body["state"]
        spec = state if isinstance(state, dict) else json.JSONDecoder().raw_decode(state[0])[0]
        spec = rows.project_input(spec)
        image = None
        if declaration["image"] is not None:
            metadata = declaration["image"]
            path = guard_path(Path(__file__).resolve().parents[1] / metadata["path"])
            data = path.read_bytes()
            if sha(data) != metadata["sha256"]:
                raise ValueError("Retained exact image changed")
            import io

            from PIL import Image

            with Image.open(io.BytesIO(data)) as pixels:
                if list(pixels.size) != metadata["pixels"]:
                    raise ValueError("Actual pixel dimensions differ")
            if base64.b64decode(state[1]["image_url"]["url"].split(",", 1)[1], validate=True) != data:
                raise ValueError("Wire image differs from retained pixels")
            image = {**metadata, "data": data}
            inventory[str(path)] = sha(data)
        rebuilt = rows.build_request(spec, declaration["model"], image)
        if json.dumps(rebuilt, separators=(",", ":")).encode() != request_path.read_bytes():
            raise ValueError("Source-only native request does not reconstruct exactly")
        entry = row["entry"]
        if entry["request_sha256"] != declaration["request_sha256"] or entry["requested_model"] != declaration["model"]:
            raise ValueError("Retained financial identity differs")
        if entry["tag"] != f"R001/{declaration['model']}/{declaration['arm']}/{declaration['case_id']}":
            raise ValueError("Historical request tag differs")
        response_name = entry["response_file"]
        if Path(response_name).name != response_name or response_name != f"response-{entry['index']}.json":
            raise ValueError("Only the exact receipt-referenced response admitted")
        raw_path = directory.parent / response_name
        raw = _json(raw_path)
        if raw.get("model") != entry.get("served_model"):
            raise ValueError("Raw returned model differs from retained provider identity")
        normalized, _ = normalized_model(raw, declaration["model"], attestation)
        assignments = rows.parse_response(spec, normalized)
        assembly = rows.materialize_assignments(spec, assignments)
        if assembly != row["score"]["assembly"] or assignments != row["score"]["assignments"]:
            raise ValueError("Pure source-owned output differs from original assembly")
        index = entry["index"]
        if index in ledger and ledger[index] != declaration["request_sha256"]:
            raise ValueError("A shared raw receipt is attributed to different wires")
        ledger[index] = declaration["request_sha256"]
        inventory[str(request_path)] = sha(request_path.read_bytes())
        inventory[str(raw_path)] = sha(raw_path.read_bytes())
        records.append(
            {
                **declaration,
                "source_input": spec,
                "assignments": assignments,
                "assembly": assembly,
                "body_table": body_table(spec, assembly),
                "entry_index": index,
                "raw_response_path": str(raw_path),
                "raw_response_sha256": sha(raw_path.read_bytes()),
            }
        )
    output = guard_path(output)
    output.mkdir(parents=True)
    write_json(output / "source-output.json", {"records": records})
    result = {
        "version": VERSION,
        "directory": str(directory),
        "manifest_sha256": inventory[str(directory / "manifest.json")],
        "historical_authority": str(historical_authority),
        "historical_authority_sha256": sha(historical_authority.read_bytes()),
        "aliases": str(aliases),
        "alias_sha256": alias_sha256,
        "artifact_sha256": inventory,
        "source_output_sha256": sha((output / "source-output.json").read_bytes()),
        "code_sha256": {name: sha(Path(__file__).with_name(name).read_bytes()) for name in CODE_FILES},
        "records": 80,
        "arms": 8,
        "unique_receipts": len(ledger),
        "shared_replay_duplicates": 80 - len(ledger),
        "reference_interpretation": False,
        "new_api_calls": 0,
        "source_scope": "Retained exact request source and encoded pixels; original PDF not retained/re-rendered",
        "projection": "Literal row_key/value records only; fixed headers excluded; author-unresolved cases unscorable",
    }
    write_json(output / "frozen.json", result)
    return result


def main() -> None:
    """Prepare only; target interpretation is a separately approved evaluation step."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--historical-authority", required=True, type=Path)
    parser.add_argument("--aliases", required=True, type=Path)
    parser.add_argument("--alias-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.directory, args.historical_authority, args.aliases, args.alias_sha256, args.output)


if __name__ == "__main__":
    main()
