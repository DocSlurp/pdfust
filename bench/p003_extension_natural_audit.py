"""Frozen-policy CPU breadth check on the explicitly authorized natural16 DEV set."""

# ruff: noqa: EM101, TRY003, E501
from __future__ import annotations

import argparse
import json
import resource
import time
import warnings
from pathlib import Path
from typing import Any

import pylopdf
from bench.generalization_report import load_corpus
from bench.p003_extension_cases import _vector
from bench.p003_extension_headerband import POLICY, proposals
from bench.p003_extension_score import prediction, score_predictions
from bench.pipeline_assembly import _clean_table, _native
from bench.pipeline_repair import _sources, validate
from bench.silver import canonical, guard_path, sha, write_json

MANIFEST_PIN = "be1cc3788068e7354586863270627ce20d19926a7ee42c1c7903ca4c87b7d6b3"
POLICY_PIN = "108f2de4790bac228ea3c00e951e80ac7ce3ec09432c1242eefd68b63e1d4a22"
ARMS = ("native", "text", "headerband")
INTENDED_PAGES = 16


def extract_record(record: dict[str, Any]) -> dict[str, Any]:
    """Interpret exactly the declared PDF page, retaining full source and scan applicability."""
    raw = guard_path(Path(record["pdf_path"])).read_bytes()
    if sha(raw) != record["pdf_sha256"]:
        raise ValueError("Frozen input PDF changed")
    with warnings.catch_warnings(record=True) as collected, pylopdf.Document(stream=raw) as document:
        page = document[record["page_number"]]
        source = {"page_size": list(page.rect), "words": [
            {"id": "w" + sha(f"{record['id']}/{record['page_number']}/{i}".encode())[:16],
             "text": word[4], "bbox": list(word[:4])}
            for i, word in enumerate(page.get_text("words"))]}
        if not source["words"]:
            empty = {"tables": [], "unresolved_ids": []}
            return {"source": source, "status": "not_applicable_no_source_text", "states": dict.fromkeys(ARMS, empty),
                    "proposal_count": 0, "warnings": [str(w.message) for w in collected]}
        lookup = _sources(source)
        states = {}
        vectors_by_arm = {}
        for arm, strategy in (("native", "lines"), ("text", "text")):
            vectors = [_vector(table) for table in page.find_tables(strategy=strategy)]
            vectors_by_arm[arm] = vectors
            projected = {**source, "vector_candidates": vectors}
            tables = [{**_clean_table(table, lookup), "bbox": vector["bbox"]}
                      for table, vector in zip(_native(projected, source["words"]), vectors, strict=True)]
            used = {ident for table in tables for cell in table["cells"] for ident in cell["source_ids"]}
            state = {"tables": tables, "unresolved_ids": [word["id"] for word in source["words"] if word["id"] not in used]}
            validate(source, state)
            states[arm] = state
        source["vector_candidates"] = vectors_by_arm["native"]
        candidates = proposals(source)
        states["headerband"] = candidates[0]["state"] if candidates and not states["native"]["tables"] else states["native"]
        return {"source": source, "status": "ok", "states": states, "proposal_count": len(candidates),
                "proposal_receipt": candidates[0]["source_receipt"] if candidates else None,
                "warnings": [str(w.message) for w in collected]}


def prepare(corpus: Path, output: Path) -> dict[str, Any]:
    """Freeze every intended source output before reading any natural16 target."""
    corpus, output = guard_path(corpus), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh audit output directory required")
    raw = (corpus / "manifest.json").read_bytes()
    if sha(raw) != MANIFEST_PIN or sha(canonical(POLICY)) != POLICY_PIN:
        raise ValueError("Explicit natural16 source manifest and frozen policy required")
    manifest = json.loads(raw)
    if manifest["split"] != "DEV" or len(manifest["pages"]) != INTENDED_PAGES:
        raise ValueError("Complete authorized 16-page DEV inventory required")
    start, cpu = time.perf_counter(), time.process_time()
    output.mkdir(parents=True)
    (output / "pages").mkdir()
    (output / "code").mkdir()
    receipts = []
    for record in manifest["pages"]:
        try:
            row = extract_record(record)
        except (ValueError, TypeError, KeyError, IndexError, RuntimeError) as error:
            row = {"status": "preparation_error", "error": type(error).__name__ + ": " + str(error),
                   "states": dict.fromkeys(ARMS, None), "source": None, "proposal_count": 0}
        row.update(id=record["id"], page_number=record["page_number"], pdf_path=record["pdf_path"], pdf_sha256=record["pdf_sha256"])
        path = output / "pages" / (record["id"] + ".json")
        write_json(path, row)
        receipts.append({"id": record["id"], "page_number": record["page_number"], "status": row["status"], "sha256": sha(path.read_bytes())})
    code = {}
    for name in (Path(__file__).name, "p003_extension_headerband.py", "p003_extension_cases.py", "pipeline_assembly.py", "pipeline_repair.py"):
        code_raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(code_raw)
        code[name] = sha(code_raw)
    frozen = {"corpus": str(corpus), "manifest_sha256": MANIFEST_PIN, "policy": POLICY, "policy_sha256": POLICY_PIN,
              "code_sha256": code, "pages": receipts, "intended_pages": 16, "references_read": False,
              "scope": "Explicit existing natural16 DEV breadth check; no policy tuning and no confirmation/heldout access",
              "resources": {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu,
                            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            "measurement": "Single parent CPU source extraction/proposals, unsampled lifetime getrusage including imports; no inference/GPU"}}
    write_json(output / "frozen.json", frozen)
    return frozen


