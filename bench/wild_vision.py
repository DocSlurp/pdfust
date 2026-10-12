"""Hosted vision-model page transcription on wild-v1 raster variants.

Each model is a separately named arm. A page image (white background, long edge
1568 px, JPEG quality 90) is sent once through the shared P003 ledger client
with a strict JSON schema whose only field is the page Markdown. Failures stop
that arm and stay in the intended-page denominator. Scores reuse the wild-v1
audit functions: text bigram F1 against the native truth, recall of text that
exists only in images, and best-match table cell recall from Markdown tables.
"""

# ruff: noqa: PLR2004, EM101, TRY003
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image

import pylopdf
from bench import wild_corpus as wild
from bench.silver import guard_path, sha, write_json

ROOT = Path(__file__).resolve().parents[1]
WILD = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
TAG_PREFIX = "P003/extension-v1-vision-"
LONG_EDGE = 1568
MAX_TOKENS = 8192
RESERVATION = 0.3
INSTRUCTIONS = (
    "Transcribe this document page into GitHub-flavored Markdown. Keep the reading order a person "
    "would use. Use #/## headings for headings, - or 1. for lists, and Markdown tables for every "
    "table, with one row per table row and empty cells left empty. Include all visible text, "
    "including text inside screenshots, charts and photos when legible. Do not summarize, translate, "
    "correct or add anything. Return only the JSON object."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "object",
            "properties": {
                "q0": {
                    "type": "object",
                    "properties": {"markdown": {"type": "string"}},
                    "required": ["markdown"],
                    "additionalProperties": False,
                }
            },
            "required": ["q0"],
            "additionalProperties": False,
        }
    },
    "required": ["answers"],
    "additionalProperties": False,
}


def page_image(pdf: Path, index: int) -> tuple[str, dict[str, Any]]:
    """Render one page on white to a JPEG data URL with a 1568 px long edge."""
    with pylopdf.open(str(guard_path(pdf))) as doc:
        page = doc[index]
        width, height = page.rect.width, page.rect.height
        scale = LONG_EDGE / max(width, height)
        png = page.render(scale=scale)
    image = Image.open(io.BytesIO(png)).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    data = buffer.getvalue()
    return (
        "data:image/jpeg;base64," + base64.b64encode(data).decode(),
        {"width": image.width, "height": image.height, "jpeg_sha256": sha(data), "jpeg_bytes": len(data)},
    )


def body(model: str, url: str, page: int, pages: int) -> dict[str, Any]:
    """One strict-schema chat request for one page image."""
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "provider": {"require_parameters": True, "allow_fallbacks": False},
        "messages": [
            {"role": "system", "content": INSTRUCTIONS},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Page {page + 1} of {pages}."},
                    {"type": "image_url", "image_url": {"url": url}},
                ],
            },
        ],
        "response_format": {"type": "json_schema", "json_schema": {"name": "page_markdown", "strict": True,
                                                                   "schema": SCHEMA}},
    }


