"""Frozen image-only retrieval DEV comparison; hosted execution is opt-in."""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path
from typing import Any

from bench.decision_context_run import wave_admission
from bench.decision_hosted import ARTIFACTS, EMBEDDING_MODELS, DecisionClient, checkpoint, exclusive_lock
from bench.decision_images import ImageCache, digest, image_part
from bench.decision_retrieval import (
    evaluate,
    image_embedding_body,
    literal_baseline,
    query_embedding_body,
    retrieval_cases,
)

CONDITIONS = ("page128", "page512", "oracle-roi512")


def parse_embeddings(result: dict[str, Any], count: int) -> list[list[float]]:
    """Require one finite nonempty vector per independent input, with exact indexes."""
    rows = result.get("data")
    if not isinstance(rows, list) or len(rows) != count:
        message = "Embedding result count differs from independent input count"
        raise ValueError(message)
    output: dict[int, list[float]] = {}
    for row in rows:
        index = row.get("index")
        vector = row.get("embedding")
        if type(index) is not int or not 0 <= index < count or index in output:
            message = "Embedding indexes are missing, repeated or out of range"
            raise ValueError(message)
        if (
            not isinstance(vector, list)
            or not vector
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in vector)
        ):
            message = "Embedding vector must contain finite numeric elements"
            raise ValueError(message)
        output[index] = vector
    return [output[i] for i in range(count)]


def run(models: list[str], *, hosted: bool) -> dict[str, Any]:
    """Freeze complete cases/config before calls; no response-dependent tuning."""
    cases = retrieval_cases()
    cache = ImageCache(ARTIFACTS / "images")
    client = DecisionClient() if hosted else None
    directory = ARTIFACTS / "retrieval"
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {
        "split": "DEV, authored synthetic controls; not independent confirmation",
        "models": models,
        "conditions": CONDITIONS,
        "query_format": "Gemini documented search prefix; others raw",
        "queries": cases["queries"],
        "documents": [
            {k: v for k, v in d.items() if k != "pdf_bytes"}
            | {"pdf_sha256": hashlib.sha256(d["pdf_bytes"]).hexdigest()}
            for d in cases["documents"]
        ],
        "code_hashes": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), Path("bench/decision_retrieval.py"), Path("bench/decision_images.py"))
        },
    }
    key = digest(manifest)
    manifest_path = directory / f"manifest-{key}.json"
    checkpoint(manifest_path, manifest)
    report: dict[str, Any] = {
        "manifest_sha256": key,
        "manifest_path": str(manifest_path),
        "baseline": literal_baseline(cases),
        "cohorts": [],
    }
    for model in models:
        queries = [q["text"] for q in cases["queries"]]
        if model == "google/gemini-embedding-2":
            queries = ["task: search result | query: " + q for q in queries]
        query_body = query_embedding_body(model, queries)
        if client is None:
            continue
        wave_admission()
        response = client.request(query_body, tag="embedding/queries/" + model)
        query_vectors = dict(
            zip((q["id"] for q in cases["queries"]), parse_embeddings(response["result"], len(queries)), strict=True)
        )
        for condition in CONDITIONS:
            cohort: dict[str, Any] = {
                "model": model,
                "condition": condition,
                "documents": [],
                "query_entry": response["entry"],
            }
            vectors = {}
            for doc in cases["documents"]:
                box = doc["bbox"] if condition.startswith("oracle") else [0, 0, 612, 792]
                crop = cache.crop(doc["pdf_bytes"], box, edge=128 if condition == "page128" else 512, grayscale=False)
                body = image_embedding_body(model, [image_part(crop)["image_url"]["url"]])
                wave_admission()
                result = client.request(body, tag=f"embedding/{model}/{condition}/{doc['id']}")
                vector = parse_embeddings(result["result"], 1)[0]
                vectors[doc["id"]] = vector
                item = {
                    "id": doc["id"],
                    "entry": result["entry"],
                    "usage": result["result"].get("usage", {}),
                    "image": {k: v for k, v in crop.items() if k != "data"},
                    "replayed": result["replayed"],
                }
                cohort["documents"].append(item)
                checkpoint(directory / f"{model.split('/')[-1]}-{condition}-progress.json", cohort)
            cohort["metrics"] = evaluate(vectors, query_vectors, cases)
            report["cohorts"].append(cohort)
            checkpoint(directory / "results.json", report)
            print(model, condition, {k: v for k, v in cohort["metrics"].items() if k != "rows"}, flush=True)
    checkpoint(directory / "results.json", report)
    return report


def main() -> None:
    """Run two admitted multimodal embedders with explicitly authorized hosted flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", choices=EMBEDDING_MODELS, default=list(EMBEDDING_MODELS[:2]))
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(ARTIFACTS / "run.lock"):
        run(args.models, hosted=args.run_hosted)


if __name__ == "__main__":
    main()
