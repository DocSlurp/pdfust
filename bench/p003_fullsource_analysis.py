"""Independent complete-denominator DEV scoring for every frozen full-source gutter profile."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_fullsource_tracks as tracks
from bench.generalization_report import load_corpus
from bench.p003_availability_analysis import authenticate_archive, read
from bench.p003_gate_run import authenticate
from bench.p003_report import strict_scores
from bench.silver import canonical, guard_path, sha


def verify(
    directory: Path, trusted_code: dict[str, str], source_trusted_code: dict[str, str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Rebuild all 144 complete states and refusal plans before reading separate targets."""
    directory = guard_path(directory)
    frozen = authenticate_archive(directory, trusted_code, unused=("p003_fullsource_tracks_prepare.py",))
    report = read(directory / "report.json")
    profiles = [{"gap_em": gap, "support_fraction": support} for gap in tracks.GAPS for support in tracks.SUPPORTS]
    if (
        frozen["processor"] != "p003_fullsource_tracks"
        or frozen["references_read"] is not False
        or frozen["fresh_confirmation_accessed"] is not False
        or frozen["inference_calls"] != 0
        or frozen["profiles"] != profiles
        or report["frozen_sha256"] != sha((directory / "frozen.json").read_bytes())
    ):
        raise ValueError("Expected frozen source-only complete profile inventory")
    baseline = guard_path(Path(frozen["baseline"]))
    source_frozen, source_report = authenticate(baseline, source_trusted_code)
    if (
        source_frozen["records"] != frozen["records"]
        or sha((baseline / "frozen.json").read_bytes()) != frozen["baseline_frozen_sha256"]
        or read(directory / "source-trusted-code.json") != source_trusted_code
        or sha((directory / "source-trusted-code.json").read_bytes()) != frozen["external_source_code_sha256"]
        or [p["id"] for p in report["pages"]] != [r["id"] for r in frozen["records"]]
        or set(frozen["page_sha256"]) != {r["id"] for r in frozen["records"]}
    ):
        raise ValueError("Full-source original provenance/inventory differs")
    originals = {p["id"]: p for p in source_report["results"]}
    pages = []
    for record in frozen["records"]:
        ident = record["id"]
        path = directory / "pages" / f"{ident}.json"
        page = read(path)
        source = originals[ident]["source"]
        if (
            sha(path.read_bytes()) != frozen["page_sha256"][ident]
            or page["record"] != record
            or page["id"] != ident
            or page["source"] != source
            or sha((baseline / f"{ident}-result.json").read_bytes()) != page["baseline_result_sha256"]
            or sha(guard_path(Path(record["pdf_path"])).read_bytes()) != record["pdf_sha256"]
        ):
            raise ValueError("Full-source literal/PDF identity differs")
        physical = tracks.physical(source)
        variants = []
        for profile in profiles:
            plan = tracks.prepare(source, physical, **profile)
            state = tracks.decode(source, plan)
            variants.append({"profile": profile, "plan": plan, "state": state, "state_sha256": sha(canonical(state))})
        if page["physical"] != physical or page["variants"] != variants:
            raise ValueError("Full-source gutter plans/ownership/refusals differ from exact reconstruction")
        pages.append(page)
    status_counts = dict(Counter(v["plan"]["status"] for p in pages for v in p["variants"]))
    refusal_counts = dict(
        Counter(v["plan"]["refusal"] for p in pages for v in p["variants"] if v["plan"].get("refusal"))
    )
    if (
        report["status_counts"] != status_counts
        or report["refusal_counts"] != refusal_counts
        or report["intended_pages"] != len(pages)
        or report["variant_count"] != len(pages) * len(profiles)
    ):
        raise ValueError("Full-source report counts differ from reconstructed full inventory")
    return frozen, pages


def analyze(
    directory: Path, corpus: Path, *, trusted_code: dict[str, str], source_trusted_code: dict[str, str]
) -> dict[str, Any]:
    """Score every declared treatment; never select a profile using page gold."""
    frozen, pages = verify(directory, trusted_code, source_trusted_code)
    manifest, targets = load_corpus(guard_path(corpus))
    if {p["id"] for p in targets["pages"]} != {p["id"] for p in pages}:
        raise ValueError("Full-source scoring must retain exact intended DEV cohort")
    treatments = []
    for index, profile in enumerate(frozen["profiles"]):
        predictions = [
            {"id": p["id"], "status": "ok", "tables": p["variants"][index]["state"]["tables"]} for p in pages
        ]
        scored = strict_scores(targets["pages"], predictions)
        treatments.append(
            {
                "profile": profile,
                "scores": scored["totals"],
                "page_scores": scored["pages"],
                "positive_macro": scored["positive_macro"],
                "status_counts": dict(Counter(p["variants"][index]["plan"]["status"] for p in pages)),
                "refusal_counts": dict(
                    Counter(
                        p["variants"][index]["plan"]["refusal"]
                        for p in pages
                        if p["variants"][index]["plan"].get("refusal")
                    )
                ),
            }
        )
    return {
        "scope": "All nine source-only full-page gutter controls; no per-page gold selection; no semantic admission",
        "frozen_sha256": sha((guard_path(directory) / "frozen.json").read_bytes()),
        "code_sha256": frozen["code_sha256"],
        "dataset_sha256": manifest["dataset_sha256"],
        "intended_pages": len(pages),
        "treatments": treatments,
        "new_api_calls": 0,
        "source_conserved": True,
        "historical_source_cost_separate": True,
    }
