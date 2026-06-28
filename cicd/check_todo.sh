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
                ':!*.lock' \
                ':!**/*.lock' \
                ':!backend/common/pyproject.toml' \
                ':!.pylintrc' \
                ':!cicd/check_todo.sh' \
                ':!backend/api/static' \
                ':!THIRD-PARTY.md' \
                ':!Frontend/public/THIRD-PARTY.md' \
                ':!Documentation/ContainerDiagram.svg'
}

check_todo
