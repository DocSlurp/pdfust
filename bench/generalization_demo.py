"""Offline fixed-screen gallery of verified P002 output, including missing and failed pages."""

# Retained experiment dictionaries are heterogeneous; templates contain explicit static CSS.
# ruff: noqa: EM101, TRY003, PLR2004, PLC0415, C901, PLR0912, E501
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

from bench.generalization_report import verify_code, verify_output
from bench.pipeline_demo import MAX_INPUT_BYTES, _read
from bench.silver import guard_path, sha, write_json

ARTIFACT_ROOT = Path(__file__).resolve().parents[1] / "bench/results/pdf-master-artifacts"
MAX_PAGES = 20
FIELDS = ("id", "pdf_path", "pdf_sha256", "page_number")


def _tables(state: dict[str, Any]) -> str:
    """Render only verified table cells and integer spans, escaping every literal value."""
    fragments = []
    for index, table in enumerate(state["tables"], 1):
        rows, columns = table["row_count"], table["col_count"]
        if type(rows) is not int or type(columns) is not int or min(rows, columns) < 1 or rows * columns > 4096:
            raise ValueError("Demo table shape exceeds admission")
        spans = {(s["row"], s["column"]): (s["row_span"], s["column_span"]) for s in table["spans"]}
        parts = [f"<table><caption>Table {index}</caption><tbody>"]
        for row, values in enumerate(table["values"]):
            parts.append("<tr>")
            for column, value in enumerate(values):
                if value is None:
                    continue
                if not isinstance(value, str):
                    raise TypeError("Demo requires literal verified cell strings")
                rs, cs = spans.get((row, column), (1, 1))
                if any(type(v) is not int or not 1 <= v <= 4096 for v in (rs, cs)):
                    raise ValueError("Demo table span exceeds admission")
                parts.append(f'<td rowspan="{rs}" colspan="{cs}">{html.escape(value).replace(chr(10), "<br>")}</td>')
            parts.append("</tr>")
        fragments.append("".join(parts) + "</tbody></table>")
    return "".join(fragments) or "<p>No admitted tables.</p>"


