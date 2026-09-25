#!/usr/bin/env python3
"""Entrypoint for the Loom Ollama container image.

`setup` runs a one-shot ollama command against a temporary server (`ollama pull` needs
one). `entry` decides `OLLAMA_NUM_PARALLEL` and then becomes ollama.

Two things this deliberately does NOT do:

* Set `OLLAMA_CONTEXT_LENGTH`. Ollama sizes the context itself from the VRAM it
  measures, and setting the variable turns off that automatic sizing -- including the
  backoff that retries a failed load one rung down the 256k -> 32k -> 4k ladder. The
  trained context length is read here only to price a slot of KV cache.
* Take the parallelism from the chart. KV cache is `context x parallel`, so choosing
  the parallelism is really choosing how much context survives; that needs the GPU's
  memory, which only the container can see.
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

# --- Sizing constants ---
# The floor, and a ceiling that stops an unexpected reading turning into an absurd
# number of slots. The ceiling is a backstop against arithmetic, not a statement about
# capacity.
MIN_PARALLELISM = 4
MAX_PARALLELISM = 16

# Headroom on top of the model weights themselves.
MIN_RESERVED_VRAM_FOR_MODEL_BYTES = 1 * (1024**3)

# What one concurrent slot costs. KV cache is `context x parallel`, so the reserve has
# to scale with the context: 128 KiB/token is a GQA-shaped f16 estimate
# (2 x layers x kv_heads x head_dim x 2 B) -- the production 9B chat model is around
# 144 KiB/token. The floor is what this file used to reserve unconditionally, kept so
# a small context does not price a slot at nothing.
KV_BYTES_PER_TOKEN = 128 * 1024
MIN_PER_SLOT_RESERVE_BYTES = 512 * (1024**2)

# Host memory the GPU may not plan against, because the rest of Loom is living in it.
# This is LOOM_MIN_MEMORY from vars.sh -- what up.sh already refuses to start below --
# and it applies only to a shared pool, never to a card's own VRAM.
HOST_RESERVE_BYTES = 25 * (1024**3)

# A reported GPU total at or above this fraction of host RAM is unified memory (a
# Strix Halo iGPU, a GB10 Blackwell) rather than a card with its own VRAM. A ratio
# rather than a list of board names: it needs nothing but /proc/meminfo, and it does
# not rot.
UNIFIED_MEMORY_RATIO = 0.8

# Ollama's own automatic context ladder, mirrored from server/routes.go so that a slot
# is priced against the context Ollama will actually choose. RE-CHECK ON EVERY OLLAMA
# BUMP: the server logs `vram-based default context` with the tier it picked, which is
# how a drift from this table shows up.
AUTO_CONTEXT_TIERS = (
    (47 * (1024**3), 262144),
    (23 * (1024**3), 32768),
)
AUTO_CONTEXT_FLOOR = 4096

# Used when no model reports a trained context, which leaves the per-slot floor as the
# binding constraint.
DEFAULT_CONTEXT_TOKENS = 4096

# --- Process constants ---
OLLAMA_STARTUP_RETRIES = 10
OLLAMA_RETRY_INTERVAL = 0.3
OLLAMA_SHUTDOWN_TIMEOUT = 5.0
NVIDIA_SMI_TIMEOUT = 10.0
NVIDIA_SMI_ARGV = [
    "nvidia-smi",
    "--query-gpu=memory.total",
    "--format=csv,nounits,noheader",
]

# --- Filesystem roots ---
# Parameterised everywhere below so the probes can be pointed at a fixture tree,
# which is what lets them be tested without patching anything.
SYSFS_ROOT = Path("/sys")
PROC_ROOT = Path("/proc")
DEV_ROOT = Path("/dev")

# --- Environment ---
GPU_VENDOR_ENV = "LOOM_GPU_VENDOR"
NUM_PARALLEL_ENV = "OLLAMA_NUM_PARALLEL"


class GpuVendor(StrEnum):
    """A GPU vendor, as the chart declares it and as the probes dispatch on it."""

    AMD = "amd"
    NVIDIA = "nvidia"


class GpuStatus(StrEnum):
    """How detection ended.

    The distinction that matters is DECLARED_BUT_MISSING against the other three: a
    chart that asked for a GPU and a container that cannot reach one is a broken
    deployment rather than a slow one, and it is the only outcome worth refusing to
    start on.
    """

    DETECTED = "detected"
    NO_DEVICE = "no-device"
    PROBE_FAILED = "probe-failed"
    DECLARED_BUT_MISSING = "declared-but-missing"


# The control device each vendor's compute stack needs. The same pair
# nixos/scripts/platform_info.sh reports, for the same reason.
DEVICE_NODES = {
    GpuVendor.NVIDIA: "nvidiactl",
    GpuVendor.AMD: "kfd",
}

# Preferred order when nothing was declared. NVIDIA first: on a box with both, the
# discrete card is the one worth having.
AUTODETECT_ORDER = (GpuVendor.NVIDIA, GpuVendor.AMD)


@dataclass(frozen=True)
class CommandResult:
    """The outcome of running something outside this process."""

    ok: bool
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    """Everything that leaves this process.

    A seam rather than a direct `subprocess` call, so a test can hand the probes another
    implementation instead of patching subprocess out from under them.
    """

    def run(self, argv: list[str], timeout_s: float) -> CommandResult:
        """Run a command, capturing both streams and never raising."""
        raise NotImplementedError


class SubprocessCommandRunner:
    """The real CommandRunner."""

    def run(self, argv: list[str], timeout_s: float) -> CommandResult:
        """Run a command, capturing both streams and never raising."""
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return CommandResult(ok=False, stdout="", stderr=str(error))
        return CommandResult(
            ok=completed.returncode == 0,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


@dataclass(frozen=True)
class AmdCard:
    """One amdgpu card, as sysfs describes it."""

    name: str
    vram_bytes: int
    gtt_bytes: int


@dataclass(frozen=True)
class GpuMemory:
    """Memory a GPU can reach, split by who else is entitled to it.

    `dedicated_bytes` is the card's own VRAM and is spendable in full. `shared_bytes` is
    GTT or a unified pool -- ordinary host RAM the GPU pins on demand -- and has to
    leave room for the rest of the stack.
    """

    vendor: GpuVendor
    dedicated_bytes: int
    shared_bytes: int
    device_count: int
    source: str

    @property
    def total_bytes(self) -> int:
        """Everything the GPU can reach, which is what Ollama itself measures."""
        return self.dedicated_bytes + self.shared_bytes


@dataclass(frozen=True)
class GpuProbeResult:
    """What one vendor's probe found, with the line to log either way."""

    memory: GpuMemory | None
    detail: str


