#!/usr/bin/env bash
# Builds the whole application

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
STEPS=(
    set_targetarch
    build_traefik
    build_keda
    build_application
)

#
# Runtime vars
#
VERBOSE=false

#
# Steps
#

build_traefik(){
    "${SCRIPT_DIR}/skaffold" traefik build "${@}"
}

build_keda(){
    "${SCRIPT_DIR}/skaffold" keda build "${@}"
}

# The host architecture in Docker/Go naming, which is what skaffold.yaml's
# `arm64` profile activates on.
#
# Exported here as well as in up.sh's set_docker_platform(), and for the same
# reason: the profile drops artifact 23 (ollama-runtime-rocm, `platforms:
# ["linux/amd64"]`), and without it `build` on an arm64 workstation emulates a
# multi-GiB ROCm image through qemu that the host can never use -- the exact
# failure the comment above that profile describes for the Spark.
#
# Unsupported architectures are left alone rather than refused: this script
# builds, it does not decide what a cluster runs on, and up.sh is where that
# error belongs.
set_targetarch(){
    case "$(uname -m)" in
        aarch64|arm64) export TARGETARCH="arm64"  ;;
        x86_64|amd64)  export TARGETARCH="amd64"  ;;
        *)             : ;;
    esac
}

build_application(){
    (
        cd "${SCRIPT_DIR}/../"
        # SKAFFOLD_PLATFORM is read by skaffold directly, no flag needed here.
        skaffold build "${@}"
    )
}

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>]"
    echo "  -h|--help                         show this help"
    echo "  -v|--verbose                      show verbose output"
}

#
# Argument parsing
#

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
    -h | --help)
        usage
        exit 0
        ;;
    -v | --verbose)
        VERBOSE=true
        ;;
    *)
        ARGS+=("${1}")
        ;;
    esac
    shift
done

#
# Main
#

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

# execute steps
for step in "${STEPS[@]}"; do
    echo "[*] Running: ${step}"
    "${step}" "${ARGS[@]}"
done
