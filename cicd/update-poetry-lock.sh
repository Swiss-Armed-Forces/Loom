#!/usr/bin/env bash
set -euxo pipefail

GIT_TOPLEVEL=$(git rev-parse --show-toplevel)

# common must be first so dependent packages resolve against its updated lock
PYTHON_PROJECTS=(
    "backend/common"
    "backend/api"
    "backend/worker"
    "backend/crawler"
    "integrationtest"
    "."
)

for dir in "${PYTHON_PROJECTS[@]}"; do
    (
        cd "${GIT_TOPLEVEL}/${dir}"
        poetry lock
    )
done