@dataclass(frozen=True)
class GpuDetection:
    """The end of detection: an outcome, the numbers if there are any, and why."""

    status: GpuStatus
    memory: GpuMemory | None
    detail: str


@dataclass(frozen=True)
class MemoryBudget:
    """What the estimate may plan against, after the host keeps its share."""

    total_bytes: int
    dedicated_bytes: int
    shared_bytes: int
    detail: str


@dataclass(frozen=True)
class ModelInfo:
    """An installed model: what it weighs, and the longest context it was trained on."""

    name: str
    size_bytes: int
    context_length_tokens: int | None


@dataclass(frozen=True)
class ModelSet:
    """Every installed model, and the aggregates the estimate needs from them."""

    models: list[ModelInfo]

    @property
    def count(self) -> int:
        """How many models are installed."""
        return len(self.models)

    @property
    def total_size_bytes(self) -> int:
        """Combined weight of every installed model."""
        return sum(model.size_bytes for model in self.models)

    @property
    def largest_context_tokens(self) -> int | None:
        """The longest trained context any installed model reports."""
        known = [
            model.context_length_tokens
            for model in self.models
            if model.context_length_tokens
        ]
        return max(known) if known else None


@dataclass(frozen=True)
class ParallelismEstimate:
    """A parallelism, the context it was priced against, and how it was reached."""

    parallelism: int
    context_tokens: int
    detail: str


@dataclass(frozen=True)
class EntryPlan:
    """What `entry` changes about the environment before becoming ollama.

    `num_parallel` of None means leave it alone -- an operator set it, and an explicit
    value outranks an estimate.
    """

    num_parallel: int | None
    detail: str


# --- Utils ---
def size_bytes_to_human(size_bytes: int) -> str:
    """Render a byte count for a log line."""
    if size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    if size_bytes >= 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    return f"{size_bytes} B"


