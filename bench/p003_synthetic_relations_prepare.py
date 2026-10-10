"""Freeze source-only synthetic micro evidence before writing generator labels."""

# ruff: noqa: EM101, TRY003, E501
from __future__ import annotations

import argparse
import io
import json
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

from bench import p003_synthetic_relations as relations
from bench.silver import guard_path, sha, write_json

TWIN_COUNT = 2
UNDERDETERMINED_FAMILY = 2

CODE = (
    "p003_synthetic_relations.py",
    "p003_synthetic_relations_prepare.py",
    "feature_cases.py",
    "pipeline_row_evidence.py",
    "pipeline_regions.py",
    "silver.py",
)


def counterfactuals(output: Path, records: list[dict[str, Any]]) -> list[dict[str, Any]]:  # noqa: C901 - all exact equivalence checks predate source freeze.
    """Assert exact source twins before source freezing, without consulting the gold sidecar."""
    families: dict[tuple[str, int], list[str]] = {}
    for plan in relations.plans():
        families.setdefault((plan["kind"], plan["family"]), []).append(plan["id"])
    by_id = {r["id"]: r for r in records}
    receipts = []
    for (kind, family), identities in sorted(families.items()):
        if len(identities) != TWIN_COUNT:
            raise ValueError("Exactly two counterfactual cases per family required")
        a, b = [json_record(output, by_id[i]["path"]) for i in identities]
        if a["status"] != "ready" or b["status"] != "ready":
            receipts.append(
                {
                    "case_ids": sorted(identities),
                    "kind": kind,
                    "status": "extraction_refused",
                    "no_equivalence_claim": True,
                }
            )
            continue
        if relations.dump(a["source"]) != relations.dump(b["source"]):
            raise ValueError("Counterfactual literal source words/IDs/boxes differ")
        for pixels in (False, True):
            if relations.dump(relations.packet(a, pixels_available=pixels)) != relations.dump(
                relations.packet(b, pixels_available=pixels)
            ):
                raise ValueError("Counterfactual text geometry bytes differ")
        rules_equal = relations.dump(a["drawings"]) == relations.dump(b["drawings"])
        if rules_equal != (family == UNDERDETERMINED_FAMILY):
            raise ValueError("Observed rule visibility differs from predeclared counterfactual construction")
        equality = []
        for ia, ib in zip(a["images"], b["images"], strict=True):
            if (ia["scope"], ia["edge"], ia["viewport"], ia["dimensions"]) != (
                ib["scope"],
                ib["edge"],
                ib["viewport"],
                ib["dimensions"],
            ):
                raise ValueError("Counterfactual image framing differs")
            equal = (output / ia["path"]).read_bytes() == (output / ib["path"]).read_bytes()
            if equal != (family == UNDERDETERMINED_FAMILY):
                raise ValueError("Counterfactual source pixels do not match declared observable-rule difference")
            equality.append({"scope": ia["scope"], "edge": ia["edge"], "byte_identical": equal})
        receipts.append(
            {
                "case_ids": sorted(identities),
                "kind": kind,
                "status": "ready",
                "source_byte_identical": True,
                "text_geometry_byte_identical": True,
                "observed_drawings_byte_identical": rules_equal,
                "images": equality,
                "source_sha256": sha(relations.dump(a["source"]).encode()),
                "text_geometry_sha256": sha(relations.dump(relations.packet(a)).encode()),
            }
        )
    return receipts


def json_record(output: Path, relative: str) -> dict[str, Any]:
    """Read a declared source record, never labels or an enumerated directory."""
    return json.loads((output / relative).read_bytes())


