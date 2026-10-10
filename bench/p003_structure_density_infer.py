"""CPU-only inference wrapper for frozen source-line/gap density proposals."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bench import p003_structure_geometry as geometry


def infer(manifest: Path, model_directory: Path, output: Path) -> dict[str, Any]:
    """Reuse exact pinned CPU forward/project logic while preserving original receipts."""
    if output.exists():
        raise ValueError("Choose a fresh inference directory; existing outputs are frozen")
    prepared = json.loads(manifest.read_bytes())
    if prepared["acquisition_arm"] != "density" or prepared["code_sha256"][Path(__file__).name] != geometry.digest(
        Path(__file__).read_bytes()
    ):
        raise ValueError("Unreviewed acquisition inference wrapper")
    report = geometry.infer(manifest, model_directory, output, threads=2)
    original = (output / "report.json").read_bytes()
    (output / "inference-report-original.json").write_bytes(original)
    report.update(
        {
            "acquisition_arm": prepared["acquisition_arm"],
            "conditional_scope": "bounded residual source-line/gap crops; no semantic gate; raw overlaps retained",
            "original_inference_report_sha256": geometry.digest(original),
            "inference_wrapper_sha256": geometry.digest(Path(__file__).read_bytes()),
            "intended_pages": len(prepared["pages"]),
            "intended_crops": sum(len(p["crops"]) for p in prepared["pages"]),
        }
    )
    for page in report["pages"]:
        if not page["crops"]:
            page["status"] = "no_owned_crop"
    (output / "report.json").write_bytes(geometry.encode(report))
    (output / "frozen-wrapper.py").write_bytes(Path(__file__).read_bytes())
    return report


def main() -> None:
    """Run only local pinned CPU weights, always with two bounded threads."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = infer(args.manifest, args.model_directory, args.output)
    print(
        json.dumps({"arm": result["acquisition_arm"], "pages": len(result["pages"]), "resources": result["resources"]})
    )


if __name__ == "__main__":
    main()
