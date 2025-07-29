#!/usr/bin/env bash
# Runs all linting and formatting and checking on code files in SEARCH_DIR
# usage:
#   ./test-base "SEARCH_DIR"
#
set -euo pipefail

SEARCH_DIR="${1:-.}"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Shellcheck
echo ">> Shell lint"
SHELL_SOURCES_IGNORES=(
    charts/templates/minio/*.txt
)
SHELL_SOURCES=$("${SCRIPT_DIR}/find_file_of_type.sh" "${SEARCH_DIR}" '(shell|\.sh)' "${SHELL_SOURCES_IGNORES[@]}")
readarray -t -d '' SHELL_SOURCES < <(xargs --no-run-if-empty printf '%s\0' <<<"${SHELL_SOURCES:-}" || true)
if [[ "${#SHELL_SOURCES[@]}" -ne 0 ]]; then
    shellcheck -x \
        -o all \
        "${SHELL_SOURCES[@]}"
fi

# YAML lint
echo ">> YAML lint"
YAML_SOURCES_IGNORES=(
    "Frontend/pnpm-lock.yaml"
    charts/templates/**/*.yaml
    charts/templates/**/**/*.yaml
    charts/charts/minio/*.yaml
    charts/charts/minio/templates/*.yaml
)
YAML_SOURCES=$("${SCRIPT_DIR}/find_file_of_type.sh" "${SEARCH_DIR}" '(yaml|\.yml|\.sls|\.top)' "${YAML_SOURCES_IGNORES[@]}")
readarray -t -d '' YAML_SOURCES < <(xargs --no-run-if-empty printf '%s\0' <<<"${YAML_SOURCES:-}" || true)
if [[ "${#YAML_SOURCES[@]}" -ne 0 ]]; then
    yamllint \
        --strict \
        -d '{ extends: default, rules: { document-start: disable, line-length: {max: 165} } }' \
        "${YAML_SOURCES[@]}"
fi

# json lint
echo ">> JSON lint"
JSON_SOURCES_IGNORES=(
    "backend/api/static/redoc.standalone.js"
    "backend/api/static/swagger-ui-bundle.js"
)
JSON_SOURCES=$("${SCRIPT_DIR}/find_file_of_type.sh" "${SEARCH_DIR}" '(json|\.js|\.aql)' "${JSON_SOURCES_IGNORES[@]}")
readarray -t -d '' JSON_SOURCES < <(xargs --no-run-if-empty printf '%s\0' <<<"${JSON_SOURCES:-}" || true)
if [[ "${#JSON_SOURCES[@]}" -ne 0 ]]; then
    for js in "${JSON_SOURCES[@]}" ; do
        if ! jq . < "${js}" >/dev/null; then
            echo "Failed: ${js}"
            exit 1
        fi
    done
fi

# Dockerfile lint
echo ">> Dockerfile lint"
DOCKER_SOURCES_IGNORES=( )
DOCKER_SOURCES=$("${SCRIPT_DIR}/find_file_of_type.sh" "${SEARCH_DIR}" '(Dockerfile)' "${DOCKER_SOURCES_IGNORES[@]}")
readarray -t -d '' DOCKER_SOURCES < <(xargs --no-run-if-empty printf '%s\0' <<<"${DOCKER_SOURCES:-}" || true)
if [[ "${#DOCKER_SOURCES[@]}" -ne 0 ]]; then
    hadolint \
        "${DOCKER_SOURCES[@]}"
fi
# Check RUN commands for proper set flags
exit_code=0
for dockerfile in "${DOCKER_SOURCES[@]}"; do
    # Find RUN commands that don't start with set -exuo pipefail or set -exu
    if grep -n '^RUN ' "${dockerfile}" | grep -v -E '^[0-9]+:RUN (set -exuo? pipefail|set -exu)' | grep -q .; then
        >&2 echo "ERROR: Found RUN commands in ${dockerfile} that don't start with 'set -exuo pipefail' or 'set -exu':"
        grep -n '^RUN ' "${dockerfile}" | grep -v -E '^[0-9]+:RUN (set -exuo? pipefail|set -exu)'
        exit_code=1
    fi
done

# Exit with error code if any files failed
if [[ ${exit_code} -ne 0 ]]; then
    exit 1
fi

# Helm lint
echo ">> Helm lint"
HELM_SERACH_DIR="${SEARCH_DIR}/charts"
helm lint "${HELM_SERACH_DIR}"
