"""Partial-table scoring cannot select successful rows from a declared cohort."""

from copy import deepcopy

import pytest
from bench.p003_partial_audit import selected_references


def test_partial_audit_requires_exact_complete_source_cohort() -> None:
    records = [
        {"id": name, "pdf_path": name + ".pdf", "pdf_sha256": name, "page_number": 0} for name in ("a", "b", "c")
    ]
    manifest = {
        "dataset_sha256": "dev-corpus",
        "pages": [{**record, "cohort": "natural" if index < 2 else "authored"} for index, record in enumerate(records)],
    }
    selected = {"split": "DEV", "dataset_sha256": "dev-corpus", "pages": records[:2]}
    refs = {"pages": [{"id": name} for name in ("a", "b", "c")]}
    assert selected_references(manifest, refs, selected, records[:2], "natural") == [{"id": "a"}, {"id": "b"}]
    with pytest.raises(ValueError, match="complete matched"):
        selected_references(manifest, refs, selected, records[:1], "natural")
    changed = deepcopy(selected)
    changed["pages"][0]["pdf_sha256"] = "changed-input"
    with pytest.raises(ValueError, match="complete matched"):
        selected_references(manifest, refs, changed, records[:2], "natural")
    with pytest.raises(ValueError, match="complete matched"):
        selected_references(manifest, refs, selected, records[:2], None)
    with pytest.raises(ValueError, match="references"):
        selected_references(manifest, {"pages": refs["pages"][:1]}, selected, records[:2], "natural")
