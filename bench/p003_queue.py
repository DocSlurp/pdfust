"""Root-owned serial P003 experiment queue with deadline and per-arm time bounds."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from bench.decision_hosted import ROOT
from bench.research_policy import P003_PAID_CUTOFF
from bench.silver import guard_path, write_json

MAX_ARMS = 64
MIN_START_SECONDS = 120


def main() -> None:  # noqa: C901, PLR0912 - explicit bounded lifecycle and interrupted-child cleanup.
    """Execute only declared p003_run arguments; never shell-evaluate a plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    git = shutil.which("git")
    if git is None:
        message = "Git is required for trusted source snapshots"
        raise RuntimeError(message)
    plan = json.loads(guard_path(args.plan).read_bytes())
    if not isinstance(plan, list) or not plan or len(plan) > MAX_ARMS:
        message = "Queue requires 1 through 64 explicit arms"
        raise ValueError(message)
    names = set()
    for arm in plan:
        name = arm["name"]
        if (
            not isinstance(name, str) or not name
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name)
        ):
            message = "Queue arm name must be a safe lowercase filename"
            raise ValueError(message)
        if (
            name in names or not isinstance(arm.get("arguments"), list)
            or any(not isinstance(v, str) for v in arm["arguments"])
        ):
            message = "Queue arm names must be unique and arguments must be literal strings"
            raise ValueError(message)
        if any(v in {"--output", "--manifest"} for v in arm["arguments"]):
            message = "Queue arguments cannot change the declared source or output location"
            raise ValueError(message)
        names.add(name)
    directory = guard_path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "logs").mkdir(exist_ok=True)
    (directory / "trusted-code").mkdir(exist_ok=True)
    status_path = directory / (args.plan.stem + "-status.json")
    if status_path.exists():
        message = "Queue status already exists; do not silently repeat an experiment"
        raise ValueError(message)
    statuses = []
    for arm in plan:
        remaining = P003_PAID_CUTOFF - time.time()
        if remaining < MIN_START_SECONDS:
            break
        output = directory / arm["name"]
        if output.exists():
            message = "Queue output exists; no automatic overwrite or retry"
            raise ValueError(message)
        files = subprocess.check_output(  # noqa: S603 - resolved local Git path and fixed arguments, no shell.
            [git, "ls-files", "bench/*.py"], cwd=ROOT, text=True,
        ).splitlines()
        trust = {Path(p).name: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
        write_json(directory / "trusted-code" / (arm["name"] + ".json"), trust)
        command = [sys.executable, "-m", "bench.p003_run", "--manifest", str(args.manifest.resolve()),
                   "--output", str(output.resolve()), *arm["arguments"]]
        started = time.time()
        status = {"name": arm["name"], "status": "running", "started_at": started, "command": command}
        statuses.append(status)
        write_json(status_path, {"plan": str(args.plan), "arms": statuses, "paid_cutoff": P003_PAID_CUTOFF})
        print(json.dumps({"arm": arm["name"], "status": "starting"}), flush=True)
        with (directory / "logs" / (arm["name"] + ".log")).open("w") as log:
            process = subprocess.Popen(  # noqa: S603 - fixed Python module and literal argv, no shell.
                command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
            try:
                code = process.wait(timeout=min(2400, remaining - 60))
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                os.killpg(process.pid, signal.SIGINT)
                try:
                    code = process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    code = process.wait()
                status["interrupted"] = True
        status.update(status="completed" if code == 0 else "failed", exit_code=code, wall_seconds=time.time() - started)
        write_json(status_path, {"plan": str(args.plan), "arms": statuses, "paid_cutoff": P003_PAID_CUTOFF})
        print(json.dumps({"arm": arm["name"], "status": status["status"], "exit_code": code}), flush=True)
        if status.get("interrupted"):
            break


if __name__ == "__main__":
    main()
