#!/usr/bin/env bash

set -euo pipefail

VERBOSE=false
PUBLISH=false

PACKAGE_NAME=loom

STEPS=(
    build_chart
)

build_chart(){
    output=$(helm package charts/ 2>&1) || {
        echo "Error: Failed to package Helm chart."
        echo "${output}"
        return 1
    }
    PACKAGE_NAME=$(echo "${output}" | awk '/Successfully packaged chart and saved it to:/{print $NF}')
    echo "Packaged Helm chart to ${PACKAGE_NAME}"
}

publish_chart(){
    curl --fail-with-body \
        --request POST \
        --form "chart=@${PACKAGE_NAME}" \
        --user "${USER}" \
        "${PACKAGE_REGISTRY}"
}

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>]"
    echo "  -h|--help                         show this help"
    echo "  -v|--verbose                      show verbose output"
    echo "  -u|--user                         user acess in format user:acessToken"
    echo "  -r|--package-registry             url for the package registry"
    echo "  -p|--publish                      publish the chart needs registry"
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
        shift
        ;;
    -p | --publish)
        PUBLISH=true
        shift
        ;;
    -u | --user)
        shift
        USER="${1}"
        shift
        ;;
    -r | --package-registry)
        shift
        PACKAGE_REGISTRY="${1}"
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

if [[ "${PUBLISH}" = true ]]; then
    if [[ -z "${PACKAGE_REGISTRY}" ]]; then
        echo "package registry is not set"
        exit 1
    fi
    STEPS+=(publish_chart)
fi

# execute steps
for step in "${STEPS[@]}"; do
    echo "[*] Running: ${step}"
    "${step}" "${ARGS[@]}"
done