"""Stage exact L011 source packets and verify native results before DEV scoring.

Source preparation never opens references. Reviewed full-source and admitted-
scope agreement remain separate;24 overlapping regions from one Senate page
are not independent documents or independently adjudicated structural gold.
"""

# ruff: noqa: C901, PLR0912, PLR2004 - explicit complete source/result admissions.
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.lowlevel_natural import ARMS
from bench.lowlevel_natural import verify as source_verify
from bench.lowlevel_run import parse_response
from bench.remote_report import _dev, _json, _jsonl, _path, _read, _verified

SOURCE_COUNT = 24
BODY_COUNT = SOURCE_COUNT * len(ARMS)


def _fail(message: str) -> None:
    raise ValueError(message)


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_inventory(source: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Verify the original source-only freeze, without matrix/reference access."""
    manifest = source_verify(source)
    if manifest.get("experiment") != "L011-source" or len(manifest["pages"]) != SOURCE_COUNT:
        _fail("Expected original24-region L011 source freeze")
    if len(manifest["records"]) != BODY_COUNT:
        _fail("Expected original96 natural source packets")
    manifest_hash = _digest(_read(source / "manifest.json"))
    rows = []
    for record in manifest["records"]:
        if set(record) != {"request", "sha256", "model", "arm", "page_ids", "body_bytes", "non_image_bytes"}:
            _fail("Natural source records must not include scorer fields")
        raw = _verified(_path(source, record["request"]), record["sha256"])
        body = json.loads(raw)
        if (
            len(body["state"]) != 2
            or not isinstance(body["state"][0], str)
            or body["state"][1].get("type") != "image_url"
        ):
            _fail("Natural canonical image state differs")
        url = body["state"][1]["image_url"]["url"]
        if not url.startswith("data:image/png;base64,"):
            _fail("Natural packet must retain its canonical PNG data URI")
        png = base64.b64decode(url.split(",", 1)[1], validate=True)
        ident = _digest(
            json.dumps(
                ["L011-native", manifest_hash, record["sha256"], record["arm"], record["page_ids"]],
                separators=(",", ":"),
            ).encode()
        )[:24]
        rows.append(
            {"id": ident, "record": record, "request_bytes": raw, "image_bytes": png, "image_sha256": _digest(png)}
        )
    if len({row["id"] for row in rows}) != BODY_COUNT:
        _fail("Natural opaque source identities collide")
    return manifest, rows


def prepare(source_dir: Path, output: Path) -> Path:
    """Freeze exact96 source bodies and PNGs; leave all references root-local."""
    started, cpu = time.monotonic(), time.process_time()
    source = _dev(source_dir)
    destination = _dev(output)
    manifest, rows = source_inventory(source)
    destination.mkdir(parents=True, exist_ok=False)
    records, index = [], []
    for row in rows:
        request = row["id"] + ".json"
        image = row["image_sha256"] + ".png"
        (destination / request).write_bytes(row["request_bytes"])
        image_path = destination / image
        if not image_path.exists():
            image_path.write_bytes(row["image_bytes"])
        records.append({"id": row["id"], "request_file": request, "image_files": [image]})
        index.append({"id": row["id"], **row["record"], "image_sha256": row["image_sha256"]})
    (destination / "manifest.json").write_text(json.dumps({"records": records}, indent=2) + "\n")
    (destination / "source-index.json").write_text(json.dumps(index, indent=2) + "\n")
    (destination / "provenance.json").write_text(
        json.dumps(
            {
                "experiment": "L011-native-source",
                "source_manifest_sha256": _digest(_read(source / "manifest.json")),
                "source_pdf_sha256": manifest["source_sha256"],
                "worker_manifest_sha256": _digest(_read(destination / "manifest.json")),
                "source_index_sha256": _digest(_read(destination / "source-index.json")),
                "request_count": BODY_COUNT,
                "source_regions": SOURCE_COUNT,
                "references_copied": False,
                "projection": "none; original request bytes/model/state/questions/PNG retained",
                "preparation_wall_seconds": time.monotonic() - started,
                "preparation_cpu_seconds": time.process_time() - cpu,
            },
            indent=2,
        )
        + "\n"
    )
    return destination / "manifest.json"


def verify_stage(source: Path, packets: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify all retained stage artifacts against exact source-only packets."""
    manifest, rows = source_inventory(source)
    expected = {row["id"]: row for row in rows}
    provenance = _json(packets.parent / "provenance.json")
    _verified(source / "manifest.json", provenance["source_manifest_sha256"])
    staged = json.loads(_verified(packets, provenance["worker_manifest_sha256"]))
    index = json.loads(_verified(packets.parent / "source-index.json", provenance["source_index_sha256"]))
    if staged.keys() != {"records"} or len(staged["records"]) != BODY_COUNT or len(index) != BODY_COUNT:
        _fail("Natural stage inventory differs")
    expected_index = [{"id": row["id"], **row["record"], "image_sha256": row["image_sha256"]} for row in rows]
    if index != expected_index:
        _fail("Natural source index differs from exact frozen inventory")
    seen = set()
    for row in staged["records"]:
        if set(row) != {"id", "request_file", "image_files"} or row["id"] in seen:
            _fail("Natural worker inventory contains unsupported fields or duplicateIDs")
        seen.add(row["id"])
        original = expected[row["id"]]
        if (
            len(row["image_files"]) != 1
            or _read(_path(packets.parent, row["request_file"])) != original["request_bytes"]
        ):
            _fail("Natural staged source request differs")
        if _read(_path(packets.parent, row["image_files"][0])) != original["image_bytes"]:
            _fail("Natural staged source PNG differs")
    if seen != set(expected):
        _fail("Natural worker/source identities differ")
    return manifest, expected


def verify_events(output: Path, inventory: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify every returned identity and request hash before references."""
    status = _json(output / "status.json")
    path = output / "attempts.jsonl"
    rows, tail = (
        _jsonl(path, allow_incomplete_tail=status.get("status") != "complete") if path.exists() else ([], False)
    )
    started, completed = set(), {}
    for row in rows:
        ident = row["id"]
        if ident not in inventory:
            _fail("Natural returned ID differs from source inventory")
        if row["event"] == "attempt_started":
            if ident in started:
                _fail("Natural duplicate fresh attempt/retry")
            started.add(ident)
        elif row["event"] == "attempt_completed":
            if ident not in started or ident in completed:
                _fail("Natural completion lacks unique prior start")
            if row.get("request_sha256") != inventory[ident]["record"]["sha256"]:
                _fail("Natural returned request hash differs")
            completed[ident] = row
        else:
            _fail("Unknown natural worker event")
    return completed, {
        "worker_status": status,
        "started": len(started),
        "completed": len(completed),
        "incomplete_tail": tail,
    }


def agreement(choice: str, reference: dict[str, Any], arm: str) -> dict[str, bool]:
    """Apply the existing L011 provisional full-source/scoped comparison semantics."""
    scoped = reference["scope_references"][arm.split("-", maxsplit=1)[0]]["choice"]
    return {
        "full_match": choice == reference["choice"],
        "scope_match": choice == scoped,
        "scope_abstention": scoped == "unresolved" and choice == "unresolved",
    }


def evaluate(source_dir: Path, packets: Path, runs: dict[str, Path], *, references_dir: Path) -> dict[str, Any]:
    """Verify complete source/stage/all-model outputs before local DEV references."""
    source, packet_manifest = _dev(source_dir), _dev(packets)
    manifest, inventory = verify_stage(source, packet_manifest)
    returned = {model: verify_events(_dev(path), inventory) for model, path in runs.items()}
    # First reference access: source/stage and every returned model have been checked.
    reference_root = _dev(references_dir)
    reference_manifest = _json(reference_root / "manifest.json")
    if (
        reference_manifest.get("experiment") != "L011"
        or reference_manifest["parent_manifest_sha256"] != _digest(_read(source / "manifest.json"))
        or reference_manifest["pages"] != manifest["pages"]
    ):
        _fail("Natural reviewed matrix differs from original source freeze")
    reviewed = json.loads(
        _verified(reference_root / "private-references.json", reference_manifest["references_sha256"])
    )
    if reviewed["source_manifest_sha256"] != _digest(_read(source / "manifest.json")):
        _fail("Natural reference provenance differs from original source")
    references = {row["id"]: row for row in reviewed["references"]}
    if set(references) != {row["id"] for row in manifest["pages"]}:
        _fail("Natural reference inventory differs")
    models = {}
    for model, (completed, status) in returned.items():
        summaries = []
        for arm in ARMS:
            records = [row for row in inventory.values() if row["record"]["arm"] == arm]
            counts: Counter[str] = Counter()
            choices: Counter[str] = Counter()
            times: list[float] = []
            cpu: list[float] = []
            rss: list[int] = []
            allocated: list[int] = []
            reserved: list[int] = []
            for row in records:
                event = completed.get(row["id"])
                if event is None:
                    counts["missing"] += 1
                    continue
                for key, destination in (("inference_wall_seconds", times), ("inference_cpu_seconds", cpu)):
                    value = event.get(key)
                    if (
                        isinstance(value, (int, float))
                        and not isinstance(value, bool)
                        and math.isfinite(value)
                        and value >= 0
                    ):
                        destination.append(float(value))
                if event.get("peak_rss_bytes") is not None:
                    rss.append(event["peak_rss_bytes"])
                for key, gpu_values in (("peak_allocated_bytes", allocated), ("peak_reserved_bytes", reserved)):
                    value = event.get("cuda", {}).get(key)
                    if value is not None:
                        gpu_values.append(value)
                if event.get("status") != "ok":
                    counts["worker_error"] += 1
                    continue
                try:
                    parsed = parse_response(event["response"], 1)[0]
                except (ValueError, TypeError, KeyError):
                    counts["schema_error"] += 1
                    continue
                choice = parsed["choice"]
                choices[choice] += 1
                counts["completed"] += 1
                counts["tie_abstentions"] += parsed["tie_abstention"]
                result = agreement(choice, references[row["record"]["page_ids"][0]], arm)
                counts.update({key: int(value) for key, value in result.items()})
            summaries.append(
                {
                    "arm": arm,
                    "planned": len(records),
                    "counts": dict(counts),
                    "choices": dict(choices),
                    "inference_seconds": sum(times) if len(times) == len(records) else None,
                    "inference_known_seconds": sum(times),
                    "cpu_seconds": sum(cpu) if len(cpu) == len(records) else None,
                    "cpu_known_seconds": sum(cpu),
                    "peak_rss_bytes": max(rss, default=None),
                    "cuda_allocated_bytes": max(allocated, default=None),
                    "cuda_reserved_bytes": max(reserved, default=None),
                }
            )
        models[model] = {"summaries": summaries, "status": status}
    return {
        "experiment": "L011-native-dev",
        "source_regions": SOURCE_COUNT,
        "inputs_per_model": BODY_COUNT,
        "models": models,
        "source_manifest_sha256": _digest(_read(source / "manifest.json")),
        "reference_annotation": reviewed.get("annotation"),
        "scope": "single source-aware provisional review;24 overlapping regions from one Senate page",
    }


def markdown(result: dict[str, Any]) -> str:
    """Report natural reference agreement without claiming independently reviewed gold."""
    lines = [
        "# Native natural DEV comparison",
        "",
        result["scope"],
        "",
        (
            "Original96 L011 request bodies and PNGs are unchanged. Source preparation read no references; "
            "all staged/returned hashes were verified before references were opened locally. "
            "Full-source reference agreement and admitted-scope agreement are separate measurements."
        ),
        "",
        (
            "| Model | Arm | Valid/planned | Full-source matches | Scope matches | Abstentions | "
            "Inference s | CPU s | RSS MiB |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, output in result["models"].items():
        for row in output["summaries"]:
            count = row["counts"]

            def metric(key: str, row: dict[str, Any] = row) -> str:
                value = row[key]
                return "unknown" if value is None else f"{value:.3f}"

            rss = row["peak_rss_bytes"]
            lines.append(
                f"| {model} | {row['arm']} | {count.get('completed', 0)}/{row['planned']} | "
                f"{count.get('full_match', 0)}/{row['planned']} | {count.get('scope_match', 0)}/{row['planned']} | "
                f"{row['choices'].get('unresolved', 0)} | {metric('inference_seconds')} | {metric('cpu_seconds')} | "
                f"{'unknown' if rss is None else f'{rss / 2**20:.1f}'} |"
            )
    lines += [
        "",
        (
            "Denominators include failed, missing and malformed outputs. Native tied maxima become unresolved. "
            "No accuracy over independent documents or natural structural gold is claimed. "
            "Scope and fixed-edge resolution "
            "jointly change legibility. Inference wall/CPU covers serial adapter prediction; RSS is process-lifetime "
            "high water, including loading. CUDA allocator peaks and detailed failures remain in JSON; GPU device-wide "
            "utilization is separate. No costs are inferred from latency."
        ),
        "",
        f"Source manifest SHA256: `{result['source_manifest_sha256']}`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Prepare source-only artifacts or score explicit returned native outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--packets", type=Path)
    parser.add_argument("--run", action="append", help="model-label=output-directory")
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--references-dir", type=Path)
    args = parser.parse_args()
    if args.prepare is not None:
        if args.run or args.packets or args.references_dir:
            parser.error("Preparation cannot read worker results")
        print(prepare(args.source, args.prepare))
    else:
        if not all((args.packets, args.run, args.markdown, args.json, args.references_dir)):
            parser.error("Reporting requires packets, runs, markdown and json")
        runs = {model: Path(path) for model, path in (item.split("=", 1) for item in args.run)}
        result = evaluate(args.source, args.packets, runs, references_dir=args.references_dir)
        args.markdown.write_text(markdown(result))
        args.json.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
