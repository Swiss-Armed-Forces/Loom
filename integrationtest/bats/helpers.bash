#!/usr/bin/env bash
# Shared helpers for integrationtest/bats/ tests.
# Loaded via `load helpers` in .bats files and sourced in setup_suite.bash.

# shellcheck disable=SC2154  # MINIKUBE_HOME, MINIKUBE_HOME_TEMPLATE are exported by setup_suite

# Re-copy the cached template into MINIKUBE_HOME and remove any stale cluster
# container it references, so the next minikube start always creates a fresh
# cluster. Assumes MINIKUBE_HOME and MINIKUBE_HOME_TEMPLATE are already set.
reinitialize_minikube_home() {
    rm -rf "${MINIKUBE_HOME:?}"
    if [[ -d "${MINIKUBE_HOME_TEMPLATE}" ]]; then
        cp -a "${MINIKUBE_HOME_TEMPLATE}" "${MINIKUBE_HOME}"
    else
        mkdir -p "${MINIKUBE_HOME}"
    fi
    # The copy references the original cluster's Docker container (stopped or
    # already deleted). Remove it so minikube start isn't constrained by its
    # configuration (e.g. missing --mount-string).
    minikube delete --all=true || true
}