def clamp(value: int, lowest: int, highest: int) -> int:
    """Confine a value to a range."""
    return max(lowest, min(highest, value))


# --- Parsing ---
def parse_size_to_bytes(size_str: str) -> int:
    """Convert a size as `ollama list` prints it ("6.5 GB") into bytes."""
    match = re.match(r"([\d.]+)\s*(gb|mb)", size_str.lower())
    if not match:
        raise ValueError(f"Invalid size string: {size_str}")
    size = float(match.group(1))
    if match.group(2) == "gb":
        return int(size * 1024**3)
    return int(size * 1024**2)


def parse_context_length_tokens(show_output: str) -> int | None:
    """Pull the trained context length, in tokens, out of `ollama show` output."""
    match = re.search(r"context length\s+(\d+)", show_output, re.IGNORECASE)
    return int(match.group(1)) if match else None


def parse_meminfo_total_bytes(meminfo_text: str) -> int | None:
    """Read MemTotal out of /proc/meminfo.

    Inside a container this reports the *host's* memory, which is the number wanted
    here: a shared GPU pool is carved out of exactly that.
    """
    match = re.search(r"^MemTotal:\s+(\d+)\s+kB", meminfo_text, re.MULTILINE)
    return int(match.group(1)) * 1024 if match else None


def parse_nvidia_memory_totals_mib(stdout: str) -> list[int]:
    """Read one memory total per visible device, dropping anything non-numeric.

    MIG slices and unsupported devices come back as `[N/A]` or `Not Supported`; they are
    skipped rather than allowed to abort the probe.
    """
    return [
        int(stripped)
        for line in stdout.splitlines()
        if (stripped := line.strip()).isdigit()
    ]


def parse_model_list(stdout: str) -> list[ModelInfo]:
    """Parse `ollama list` output into models that have no context length yet."""
    models: list[ModelInfo] = []
    for line in stdout.strip().splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        parts = re.split(r"\s{2,}", stripped)
        if len(parts) < 3:
            raise ValueError(f"Invalid model entry: {stripped}")
        models.append(
            ModelInfo(
                name=parts[0],
                size_bytes=parse_size_to_bytes(parts[2]),
                context_length_tokens=None,
            )
        )
    return models


# --- GPU probes ---
def read_int_attribute(path: Path) -> int | None:
    """Read a sysfs attribute holding a single integer.

    Anything unreadable or unexpected -- a permission error, a directory where a file
    belongs, `N/A` -- is None rather than an exception, so one odd attribute cannot take
    the whole probe down with it.
    """
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    return int(text) if text.isdigit() else None


def parse_amd_card_dir(card_dir: Path) -> AmdCard | None:
    """Read one /sys/class/drm entry, if it is an amdgpu card at all.

    Two filters, both load-bearing. The name has to be `cardN`, because connectors
    (`card1-DP-1`) carry a `device` symlink of their own and would otherwise each be
    reported as a GPU. And the driver has to be amdgpu, because an i915 or a BMC's
    display adapter is usually `card0` and would shadow the real thing.
    """
    if not re.fullmatch(r"card[0-9]+", card_dir.name):
        return None
    device = card_dir / "device"
    try:
        if (device / "driver").resolve().name != "amdgpu":
            return None
    except OSError:
        return None
    vram_bytes = read_int_attribute(device / "mem_info_vram_total")
    gtt_bytes = read_int_attribute(device / "mem_info_gtt_total")
    if vram_bytes is None and gtt_bytes is None:
        return None
    return AmdCard(
        name=card_dir.name,
        vram_bytes=vram_bytes or 0,
        gtt_bytes=gtt_bytes or 0,
    )


def list_amd_cards(sysfs_root: Path) -> list[AmdCard]:
    """Every amdgpu card sysfs knows about."""
    try:
        entries = sorted((sysfs_root / "class" / "drm").iterdir())
    except OSError:
        return []
    cards = [parse_amd_card_dir(entry) for entry in entries]
    return [card for card in cards if card is not None]


def select_amd_card(cards: list[AmdCard]) -> AmdCard | None:
    """Pick the card to plan against -- never sum them.

    Every amdgpu card reports the same system-wide GTT pool, so adding two of them up
    claims the machine twice. The largest VRAM wins, which on an iGPU-plus-dGPU box is
    the discrete card.
    """
    if not cards:
        return None
    return max(cards, key=lambda card: (card.vram_bytes, card.gtt_bytes, card.name))


