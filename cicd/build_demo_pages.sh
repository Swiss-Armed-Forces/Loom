#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
TOPLEVEL_DIR="${SCRIPT_DIR}/.."
FRONTEND_DIR="${TOPLEVEL_DIR}/Frontend"
DEMO_OUTPUT_DIR="${FRONTEND_DIR}/dist-demo"

pnpm \
    --dir "${FRONTEND_DIR}" \
    run build:demo \
    "${@}"

for artifact in index.html 404.html mockServiceWorker.js; do
    test -s "${DEMO_OUTPUT_DIR}/${artifact}"
done
