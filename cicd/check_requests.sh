#!/usr/bin/env bash
set -euo pipefail

#
# Consts
#
RESOURCE_SUMMARY="templates/common/resource-summary.yaml"

#
# Arguments
#
CHARTS_DIR="${1?Missing Charts Dir}"

# Max allowed requests
#
# Note: if you change those, you probably also
# want to update the README.md
# Note: minikube declares a base load of:
# - ~ 1200m CPU
# - ~ 440Mi RAM
MAX_CPU="6500"       # in millicores
MAX_MEMORY="21000"   # in Mi

# Render the Helm chart and extract the ConfigMap YAML
RENDERED=$(helm template "${CHARTS_DIR}" --show-only "${RESOURCE_SUMMARY}" )

# Extract values from the resource-summary ConfigMap
CPU_REQUESTS=$(echo "${RENDERED}" | yq --raw-output  '.data.totalCpuRequests')
MEMORY_REQUESTS=$(echo "${RENDERED}" | yq --raw-output '.data.totalMemoryRequests')

# Strip "m" and "Mi" suffixes
CPU_VALUE="${CPU_REQUESTS%m}"
MEM_VALUE="${MEMORY_REQUESTS%Mi}"

# Assert against thresholds
if (( CPU_VALUE > MAX_CPU )); then
  echo "❌ CPU request (${CPU_VALUE} m) exceeds limit (${MAX_CPU} m)"
  exit 1
fi

if (( MEM_VALUE > MAX_MEMORY )); then
  echo "❌ Memory request (${MEM_VALUE} Mi) exceeds limit (${MAX_MEMORY} Mi)"
  exit 1
fi

echo "✅ CPU (${CPU_VALUE} m) and memory (${MEM_VALUE} Mi) requests are within limits."