def probe_amd(sysfs_root: Path) -> GpuProbeResult:
    """Read AMD GPU memory out of sysfs.

    sysfs rather than rocm-smi because the ROCm runtime image does not carry it -- its
    ROCm userspace is vendored rather than packaged -- while /sys is mounted in every
    container.
    """
    cards = list_amd_cards(sysfs_root)
    chosen = select_amd_card(cards)
    if chosen is None:
        return GpuProbeResult(
            memory=None,
            detail=f"no amdgpu card under {sysfs_root}/class/drm",
        )
    names = ", ".join(card.name for card in cards)
    return GpuProbeResult(
        memory=GpuMemory(
            vendor=GpuVendor.AMD,
            dedicated_bytes=chosen.vram_bytes,
            shared_bytes=chosen.gtt_bytes,
            device_count=len(cards),
            source=f"{sysfs_root}/class/drm/{chosen.name} (amdgpu)",
        ),
        detail=f"amdgpu cards: {names}; planning against {chosen.name}",
    )


def probe_nvidia(
    runner: CommandRunner,
    host_memory_bytes: int | None,
) -> GpuProbeResult:
    """Read NVIDIA GPU memory out of nvidia-smi.

    Across several visible devices the smallest wins: a model has to fit on whichever
    one it lands on. A total that is most of host RAM is unified memory rather than a
    card's own, and is booked as shared so the host reserve applies to it.
    """
    result = runner.run(NVIDIA_SMI_ARGV, NVIDIA_SMI_TIMEOUT)
    if not result.ok:
        return GpuProbeResult(
            memory=None,
            detail=f"nvidia-smi unavailable: {result.stderr.strip() or 'no output'}",
        )
    totals = parse_nvidia_memory_totals_mib(result.stdout)
    if not totals:
        return GpuProbeResult(memory=None, detail="nvidia-smi reported no devices")
    total_bytes = min(totals) * (1024**2)
    unified = (
        host_memory_bytes is not None
        and total_bytes >= UNIFIED_MEMORY_RATIO * host_memory_bytes
    )
    kind = "unified memory" if unified else "dedicated VRAM"
    return GpuProbeResult(
        memory=GpuMemory(
            vendor=GpuVendor.NVIDIA,
            dedicated_bytes=0 if unified else total_bytes,
            shared_bytes=total_bytes if unified else 0,
            device_count=len(totals),
            source="nvidia-smi",
        ),
        detail=f"{len(totals)} device(s), {size_bytes_to_human(total_bytes)} {kind}",
    )


# --- Detection ---
def read_host_memory_bytes(proc_root: Path = PROC_ROOT) -> int | None:
    """Total host memory, or None if /proc/meminfo cannot be read."""
    try:
        meminfo = (proc_root / "meminfo").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return parse_meminfo_total_bytes(meminfo)


def present_vendors(dev_root: Path) -> frozenset[GpuVendor]:
    """Which vendors' compute is actually reachable from this container."""
    return frozenset(
        vendor for vendor, node in DEVICE_NODES.items() if (dev_root / node).exists()
    )


def declared_vendor(environ: Mapping[str, str]) -> GpuVendor | None:
    """The vendor the chart declared, if any.

    An unrecognised value raises rather than falling through to autodetection: a typo
    in a values file quietly degrading to CPU is the failure this whole path exists to
    prevent.
    """
    raw = environ.get(GPU_VENDOR_ENV, "").strip().lower()
    if not raw:
        return None
    try:
        return GpuVendor(raw)
    except ValueError:
        valid = ", ".join(vendor.value for vendor in GpuVendor)
        raise ValueError(
            f"{GPU_VENDOR_ENV}={raw!r} is not a known GPU vendor (expected: {valid})"
        ) from None


def _detection_from_probe(
    vendor: GpuVendor,
    probe: Callable[[GpuVendor], GpuProbeResult],
) -> GpuDetection:
    """Run one vendor's probe and classify what came back."""
    result = probe(vendor)
    status = GpuStatus.PROBE_FAILED if result.memory is None else GpuStatus.DETECTED
    return GpuDetection(
        status=status,
        memory=result.memory,
        detail=f"{vendor.value}: {result.detail}",
    )


