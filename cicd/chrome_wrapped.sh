#!/usr/bin/env bash
#
# This script provides a way to locally test the infra with chrome
# all known domains will be resolve to LOOM_SERVER
#
# Note that --host-rules maps *every* name to LOOM_SERVER regardless of which
# tabs are opened, so the one default tab below costs nothing in reachability:
# any *.loom link followed from it still lands on the same server.
#
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DEFAULT_LOOM_SERVER="127.0.0.1"
DEFAULT_LOOM_SERVER_PORT="8080"
DEFAULT_LOOM_SERVER_PORT_SET="80"

# The host to open. One tab, not one per entry in LOOM_HOSTS_FQDN: opening all
# of them -- two dozen, and growing with every service added to the chart --
# means two dozen self-signed certificate interstitials to click through before
# reaching the one page anybody wanted.
LOOM_HOST="frontend"

#
# Shared variables
#

# variables defined in vars.sh, here for shellcheck:
LOOM_DOMAIN=""

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
    echo "usage: ${0} [<options>] [LOOM_SERVER [LOOM_SERVER_PORT]]"
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

# A URL rather than a bare hostname, because chromium decides for itself what
# to do with `frontend.loom` on a command line and the answer is not stable.
#
# The scheme follows the port rather than being fixed: 8080 and 80, the two
# defaults above, are the http that a local port-forward serves, while a box
# reached on 443 serves only https -- every ingress in charts/values.yaml is
# annotated `router.entrypoints: websecure` and only values-development widens
# that to `web`, so http there reaches an entrypoint that routes nothing and
# answers 404 on a stack that is perfectly healthy.
if [[ "${LOOM_SERVER_PORT}" = 443 ]]; then
    LOOM_URL="https://${LOOM_HOST}.${LOOM_DOMAIN}"
else
    LOOM_URL="http://${LOOM_HOST}.${LOOM_DOMAIN}"
fi

echo "[*] LOOM_SERVER: ${LOOM_SERVER} -> ${LOOM_SERVER_RESOLVED}:${LOOM_SERVER_PORT}"
echo "[*] Opening: ${LOOM_URL}"
chromium \
    --new-instance \
    --host-rules="MAP * ${LOOM_SERVER_RESOLVED}:${LOOM_SERVER_PORT}" \
    "${LOOM_URL}"
