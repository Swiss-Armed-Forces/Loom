#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TOPLEVEL_DIR="${SCRIPT_DIR}/.."

VERBOSE=false
ACTION="test_git_files_changed"


test_git_files_changed() {
    (
        cd "${TOPLEVEL_DIR}"
        changes=$(git status --porcelain=v1 2>/dev/null)
        if [[ -n "${changes}" ]]; then
            echo >&2 "${changes}"
            echo >&2 "[*] Git files are not up to date"
            exit 1
        fi
    )
}

usage() {
    echo "usage: $0 [OPTIONS]"
    echo
    echo "With OPTIONS:"
    echo "  -v   |--verbose                     make verbose"
}

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
