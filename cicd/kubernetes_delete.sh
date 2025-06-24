#!/usr/bin/env bash
set -eou pipefail

minikube delete \
    --all=true \
    --purge=true