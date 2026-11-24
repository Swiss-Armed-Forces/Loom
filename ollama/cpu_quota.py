"""What CPU budget this container holds, and what follows from it.

llama.cpp sizes its thread pool from the CPUs the host has. It honours neither the
cgroup CPU quota nor a cpuset, so inside a limited container it starts one compute
thread per host core: on a 192-core node under a ten-core limit, 192 threads spin-wait
on each other and every CFS period is throttled, which costs roughly thirty times the
throughput rather than a few percent.

Nothing here is tuning. It is the budget the kernel already enforces, read so that the
thread count can be told what the runner cannot work out for itself. Upstream
https://github.com/ollama/ollama/issues/17916
is open for the detection this stands in
for.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Compute threads the container leaves unclaimed, for ollama's own Go runtime and for
# the kernel. One is enough: the binary is built with a Go that sizes GOMAXPROCS from
# the cgroup quota itself, so the Go side is not competing for a thread this has to
# reserve on its behalf.
CPU_QUOTA_HEADROOM = 1
MIN_THREADS = 1

# Parameterised the way the wrapper's other probes are, so the readers can be pointed
# at a fixture tree and tested without patching anything.
SYSFS_ROOT = Path("/sys")

# llama.cpp's own variable, read by the argument parser ollama links in as
# `libllama-common.so`, not by ollama's configuration layer: `ollama serve --help`
# documents `LLAMA_ARG_FIT` and `LLAMA_ARG_FIT_TARGET` of that table and no more. It is
# the only knob that reaches the runner for every endpoint -- `options.num_thread`, the
# one ollama documents, is accepted by `POST /v1/systemone` and discarded.
# `LLAMA_ARG_THREADS_BATCH` is not in that table at all; llama.cpp defaults the batch
# count to this one.
THREADS_ENV = "LLAMA_ARG_THREADS"


@dataclass(frozen=True)
class CpuQuota:
    """The CPU budget the container's cgroup enforces, in cores.

    `cores` of None means nothing is enforced, which is a different answer from "one
    core": llama.cpp's own sizing is right on an unconstrained host and is left alone
    there.
    """

    cores: float | None
    detail: str


@dataclass(frozen=True)
class ThreadPlan:
    """How many compute threads llama.cpp should run.

    `threads` of None means leave it alone -- either an operator set the variable, or no
    quota constrains the container.
    """

    threads: int | None
    detail: str


def parse_cpu_max(cpu_max_text: str) -> float | None:
    """Cores out of a cgroup v2 `cpu.max`, which reads `<quota> <period>` in
    microseconds.

    `max` in the quota field means no limit. A zero or negative period is unreadable
    rather than unlimited, and is reported as unlimited all the same: the alternative is
    dividing by it.
    """
    fields = cpu_max_text.split()
    if len(fields) != 2 or fields[0] == "max":
        return None
    try:
        quota, period = int(fields[0]), int(fields[1])
    except ValueError:
        return None
    if quota <= 0 or period <= 0:
        return None
    return quota / period


def parse_cpu_cfs_quota(quota_text: str, period_text: str) -> float | None:
    """Cores out of a cgroup v1 pair, where a quota of -1 means no limit."""
    try:
        quota, period = int(quota_text.strip()), int(period_text.strip())
    except ValueError:
        return None
    if quota <= 0 or period <= 0:
        return None
    return quota / period


def read_cpu_quota(sysfs_root: Path = SYSFS_ROOT) -> CpuQuota:
    """The CPU quota this container runs under, cgroup v2 first and then v1.

    Read here rather than taken from `resources.limits.cpu`, because the chart's value
    is an intent and this is what the kernel enforces: an overwrite layer, a LimitRange
    or a node without CFS quota can each make the two differ, and the thread count has
    to follow the one that throttles.
    """
    cgroup = sysfs_root / "fs" / "cgroup"
    try:
        cores = parse_cpu_max((cgroup / "cpu.max").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        pass
    else:
        return CpuQuota(cores=cores, detail=_quota_detail(cores, cgroup / "cpu.max"))

    quota_file = cgroup / "cpu" / "cpu.cfs_quota_us"
    try:
        cores = parse_cpu_cfs_quota(
            quota_file.read_text(encoding="utf-8"),
            (cgroup / "cpu" / "cpu.cfs_period_us").read_text(encoding="utf-8"),
        )
    except (OSError, UnicodeDecodeError):
        return CpuQuota(cores=None, detail="no readable cgroup CPU quota")
    return CpuQuota(cores=cores, detail=_quota_detail(cores, quota_file))


def _quota_detail(cores: float | None, source: Path) -> str:
    """The log line for a quota, naming the file it came from either way."""
    if cores is None:
        return f"no limit in {source}"
    return f"{cores:g} cores from {source}"


def read_visible_cpus() -> int:
    """How many CPUs this process may run on.

    The affinity mask rather than the host's count, so a cpuset-pinned container is read
    correctly -- llama.cpp honours neither, which is the whole reason for this.
    """
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return os.cpu_count() or 1


def calculate_threads(quota_cores: float, visible_cpus: int) -> int:
    """Compute threads for a container holding this much CPU.

    The smaller of the quota and the affinity mask, less the headroom. Running more
    than the quota allows does not run faster: the threads spin-wait on each other and
    the cgroup throttles the lot for the rest of every CFS period.
    """
    budget = min(int(quota_cores), visible_cpus)
    return max(MIN_THREADS, budget - CPU_QUOTA_HEADROOM)


def plan_thread_environment(
    environ: Mapping[str, str],
    quota: CpuQuota,
    visible_cpus: int,
) -> ThreadPlan:
    """Decide the compute thread count the entrypoint sets before exec."""
    preset = environ.get(THREADS_ENV)
    if preset is not None:
        return ThreadPlan(
            threads=None,
            detail=f"honouring {THREADS_ENV}={preset} from the environment",
        )
    if quota.cores is None:
        return ThreadPlan(
            threads=None,
            detail=f"{quota.detail}; leaving llama.cpp its own sizing",
        )
    return ThreadPlan(
        threads=calculate_threads(quota.cores, visible_cpus),
        detail=(
            f"{quota.detail}, {visible_cpus} visible,"
            f" less {CPU_QUOTA_HEADROOM} for the runtime"
        ),
    )


def cap_parallelism_to_quota(parallelism: int, quota: CpuQuota) -> int:
    """Hold the slot count to what the CPU quota can actually run at once.

    The wrapper's estimate plans against memory, which is the binding constraint on a
    GPU. A quota smaller than that answer is the binding constraint instead, and each
    slot past it adds KV cache and contention for throughput that is not there.
    """
    if quota.cores is None:
        return parallelism
    return max(1, min(parallelism, int(quota.cores)))
