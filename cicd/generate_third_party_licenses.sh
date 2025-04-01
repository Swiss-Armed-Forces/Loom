#!/usr/bin/env bash
set -euo pipefail

GIT_TOPLEVEL=$(git rev-parse --show-toplevel)
FRONTEND_DIR="${GIT_TOPLEVEL}/Frontend"

THIRD_PARTY_LICENES="${GIT_TOPLEVEL}/THIRD-PARTY-LICENSES.md"

DO_TEST=false
VERBOSE=false
ACTION="generate_third_party_licenses"

generate_third_party_licenses() {
    {
        echo "# Third Party Licenses"
        echo "<!-- markdownlint-disable -->"
        echo "This Project uses the following open source software"
        echo
        echo "## Python Licenses"
        echo
        pip-licenses \
            --order=license \
            --format=markdown
        echo
        echo "## JavaScript Licenses"
        echo
        license-report \
            --package "${FRONTEND_DIR}/package.json"  \
            --output markdown \
            --fields name \
            --fields licenseType \
            --fields installedVersion
    } \
    | uniq \
    | sed \
        's/[[:space:]]\+$//' \
    | sed \
        '${/^$/d;}' \
    > "${THIRD_PARTY_LICENES}"
}


test_if_files_changed() {
    changes=$(git status --porcelain=v1 -- "${THIRD_PARTY_LICENES}" 2>/dev/null)
    if [[ -n "${changes}" ]]; then
        echo >&2 "${changes}"
        echo >&2 "[*] Third party licenses are not up to date"
        exit 1
    fi
}

usage() {
    echo "usage: $0 [OPTIONS]"
    echo
    echo "With OPTIONS:"
    echo "  -t   |--test                        test if files are up to date"
    echo "  -v   |--verbose                     make verbose"
}

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
    -h | --help)
        usage
        exit 0
        ;;
    -t | --test)
        DO_TEST=true
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

if [[ "${DO_TEST}" = true ]]; then
    test_if_files_changed
fi
