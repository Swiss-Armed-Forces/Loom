#!/usr/bin/env bash
set -euo pipefail

#
# Kubernetes Resource Request Checker
#
# Uses check_resources.py to verify CPU and memory requests
# against defined thresholds.
#
# Note: if you change the thresholds, you probably also
# want to update the README.md
# Note: minikube declares a base load of:
# - ~ 1200m CPU
# - ~ 440Mi RAM
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#
# Arguments
#
CHARTS_DIR="${1?Missing Charts Dir}"

# Max allowed requests (resource requests)
MAX_CPU="8"
MAX_MEMORY="25Gi"
MAX_GPU="3"

# Max allowed limits (resource limits)
MAX_CPU_LIMITS="65"
MAX_MEMORY_LIMITS="85Gi"
MAX_GPU_LIMITS="3"

# Run the resource checker
# --exclude-ephemeral: excludes Job and CronJob from calculations
echo "Default resources check"
helm template "${CHARTS_DIR}" \
| poetry run python "${SCRIPT_DIR}/check_resources.py" \
    --exclude-ephemeral \
    --threshold-request "cpu=${MAX_CPU}" \
    --threshold-request "memory=${MAX_MEMORY}" \
    --threshold-limit "cpu=${MAX_CPU_LIMITS}" \
    --threshold-limit "memory=${MAX_MEMORY_LIMITS}"

echo "GPU resources check"

helm template "${CHARTS_DIR}" --values "${CHARTS_DIR}/values-gpu.yaml" \
| poetry run python "${SCRIPT_DIR}/check_resources.py" \
    --exclude-ephemeral \
    --threshold-request "cpu=${MAX_CPU}" \
    --threshold-request "memory=${MAX_MEMORY}" \
    --threshold-request "nvidia.com/gpu=${MAX_GPU}" \
    --threshold-limit "cpu=${MAX_CPU_LIMITS}" \
    --threshold-limit "memory=${MAX_MEMORY_LIMITS}" \
    --threshold-limit "nvidia.com/gpu=${MAX_GPU_LIMITS}"

# Check if README.md contains the expected resource requirements block
# This ensures the README stays in sync with the actual threshold values

README_FILE="${SCRIPT_DIR}/../README.md"

if [[ ! -f "${README_FILE}" ]]; then
    echo "ERROR: README.md not found at ${README_FILE}"
    exit 1
fi

MISSING_LINES=0

# Define patterns to check - each line individually
PATTERNS=(
    "**RAM:** ${MAX_MEMORY}"
    "**CPU:** ${MAX_CPU} Cores"
    "**GPU (Optional):** For enhanced performance with certain features, we recommend using at least ${MAX_GPU} GPUs."
    "**RAM:** ${MAX_MEMORY_LIMITS}"
    "**CPU:** ${MAX_CPU_LIMITS} Cores"
    "**GPU (Optional):** ${MAX_GPU}"
)

for pattern in "${PATTERNS[@]}"; do
    if ! grep -qF "${pattern}" "${README_FILE}"; then
        echo "ERROR: README.md is missing expected line: ${pattern}"
        MISSING_LINES=$((MISSING_LINES + 1))
    fi
done

if [[ ${MISSING_LINES} -gt 0 ]]; then
    echo "ERROR: README.md is missing ${MISSING_LINES} expected line(s)"
    echo "Please ensure the README.md contains the resource requirements with these values:"
    echo "  - MAX_MEMORY: ${MAX_MEMORY}"
    echo "  - MAX_CPU: ${MAX_CPU}"
    echo "  - MAX_GPU: ${MAX_GPU}"
    echo "  - MAX_MEMORY_LIMITS: ${MAX_MEMORY_LIMITS}"
    echo "  - MAX_CPU_LIMITS: ${MAX_CPU_LIMITS}"
    exit 1
fi

echo "README.md resource requirements verification passed"
