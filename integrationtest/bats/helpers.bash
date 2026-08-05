#!/usr/bin/env bash
# Shared helpers for integrationtest/bats/ tests.
# Loaded via `load helpers` in .bats files and sourced in setup_suite.bash.

# shellcheck disable=SC2154  # MINIKUBE_HOME, MINIKUBE_HOME_TEMPLATE are exported by setup_suite

# Global setup executed by BATS before every @test block.
# Reinitializes the minikube home so every test starts with a clean cluster.
setup() {
    reinitialize_minikube_home
}

# Global teardown executed by BATS after every @test block.
# Undeploys all Helm releases (+ docker prune) and removes root-owned PVC data.
# Cluster reinitialization is left to setup() so a failed test's cluster state
# can be inspected before the next test wipes it.
teardown() {
    bash -c "cd '${REPO_DIR}' && ./up.sh --down" || true
    # Remove root-owned PVC data so teardown_suite can delete MOUNT_DIR without
    # sudo. minikube ssh connects as the docker user (non-root) and cannot delete
    # root-owned files; docker exec runs as root and can. When --mount-string is
    # active, /var/hostpath-provisioner is bind-mounted from MOUNT_DIR on the
    # host, so deleting its contents here propagates to the host filesystem.
    # Matches MINIKUBE_HOSTPATH_PROVISIONER_DIR in up.sh.
    docker exec minikube sh -c 'rm -rf /var/hostpath-provisioner/*' || true
}

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
