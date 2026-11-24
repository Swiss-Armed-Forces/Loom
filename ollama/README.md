# `ollama/` — the Ollama container images

The entrypoint of the Ollama container, and the two images it ships in. What an operator has to
set — the values for a GPU, the volume the models live on, the environment overrides — is in
[../Documentation/installation.md](../Documentation/installation.md); this file is about the code.

## Files

| File | What it is |
| --- | --- |
| `Dockerfile.runtime` | The Ollama server image. `GPU_VARIANT` selects the NVIDIA or the ROCm base, both pinned by digest. Adds python3 and the three wrapper modules, side by side so that a script run by path resolves its siblings off `sys.path`. |
| `Dockerfile.models` | The models, in an image of their own, copied into Ollama's storage by an initContainer. `ARG LLM_MODELS` names what it pulls; the published target is alpine plus the blobs, so the base's CUDA runtime stays behind in the pull stage. |
| `pull_models.sh` | What the pull stage runs. Keeps `ollama pull`'s progress bar out of the job log, which it would otherwise overrun. |
| `ollama_wrapper.py` | The entrypoint. `entry` decides the environment and then becomes ollama; `setup` runs a one-shot ollama command against a temporary server, which is what `ollama pull` needs. |
| `nvml.py` | The `libnvidia-ml` binding the GPU memory probe reads through, via `ctypes`. |
| `cpu_quota.py` | The CPU quota the container's cgroup enforces, and the thread count that follows from it. |
| `tests/` | The pytest suite for all of the above. |

Both Dockerfiles pin the same Ollama version, and have to: a model pulled by 0.40 or newer is
written in a manifest format a pre-0.40 runtime cannot read.

## Tests

`ollama-test` runs `ollama/tests`; extra arguments go to pytest. It is a script of its own because
`backend-test` cds into `backend/` and cannot reach this directory, and because `appliance-pytest`
is the appliance's suites sharing one pytest session. It also runs as a git hook on any change to
`ollama/*.py`, so `devenv test` covers it and there is no CI job of its own.

Every probe in the wrapper takes its filesystem root as an argument — `SYSFS_ROOT`, `PROC_ROOT`,
`DEV_ROOT` in `ollama_wrapper.py`, `SYSFS_ROOT` in `cpu_quota.py` — so a test points it at a
fixture tree instead of patching anything.

## What the entrypoint decides

### The GPU it can see

`LOOM_GPU_VENDOR`, set by `charts/values-{amd,nvidia}-gpu.yaml`, picks how the container reads the
GPU's memory: NVML for NVIDIA, amdgpu's sysfs attributes for AMD, the ROCm image shipping no
`rocm-smi`. NVML rather than `nvidia-smi` because the container toolkit injects a NixOS host's
driver executables without the ELF interpreter they need, so they cannot exec in a pod.

When the variable names a vendor whose device node is absent, the container **refuses to start**
rather than falling back to the CPU — a pod deployed as a GPU workload that cannot reach a GPU
fails in milliseconds, not after a whole server cycle. Left empty, the container autodetects and a
CPU fallback is silent.

### `OLLAMA_NUM_PARALLEL`

Sized against the memory the container can actually see, because KV cache is `context × parallel`
and choosing the parallelism is really choosing how much context survives. Taking the value from
the chart would mean choosing it without the one number that decides it. The slot count is then
held to the CPU quota as well, since slots past it add KV cache for throughput the CPU cannot
deliver.

### `LLAMA_ARG_THREADS`

llama.cpp sizes its thread pool from the CPUs the host has, and honours neither the CFS quota nor a
cpuset. Inside a limited container it therefore starts one compute thread per host core: 192
threads under a ten-core limit spin-wait on each other, every CFS period is throttled, and prompt
processing costs roughly thirty times what it should. `cpu_quota.py` reads the budget the kernel
already enforces and the entrypoint sets the thread count to it, less one core for ollama's own Go
runtime.

The quota comes from the container's `cpu.max` (cgroup v1's `cpu.cfs_quota_us` pair as a fallback)
rather than from `ollama.resources.limits.cpu`, because that value is an intent and the cgroup is
what throttles: an overwrite layer, a `LimitRange` or a node without CFS quota can each make the
two differ. Where no quota is enforced nothing is set, llama.cpp's own sizing being right on an
unconstrained host.

`LLAMA_ARG_THREADS` is llama.cpp's own variable, read by the argument parser ollama links in and
not by ollama's configuration layer — `ollama serve --help` documents only `LLAMA_ARG_FIT` and
`LLAMA_ARG_FIT_TARGET` of that table. It is the one knob that reaches the runner for every
endpoint: `options.num_thread`, the one ollama does document, is accepted by `POST /v1/systemone`
and discarded. Upstream [ollama/ollama#17916](https://github.com/ollama/ollama/issues/17916) is
open for the quota detection this stands in for.

### `OLLAMA_CONTEXT_LENGTH`, deliberately not set

Ollama sizes the context from its own VRAM measurement and walks it back down a
256k → 32k → 4k ladder when a load fails. Setting the variable turns that off. The trained context
length is read here only to price a slot of KV cache.

### Anything an operator set

Both variables the entrypoint works out — `OLLAMA_NUM_PARALLEL` and `LLAMA_ARG_THREADS` — yield to
a value already in the environment, so `ollama.extraEnv` keeps the last word.
