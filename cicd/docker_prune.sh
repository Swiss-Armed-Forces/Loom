#!/usr/bin/env bash
set -eou pipefail

docker system prune \
    --all \
    --volumes \
    --force
docker volume prune \
    --all \
    --force