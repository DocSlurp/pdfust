"""Scoring helpers for the wild-v1 DEV corpus audit."""

from __future__ import annotations

from bench import wild_corpus as wild

TRUTH = {
    "metadata": {"title": "Invoice"},
    "blocks": [
        {"kind": "heading", "level": 1, "text": "Facture n° 2026-014"},
        {"kind": "paragraph", "text": "Montant dû : 1 234,56 € — ﬁnal"},
        {"kind": "table", "id": "t1", "rendering": "ruled", "header_rows": 1,
         "values": [["Item", "Prix"], ["Café", "4,50 €"]], "spans": []},
        {"kind": "table", "id": "t2", "rendering": "screenshot", "header_rows": 1,
         "values": [["Hidden", "Only pixels"]], "spans": []},
        {"kind": "figure", "id": "f1", "figure_kind": "photo", "caption": "東京の夜",
         "text_in_image": ["EXIT"]},
    ],
}


def test_truth_text_separates_native_and_pixel_only_content() -> None:
    native = wild.truth_text(TRUTH)
    assert "Café" in native
    assert "東京" in native
    assert "Only pixels" not in native
    assert "EXIT" not in native
    pixels = wild.image_text(TRUTH)
    assert "Only pixels" in pixels
    assert "EXIT" in pixels


def test_bigram_f1_is_order_insensitive_and_handles_empty() -> None:
    assert wild.bigram_f1("abc def", "def abc")["recall"] == 1.0
    assert wild.bigram_f1("", "x")["f1"] is None
    assert wild.bigram_f1("abcd", "")["f1"] == 0.0


def test_feature_survival_and_nfkc_scripts() -> None:
    reference = wild.truth_text(TRUTH)
    flattened = reference.replace(" ", " ").replace("ﬁ", "fi")
    features = wild.feature_survival(reference, flattened)
    assert features["nbsp"]["exact_kept"] == 0
    assert features["ligature"]["exact_kept"] == 0
    assert features["currency"]["exact_kept"] == features["currency"]["expected"]
    scripts = wild.script_recall(reference, flattened)
    assert scripts["CJK"]["exact"] == 1.0
    decomposed = wild.script_recall("Café", "Café")
    assert decomposed["LATIN"]["exact"] == 0.0
    assert decomposed["LATIN"]["nfkc"] == 1.0


def test_table_scores_best_match_ignores_screenshot_tables() -> None:
    scores = wild.table_scores(TRUTH, [[["Item", "Prix"], ["Café", "4,50 €"]], [["x"]]])
    assert len(scores) == 1
    assert scores[0]["exact"] is True
    assert wild.table_scores(TRUTH, [])[0]["matched"] is False
