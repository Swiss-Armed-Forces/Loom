#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TOPLEVEL_DIR="${SCRIPT_DIR}/.."

FRONTEND_DIR="${TOPLEVEL_DIR}/Frontend"
THIRD_PARTY_LICENCES="THIRD-PARTY-LICENSES.md"
THIRD_PARTY_LICENCES_OUTPUT="${TOPLEVEL_DIR}/${THIRD_PARTY_LICENCES}"
FRONTEND_STATIC_DIR="${FRONTEND_DIR}/public"
LICENSE_TXT="${TOPLEVEL_DIR}/License.txt"

VERBOSE=false
ACTION="copy_to_frontend_static"

copy_to_frontend_static(){
    cp \
        "${THIRD_PARTY_LICENCES_OUTPUT}" "${FRONTEND_STATIC_DIR}"
    cp \
        "${LICENSE_TXT}" "${FRONTEND_STATIC_DIR}"
}

#
# Usage
#

usage() {
    echo "usage: $0 [OPTIONS]"
    echo
    echo "With OPTIONS:"
    echo "  -h   |--help                        print this help"
    echo "  -v   |--verbose                     make verbose"
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

"${ACTION}" "${ARGS[@]}"
