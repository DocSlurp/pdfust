"""Audit immutable A001 physical and rolling candidate opportunity on all DEV pages."""

# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR0912
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bench.p003_scoring_audit import pinned
from bench.pipeline_run import Resources
from bench.silver import canonical, dataset_path, guard_path, sha, write_json

VERSION = "p003-rolling-candidate-audit-v1"
PAGE_COUNT = 28
VARIANTS = ("physical", "rolling")
ORIGINAL_HASHES = {
    "manifest.json": "1606fcde633f3fe5b2c6a16d9476508e18644477bdd86dbefca020ed2f8f4cbb",
    "source-frozen.json": "53c47a4afd26c7ccdda5a2342eaf2a8f7aa663685e9a800aa901f0ad2a53f40f",
    "candidates-frozen.json": "30044b381bb5d2cf3842a975f486b3f8c92c7c7a3b736efeecea52d6156dc75e",
    "evaluation.json": "cd405d1e6507c44daff4205adfb66ffe210b34a3cbb68d6eae1aad94b7e7fa2e",
}
CODE_FILES = (
    "p003_rolling_candidate_audit.py",
    "borderless_challenge.py",
    "p003_scoring_audit.py",
    "p003_report.py",
    "generalization_scoring.py",
    "pipeline_scoring.py",
    "p003_schema_sensitivity.py",
    "p003_content_alignment.py",
    "p003_span_content.py",
    "pipeline_run.py",
    "silver.py",
)
TABLE_FIELDS = ("row_count", "col_count", "values", "spans")


def admit_alternative(source: dict[str, Any], alternative: dict[str, Any]) -> dict[str, Any]:
    """Verify each exact cell literal and one ownership/unresolved partition of source IDs."""
    words = source["words"]
    lookup = {w["id"]: w["text"] for w in words}
    if len(lookup) != len(words) or alternative["source_words"] != words:
        raise ValueError("Unique complete source words required")
    owned: list[str] = []
    tables = []
    for candidate in alternative["candidates"]:
        cells = candidate["cells"]
        values = [value for row in candidate["values"] for value in row]
        if len(cells) != len(values) or len(values) != candidate["row_count"] * candidate["col_count"]:
            raise ValueError("Complete cell ownership matrix required")
        if not str(candidate["header_role"]).startswith("unknown"):
            raise ValueError("Original unknown header role required")
        for cell, value in zip(cells, values, strict=True):
            ids = cell["source_ids"]
            if cell["role"] != "unknown" or any(i not in lookup for i in ids):
                raise ValueError("Unknown roles and admitted source IDs required")
            if value != " ".join(lookup[i] for i in ids):
                raise ValueError("Cell literal differs from exact source ID join")
            owned.extend(ids)
        tables.append({key: candidate[key] for key in TABLE_FIELDS})
    unresolved = alternative["unresolved_ids"]
    if Counter(owned + unresolved) != Counter(lookup.keys()):
        raise ValueError("Complete disjoint owned/unresolved conservation required")
    return {
        "id": source["id"],
        "status": "ok",
        "tables": tables,
        "owned_source_ids": len(owned),
        "unresolved_source_ids": len(unresolved),
        "header_roles": "unknown; original first row retained",
    }


