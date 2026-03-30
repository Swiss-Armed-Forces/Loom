#!/usr/bin/env bash
# Checks that all RUN commands in Dockerfiles start with 'set -exuo pipefail' or 'set -exu'
#
# Usage:
#   ./check_dockerfile_run_flags.sh <dockerfile1> [dockerfile2] ...
#
set -euo pipefail

VALID_RUN_PATTERN='^[0-9]+:RUN (set -exuo? pipefail|set -exu)'

exit_code=0
for dockerfile in "$@"; do
    violations=$(
        grep \
            --line-number \
            '^RUN ' "${dockerfile}" \
        | grep \
            --invert-match \
            --extended-regexp \
            "${VALID_RUN_PATTERN}" \
        || true
    )
    if [[ -n "${violations}" ]]; then
        >&2 echo "ERROR: Found RUN commands in ${dockerfile} that don't start with 'set -exuo pipefail' or 'set -exu':"
        >&2 echo "${violations}"
        exit_code=1
    fi
done

exit "${exit_code}"
