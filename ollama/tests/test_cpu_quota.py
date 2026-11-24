"""The CPU budget the container holds, and the thread count that follows from it."""

from pathlib import Path

from cpu_quota import (
    THREADS_ENV,
    CpuQuota,
    calculate_threads,
    cap_parallelism_to_quota,
    parse_cpu_max,
    plan_thread_environment,
    read_cpu_quota,
)


# --- Reading the quota ---
def test_the_quota_is_read_as_cores_and_an_unlimited_one_as_nothing() -> None:
    """`cpu.max` is `<quota> <period>` in microseconds, or `max` for no limit."""
    assert parse_cpu_max("1000000 100000\n") == 10
    assert parse_cpu_max("max 100000\n") is None
    assert parse_cpu_max("garbage\n") is None


def test_cgroup_v1_is_read_when_v2_is_absent(tmp_path: Path) -> None:
    """A v1 host spells the same budget over two files."""
    cpu = tmp_path / "fs" / "cgroup" / "cpu"
    cpu.mkdir(parents=True)
    (cpu / "cpu.cfs_quota_us").write_text("1000000\n", encoding="utf-8")
    (cpu / "cpu.cfs_period_us").write_text("100000\n", encoding="utf-8")

    assert read_cpu_quota(tmp_path).cores == 10


def test_no_cgroup_files_at_all_reads_as_unlimited(tmp_path: Path) -> None:
    """Nothing to read is not a reason to clamp an unconstrained host."""
    assert read_cpu_quota(tmp_path).cores is None


# --- What follows from it ---
def test_threads_follow_the_quota_rather_than_the_visible_cpus() -> None:
    """The defect: 192 visible cores inside a 10-core quota started 192 threads."""
    assert calculate_threads(quota_cores=10, visible_cpus=192) == 9


def test_a_quota_below_the_headroom_still_leaves_one_thread() -> None:
    """Subtracting headroom must not reach zero threads on a one-core pod."""
    assert calculate_threads(quota_cores=1, visible_cpus=8) == 1
    assert calculate_threads(quota_cores=0.5, visible_cpus=8) == 1


def test_an_operator_thread_count_outranks_the_quota() -> None:
    """`ollama.extraEnv` has the last word, as it does for the parallelism."""
    plan = plan_thread_environment(
        {THREADS_ENV: "4"}, CpuQuota(cores=10, detail="test"), visible_cpus=192
    )

    assert plan.threads is None


def test_an_unconstrained_container_is_left_to_llama_cpp() -> None:
    """Without a quota llama.cpp's own sizing is right, and must not be overridden."""
    plan = plan_thread_environment(
        {}, CpuQuota(cores=None, detail="test"), visible_cpus=8
    )

    assert plan.threads is None


def test_the_slot_count_is_held_to_the_quota() -> None:
    """A memory-sized estimate cannot run more at once than the quota allows."""
    assert cap_parallelism_to_quota(16, CpuQuota(cores=10, detail="test")) == 10
    assert cap_parallelism_to_quota(4, CpuQuota(cores=10, detail="test")) == 4
    assert cap_parallelism_to_quota(16, CpuQuota(cores=None, detail="test")) == 16
