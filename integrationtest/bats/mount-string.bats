#!/usr/bin/env bats

# shellcheck disable=SC2154  # BATS_TEST_FILENAME is set by the BATS runtime
load helpers

REPO_DIR="$(cd -- "$(dirname -- "${BATS_TEST_FILENAME}")/../.." && pwd)"
MANIFEST="$(dirname -- "${BATS_TEST_FILENAME}")/mount-test.yaml"
# MOUNT_DIR is exported by setup_suite (setup_suite.bash) as a fresh temp dir.
# The fallback below only applies when running this file outside the suite.
MOUNT_DIR="${MOUNT_DIR:-${REPO_DIR}/data}"

@test "PVC data survives a full cluster rebuild" {
    # First cluster bring-up and write
    run bash -c "cd '${REPO_DIR}' && ./up.sh --setup --mount-string '${MOUNT_DIR}'"
    [[ "${status}" -eq 0 ]]

    kubectl delete job -n mount-test mount-test-writer --ignore-not-found
    kubectl apply -f "${MANIFEST}"
    kubectl wait --for=condition=complete job/mount-test-writer -n mount-test --timeout=60s

    run kubectl logs -n mount-test job/mount-test-writer
    [[ "${status}" -eq 0 ]]
    count_1="$(echo "${output}" | grep -c "^run at:" || true)"
    [[ "${count_1}" -eq 1 ]]

    # Full cluster rebuild — purge and re-seed from cached template so the
    # second up.sh call doesn't pull images from the internet.
    reinitialize_minikube_home
    run bash -c "cd '${REPO_DIR}' && ./up.sh --setup --mount-string '${MOUNT_DIR}'"
    [[ "${status}" -eq 0 ]]

    kubectl delete job -n mount-test mount-test-writer --ignore-not-found
    kubectl apply -f "${MANIFEST}"
    kubectl wait --for=condition=complete job/mount-test-writer -n mount-test --timeout=60s

    # Second write must see the first write's data
    run kubectl logs -n mount-test job/mount-test-writer
    [[ "${status}" -eq 0 ]]
    count="$(echo "${output}" | grep -c "^run at:" || true)"
    [[ "${count}" -ge 2 ]]
}
