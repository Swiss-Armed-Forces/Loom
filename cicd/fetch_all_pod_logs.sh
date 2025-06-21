#!/usr/bin/env bash
set -euo pipefail

# Set the namespace
NAMESPACE="loom"
PODS=$(kubectl get pods --namespace="${NAMESPACE}" -o name | sed 's|pod/||')

LOG_DIR="./logs"
LOG_DIR_SUBDIR=""
LOG_DIR_FINAL=""

VERBOSE=false
DO_BACKGROUND=false

#
# Utils
#

fetch_logs(){
    kubectl logs \
        --tail=-1 \
        "${POD_NAME}" \
        --all-containers=true \
        --namespace="${NAMESPACE}" \
        "${@}"
}

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>]"
    echo "  -h|--help                         show this help"
    echo "  -v|--verbose                      show verbose output"
    echo "  -b|--background                   fetch logs but in the background"
    echo "  -s|--subdor SUBDIR                write logs to a subdirectory SUBDIR"
}

#
# Argument parsing
#

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            usage
            trap - EXIT
            exit 0
        ;;
        -v|--verbose)
            VERBOSE=true
            shift
        ;;
        -b|--background)
            DO_BACKGROUND=true
            shift
        ;;
        -s|--subdir)
            shift
            LOG_DIR_SUBDIR="${1}"
            shift
        ;;
        *)
            ARGS+=("${1}")
            shift
        ;;
    esac
done

#
# Main
#

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

LOG_DIR_FINAL="${LOG_DIR}/${LOG_DIR_SUBDIR}"
mkdir -p "${LOG_DIR_FINAL}"

# Loop through each pod and save logs
for POD in ${PODS}; do
    # Use the full pod name
    POD_NAME="${POD}"
    LOG_FILE_BASE="${LOG_DIR_FINAL}/${POD_NAME}"

    echo "[*] Fetching logs for: ${POD_NAME}"

    if [[ "${DO_BACKGROUND}" = false ]]; then
      fetch_logs "${ARGS[@]}" > "${LOG_FILE_BASE}.log"
    else
      fetch_logs "${ARGS[@]}" > "${LOG_FILE_BASE}.log" &
    fi
done