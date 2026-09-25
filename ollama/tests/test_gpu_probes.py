"""The two vendor probes: amdgpu sysfs, and nvidia-smi."""

from pathlib import Path

from doubles import GIB, MIB, FakeCard, FakeCommandRunner, make_sysfs

from ollama_wrapper import CommandResult, GpuVendor, probe_amd, probe_nvidia


def _ok(stdout: str) -> FakeCommandRunner:
    return FakeCommandRunner(CommandResult(ok=True, stdout=stdout, stderr=""))


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
    assert result.memory.shared_bytes == 64 * GIB


def test_apu_reports_carve_out_and_gtt_separately(tmp_path: Path) -> None:
    """The EVO-X2 shape: a tiny carve-out plus the GTT pool that actually matters."""
    sysfs = make_sysfs(
        tmp_path,
        {"card0": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB))},
    )

    result = probe_amd(sysfs)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 512 * MIB
    assert result.memory.shared_bytes == 64 * GIB
    assert result.memory.vendor is GpuVendor.AMD


def test_two_cards_do_not_have_their_gtt_summed(tmp_path: Path) -> None:
    """Both cards report the same system-wide pool; summing claims the box twice."""
    sysfs = make_sysfs(
        tmp_path,
        {
            "card0": FakeCard(vram=str(512 * MIB), gtt=str(64 * GIB)),
            "card1": FakeCard(vram=str(24 * GIB), gtt=str(64 * GIB)),
        },
    )

    result = probe_amd(sysfs)

    assert result.memory is not None
    assert result.memory.shared_bytes == 64 * GIB
    assert result.memory.dedicated_bytes == 24 * GIB
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
    result = probe_nvidia(_ok("24576\n"), host_memory_bytes=128 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 24576 * MIB
    assert result.memory.shared_bytes == 0
    assert result.memory.device_count == 1


def test_nvidia_smi_reporting_no_devices() -> None:
    """Exit 0 with empty output means no GPU, not a GPU of unknown size."""
    assert probe_nvidia(_ok(""), host_memory_bytes=128 * GIB).memory is None


def test_nvidia_smi_missing_carries_its_error() -> None:
    """The ROCm image has no nvidia-smi; the reason has to reach the log."""
    runner = FakeCommandRunner(
        CommandResult(ok=False, stdout="", stderr="No such file or directory")
    )

    result = probe_nvidia(runner, host_memory_bytes=128 * GIB)

    assert result.memory is None
    assert "No such file or directory" in result.detail


def test_smallest_of_several_devices_wins() -> None:
    """A model has to fit on whichever device it lands on."""
    result = probe_nvidia(_ok("24576\n12288\n"), host_memory_bytes=128 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 12288 * MIB
    assert result.memory.device_count == 2


def test_non_numeric_lines_are_dropped() -> None:
    """MIG and unsupported devices report `[N/A]`, which must not abort the probe."""
    runner = _ok("[N/A]\n24576\nNot Supported\n")

    result = probe_nvidia(runner, host_memory_bytes=128 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 24576 * MIB
    assert result.memory.device_count == 1


def test_unified_memory_is_not_booked_as_vram() -> None:
    """A GB10 reports most of host RAM; spending that as VRAM would starve the box."""
    result = probe_nvidia(_ok("121856\n"), host_memory_bytes=125 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 0
    assert result.memory.shared_bytes == 121856 * MIB


def test_a_big_discrete_card_is_still_dedicated() -> None:
    """80 GiB on a 125 GiB host is a card, not unified memory."""
    result = probe_nvidia(_ok("81920\n"), host_memory_bytes=125 * GIB)

    assert result.memory is not None
    assert result.memory.dedicated_bytes == 81920 * MIB
    assert result.memory.shared_bytes == 0
