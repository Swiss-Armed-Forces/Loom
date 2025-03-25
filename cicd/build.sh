#!/usr/bin/env bash
# Builds the whole application

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
STEPS=(
    build_traefik
    build_application
)

#
# Runtime vars
#
VERBOSE=false

#
# Steps
#

build_traefik(){
    (
        cd "${SCRIPT_DIR}/../traefik"
        # Note: use the wrapper here
        ./skaffold build \
            "${@}"
    )
}

build_application(){
    (
        cd "${SCRIPT_DIR}/../"
        skaffold build \
            "${@}"
    )
}

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>]"
    echo "  -h|--help                         show this help"
    echo "  -v|--verbose                      show verbose output"
}

#
# Argument parsing
#

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
    -h | --help)
        usage
        exit 0
        ;;
    -v | --verbose)
        VERBOSE=true
        ;;
    *)
        ARGS+=("${1}")
        ;;
    esac
    shift
done

#
# Main
#

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

# execute steps
for step in "${STEPS[@]}"; do
    echo "[*] Running: ${step}"
    "${step}" "${ARGS[@]}"
done