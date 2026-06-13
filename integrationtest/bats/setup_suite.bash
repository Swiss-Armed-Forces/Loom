#!/usr/bin/env bash
# BATS suite-level setup/teardown for integrationtest/bats/
# Must live in this file (not in .bats files) so BATS actually executes it.

# shellcheck disable=SC2154  # BATS_SUITE_TMPDIR is set by the BATS runtime
# shellcheck source=integrationtest/bats/helpers.bash
source "$(dirname "${BASH_SOURCE[0]}")/helpers.bash"

setup_suite() {
    export MINIKUBE_HOME_TEMPLATE="${MINIKUBE_HOME:-${HOME}/.minikube}"

    # Stop any cluster running in the original home BEFORE switching MINIKUBE_HOME,
    # so minikube stop targets the correct (pre-existing) cluster state.
    minikube stop || true

    export MINIKUBE_HOME="${BATS_SUITE_TMPDIR}/minikube"
    reinitialize_minikube_home

    # Use a fresh temp directory for mount data. PVC files are written as root
    # inside minikube, so teardown_suite handles cleanup with sudo.
    export MOUNT_DIR="${BATS_SUITE_TMPDIR}/data"
    mkdir -p "${MOUNT_DIR}"
}

teardown_suite() {
    # Fully purge the isolated home; --all --purge removes all profiles and the
    # minikube directory itself.
    minikube delete --all=true --purge=true || true
    # PVC data inside MOUNT_DIR is written as root by processes inside minikube,
    # so BATS cannot remove it on its own; clean it up explicitly.
    sudo rm -rf "${MOUNT_DIR:?}"
}
