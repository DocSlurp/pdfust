"""CPU-only parallel scoring of one frozen prospective arm manifest."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from bench.p003_extension_run import read
from bench.p003_extension_score import load_frozen, score_run
from bench.pipeline_run import Resources
from bench.silver import sha, write_json


def score_arm(directory: str, corpus: str) -> dict[str, Any]:
    """Retain complete scored evidence and separate evaluation resource scope."""
    folder = Path(directory)
    report_path = folder / "report.json"
    if not report_path.exists():
        report_path = folder / "recovered-report-v1.json"
    destination = folder / "score-v1.json"
    if destination.exists():
        return {"directory": directory, "status": "retained", "score_sha256": sha(destination.read_bytes())}
    if not report_path.exists():
        return {"directory": directory, "status": "missing_report"}
    with Resources() as resources:
        frozen = load_frozen(Path(corpus))
        result = score_run(frozen, read(report_path))
    result["evaluation_resources"] = resources.summary()
    result["source_report_sha256"] = sha(report_path.read_bytes())
    write_json(destination, result)
    return {
        "directory": directory,
        "status": "scored",
        "score_sha256": sha(destination.read_bytes()),
        "strict_exact_pages": result["model_selected_only"]["strict"]["totals"]["exact_page"],
    }


def main() -> None:
    """Score only the explicit manifest's DEV rows; never discover target corpora."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    manifest = read(args.manifest)
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(score_arm, a["directory"], str(args.corpus)): a for a in manifest["arms"]}
        for job in as_completed(jobs):
            arm = jobs[job]
            try:
                row = job.result()
            except Exception as error:
                row = {
                    "directory": arm["directory"],
                    "status": "error",
                    "error": type(error).__name__ + ": " + str(error),
                }
            rows.append(row)
            write_json(
                args.manifest.with_name(args.manifest.stem + "-score-progress.json"),
                {"completed": len(rows), "intended": len(jobs), "results": rows},
            )
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
