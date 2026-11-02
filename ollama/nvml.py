"""Reading NVIDIA GPU memory through NVML, with ctypes.

Its own module because it is the one part of the entrypoint that calls into a C library
-- every other probe reads a file -- so it is the part whose failure modes are about
symbols and structs rather than about arithmetic.

**Not nvidia-smi.** The container toolkit injects a NixOS host's driver executables
without the ELF interpreter they need, so they cannot exec in a pod at all; the shared
library is injected the same way and loads fine.

Shipped beside the wrapper in the runtime image -- see ollama/Dockerfile.runtime.
"""

import ctypes
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

# The soname, not a path: `ld.so` is what knows where the toolkit put it.
NVML_LIBRARY = "libnvidia-ml.so.1"
NVML_SUCCESS: Final = 0


@dataclass(frozen=True)
class NvmlReading:
    """What NVML said about the GPUs it found.

    `available` separates "no NVML here" from "NVML answered": only the second is
    evidence about the hardware. `totals_bytes` is empty for a part reporting no total
    -- a GB10 answers `NVML_ERROR_NOT_SUPPORTED`.
    """

    available: bool
    device_count: int
    totals_bytes: tuple[int, ...]
    detail: str


def nvml_unavailable(detail: str) -> NvmlReading:
    """A reading that says nothing about the hardware, and why."""
    return NvmlReading(False, device_count=0, totals_bytes=(), detail=detail)


def nvml_device_total_bytes(nvml: ctypes.CDLL, index: int) -> int:
    """One device's total, or 0 if it reports none or cannot be read at all.

    `pointer` rather than `byref` for the out-parameters: both put the same address on
    the stack, but `byref` returns a `CArgObject` whose target is reachable only through
    a private attribute, so a fake library cannot answer through one. Three allocations
    per probe, once per process.
    """
    handle = ctypes.c_void_p()
    if (
        nvml.nvmlDeviceGetHandleByIndex_v2(index, ctypes.pointer(handle))
        != NVML_SUCCESS
    ):
        return 0
    # nvmlMemory_t is three unsigned long longs: total, free, used. An array is
    # already passed by reference, so it needs no pointer of its own.
    memory = (ctypes.c_ulonglong * 3)()
    if nvml.nvmlDeviceGetMemoryInfo(handle, memory) != NVML_SUCCESS:
        return 0
    return int(memory[0])


def load_nvml() -> ctypes.CDLL:
    """Open NVML by soname, which is how the toolkit's injected copy is found.

    A seam so the suite can hand in a library that is missing a symbol.
    """
    return ctypes.CDLL(NVML_LIBRARY)


def read_nvml(load: Callable[[], ctypes.CDLL] = load_nvml) -> NvmlReading:
    """Ask the real NVML about every device, never raising.

    The symbol lookups as well as the load: every `nvml.<symbol>` raises
    AttributeError if the library does not export it -- a driver/stub mismatch,
    which is exactly the box this probe is for -- and AttributeError is not in
    the tuple `run_entry_command` catches, so it would escape `main()`.
    """
    try:
        nvml = load()
    except OSError as error:
        return nvml_unavailable(f"{NVML_LIBRARY} did not load: {error}")
    try:
        return _read_nvml_devices(nvml)
    except (OSError, AttributeError) as error:
        return nvml_unavailable(f"{NVML_LIBRARY} is not usable: {error}")


def _read_nvml_devices(nvml: ctypes.CDLL) -> NvmlReading:
    """The part that calls into the library, with the symbols it needs."""
    if nvml.nvmlInit_v2() != NVML_SUCCESS:
        return nvml_unavailable("nvmlInit failed")
    try:
        count = ctypes.c_uint()
        if nvml.nvmlDeviceGetCount_v2(ctypes.pointer(count)) != NVML_SUCCESS:
            return nvml_unavailable("nvmlDeviceGetCount failed")
        reported = (nvml_device_total_bytes(nvml, i) for i in range(count.value))
        totals = [total for total in reported if total > 0]
        return NvmlReading(
            available=True,
            device_count=count.value,
            totals_bytes=tuple(totals),
            detail=f"{count.value} device(s), {len(totals)} with a memory total",
        )
    finally:
        nvml.nvmlShutdown()
