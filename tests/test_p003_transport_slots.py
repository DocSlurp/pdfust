"""Real CPU processes exercise slot waits without credentials, clients or requests."""

from pathlib import Path

import pytest
from bench.p003_client import transport_slot


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
