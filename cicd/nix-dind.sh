#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CONTEXT_DIR=$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)
DOCKERFILE="${CONTEXT_DIR}/nix-dind/Dockerfile"

# CI variables
CI_REGISTRY_IMAGE="registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom"
CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX="gitlab.com:443/swiss-armed-forces/cyber-command/cea/dependency_proxy/containers"

# Image name
IMAGE_NAME="nix-dind"
IMAGE_FULL_NAME="${CI_REGISTRY_IMAGE}/${IMAGE_NAME}"
IMAGE_TAG="latest"
CONTAINER_NAME="nix-dind-${RANDOM}${RANDOM}${RANDOM}"

USER_ID="$(id -u)"
GROUP_ID="$(id -g)"
SKIP=()
USER_DOCKER_CONF="${HOME}/.docker/config.json"

# Steps to setup the cluster before startup
STEPS=(
    build
)

VERBOSE=false
DO_PULL=false
DO_PUSH=false
DO_RUN=false
DOCKER_VOLUME=""
CODE_OVERLAY_VOLUME=""

is_tty_attached() {
    tty -s
}

get_absolute_path(){
    local path
    path="${1}" && shift

    readlink -m "${path}"
}


pull(){
    docker pull \
        "${IMAGE_FULL_NAME}:${IMAGE_TAG}"
}

build(){
    # ulimit because of:
    # https://github.com/NixOS/nix/issues/11258#issuecomment-2323063903
    docker build \
        --ulimit nofile=1024:1024 \
        --file "${DOCKERFILE}" \
        --tag "${IMAGE_FULL_NAME}:${IMAGE_TAG}" \
        --build-arg CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX="${CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX}" \
        --build-arg NIX_GROUP_ID="${GROUP_ID}" \
        --build-arg NIX_USER_ID="${USER_ID}" \
        --cache-to type=inline \
        --cache-from type=registry,ref="${IMAGE_FULL_NAME}:${IMAGE_TAG}" \
        "${CONTEXT_DIR}"
}

push(){
    docker push \
        "${IMAGE_FULL_NAME}:${IMAGE_TAG}"
}

run(){
    local docker_run_options
    docker_run_options=()

    if [[ -n "${DOCKER_VOLUME}" ]]; then
        local abs_docker_volume
        abs_docker_volume="$(get_absolute_path "${DOCKER_VOLUME}")"
        docker_run_options+=( \
            "--volume" \
            "${abs_docker_volume}:/var/lib/docker:rw" \
        )
    fi

    if [[ -n "${CODE_OVERLAY_VOLUME}" ]]; then
        local abs_code_overlay_volume
        abs_code_overlay_volume="$(get_absolute_path "${CODE_OVERLAY_VOLUME}")"
        docker_run_options+=( \
            "--volume" \
            "${abs_code_overlay_volume}:/code-overlay:rw" \
        )
    fi

    if [[ -f "${USER_DOCKER_CONF}" ]]; then
        local abs_user_docker_conf
        abs_user_docker_conf="$(get_absolute_path "${USER_DOCKER_CONF}")"

        docker_run_options+=( \
            "--volume" \
            "${abs_user_docker_conf}:/home/nix/.docker/config.json:ro" \
        )
    fi

    local abs_context_dir
    abs_context_dir="$(get_absolute_path "${CONTEXT_DIR}")"

    # shellcheck disable=SC2310
    if is_tty_attached; then
        docker_run_options+=( "--tty" )
    fi

    # ulimit because of:
    # https://github.com/NixOS/nix/issues/11258#issuecomment-2323063903
    docker run \
        --ulimit nofile=1024:1024 \
        --privileged \
        --interactive \
        --env TAILSCALE_AUTHKEY \
        --volume "${abs_context_dir}/:/code-ro:ro" \
        --name "${CONTAINER_NAME}" \
        "${docker_run_options[@]}" \
        "${IMAGE_FULL_NAME}:${IMAGE_TAG}" \
        "${@}"
}

#
# Usage
#

usage(){
    echo "usage: $0 [<options>]"
    echo "  -h|--help                                       show this help"
    echo "  -v|--verbose                                    show verbose output"
    echo "  -pu|--pull                                      pull the image"
    echo "  -p|--push                                       push the image"
    echo "  -r|--run                                        run the image"
    echo "  -n|--container-name CONTAINER_NAME              name of the container"
    echo "  -dv|--docker-volume DOCKER_VOLUME               docker volume path"
    echo "  -cov|--code-overlay-volume CODE_OVERLAY_VOLUME  code overlay volume path"
    echo "  -ctx|--context-dir CONTEXT_DIR                  use CONTEXT_DIR instead of the git toplevel"
    echo "  --skip-STEP                                     skip step STEP"
}

#
# Atexit handler
#

atexit(){
    echo "[*] Exiting.."
}
trap atexit EXIT


#
# Argument parsing
#

ARGS=()
while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            usage
            trap - EXIT
            exit 0
        ;;
        -v|--verbose)
            VERBOSE=true
            shift
        ;;
        -pu|--pull)
            DO_PULL=true
            shift
        ;;
        -p|--push)
            DO_PUSH=true
            shift
        ;;
        -r|--run)
            DO_RUN=true
            shift
        ;;
        -n|--container-name)
            shift
            CONTAINER_NAME="${1}"
            shift
        ;;
        -dv|--docker-volume)
            shift
            DOCKER_VOLUME="${1}"
            shift
        ;;
        -cov|--code-overlay-volume)
            shift
            CODE_OVERLAY_VOLUME="${1}"
            shift
        ;;
        -ctx|--context-dir)
            shift
            CONTEXT_DIR="${1}"
            shift
        ;;
        --skip-*)
            SKIP+=("${1}")
            shift
        ;;
        *)
            ARGS+=("${1}")
            shift
        ;;
    esac
done

#
# Main
#

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

if [[ "${DO_PULL}" = true ]]; then
    STEPS=( pull  "${STEPS[@]}" )
fi

if [[ "${DO_PUSH}" = true ]]; then
    STEPS+=( push )
fi

if [[ "${DO_RUN}" = true ]]; then
    STEPS+=( run )
fi

# execute steps
for step in "${STEPS[@]}"; do
    if [[ "${SKIP[*]}" == *"--skip-${step}"* ]]; then
        echo "[*] Skipping: ${step}"
        continue
    fi
    echo "[*] Running: ${step}"
    "${step}" "${ARGS[@]}"
done