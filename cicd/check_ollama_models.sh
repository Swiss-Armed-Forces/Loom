#!/usr/bin/env bash
#
# Asserts that the models baked into the production Ollama image are the models
# the chart actually asks for.
#
# `ollama/Dockerfile.models` hardcodes its production set as an `ARG
# LLM_MODELS`, and the chart names its own in `charts/values.yaml` --
# `_llmDefaults.model` for chat and `llm.embedding.model` for embeddings. They
# agree today and nothing made them.
#
# A drift is invisible until an air-gapped box is in front of somebody: the
# image carries only what was baked in, so a chat model the chart names and the
# image does not produces a console pane that cannot answer, and a worker that
# cannot summarise. vars.sh's `LOOM_CHAT_MODEL` reads the chart precisely so
# that the appliance console cannot be a third spelling of it, and says of this
# Dockerfile that it "pulls exactly `_llmDefaults.model`" -- which is the
# sentence this script makes true.
#
# It also holds `ollama_wrapper.py`'s HOST_RESERVE_BYTES to vars.sh's
# LOOM_MIN_MEMORY, for the same reason: the wrapper ships inside a container
# that cannot read vars.sh, the constant is a second copy of that value, and on
# a unified-memory box it is the only thing standing between ollama's budget and
# the rest of the stack.
#
# Needs no cluster and no network: it is one yq and one grep.
set -eou pipefail

CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALUES_FILE="${CONTEXT_DIR}/charts/values.yaml"
DOCKERFILE="${CONTEXT_DIR}/ollama/Dockerfile.models"
VARS_FILE="${CONTEXT_DIR}/vars.sh"
WRAPPER="${CONTEXT_DIR}/ollama/ollama_wrapper.py"

# The `pull-production` stage's own ARG, not the `pull-dev` one above it -- that
# one carries qwen2.5:0.5b and moondream, which is deliberately not what the
# chart names. Read from the stage line down, so a renamed stage leaves this
# empty and fails below rather than silently checking the wrong models.
baked="$(
    sed --quiet --regexp-extended \
        '/^FROM .* AS pull-production$/,/^FROM /{
            s/^ARG LLM_MODELS="?([^"]*)"?$/\1/p
        }' "${DOCKERFILE}" | head --lines=1
)"

if [[ -z "${baked}" ]]; then
    echo >&2 "[!] Error: no 'ARG LLM_MODELS=' line in ${DOCKERFILE}."
    echo >&2 "[!] If the image stopped taking its model list that way, this check needs"
    echo >&2 "[!] rewriting rather than deleting -- see the header."
    exit 1
fi

declared=()
for path in '._llmDefaults.model' '.llm.embedding.model'; do
    value="$(yq --raw-output "${path}" "${VALUES_FILE}")"
    if [[ -z "${value}" || "${value}" == "null" ]]; then
        echo >&2 "[!] Error: ${path} is not set in ${VALUES_FILE}."
        exit 1
    fi
    declared+=("${value}")
done

# One model name per line, so each can be compared whole.
#
# `grep --word-regexp` is not that comparison and the counterexample is the one
# this check is about: `-w` only requires the match to be bounded by non-word
# characters, and `-`, `.` and `:` are all non-word -- so a Dockerfile baking
# `qwen3.8:27b-instruct` satisfies a chart asking for `qwen3.8:27b`, and the box
# carries no model the chart names. `-x` against the split list compares tokens.
baked_lines="$(tr ' ' '\n' <<< "${baked}")"

missing=()
for model in "${declared[@]}"; do
    if ! grep --quiet --line-regexp --fixed-strings -- "${model}" <<< "${baked_lines}"; then
        missing+=("${model}")
    fi
done

if (( ${#missing[@]} > 0 )); then
    echo >&2 "[!] Error: ${DOCKERFILE} does not bake every model the chart names."
    echo >&2 "[!]   baked:   ${baked}"
    echo >&2 "[!]   missing: ${missing[*]}"
    echo >&2 "[!] An air-gapped box has only what the image carries, so a chart that names"
    echo >&2 "[!] a model the image does not pull gives a console pane that cannot answer."
    exit 1
fi

echo "[*] ollama/Dockerfile.models bakes every model charts/values.yaml names."

# --- the host reserve, which is LOOM_MIN_MEMORY in another spelling ---

# shellcheck disable=SC1090
source "${VARS_FILE}"

if [[ -z "${LOOM_MIN_MEMORY:-}" ]]; then
    echo >&2 "[!] Error: ${VARS_FILE} defines no LOOM_MIN_MEMORY."
    exit 1
fi

# `25Gi` -> gibibytes. The two spellings are deliberately different -- one is a
# Kubernetes quantity, the other a Python expression -- so the comparison is of
# the numbers, not of the text.
want_gib="${LOOM_MIN_MEMORY%Gi}"
if [[ "${want_gib}" == "${LOOM_MIN_MEMORY}" ]]; then
    echo >&2 "[!] Error: LOOM_MIN_MEMORY is '${LOOM_MIN_MEMORY}', which this check only"
    echo >&2 "[!] understands in gibibytes (e.g. 25Gi)."
    exit 1
fi

have_gib="$(
    sed --quiet --regexp-extended \
        's/^HOST_RESERVE_BYTES = ([0-9]+) \* \(1024\*\*3\)$/\1/p' "${WRAPPER}" |
        head --lines=1
)"

if [[ -z "${have_gib}" ]]; then
    echo >&2 "[!] Error: no 'HOST_RESERVE_BYTES = N * (1024**3)' line in ${WRAPPER}."
    echo >&2 "[!] If the constant changed shape, this check needs rewriting rather than"
    echo >&2 "[!] deleting -- see the header."
    exit 1
fi

if [[ "${have_gib}" != "${want_gib}" ]]; then
    echo >&2 "[!] Error: the host reserve is spelled twice and the two disagree."
    echo >&2 "[!]   vars.sh LOOM_MIN_MEMORY:        ${want_gib}Gi"
    echo >&2 "[!]   ollama_wrapper.py HOST_RESERVE: ${have_gib}Gi"
    echo >&2 "[!] On a unified-memory box that constant is what keeps ollama's budget off"
    echo >&2 "[!] the memory the rest of Loom is living in."
    exit 1
fi

echo "[*] ollama_wrapper.py reserves the ${want_gib}Gi vars.sh asks for."
