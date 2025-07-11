#!/usr/bin/env bash
set -euxo pipefail

GIT_TOPLEVEL=$(git rev-parse --show-toplevel)

PYTHON_PROJECTS="$(git -C "${GIT_TOPLEVEL}" ls-files '*pyproject.toml')"
readarray -t PYTHON_PROJECTS <<< "${PYTHON_PROJECTS}"

for project in "${PYTHON_PROJECTS[@]}"; do
    dir=$(dirname "${project}")
    (
        cd "${dir}"
        poetry lock
    )
done