def prepare(original: Path, corpus: Path, output: Path) -> dict[str, Any]:
    """Freeze two complete prediction inventories and actual source bytes before targets."""
    original, corpus, output = (guard_path(p) for p in (original, corpus, output))
    if output.exists():
        raise FileExistsError("Fresh source preparation directory required")
    with Resources() as resource:
        originals = {n: pinned(str(original / n), digest) for n, digest in ORIGINAL_HASHES.items()}
        manifest = originals["manifest.json"]
        if (
            manifest["source_sha256"] != ORIGINAL_HASHES["source-frozen.json"]
            or manifest["frozen_candidates_sha256"] != ORIGINAL_HASHES["candidates-frozen.json"]
        ):
            raise ValueError("Original source/candidate receipt differs")
        corpus_manifest_path = corpus / "manifest.json"
        corpus_manifest = json.loads(corpus_manifest_path.read_bytes())
        sources = originals["source-frozen.json"]["pages"]
        candidates = originals["candidates-frozen.json"]
        if candidates["source_sha256"] != ORIGINAL_HASHES["source-frozen.json"]:
            raise ValueError("Candidate source identity differs")
        pages = candidates["pages"]
        ids = [p["id"] for p in sources]
        if (
            len(ids) != PAGE_COUNT
            or len(set(ids)) != PAGE_COUNT
            or {p["id"] for p in pages} != set(ids)
            or len(pages) != PAGE_COUNT
            or {p["id"] for p in corpus_manifest["cases"]} != set(ids)
        ):
            raise ValueError("Complete unique 28-page source/candidate/corpus inventory required")
        by_id = {p["id"]: p for p in pages}
        cases = {p["id"]: p for p in corpus_manifest["cases"]}
        predictions: dict[str, list[dict[str, Any]]] = {v: [] for v in VARIANTS}
        source_receipts = []
        for source in sources:
            case = cases[source["id"]]
            pdf = dataset_path(corpus, case["pdf_path"])
            if sha(pdf.read_bytes()) != case["pdf_sha256"]:
                raise ValueError("Corpus PDF bytes differ")
            image = guard_path(Path(source["image_path"]))
            alternatives = by_id[source["id"]]["alternatives"]
            if len(alternatives) != len(VARIANTS) or {a["variant"] for a in alternatives} != set(VARIANTS):
                raise ValueError("Exactly physical and rolling alternatives required")
            for alternative in alternatives:
                predictions[alternative["variant"]].append(admit_alternative(source, alternative))
            source_receipts.append(
                {
                    "id": source["id"],
                    "source_sha256": sha(canonical(source)),
                    "pdf": str(pdf),
                    "pdf_sha256": case["pdf_sha256"],
                    "image": str(image),
                    "image_sha256": sha(image.read_bytes()),
                }
            )
        legacy = originals["evaluation.json"]["candidate_ceiling_rows"]
        if len(legacy) != PAGE_COUNT * len(VARIANTS) or {(r["id"], r["variant"]) for r in legacy} != {
            (i, v) for i in ids for v in VARIANTS
        }:
            raise ValueError("Complete original legacy page-score witnesses required")
        output.mkdir(parents=True)
        for variant, rows in predictions.items():
            write_json(output / (variant + "-predictions.json"), {"pages": rows})
        declaration = {
            "version": VERSION,
            "original": str(original),
            "original_sha256": ORIGINAL_HASHES,
            "corpus": str(corpus),
            "corpus_manifest_sha256": sha(corpus_manifest_path.read_bytes()),
            "source_receipts": source_receipts,
            "variants": list(VARIANTS),
            "intended_pages": PAGE_COUNT,
            "predictions_sha256": {v: sha((output / (v + "-predictions.json")).read_bytes()) for v in VARIANTS},
            "original_rules": candidates["rules"],
            "original_legacy_code_sha256": originals["evaluation.json"]["code_sha256"],
            "scope": "Unaccepted source-owned candidate opportunity; no decision-model outcome",
            "reference_files_opened": False,
            "new_api_calls": 0,
        }
        write_json(output / "plan.json", declaration)
    freeze = {
        "plan_sha256": sha((output / "plan.json").read_bytes()),
        "resources": resource.summary(),
        "code_sha256": {n: sha(Path(__file__).with_name(n).read_bytes()) for n in CODE_FILES},
        "reference_files_opened": False,
        "new_api_calls": 0,
    }
    write_json(output / "freeze.json", freeze)
    return freeze


