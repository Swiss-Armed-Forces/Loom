#!/usr/bin/env bash
#
# This script downloads a specific version of the Traefik Helm chart.
#
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

# variables defined in vars.sh, here for shellcheck:
TRAEFIK_HELM_VERSION=""

VARS_FILE="${SCRIPT_DIR}/../vars.sh"
# shellcheck disable=SC1091
# shellcheck source=../vars.sh
source "${VARS_FILE}"

HELM_TRAEFIK_REPO="https://traefik.github.io/charts"

helm repo add traefik "${HELM_TRAEFIK_REPO}"
helm repo update

helm \
    pull \
        --version "${TRAEFIK_HELM_VERSION}" \
        traefik/traefik