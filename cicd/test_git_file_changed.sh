#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TOPLEVEL_DIR="${SCRIPT_DIR}/.."

VERBOSE=false
ACTION="test_git_files_changed"
CHANGED_FILES_ARCHIVE="changed-files/"

test_git_files_changed() {
    (
        cd "${TOPLEVEL_DIR}"
        # Get changed files (staged and unstaged)
        local has_changed_files
        has_changed_files=false

        local status
        local path
        while read -r status path; do
            >&2 echo "[*] Changed path: '${path}' (status: ${status})"

            # Create directory structure if needed
            mkdir -p "${CHANGED_FILES_ARCHIVE}/$(dirname "${path}")"

            # Copy the path to the changed files archive
            cp -r "${path}" "${CHANGED_FILES_ARCHIVE}/${path}"
            has_changed_files=true
        done < <(git status --porcelain=v1 2>/dev/null || true)

        if [[ "${has_changed_files}" = true ]]; then
            >&2 echo "[*] Some files are not up to date"
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