def audit(plan: Path, output: Path, *, plan_sha256: str, trusted_code: Path, targets_sha256: str) -> dict[str, Any]:
    """Replay legacy scores exactly, then add fixed schema/content diagnostics."""
    from bench.borderless_challenge import score
    from bench.p003_report import strict_scores
    from bench.p003_scoring_audit import dual_scores

    authority = json.loads(guard_path(trusted_code).read_bytes())
    for name in CODE_FILES:
        if authority.get(name) != sha(Path(__file__).with_name(name).read_bytes()):
            raise ValueError("Independent current helper authority differs: " + name)
    declaration = pinned(str(plan), plan_sha256)
    if (
        declaration["version"] != VERSION
        or declaration["variants"] != list(VARIANTS)
        or declaration["original_sha256"] != ORIGINAL_HASHES
    ):
        raise ValueError("Frozen complete physical/rolling scope required")
    original = Path(declaration["original"])
    originals = {n: pinned(str(original / n), digest) for n, digest in declaration["original_sha256"].items()}
    sources = {p["id"]: p for p in originals["source-frozen.json"]["pages"]}
    predictions = {
        v: pinned(str(plan.parent / (v + "-predictions.json")), digest)["pages"]
        for v, digest in declaration["predictions_sha256"].items()
    }
    for receipt in declaration["source_receipts"]:
        for field in ("pdf", "image"):
            if sha(guard_path(Path(receipt[field])).read_bytes()) != receipt[field + "_sha256"]:
                raise ValueError("Frozen PDF/image source changed")
        if sha(canonical(sources[receipt["id"]])) != receipt["source_sha256"]:
            raise ValueError("Frozen source record changed")
    rebuilt: dict[str, list[dict[str, Any]]] = {v: [] for v in VARIANTS}
    for page in originals["candidates-frozen.json"]["pages"]:
        for alternative in page["alternatives"]:
            rebuilt[alternative["variant"]].append(admit_alternative(sources[page["id"]], alternative))
    for variant in VARIANTS:
        if len(predictions[variant]) != PAGE_COUNT or len({r["id"] for r in predictions[variant]}) != PAGE_COUNT:
            raise ValueError("Complete unique prediction inventory required")
        if {r["id"]: r for r in rebuilt[variant]} != {r["id"]: r for r in predictions[variant]}:
            raise ValueError("Prepared predictions differ from original source-owned candidates")
    corpus = guard_path(Path(declaration["corpus"]))
    pinned(str(corpus / "manifest.json"), declaration["corpus_manifest_sha256"])
    target_bytes = guard_path(corpus / "private-targets.json").read_bytes()
    if sha(target_bytes) != targets_sha256:
        raise ValueError("Externally approved target identity differs")
    targets = json.loads(target_bytes)
    if len(targets) != PAGE_COUNT or {t["id"] for t in targets} != set(sources):
        raise ValueError("Complete original reference inventory required")
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh scoring output required")
    output.mkdir(parents=True)
    gold = {t["id"]: t for t in targets}
    legacy = {(r["id"], r["variant"]): r for r in originals["evaluation.json"]["candidate_ceiling_rows"]}
    result: dict[str, Any] = {
        "version": VERSION,
        "plan_sha256": plan_sha256,
        "targets_sha256": targets_sha256,
        "scope": declaration["scope"],
        "new_api_calls": 0,
        "runs": [],
    }
    for variant in VARIANTS:
        rows = predictions[variant]
        with Resources() as resource:
            legacy_rows = [{"id": r["id"], "scores": score(gold[r["id"]], r["tables"])} for r in rows]
            if any(r["scores"] != legacy[(r["id"], variant)]["scores"] for r in legacy_rows):
                raise ValueError("Original per-page legacy scores differ")
            strict = strict_scores(targets, rows)
            secondary = dual_scores(targets, rows, strict)
        summary = {
            "name": variant,
            "strict": strict["totals"],
            "secondary": {k: v for k, v in secondary.items() if k != "pages"},
            "resources": resource.summary(),
        }
        write_json(
            output / (variant + ".json"),
            {"predictions": rows, "legacy": legacy_rows, "strict": strict, "secondary": secondary, "summary": summary},
        )
        result["runs"].append(summary)
    result["code_sha256"] = {n: sha(Path(__file__).with_name(n).read_bytes()) for n in CODE_FILES}
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Keep source preparation and approved scoring explicit separate actions."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--original", type=Path, required=True)
    prep.add_argument("--corpus", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    scoring = commands.add_parser("score")
    scoring.add_argument("--plan", type=Path, required=True)
    scoring.add_argument("--plan-sha256", required=True)
    scoring.add_argument("--trusted-code", type=Path, required=True)
    scoring.add_argument("--targets-sha256", required=True)
    scoring.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.original, args.corpus, args.output)
    else:
        audit(
            args.plan,
            args.output,
            plan_sha256=args.plan_sha256,
            trusted_code=args.trusted_code,
            targets_sha256=args.targets_sha256,
        )


if __name__ == "__main__":
    main()
