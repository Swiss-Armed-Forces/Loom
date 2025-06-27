#!/usr/bin/env bash
set -euo pipefail

#
# Consts
#

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
GIT_TOPLEVEL=$(git rev-parse --show-toplevel)

OPENAPI_GENERATOR_CONFIG="${GIT_TOPLEVEL}/openapitools.json"
FRONTEND_API_DIR="${GIT_TOPLEVEL}/Frontend/src/app/api/generated"
OPENAPI_SCHEMA_TMP="$(mktemp)"

VERBOSE=false
ACTION="generate_frontend_api"

#
# Functions
#

generate_frontend_api() {
    echo "[*] Removing previously generated files"
    rm -rf \
        "${FRONTEND_API_DIR}"

    echo "[*] Generating openapi schema"
    "${SCRIPT_DIR}/generate_openapi_schema.py" > "${OPENAPI_SCHEMA_TMP}"

    echo "[*] Generating typescript client"
    export TS_POST_PROCESS_FILE="${SCRIPT_DIR}/generate_frontend_api.sh --post-process-typescript"
    openapi-generator-cli \
        generate \
            --config "${OPENAPI_GENERATOR_CONFIG}" \
            --generator-name "typescript-fetch" \
            --input-spec "${OPENAPI_SCHEMA_TMP}" \
            --enable-post-process-file \
            --output "${FRONTEND_API_DIR}"

    echo "[*] Check and fixing syntax"
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

usage() {
    echo "usage: $0 [OPTIONS]"
    echo
    echo "With OPTIONS:"
    echo "  -h   |--help                        print this help"
    echo "  -ppt | --post-process-typescript    post process a typescript file"
    echo "  -v   |--verbose                     make verbose"
}


#
# Atexit handler
#

atexit(){
    rm -rf "${OPENAPI_SCHEMA_TMP}"
}
trap atexit EXIT

#
# Argument parser
#

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
    -h | --help)
        usage
        exit 0
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