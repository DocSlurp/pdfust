"""Open document-OCR models served by vLLM on a rented GPU, scored like hosted vision arms.

The coordinator starts one vLLM OpenAI-compatible server per model on the
remote host and forwards it to a local port over SSH. This client renders the
same wild-v1 page images locally, sends them with each model's published
prompt, and writes per-page records in the `bench.wild_vision` format so
`bench.wild_vision.evaluate` scores them unchanged. No credentials are used:
the tunnel is the only route to the server.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pylopdf
from bench import wild_vision
from bench.silver import guard_path, write_json

# Published prompts and preferred long edges. Each model is a separately named arm.
MODELS: dict[str, dict[str, Any]] = {
    "allenai/olmOCR-2-7B-1025": {
        "long_edge": 1288,
        "prompt": (
            "Attached is one page of a document that you must process. Just return the plain text "
            "representation of this document as if you were reading it naturally. Convert equations to "
            "LateX and tables to HTML.\nIf there are any figures or charts, label them with the following "
            "markdown syntax ![Alt text describing the contents of the figure](page_startx_starty_width_height.png)"
            "\nReturn your output as markdown, with a front matter section on top specifying values for the "
            "primary_language, is_rotation_valid, rotation_correction, is_table, and is_diagram parameters."
        ),
    },
    "nanonets/Nanonets-OCR2-3B": {
        "long_edge": 1568,
        "prompt": (
            "Extract the text from the above document as if you were reading it naturally. Return the tables "
            "in html format. Return the equations in LaTeX representation. If there is an image in the "
            "document and image caption is not present, add a small description of the image inside the "
            "<img></img> tag; otherwise, add the image caption inside <img></img>. Watermarks should be "
            "wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in "
            "brackets. Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. Prefer using "
            "☐ and ☑ for check boxes."
        ),
    },
    "dots-studio/dots.ocr": {"long_edge": 1568, "prompt": "Extract the text content from this image."},
    # DeepSeek-OCR-2 has an 8,192-token context; vLLM rejects prompt + max_tokens above it with HTTP 400.
    # Its tokenizer registers <tr>/<td> as special tokens, so vLLM must keep them to preserve tables.
    "deepseek-ai/DeepSeek-OCR-2": {
        "long_edge": 1024, "prompt": "<|grounding|>Convert the document to markdown.", "max_tokens": 6144,
        "extra": {"skip_special_tokens": False},
    },
}


def chat(  # noqa: PLR0913 - one request and its serving options.
    port: int, model: str, url: str, prompt: str, *, max_tokens: int = 8192, extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    """One OpenAI-compatible chat completion against the tunnelled vLLM server."""
    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": url}},
            {"type": "text", "text": prompt},
        ]}],
        **(extra or {}),
    }
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:  # noqa: S310
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        message = f"HTTP {error.code}: {detail}"
        raise RuntimeError(message) from error


def run_arm(  # noqa: PLR0913 - one served arm and its inputs.
    model: str, port: int, levels: list[str], docs: list[str], output: Path, *, workers: int = 16
) -> dict[str, Any]:
    """Transcribe every page of the selected variants with one served model."""
    spec = MODELS[model]
    arm_dir = guard_path(output / model.replace("/", "-"))
    arm_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for doc_id in docs:
        for level in levels:
            pdf = wild_vision.WILD / "variants" / doc_id / f"{level}.pdf"
            if pdf.exists():
                with pylopdf.open(str(pdf)) as doc:
                    jobs.extend((doc_id, level, index) for index in range(len(doc)))
    lock = threading.Lock()
    rows: list[dict[str, Any]] = []
    start = time.time()

    def one(job: tuple[str, str, int]) -> None:
        doc_id, level, index = job
        target = arm_dir / f"{doc_id}--{level}--p{index}.json"
        if target.exists():
            with lock:
                rows.append(json.loads(target.read_text()))
            return
        record: dict[str, Any] = {"doc_id": doc_id, "level": level, "page": index, "model": model}
        original = wild_vision.LONG_EDGE
        wild_vision.LONG_EDGE = spec["long_edge"]
        try:
            url, image = wild_vision.page_image(wild_vision.WILD / "variants" / doc_id / f"{level}.pdf", index)
        finally:
            wild_vision.LONG_EDGE = original
        record["image"] = image
        began = time.time()
        try:
            result = chat(port, model, url, spec["prompt"], max_tokens=spec.get("max_tokens", 8192),
                          extra=spec.get("extra"))
            record.update(status="ok", markdown=result["choices"][0]["message"]["content"] or "",
                          usage=result.get("usage", {}), finish_reason=result["choices"][0].get("finish_reason"))
        except Exception as error:  # every failure is a retained outcome
            record.update(status="error", error=f"{type(error).__name__}: {str(error)[:300]}")
        record["client_seconds"] = time.time() - began
        write_json(target, record)
        with lock:
            rows.append(record)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, jobs))
    summary = {"model": model, "intended_pages": len(jobs), "status": {}, "wall_seconds": time.time() - start,
               "accounted_usd": 0.0, "cost_scope": "GPU rental billed separately; see the run record"}
    for row in rows:
        summary["status"][row["status"]] = summary["status"].get(row["status"], 0) + 1
    write_json(arm_dir / "summary.json", summary)
    return summary


def main() -> None:
    """Run one arm against a tunnelled server, or score retained outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=wild_vision.WILD / "vision-open-v1")
    parser.add_argument("--model", choices=sorted(MODELS))
    parser.add_argument("--port", type=int, default=18000)
    parser.add_argument("--levels", nargs="+", default=["L4_raster", "L6_phone_scan", "L7_photocopy"])
    parser.add_argument("--docs", nargs="*")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args()
    docs = args.docs or sorted(p.parent.name for p in (wild_vision.WILD / "docs").glob("*/truth.json"))
    if args.model:
        print(json.dumps(run_arm(args.model, args.port, args.levels, docs, args.output, workers=args.workers)))
    if args.score:
        for arm, result in wild_vision.evaluate(args.output).items():
            print(arm, json.dumps(result["levels"]))


if __name__ == "__main__":
    main()
