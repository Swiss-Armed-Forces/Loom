#!/usr/bin/env bash
#
# This script downloads a specific version of the KEDA Helm chart.
#
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

# variables defined in vars.sh, here for shellcheck:
KEDA_HELM_VERSION=""

VARS_FILE="${SCRIPT_DIR}/../vars.sh"
# shellcheck disable=SC1091
# shellcheck source=../vars.sh
source "${VARS_FILE}"

KEDA_REPO="https://kedacore.github.io/charts"

helm repo add kedacore "${KEDA_REPO}"
helm repo update

helm \
    pull \
        --version "${KEDA_HELM_VERSION}" \
        --destination "${SCRIPT_DIR}" \
        kedacore/keda
