"""Reproduce fixed offline partial salvage and its source-only review gallery."""

# Frozen artifacts use heterogeneous schemas; no provider client is constructed.
# ruff: noqa: EM101, EM102, TRY003, C901, PLC0415
from __future__ import annotations

import argparse
import hashlib
import html
import json
import platform
import re
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.generalization_scoring import score_dataset
from bench.pipeline_vision_partial import SPEC, salvage
from bench.pipeline_vision_transcription import PROVENANCE, markdown
from bench.silver import guard_path, write_json

CONTROLS = (
    "natural16-vision-crops-sonnet-1024",
    "natural16-hybrid-sonnet-1024",
    "natural16-vision-crops-haiku-1024",
    "natural16-vision-haiku-2048-q50",
    "natural16-vision-haiku-2048-q50-workers4",
)
DENSE_IDS = {"p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"}
EXPECTED_PAGES = 16
BASELINE_KEYS = (
    "correct_text_cells",
    "correct_structure_cells",
    "complete_tables",
    "exact_table_spans",
    "false_positive_tables",
    "false_positive_page",
    "missing_tables",
    "localized_tables_iou_ge_0_5",
)


def _index(rows: list[dict[str, Any]], ids: list[str], label: str) -> dict[str, dict[str, Any]]:
    result = {row["id"]: row for row in rows}
    if len(rows) != len(ids) or len(result) != len(rows) or set(result) != set(ids):
        raise ValueError(f"Incomplete or duplicate sixteen-page coverage: {label}")
    return result


def gallery(manifest: dict[str, Any], partials: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    """Render every source page and escaped partial tables without reference access."""
    import pylopdf

    pages = manifest["pages"]
    by_id = _index(partials, [p["id"] for p in pages], "gallery partials")
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=True)
    sections, images = [], []
    for record in pages:
        identifier = record["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", identifier):
            raise ValueError("Unsafe gallery page identifier")
        path = guard_path(Path(record["pdf_path"]))
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != record["pdf_sha256"]:
            raise ValueError("Source PDF changed before gallery rendering")
        with pylopdf.open(stream=data) as document:
            page = document[record["page_number"]]
            pixels = page.render(scale=767 / max(page.rect.width, page.rect.height), background=(255, 255, 255))
            image_info = {
                "id": identifier,
                "pdf_sha256": record["pdf_sha256"],
                "page_number": record["page_number"],
                "viewport": list(page.rect),
                "rotation": page.rotation,
                "image_sha256": hashlib.sha256(pixels).hexdigest(),
            }
        if path.read_bytes() != data:
            raise ValueError("Source PDF changed during gallery rendering")
        (output / f"{identifier}.png").write_bytes(pixels)
        images.append(image_info)
        partial = by_id[identifier]
        escaped_tables = markdown(
            {"tables": partial["tables"], "text_provenance": PROVENANCE, "source_conserved": False}
        )
        reasons = html.escape(json.dumps(partial["quarantined"], ensure_ascii=False, indent=2))
        status = html.escape(str(partial["baseline_status"]))
        sections.append(
            f"<section><h2>PARTIAL — {html.escape(identifier)}</h2>"
            f"<p>Original status: <strong>{status}</strong>. Partial review only; "
            "coverage unverified, no complete-page success or source conservation.</p>"
            f'<div class="columns"><img src="{identifier}.png" alt="Original source page">'
            f"<div><h3>Retained isolated tables ({len(partial['tables'])})</h3>"
            f"{escaped_tables or '<p>No isolated valid tables retained.</p>'}"
            f"<h3>Quarantine reasons</h3><pre>{reasons}</pre></div></div></section>"
        )
    gallery_html = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>PARTIAL hybrid Sonnet review — all sixteen pages</title>"
        "<style>body{font:16px system-ui;max-width:1500px;margin:auto;padding:24px}"
        "h1,h2{color:#8b2500}section{border-top:2px solid #999;padding:20px 0}"
        ".columns{display:grid;grid-template-columns:minmax(250px,1fr) minmax(350px,1fr);gap:24px}"
        ".columns>div{min-width:0;overflow-x:auto}"
        "img{max-width:100%;height:auto}table{border-collapse:collapse;margin:12px 0}"
        "td{border:1px solid #777;padding:4px}pre{white-space:pre-wrap;overflow-wrap:anywhere}"
        "@media(max-width:800px){.columns{grid-template-columns:1fr}}</style>"
        "<h1>PARTIAL: hybrid Sonnet1024 offline review</h1>"
        "<p>All sixteen intended source pages, without reference-selected content. "
        "Strict complete-page failures and original charges remain unchanged. "
        "Tables are model-transcribed partial evidence, not approved complete extraction.</p>"
        + "".join(sections)
        + "</html>"
    )
    (output / "index.html").write_text(gallery_html)
    write_json(output / "source-images.json", images)
    return {"path": str(output / "index.html"), "pages": len(images), "source_images": images}


