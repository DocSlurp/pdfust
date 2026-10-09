"""Group retained DEV document metadata offline, without opening PDFs or labels."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def checked_path(path: Path) -> Path:
    """Reject sealed locations, including symlink destinations, before file reads."""
    protected = {"heldout-silver", "silver-heldout-v1"}
    if protected.intersection(path.absolute().parts):
        msg = "Protected held-out paths are unavailable to DEV queries"
        raise ValueError(msg)
    resolved = path.resolve()
    if protected.intersection(resolved.parts):
        msg = "Protected held-out paths are unavailable to DEV queries"
        raise ValueError(msg)
    if resolved.name != "metadata.jsonl":
        msg = "Provide a DEV benchmark run's document metadata.jsonl"
        raise ValueError(msg)
    return resolved


def load_rows(path: Path) -> list[dict[str, Any]]:
    """Validate the complete export before aggregating any observations."""
    rows: list[dict[str, Any]] = []
    with checked_path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or row.get("split") != "DEV":
                msg = f"Row {number} is not explicitly DEV; refusing the complete export"
                raise ValueError(msg)
            rows.append(row)
    return rows


def values(rows: list[dict[str, Any]], section: str, key: str) -> list[float]:
    """Retain finite measured values; unavailable measurements stay absent."""
    result = []
    for row in rows:
        value = row.get(section, {}).get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            result.append(float(value))
    return result


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Report measurement denominators and literal-anchor counts, including errors."""
    cpu = values(rows, "resources", "cpu_ms")
    rss = values(rows, "resources", "peak_rss_bytes")
    cold = values(rows, "extraction", "cold_wall_ms")
    warm = values(rows, "extraction", "warm_wall_ms")
    anchors = [row["silver_anchor_score"] for row in rows if "silver_anchor_score" in row]
    found = sum(anchor["found"] for anchor in anchors)
    total = sum(anchor["total"] for anchor in anchors)
    return {
        "documents": len(rows),
        "completed": sum(row.get("status") == "ok" for row in rows),
        "metadata_error_documents": sum(bool(row.get("metadata", {}).get("errors")) for row in rows),
        "cpu_measured_documents": len(cpu),
        "worker_cpu_ms_sum": sum(cpu) if cpu else None,
        "rss_measured_documents": len(rss),
        "worker_peak_rss_mib_max": max(rss) / (1024 * 1024) if rss else None,
        "cold_measured_documents": len(cold),
        "cold_wall_ms_median": statistics.median(cold) if cold else None,
        "warm_measured_documents": len(warm),
        "warm_wall_ms_median": statistics.median(warm) if warm else None,
        "anchor_measured_documents": len(anchors),
        "literal_anchors_found": found,
        "literal_anchors_total": total,
        "literal_anchor_recall": found / total if total else None,
    }


def main() -> None:
    """Print JSON groups for family, authored encoding, and measured PDF version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path, help="DEV run's metadata.jsonl")
    parser.add_argument("--group-by", choices=("family", "encoding", "pdf-version"), default="family")
    args = parser.parse_args()
    rows = load_rows(args.metadata)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = (
            row.get("metadata", {}).get("effective_pdf_version")
            if args.group_by == "pdf-version"
            else row.get(args.group_by)
        )
        groups[str(value) if value is not None else "unmeasured"].append(row)
    print(
        json.dumps(
            {
                "group_by": args.group_by,
                "metric_note": "Literal anchors are authored silver observations, not layout or math accuracy.",
                "resource_note": "CPU sums fresh workers; maximum worker peak RSS is not concurrent total memory.",
                "groups": {name: aggregate(group) for name, group in sorted(groups.items())},
            },
            indent=2,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
