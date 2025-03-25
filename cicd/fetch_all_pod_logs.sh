#!/usr/bin/env bash
set -euo pipefail

# Set the namespace
NAMESPACE="loom"
APPS=$(kubectl get deployments,statefulsets,daemonset --namespace="${NAMESPACE}" -o name)

LOG_DIR="./logs"
LOG_FILE_SUFFIX=""

VERBOSE=false
DO_BACKGROUND=false

#
# Utils
#

fetch_logs(){
    kubectl logs \
        --tail=-1 \
        --selector app="${APP_NAME}" \
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
    echo "  -s|--suffix SUFFIX                use SUFFIX as log file suffix"
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
        -s|--suffix)
            shift
            LOG_FILE_SUFFIX="${1}"
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

mkdir -p "${LOG_DIR}"

# Loop through each app and save logs
for APP in ${APPS}; do
    # Get base of deployment name
    APP_NAME=$(basename "${APP}")
    # Remove environement from deployment name
    APP_NAME="${APP_NAME#*-}"
    LOG_FILE_BASE="${LOG_DIR}/${APP_NAME}${LOG_FILE_SUFFIX}"

    echo "[*] Fetching logs for: ${APP_NAME}"

    if [[ "${DO_BACKGROUND}" = false ]]; then
      fetch_logs "${ARGS[@]}" > "${LOG_FILE_BASE}.log"
    else
      fetch_logs "${ARGS[@]}" > "${LOG_FILE_BASE}.log" &
    fi
done