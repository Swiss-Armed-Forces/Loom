#!/usr/bin/env bash
set -euo pipefail

GIT_TOPLEVEL=$(git rev-parse --show-toplevel)

check_todo()
{
    cd "${GIT_TOPLEVEL}"
    ! git \
        --no-pager \
        grep \
            -I \
            --ignore-case \
            --line-number \
            TODO \
            -- \
                ':!devenv.nix' \
                ':!poetry.lock' \
                ':!backend/common/poetry.lock' \
                ':!backend/crawler/poetry.lock' \
                ':!backend/worker/poetry.lock' \
                ':!backend/api/poetry.lock' \
                ':!integrationtest/poetry.lock' \
                ':!backend/common/pyproject.toml' \
                ':!.pylintrc' \
                ':!cicd/check_todo.sh' \
                ':!backend/api/static' \
                ':!THIRD-PARTY-LICENSES.md'
}

check_todo