def decide_detection(
    declared: GpuVendor | None,
    present: frozenset[GpuVendor],
    probe: Callable[[GpuVendor], GpuProbeResult],
) -> GpuDetection:
    """Turn a declaration and a set of reachable devices into an outcome.

    Pure, so the policy can be tested without a filesystem or a subprocess.
    """
    if declared is not None:
        if declared not in present:
            node = DEVICE_NODES[declared]
            return GpuDetection(
                status=GpuStatus.DECLARED_BUT_MISSING,
                memory=None,
                detail=f"{GPU_VENDOR_ENV}={declared.value} but /dev/{node} is absent",
            )
        return _detection_from_probe(declared, probe)
    for vendor in AUTODETECT_ORDER:
        if vendor in present:
            return _detection_from_probe(vendor, probe)
    return GpuDetection(
        status=GpuStatus.NO_DEVICE,
        memory=None,
        detail="no GPU declared and none reachable",
    )


def detect_gpu_memory(
    environ: Mapping[str, str],
    runner: CommandRunner,
    sysfs_root: Path = SYSFS_ROOT,
    proc_root: Path = PROC_ROOT,
    dev_root: Path = DEV_ROOT,
) -> GpuDetection:
    """Find the GPU and its memory, dispatching on the vendor the chart declared."""
    host_memory_bytes = read_host_memory_bytes(proc_root)

    def probe(vendor: GpuVendor) -> GpuProbeResult:
        if vendor is GpuVendor.AMD:
            return probe_amd(sysfs_root)
        return probe_nvidia(runner, host_memory_bytes)

    return decide_detection(
        declared=declared_vendor(environ),
        present=present_vendors(dev_root),
        probe=probe,
    )


# --- Sizing ---
def build_memory_budget(
    memory: GpuMemory,
    host_memory_bytes: int | None,
) -> MemoryBudget:
    """Decide how much of the GPU's memory the estimate may plan against.

    A card's own VRAM is spent in full -- nothing else is entitled to it. A shared pool
    is host RAM, so the rest of Loom keeps HOST_RESERVE_BYTES of it whatever ceiling the
    GPU was given.
    """
    if memory.shared_bytes <= 0:
        detail = "dedicated VRAM only"
        shared = 0
    elif host_memory_bytes is None:
        detail = "host memory unknown; ignoring the shared pool"
        shared = 0
    else:
        shared = max(
            0, min(memory.shared_bytes, host_memory_bytes - HOST_RESERVE_BYTES)
        )
        detail = (
            f"shared pool {size_bytes_to_human(memory.shared_bytes)}, capped to"
            f" {size_bytes_to_human(shared)} by the"
            f" {size_bytes_to_human(HOST_RESERVE_BYTES)} host reserve"
        )
    return MemoryBudget(
        total_bytes=memory.dedicated_bytes + shared,
        dedicated_bytes=memory.dedicated_bytes,
        shared_bytes=shared,
        detail=detail,
    )


def auto_context_for(total_bytes: int) -> int:
    """The context Ollama picks for itself at this much GPU memory."""
    for threshold, tokens in AUTO_CONTEXT_TIERS:
        if total_bytes >= threshold:
            return tokens
    return AUTO_CONTEXT_FLOOR


def effective_context_tokens(total_bytes: int, trained_tokens: int | None) -> int:
    """The context a slot should be priced against.

    Ollama's automatic choice, clamped to what the model was trained for -- which is
    what the server does to it at load time anyway.
    """
    if trained_tokens is None:
        return DEFAULT_CONTEXT_TOKENS
    return min(auto_context_for(total_bytes), trained_tokens)


def per_slot_reserve_bytes(context_tokens: int) -> int:
    """What one concurrent request costs in KV cache."""
    return max(MIN_PER_SLOT_RESERVE_BYTES, context_tokens * KV_BYTES_PER_TOKEN)


