"""Entry policy and the parsing the estimate feeds on."""

import pytest

from ollama_wrapper import (
    MIN_PARALLELISM,
    NUM_PARALLEL_ENV,
    ParallelismEstimate,
    parse_context_length_tokens,
    parse_meminfo_total_bytes,
    parse_model_list,
    parse_size_to_bytes,
    plan_entry_environment,
    wants_estimate,
)

OLLAMA_LIST_OUTPUT = """NAME                          ID              SIZE      MODIFIED
huihui_ai/qwen3.5:9b          62387fdc1234    6.0 GB    2 days ago
nomic-embed-text-v2-moe       aabbccddeeff    512 MB    2 days ago
"""


def _estimate(parallelism: int) -> ParallelismEstimate:
    return ParallelismEstimate(
        parallelism=parallelism, context_tokens=40960, detail="test"
    )


# --- Entry policy ---
def test_a_preset_value_skips_the_estimate_entirely() -> None:
    """Estimating costs a whole temporary-server cycle for a discarded answer."""
    assert not wants_estimate({NUM_PARALLEL_ENV: "8"})
    assert wants_estimate({})


def test_a_preset_value_is_left_alone_however_small() -> None:
    """An explicit operator value outranks the estimate; 1 is legitimate."""
    plan = plan_entry_environment({NUM_PARALLEL_ENV: "1"}, _estimate(8))

    assert plan.num_parallel is None


def test_a_preset_value_is_left_alone_however_large() -> None:
    """The ceiling bounds the estimate, not what an operator asked for."""
    plan = plan_entry_environment({NUM_PARALLEL_ENV: "64"}, _estimate(8))

    assert plan.num_parallel is None


def test_an_unset_value_is_filled_from_the_estimate() -> None:
    """The ordinary case."""
    assert plan_entry_environment({}, _estimate(9)).num_parallel == 9


def test_no_estimate_and_no_preset_falls_back_to_the_floor() -> None:
    """Ollama's own default is 1, which is lower than Loom's worker concurrency."""
    assert plan_entry_environment({}, None).num_parallel == MIN_PARALLELISM


# --- Parsing ---
def test_the_context_length_is_read_in_tokens() -> None:
    """The number this used to treat as bytes."""
    assert parse_context_length_tokens("  context length    40960\n") == 40960
    assert parse_context_length_tokens("  parameters   9.7B\n") is None


def test_model_sizes_are_read_off_ollama_list() -> None:
    """Both units Ollama prints, and a refusal for anything else."""
    assert parse_size_to_bytes("6.0 GB") == 6 * (1024**3)
    assert parse_size_to_bytes("512 MB") == 512 * (1024**2)
    with pytest.raises(ValueError, match="1.2 TB"):
        parse_size_to_bytes("1.2 TB")


def test_the_model_table_is_parsed_past_its_header() -> None:
    """Columns are separated by runs of spaces, and names may contain slashes."""
    models = parse_model_list(OLLAMA_LIST_OUTPUT)

    assert [model.name for model in models] == [
        "huihui_ai/qwen3.5:9b",
        "nomic-embed-text-v2-moe",
    ]
    assert models[0].size_bytes == 6 * (1024**3)


def test_host_memory_is_read_in_kilobytes() -> None:
    """/proc/meminfo reports kB; inside a container it is the host's total."""
    meminfo = "MemTotal:       131072000 kB\nMemFree:         1000000 kB\n"

    assert parse_meminfo_total_bytes(meminfo) == 131072000 * 1024
    assert parse_meminfo_total_bytes("MemFree: 1000 kB\n") is None
