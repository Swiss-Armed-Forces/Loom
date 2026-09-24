#!/usr/bin/env bash
# shellcheck disable=SC2034
set -eou pipefail

# Minimum resources required to deploy Loom.
# See README.md "Minimum Deployment Resources".
LOOM_MIN_CPU="8"
LOOM_MIN_MEMORY="25Gi"
LOOM_MIN_GPU="1"

TRAEFIK_HELM_VERSION="39.0.9"
TRAEFIK_IMAGE_VERSION="v3.6.15"

KEDA_HELM_VERSION="2.20.1"
KEDA_IMAGE_VERSION="2.20.1"

NAMESPACE="loom"

# The chat model the appliance console pins itself to (nixos/console.nix's
# loom-chat, via cicd/build_appliance_image.sh). Not a free choice: an
# air-gapped box only ever has the models baked into the ollama image, and the
# production target of ollama/Dockerfile pulls exactly this one plus the
# embedding model. Pointing the console at anything else gives a pane that
# cannot answer.
#
# Naming a model the workers do not use would also be wrong even if it were
# present -- ollama would load a second model and evict the one mid-index. So
# this tracks `_llmDefaults.model` in charts/values.yaml, and the appliance test
# asserts the value that reaches the image.
LOOM_CHAT_MODEL="huihui_ai/qwen3.5-abliterated:9b"

# The domain and every name under it, read out of the chart rather than
# restated here. `hostnames` in charts/values.yaml is what the pre-install Job
# names in the certificate's subjectAltName, and cicd/check_chart_hostnames.sh
# holds that list to the hosts the chart routes by name. A copy in this
# file would be a third statement of the same set with nothing checking it, and
# the failure it invites is quiet: a host in /etc/hosts that the certificate
# does not cover resolves fine and fails TLS verification.
#
# Resolved relative to this file rather than to the caller: vars.sh is sourced
# from several working directories, and a checkout carries the values file that
# belongs to it.
LOOM_VALUES_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/charts/values.yaml"

if ! command -v yq > /dev/null; then
    echo >&2 "[!] Error: yq is needed to read the hostnames out of"
    echo >&2 "    ${LOOM_VALUES_FILE}"
    exit 1
fi

if [[ ! -r "${LOOM_VALUES_FILE}" ]]; then
    echo >&2 "[!] Error: ${LOOM_VALUES_FILE} is not readable. vars.sh takes the"
    echo >&2 "    domain and the host list from the chart next to it."
    exit 1
fi

LOOM_DOMAIN="$(yq --raw-output '.domain' "${LOOM_VALUES_FILE}")"
# Both halves of `hostnames`: they differ in how they are served -- `extra` has
# no route naming it and is told apart by entrypoint -- but not in how they are
# named, so both need a hosts entry. Read, then sorted, in two steps rather than
# a pipeline, so `set -e` still sees yq fail.
#
# Sorted, so the list is a set rather than an order somebody has to maintain.
# The one place the order is visible is cicd/chrome_wrapped.sh, which opens a
# tab per entry: the focused first tab is now api.loom, where the hand-written
# array this replaced began with rabbit.loom.
LOOM_HOSTS_RAW="$(yq --raw-output '.hostnames.ingress[], .hostnames.extra[]' "${LOOM_VALUES_FILE}")"
LOOM_HOSTS_RAW="$(sort --unique <<< "${LOOM_HOSTS_RAW}")"

# An absent key leaves yq successful and empty, and a Loom whose hosts nothing
# resolves is worth failing on here rather than at the first curl.
if [[ -z "${LOOM_DOMAIN}" || "${LOOM_DOMAIN}" == "null" || -z "${LOOM_HOSTS_RAW}" ]]; then
    echo >&2 "[!] Error: could not read 'domain' and 'hostnames' from"
    echo >&2 "    ${LOOM_VALUES_FILE}"
    exit 1
fi

mapfile -t LOOM_HOSTS <<< "${LOOM_HOSTS_RAW}"
unset LOOM_HOSTS_RAW

LOOM_HOSTS_FQDN=()
for h in "${LOOM_HOSTS[@]}"; do
    LOOM_HOSTS_FQDN+=("${h}.${LOOM_DOMAIN}")
done
