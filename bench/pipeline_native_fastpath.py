"""Prove a native-only detector shortcut for source-ID region assembly."""

# Frozen benchmark dictionaries are heterogeneous; invalid input is a failed proof.
# ruff: noqa: EM101, TRY003, PLR2004, C901, PLR0912
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from bench.generalization_run import sanitize_vectors
from bench.pipeline_layout_detector import _Measure, detector_regions


def native_fastpath(
    source: dict[str, Any], *, source_id_only: bool = False, max_words: int = 512, max_characters: int = 8000
) -> dict[str, Any]:
    """Return a detector-free plan only after complete native ownership is proven.

    Call after the runner's ordinary source/native validation. Source-ID scope must
    be explicit; the proof says nothing about image-only tables or visible pixels.
    Invalid input returns an ineligible proof, preserving the ordinary error path.
    """
    if source_id_only is not True:
        return {"eligible": False, "reason": "source_id_scope_required", "plan": None}
    try:
        plan = detector_regions(source, [], max_words=max_words, max_characters=max_characters)
        words = plan["words"]
        if not words:
            return {"eligible": False, "reason": "zero_source_words", "plan": None}
        native = [r for r in plan["regions"] if r["kind"] == "native"]
        native_ids = [ident for region in native for ident in region["source_ids"]]
        owned = set(native_ids)
        residual = [w["id"] for w in words if w["id"] not in owned]
        eligible = bool(native) and not residual and Counter(native_ids) == Counter(w["id"] for w in words)
        return {
            "eligible": eligible,
            "reason": "complete_native_ownership" if eligible else "residual_source_words",
            "source_word_count": len(words),
            "native_word_count": len(native_ids),
            "native_region_count": len(native),
            "residual_ids": residual,
            "plan": plan if eligible else None,
            "equivalence": (
                "Native region topology and literal source ownership only; detector evidence metadata differs"
            ),
        }
    except (ValueError, KeyError, TypeError, IndexError) as error:
        return {"eligible": False, "reason": "invalid_source_or_native_layout", "detail": str(error), "plan": None}


def _summary(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "sum": sum(values) if values else None,
        "median": median(values) if values else None,
        "maximum": max(values) if values else None,
    }


def _number(value: object) -> float | None:
    return (
        float(value)
        if not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
        else None
    )


