#!/usr/bin/env bash
# Checks that local-override Helm values files contain no actual content.
#
# charts/values-overwrites.yaml and charts/values-up-flags.yaml are committed
# as empty templates. Any non-comment, non-blank line means content was
# accidentally staged for commit.
#
# Usage:
#   ./check_values_local_overrides.sh <file1> [file2] ...
#
set -euo pipefail

exit_code=0
for file in "$@"; do
    violations=$(grep --line-number --extended-regexp --invert-match '^\s*(#.*)?$' "${file}" || true)
    if [[ -n "${violations}" ]]; then
        >&2 echo "ERROR: ${file} contains content that should not be committed:"
        >&2 echo "${violations}"
        >&2 echo "This file is a local-override template and must remain empty."
        >&2 echo "Put your local overrides there but do not stage or commit them."
        exit_code=1
    fi
done

exit "${exit_code}"
