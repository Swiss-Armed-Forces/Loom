#!/usr/bin/env bash
set -exuo pipefail

# check for whitespace errors
git_rev="$(git rev-parse origin/"${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-main}")"
git diff-tree --check \
    "${git_rev}" \
    HEAD \
    -- \
        . \
        ':!integrationtest/assets' \
        ':!backend/api/static'
