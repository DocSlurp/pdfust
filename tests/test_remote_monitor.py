# ruff: noqa: ANN001, ANN201, ANN202, ANN204, D101, D102, D107 - mock process interface.
import json
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from bench.remote_monitor import TreeSampler, monitor


class MissingError(Exception):
    pass


class DeniedError(Exception):
    pass


class Process:
    def __init__(self, pid=10, created=1.0, cpu=2.0):
        self.pid = pid
        self.created = created
        self.cpu = cpu
        self.descendants = []
        self.running = True

    def create_time(self):
        return self.created

    def is_running(self):
        return self.running

    def status(self):
        return "running"

    def children(self, *, recursive):
        assert recursive
        return self.descendants

    def oneshot(self):
        return nullcontext()

    def cpu_times(self):
        return SimpleNamespace(user=self.cpu, system=0.0)

    def memory_info(self):
        return SimpleNamespace(rss=100)

    def num_threads(self):
        return 3


def runtime(root):
    return SimpleNamespace(
        Process=lambda _: root,
        NoSuchProcess=MissingError,
        AccessDenied=DeniedError,
        ZombieProcess=MissingError,
        STATUS_ZOMBIE="zombie",
    )


def test_cpu_identity_and_exited_child_conservation():
    root = Process()
    child = Process(11, cpu=4)
    root.descendants = [child]
    sampler = TreeSampler(10, runtime(root))
    first = sampler.sample(0)
    assert first["cpu_utilization_percent"] is None
    assert first["rss_sum_bytes"] == 200
    assert first["thread_count"] == 6
    root.cpu += 1
    child.cpu += 2
    second = sampler.sample(1)
    assert second["cpu_utilization_percent"] == 300
    assert second["observed_cpu_cumulative_seconds"] == 3
    root.descendants = [Process(11, created=2, cpu=20)]
    third = sampler.sample(2)
    assert third["observed_cpu_cumulative_seconds"] == 3
    root.descendants = []
    root.cpu += 1
    assert sampler.sample(3)["observed_cpu_cumulative_seconds"] == 4
    root.created = 3
    assert sampler.sample(4) is None


def test_missing_child_does_not_drop_root_sample():
    root = Process()
    child = Process(11)

    def refuse():
        raise MissingError

    child.create_time = refuse
    root.descendants = [child]
    result = TreeSampler(10, runtime(root)).sample(0)
    assert result["process_count"] == 1
    assert result["skipped_process_count"] == 1


def test_deadline_first_sample_and_retained_jsonl(tmp_path):
    now = [0.0]
    root = Process()

    def sleep(seconds):
        now[0] += seconds
        root.cpu += seconds

    output = tmp_path / "monitor.jsonl"
    assert monitor(10, output, 2.5, psutil_module=runtime(root), clock=lambda: now[0], sleep=sleep) == "deadline"
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert rows[0]["record"] == "metadata"
    samples = rows[1:-1]
    assert [row["elapsed_seconds"] for row in samples] == [0, 1, 2]
    assert rows[-1]["observed_cpu_cumulative_seconds"] == 2
    assert rows[-1]["elapsed_seconds"] == 2.5
    with pytest.raises(FileExistsError):
        monitor(10, output, 1, psutil_module=runtime(root))


def test_root_exit_stops_sampling(tmp_path):
    root = Process()
    now = [0.0]

    def sleep(seconds):
        now[0] += seconds
        root.running = False

    assert (
        monitor(10, tmp_path / "out", 10, psutil_module=runtime(root), clock=lambda: now[0], sleep=sleep)
        == "server_exited"
    )


@pytest.mark.parametrize(("deadline", "interval"), [(0, 1), (-1, 1), (float("inf"), 1), (1, float("nan"))])
def test_finite_admission(tmp_path, deadline, interval):
    with pytest.raises(ValueError, match="positive and finite"):
        monitor(10, tmp_path / "out", deadline, interval, psutil_module=runtime(Process()))
