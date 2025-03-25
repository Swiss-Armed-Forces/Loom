#!/usr/bin/env bash
set -exou pipefail

docker system prune \
    --all \
    --volumes \
    --force
docker volume prune \
    --all \
    --force