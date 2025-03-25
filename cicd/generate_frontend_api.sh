#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
GIT_TOPLEVEL=$(git rev-parse --show-toplevel)

OPENAPI_GENERATOR_CONFIG="${GIT_TOPLEVEL}/openapitools.json"
FRONTEND_API_DIR="${GIT_TOPLEVEL}/Frontend/src/app/api/generated"
API_URL="http://api.loom"

DO_TEST=false
VERBOSE=false
ACTION="generate_frontend_api"

generate_frontend_api() {
    # first, remove all files previously generated
    rm -rf \
        "${FRONTEND_API_DIR}"

    # then, fresh generate files
    export TS_POST_PROCESS_FILE="${SCRIPT_DIR}/generate_frontend_api.sh --post-process-typescript"
    # disable certificate verification
    export JAVA_OPTS="-Dio.swagger.parser.util.RemoteUrl.trustAll=true -Dio.swagger.v3.parser.util.RemoteUrl.trustAll=true"

    openapi-generator-cli \
        generate \
            --config "${OPENAPI_GENERATOR_CONFIG}" \
            --generator-name "typescript-fetch" \
            --input-spec "${API_URL}/openapi.json" \
            --enable-post-process-file \
            --output "${FRONTEND_API_DIR}"

    # last, fix all the generated files
    "${SCRIPT_DIR}/check-syntax.sh" \
        --fix \
        --skip-python
}

post_process_typescript() {
    # Add ts-nocheck to the top of each generated file
    # This is required because the generated code contains unused symbols
    # see: https://github.com/OpenAPITools/openapi-generator/issues/8961
    sed \
        --in-place \
        '3i // @ts-nocheck' \
        "${@}"

    # Make API location relative to window.location.origin
    # shellcheck disable=SC2016
    sed \
        --in-place \
        --regexp-extended \
        's|^(export const BASE_PATH = )("[^"]+")(.*)$|\1`${window.location.origin}/api`\3|' \
        "${@}"
}

test_if_files_changed() {
    changes=$(git status --porcelain=v1 -- "${FRONTEND_API_DIR}" 2>/dev/null)
    if [[ -n "${changes}" ]]; then
        echo >&2 "${changes}"
        echo >&2 "[*] Frontend api is not up to date"
        exit 1
    fi
}

usage() {
    echo "usage: $0 [OPTIONS]"
    echo
    echo "With OPTIONS:"
    echo "  -t   |--test                        test if frontend types are up to date"
    echo "  -ppt | --post-process-typescript    post process a typescript file"
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
    -ppt | --post-process-typescript)
        ACTION="post_process_typescript"
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
