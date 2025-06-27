#!/usr/bin/env bash
set -eou pipefail

#
# Consts
#
DOCKER_CONFIG="${HOME}/.docker/config.json"

#
# Functions
#

check_if_auth_exists(){
    local registry_name
    registry_name="${1}" && shift
    jq \
        --exit-status \
        ".auths | has(\"${registry_name}\")" \
        "${DOCKER_CONFIG}" \
        &>/dev/null
}

#
# Arguments
#
REGISTRY_NAME="${1?Missing argument: REGISTRY_NAME}" && shift

#
# Main
#

# shellcheck disable=SC2310
if ! check_if_auth_exists "${REGISTRY_NAME}"; then
    >&2 echo "[!] Docker auth for '${REGISTRY_NAME}' not found"
    exit 1
fi
docker login "${REGISTRY_NAME}"
