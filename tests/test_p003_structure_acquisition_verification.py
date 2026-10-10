"""Reviewed source-only compatibility never accepts altered crop or density semantics."""

import pytest
from bench import p003_structure_acquisition_verification as verification
from bench.silver import sha


def test_unknown_historical_helper_cannot_authenticate_itself() -> None:
    archived = b"def _crop(): return 'same'\n"
    current = b"def _crop(): return 'different'\n"
    assert not verification.source_helper_matches("unknown.py", archived, current)
    assert not verification.source_helper_matches("generalization_vision_regions.py", archived, current)


def test_reviewed_unused_branch_keeps_crop_and_constants_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    archived = b"EDGE = 1024\ndef _crop(): return EDGE\ndef process(): return 'old'\n"
    current = b"EDGE = 1024\ndef _crop(): return EDGE\ndef process(): return 'new'\n"
    monkeypatch.setitem(
        verification.REVIEWED_SOURCE_HELPERS, "generalization_vision_regions.py", (sha(archived), {"process"})
    )
    assert verification.source_helper_matches("generalization_vision_regions.py", archived, current)
    assert not verification.source_helper_matches(
        "generalization_vision_regions.py", archived, current.replace(b"EDGE = 1024", b"EDGE = 512")
    )
    assert not verification.source_helper_matches(
        "generalization_vision_regions.py", archived, current.replace(b"return EDGE", b"return 0")
    )


def test_density_compatibility_allows_only_reviewed_literal_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    archived = b"CAP = 8\ndef _ocr_regions(): return CAP\ndef union_plans(): return 'old'\n"
    current = b"from copy import deepcopy\nfrom bench.silver import canonical, sha\n" + archived.replace(
        b"'old'", b"'new'"
    )
    monkeypatch.setitem(
        verification.REVIEWED_SOURCE_HELPERS, "p003_region_candidates.py", (sha(archived), {"union_plans"})
    )
    assert verification.source_helper_matches("p003_region_candidates.py", archived, current)
    assert not verification.source_helper_matches(
        "p003_region_candidates.py", archived, current.replace(b"canonical, sha", b"canonical as CAP, sha")
    )
