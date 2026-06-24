#!/usr/bin/env bash
set -euo pipefail

#
# Kubernetes Resource Request Checker
#
# Uses check_resources.py to verify CPU and memory requests
# against defined thresholds.
#
# Note: if you change the thresholds, you probably also
# want to update Documentation/installation.md
# Note: minikube declares a base load of:
# - ~ 1200m CPU
# - ~ 440Mi RAM
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# variables defined in vars.sh, here for shellcheck:
LOOM_MIN_CPU=""
LOOM_MIN_MEMORY=""
LOOM_MIN_GPU=""
# shellcheck disable=SC1091
# shellcheck source=../vars.sh
source "${SCRIPT_DIR}/../vars.sh"

#
# Arguments
#
CHARTS_DIR="${1?Missing Charts Dir}"

# Maximum combined resource limits across all containers
LOOM_MAX_CPU="66"
LOOM_MAX_MEMORY="90Gi"
LOOM_MAX_GPU="3"

# Run the resource checker
# --exclude-ephemeral: excludes Job and CronJob from calculations
echo "Default resources check"
helm template "${CHARTS_DIR}" \
| poetry run python "${SCRIPT_DIR}/check_resources.py" \
    --exclude-ephemeral \
    --threshold-request "cpu=${LOOM_MIN_CPU}" \
    --threshold-request "memory=${LOOM_MIN_MEMORY}" \
    --threshold-limit "cpu=${LOOM_MAX_CPU}" \
    --threshold-limit "memory=${LOOM_MAX_MEMORY}"

echo "GPU resources check"

helm template "${CHARTS_DIR}" --values "${CHARTS_DIR}/values-gpu.yaml" \
| poetry run python "${SCRIPT_DIR}/check_resources.py" \
    --exclude-ephemeral \
    --threshold-request "cpu=${LOOM_MIN_CPU}" \
    --threshold-request "memory=${LOOM_MIN_MEMORY}" \
    --threshold-request "nvidia.com/gpu=${LOOM_MIN_GPU}" \
    --threshold-limit "cpu=${LOOM_MAX_CPU}" \
    --threshold-limit "memory=${LOOM_MAX_MEMORY}" \
    --threshold-limit "nvidia.com/gpu=${LOOM_MAX_GPU}"

echo "No resources check"

helm template "${CHARTS_DIR}" --values "${CHARTS_DIR}/values-no-resources.yaml" \
| poetry run python "${SCRIPT_DIR}/check_resources.py" \
    --exclude-ephemeral \
    --threshold-request "cpu=${LOOM_MIN_CPU}" \
    --threshold-request "memory=${LOOM_MIN_MEMORY}" \
    --threshold-limit "cpu=${LOOM_MAX_CPU}" \
    --threshold-limit "memory=${LOOM_MAX_MEMORY}"

echo "Scalable quota consistency check"

helm template "${CHARTS_DIR}" \
| poetry run python "${SCRIPT_DIR}/check_resources.py" \
    --exclude-ephemeral \
    --filter-priority-class "*-scalable" \
    --quota-values "${CHARTS_DIR}/values.yaml"

# Check if Documentation/installation.md contains the expected resource requirements block
# This ensures the installation docs stay in sync with the actual threshold values

INSTALLATION_FILE="${SCRIPT_DIR}/../Documentation/installation.md"

if [[ ! -f "${INSTALLATION_FILE}" ]]; then
    echo "ERROR: Documentation/installation.md not found at ${INSTALLATION_FILE}"
    exit 1
fi

MISSING_LINES=0

# Define patterns to check - each line individually
PATTERNS=(
    "**RAM:** ${LOOM_MIN_MEMORY}"
    "**CPU:** ${LOOM_MIN_CPU} Cores"
    "**GPU (Optional):** For enhanced performance with certain features, we recommend using at least ${LOOM_MIN_GPU} GPUs."
    "**RAM:** ${LOOM_MAX_MEMORY}"
    "**CPU:** ${LOOM_MAX_CPU} Cores"
    "**GPU (Optional):** ${LOOM_MIN_GPU}"
)

for pattern in "${PATTERNS[@]}"; do
    if ! grep -qF "${pattern}" "${INSTALLATION_FILE}"; then
        echo "ERROR: Documentation/installation.md is missing expected line: ${pattern}"
        MISSING_LINES=$((MISSING_LINES + 1))
    fi
done

if [[ ${MISSING_LINES} -gt 0 ]]; then
    echo "ERROR: Documentation/installation.md is missing ${MISSING_LINES} expected line(s)"
    echo "Please ensure the Documentation/installation.md contains the resource requirements with these values:"
    echo "  - LOOM_MIN_MEMORY: ${LOOM_MIN_MEMORY}"
    echo "  - LOOM_MIN_CPU: ${LOOM_MIN_CPU}"
    echo "  - LOOM_MIN_GPU: ${LOOM_MIN_GPU}"
    echo "  - LOOM_MAX_MEMORY: ${LOOM_MAX_MEMORY}"
    echo "  - LOOM_MAX_CPU: ${LOOM_MAX_CPU}"
    exit 1
fi

echo "Documentation/installation.md resource requirements verification passed"
