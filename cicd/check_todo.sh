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
            --line-number \
            TODO \
            -- \
                ':!.gitlab-ci.yml' \
                ':!.pylintrc' \
                ':!cicd/check_todo.sh' \
                ':!backend/api/static'
}

check_todo
