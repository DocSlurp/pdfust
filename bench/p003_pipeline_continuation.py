"""Offline source-equivalent continuation planning for stopped P003 pipeline arms."""

# ruff: noqa: ANN401, EM101, TRY003, TRY301, C901, PLR0912
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from bench.generalization_report import verify_output
from bench.silver import guard_path, sha, write_json

FIELDS = ("id", "pdf_path", "pdf_sha256", "page_number")
PROCESSORS = {"regions", "vision_regions", "hybrid", "whole"}


def _read(path: Path) -> Any:
    return json.loads(guard_path(path).read_bytes())


def _id(value: Any) -> str:
    if not isinstance(value, str) or not value or Path(value).name != value or value in {".", ".."} or "\\" in value:
        raise ValueError("Unsafe page or archived code identity")
    return value


def _inventory(directory: Path) -> dict[str, str]:
    """Hash only explicit segment-local files; never visit external artifact trees."""
    return {
        str(path.relative_to(directory)): sha(guard_path(path).read_bytes())
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def authenticate(
    directory: Path, trusted_code: dict[str, str], *, never_transmitted: Path | None = None
) -> dict[str, Any]:
    """Authenticate a stable stopped segment, preserving errors and quarantining invalid outputs."""
    directory = guard_path(directory)
    before = _inventory(directory)
    frozen = _read(directory / "frozen.json")
    config = frozen["config"]
    if config.get("campaign") != "P003" or config.get("workers", 1) != 1:
        raise ValueError("Continuation requires a serial-page P003 arm")
    processor = config.get("processor", "whole")
    if processor not in PROCESSORS:
        raise ValueError("Continuation has no trusted output verifier for this processor")
    hashes = frozen["code_sha256"]
    if not isinstance(hashes, dict) or "pipeline_run.py" not in hashes or not hashes:
        raise ValueError("Missing original pipeline code identity")
    for name, digest in hashes.items():
        _id(name)
        if not name.endswith(".py") or trusted_code.get(name) != digest or before.get("code/" + name) != digest:
            raise ValueError("Archive differs from independent root trusted code map")
    records = frozen["records"]
    ids = [_id(row["id"]) for row in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate frozen page identity")
    checked = set()
    for row in records:
        if set(row) != set(FIELDS):
            raise ValueError("Unexpected frozen source record fields")
        pdf = guard_path(Path(row["pdf_path"]))
        key = (str(pdf), row["pdf_sha256"])
        if key not in checked and sha(pdf.read_bytes()) != row["pdf_sha256"]:
            raise ValueError("Frozen PDF identity changed")
        checked.add(key)
    report = _read(directory / "report.json") if "report.json" in before else None
    if report is not None and report["config"] != config:
        raise ValueError("Report config differs from original frozen treatment")
    reported = {row["id"]: row for row in report["results"]} if report else {}
    if report and (len(reported) != len(report["results"]) or set(reported) - set(ids)):
        raise ValueError("Report contains duplicate or unknown page results")
    ownership = {ident: {} for ident in ids}
    for name, digest in before.items():
        leaf = Path(name).name
        matches = [ident for ident in ids if leaf.startswith((ident + "-", ident + "."))]
        if matches:
            ownership[max(matches, key=len)][name] = digest
    pages = []
    for record in records:
        ident = record["id"]
        artifacts = ownership[ident]
        page: dict[str, Any] = {"record": record, "artifacts": artifacts}
        filename = ident + "-result.json"
        if filename in before:
            try:
                result = _read(directory / filename)
                if result["id"] != ident or result.get("status") not in {"ok", "error", "unsupported_no_text"}:
                    raise ValueError("Malformed completed page identity or status")
                if report and reported.get(ident) != result:
                    raise ValueError("Retained result differs from segment report")
                page["result"] = result
                if result["status"] != "ok":
                    page["status"] = "completed_error"
                else:
                    verify_output(
                        directory, result, processor=processor, source_order=config.get("source_order", "legacy")
                    )
                    page["status"] = "completed_success"
            except (ValueError, KeyError, TypeError, OSError) as error:
                page.update(
                    status="invalid_completed_output", validation_error=type(error).__name__ + ": " + str(error)[:500]
                )
        else:
            page["status"] = "interrupted_artifacts" if artifacts else "clean_missing"
        pages.append(page)
    if report and any(page["record"]["id"] not in reported for page in pages):
        raise ValueError("Final segment report omits frozen pages")
    if before != _inventory(directory):
        raise ValueError("Segment changed during authentication; stop the arm before planning")
    segment = {
        "directory": str(directory.resolve()),
        "frozen": frozen,
        "report": report,
        "pages": pages,
        "artifact_sha256": before,
        "trusted_code": trusted_code,
    }
    if never_transmitted is not None:
        attest_never_transmitted(segment, never_transmitted)
    return segment


def attest_never_transmitted(segment: dict[str, Any], path: Path) -> None:
    """Validate external root proof against an immutable captured ledger snapshot."""
    proof = _read(path)
    frozen = segment["frozen"]
    directory = Path(segment["directory"])
    snapshot = proof.get("ledger_snapshot", {})
    if (
        proof.get("schema") != 1
        or proof.get("kind") != "root_prepared_never_transmitted"
        or proof.get("root_reviewed") is not True
        or proof.get("segment_directory") != str(directory)
        or proof.get("run_id") != frozen["config"]["run_id"]
        or proof.get("frozen_sha256") != segment["artifact_sha256"]["frozen.json"]
        or proof.get("code_sha256") != frozen["code_sha256"]
        or not isinstance(proof.get("audit_description"), str)
        or not proof["audit_description"].strip()
        or directory in guard_path(path).resolve().parents
    ):
        raise ValueError("Never-transmitted proof differs from stopped source/code/run identity")
    captured = guard_path(Path(snapshot["path"]))
    if directory in captured.resolve().parents or sha(captured.read_bytes()) != snapshot.get("sha256"):
        raise ValueError("Captured ledger snapshot identity differs")
    requests = _read(captured).get("requests")
    if not isinstance(requests, list) or any(
        not isinstance(e, dict) or not isinstance(e.get("tag"), str) for e in requests
    ):
        raise ValueError("Captured ledger lacks a complete request tag inventory")
    pages = {p["record"]["id"]: p for p in segment["pages"]}
    admitted = set()
    for item in proof["pages"]:
        ident = _id(item["id"])
        prefix = f"P003/{frozen['config']['run_id']}/{ident}/"
        page = pages.get(ident)
        if (
            ident in admitted
            or page is None
            or page["status"] != "interrupted_artifacts"
            or item.get("record") != page["record"]
            or item.get("artifacts") != page["artifacts"]
            or item.get("tag_prefix") != prefix
            or item.get("ledger_entry_count") != 0
            or not page["artifacts"]
            or any(
                re.fullmatch(re.escape(ident) + r"-request-[0-9]+\.json", name) is None for name in page["artifacts"]
            )
            or any(e["tag"].startswith(prefix) for e in requests)
        ):
            raise ValueError("Page lacks exact request-only and zero-admission proof")
        admitted.add(ident)
    if not admitted:
        raise ValueError("Never-transmitted proof admits no pages")
    for ident in admitted:
        pages[ident]["status"] = "prepared_never_transmitted"
    segment["never_transmitted_attestation"] = {
        "path": str(guard_path(path).resolve()),
        "sha256": sha(guard_path(path).read_bytes()),
        "proof": proof,
        "scope": "explicit root audit; no retry of any admitted attempt",
    }


def prepare(
    directory: Path, trusted_code: Path, manifest_path: Path, output: Path, *, never_transmitted: Path | None = None
) -> dict[str, Any]:
    """Freeze clean missing pages only; never re-admit successful, failed or interrupted pages."""
    segment = authenticate(directory, _read(trusted_code), never_transmitted=never_transmitted)
    manifest_path, output = guard_path(manifest_path), guard_path(output)
    manifest = _read(manifest_path)
    if manifest.get("split") != "DEV" or sha(manifest_path.read_bytes()) != segment["frozen"]["manifest_sha256"]:
        raise ValueError("Explicit original source manifest differs from frozen identity")
    rows = [{key: row[key] for key in FIELDS} for row in manifest["pages"]]
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Original source manifest repeats page IDs")
    by_id = {row["id"]: row for row in rows}
    if any(by_id.get(row["id"]) != row for row in segment["frozen"]["records"]):
        raise ValueError("Original manifest source records differ from frozen source records")
    remaining = [
        page["record"] for page in segment["pages"] if page["status"] in {"clean_missing", "prepared_never_transmitted"}
    ]
    subset = {
        "schema": manifest.get("schema", 1),
        "split": "DEV",
        "pages": [{**row, "pilot": True} for row in remaining],
        "source_manifest_sha256": segment["frozen"]["manifest_sha256"],
        "scope": "clean unattempted pages only; source-equivalent per-model continuation",
    }
    output.mkdir(parents=True, exist_ok=False)
    archive_attestation(segment, output)
    write_json(output / "manifest.json", subset)
    plan = {
        "processor": "p003_pipeline_continuation_plan",
        "original": segment,
        "manifest_sha256": sha((output / "manifest.json").read_bytes()),
        "remaining_ids": [row["id"] for row in remaining],
        "status_counts": dict(Counter(page["status"] for page in segment["pages"])),
        "blocked_ids": [
            page["record"]["id"]
            for page in segment["pages"]
            if page["status"] in {"interrupted_artifacts", "invalid_completed_output"}
        ],
        "same_model_only": True,
        "automatic_retries": False,
        "no_paid_calls": True,
        "accounting": (
            "Absent original run report leaves whole-run CPU and cost unknown; page timings are not substituted"
        ),
        "helper_sha256": sha(Path(__file__).read_bytes()),
    }
    write_json(output / "plan.json", plan)
    shutil.copyfile(Path(__file__), output / Path(__file__).name)
    return {
        key: plan[key]
        for key in (
            "remaining_ids",
            "blocked_ids",
            "status_counts",
            "same_model_only",
            "automatic_retries",
            "no_paid_calls",
        )
    }


def _finite(value: Any) -> float | None:
    if isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return float(value)
    return None


def archive_attestation(segment: dict[str, Any], output: Path) -> None:
    """Retain the root audit and immutable captured ledger alongside derived artifacts."""
    receipt = segment.get("never_transmitted_attestation")
    if receipt is not None:
        target = output / "never-transmitted-audit"
        target.mkdir()
        shutil.copyfile(guard_path(Path(receipt["path"])), target / "root-attestation.json")
        snapshot = receipt["proof"]["ledger_snapshot"]
        raw = guard_path(Path(snapshot["path"])).read_bytes()
        if sha(raw) != snapshot["sha256"]:
            raise ValueError("Captured ledger changed before audit freezing")
        (target / "captured-ledger.json").write_bytes(raw)


def combine(specs: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    """Combine disjoint same-treatment segments; explicit measured totals never double count segments."""
    if not specs:
        raise ValueError("At least one original segment is required")
    segments = [
        authenticate(
            Path(spec["directory"]),
            _read(Path(spec["trusted_code"])),
            never_transmitted=Path(spec["never_transmitted"]) if spec.get("never_transmitted") else None,
        )
        for spec in specs
    ]
    if len({segment["directory"] for segment in segments}) != len(segments):
        raise ValueError("Duplicate segment would double count original work")
    original = segments[0]["frozen"]
    config = {key: value for key, value in original["config"].items() if key != "run_id"}
    by_id = {row["id"]: row for row in original["records"]}
    selected = {}
    for segment in segments:
        if {key: value for key, value in segment["frozen"]["config"].items() if key != "run_id"} != config:
            raise ValueError("Continuation changes original model or treatment")
        if segment["frozen"]["code_sha256"] != original["code_sha256"]:
            raise ValueError("Continuation changes original frozen pipeline code")
        for page in segment["pages"]:
            ident = page["record"]["id"]
            if by_id.get(ident) != page["record"]:
                raise ValueError("Continuation changes original source identity")
            if page["status"] == "invalid_completed_output":
                raise ValueError("Invalid completed output cannot be promoted during composition")
            if page["status"] in {"completed_success", "completed_error"}:
                if ident in selected:
                    raise ValueError("Completed page repeated; automatic retries are forbidden")
                selected[ident] = (segment, page)
    # Any earlier attempted missing page is never silently retried by a later segment.
    for segment in segments:
        for page in segment["pages"]:
            if page["status"] == "interrupted_artifacts" and page["record"]["id"] in selected:
                raise ValueError("Interrupted page was retried without a separate explicit retry treatment")
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=False)
    provenance = []
    measurements = []
    for index, (spec, segment) in enumerate(zip(specs, segments, strict=True)):
        target = output / "segments" / str(index)
        shutil.copytree(Path(segment["directory"]), target)
        archive_attestation(segment, target)
        provenance.append(
            {
                "directory": segment["directory"],
                "artifact_sha256": segment["artifact_sha256"],
                "trusted_code": segment["trusted_code"],
                "never_transmitted_attestation": segment.get("never_transmitted_attestation"),
            }
        )
        retained_report = segment["report"]
        # Root may supply independently measured killed-process interval/accounting;
        # preserve its provenance instead of inferring totals from completed page calls.
        measurement = spec.get("measurement")
        if measurement is None:
            measurement = (
                {
                    "metrics": retained_report.get("metrics", {}),
                    "effective_usd": retained_report.get("effective_usd"),
                    "accounted_usd": retained_report.get("accounted_usd"),
                    "source": "original complete segment report",
                }
                if retained_report
                else {
                    "metrics": {},
                    "effective_usd": None,
                    "accounted_usd": None,
                    "source": "unmeasured: stopped segment has no report",
                }
            )
        measurements.append(measurement)
    results = []
    for record in original["records"]:
        if record["id"] in selected:
            segment, page = selected[record["id"]]
            for filename in page["artifacts"]:
                target = output / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(Path(segment["directory"]) / filename, target)
            results.append(page["result"])

    def total(values: list[Any]) -> float | None:
        numbers = [_finite(value) for value in values]
        return sum(numbers) if all(value is not None for value in numbers) else None

    wall = total([row.get("metrics", {}).get("wall_seconds") for row in measurements])
    cpu = total([row.get("metrics", {}).get("cpu_seconds") for row in measurements])
    peaks = [_finite(row.get("metrics", {}).get("peak_sampled_rss_bytes")) for row in measurements]
    good = sum(row["status"] == "ok" for row in results)
    missing = [row["id"] for row in original["records"] if row["id"] not in selected]
    report = {
        "config": original["config"],
        "results": results,
        "page_count": len(results),
        "complete_output_pages": good,
        "missing_ids": missing,
        "continuation_status": "complete" if not missing else "incomplete",
        "segments": provenance,
        "segment_measurements": measurements,
        "metrics": {
            "wall_seconds": wall,
            "cpu_seconds": cpu,
            "peak_sampled_rss_bytes": max(peaks) if all(p is not None for p in peaks) else None,
            "measurement": (
                "sum of separately measured same-arm segment intervals; RSS maximum, never sum; no queue idle gaps"
            ),
            "comparability": "contended segmented pipeline; not a serial performance comparison",
        },
        "effective_usd": total([row.get("effective_usd") for row in measurements]),
        "accounted_usd": total([row.get("accounted_usd") for row in measurements]),
        "calls": sum(len(row.get("calls", [])) for row in results),
        "cost_scope": (
            "all original plus continuation attempts once per segment; absent totals stay unknown; "
            "retained page calls are not complete ledger costs"
        ),
        "pages_per_minute": good / wall * 60 if wall and not missing else None,
        "no_paid_calls": True,
        "automatic_retries": False,
    }
    shutil.copytree(Path(segments[0]["directory"]) / "code", output / "code")
    write_json(
        output / "frozen.json",
        {
            **original,
            "continuation_segments": provenance,
            "continuation_helper_sha256": sha(Path(__file__).read_bytes()),
        },
    )
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Plan or combine artifacts locally; this CLI cannot launch inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("prepare")
    plan.add_argument("--segment", type=Path, required=True)
    plan.add_argument("--trusted-code", type=Path, required=True)
    plan.add_argument("--manifest", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--never-transmitted", type=Path)
    merge = commands.add_parser("combine")
    merge.add_argument(
        "--segments",
        type=Path,
        required=True,
        help="JSON list of directory/trusted_code and optional explicit measurement",
    )
    merge.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = (
        prepare(args.segment, args.trusted_code, args.manifest, args.output, never_transmitted=args.never_transmitted)
        if args.command == "prepare"
        else combine(_read(args.segments), args.output)
    )
    print(json.dumps({key: value for key, value in result.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
