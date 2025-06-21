#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

# Environment
SLEEP_TIME="${SLEEP_TIME:-0}"

#
# Main
#

atexit(){
    echo "[*] Exiting..."

    echo "[*] Fetching pod logs again"
    "${SCRIPT_DIR}/fetch_all_pod_logs.sh" \
        --subdir "at_exit"

    echo "[*] Listing all pods"
    kubectl get pods \
        --all-namespaces=true

    echo "[*] sleeping for: ${SLEEP_TIME}"
    sleep "${SLEEP_TIME}"
}
trap atexit EXIT

echo "[*] Start fetching pod logs"
"${SCRIPT_DIR}/fetch_all_pod_logs.sh" \
    --background \
    --subdir "at_start" \
    --follow

echo "[*] Running integrationtests"
poetry run \
    pytest \
    --exitfirst \
    --random-order \
    integrationtest