def calculate_parallelism(
    budget: MemoryBudget,
    models: ModelSet,
    context_tokens: int,
) -> int:
    """How many concurrent slots fit, once the weights and their headroom are paid for.

    Multiplying by the model count over-reserves -- Ollama does not keep every model
    resident, and an embedding model's KV cache is negligible -- but it errs toward
    fewer slots, which is the safe direction.
    """
    usable = (
        budget.total_bytes - models.total_size_bytes - MIN_RESERVED_VRAM_FOR_MODEL_BYTES
    )
    if usable <= 0:
        return MIN_PARALLELISM
    per_slot = per_slot_reserve_bytes(context_tokens) * max(1, models.count)
    return clamp(usable // per_slot, MIN_PARALLELISM, MAX_PARALLELISM)


def estimate_parallelism(
    detection: GpuDetection,
    models: ModelSet,
    host_memory_bytes: int | None,
) -> ParallelismEstimate:
    """Turn a detected GPU and the installed models into a parallelism."""
    if detection.memory is None:
        return ParallelismEstimate(
            parallelism=MIN_PARALLELISM,
            context_tokens=DEFAULT_CONTEXT_TOKENS,
            detail=f"no GPU memory to plan against ({detection.status.value})",
        )
    budget = build_memory_budget(detection.memory, host_memory_bytes)
    # The tier follows everything the GPU can reach, because that is what Ollama
    # measures; the budget is what we are willing to spend of it.
    context_tokens = effective_context_tokens(
        detection.memory.total_bytes,
        models.largest_context_tokens,
    )
    return ParallelismEstimate(
        parallelism=calculate_parallelism(budget, models, context_tokens),
        context_tokens=context_tokens,
        detail=(
            f"{budget.detail}; planning against"
            f" {size_bytes_to_human(budget.total_bytes)} for {models.count} model(s)"
            f" totalling {size_bytes_to_human(models.total_size_bytes)} at"
            f" {context_tokens} tokens"
            f" ({size_bytes_to_human(per_slot_reserve_bytes(context_tokens))}/slot)"
        ),
    )


# --- Entry policy ---
def wants_estimate(environ: Mapping[str, str]) -> bool:
    """Whether anything has to be worked out at all.

    An operator who set the value has already answered the question, and answering it
    again would cost a whole temporary-server cycle for a result that gets discarded.
    """
    return NUM_PARALLEL_ENV not in environ


def plan_entry_environment(
    environ: Mapping[str, str],
    estimate: ParallelismEstimate | None,
) -> EntryPlan:
    """Decide what `entry` changes about the environment before exec."""
    preset = environ.get(NUM_PARALLEL_ENV)
    if preset is not None:
        return EntryPlan(
            num_parallel=None,
            detail=f"honouring {NUM_PARALLEL_ENV}={preset} from the environment",
        )
    if estimate is None:
        return EntryPlan(
            num_parallel=MIN_PARALLELISM,
            detail="no estimate available; using the floor",
        )
    return EntryPlan(num_parallel=estimate.parallelism, detail=estimate.detail)


# --- Ollama helpers ---
def wait_for_ollama_ready(
    retries: int = OLLAMA_STARTUP_RETRIES, interval: float = OLLAMA_RETRY_INTERVAL
) -> bool:
    """Wait for `ollama ps` to respond, indicating the server is ready."""
    for _ in range(retries):
        try:
            subprocess.check_output(["ollama", "ps"], stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            time.sleep(interval)
    return False


@contextmanager
def temporary_ollama_serve() -> Generator[None, None, None]:
    """Start `ollama serve` in the background, shut it down on the way out."""
    serve_process: subprocess.Popen[bytes] | None = None
    try:
        print("🌀 Starting temporary `ollama serve`...")
        serve_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not wait_for_ollama_ready():
            print("❌ `ollama serve` failed to start in time.")
            raise RuntimeError("Ollama server did not become ready.")
        yield
    finally:
        if serve_process:
            print("🛑 Shutting down temporary `ollama serve`...")
            serve_process.send_signal(signal.SIGINT)
            try:
                serve_process.wait(timeout=OLLAMA_SHUTDOWN_TIMEOUT)
            except subprocess.TimeoutExpired:
                # Raising in here would mask whatever sent us into the finally.
                serve_process.kill()


def read_context_length_tokens(model_name: str) -> int | None:
    """Ask a running server for one model's trained context length."""
    try:
        output = subprocess.check_output(["ollama", "show", model_name], text=True)
    except subprocess.CalledProcessError:
        print(f"❌ Failed to show model '{model_name}'")
        return None
    tokens = parse_context_length_tokens(output)
    if tokens is None:
        print(f"⚠️ No context length found for model '{model_name}'")
    return tokens


def get_installed_models() -> ModelSet:
    """Every installed model, with its weight and its trained context length."""
    with temporary_ollama_serve():
        output = subprocess.check_output(["ollama", "list"]).decode("utf-8")
        return ModelSet(
            models=[
                ModelInfo(
                    name=model.name,
                    size_bytes=model.size_bytes,
                    context_length_tokens=read_context_length_tokens(model.name),
                )
                for model in parse_model_list(output)
            ]
        )


# --- Mode handlers ---
def report_detection(detection: GpuDetection) -> None:
    """Say what was found, in terms an operator can act on."""
    if detection.status is GpuStatus.DETECTED and detection.memory is not None:
        memory = detection.memory
        print(
            f"🧠 GPU detected via {memory.source}:"
            f" {size_bytes_to_human(memory.dedicated_bytes)} dedicated,"
            f" {size_bytes_to_human(memory.shared_bytes)} shared"
        )
        print(f"   {detection.detail}")
        return
    if detection.status is GpuStatus.DECLARED_BUT_MISSING:
        print(f"❌ {detection.detail}")
        print("   This container was deployed as a GPU workload but cannot reach one.")
        print("   Check that the device plugin is installed and advertising the")
        print("   resource, that the right charts/values-*-gpu.yaml was applied, or")
        print("   rebuild the appliance image with --no-gpu for a CPU-only box.")
        return
    if detection.status is GpuStatus.PROBE_FAILED:
        print(f"⚠️ GPU present but its memory could not be read: {detection.detail}")
        return
    print(f"ℹ️ Running on CPU: {detection.detail}")


def run_setup_command(ollama_args: list[str]) -> None:
    """Run a one-shot Ollama command with a temporary server (e.g. `pull`, `list`).

    Deliberately no GPU check: setup also runs on CPU-only installs, which use the
    nvidia-tagged runtime image by default, and failing a model pull over a missing
    device would break them.
    """
    with temporary_ollama_serve():
        print(f"🔧 Running setup command: ollama {' '.join(ollama_args)}")
        subprocess.run(["ollama"] + ollama_args, check=True)


def run_entry_command(ollama_args: list[str]) -> None:
    """Set OLLAMA_NUM_PARALLEL if nobody else did, then become ollama."""
    env = os.environ.copy()

    # Before anything expensive: a container deployed as a GPU workload that cannot
    # reach a GPU should fail in milliseconds, not after a whole server cycle.
    detection = detect_gpu_memory(environ=env, runner=SubprocessCommandRunner())
    report_detection(detection)
    if detection.status is GpuStatus.DECLARED_BUT_MISSING:
        sys.exit(1)

    estimate: ParallelismEstimate | None = None
    if wants_estimate(env):
        models = get_installed_models()
        if models.count == 0:
            print("⚠️ No installed models found.")
        estimate = estimate_parallelism(detection, models, read_host_memory_bytes())

    plan = plan_entry_environment(env, estimate)
    if plan.num_parallel is None:
        print(f"🔧 {plan.detail}")
    else:
        env[NUM_PARALLEL_ENV] = str(plan.num_parallel)
        print(f"✅ {NUM_PARALLEL_ENV}={plan.num_parallel}: {plan.detail}")

    sys.stdout.flush()
    sys.stderr.flush()

    os.execvpe("ollama", ["ollama"] + ollama_args, env)


# --- CLI Parser ---
def parse_args() -> argparse.Namespace:
    """Parse the wrapper's own arguments."""
    parser = argparse.ArgumentParser(description="Wrapper for Ollama")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    setup_parser = subparsers.add_parser(
        "setup", help="Run a one-time ollama command with temporary server"
    )
    setup_parser.add_argument(
        "ollama_args", nargs=argparse.REMAINDER, help="Arguments passed to ollama"
    )

    entry_parser = subparsers.add_parser(
        "entry", help="Run Ollama with an estimated OLLAMA_NUM_PARALLEL"
    )
    entry_parser.add_argument(
        "ollama_args", nargs=argparse.REMAINDER, help="Arguments passed to ollama"
    )

    return parser.parse_args()


def main() -> None:
    """Dispatch on the wrapper's mode."""
    args = parse_args()

    if args.mode == "setup":
        run_setup_command(args.ollama_args)
    elif args.mode == "entry":
        run_entry_command(args.ollama_args)
    else:
        print(f"❌ Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