def audit(run: Path, output: Path, *, native_run: Path | None = None, allow_incomplete: bool = False) -> dict[str, Any]:
    """Read only explicit frozen records; preserve partial coverage and nested timings."""
    frozen_bytes = (run / "frozen.json").read_bytes()
    frozen = json.loads(frozen_bytes)
    records = frozen["records"]
    complete = (run / "report.json").is_file() and all((run / f"{r['id']}-result.json").is_file() for r in records)
    if not complete and not allow_incomplete:
        raise ValueError("Final aggregation requires the completed report and every intended result")
    output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "run": str(run.resolve()),
        "frozen_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "complete": complete,
        "intended_pages": len(records),
        "pages": [],
        "missing_ids": [],
        "measurement_note": (
            "Source includes OCR. Detector parent includes raster, transport, worker wait "
            "and partition; child wall is nested. API client wall is synchronous and separate. "
            "Parent CPU excludes detector child; OCR CPU is not separately measured. "
            "Peaks are maxima, never sums. No fresh end-to-end timings."
        ),
    }
    options = {
        "max_words": frozen["config"].get("region_words", 256),
        "max_characters": frozen["config"].get("region_characters", 8000),
    }
    with _Measure() as measure:
        for record in records:
            path = run / f"{record['id']}-result.json"
            if not path.is_file():
                report["missing_ids"].append(record["id"])
                continue
            raw_bytes = path.read_bytes()
            result = json.loads(raw_bytes)
            page: dict[str, Any] = {
                "id": record["id"],
                "status": result["status"],
                "result_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            }
            source = result.get("source")
            if source is not None:
                sanitized, warnings = sanitize_vectors(source)
                proof = native_fastpath(sanitized, source_id_only=True, **options)
                page["proof"] = {k: v for k, v in proof.items() if k != "plan"}
                page["native_quarantine_warnings"] = warnings
                if result.get("layout_detector"):
                    original = detector_regions(sanitized, result["layout_detector"]["boxes"], **options)
                    empty_plan = proof["plan"] if proof["eligible"] else detector_regions(sanitized, [], **options)
                    page["cached_native_regions_preserved"] = [
                        r for r in original["regions"] if r["kind"] == "native"
                    ] == [r for r in empty_plan["regions"] if r["kind"] == "native"]
                    page["cached_source_inventory_preserved"] = Counter(
                        i for r in original["regions"] for i in r["source_ids"]
                    ) == Counter(w["id"] for w in sanitized["words"])
                    if not page["cached_native_regions_preserved"] or not page["cached_source_inventory_preserved"]:
                        raise ValueError("Cached detector plan changed native regions or source inventory")
                    if proof["eligible"]:
                        page["cached_region_equivalence"] = (
                            original["regions"] == empty_plan["regions"] and original["words"] == empty_plan["words"]
                        )
                        if not page["cached_region_equivalence"]:
                            raise ValueError("Native shortcut disagrees with cached detector partition")
            else:
                page["proof"] = {"eligible": False, "reason": "no_retained_source"}
            detector = result.get("layout_detector", {})
            worker = detector.get("metrics", {})
            calls = result.get("calls", [])
            api_wall_values = [_number(c.get("client_wall_seconds")) for c in calls]
            api_cpu_values = [_number(c.get("client_cpu_seconds")) for c in calls]
            api_wall = (
                sum(v for v in api_wall_values if v is not None)
                if all(v is not None for v in api_wall_values)
                else None
            )
            api_cpu = (
                sum(v for v in api_cpu_values if v is not None) if all(v is not None for v in api_cpu_values) else None
            )
            total = _number(result.get("wall_seconds"))
            source_wall = _number(result.get("stages", {}).get("source_seconds"))
            ocr_wall = _number(result.get("ocr", {}).get("wall_seconds"))
            detector_parent = _number(detector.get("parent_wall_seconds"))
            known_source = source_wall or 0.0
            known_detector = detector_parent or 0.0
            other = (
                total - known_source - known_detector - api_wall if total is not None and api_wall is not None else None
            )
            if other is not None and other < -0.001:
                raise ValueError("Retained parent wall phases overlap or exceed page total")
            page["timing"] = {
                "total_parent_wall": total,
                "source_wall_including_ocr": source_wall,
                "ocr_wall_nested_in_source": ocr_wall,
                "detector_parent_wall_including_worker": detector_parent,
                "detector_worker_wall_nested": _number(worker.get("wall_seconds")),
                "api_client_wall": api_wall,
                "other_or_uninstrumented_parent_wall": other,
                "total_parent_cpu": _number(result.get("cpu_seconds")),
                "detector_parent_cpu": _number(detector.get("parent_cpu_seconds")),
                "detector_worker_cpu": _number(worker.get("cpu_seconds")),
                "api_client_parent_cpu": api_cpu,
                "detector_worker_sampled_rss": _number(worker.get("peak_sampled_rss_bytes")),
                "detector_worker_lifetime_peak_rss_kib": _number(worker.get("worker_lifetime_peak_rss_kib")),
            }
            page["calls"] = len(calls)
            report["pages"].append(page)
        if native_run is not None:
            native_records = json.loads((native_run / "frozen.json").read_text())["records"]
            census = []
            for record in native_records:
                path = native_run / f"{record['id']}-result.json"
                if not path.is_file():
                    census.append({"id": record["id"], "reason": "missing_result", "eligible": False})
                    continue
                result = json.loads(path.read_text())
                if result.get("source") is None:
                    census.append({"id": record["id"], "reason": "no_retained_source", "eligible": False})
                    continue
                sanitized, warnings = sanitize_vectors(result["source"])
                proof = native_fastpath(sanitized, source_id_only=True, **options)
                census.append(
                    {
                        "id": record["id"],
                        **{k: v for k, v in proof.items() if k != "plan"},
                        "native_quarantine_warnings": warnings,
                    }
                )
            report["native_census"] = {
                "run": str(native_run.resolve()),
                "intended_pages": len(native_records),
                "pages": census,
            }
    report["audit_resources"] = {
        **measure.result,
        "measurement": (
            "Audit parent process_time CPU and /proc/self/statm RSS every100ms plus endpoints; "
            "lifetime peak getrusage. No OCR/detector/network calls."
        ),
    }
    report["status_counts"] = dict(Counter(p["status"] for p in report["pages"]))
    report["eligible_pages"] = sum(p["proof"]["eligible"] for p in report["pages"])
    keys: list[str] = list(next((p["timing"].keys() for p in report["pages"]), []))
    report["timing_summary"] = {
        k: _summary([p["timing"][k] for p in report["pages"] if p["timing"][k] is not None]) for k in keys
    }
    for key in ("detector_worker_sampled_rss", "detector_worker_lifetime_peak_rss_kib"):
        report["timing_summary"][key]["sum"] = None
        report["timing_summary"][key]["aggregation"] = "Memory peaks are not additive"
    report["ocr_nested_breakdown"] = {
        "within_measured_source_wall": _summary(
            [
                p["timing"]["ocr_wall_nested_in_source"]
                for p in report["pages"]
                if p["timing"]["ocr_wall_nested_in_source"] is not None
                and p["timing"]["source_wall_including_ocr"] is not None
            ]
        ),
        "within_uninstrumented_parent_wall": _summary(
            [
                p["timing"]["ocr_wall_nested_in_source"]
                for p in report["pages"]
                if p["timing"]["ocr_wall_nested_in_source"] is not None
                and p["timing"]["source_wall_including_ocr"] is None
            ]
        ),
    }
    report["replay_dependencies"] = {
        name: {
            "local_sha256": hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest(),
            "frozen_sha256": frozen.get("code_sha256", {}).get(name),
        }
        for name in ("pipeline_assembly.py", "pipeline_regions.py", "pipeline_layout_detector.py")
    }
    report["eligible_retained_upper_bounds"] = {
        k: _summary([p["timing"][k] for p in report["pages"] if p["proof"]["eligible"] and p["timing"][k] is not None])
        for k in (
            "detector_parent_wall_including_worker",
            "detector_parent_cpu",
            "detector_worker_wall_nested",
            "detector_worker_cpu",
        )
    }
    if complete:
        operational = json.loads((run / "report.json").read_text())
        report["pipeline_parent_run_metrics"] = operational.get("metrics", {})
        report["operational_resource_fields"] = {
            k: v
            for k, v in operational.items()
            if k not in {"results", "records", "pages", "config"}
            and any(s in k for s in ("wall", "cpu", "rss", "initialization", "detector", "resource"))
        }
    (output / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    """Run one explicit retained-source census and stage profile without inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--native-run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    report = audit(args.run, args.output, native_run=args.native_run, allow_incomplete=args.allow_incomplete)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "complete",
                    "intended_pages",
                    "eligible_pages",
                    "status_counts",
                    "eligible_retained_upper_bounds",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