def prepare(output: Path) -> dict[str, Any]:
    """Retain all24 denominators, actual source pixels and distinct label-free evidence treatments."""
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Synthetic micro preparation requires a new directory")
    began, cpu = time.perf_counter(), time.process_time()
    output.mkdir(parents=True)
    for directory in ("code", "pdfs", "sources", "packets", "images"):
        (output / directory).mkdir()
    code = {}
    for name in CODE:
        raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(raw)
        code[name] = sha(raw)
    records, gold = [], []
    for plan in relations.plans():
        ident = plan["id"]
        pdf, target = relations.authored(plan)
        path = output / "pdfs" / f"{ident}.pdf"
        path.write_bytes(pdf)
        record: dict[str, Any] = {
            "id": ident,
            "kind": plan["kind"],
            "pdf_path": str(path.relative_to(output)),
            "pdf_sha256": sha(pdf),
            "status": "extraction_refused",
            "question_id": "q0",
        }
        target["pdf_sha256"] = sha(pdf)
        try:
            source, pair, drawings = relations.extract(pdf, plan["literals"])
            record.update(status="ready", source=source, pair_source_ids=pair, drawings=drawings)
            boxes = [w["bbox"] for w in source["words"]]
            viewport = [
                max(0, min(b[0] for b in boxes) - 24),
                max(0, min(b[1] for b in boxes) - 24),
                min(source["page_size"][2], max(b[2] for b in boxes) + 24),
                min(source["page_size"][3], max(b[3] for b in boxes) + 24),
            ]
            record["images"] = []
            for scope, bounds in (("page", source["page_size"]), ("crop", viewport)):
                for edge in relations.EDGES:
                    raw = relations.image(pdf, edge=edge, viewport=bounds)
                    image_path = output / "images" / f"{ident}-{scope}-{edge}.png"
                    image_path.write_bytes(raw)
                    with Image.open(io.BytesIO(raw)) as image:
                        dimensions = list(image.size)
                    record["images"].append(
                        {
                            "scope": scope,
                            "edge": edge,
                            "viewport": bounds,
                            "path": str(image_path.relative_to(output)),
                            "sha256": sha(raw),
                            "encoded_bytes": len(raw),
                            "dimensions": dimensions,
                            "encoding": "Lossless actual source RGB PNG, compress6, no palette",
                            "coordinate_mapping": "Render source page at edge/max(viewport extent); round display viewport*scale to crop pixel bounds; no resampling",
                            "all_source_words_inside_viewport": True,
                        }
                    )
            record["packets"] = []
            for mode in relations.MODES:
                for pixels in (False, True):
                    packet = relations.packet(record, mode=mode, pixels_available=pixels)
                    raw = relations.dump(packet).encode()
                    packet_path = output / "packets" / f"{ident}-{mode}-{'pixels' if pixels else 'text'}.json"
                    packet_path.write_bytes(raw)
                    record["packets"].append(
                        {
                            "mode": mode,
                            "pixels_available": pixels,
                            "path": str(packet_path.relative_to(output)),
                            "sha256": sha(raw),
                            "utf8_bytes": len(raw),
                            "word_count": len(source["words"]),
                            "omitted_word_count": 0,
                            "state_cap_bytes": relations.MAX_STATE_BYTES,
                        }
                    )
            target["pair_source_ids"] = pair
            target["actual_source_sha256"] = sha(relations.dump(source).encode())
        except (ValueError, RuntimeError) as error:
            record.update(
                status="extraction_refused",
                refusal={"type": type(error).__name__, "detail": str(error)},
                no_question=True,
            )
            target["extraction_refused"] = True
        source_path = output / "sources" / f"{ident}.json"
        write_json(source_path, record)
        records.append(
            {
                "id": ident,
                "kind": plan["kind"],
                "status": record["status"],
                "path": str(source_path.relative_to(output)),
                "sha256": sha(source_path.read_bytes()),
                "pdf_sha256": sha(pdf),
            }
        )
        gold.append(target)
    # This source-only manifest is immutable before any private labels are written.
    artifacts = {
        str(p.relative_to(output)): sha(p.read_bytes())
        for p in sorted(output.rglob("*"))
        if p.is_file() and "code" not in p.relative_to(output).parts
    }
    twins = counterfactuals(output, records)
    frozen = {
        "schema": 1,
        "seed": relations.SEED,
        "records": records,
        "code_sha256": code,
        "artifact_sha256": artifacts,
        "source_only": True,
        "gold_in_prompt": False,
        "intended_case_count": 24,
        "treatments": {
            "geometry": list(relations.MODES),
            "pixels": ["text", "page128", "page512", "crop128", "crop512"],
        },
        "no_model_requests": True,
        "pair_policy": "Generator-predeclared pair; unique literal-to-extracted-ID matching only; missing/duplicate/merged extraction refuses; no model or natural corpus selection",
        "counterfactual_twins": twins,
    }
    write_json(output / "frozen.json", frozen)
    source_freeze_sha = sha((output / "frozen.json").read_bytes())
    write_json(
        output / "private-gold.json",
        {
            "source_frozen_sha256": source_freeze_sha,
            "cases": gold,
            "scope": "Author-owned logical labels; hidden ambiguity is evidence-scope limitation, not asserted recoverability",
        },
    )
    summary = {
        "source_frozen_sha256": source_freeze_sha,
        "gold_sha256": sha((output / "private-gold.json").read_bytes()),
        "case_count": len(records),
        "statuses": dict(Counter(r["status"] for r in records)),
        "construction_balance": dict(Counter(f"{g['kind']}:{g['expected_choice']}" for g in gold)),
        "deliberately_underdetermined_cases": sum(g["evidence_limitation"] for g in gold),
        "counterfactual_pair_count": len(twins),
        "identical_text_geometry_pairs": sum(t.get("text_geometry_byte_identical", False) for t in twins),
        "identical_all_pixel_pairs": sum(t.get("observed_drawings_byte_identical", False) for t in twins),
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Single sequential parent, perf_counter/process_time, unsampled getrusage lifetime peak includes imports; no hosted/GPU/subprocess work",
            "thread_bounds": "OMP/OPENBLAS/MKL=1 at invocation; renderer sequential",
        },
        "model_quality_measured": False,
        "hosted_calls": 0,
    }
    write_json(output / "report.json", summary)
    return summary


def main() -> None:
    """Prepare only in an explicit new ignored artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(relations.dump(prepare(args.output)))


if __name__ == "__main__":
    main()
