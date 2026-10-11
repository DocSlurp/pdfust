"""Bounded root-owned subprocess queue for explicitly frozen extension arms."""

# ruff: noqa: PLR2004, S603
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from bench.p003_extension_run import ROOT, read
from bench.research_policy import P003_EXTENSION_CUTOFF
from bench.silver import write_json


def main() -> None:
    """Launch at most three independent model arms; preserve failed jobs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    if not args.run_hosted:
        parser.error("Hosted execution requires --run-hosted")
    manifest = read(args.manifest)
    output = args.manifest.parent
    with (output / (args.manifest.stem + "-queue-started.json")).open("x") as handle:
        handle.write(str(time.time()))
    pending = list(manifest["arms"])
    active, finished = [], []
    ledger_path = ROOT / "bench/results/pdf-master-artifacts/decisions/ledger.json"
    env = {
        **os.environ,
        "JEV_P003_TRANSPORT_SLOTS": "3",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    cap = manifest["starting_p003_accounted_usd"] + manifest["cap_additional_accounted_usd"]
    started = time.time()
    while pending or active:
        ledger = read(ledger_path)
        exposure = sum(e["accounted_usd"] for e in ledger["requests"] if e.get("tag", "").startswith("P003/"))
        reason = (
            "paid cutoff" if time.time() >= P003_EXTENSION_CUTOFF else "screen cap" if exposure + 0.9 > cap else None
        )
        if reason:
            finished.extend(
                {"run_id": a["config"]["run_id"], "status": "not_started", "reason": reason} for a in pending
            )
            pending = []
        while pending and len(active) < 3:
            arm = pending.pop(0)
            directory = Path(arm["directory"])
            # Gateway's existing transport holds the shared ledger during HTTP;
            # run it serially after OpenRouter to avoid blocked slots and unfair timing.
            if arm["config"]["provider"] == "vercel" and active:
                pending.insert(0, arm)
                break
            log = (directory / "runner.log").open("wb")
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "bench.p003_extension_run",
                    "run",
                    "--directory",
                    str(directory),
                    "--run-hosted",
                ],
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            active.append((process, log, arm, time.time()))
            if arm["config"]["provider"] == "vercel":
                break
        for entry in list(active):
            process, log, arm, arm_started = entry
            code = process.poll()
            if code is not None:
                log.close()
                active.remove(entry)
                finished.append(
                    {
                        "run_id": arm["config"]["run_id"],
                        "status": "finished" if code == 0 else "process_error",
                        "returncode": code,
                        "wall_seconds": time.time() - arm_started,
                    }
                )
        write_json(
            output / (args.manifest.stem + "-queue-progress.json"),
            {
                "observed_at": time.time(),
                "started_at": started,
                "pending": len(pending),
                "active": [a["config"]["run_id"] for _, _, a, _ in active],
                "finished": finished,
                "p003_accounted_usd": exposure,
                "additional_accounted_usd": exposure - manifest["starting_p003_accounted_usd"],
                "measurement": "Queue wall and ledger snapshots; each subprocess measures its own CPU/RSS",
            },
        )
        if pending or active:
            time.sleep(0.5)
    print(f"Queue finished: {len(finished)} arms")


if __name__ == "__main__":
    main()
