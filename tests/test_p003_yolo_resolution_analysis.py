"""Box acquisition metrics preserve multiplicity and exclude content matching."""

from bench.p003_yolo_resolution_analysis import box_counts


def test_duplicate_proposals_receive_extra_penalty() -> None:
    result = box_counts([[0, 0, 10, 10]], [[0, 0, 10, 10], [0, 0, 10, 10]], 0.5)
    assert result["matched"] == 1
    assert result["extra"] == 1
    assert result["missed"] == 0


def test_negative_proposal_counts_are_preserved() -> None:
    result = box_counts([], [[0, 0, 10, 10]], 0.1)
    assert result["negative_fp_page"] == 1
    assert result["extra"] == 1


def test_iou_sensitivity_does_not_change_proposals() -> None:
    expected, proposals = [[0, 0, 10, 10]], [[0, 0, 10, 5]]
    assert box_counts(expected, proposals, 0.5)["matched"] == 1
    assert box_counts(expected, proposals, 0.7)["matched"] == 0
    assert box_counts(expected, proposals, 0.7)["missed"] == 1
