"""Freeze bounded header hypotheses for one externally authenticated DEV16 baseline."""

# ruff: noqa: EM101, TRY003, SLF001, C901, PLR2004, PLR0912
from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import pdfust
from bench import generalization_vision_regions as regions
from bench import p003_candidate_run as baseline
from bench import p003_header_proposals as headers
from bench import pipeline_vision_transcription as strict
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

CODE_FILES = (
    "p003_header_proposals.py",
    "p003_header_proposals_prepare.py",
    "pipeline_vision_transcription.py",
    "generalization_vision_regions.py",
    "pipeline_frontier.py",
    "p003_candidate_run.py",
    "pipeline_run.py",
    "generalization_report.py",
    "p003_candidate_choice.py",
)


def prepare(directory: Path, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Authenticate complete source, crops, requests and raw responses before hypothesis freezing."""
    directory, output = guard_path(directory), guard_path(output)
    if output.exists():
        raise FileExistsError("Header proposal inventory requires a fresh output")
    trusted = baseline._read(guard_path(trusted_code))
    with Resources() as resources:
        frozen, report, _ = baseline.authenticate(directory, trusted)
        if report.get("config") != frozen["config"]:
            raise ValueError("Original report differs from frozen model/treatment configuration")
        if len(frozen["records"]) != 16 or frozen["config"].get("transcription_representation", "legacy") != "legacy":
            raise ValueError("Header hypotheses require one complete legacy DEV16 baseline")
        results = {row["id"]: row for row in report["results"]}
        plans = []
        for record in frozen["records"]:
            page = results[record["id"]]
            raw = guard_path(Path(record["pdf_path"])).read_bytes()
            if sha(raw) != record["pdf_sha256"]:
                raise ValueError("Original PDF identity changed")
            with pdfust.open(stream=raw) as document:
                source = document[record["page_number"]]
                if list(source.rect) != page["viewport"] or source.rotation != page["original_rotation"]:
                    raise ValueError("Original source geometry changed")
            expected = regions.proposals(page["layout_detection"], page["viewport"])
            keys = ("index", "request_index", "viewport", "detector_box")
            if [{k: c[k] for k in keys} for c in page["transcription_regions"]] != [
                {k: c[k] for k in keys} for c in expected
            ]:
                raise ValueError("Complete original crop inventory changed")
            input_refusal = None
            for crop in page["transcription_regions"]:
                request_path = directory / f"{record['id']}-request-{crop['request_index']}.json"
                if not request_path.exists():
                    input_refusal = "Missing complete original request; no unauthenticated hypothesis"
                    continue
                request = baseline._read(request_path)
                if request["model"] != frozen["config"]["generation_model"]:
                    raise ValueError("Original request differs from the single declared generation model")
                url, image = baseline._crop_bytes(request)
                rebuilt = strict.request(request["model"], url, crop["viewport"], request["max_tokens"])
                provider = frozen["config"].get("generation_provider")
                if provider:
                    rebuilt["provider"] = {"only": [provider], "allow_fallbacks": False, "require_parameters": True}
                if (
                    rebuilt != request
                    or sha(json.dumps(rebuilt, separators=(",", ":")).encode()) != crop["request"]["body_sha256"]
                    or sha(image) != crop["image"]["image_sha256"]
                    or len(image) != crop["image"]["image_bytes"]
                    or crop["image"]["image_viewport"] != crop["viewport"]
                ):
                    raise ValueError("Original crop/request pixel provenance changed")
            plan = headers.freeze_page(page, input_refusal=input_refusal)
            plan["record"] = record
            plans.append(plan)
        output.mkdir(parents=True)
        shutil.copytree(directory, output / "baseline")
        (output / "code").mkdir()
        hashes = {}
        for name in CODE_FILES:
            path = Path(__file__).with_name(name)
            shutil.copyfile(path, output / "code" / name)
            hashes[name] = sha(path.read_bytes())
        for plan in plans:
            write_json(output / (plan["id"] + "-header-plan.json"), plan)
        write_json(
            output / "frozen.json",
            {
                "processor": "p003_header_proposals",
                "records": frozen["records"],
                "manifest_sha256": frozen["manifest_sha256"],
                "baseline_config": frozen["config"],
                "baseline_directory": str(directory.resolve()),
                "baseline_frozen_sha256": sha((directory / "frozen.json").read_bytes()),
                "baseline_report_sha256": sha((directory / "report.json").read_bytes()),
                "external_trusted_code": trusted,
                "code_sha256": hashes,
                "max_table_alternatives": headers.MAX_TABLE_ALTERNATIVES,
                "max_page_alternatives": headers.MAX_PAGE_ALTERNATIVES,
                "references_read": False,
                "hosted_calls": 0,
                "plan_sha256": {p["id"]: sha((output / (p["id"] + "-header-plan.json")).read_bytes()) for p in plans},
                "no_original_baseline_mutation": True,
                "no_default_parser_repair": True,
                "source_conserved": False,
            },
        )
    summary = {
        "page_count": len(plans),
        "status_counts": dict(Counter(p["status"] for p in plans)),
        "complete_alternative_count": sum(len(p["complete_page_alternatives"]) for p in plans),
        "pages": [
            {
                "id": p["id"],
                "original_status": p["original_page_status"],
                "status": p["status"],
                "alternative_count": len(p["complete_page_alternatives"]),
                "reason": p.get("reason"),
            }
            for p in plans
        ],
        "resources": resources.summary(),
        "hosted_calls": 0,
        "references_read": False,
        "scope": "source-only hypothetical retained-header structures; not quality or pipeline speed",
    }
    write_json(output / "report.json", summary)
    write_json(output / "resources.json", resources.samples)
    return summary


def main() -> None:
    """Run explicit CPU-only source authentication and alternative freezing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.baseline, args.trusted_code, args.output), indent=2))


if __name__ == "__main__":
    main()
