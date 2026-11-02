"""The two vendor probes: amdgpu sysfs, and NVML."""

from pathlib import Path

from doubles import (
    GIB,
    MIB,
    FakeCard,
    make_sysfs,
    nvml_reading,
    nvml_totals,
    nvml_without_totals,
)

from ollama_wrapper import GpuVendor, NvmlReading, probe_amd, probe_nvidia


# --- AMD ---
def test_connector_entries_are_not_cards(tmp_path: Path) -> None:
    """A connector carries its own `device` symlink and must not count as a GPU."""
    sysfs = make_sysfs(
        tmp_path,
        {
            "card1": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB)),
            "card1-DP-1": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB)),
            "card1-HDMI-A-1": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB)),
        },
    )

    result = probe_amd(sysfs)

    assert result.memory is not None
    assert result.memory.device_count == 1


def test_non_amdgpu_card_does_not_shadow_the_real_one(tmp_path: Path) -> None:
    """An i915 card0 must not be picked over the amdgpu card behind it."""
    sysfs = make_sysfs(
        tmp_path,
        {
            "card0": FakeCard(driver="i915"),
            "card1": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB)),
        },
    )

    result = probe_amd(sysfs)

    assert result.memory is not None
    assert result.memory.source.endswith("card1 (amdgpu)")
    # An APU: the 512 MiB carve-out is part of the same pool, so the two are
    # reported as one shared figure rather than as a card with its own memory.
    assert result.memory.shared_bytes == 64 * GIB + 512 * MIB


def test_an_apu_is_planned_as_unified_memory(tmp_path: Path) -> None:
    """The EVO-X2 shape: a tiny carve-out plus the GTT pool that actually matters.

    Both are system memory, so both go in `shared_bytes` and the card has no dedicated
    VRAM at all -- the same shape `probe_nvidia` produces for a GB10, and the reason the
    two vendors plan the same box the same way.
    """
    sysfs = make_sysfs(
        tmp_path,
        {"card0": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB))},
    )

    result = probe_amd(sysfs)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 0
    assert result.memory.shared_bytes == 64 * GIB + 512 * MIB
    assert result.memory.vendor is GpuVendor.AMD


def test_a_discrete_card_is_planned_at_its_own_vram(tmp_path: Path) -> None:
    """An iGPU beside a dGPU, the topology this probe is easiest to get wrong on.

    Both cards report the same system-wide GTT pool, so summing them claims the box
    twice -- and booking GTT *at all* for the discrete card claims host memory it cannot
    place KV cache in. 24 GiB of card is 24 GiB to plan with, which is what
    `probe_nvidia` answers for the same hardware.
    """
    sysfs = make_sysfs(
        tmp_path,
        {
            "card0": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB)),
            "card1": FakeCard(vram=str(24 * GIB), gtt=str(64 * GIB)),
        },
    )

    result = probe_amd(sysfs)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 24 * GIB
    assert result.memory.shared_bytes == 0
    assert result.memory.source.endswith("card1 (amdgpu)")


def test_card_without_gtt_attribute_reports_no_shared_pool(tmp_path: Path) -> None:
    """An older driver exposes no mem_info_gtt_total; the card still counts."""
    sysfs = make_sysfs(tmp_path, {"card0": FakeCard(vram=str(16 * GIB))})

    result = probe_amd(sysfs)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 16 * GIB
    assert result.memory.shared_bytes == 0


def test_unparsable_attributes_skip_the_card(tmp_path: Path) -> None:
    """`N/A` in both attributes leaves nothing to plan against."""
    sysfs = make_sysfs(tmp_path, {"card0": FakeCard(vram="N/A", gtt="")})

    assert probe_amd(sysfs).memory is None


def test_unreadable_attributes_skip_the_card(tmp_path: Path) -> None:
    """A read that raises must not escape the probe."""
    sysfs = make_sysfs(
        tmp_path,
        {"card0": FakeCard(vram=str(16 * GIB), gtt=str(16 * GIB), as_directory=True)},
    )

    assert probe_amd(sysfs).memory is None


def test_no_drm_tree_at_all(tmp_path: Path) -> None:
    """A container with no /sys/class/drm is not an error, just no GPU."""
    assert probe_amd(tmp_path).memory is None


# --- NVIDIA ---
def test_single_discrete_card() -> None:
    """A card well below host RAM is dedicated VRAM."""
    result = probe_nvidia(nvml_totals(24576 * MIB), host_memory_bytes=128 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 24576 * MIB
    assert result.memory.shared_bytes == 0
    assert result.memory.device_count == 1


def test_nvml_reporting_no_devices() -> None:
    """NVML that initialised and found nothing means no GPU, not one of unknown size."""
    assert probe_nvidia(nvml_totals(), host_memory_bytes=128 * GIB).memory is None


def test_nvml_missing_carries_its_error() -> None:
    """The ROCm image has no NVML; the reason has to reach the log."""
    nvml = nvml_reading(
        NvmlReading(
            available=False,
            device_count=0,
            totals_bytes=(),
            detail="libnvidia-ml.so.1 did not load: No such file or directory",
        )
    )

    result = probe_nvidia(nvml, host_memory_bytes=128 * GIB)

    assert result.memory is None
    assert "No such file or directory" in result.detail


def test_smallest_of_several_devices_wins() -> None:
    """A model has to fit on whichever device it lands on."""
    result = probe_nvidia(
        nvml_totals(24576 * MIB, 12288 * MIB), host_memory_bytes=128 * GIB
    )

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 12288 * MIB
    assert result.memory.device_count == 2


def test_unified_memory_is_not_booked_as_vram() -> None:
    """A GPU reporting most of host RAM would starve the box if spent as VRAM."""
    result = probe_nvidia(nvml_totals(121856 * MIB), host_memory_bytes=125 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 0
    assert result.memory.shared_bytes == 121856 * MIB


def test_a_big_discrete_card_is_still_dedicated() -> None:
    """80 GiB on a 125 GiB host is a card, not unified memory."""
    result = probe_nvidia(nvml_totals(81920 * MIB), host_memory_bytes=125 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 81920 * MIB
    assert result.memory.shared_bytes == 0


def test_device_without_a_total_is_booked_as_unified_host_memory() -> None:
    """A GB10 answers NVML_ERROR_NOT_SUPPORTED: its memory is the host's.

    Failing the probe here would plan a 120 GiB box at the minimum parallelism.
    """
    result = probe_nvidia(nvml_without_totals(), host_memory_bytes=125 * GIB)

    assert result.memory is not None
    assert result.memory.vendor is GpuVendor.NVIDIA
    assert result.memory.dedicated_bytes == 0
    assert result.memory.shared_bytes == 125 * GIB
    assert result.memory.device_count == 1


def test_no_total_and_no_host_memory_is_still_a_failure() -> None:
    """With neither number there is nothing to plan against, and guessing is worse."""
    result = probe_nvidia(nvml_without_totals(), host_memory_bytes=None)

    assert result.memory is None
