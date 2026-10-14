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
# Needs no cluster and no network: it is one yq and one grep.
set -eou pipefail

CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALUES_FILE="${CONTEXT_DIR}/charts/values.yaml"
DOCKERFILE="${CONTEXT_DIR}/ollama/Dockerfile.models"

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

missing=()
for model in "${declared[@]}"; do
    # Word-boundary match rather than a substring: model names share prefixes,
    # and `qwen3.5` must not be satisfied by `qwen3.5-abliterated`.
    if ! grep --quiet --word-regexp --fixed-strings -- "${model}" <<< "${baked}"; then
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
