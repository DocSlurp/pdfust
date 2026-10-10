"""Source-only fresh confirmation selection and construction contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_confirmation_corpus as corpus
from bench.silver import sha

import pylopdf


def row(identifier: str, count: int) -> dict[str, object]:
    """Build source metadata without any natural answer fields."""
    return {
        "source_id": identifier,
        "source_parent_group": corpus.parent_group(identifier),
        "width": 100,
        "height": 200,
        "attributes": {"language": "en"},
        "category_counts": {"table": count},
    }


def test_selection_exact_disjoint_and_unknown_parent() -> None:
    """Keep quotas, exclude parents, reject unknown IDs, and ignore input ordering."""
    rows = [row(f"group-{density}-{i}_page_1.png", density) for density in range(3) for i in range(20)]
    rows += [row("unknown.png", 2), row("excluded_page_2.png", 2)]
    excluded = {"source_ids": ["excluded_page_1.png"], "source_parent_groups": ["excluded"]}
    first, diagnostics = corpus.select(rows, excluded)
    second, _ = corpus.select(list(reversed(rows)), excluded)
    assert first == second
    assert len(first) == 32
    assert [sum(r["category_counts"].get("table", 0) == n for r in first) for n in range(3)] == [8, 12, 12]
    assert len({r["source_parent_group"] for r in first}) == 32
    assert diagnostics["unknown_parent_rejected"] == 1
    assert not any(r["source_id"].startswith("excluded") for r in first)


def test_selection_refuses_insufficient_known_parent_quota() -> None:
    """Never relax parent separation to fill missing pages."""
    with pytest.raises(ValueError, match="Insufficient"):
        corpus.select([row("one_page_1.png", 2)], {"source_ids": [], "source_parent_groups": []})


def test_metadata_projection_discards_answers() -> None:
    """Changing natural answers cannot change selection metadata."""
    value = [
        {
            "page_info": {"image_path": "a.pdf_3.png", "width": 100, "height": 200, "page_attribute": {}},
            "layout_dets": [{"category_type": "table", "html": "secret", "text": "secret", "poly": [1, 2]}],
        }
    ]
    first = corpus.metadata(json.dumps(value).encode())
    value[0]["layout_dets"][0]["html"] = "different"
    assert first == corpus.metadata(json.dumps(value).encode())
    assert first[0]["source_parent_group"] == "a"
    assert "secret" not in json.dumps(first)


def test_exclusion_ocr_subset_is_required(tmp_path: Path) -> None:
    """An unmapped opaque OCR page cannot silently disappear from exclusions."""
    files = []
    for name, identifier in [("corpus-r2", "a"), ("ocr-evidence", "b")]:
        path = tmp_path / name / "manifest.json"
        path.parent.mkdir()
        path.write_text(json.dumps({"pages": [{"id": identifier, "pdf_sha256": "hash"}]}))
        files.append(path)
    with pytest.raises(ValueError, match="OCR selection"):
        corpus.exclusions(tuple(files))


def test_authored_new_designs_finite_nonoverlapping_slots() -> None:
    """All newly seeded PDFs open and their construction tilings are complete."""
    plans = corpus.plans()
    assert len(plans) == 16
    assert len({p["seed_sha256"] for p in plans}) == 16
    hashes = set()
    for plan in plans:
        data, targets = corpus.authored(plan)
        assert data == corpus.authored(plan)[0]
        hashes.add(sha(data))
        with pylopdf.Document(stream=data) as doc:
            assert len(doc) == 1
            assert "Trial" in doc[0].get_text()
        for table in targets:
            slots = []
            for span in table["spans"]:
                slots.extend(
                    (r, c)
                    for r in range(span["row"], span["row"] + span["row_span"])
                    for c in range(span["column"], span["column"] + span["column_span"])
                )
            assert len(slots) == len(set(slots)) == table["row_count"] * table["col_count"]
    assert len(hashes) == 16
