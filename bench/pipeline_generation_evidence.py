"""Source-only generation evidence encodings; text and ownership remain immutable."""

# Experimental source/measurement dictionaries contain heterogeneous JSON values.
# ruff: noqa: EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from bench.pipeline_assembly import _source

FORMATS = ("objects", "arrays", "quarter")


def _coordinate(value: float) -> float | int:
    # Above this magnitude every representable float already has quarter-unit spacing.
    if abs(value) >= 2**50:
        return value
    rounded = round(value * 4) / 4
    return int(rounded) if rounded.is_integer() else rounded


def encode(source: dict[str, Any], viewport: list[float] | None, evidence_format: str = "objects") -> str:
    """Encode every admitted source ID and text before the request packet admission."""
    if evidence_format not in FORMATS:
        raise ValueError("Unknown generation evidence format")
    retained = _source(source)
    if any(not word["id"] or len(word["id"]) > 128 for word in retained["words"]):
        raise ValueError("Invalid or over-limit source ID")
    packet: dict[str, Any] = {"page_size": retained["page_size"], "viewport": viewport}
    if evidence_format == "objects":
        packet["words"] = retained["words"]
    else:
        packet["word_fields"] = ["id", "text", "bbox"]
        packet["bbox_fields"] = ["left", "top", "right", "bottom"]
        packet["coordinate_space"] = "original display units; page_size and viewport are unchanged"
        packet["geometry"] = {
            "rounding": "none" if evidence_format == "arrays" else "nearest 0.25 display units, ties to even",
            "maximum_coordinate_error": 0 if evidence_format == "arrays" else 0.125,
            "parser_coordinates": "original retained source; transmitted geometry is model evidence only",
        }
        packet["words"] = [
            [
                word["id"],
                word["text"],
                list(word["bbox"]) if evidence_format == "arrays" else [_coordinate(value) for value in word["bbox"]],
            ]
            for word in retained["words"]
        ]
    return json.dumps(packet, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def benchmark(
    manifest_path: Path, sources_directory: Path, output: Path, *, tokenizer_json: Path | None = None
) -> dict[str, Any]:
    """Measure frozen source packet sizes; do not infer token counts or model quality."""
    from bench.pipeline_regions import split
    from bench.silver import guard_path, sha, write_json

    began, cpu = time.perf_counter(), time.process_time()
    manifest = json.loads(guard_path(manifest_path).read_bytes())
    if manifest.get("split") != "DEV":
        raise ValueError("Evidence benchmark requires explicit DEV sources")
    tokenizer = None
    tokenizer_metadata: dict[str, Any] = {
        "status": "unmeasured",
        "reason": "No explicit local tokenizer JSON configured",
    }
    if tokenizer_json is not None:
        from tokenizers import Tokenizer  # type: ignore[import-not-found]

        admitted = guard_path(tokenizer_json)
        tokenizer = Tokenizer.from_file(str(admitted))
        tokenizer_metadata = {
            "status": "local tokenizer counts; not provider-reported tokens",
            "json_sha256": sha(admitted.read_bytes()),
            "scope": "Source evidence packet only",
        }
    rows = []
    for record in manifest["pages"]:
        cached = json.loads(guard_path(sources_directory / f"{record['id']}-result.json").read_bytes())
        if cached["id"] != record["id"]:
            raise ValueError("Cached source ID does not match frozen page")
        original_hash = sha(json.dumps(cached["source"], sort_keys=True, ensure_ascii=False).encode())
        for budget in (256, 1024):
            plan = split(cached["source"], max_words=budget, max_characters=16_000)
            for region in plan["regions"]:
                for evidence_format in FORMATS:
                    text = encode(region["source"], region["bbox"], evidence_format)
                    packet = json.loads(text)
                    differences = [
                        abs(original - transmitted)
                        for word, row in zip(region["source"]["words"], packet["words"], strict=True)
                        for original, transmitted in zip(
                            word["bbox"], row[2] if evidence_format != "objects" else row["bbox"], strict=True
                        )
                    ]
                    rows.append(
                        {
                            "page_id": record["id"],
                            "original_cached_source_sha256": original_hash,
                            "region_id": region["id"],
                            "region_word_budget": budget,
                            "source_words": len(region["source"]["words"]),
                            "format": evidence_format,
                            "utf8_bytes": len(text.encode()),
                            "characters": len(text),
                            "within_packet_admission": len(text) <= 128_000,
                            "maximum_coordinate_error": max(differences, default=0),
                            "local_tokenizer_tokens": None if tokenizer is None else len(tokenizer.encode(text).ids),
                            "packet_sha256": sha(text.encode()),
                        }
                    )
    report = {
        "schema": 1,
        "source_only": True,
        "manifest_sha256": sha(manifest_path.read_bytes()),
        "tokenizer": tokenizer_metadata,
        "rows": rows,
        "scope": "Serialization only; no inference, quality claim, truncation, or parser-coordinate replacement",
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Own-process process_time CPU and Linux getrusage lifetime peak RSS; no RSS sampling",
            "scope": "Source reading, validation, splitting and all encodings; excludes original OCR/extraction",
        },
    }
    write_json(guard_path(output), report)
    return report


def main() -> None:
    """Run an explicit local source-only serialization benchmark."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sources-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tokenizer-json", type=Path)
    args = parser.parse_args()
    benchmark(args.manifest, args.sources_directory, args.output, tokenizer_json=args.tokenizer_json)


if __name__ == "__main__":
    main()
