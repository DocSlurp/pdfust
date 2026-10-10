"""Explicit detector inference size must reach the acknowledged CPU worker."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from bench import p003_run
from bench.pipeline_layout_detector import LayoutDetector


@pytest.mark.parametrize("size", [1024, 1280])
def test_worker_receives_and_acknowledges_size(tmp_path: Path, size: int) -> None:
    model, script = tmp_path / "weights", tmp_path / "worker.py"
    model.write_bytes(b"fake weights")
    script.write_text("""import json, sys
size = int(sys.argv[sys.argv.index('--image-size') + 1])
print(json.dumps({'type':'ready','device':'cpu','configuration':{'imgsz':size}}), flush=True)
for line in sys.stdin:
    print(json.dumps({'type':'result','image_size':[100,200],'boxes':[]}), flush=True)
""")
    with LayoutDetector(model=model, python=Path(sys.executable), worker_script=script, image_size=size) as worker:
        assert worker.initialization["configuration"]["imgsz"] == size
        assert worker.detect(b"synthetic frame", viewport=[0, 0, 100, 200])["boxes"] == []
    assert worker.process.poll() is not None


def test_worker_cannot_silently_use_wrong_resolution(tmp_path: Path) -> None:
    model, script = tmp_path / "weights", tmp_path / "worker.py"
    model.write_bytes(b"fake weights")
    script.write_text("import json\n"
                      "print(json.dumps({'type':'ready','device':'cpu','configuration':{'imgsz':640}}),flush=True)\n")
    with pytest.raises(RuntimeError, match="did not acknowledge"):
        LayoutDetector(model=model, python=Path(sys.executable), worker_script=script, image_size=1280)


@pytest.mark.parametrize("size", [True, 0, 512, 2048, 1024.0])
def test_resolution_rejected_before_worker_or_file_access(size: Any) -> None:  # noqa: ANN401 - invalid boundary types.
    with pytest.raises(ValueError, match="inference size"):
        LayoutDetector(model=Path("/does-not-exist"), image_size=size)


def test_cli_freezes_explicit_resolution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    observed: dict[str, Any] = {}

    def run(_manifest: Path, _output: Path, config: dict[str, Any]) -> dict[str, Any]:
        observed.update(config)
        return {}

    monkeypatch.setattr(p003_run.pipeline_run, "run", run)
    monkeypatch.setattr(sys, "argv", ["p003_run", "--manifest", str(tmp_path / "manifest.json"),
                                    "--output", str(tmp_path / "output"),
                                    "--detector-inference-size", "1280", "--preset", "ordinal"])
    p003_run.main()
    assert observed["detector_inference_size"] == 1280
