"""Offline optimistic source-token ceilings for fixed natural table annotations."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import json
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.generalization_report import load_corpus
from bench.generalization_scoring import _cells, normalize_text
from bench.silver import guard_path, sha

DENSE_IDS = {"p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"}


def relaxed_text(text: str) -> str:
    """Remove Unicode whitespace after canonical decomposition, preserving case."""
    return "".join(unicodedata.normalize("NFD", text).split())


class Inventory:
    """Index whole tokens for arbitrary-order, unlimited-reuse segmentation."""

    def __init__(self, texts: list[str], *, relaxed: bool = False) -> None:
        """Normalize each whole token using the selected matching policy."""
        self.relaxed = relaxed
        normalize = relaxed_text if relaxed else normalize_text
        self.tokens: dict[str, set[str]] = defaultdict(set)
        for text in texts:
            token = normalize(text)
            if token:
                self.tokens[token[0]].add(token)

    def possible(self, value: str) -> bool:
        """Return necessary text feasibility, ignoring geometry and exclusive IDs."""
        target = relaxed_text(value) if self.relaxed else normalize_text(value)
        if not target:
            return True  # Empty source_ids is admitted for an empty anchor.
        reachable = {0}
        for start in range(len(target)):
            if start not in reachable:
                continue
            for token in self.tokens.get(target[start], ()):
                if target.startswith(token, start):
                    end = start + len(token)
                    if end == len(target):
                        return True
                    if self.relaxed:
                        reachable.add(end)
                    elif target[end] == " ":
                        reachable.add(end + 1)
        return False


def _totals(pages: list[dict[str, Any]]) -> dict[str, int]:
    fields = (
        "pages",
        "measured_pages",
        "expected_tables",
        "expected_cells",
        "empty_cells",
        "unmeasured_cells",
        "unmeasured_tables",
        "possible_cells",
        "possible_tables",
        "relaxed_possible_cells",
        "relaxed_possible_tables",
    )
    result = {field: sum(page.get(field, 0) for page in pages) for field in fields}
    result["optimistic_upper_cells"] = result["possible_cells"] + result["unmeasured_cells"]
    result["optimistic_upper_tables"] = result["possible_tables"] + result["unmeasured_tables"]
    return result


def evaluate(targets: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure all annotated anchors against complete retained page inventories."""
    by_id = {prediction["id"]: prediction for prediction in predictions}
    if len(by_id) != len(predictions):
        raise ValueError("Duplicate retained page inventory")
    pages = []
    for target in targets:
        tables = [_cells(table) for table in target.get("tables", [])]
        values = [value for table in tables for value in table.values()]
        source = by_id.get(target["id"], {}).get("source")
        measured = isinstance(source, dict) and isinstance(source.get("words"), list)
        page: dict[str, Any] = {
            "id": target["id"],
            "pages": 1,
            "measured_pages": int(measured),
            "expected_tables": len(tables),
            "expected_cells": len(values),
            "empty_cells": sum(not value for value in values),
            "unmeasured_cells": 0 if measured else len(values),
            "unmeasured_tables": 0 if measured else len(tables),
        }
        if measured and isinstance(source, dict):
            texts = [word["text"] for word in source["words"]]
            if any(not isinstance(text, str) for text in texts):
                raise ValueError("Inventory contains nonliteral source text")
            strict, relaxed = Inventory(texts), Inventory(texts, relaxed=True)
            for prefix, inventory in (("", strict), ("relaxed_", relaxed)):
                feasible = [[inventory.possible(value) for value in table.values()] for table in tables]
                page[prefix + "possible_cells"] = sum(sum(table) for table in feasible)
                page[prefix + "possible_tables"] = sum(all(table) for table in feasible)
            page["source_words"] = len(texts)
        pages.append(page)
    return {
        "totals": _totals(pages),
        "pages": pages,
        "posthoc_density": {
            "two_dense_newspapers": _totals([page for page in pages if page["id"] in DENSE_IDS]),
            "remaining_fourteen": _totals([page for page in pages if page["id"] not in DENSE_IDS]),
        },
        "semantics": {
            "strict": "NFC and Unicode whitespace normalization of literal ASCII-space joins of whole source tokens",
            "relaxed": "NFD canonical decomposition and all Unicode whitespace removed before segmentation",
            "relaxations": "Arbitrary whole-page token order and unlimited reuse; geometry, region bounds, "
            "ID uniqueness, "
            "slot admissions, topology and simultaneous cell ownership ignored",
            "interpretation": "Strict impossible cells cannot be exact under the source-ID literal join parser. "
            "Possible cells and tables are optimistic necessary bounds, not achievable quality. "
            "Missing inventories are unmeasured, never impossible. Empty anchors are counted separately.",
        },
    }


def main() -> None:
    """Read only explicitly named frozen DEV corpus and retained run reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    began, cpu = time.perf_counter(), time.process_time()
    manifest, targets = load_corpus(args.corpus)
    results = []
    for run in args.run:
        report_path = guard_path(run / "report.json")
        frozen = json.loads(guard_path(run / "frozen.json").read_bytes())
        if frozen["manifest_sha256"] != sha(guard_path(args.corpus / "manifest.json").read_bytes()):
            raise ValueError("Inventory and annotation manifests differ")
        report = json.loads(report_path.read_bytes())
        for prediction in report["results"]:
            ident = prediction["id"]
            if not isinstance(ident, str) or Path(ident).name != ident or ident in {".", ".."}:
                raise ValueError("Unsafe retained page inventory ID")
            retained = json.loads(guard_path(run / f"{ident}-result.json").read_bytes())
            if retained != prediction:
                raise ValueError("Retained source inventory differs from its report")
        result = evaluate(targets["pages"], report["results"])
        result.update(name=run.name, report_sha256=sha(report_path.read_bytes()), config=report["config"])
        results.append(result)
    output = {
        "dataset_sha256": manifest["dataset_sha256"],
        "runs": results,
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "rss": "unmeasured",
            "measurement": "time.perf_counter/process_time; current process, corpus loading and all requested arms",
            "remote_requests": 0,
        },
    }
    guard_path(args.output).write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
