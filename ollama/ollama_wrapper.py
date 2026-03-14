#!/usr/bin/env python3
from math import floor
import os
import re
import sys
import time
import signal
import subprocess
import argparse

from typing import Iterator
from dataclasses import dataclass
from contextlib import contextmanager


# --- Constants ---
MIN_RESERVED_VRAM_FOR_MODEL_BYTES = 1 * (1024**3)
MIN_RESERVED_VRAM_FOR_CONTEXT_BYTES = 0.5 * (1024**3)
DEFAULT_CONTEXT_BYTES = 4096
OLLAMA_STARTUP_RETRIES = 10
OLLAMA_RETRY_INTERVAL = 0.3


# ---- Utils ---
def size_bytes_to_human(size_bytes: int) -> str:
    if size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    if size_bytes >= 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    return f"{size_bytes} B"


# --- Data classes ---
@dataclass
class ParallelismEstimate:
    """Result of estimating OLLAMA_NUM_PARALLEL and related settings."""

    parallelism: int
    largest_context_length: int | None = None


@dataclass
class ModelInfo:
    """Represents an installed Ollama model with its parsed size in bytes."""

    name: str
    size_bytes: int
    context_length_bytes: int | None = None  # Extracted from `ollama show`

    @property
    def size_human(self) -> str:
        return size_bytes_to_human(self.size_bytes)

    @property
    def context_length_human(self) -> str:
        return (
            size_bytes_to_human(self.context_length_bytes)
            if self.context_length_bytes
            else ""
        )

    @staticmethod
    def from_name_and_size_str(name: str, size_str: str) -> "ModelInfo":
        """Creates a ModelInfo instance and fetches context length via `ollama show`."""
        size_bytes = ModelInfo._parse_size_to_bytes(size_str)
        context_len = ModelInfo._get_context_length(name)
        return ModelInfo(
            name=name, size_bytes=size_bytes, context_length_bytes=context_len
        )

    @staticmethod
    def _parse_size_to_bytes(size_str: str) -> int:
        match = re.match(r"([\d.]+)\s*(gb|mb)", size_str.lower())
        if not match:
            raise ValueError(f"Invalid size string: {size_str}")
        size = float(match.group(1))
        unit = match.group(2)
        if unit == "gb":
            return int(size * 1024**3)
        if unit == "mb":
            return int(size * 1024**2)
        raise ValueError(f"Unknown unit in size string: {size_str}")

    @staticmethod
    def _get_context_length(model_name: str) -> int | None:
        """
        Parses the `context length` from `ollama show <model>` output.

        Args:
            model_name (str): The model name.

        Returns:
            int | None: Context length in tokens, or None if not found.
        """
        try:
            output = subprocess.check_output(["ollama", "show", model_name], text=True)
            match = re.search(r"context length\s+(\d+)", output, re.IGNORECASE)
            if match:
                return int(match.group(1))
            print(f"⚠️ No context length found for model '{model_name}'")
            return None
        except subprocess.CalledProcessError:
            print(f"❌ Failed to show model '{model_name}'")
            return None


# --- Ollama helpers ---
def wait_for_ollama_ready(
    retries: int = OLLAMA_STARTUP_RETRIES, interval: float = OLLAMA_RETRY_INTERVAL
) -> bool:
    """Waits for `ollama ps` to respond, indicating the server is ready."""
    for _ in range(retries):
        try:
            subprocess.check_output(["ollama", "ps"], stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            time.sleep(interval)
    return False


@contextmanager
def temporary_ollama_serve() -> Iterator[None]:
    """Starts `ollama serve` temporarily in the background, shuts it down on exit."""
    serve_process: subprocess.Popen | None = None
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
            serve_process.wait(timeout=5)


def get_installed_models() -> list[ModelInfo]:
    """Returns a list of installed models from `ollama list`."""
    with temporary_ollama_serve():
        output = subprocess.check_output(["ollama", "list"]).decode("utf-8")
        lines = output.strip().split("\n")[1:]
        models: list[ModelInfo] = []
        for line in lines:
            try:
                parts = re.split(r"\s{2,}", line.strip())
                name = parts[0]
                size_str = parts[2]

                models.append(ModelInfo.from_name_and_size_str(name, size_str))
            except Exception as ex:
                raise ValueError(f"Invalid model entry: {line}") from ex
        return models


def get_total_gpu_vram_mb() -> int | None:
    """Returns total VRAM from `nvidia-smi`, or None if not available."""
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,nounits,noheader"]
        )
        return int(output.decode("utf-8").strip().split("\n", maxsplit=1)[0])
    except Exception:
        return None


