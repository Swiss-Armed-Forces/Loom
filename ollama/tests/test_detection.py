"""Detection policy: what a declaration plus a set of reachable devices means.

Most of it is asserted against `decide_detection`, which is pure. The two at the bottom
go through `detect_gpu_memory` over real directory trees instead, because the roots it
reads -- /dev for the device node, /sys for the amdgpu attributes, /proc for host memory
-- are three separate parameters, and a policy that is right about a `frozenset` says
nothing about which of them were actually looked at.
"""

from pathlib import Path

import pytest
from doubles import (
    GIB,
    MIB,
    FakeCard,
    RecordingProbe,
    make_dev,
    make_proc,
    make_sysfs,
    nvml_totals,
)

from ollama_wrapper import (
    GPU_VENDOR_ENV,
    GpuMemory,
    GpuProbeResult,
    GpuStatus,
    GpuVendor,
    decide_detection,
    declared_vendor,
    detect_gpu_memory,
)


def _found(vendor: GpuVendor) -> GpuProbeResult:
    return GpuProbeResult(
        memory=GpuMemory(
            vendor=vendor,
            dedicated_bytes=24 * GIB,
            shared_bytes=0,
            device_count=1,
            source="test",
        ),
        detail="test",
    )


def _missed() -> GpuProbeResult:
    return GpuProbeResult(memory=None, detail="nothing there")


def _probe(**answers: GpuProbeResult) -> RecordingProbe:
    return RecordingProbe({GpuVendor(name): value for name, value in answers.items()})


def test_declared_vendor_that_is_present_and_probes_clean() -> None:
    """The ordinary GPU deployment."""
    probe = _probe(amd=_found(GpuVendor.AMD))

    detection = decide_detection(GpuVendor.AMD, frozenset({GpuVendor.AMD}), probe)

    assert detection.status is GpuStatus.DETECTED
    assert detection.memory is not None


def test_declared_vendor_with_no_device_never_reaches_the_probe() -> None:
    """The failure this whole path exists for: fail closed, and fail fast."""
    probe = _probe(amd=_found(GpuVendor.AMD))

    detection = decide_detection(GpuVendor.AMD, frozenset(), probe)

    assert detection.status is GpuStatus.DECLARED_BUT_MISSING
    assert not probe.calls
    assert "/dev/kfd" in detection.detail


def test_device_present_but_memory_unreadable_is_not_fatal() -> None:
    """A GPU we cannot measure is still a GPU; only a missing device stops the pod."""
    probe = _probe(nvidia=_missed())

    detection = decide_detection(GpuVendor.NVIDIA, frozenset({GpuVendor.NVIDIA}), probe)

    assert detection.status is GpuStatus.PROBE_FAILED
    assert detection.memory is None


def test_nothing_declared_and_nothing_present() -> None:
    """The CPU-only image, which is a legitimate deployment rather than a fault."""
    detection = decide_detection(None, frozenset(), _probe())

    assert detection.status is GpuStatus.NO_DEVICE


def test_autodetection_finds_an_undeclared_gpu() -> None:
    """A CPU-tagged image on a GPU host should still tune for the GPU."""
    probe = _probe(amd=_found(GpuVendor.AMD))

    detection = decide_detection(None, frozenset({GpuVendor.AMD}), probe)

    assert detection.status is GpuStatus.DETECTED
    assert probe.calls == [GpuVendor.AMD]


def test_a_declaration_settles_a_box_with_both_vendors() -> None:
    """With an AMD iGPU and an NVIDIA card, dispatch must not be a guess."""
    probe = _probe(nvidia=_found(GpuVendor.NVIDIA), amd=_found(GpuVendor.AMD))

    decide_detection(
        GpuVendor.NVIDIA, frozenset({GpuVendor.AMD, GpuVendor.NVIDIA}), probe
    )

    assert probe.calls == [GpuVendor.NVIDIA]


def test_an_unknown_vendor_is_refused_rather_than_ignored() -> None:
    """A typo in a values file must not degrade quietly to CPU."""
    with pytest.raises(ValueError, match="rocm"):
        declared_vendor({GPU_VENDOR_ENV: "rocm"})


def test_a_declared_vendor_is_case_and_space_insensitive() -> None:
    """Values files are edited by hand."""
    assert declared_vendor({GPU_VENDOR_ENV: "  AMD "}) is GpuVendor.AMD
    assert declared_vendor({}) is None
    assert declared_vendor({GPU_VENDOR_ENV: ""}) is None


# --- End to end, over real trees ---
def test_a_declared_vendor_with_no_device_node_stops_the_pod(tmp_path: Path) -> None:
    """The refuse-to-start path, from the environment variable to the verdict.

    `charts/values-amd-gpu.yaml` sets LOOM_GPU_VENDOR and the box does not enumerate its
    GPU -- the case `--no-gpu` exists for. Asserted through `detect_gpu_memory` rather
    than through the policy alone, because what has to be true is that the *absence of
    /dev/kfd under dev_root* is what produced it: a probe reached anyway would read the
    host's real /sys and could answer either way.
    """
    detection = detect_gpu_memory(
        {GPU_VENDOR_ENV: "amd"},
        nvml_totals(),
        sysfs_root=make_sysfs(tmp_path / "sys", {}),
        proc_root=make_proc(tmp_path / "proc", 128 * GIB),
        dev_root=make_dev(tmp_path / "dev", ()),
    )

    assert detection.status is GpuStatus.DECLARED_BUT_MISSING
    assert detection.memory is None
    assert "/dev/kfd" in detection.detail


def test_a_declared_vendor_whose_node_is_there_is_measured(tmp_path: Path) -> None:
    """The other side of the same seam: the node exists, so the probe really runs."""
    detection = detect_gpu_memory(
        {GPU_VENDOR_ENV: "amd"},
        nvml_totals(),
        sysfs_root=make_sysfs(
            tmp_path / "sys",
            {"card0": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB))},
        ),
        proc_root=make_proc(tmp_path / "proc", 128 * GIB),
        dev_root=make_dev(tmp_path / "dev", ("kfd",)),
    )

    assert detection.status is GpuStatus.DETECTED
    assert detection.memory is not None
    assert detection.memory.vendor is GpuVendor.AMD
    # Carve-out plus GTT: an APU's "VRAM" is the same system memory, so
    # `probe_amd` reports one pool rather than two (see
    # test_gpu_probes.test_an_apu_is_planned_as_unified_memory).
    assert detection.memory.shared_bytes == 64 * GIB + 512 * MIB
