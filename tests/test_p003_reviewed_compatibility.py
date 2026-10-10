"""Reviewed administrative compatibility cannot change called helpers or corpus scope."""

import hashlib

import pytest
from bench import p003_reviewed_compatibility as compatibility


@pytest.fixture
def reviewed_pair(monkeypatch: pytest.MonkeyPatch) -> tuple[bytes, bytes]:
    old = b"CONSTANT = 16\ndef authenticate(x): return x\ndef run(x): return len(x) == 16\ndef main(): return run([])\n"
    new = (
        b"CONSTANT = 16\nMAX_EXPECTED_PAGES = 512\ndef authenticate(x): return x\n"
        b"def run(x): return len(x) <= MAX_EXPECTED_PAGES\ndef main(): return run([])\n"
    )
    monkeypatch.setattr(compatibility, "PRECOUNT_SHA256", hashlib.sha256(old).hexdigest())
    monkeypatch.setattr(compatibility, "COUNT_SHA256", hashlib.sha256(new).hexdigest())
    return old, new


def test_administrative_pair_only_accepts_original_implicit_sixteen(reviewed_pair: tuple[bytes, bytes]) -> None:
    old, new = reviewed_pair
    assert compatibility.reviewed_precount_helper(old, new, {}, [{}] * 16)
    assert not compatibility.reviewed_precount_helper(old, new, {"expected_pages": 16}, [{}] * 16)
    assert not compatibility.reviewed_precount_helper(old, new, {"expected_pages": 48}, [{}] * 48)


def test_called_helper_change_rejected_even_if_pair_digests_are_reviewed(
    reviewed_pair: tuple[bytes, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    old, new = reviewed_pair
    changed = new.replace(b"authenticate(x): return x", b"authenticate(x): return []")
    monkeypatch.setattr(compatibility, "COUNT_SHA256", hashlib.sha256(changed).hexdigest())
    assert not compatibility.reviewed_precount_helper(old, changed, {}, [{}] * 16)


def test_unreviewed_current_bytes_rejected(reviewed_pair: tuple[bytes, bytes]) -> None:
    old, new = reviewed_pair
    assert not compatibility.reviewed_precount_helper(old, new + b"# new edit\n", {}, [{}] * 16)
