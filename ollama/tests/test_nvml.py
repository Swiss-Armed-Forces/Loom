"""The ctypes layer, which the doubles elsewhere in this suite step over.

`doubles.py` substitutes the `Callable[[], NvmlReading]` seam, so every other
test in this directory exercises the arithmetic above `read_nvml` and none of it
-- not the `_v2` symbol names, not the `byref` usage, not the struct layout. A
mistake there degrades quietly: a Spark drops from eight slots to `PROBE_FAILED`
and four, with a warning nothing acts on.

What is pinned here is the error contract, which is the half a wrong environment
actually hits. The library is faked with a plain object, because `ctypes.CDLL`
resolves attributes on `__getattr__` and anything that answers the same way is
indistinguishable to the code under test.
"""

import ctypes
from collections.abc import Callable
from pathlib import Path
from typing import Any

from nvml import NVML_LIBRARY, NVML_SUCCESS, NvmlReading, read_nvml

SYMBOLS = (
    "nvmlInit_v2",
    "nvmlDeviceGetCount_v2",
    "nvmlDeviceGetHandleByIndex_v2",
    "nvmlDeviceGetMemoryInfo",
    "nvmlShutdown",
)

DEVICE_TOTAL_BYTES = 24 * (1024**3)


class FakeNvml:
    """A stand-in for `ctypes.CDLL`, missing whichever symbols the test says.

    The C names are a lookup table rather than methods, so this file stays readable
    Python: `nvmlDeviceGetHandleByIndex_v2` is the library's spelling, not a name
    anything here should have to be called by.
    """

    def __init__(self, *, missing: frozenset[str] = frozenset(), devices: int = 1):
        self._missing = missing
        self._devices = devices
        self.shutdown_calls = 0
        self._symbols: dict[str, Callable[..., int]] = {
            "nvmlInit_v2": self._init,
            "nvmlDeviceGetCount_v2": self._device_count,
            "nvmlDeviceGetHandleByIndex_v2": self._device_handle,
            "nvmlDeviceGetMemoryInfo": self._memory_info,
            "nvmlShutdown": self._shutdown,
        }

    def __getattr__(self, name: str) -> Callable[..., int]:
        # Exactly what a real CDLL does for a symbol the library does not
        # export: AttributeError, not a None that would be called later.
        symbols = self.__dict__.get("_symbols", {})
        if name in self.__dict__.get("_missing", frozenset()) or name not in symbols:
            raise AttributeError(f"{name} not found")
        return symbols[name]

    def _init(self) -> int:
        return NVML_SUCCESS

    def _device_count(self, count: Any) -> int:
        # Through the pointer `nvml.py` passes rather than a `byref` wrapper, which
        # is why it passes one: a `CArgObject` hides its target.
        count[0] = self._devices
        return NVML_SUCCESS

    def _device_handle(self, index: int, handle: Any) -> int:
        del index, handle
        return NVML_SUCCESS

    def _memory_info(self, handle: Any, memory: Any) -> int:
        del handle
        memory[0] = DEVICE_TOTAL_BYTES
        return NVML_SUCCESS

    def _shutdown(self) -> int:
        self.shutdown_calls += 1
        return NVML_SUCCESS


def _read(library: FakeNvml) -> NvmlReading:
    """`read_nvml` against one fake library."""
    return read_nvml(lambda: library)


def test_a_library_without_the_symbols_is_unavailable_rather_than_fatal() -> None:
    """A driver/stub mismatch is exactly the box this probe exists for.

    `AttributeError` is not in the tuple `run_entry_command` catches, so letting one
    escape turns "this container's NVML is odd" into a traceback out of `main()` instead
    of a CPU-only server.
    """
    for symbol in SYMBOLS:
        reading = _read(FakeNvml(missing=frozenset({symbol})))

        assert reading.available is False, symbol
        assert not reading.totals_bytes, symbol
        assert "not usable" in reading.detail, symbol


def test_a_working_library_reports_every_device_that_has_a_total() -> None:
    nvml = FakeNvml(devices=2)

    reading = _read(nvml)

    assert reading.available is True
    assert reading.device_count == 2
    assert reading.totals_bytes == (DEVICE_TOTAL_BYTES, DEVICE_TOTAL_BYTES)
    assert nvml.shutdown_calls == 1


def test_a_library_that_will_not_load_is_unavailable() -> None:
    """The case every CPU-only box is in."""

    def refuse() -> ctypes.CDLL:
        raise OSError(f"{NVML_LIBRARY}: cannot open shared object file")

    reading = read_nvml(refuse)

    assert reading.available is False
    assert "did not load" in reading.detail


def test_the_library_name_is_the_soname_not_a_path() -> None:
    """`libnvidia-ml.so.1` is what the container toolkit injects and `ld` finds.

    A path would be wrong twice over: the file is not at a fixed location, and
    the toolkit's injected copies are the ones with no ELF interpreter -- which
    is why this reads the library through ctypes rather than running
    `nvidia-smi`.
    """
    assert NVML_LIBRARY == "libnvidia-ml.so.1"
    assert not Path(NVML_LIBRARY).is_absolute()
