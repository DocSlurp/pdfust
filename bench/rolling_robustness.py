"""Score corrected v2 DEV topology variations against frozen A001 rules.

The cue-bearing v1 inputs and historical scores remain immutable and quarantined.
Ambiguous v2 pages have no binary admission or exact-structure score.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.borderless_challenge import score
from bench.rolling_rows import assemble
from bench.silver import sha, write_json
from bench.silver_realism import DESIGN as DESIGN  # noqa: PLC0414 - retain the public generator import
from bench.silver_realism import freeze, generate_cases
from bench.silver_structure import process_peak_rss


def exact_source_ownership(
    target: dict[str, Any], source: dict[str, Any], candidate: dict[str, Any] | None
) -> dict[str, Any]:
    """Map uniquely authored placement lines to extracted words after source/candidates are frozen."""
    intended: dict[tuple[int, int], list[str]] = {}
    unmapped = []
    for word in source["words"]:
        matches = [
            slot
            for slot in target["authored_slots"]
            if abs(word["bbox"][1] - (slot["baseline"] - slot["size"] * 0.8)) < slot["size"] * 0.25
            and slot["x"] - 0.1 <= word["bbox"][0] <= slot["x"] + len(slot["text"]) * slot["size"]
            and word["text"] in slot["text"].split()
        ]
        if len(matches) == 1:
            key = (matches[0]["row"], matches[0]["column"])
            intended.setdefault(key, []).append(word["id"])
        elif matches:
            unmapped.append(word["id"])
    actual = (
        {
            (i // candidate["col_count"], i % candidate["col_count"]): cell["source_ids"]
            for i, cell in enumerate(candidate["cells"])
        }
        if candidate
        else {}
    )
    correct = sum(set(ids) == set(actual.get(slot, [])) for slot, ids in intended.items())
    owned = sum(len(set(ids) & set(actual.get(slot, []))) for slot, ids in intended.items())
    return {
        "intended_word_ids": sum(len(ids) for ids in intended.values()),
        "correct_slot_word_ids": owned,
        "intended_nonempty_slots": len(intended),
        "exact_nonempty_slots": correct,
        "ambiguous_mapping_word_ids": unmapped,
        "source_slot_exact": bool(intended) and correct == len(intended) and not unmapped,
    }


def run(directory: Path) -> dict[str, Any]:
    """Freeze authored inputs first, then extract source, freeze candidates, and score separately."""
    output = freeze(directory)
    manifest = json.loads((output / "manifest.json").read_text())
    identity = manifest["dataset_sha256"]
    assembler_hash = sha(Path(__file__).with_name("rolling_rows.py").read_bytes())
    cases = generate_cases()
    sources = json.loads((output / "source-evidence.json").read_text())["pages"]
    # The input/source freeze is complete before any assembler or scorer runs.
    start, cpu = time.perf_counter(), time.process_time()
    frozen_pages = [
        {"id": source["id"], "alternatives": [assemble(source, variant) for variant in ("physical", "rolling")]}
        for source in sources
    ]
    source_bytes = (output / "source-evidence.json").read_bytes()
    candidate_payload = {
        "schema": 1,
        "source_sha256": sha(source_bytes),
        "pages": frozen_pages,
        "rules_source_sha256": assembler_hash,
    }
    write_json(output / "candidates-frozen.json", candidate_payload)
    # Scoring starts after all PDF/source/candidate bytes have been retained.
    results = []
    for case, source, frozen in zip(cases, sources, frozen_pages, strict=True):
        if not case["target"]["binary_admission_eligible"]:
            results.append(
                {
                    "id": case["id"],
                    "kind": "ambiguous",
                    "route": "unscored",
                    "truth_status": "ambiguous-unscored",
                    "scores": None,
                }
            )
            continue
        native_tables = source["vector_candidates"] + source["text_candidates"]
        native_best = max(
            [score(case["target"], [t]) for t in native_tables],
            key=lambda s: (s["exact_cells"], s["owned_values"], s["owned_words"]),
            default=score(case["target"], []),
        )
        results.append(
            {"id": case["id"], "route": "native-ceiling", "kind": case["target"]["kind"], "scores": native_best}
        )
        for alternative in frozen["alternatives"]:
            tables = alternative["candidates"]
            owned = [i for t in tables for cell in t["cells"] for i in cell["source_ids"]]
            conserved = Counter(owned + alternative["unresolved_ids"]) == Counter(w["id"] for w in source["words"])
            results.append(
                {
                    "id": case["id"],
                    "route": alternative["variant"],
                    "kind": case["target"]["kind"],
                    "scores": score(case["target"], tables),
                    "source_conservation": conserved,
                    "ownership": exact_source_ownership(case["target"], source, tables[0] if tables else None),
                }
            )
    rss, tool = process_peak_rss()
    summary = {
        "dataset_sha256": identity,
        "corpus": str(output),
        "pages": len(cases),
        "unscored_ambiguous_pages": sum(not c["target"]["binary_admission_eligible"] for c in cases),
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"perf_counter/process_time; {tool}; sequential CPU; lifetime RSS; no sampling",
        "routes": {
            route: {
                kind: {
                    "pages": sum(r["route"] == route and r["kind"] == kind for r in results),
                    **{
                        key: sum(r["scores"][key] for r in results if r["route"] == route and r["kind"] == kind)
                        for key in (
                            "exact_page",
                            "exact_cells",
                            "exact_spans",
                            "owned_values",
                            "owned_words",
                            "false_positive_page",
                        )
                    },
                }
                for kind in ("borderless", "prose")
            }
            for route in ("native-ceiling", "physical", "rolling")
        },
    }
    write_json(output / "private-scores.json", {"rows": results})
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    """Build and score the declared CPU DEV check, with no hosted client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))


if __name__ == "__main__":
    main()