def audit(root: Path, output: Path, *, with_gallery: bool = False) -> dict[str, Any]:
    """Read only explicit fixed inputs; attest report identity before salvage/scoring."""
    root, output = guard_path(root), guard_path(output)
    started, cpu = time.perf_counter(), time.process_time()
    hashes: dict[str, str] = {}

    def load(path: Path) -> dict[str, Any]:
        payload = guard_path(path).read_bytes()
        hashes[str(path)] = hashlib.sha256(payload).hexdigest()
        return json.loads(payload)

    manifest = load(root / "screens/natural16/manifest.json")
    targets = load(root / "screens/natural16/private-targets.json")
    if manifest.get("split") != "DEV" or manifest["dataset_sha256"] != targets["dataset_sha256"]:
        raise ValueError("Requires matched explicit DEV screen")
    ids = [p["id"] for p in manifest["pages"]]
    if len(ids) != EXPECTED_PAGES or len(set(ids)) != EXPECTED_PAGES:
        raise ValueError("Requires all sixteen unique intended pages")
    gold = _index(targets["pages"], ids, "targets")
    runs = []
    for name in CONTROLS:
        report_path = root / name / "report.json"
        report = load(report_path)
        evaluated = load(root / name / "verified-evaluation.json")
        if evaluated.get("report_sha256") != hashes[str(report_path)]:
            raise ValueError(f"Changed report identity: {name}")
        if (
            evaluated.get("manifest_sha256") != hashes[str(root / "screens/natural16/manifest.json")]
            or evaluated.get("dataset_sha256") != manifest["dataset_sha256"]
        ):
            raise ValueError("Verified evaluation corpus identity changed")
        by_id = _index(report["results"], ids, name)
        _index(evaluated["page_scores"], ids, f"{name} verified scores")
        partials, score_predictions = [], []
        quarantines: Counter[str] = Counter()
        native_count = 0
        for identifier in ids:
            parent = by_id[identifier]
            vision = parent.get("vision_result", parent)
            native_count += len(parent.get("native_state", {}).get("tables", []))
            viewport = vision.get("viewport", parent.get("viewport"))
            if viewport is None:
                raise ValueError("Missing original page viewport")
            descriptors = (
                [
                    {"viewport": region["viewport"], "response": region.get("transcription_response")}
                    for region in vision["transcription_regions"]
                ]
                if "transcription_regions" in vision
                else [{"viewport": viewport, "response": vision.get("transcription_response")}]
            )
            partial = salvage(descriptors, viewport)
            quarantines.update(q["code"] for q in partial["quarantined"])
            partials.append(
                {"id": identifier, "baseline_status": parent["status"], "vision_status": vision["status"], **partial}
            )
            # Scorer-only projection; processor outputs retain status partial.
            score_predictions.append({"id": identifier, "status": "ok", "tables": partial["tables"]})
        secondary = score_dataset(targets, score_predictions)
        groups = {}
        for group in ("all16", "dense2", "remaining14"):
            selected = ids if group == "all16" else [i for i in ids if (i in DENSE_IDS) == (group == "dense2")]
            group_predictions = [p for p in score_predictions if p["id"] in selected]
            baseline = [p for p in evaluated["page_scores"] if p["id"] in selected]
            groups[group] = {
                "intended": len(selected),
                "partial_pages_with_tables": sum(bool(p["tables"]) for p in group_predictions),
                "baseline_errors": sum(p["error"] for p in baseline),
                "secondary": score_dataset([gold[i] for i in selected], group_predictions)["totals"],
                "baseline": {key: sum(p.get(key, 0) for p in baseline) for key in BASELINE_KEYS},
            }
        runs.append(
            {
                "name": name,
                "groups": groups,
                "baseline_scores": evaluated["scores"],
                "baseline_costs_unchanged": evaluated["costs"],
                "baseline_resources_unchanged": evaluated["resources"],
                "parent_native_table_count": native_count,
                "quarantine_codes": dict(quarantines),
                "partial_pages": partials,
                "secondary_page_scores": secondary["pages"],
            }
        )
    result = {
        "spec": SPEC,
        "frozen_metric_commit": "20b87cc",
        "dataset_sha256": manifest["dataset_sha256"],
        "inputs_sha256": hashes,
        "runs": runs,
        "partial_helper_sha256": hashlib.sha256(
            Path(__file__).with_name("pipeline_vision_partial.py").read_bytes()
        ).hexdigest(),
    }
    if with_gallery:
        hybrid = next(run for run in runs if run["name"] == "natural16-hybrid-sonnet-1024")
        result["gallery"] = gallery(manifest, hybrid["partial_pages"], output / "hybrid-partial-review")
    for path, digest in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError("Input changed during audit")
    result["resources"] = {
        "wall_s": time.perf_counter() - started,
        "cpu_s": time.process_time() - cpu,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "scope": (
            "Single CPU process; audit wall/CPU excludes imports; lifetime kernel RSS includes imports; no sampling"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "audit.json", result)
    return result


def main() -> None:
    """Run fixed retained controls without any provider transport."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gallery", action="store_true")
    args = parser.parse_args()
    result = audit(args.artifact_root, args.output, with_gallery=args.gallery)
    print(
        json.dumps(
            {
                "output": str(args.output / "audit.json"),
                "resources": result["resources"],
                "gallery": result.get("gallery", {}).get("path"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