def _quality(path: Path | None, *, run: Path, frozen: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Read optional already-verified offline evaluation data; never load reference files."""
    if path is None:
        return {}
    evaluation = json.loads(_read(path, MAX_INPUT_BYTES))
    if evaluation.get("config") != frozen["config"] or evaluation.get("manifest_sha256") != frozen["manifest_sha256"]:
        raise ValueError("Evaluation does not identify this frozen run")
    if evaluation.get("code_verification", {}).get("archive_hashes_verified") is not True:
        raise ValueError("Evaluation lacks retained code verification")
    if evaluation.get("report_sha256") is not None and evaluation["report_sha256"] != sha(
        (run / "report.json").read_bytes()
    ):
        raise ValueError("Evaluation report hash does not match this run")
    if evaluation.get("operational_pages") != report.get("complete_output_pages"):
        raise ValueError("Evaluation completion count does not match this run")
    pages = evaluation.get("page_scores", [])
    if len({page["id"] for page in pages}) != len(pages):
        raise ValueError("Evaluation has duplicate page scores")
    return {page["id"]: page for page in pages}


def build(
    manifest_path: Path, run: Path, output: Path, *, evaluation_path: Path | None = None, image_edge: int = 1024
) -> dict[str, Any]:
    """Verify a predefined complete screen and emit an ignored local gallery without inference."""
    import pylopdf

    if image_edge not in (512, 1024):
        raise ValueError("Demo image edge must be 512 or 1024")
    output = guard_path(output)
    if not output.is_relative_to(ARTIFACT_ROOT):
        raise ValueError("Gallery output must be under ignored bench/results/pdf-master-artifacts")
    manifest = json.loads(_read(manifest_path, MAX_INPUT_BYTES))
    frozen = json.loads(_read(run / "frozen.json", MAX_INPUT_BYTES))
    report = json.loads(_read(run / "report.json", MAX_INPUT_BYTES))
    if manifest.get("split") != "DEV" or not 1 <= len(manifest["pages"]) <= MAX_PAGES:
        raise ValueError("Gallery requires an explicit DEV screen of at most twenty pages")
    if report["config"] != frozen["config"]:
        raise ValueError("Run report configuration differs from frozen configuration")
    records = [{key: record[key] for key in FIELDS} for record in manifest["pages"]]
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)) or any(re.fullmatch(r"[A-Za-z0-9_-]{1,80}", ident) is None for ident in ids):
        raise ValueError("Gallery page IDs must be unique safe opaque names")
    frozen_records = {record["id"]: {key: record[key] for key in FIELDS} for record in frozen["records"]}
    if any(frozen_records.get(record["id"]) != record for record in records):
        raise ValueError("Screen source records differ from the frozen run")
    predictions = {prediction["id"]: prediction for prediction in report["results"]}
    if len(predictions) != len(report["results"]):
        raise ValueError("Run has duplicate page predictions")
    processor = frozen["config"].get("processor", "whole")
    code = verify_code(run, frozen, processor=processor)
    quality = _quality(evaluation_path, run=run, frozen=frozen, report=report)
    output.mkdir(parents=True, exist_ok=False)
    (output / "images").mkdir()
    (output / "outputs").mkdir()
    cards, metadata = [], []
    for record in records:
        ident = record["id"]
        pdf_path = Path(record["pdf_path"])
        if not pdf_path.is_absolute():
            raise ValueError("Source PDF paths must be absolute")
        pdf_path = guard_path(pdf_path)
        data = _read(pdf_path, MAX_INPUT_BYTES)
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Frozen source PDF hash changed")
        prediction = predictions.get(ident)
        verified = None
        if prediction is not None:
            result_path = run / f"{ident}-result.json"
            if result_path.exists():
                verified = verify_output(run, prediction, processor=processor)
            elif prediction.get("status") == "ok":
                raise ValueError("Successful page lacks its retained result")
        status = "missing" if prediction is None else prediction.get("status", "unknown")
        operational = verified is not None and verified["operational"]
        markdown, state = "", None
        if operational:
            markdown = _read(run / f"{ident}.md").decode()
            state = json.loads(_read(run / f"{ident}-structure.json"))
        with pylopdf.open(stream=data) as document:
            page = document[record["page_number"]]
            original_rotation = page.rotation
            if prediction is not None and processor not in {"vision", "vision_regions", "vision_multiscale", "hybrid"}:
                if "effective_rotation" in prediction:
                    page.set_rotation(prediction["effective_rotation"])
                elif prediction.get("rotation_normalized") or frozen["config"].get("normalize_rotation"):
                    page.set_rotation(0)
            png = page.render(scale=image_edge / max(page.rect.width, page.rect.height), background=(255, 255, 255))
            viewport = list(page.rect)
        (output / "images" / f"{ident}.png").write_bytes(png)
        provenance = (
            "model-transcribed; no source ownership"
            if processor in {"vision", "vision_regions", "vision_multiscale"}
            else (
                "mixed native-source/model-transcribed; original words accounted"
                if processor == "hybrid" and operational
                else "source-owned; complete retained-source conservation"
                if operational and verified is not None and verified["conserved"]
                else "no verified complete output"
            )
        )
        links = []
        for suffix in (".md", "-structure.json", "-result.json"):
            artifact = run / f"{ident}{suffix}"
            if artifact.exists():
                copied = _read(artifact)
                (output / "outputs" / artifact.name).write_bytes(copied)
                links.append(f'<a download href="outputs/{artifact.name}">{html.escape(artifact.name)}</a>')
        info = {
            "id": ident,
            "status": status,
            "processor": processor,
            "provenance": provenance,
            "pdf_sha256": record["pdf_sha256"],
            "page_number": record["page_number"],
            "original_rotation": original_rotation,
            "display_viewport": viewport,
            "complete_output_verified": bool(operational),
            "result_present": prediction is not None,
            "retained_result_present": (run / f"{ident}-result.json").exists(),
        }
        metadata.append(info)
        errors = (
            ""
            if prediction is None
            else html.escape(
                json.dumps(
                    {key: prediction[key] for key in ("error_type", "error", "error_stage") if key in prediction},
                    ensure_ascii=False,
                )
            )
        )
        scores = (
            ""
            if ident not in quality
            else f"<details><summary>Offline evaluation</summary><pre>{html.escape(json.dumps(quality[ident], ensure_ascii=False, indent=2))}</pre></details>"
        )
        cards.append(f"""<article id="{ident}"><h2>{html.escape(ident)} — {html.escape(status)}</h2>
<p>{html.escape(provenance)}</p><p class="error">{errors}</p><div class="grid">
<section><h3>Complete source page</h3><img src="images/{ident}.png" alt="Verified source page {ident}"></section>
<section><h3>Verified structured tables</h3>{_tables(state) if state else "<p>No verified complete table output.</p>"}
<details><summary>Exact retained Markdown</summary><pre>{html.escape(markdown) if operational else "Missing or failed complete output."}</pre></details>
<details><summary>Exact retained structure</summary><pre>{html.escape(json.dumps(state, ensure_ascii=False, indent=2)) if state else "Unavailable."}</pre></details>
<p>{" · ".join(links)}</p>{scores}</section></div><details><summary>Source and run provenance</summary><pre>{html.escape(json.dumps(info, indent=2))}</pre></details></article>""")
    content = (
        """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Verified PDF pipeline gallery</title><style>body{margin:24px;color:#202020;background:#f4f3ee;font:16px/1.5 system-ui,sans-serif}article{padding:20px;margin:24px 0;background:white;border:1px solid #aaa}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}section{min-width:0;overflow:auto}img{width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}table{border-collapse:collapse;margin:16px 0}td{border:1px solid #888;padding:6px;vertical-align:top}caption{text-align:left;font-weight:bold}.error{color:#8c1616}a{color:#164e9b}@media(max-width:850px){.grid{grid-template-columns:1fr}}</style>
<h1>Verified PDF pipeline gallery</h1><p>Complete predefined DEV screen, including failures and missing pages. Experimental opt-in output. This viewer performs no inference or network requests. Table values are escaped; retained Markdown is shown as literal code.</p>"""
        + "".join(cards)
        + "</html>"
    )
    (output / "index.html").write_text(content)
    summary = {
        "run_id": frozen["config"]["run_id"],
        "screen_manifest_sha256": sha(manifest_path.read_bytes()),
        "run_manifest_sha256": frozen["manifest_sha256"],
        "run_report_sha256": sha((run / "report.json").read_bytes()),
        "code_verification": code,
        "page_count": len(records),
        "pages": metadata,
        "scope": "All explicit screen pages; no output-quality filtering; optional evaluation loaded offline only",
    }
    write_json(output / "gallery.json", summary)
    return {"html": str(output / "index.html"), **summary}


def main() -> None:
    """Create a local gallery from an explicit fixed manifest and retained run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path)
    parser.add_argument("--image-edge", type=int, choices=(512, 1024), default=1024)
    args = parser.parse_args()
    print(
        json.dumps(
            build(args.manifest, args.run, args.output, evaluation_path=args.evaluation, image_edge=args.image_edge)
        )
    )


if __name__ == "__main__":
    main()
