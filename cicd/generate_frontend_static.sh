#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TOPLEVEL_DIR="${SCRIPT_DIR}/.."

FRONTEND_DIR="${TOPLEVEL_DIR}/Frontend"
THIRD_PARTY_LICENCES="THIRD-PARTY.md"
THIRD_PARTY_LICENCES_OUTPUT="${TOPLEVEL_DIR}/${THIRD_PARTY_LICENCES}"
FRONTEND_STATIC_DIR="${FRONTEND_DIR}/public"
LICENSE_TXT="${TOPLEVEL_DIR}/LICENSE.txt"
CHARTS_DIR="${TOPLEVEL_DIR}/charts"

VERBOSE=false
STEPS=(
    copy_third_party_license
    copy_license
    write_chart_data
    fix_frontend
)
SKIP=()

copy_third_party_license(){
    cp \
        "${THIRD_PARTY_LICENCES_OUTPUT}" "${FRONTEND_STATIC_DIR}"
}

copy_license(){
    cp \
        "${LICENSE_TXT}" "${FRONTEND_STATIC_DIR}"
}

write_chart_data(){
    helm \
        show chart "${CHARTS_DIR}" \
    | yq \
    > "${FRONTEND_STATIC_DIR}/chartData.json"
}

fix_frontend(){
    pre-commit \
        run \
        --all-files \
        prettier::Frontend \
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