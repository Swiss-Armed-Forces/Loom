"""Test doubles and fixture builders for the Ollama wrapper's tests.

The sysfs builder writes a real directory tree under pytest's `tmp_path` rather than
faking the filesystem, so the probes exercise their real globbing, their real reads
and their real error branches. Only the one thing that genuinely leaves the process --
`nvidia-smi` -- gets a double.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ollama_wrapper import CommandResult, GpuProbeResult, GpuVendor

GIB = 1024**3
MIB = 1024**2


@dataclass
class FakeCommandRunner:
    """A CommandRunner that answers from a canned result and records its calls."""

    result: CommandResult
    calls: list[list[str]] = field(default_factory=list)

    def run(self, argv: list[str], timeout_s: float) -> CommandResult:
        """Record the call and hand back the canned answer."""
        del timeout_s
        self.calls.append(argv)
        return self.result


@dataclass
class RecordingProbe:
    """A probe callable that records which vendors it was asked about."""

    answers: Mapping[GpuVendor, GpuProbeResult]
    calls: list[GpuVendor] = field(default_factory=list)

    def __call__(self, vendor: GpuVendor) -> GpuProbeResult:
        """Record the vendor and return the answer prepared for it."""
        self.calls.append(vendor)
        return self.answers[vendor]


@dataclass(frozen=True)
class FakeCard:
    """One entry to write under /sys/class/drm.

    `vram`/`gtt` are written verbatim, so a test can put `"N/A"` or `""` in them. None
    leaves the attribute out entirely, the way an older driver would. `as_directory`
    makes the attributes directories instead of files, which is how the unreadable case
    is provoked in a container where tests run as root and `chmod 000` would not deny
    anything.
    """

    driver: str = "amdgpu"
    vram: str | None = None
    gtt: str | None = None
    as_directory: bool = False


def make_sysfs(root: Path, cards: Mapping[str, FakeCard]) -> Path:
    """Build a /sys tree containing the given drm entries, and return its root."""
    drm = root / "class" / "drm"
    drm.mkdir(parents=True, exist_ok=True)
    for name, card in cards.items():
        device = drm / name / "device"
        device.mkdir(parents=True)
        driver_dir = root / "bus" / "pci" / "drivers" / card.driver
        driver_dir.mkdir(parents=True, exist_ok=True)
        (device / "driver").symlink_to(driver_dir)
        _write_attribute(device / "mem_info_vram_total", card.vram, card.as_directory)
        _write_attribute(device / "mem_info_gtt_total", card.gtt, card.as_directory)
    return root


def _write_attribute(path: Path, value: str | None, as_directory: bool) -> None:
    """Write one sysfs attribute, or make it unreadable, or leave it out."""
    if value is None:
        return
    if as_directory:
        path.mkdir()
        return
    path.write_text(f"{value}\n", encoding="utf-8")


def make_proc(root: Path, mem_total_bytes: int) -> Path:
    """Build a /proc tree with a meminfo reporting the given total, and return it."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "meminfo").write_text(
        f"MemTotal:       {mem_total_bytes // 1024} kB\n"
        "MemFree:         1000000 kB\n",
        encoding="utf-8",
    )
    return root


def make_dev(root: Path, nodes: tuple[str, ...]) -> Path:
    """Build a /dev tree containing the given device nodes, and return its root."""
    root.mkdir(parents=True, exist_ok=True)
    for node in nodes:
        (root / node).write_text("", encoding="utf-8")
    return root
