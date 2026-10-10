"""Offline optimistic complete-cell inventory bound; never inference evidence."""

# Frozen evaluation dictionaries have heterogeneous schemas.
# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.generalization_scoring import MAX_TABLES, _cells

EXPECTED_PAGES = 16

SPEC = {
    "version": 1,
    "normalization": "Authoritative NFC plus collapsed Unicode whitespace; preserve case and punctuation",
    "unit": "Complete anchor-cell string, excluding merged covered slots",
    "matching": "Page-wide multiset intersection across all admitted tables; consume each duplicate once",
    "ignored": ["table identity", "row", "column", "span dimensions", "geometry"],
    "empty": "Report normalized empty anchors and their intersection separately",
    "failure": "Non-ok predictions contribute zero anchors, including retained successful prefixes",
    "purpose": "Optimistic offline placement-free bound; never primary score, inference evidence or routing",
}


def inventory(tables: list[dict[str, Any]]) -> Counter[str]:
    """Count validated complete normalized anchors without splitting or joining text."""
    if len(tables) > MAX_TABLES:
        raise ValueError("Too many tables")
    return Counter(value for table in tables for value in _cells(table).values())


def compare(target: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    """Consume page-wide duplicate strings once; retain separate empty-anchor counts."""
    expected = inventory(target.get("tables", []))
    admitted = prediction.get("status") == "ok"
    actual = inventory(prediction.get("tables", [])) if admitted else Counter()
    matches = expected & actual
    return {
        "id": target["id"],
        "admitted": admitted,
        "expected_nonempty": sum(expected.values()) - expected[""],
        "predicted_nonempty": sum(actual.values()) - actual[""],
        "matched_nonempty": sum(matches.values()) - matches[""],
        "expected_empty": expected[""],
        "predicted_empty": actual[""],
        "matched_empty": matches[""],
        "optimistic_total": sum(matches.values()),
    }


def audit(artifact_root: str | Path, output: str | Path) -> dict[str, Any]:  # noqa: C901
    """Audit four fixed retained controls; preserve all intended pages and hashes."""
    from bench.silver import guard_path  # noqa: PLC0415

    root, destination = Path(artifact_root), Path(output)
    started, cpu = time.perf_counter(), time.process_time()
    inputs: dict[str, str] = {}

    def load(path: Path) -> dict[str, Any]:
        payload = guard_path(path).read_bytes()
        inputs[str(path)] = hashlib.sha256(payload).hexdigest()
        return json.loads(payload)

    corpus = root / "screens/natural16"
    manifest = load(corpus / "manifest.json")
    targets = load(corpus / "private-targets.json")
    if manifest["split"] != "DEV" or targets["dataset_sha256"] != manifest["dataset_sha256"]:
        raise ValueError("Requires the matched explicit DEV screen")
    ids = [page["id"] for page in manifest["pages"]]
    gold = {page["id"]: page for page in targets["pages"]}
    if len(ids) != EXPECTED_PAGES or set(ids) != set(gold):
        raise ValueError("Requires all sixteen intended pages")
    # Fixed density strata are reporting only, never inference or metric rules.
    dense = {"p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"}
    controls = [
        "natural16-vision-crops-sonnet-1024",
        "natural16-vision-crops-haiku-1024",
        "natural16-vision-sonnet-2048-q50",
        "natural16-vision-opus-2048-q50",
    ]
    runs = []
    for name in controls:
        report_path = root / name / "report.json"
        report = load(report_path)
        evaluated = load(root / name / "verified-evaluation.json")
        if evaluated["report_sha256"] != inputs[str(report_path)]:
            raise ValueError("Evaluation does not attest these exact report bytes")
        predicted = {page["id"]: page for page in report["results"]}
        primary = {page["id"]: page for page in evaluated["page_scores"]}
        if set(predicted) != set(ids) or set(primary) != set(ids):
            raise ValueError("Missing or extra retained page")
        pages = []
        for identifier in ids:
            prediction = predicted[identifier]
            # Independently verified failure status suppresses any retained prefix.
            if primary[identifier]["error"]:
                prediction = {"status": "error", "tables": []}
            row = compare(gold[identifier], prediction)
            row["primary_exact_cells"] = primary[identifier]["correct_text_cells"]
            row["stratum"] = "dense2" if identifier in dense else "remaining14"
            if row["optimistic_total"] < row["primary_exact_cells"]:
                raise ValueError("Inventory bound fell below primary exact cells")
            pages.append(row)
        groups = {}
        for group in ("all16", "dense2", "remaining14"):
            selected = pages if group == "all16" else [row for row in pages if row["stratum"] == group]
            counts = {
                key: sum(row[key] for row in selected) for key in pages[0] if key not in {"id", "admitted", "stratum"}
            }
            groups[group] = {"pages": len(selected), "admitted": sum(row["admitted"] for row in selected), **counts}
        runs.append({"name": name, "groups": groups, "pages": pages})
    # Detect any mutation during this read-only audit.
    for path, digest in inputs.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError("Input changed during audit")
    result = {
        "spec": SPEC,
        "dataset_sha256": manifest["dataset_sha256"],
        "inputs_sha256": inputs,
        "runs": runs,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": ("Audit CPU/wall excludes imports; lifetime kernel peak RSS includes imports; "
                      "one CPU process, no sampling"),
        },
    }
    guard_path(destination).parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main() -> None:
    """Run the isolated retained-control audit without any provider client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.artifact_root, args.output)
    print(
        json.dumps(
            {
                "runs": [{"name": run["name"], "groups": run["groups"]} for run in result["runs"]],
                "resources": result["resources"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
