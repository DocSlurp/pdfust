from bench.p003_boundary_ceiling import best_partition


def test_dynamic_program_preserves_three_row_limit_and_minimum_two_rows() -> None:
    graph = {
        "physical_rows": 4,
        "columns": 1,
        "groups": [
            {"start": start, "end": end, "values": [" ".join(str(r) for r in range(start, end))]}
            for start in range(4)
            for end in range(start + 1, min(4, start + 3) + 1)
        ],
    }
    result = best_partition(graph, {"row_count": 2, "col_count": 1, "values": [["0 1 2"], ["3"]]})
    assert result["strict_anchor_score"] == 2
    assert result["partition"] == [[0, 3], [3, 4]]
    result = best_partition(graph, {"row_count": 1, "col_count": 1, "values": [["0 1 2 3"]]})
    assert result["strict_anchor_score"] == 0
    assert result["logical_rows"] >= 2


def test_unavailable_edges_cannot_be_invented() -> None:
    graph = {
        "physical_rows": 3,
        "columns": 1,
        "groups": [{"start": start, "end": start + 1, "values": [str(start)]} for start in range(3)],
    }
    result = best_partition(graph, {"row_count": 2, "col_count": 1, "values": [["0 1"], ["2"]]})
    assert result["strict_anchor_score"] == 0
    assert result["partition"] == [[0, 1], [1, 2], [2, 3]]


def test_dp_matches_exhaustive_partitions() -> None:
    graph = {
        "physical_rows": 5,
        "columns": 1,
        "groups": [
            {"start": start, "end": end, "values": [" ".join(str(r) for r in range(start, end))]}
            for start in range(5)
            for end in range(start + 1, min(5, start + 3) + 1)
            if not (start <= 2 < end - 1)
        ],
    }
    reference = [["0 1"], ["2"], ["3 4"]]
    target = {"row_count": 3, "col_count": 1, "values": reference}
    partitions = [[]]
    complete = []
    while partitions:
        partition = partitions.pop()
        end = partition[-1]["end"] if partition else 0
        if end == 5:
            if len(partition) >= 2:
                complete.append(partition)
        else:
            partitions.extend([*partition, group] for group in graph["groups"] if group["start"] == end)
    score = max(
        sum(index < len(reference) and group["values"] == reference[index] for index, group in enumerate(partition))
        for partition in complete
    )
    assert best_partition(graph, target)["strict_anchor_score"] == score == 3
