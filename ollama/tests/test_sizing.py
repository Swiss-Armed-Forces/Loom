"""The budget and the estimate.

The four "shape" tests are regression guards: they assert an exact parallelism for a
real box, so that changing a constant has to be argued for rather than noticed later.
"""

from doubles import GIB, MIB

from ollama_wrapper import (
    MAX_PARALLELISM,
    MIN_PARALLELISM,
    GpuDetection,
    GpuMemory,
    GpuStatus,
    GpuVendor,
    MemoryBudget,
    ModelInfo,
    ModelSet,
    auto_context_for,
    build_memory_budget,
    calculate_parallelism,
    effective_context_tokens,
    estimate_parallelism,
    per_slot_reserve_bytes,
)

HOST_BYTES = 125 * GIB

# What the production models image ships: a 9B chat model with a 40960-token trained
# context, and an embedding model.
PRODUCTION_MODELS = ModelSet(
    models=[
        ModelInfo("chat", 6 * GIB, 40960),
        ModelInfo("embed", 512 * MIB, 2048),
    ]
)


def _detected(dedicated: int, shared: int) -> GpuDetection:
    return GpuDetection(
        status=GpuStatus.DETECTED,
        memory=GpuMemory(
            vendor=GpuVendor.AMD,
            dedicated_bytes=dedicated,
            shared_bytes=shared,
            device_count=1,
            source="test",
        ),
        detail="test",
    )


def _budget(total: int) -> MemoryBudget:
    return MemoryBudget(
        total_bytes=total,
        dedicated_bytes=total,
        shared_bytes=0,
        detail="test",
    )


# --- Budget ---
def test_a_cards_own_vram_is_spent_in_full() -> None:
    """The host reserve is about host RAM; it must not shrink a discrete card."""
    memory = GpuMemory(GpuVendor.NVIDIA, 24 * GIB, 0, 1, "test")

    budget = build_memory_budget(memory, host_memory_bytes=32 * GIB)

    assert budget.total_bytes == 24 * GIB
    assert budget.shared_bytes == 0


def test_a_shared_pool_leaves_the_host_its_share() -> None:
    """GTT is host RAM, and the rest of Loom is living in it."""
    memory = GpuMemory(GpuVendor.AMD, 512 * MIB, 64 * GIB, 1, "test")

    budget = build_memory_budget(memory, host_memory_bytes=HOST_BYTES)

    assert budget.shared_bytes == 64 * GIB
    assert budget.total_bytes == 512 * MIB + 64 * GIB


def test_a_shared_pool_on_a_small_host_yields_nothing() -> None:
    """Below the reserve there is nothing to give, and it must not go negative."""
    memory = GpuMemory(GpuVendor.AMD, 512 * MIB, 16 * GIB, 1, "test")

    budget = build_memory_budget(memory, host_memory_bytes=16 * GIB)

    assert budget.shared_bytes == 0
    assert budget.total_bytes == 512 * MIB


def test_unknown_host_memory_forfeits_the_shared_pool() -> None:
    """Without /proc/meminfo there is no way to know what may be taken."""
    memory = GpuMemory(GpuVendor.AMD, 512 * MIB, 64 * GIB, 1, "test")

    budget = build_memory_budget(memory, host_memory_bytes=None)

    assert budget.total_bytes == 512 * MIB


# --- Context ---
def test_the_context_tiers_match_ollamas_own() -> None:
    """Mirrored from server/routes.go; a drift here prices every slot wrongly."""
    assert auto_context_for(22 * GIB) == 4096
    assert auto_context_for(23 * GIB) == 32768
    assert auto_context_for(46 * GIB) == 32768
    assert auto_context_for(47 * GIB) == 262144


def test_the_context_is_clamped_to_what_the_model_was_trained_on() -> None:
    """Ollama clamps at load; pricing a slot above that reserves fiction."""
    assert effective_context_tokens(64 * GIB, 40960) == 40960
    assert effective_context_tokens(24 * GIB, 40960) == 32768
    assert effective_context_tokens(64 * GIB, None) == 4096


def test_a_slot_costs_in_proportion_to_its_context() -> None:
    """The unit fix: the reserve scales with tokens instead of being a constant."""
    assert per_slot_reserve_bytes(16384) == 2 * per_slot_reserve_bytes(8192)


def test_a_tiny_context_still_costs_the_floor() -> None:
    """Below the floor a slot would look free, and parallelism would run away."""
    assert per_slot_reserve_bytes(1) == per_slot_reserve_bytes(4096)


# --- Parallelism ---
def test_slots_halve_when_the_context_doubles() -> None:
    """The consequence that matters: parallelism trades directly against context."""
    models = ModelSet(models=[ModelInfo("chat", 1 * GIB, 16384)])
    budget = _budget(14 * GIB)

    assert calculate_parallelism(budget, models, 8192) == 12
    assert calculate_parallelism(budget, models, 16384) == 6


def test_a_budget_smaller_than_the_models_falls_to_the_floor() -> None:
    """Nothing fits, and Ollama's own scheduler is a better judge from here."""
    models = ModelSet(models=[ModelInfo("chat", 20 * GIB, 8192)])

    assert calculate_parallelism(_budget(8 * GIB), models, 8192) == MIN_PARALLELISM


def test_an_enormous_budget_is_capped() -> None:
    """The backstop against an unexpected reading turning into absurd concurrency."""
    models = ModelSet(models=[ModelInfo("chat", 1 * GIB, 512)])

    assert calculate_parallelism(_budget(500 * GIB), models, 512) == MAX_PARALLELISM


# --- Whole-box regression guards ---
def test_evo_x2_shape() -> None:
    """Strix Halo: a 512 MiB carve-out plus a 64 GiB GTT ceiling."""
    estimate = estimate_parallelism(
        _detected(dedicated=512 * MIB, shared=64 * GIB),
        PRODUCTION_MODELS,
        HOST_BYTES,
    )

    assert estimate.context_tokens == 40960
    assert estimate.parallelism == 5


def test_dgx_spark_shape() -> None:
    """GB10: unified memory, so the host reserve is what bounds it."""
    estimate = estimate_parallelism(
        _detected(dedicated=0, shared=119 * GIB),
        PRODUCTION_MODELS,
        HOST_BYTES,
    )

    assert estimate.context_tokens == 40960
    assert estimate.parallelism == 9


def test_discrete_24_gib_card_shape() -> None:
    """A 24 GiB card genuinely does not fit more than the floor at this context."""
    estimate = estimate_parallelism(
        _detected(dedicated=24 * GIB, shared=0),
        PRODUCTION_MODELS,
        HOST_BYTES,
    )

    assert estimate.context_tokens == 32768
    assert estimate.parallelism == MIN_PARALLELISM


def test_discrete_80_gib_card_shape() -> None:
    """A big card is spent in full, unlike a unified pool of the same size."""
    estimate = estimate_parallelism(
        _detected(dedicated=80 * GIB, shared=0),
        PRODUCTION_MODELS,
        HOST_BYTES,
    )

    assert estimate.parallelism == 7


def test_no_gpu_falls_back_to_the_floor() -> None:
    """CPU-only is a supported deployment, not an error."""
    detection = GpuDetection(GpuStatus.NO_DEVICE, None, "none")

    estimate = estimate_parallelism(detection, PRODUCTION_MODELS, HOST_BYTES)

    assert estimate.parallelism == MIN_PARALLELISM