def parse_markdown(result: dict[str, Any]) -> str:
    """Extract answers.q0.markdown from a chat completion."""
    content = result["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    match = re.search(r"\{.*\}", content, re.DOTALL)
    payload = json.loads(match.group(0) if match else content)
    markdown = payload["answers"]["q0"]["markdown"]
    if not isinstance(markdown, str):
        raise TypeError("markdown must be a string")
    return markdown


def markdown_tables(markdown: str) -> list[list[list[str]]]:
    """Parse pipe tables into cell matrices, dropping the separator row."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in [*markdown.splitlines(), ""]:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.count("|") >= 2:
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell):
                current.append([re.sub(r"<br\s*/?>", " ", cell) for cell in cells])
            continue
        if current:
            tables.append(current)
            current = []
    return tables


def plain_text(markdown: str) -> str:
    """Strip Markdown syntax so text scoring compares content, not markup."""
    text = re.sub(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"[|#*_`>]", " ", text)
    text = re.sub(r"^\s*(?:[-+]|\d+\.)\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)


def score(truth: dict[str, Any], markdown: str) -> dict[str, Any]:
    """Score one document's concatenated page Markdown with the wild-v1 metrics."""
    text = plain_text(markdown)
    reference = wild.truth_text(truth)
    images = wild.image_text(truth)
    tables = wild.table_scores(truth, markdown_tables(markdown))
    return {
        "text": wild.bigram_f1(reference, text),
        "image_only_text_recovered": wild.bigram_f1(images, text)["recall"] if images else None,
        "tables": tables,
        "scripts": wild.script_recall(reference, text),
    }


def run_arm(model: str, levels: list[str], docs: list[str], output: Path, *, workers: int = 3) -> dict[str, Any]:
    """Transcribe every page of the selected variants with one model."""
    from bench.p003_client import P003ConcurrentClient  # noqa: PLC0415 - paid transport only when running.

    os.environ.setdefault("JEV_P003_TRANSPORT_SLOTS", "3")
    client = P003ConcurrentClient(ROOT)
    arm = model.replace("/", "-")
    arm_dir = guard_path(output / arm)
    arm_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for doc_id in docs:
        for level in levels:
            pdf = WILD / "variants" / doc_id / f"{level}.pdf"
            if not pdf.exists():
                continue
            with pylopdf.open(str(pdf)) as doc:
                pages = len(doc)
            jobs.extend((doc_id, level, index, pages) for index in range(pages))
    lock = threading.Lock()
    rows: list[dict[str, Any]] = []
    start = time.time()

    def one(job: tuple[str, str, int, int]) -> None:
        doc_id, level, index, pages = job
        record: dict[str, Any] = {"doc_id": doc_id, "level": level, "page": index, "model": model}
        target = arm_dir / f"{doc_id}--{level}--p{index}.json"
        if target.exists():
            record.update(json.loads(target.read_text()))
            with lock:
                rows.append(record)
            return
        if client.stopped:
            record["status"] = "not_attempted"
            with lock:
                rows.append(record)
            return
        url, image = page_image(WILD / "variants" / doc_id / f"{level}.pdf", index)
        record["image"] = image
        began = time.time()
        try:
            response = client.request(
                body(model, url, index, pages),
                tag=f"{TAG_PREFIX}{arm}/{doc_id}/{level}/p{index}",
                max_body_bytes=750_000,
                reservation_usd=RESERVATION,
            )
            record.update(
                status="ok",
                markdown=parse_markdown(response["result"]),
                usage=response["result"].get("usage", {}),
                entry={k: response["entry"].get(k) for k in ("index", "accounted_usd", "cost_status",
                                                              "provider_reported_usd", "served_model", "provider")},
            )
        except Exception as error:
            record.update(status="error", error=f"{type(error).__name__}: {str(error)[:300]}")
        record["client_seconds"] = time.time() - began
        write_json(target, record)
        with lock:
            rows.append(record)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, jobs))
    summary = {"model": model, "intended_pages": len(jobs), "status": {}, "wall_seconds": time.time() - start}
    for row in rows:
        summary["status"][row["status"]] = summary["status"].get(row["status"], 0) + 1
    summary["accounted_usd"] = sum((row.get("entry") or {}).get("accounted_usd") or 0 for row in rows)
    write_json(arm_dir / "summary.json", summary)
    return summary


def evaluate(output: Path) -> dict[str, Any]:
    """Score every arm per document and level; failed pages contribute no text."""
    results: dict[str, Any] = {}
    for arm_dir in sorted(p for p in guard_path(output).iterdir() if p.is_dir()):
        pages: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for path in arm_dir.glob("*--p*.json"):
            row = json.loads(path.read_text())
            pages.setdefault((row["doc_id"], row["level"]), []).append(row)
        per_level: dict[str, list[dict[str, Any]]] = {}
        for (doc_id, level), rows in sorted(pages.items()):
            rows.sort(key=lambda row: row["page"])
            truth = json.loads((WILD / "docs" / doc_id / "truth.json").read_text(encoding="utf-8"))
            markdown = "\n\n".join(row.get("markdown", "") for row in rows if row.get("status") == "ok")
            item = {"doc_id": doc_id, "failed_pages": sum(row.get("status") != "ok" for row in rows),
                    **score(truth, markdown)}
            per_level.setdefault(level, []).append(item)
        summary = {}
        for level, items in per_level.items():
            tables = [t for item in items for t in item["tables"]]
            summary[level] = {
                "documents": len(items),
                "failed_pages": sum(item["failed_pages"] for item in items),
                "text_f1": sum(item["text"]["f1"] or 0 for item in items) / len(items),
                "image_text_recall": _mean([item["image_only_text_recovered"] for item in items
                                            if item["image_only_text_recovered"] is not None]),
                "tables": len(tables),
                "table_exact": sum(bool(t.get("exact")) for t in tables),
                "table_cell_recall": _mean([t["cell_recall"] for t in tables]),
            }
        results[arm_dir.name] = {"levels": summary, "documents": per_level}
    write_json(guard_path(output) / "scores.json", results)
    return results


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def main() -> None:
    """Run arms (paid; requires --run-hosted) and/or score retained outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=WILD / "vision-v1")
    parser.add_argument("--models", nargs="*", default=[])
    parser.add_argument("--levels", nargs="+", default=["L4_raster", "L6_phone_scan", "L7_photocopy"])
    parser.add_argument("--docs", nargs="*")
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args()
    docs = args.docs or sorted(p.parent.name for p in (WILD / "docs").glob("*/truth.json"))
    if args.models and not args.run_hosted:
        parser.error("hosted transcription requires --run-hosted")
    for model in args.models:
        print(json.dumps(run_arm(model, args.levels, docs, args.output)), flush=True)
    if args.score:
        for arm, result in evaluate(args.output).items():
            print(arm, json.dumps(result["levels"]))


if __name__ == "__main__":
    main()
