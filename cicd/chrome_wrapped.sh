#!/usr/bin/env bash
#
# This script provides a way to locally test the infra with chrome
# all known domains will be resolve to LOOM_SERVER
#
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DEFAULT_LOOM_SERVER="127.0.0.1"
DEFAULT_LOOM_SERVER_PORT="8080"
DEFAULT_LOOM_SERVER_PORT_SET="80"

#
# Shared variables
#

# variables defined in vars.sh, here for shellcheck:
LOOM_HOSTS_FQDN=()

VARS_FILE="${SCRIPT_DIR}/../vars.sh"
# shellcheck disable=SC1091
# shellcheck source=../vars.sh
source "${VARS_FILE}"

#
# Runtime vars
#

LOOM_SERVER=""
LOOM_SERVER_PORT=""
LOOM_SERVER_RESOLVED=""
VERBOSE=false

#
# Utils
#

# Function to resolve DNS name to IP addresses
resolve_dns() {
    local dns_name="${1}"
    nslookup "${dns_name}" 2>/dev/null \
        | grep "Address:" \
        | tail -n1 \
        | awk '{ print $2 }'
}

# Function to check if the input is an IPv4 address
is_ipv4() {
    local ip="${1}"
    [[ "${ip}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

# Function to check if the input is an IPv6 address
is_ipv6() {
    local ip="${1}"
    [[ "${ip}" =~ ^[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){7}$ ]]
}

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>] [LOOM_SERVER]"
    echo "  -h|--help                         show this help"
    echo "  -v|--verbose                      show verbose output"
    echo
    echo "LOOM_SERVER: The server running loom, default: ${DEFAULT_LOOM_SERVER}:${DEFAULT_LOOM_SERVER_PORT}"
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


if [[ "${#ARGS[@]}" -lt 1 ]]; then
    LOOM_SERVER="${DEFAULT_LOOM_SERVER}"
    LOOM_SERVER_PORT="${DEFAULT_LOOM_SERVER_PORT}"
else
    LOOM_SERVER="${ARGS[0]}"
    LOOM_SERVER_PORT="${ARGS[1]:-${DEFAULT_LOOM_SERVER_PORT_SET}}"
fi

# Check if the input is an IP address or a DNS name
LOOM_SERVER_RESOLVED="${LOOM_SERVER}"
# shellcheck disable=SC2310
if ! is_ipv4 "${LOOM_SERVER}" && ! is_ipv6 "${LOOM_SERVER}"; then
    LOOM_SERVER_RESOLVED="$(resolve_dns "${LOOM_SERVER}")"
fi

echo "[*] LOOM_SERVER: ${LOOM_SERVER} -> ${LOOM_SERVER_RESOLVED}"
chromium \
    --new-instance \
    --host-rules="MAP * ${LOOM_SERVER_RESOLVED}:${LOOM_SERVER_PORT}" \
    "${LOOM_HOSTS_FQDN[@]}"
