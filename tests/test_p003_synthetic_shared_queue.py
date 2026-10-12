"""Source-only plan preparation and own-process queue adaptation, never hosted calls."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from bench import p003_synthetic_relations_multi_run as runner
from bench import p003_synthetic_shared_queue as driver

MAIN = Path("/home/dan/code/oss/pylopdf")
ARTIFACTS = MAIN / "bench/results/pdf-master-artifacts/pipeline-p003"
POOL = ARTIFACTS / "synthetic-micro-relations-v2"
SOURCE_MAP = ARTIFACTS / "trusted-code/synthetic-micro-relations-v2.json"


@pytest.fixture
def core() -> ModuleType:
    spec = importlib.util.spec_from_file_location("owned_test_current_queue", MAIN / "bench/p003_parallel.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dirty_runtime_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "bench").mkdir()
    originals = {name: (MAIN / "bench" / name).read_bytes() for name in (*runner.CODE_FILES, "p003_parallel.py")}
    for name, raw in originals.items():
        (tmp_path / "bench" / name).write_bytes(raw)
    monkeypatch.setattr(driver.subprocess, "check_output", lambda argv, **_: originals[argv[-1].split("bench/")[1]])
    assert len(driver.runtime_authority(tmp_path)) == 25
    (tmp_path / "bench" / runner.CODE_FILES[0]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="Dirty runtime"):
        driver.runtime_authority(tmp_path)


