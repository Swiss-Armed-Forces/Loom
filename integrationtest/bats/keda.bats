#!/usr/bin/env bats

# shellcheck disable=SC2154  # BATS_TEST_FILENAME is set by the BATS runtime
load helpers

REPO_DIR="$(cd -- "$(dirname -- "${BATS_TEST_FILENAME}")/../.." && pwd)"
MANIFEST="$(dirname -- "${BATS_TEST_FILENAME}")/keda-test.yaml"

@test "KEDA deploys and runs successfully" {
    run bash -c "cd '${REPO_DIR}' && ./up.sh --scaling --skip-run_skaffold"
    [[ "${status}" -eq 0 ]]

    kubectl apply -f "${MANIFEST}"

    # KEDA sets minReplicaCount: 1, so the operator must scale the deployment
    # from 0 to 1 without any external trigger — proves KEDA is functional.
    kubectl wait deployment keda-test \
        -n loom \
        --for=condition=Available \
        --timeout=120s
}
