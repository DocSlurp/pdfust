"""Necessary character availability keeps its optimistic limitations explicit."""

from bench.p003_availability_analysis import characters, necessary_counts


def test_per_cell_reuse_is_optimistic_but_aggregate_preserves_multiplicity() -> None:
    target = {"tables": [{"values": [["aa", "aa", "", None]]}]}
    bag = {"nonspace_character_bag": [["a", 2]], "word_count": 1}
    counts = necessary_counts(target, bag)
    assert counts["reference_cells"] == 3
    assert counts["independently_character_possible_cells"] == 3
    assert counts["all_cells_independently_possible_tables"] == 1
    assert counts["blank_reference_cells"] == 1
    assert counts["aggregate_missing_reference_characters"] == 2


def test_case_punctuation_and_literal_unicode_are_not_corrected() -> None:
    target = {"tables": [{"values": [["A", "—", "a"]]}]}
    counts = necessary_counts(target, {"nonspace_character_bag": [["a", 1], ["-", 1]], "word_count": 2})
    assert counts["independently_character_possible_cells"] == 1
    assert counts["character_impossible_cells"] == 2
    assert counts["all_cells_independently_possible_tables"] == 0


def test_nfc_and_freely_assembled_whitespace_only() -> None:
    assert characters("e\u0301\t a\n") == characters("é a")
    assert characters("ab") == characters("b a")  # Order deliberately ignored, not cell correctness.
