"""Offline coverage/size audit of frozen row evidence on an explicit DEV corpus."""

# Heterogeneous artifact summaries preserve missing pages and full source provenance.
# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from bench.pipeline_row_evidence import SPEC, build, encode
from bench.silver import guard_path, sha, write_json


def audit(run: Path, manifest_path: Path, evaluation_path: Path, output: Path) -> dict[str, Any]:
    """Build every source packet first; join fixed outcomes only for reporting."""
    began, cpu = time.perf_counter(), time.process_time()
    manifest = json.loads(guard_path(manifest_path).read_bytes())
    if manifest.get("split") != "DEV":
        raise ValueError("Only explicit DEV corpus sources are admitted")
    output.mkdir(parents=True, exist_ok=True)
    rows, examples = [], []
    example_cohorts = set()
    for record in manifest["pages"]:
        payload = guard_path(run / f"{record['id']}-result.json").read_bytes()
        retained = json.loads(payload)
        if retained["id"] != record["id"]:
            raise ValueError("Frozen source result ID mismatch")
        row: dict[str, Any] = {
            "id": record["id"],
            "cohort": record["cohort"],
            "family": record["family"],
            "input_sha256": sha(payload),
            "source_status": retained["status"],
        }
        source = retained.get("source")
        if source is None:
            row["status"] = "missing_source"
        else:
            try:
                packet = build(source)
                encoded = encode(packet)
                (output / f"{record['id']}-row-evidence.json").write_text(encoded)
                baseline = {
                    "page_size": packet["page_size"],
                    "viewport": packet["viewport"],
                    "word_fields": packet["word_fields"],
                    "words": packet["words"],
                }
                source_bytes = len(
                    json.dumps(baseline, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
                )
                count = len(packet["rows"])
                row.update(
                    status="ok",
                    words=len(packet["words"]),
                    rows=count,
                    tracks=len(packet["tracks"]["starts"]) + len(packet["tracks"]["ends"]),
                    source_bytes=source_bytes,
                    evidence_bytes=len(encoded.encode()),
                    evidence_sha256=sha(encoded.encode()),
                    em_proxy_available=packet["em_proxy"] is not None,
                    rows_with_gaps=sum(bool(r["gaps_em"]) for r in packet["rows"]),
                    rows_with_neighbors=sum(
                        r["adjacent"]["previous"] is not None or r["adjacent"]["following"] is not None
                        for r in packet["rows"]
                    ),
                )
                if count > 1 and record["cohort"] not in example_cohorts:
                    lookup = {word[0]: word[1] for word in packet["words"]}
                    examples.append(
                        {
                            "id": record["id"],
                            "cohort": record["cohort"],
                            "em_proxy": packet["em_proxy"],
                            "selection": "First available multi-row source page in manifest order "
                            "per cohort; no outcome selection",
                            "rows": [
                                {**r, "display_excerpt": [lookup[i] for i in r["source_ids"][:8]]}
                                for r in packet["rows"][:2]
                            ],
                        }
                    )
                    example_cohorts.add(record["cohort"])
            except ValueError as error:
                row.update(status="error", error=str(error)[:500])
        rows.append(row)
    evaluation = json.loads(guard_path(evaluation_path).read_bytes())
    scores = {row["id"]: row for row in evaluation["page_scores"]}
    if evaluation.get("dataset_sha256") != manifest["dataset_sha256"] or set(scores) != {row["id"] for row in rows}:
        raise ValueError("Fixed verified outcomes must cover the complete matching manifest")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        score = scores[row["id"]]
        row["stratum"] = (
            "negative" if score.get("negative_page") else "positive" if score.get("positive_page") else "unscored"
        )
        groups[f"{row['stratum']}/{row['family']}"].append(row)
    summaries = {}
    for key, pages in sorted(groups.items()):
        available = [page for page in pages if page["status"] == "ok"]
        summaries[key] = {
            "pages": len(pages),
            "source_packets": len(available),
            **{
                f"median_{field}": median([page[field] for page in available]) if available else None
                for field in ("words", "rows", "tracks", "source_bytes", "evidence_bytes")
            },
        }
    result = {
        "feature_spec": SPEC,
        "manifest_sha256": sha(manifest_path.read_bytes()),
        "evaluation_sha256": sha(evaluation_path.read_bytes()),
        "pages": rows,
        "groups": summaries,
        "examples": examples,
        "metrics": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": "Single CPU Python process, no subprocesses; "
            "Linux getrusage high-water RSS; utilization unsampled",
        },
    }
    write_json(output / "audit.json", result)
    return result


def main() -> None:
    """Require named inputs; no corpus discovery or provider calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.manifest, args.evaluation, args.output)
    print(json.dumps({"pages": len(result["pages"]), "metrics": result["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