def evaluate(output: Path, *, frozen_sha256: str, targets_sha256: str) -> dict[str, Any]:
    """Authenticate frozen source output and pinned targets before complete-denominator scoring."""
    output = guard_path(output)
    if (output / "evaluation.json").exists():
        raise FileExistsError("Do not overwrite completed audit evaluation")
    raw = (output / "frozen.json").read_bytes()
    if sha(raw) != frozen_sha256:
        raise ValueError("Frozen source-output receipt changed")
    frozen = json.loads(raw)
    corpus = guard_path(Path(frozen["corpus"]))
    if sha((corpus / "manifest.json").read_bytes()) != MANIFEST_PIN or frozen["references_read"]:
        raise ValueError("Source manifest/freeze provenance changed")
    rows = []
    for receipt in frozen["pages"]:
        path = output / "pages" / (receipt["id"] + ".json")
        raw = path.read_bytes()
        if sha(raw) != receipt["sha256"]:
            raise ValueError("Frozen natural source output changed")
        row = json.loads(raw)
        if sha(guard_path(Path(row["pdf_path"])).read_bytes()) != row["pdf_sha256"] or row["page_number"] != receipt["page_number"]:
            raise ValueError("Declared source PDF/page changed")
        if row["status"] == "ok":
            for state in row["states"].values():
                validate(row["source"], state)
        rows.append(row)
    # Hash pin is checked before the existing loader interprets authorized DEV targets.
    if sha((corpus / "private-targets.json").read_bytes()) != targets_sha256:
        raise ValueError("Pinned natural16 targets changed")
    _manifest, targets = load_corpus(corpus)
    start, cpu = time.perf_counter(), time.process_time()
    arms = {arm: score_predictions(targets["pages"], [prediction(row["id"], row["states"][arm], status=row["status"]) for row in rows]) for arm in ARMS}
    result = {"frozen_sha256": frozen_sha256, "targets_sha256": targets_sha256, "manifest_sha256": MANIFEST_PIN,
              "policy_sha256": POLICY_PIN, "intended_pages": 16, "source_admitted_before_target_read": True,
              "applicability": {"text_pages": sum(row["status"] == "ok" for row in rows),
                                "no_source_text_pages": sum(row["status"] == "not_applicable_no_source_text" for row in rows),
                                "preparation_error_pages": sum(row["status"] == "preparation_error" for row in rows)},
              "arms": arms, "source_preparation_resources": frozen["resources"],
              "resources": {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu,
                            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            "measurement": "Single parent CPU scoring; unsampled lifetime getrusage including imports; no GPU/inference"},
              "scope": "All 16 intended DEV pages; no-text scans remain not applicable and are not omitted or credited as model success"}
    write_json(output / "evaluation.json", result)
    return result


def main() -> None:
    """Prepare first, then evaluate only when explicit frozen and target pins are supplied."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--frozen-sha256")
    parser.add_argument("--targets-sha256")
    args = parser.parse_args()
    if args.frozen_sha256 and args.targets_sha256:
        result = evaluate(args.output, frozen_sha256=args.frozen_sha256, targets_sha256=args.targets_sha256)
    elif args.corpus:
        result = prepare(args.corpus, args.output)
    else:
        raise ValueError("Prepare needs --corpus; evaluation needs both explicit pins")
    print(json.dumps({"intended_pages": result["intended_pages"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
