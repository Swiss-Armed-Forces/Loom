#!/usr/bin/env bash
set -eou pipefail

if ! docker container inspect minikube &>/dev/null; then
    >&2 echo "[!] minikube container not found"
    exit 0
fi

minikube ssh \
    -- \
    docker \
        system prune \
        "${@}"