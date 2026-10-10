"""Real CPU processes exercise slot waits without credentials, clients or requests."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from bench.p003_client import transport_slot


def test_six_processes_share_only_three_pre_admission_slots(tmp_path: Path) -> None:
    code = (
        "import sys,time,json; from pathlib import Path; from bench.p003_client import transport_slot; "
        "p=Path(sys.argv[1]); i=sys.argv[2]; "
        "exec('with transport_slot(p,enabled=True,timeout=5) as waited:\\n"
        " start=time.monotonic(); time.sleep(0.3); end=time.monotonic();\\n"
        ' (p/(i+".json")).write_text(json.dumps([start,end,waited]))\')'
    )
    processes = [subprocess.Popen([sys.executable, "-c", code, str(tmp_path), str(i)]) for i in range(6)]  # noqa: S603 - fixed test code.
    assert all(p.wait(timeout=10) == 0 for p in processes)
    intervals = [json.loads((tmp_path / f"{i}.json").read_text()) for i in range(6)]
    events = sorted([(a, 1) for a, _b, _w in intervals] + [(b, -1) for _a, b, _w in intervals])
    active = peak = 0
    for _at, delta in events:
        active += delta
        peak = max(peak, active)
    assert peak == 3
    assert active == 0
    assert any(waited > 0.1 for _a, _b, waited in intervals)


def test_slot_is_released_after_exception_and_disabled_mode_touches_nothing(tmp_path: Path) -> None:
    missing = tmp_path / "never-created"
    with transport_slot(missing) as elapsed:
        assert elapsed == 0
    assert not missing.exists()
    message = "mock"
    with pytest.raises(ValueError, match="mock"), transport_slot(tmp_path, enabled=True):
        raise ValueError(message)
    with transport_slot(tmp_path, enabled=True, timeout=0.1) as elapsed:
        assert elapsed < 0.1