def calculate_parallelism(
    vram_bytes: int,
    model_count: int,
    total_model_size_bytes: int,
    largest_context_byte: int | None,
) -> int:
    """Estimates OLLAMA_NUM_PARALLEL given available and model memory."""
    usable_for_context_bytes = (
        vram_bytes - total_model_size_bytes - MIN_RESERVED_VRAM_FOR_MODEL_BYTES
    )
    if usable_for_context_bytes <= 0:
        return 1
    if largest_context_byte is None:
        largest_context_byte = DEFAULT_CONTEXT_BYTES
    return floor(
        max(
            usable_for_context_bytes
            // (
                model_count
                * (largest_context_byte + MIN_RESERVED_VRAM_FOR_CONTEXT_BYTES)
            ),
            1,
        )
    )


def estimate_parallelism() -> ParallelismEstimate:
    """Estimates a safe OLLAMA_NUM_PARALLEL from installed model and GPU memory."""
    models = get_installed_models()
    if not models:
        print("⚠️ No installed models found.")
        return ParallelismEstimate(parallelism=1)

    total_model_size_bytes = sum(m.size_bytes for m in models)
    print(f"📦 Total model size: {size_bytes_to_human(total_model_size_bytes)}")

    # Find largest context length if any model has it
    models_with_context = [m for m in models if m.context_length_bytes is not None]
    largest_context_length: int | None = None
    if models_with_context:
        largest_context = max(
            models_with_context,
            key=lambda m: (
                m.context_length_bytes if m.context_length_bytes is not None else 0
            ),
        )
        largest_context_length = largest_context.context_length_bytes
        print(
            f"💬 Largest context: {largest_context.name} ({largest_context.context_length_human})"
        )
    else:
        print("⚠️ No context length information found for any model.")

    vram_mb = get_total_gpu_vram_mb()
    if vram_mb is None:
        print("⚠️ No GPU detected. Assuming CPU-only environment.")
        return ParallelismEstimate(
            parallelism=1, largest_context_length=largest_context_length
        )
    print(f"🧠 GPU detected: {vram_mb} MB VRAM")

    vram_bytes = vram_mb * (1024**2)
    parallelism = calculate_parallelism(
        vram_bytes,
        len(models),
        total_model_size_bytes,
        largest_context_length,
    )
    return ParallelismEstimate(
        parallelism=parallelism, largest_context_length=largest_context_length
    )


# --- Mode handlers ---
def run_setup_command(ollama_args: list[str]) -> None:
    """Runs a one-shot Ollama command with a temporary server (e.g., `pull`, `list`)."""
    with temporary_ollama_serve():
        print(f"🔧 Running setup command: ollama {' '.join(ollama_args)}")
        subprocess.run(["ollama"] + ollama_args, check=True)


def run_entry_command(ollama_args: list[str]) -> None:
    """Runs a main Ollama command, estimating OLLAMA_NUM_PARALLEL if not already set."""
    env = os.environ.copy()

    estimate = estimate_parallelism()
    if "OLLAMA_NUM_PARALLEL" in env:
        print(f"🔧 Using pre-defined OLLAMA_NUM_PARALLEL={env['OLLAMA_NUM_PARALLEL']}")
    else:
        print(f"✅ Dynamically setting OLLAMA_NUM_PARALLEL={estimate.parallelism}")
        env["OLLAMA_NUM_PARALLEL"] = str(estimate.parallelism)

    if "OLLAMA_CONTEXT_LENGTH" in env:
        print(
            f"🔧 Using pre-defined OLLAMA_CONTEXT_LENGTH={env['OLLAMA_CONTEXT_LENGTH']}"
        )
    elif estimate is not None and estimate.largest_context_length is not None:
        print(
            f"✅ Dynamically setting OLLAMA_CONTEXT_LENGTH={estimate.largest_context_length}"
        )
        env["OLLAMA_CONTEXT_LENGTH"] = str(estimate.largest_context_length)

    # flush std*
    sys.stdout.flush()
    sys.stderr.flush()

    os.execvpe("ollama", ["ollama"] + ollama_args, env)


# --- CLI Parser ---
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wrapper for Ollama")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # setup mode
    setup_parser = subparsers.add_parser(
        "setup", help="Run a one-time ollama command with temporary server"
    )
    setup_parser.add_argument(
        "ollama_args", nargs=argparse.REMAINDER, help="Arguments passed to ollama"
    )

    # entry mode
    entry_parser = subparsers.add_parser(
        "entry", help="Run Ollama with estimated OLLAMA_NUM_PARALLEL"
    )
    entry_parser.add_argument(
        "ollama_args", nargs=argparse.REMAINDER, help="Arguments passed to ollama"
    )

    return parser.parse_args()


def main() -> None:
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
