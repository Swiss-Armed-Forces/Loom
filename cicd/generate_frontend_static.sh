#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TOPLEVEL_DIR="${SCRIPT_DIR}/.."

FRONTEND_DIR="${TOPLEVEL_DIR}/Frontend"
FRONTEND_STATIC_DIR="${FRONTEND_DIR}/public"
LICENSE_TXT="${TOPLEVEL_DIR}/LICENSE.txt"
CONTRIBUTING_MD="${TOPLEVEL_DIR}/CONTRIBUTING.md"
CODE_OF_CONDUCT_MD="${TOPLEVEL_DIR}/CODE_OF_CONDUCT.md"

VERBOSE=false
# THIRD-PARTY.md is not copied here. generate_third_party writes the frontend's
# copy itself, in the same run that writes the root file, so that the two cannot
# disagree; this script runs beside it rather than after it.
STEPS=(
    copy_license
    copy_contributing
    copy_code_of_conduct
    fix_frontend
)
SKIP=()

copy_license(){
    cp \
        "${LICENSE_TXT}" "${FRONTEND_STATIC_DIR}"
}

copy_contributing(){
    cp \
        "${CONTRIBUTING_MD}" "${FRONTEND_STATIC_DIR}"
}

copy_code_of_conduct(){
    cp \
        "${CODE_OF_CONDUCT_MD}" "${FRONTEND_STATIC_DIR}"
}

fix_frontend(){
    prek \
        run \
        --all-files \
        prettier_Frontend \
    || true
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
    echo "  --skip-STEP                         skip step STEP"
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
    --skip-*)
        SKIP+=("${1}")
        shift
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
    if [[ "${SKIP[*]}" == *"--skip-${step}"* ]]; then
        echo "[*] Skipping: ${step}"
        continue
    fi
    echo "[*] Running: ${step}"
    "${step}" "${ARGS[@]}"
done
