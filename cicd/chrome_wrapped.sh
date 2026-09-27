#!/usr/bin/env bash
#
# This script provides a way to locally test the infra with chrome
# all known domains will be resolve to LOOM_SERVER
#
# Note that --host-rules maps *every* name to LOOM_SERVER regardless of which
# tabs are opened, so the one default tab below costs nothing in reachability:
# any *.loom link followed from it still lands on the same server.
#
# The mapping is written as one rule per port rather than as a single catch-all.
# See the rules built in Main for why.
#
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DEFAULT_LOOM_SERVER="127.0.0.1"

# With no server named this points at a local VM, so the defaults are the two
# ports cicd/run_appliance_vm.sh forwards to it: `hostfwd=tcp::8080-:80` and
# `hostfwd=tcp::8443-:443`. They have to be taken as a pair -- mapping both of
# traefik's entrypoints onto the http forward is exactly the 404 this script
# used to produce.
DEFAULT_LOOM_HTTP_PORT="8080"
DEFAULT_LOOM_HTTPS_PORT="8443"

# A named server is a box addressed directly, which serves traefik on the
# standard ports.
DEFAULT_LOOM_HTTP_PORT_SET="80"
DEFAULT_LOOM_HTTPS_PORT_SET="443"

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
LOOM_HTTP_PORT=""
LOOM_HTTPS_PORT=""
LOOM_SERVER_RESOLVED=""
LOOM_HOST_RULES=""
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

# Function to check if the input is a port number. Checked rather than passed
# through, because chromium takes an unparsable --host-rules entry by dropping
# it, leaving a browser that reaches the real internet instead of the box and
# says nothing about it.
is_port() {
    local port="${1}"
    [[ "${port}" =~ ^[0-9]+$ ]] && (( port >= 1 && port <= 65535 ))
}

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>] [LOOM_SERVER [LOOM_HTTP_PORT [LOOM_HTTPS_PORT]]]"
    echo "  -h|--help                         show this help"
    echo "  -v|--verbose                      show verbose output"
    echo
    echo "LOOM_SERVER:     The server running loom"
    echo "                 default: ${DEFAULT_LOOM_SERVER}"
    echo "LOOM_HTTP_PORT:  The port serving traefik's 'web' entrypoint"
    echo "                 default: ${DEFAULT_LOOM_HTTP_PORT}, or ${DEFAULT_LOOM_HTTP_PORT_SET} with LOOM_SERVER given"
    echo "LOOM_HTTPS_PORT: The port serving traefik's 'websecure' entrypoint"
    echo "                 default: ${DEFAULT_LOOM_HTTPS_PORT}, or ${DEFAULT_LOOM_HTTPS_PORT_SET} with LOOM_SERVER given"
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


if [[ "${#ARGS[@]}" -gt 3 ]]; then
    echo >&2 "[!] Error: at most 3 positional arguments, got ${#ARGS[@]}"
    usage >&2
    exit 1
fi

if [[ "${#ARGS[@]}" -lt 1 ]]; then
    LOOM_SERVER="${DEFAULT_LOOM_SERVER}"
    LOOM_HTTP_PORT="${DEFAULT_LOOM_HTTP_PORT}"
    LOOM_HTTPS_PORT="${DEFAULT_LOOM_HTTPS_PORT}"
else
    LOOM_SERVER="${ARGS[0]}"
    LOOM_HTTP_PORT="${ARGS[1]:-${DEFAULT_LOOM_HTTP_PORT_SET}}"
    LOOM_HTTPS_PORT="${ARGS[2]:-${DEFAULT_LOOM_HTTPS_PORT_SET}}"
fi

for LOOM_PORT in "${LOOM_HTTP_PORT}" "${LOOM_HTTPS_PORT}"; do
    # shellcheck disable=SC2310
    if ! is_port "${LOOM_PORT}"; then
        echo >&2 "[!] Error: '${LOOM_PORT}' is not a port number"
        usage >&2
        exit 1
    fi
done

# Check if the input is an IP address or a DNS name
LOOM_SERVER_RESOLVED="${LOOM_SERVER}"
# shellcheck disable=SC2310
if ! is_ipv4 "${LOOM_SERVER}" && ! is_ipv6 "${LOOM_SERVER}"; then
    LOOM_SERVER_RESOLVED="$(resolve_dns "${LOOM_SERVER}")"
fi

# One rule per port, rather than the single `MAP *` this used to build. A
# catch-all rewrites the *port* as well as the host, so it also caught the
# `https://` that every Loom redirects to and sent it back at the http port --
# where no router matches, because every ingress in charts/values.yaml is
# annotated `router.entrypoints: websecure` and only values-development widens
# that to `web`. Traefik answered 404 on a stack that was perfectly healthy.
#
# The patterns are the ports chromium asks for, which are the scheme defaults
# and not the ports below: what is being mapped is `http://` and `https://`,
# onto wherever this particular server happens to serve them.
LOOM_HOST_RULES="MAP *:80 ${LOOM_SERVER_RESOLVED}:${LOOM_HTTP_PORT}"
LOOM_HOST_RULES+=",MAP *:443 ${LOOM_SERVER_RESOLVED}:${LOOM_HTTPS_PORT}"

# A URL rather than a bare hostname, because chromium decides for itself what
# to do with `frontend.loom` on a command line and the answer is not stable.
#
# http, fixed, now that both ports are mapped: on a box it is one redirect to
# https, and under charts/values-development.yaml -- the one configuration that
# widens the routers to the `web` entrypoint -- there is no redirect and http is
# all that is served. Naming https instead would be one hop shorter on a box and
# refused outright in development.
LOOM_URL="http://${LOOM_HOST}.${LOOM_DOMAIN}"

echo "[*] LOOM_SERVER: ${LOOM_SERVER} -> ${LOOM_SERVER_RESOLVED}"
echo "[*] Host rules:  ${LOOM_HOST_RULES}"
echo "[*] Opening:     ${LOOM_URL}"
chromium \
    --new-instance \
    --host-rules="${LOOM_HOST_RULES}" \
    "${LOOM_URL}"
