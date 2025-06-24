#!/usr/bin/env bash
set -eou pipefail

if ! docker container inspect minikube &>/dev/null; then
    exit 0
fi

minikube ssh \
    -- \
    docker \
        system prune \
        --all \
        --volumes \
        --force