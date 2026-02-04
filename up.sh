#!/usr/bin/env bash
#
# This script orchestrates the setup, management, and deployment of a Kubernetes cluster using Minikube and Skaffold.
# It includes environment validation, system configuration, cluster creation, namespace management, and Helm chart installation.
# Supports customizable workflows via arguments for exposing, and tailoring cluster operations.
#
set -eou pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
SCRIPT_NAME=$(basename "$0")

#
# Environment
#
EDITOR="${EDITOR:-nano}"
REGISTRY_MIRROR="${REGISTRY_MIRROR:-}"
SKAFFOLD_HOME="${SKAFFOLD_HOME:-${HOME}/.skaffold}"

#
# Defines
#
NAMESPACE="loom"
DOCKER_SECRET_NAME="docker-registry-secret"
DOCKER_CONFIG_FILE="${HOME}/.docker/config.json"
HOSTS_FILE="/etc/hosts"
TUNNEL_PIDFILE_DIR="/run/user/${UID}/"
TUNNEL_PIDFILE="${TUNNEL_PIDFILE_DIR}/${SCRIPT_NAME}.minikube.tunnel.pid"
TRAEFIK_SKAFFOLD_CMD="${SCRIPT_DIR}/traefik/skaffold"
ONLINE_TEST_URL="https://gitlab.com"
OFFLINE_IMAGE_TAG="latest"
CERTIFICATE_SECRET_NAME="self-signed-cert"

WAIT_MAX_RETRIES=30

#
# Shared variables
#

# variables defined in vars.sh, here for shellcheck:
LOOM_DOMAIN=""
LOOM_HOSTS_FQDN=()
TRAEFIK_HELM_VERSION=""

VARS_FILE="${SCRIPT_DIR}/vars.sh"
# shellcheck disable=SC1091
# shellcheck source=./vars.sh
source "${VARS_FILE}"

#
# Steps
#

# Steps which always run
# some of these steps require root
STEPS_SETUP_SYSTEM=(
    set_offline_mode
    set_skaffold_profile
    set_skaffold_command
    set_skaffold_args
    validate_environment
    setup_system
    create_cluster
    install_host_entries
)

# Steps to setup the cluster before startup
STEPS_SETUP_CLUSTER=(
    create_namespace
    use_namespace
    create_docker_secret_from_config
    install_traefik
    install_certificate
    stop_expose_minikube
    warn_dev_or_integration
)

#
# Runtime vars
#

SKIP=()
VERBOSE=false
DEVELOPMENT=false
INTEGRATIONTEST=false
SETUP=false
TAIL=false
EXPOSE=false
EXPOSE_IP=""
GPUS=""
OFFLINE_MODE=false
DELETE=false
SKAFFOLD_PROFILE="prod"
SKAFFOLD_ARGS=()
TRAEFIK_SKAFFOLD_ARGS=()
SKAFFOLD_COMMAND="run"
SKAFFOLD_CACHE_FILE="${SKAFFOLD_HOME}/cache"
SKAFFOLD_REMOTE_CACHE_DIR="${SKAFFOLD_HOME}/remote-cache"
CERTIFICATE=false

#
# Utils
#

check_command() {
    local cmd
    cmd="${1}" && shift

    if ! command -v "${cmd}" &>/dev/null; then
        echo >&2 "[!] ${cmd} is not installed."
        echo >&2 "[!] Please install ${cmd} and try again."
        exit 1
    fi
}

wait_for(){
    local check_function
    check_function="${1}" && shift

    # Initialize retry counter
    local retry_count
    retry_count=0

    # Loop until check_function is ready or max retries is reached
    while ! "${check_function}"; do
        if [[ "${retry_count}" -ge "${WAIT_MAX_RETRIES}" ]]; then
            echo "${check_function} was not ready after ${WAIT_MAX_RETRIES} seconds."
            exit 1
        fi

        echo "Waiting for ${check_function}... Attempt $((retry_count+1))/${WAIT_MAX_RETRIES}"
        sleep 1
        retry_count=$((retry_count + 1))
    done

    echo "${check_function} is ready!"
}

namespace_exists() {
    kubectl \
        get namespace \
        "${NAMESPACE}" &> /dev/null
}

is_hosts_file_writable_as_root(){
    sudo [ -w "${HOSTS_FILE}" ]
}

is_serviceaccount_ready() {
    kubectl get \
        serviceaccount \
        default \
        --namespace "${NAMESPACE}" \
    &>/dev/null
}

is_offline() {
    ! curl \
        --silent \
        --fail \
        --max-time 5 \
        --head "${ONLINE_TEST_URL}" \
    &>/dev/null
}

#
# Steps
#

set_offline_mode(){
    # shellcheck disable=SC2310
    if is_offline; then
        OFFLINE_MODE=true
    fi
    if [[ "${OFFLINE_MODE}" = true ]] && [[ "${DEVELOPMENT}" = true ]] ; then
        echo "[!] Error: Can not start development mode when offline"
        exit 1
    fi
    if [[ "${OFFLINE_MODE}" = true ]]; then
        local tag
        if ! tag="$(git describe --exact-match --tags HEAD 2>/dev/null)"; then
            echo >&2 "[!] Offline mode requires checking out a specific Git tag."
            echo >&2 "    You are currently not on a tagged commit (likely on the main branch)."
            echo >&2 ""
            echo >&2 "    To check out a tag, run:"
            echo >&2 "      git fetch --tags"
            echo >&2 "      git tag -l                    # List available tags"
            echo >&2 "      git checkout <tag-name>  # Check out a specific tag"
            echo >&2 ""
            echo >&2 "    Example:"
            echo >&2 "      git checkout tags/1.0.0"
            exit 1
        fi
        echo "[*] Running in offline mode, on tag: ${tag}"
    fi
}

set_skaffold_profile(){
    if [[ "${DEVELOPMENT}" = true ]] || [[ "${INTEGRATIONTEST}" = true ]]; then
        SKAFFOLD_PROFILE="dev"
    fi
    if [[ "${OFFLINE_MODE}" = true ]]; then
        SKAFFOLD_PROFILE="offline"
    fi
}

set_skaffold_command(){
    if [[ "${DEVELOPMENT}" = true ]]; then
        SKAFFOLD_COMMAND="debug"
    fi
}


set_skaffold_args(){
    if [[ "${DEVELOPMENT}" = true ]]; then
        SKAFFOLD_ARGS+=(
            "--auto-build"
            "--auto-deploy"
            "--auto-sync"
        )
    fi
    if [[ "${OFFLINE_MODE}" = true ]]; then
        local offline_skaffold_args
        offline_skaffold_args=(
            # fix tags: dynamic tag computation requires
            # checking of base images in the registry
            # Note: skaffold won't deploy this tag,
            # but instead it will use the appVersion
            # from Charts.yaml
            "--tag=${OFFLINE_IMAGE_TAG}"
            # we can not download caches from the registry
            "--cache-artifacts=false"
            # we can not build any images
            "--build-image=[]"
        )
        SKAFFOLD_ARGS+=(
            "${offline_skaffold_args[@]}"
        )
        TRAEFIK_SKAFFOLD_ARGS+=( "${offline_skaffold_args[@]}" )
    fi
    local skaffold_cache_args
    skaffold_cache_args=(
        "--cache-file=${SKAFFOLD_CACHE_FILE}"
        "--remote-cache-dir=${SKAFFOLD_REMOTE_CACHE_DIR}"
    )
    # default args:
    SKAFFOLD_ARGS+=(
        "--tail=${TAIL}"
        "${skaffold_cache_args[@]}"
    )
    TRAEFIK_SKAFFOLD_ARGS+=(
        "${skaffold_cache_args[@]}"
    )
}

delete_cluster(){
    minikube delete
}

validate_environment() {
    # Check if not run as root
    if [[ "${EUID}" -eq 0 ]]; then
        echo >&2 "[!] Error: Script must not be run as root!"
        exit 1
    fi

    # Check submodules
    submodules=$(git submodule | awk '{ print $2 }')
    for submodule in ${submodules}; do
        if [[ ! -f "${submodule}/.git" ]]; then
            echo >&2 "[!] Error: Git submodule '${submodule}' missing!"
            echo >&2 "[!] You need to clone the git repository with '--recursive' in order to clone submodules."
            echo >&2 "[!] You can fix that by running 'git submodule update --init --recursive'"
            exit 1
        fi
    done

    # Check git lfs
    if [[ ! -d ".git/lfs/objects" ]]; then
        echo >&2 "[!] Error: Git lfs objects missing!"
        echo >&2 "[!] Install git-lfs and run: 'git lfs pull'"
        exit 1
    fi

    # utils
    check_command cp
    check_command mkdir
    check_command diff
    check_command grep
    check_command sudo
    check_command sysctl
    check_command pidwait
    check_command pkill
    check_command tee
    check_command realpath
    check_command sh
    check_command curl

    # k8s
    check_command docker
    check_command kubectl
    check_command helm
    check_command minikube
    check_command skaffold
}

create_docker_secret_from_config() {
    # shellcheck disable=SC2310
    if ! is_serviceaccount_ready; then
        wait_for is_serviceaccount_ready
    fi

    if [[ ! -f "${DOCKER_CONFIG_FILE}" ]]; then
        echo "[*] Docker config file: '${DOCKER_CONFIG_FILE}' does not exist"
        return
    fi

    if kubectl get secret "${DOCKER_SECRET_NAME}" &>/dev/null; then
      echo "[*] Secret '${DOCKER_SECRET_NAME}' already exists"
      return
    fi

    echo "[*] Creating Docker registry secret from ${DOCKER_CONFIG_FILE}"
    kubectl \
        create secret generic "${DOCKER_SECRET_NAME}" \
            --namespace="${NAMESPACE}" \
            --from-file=.dockerconfigjson="${DOCKER_CONFIG_FILE}" \
            --type=kubernetes.io/dockerconfigjson

    echo "[*] Patching 'default' service account to use docker image pull secret as default"
    kubectl patch serviceaccount default \
        --namespace="${NAMESPACE}" \
        --patch="{\"imagePullSecrets\": [{\"name\": \"${DOCKER_SECRET_NAME}\"}]}"
}

setup_system(){
    local sysctl_changed
    sysctl_changed=false

    VM_MAX_MAP_COUNT=1677720
    vm_max_map_count="$(sysctl -n vm.max_map_count)"
    if [[ "${vm_max_map_count}" -lt "${VM_MAX_MAP_COUNT}" ]]; then
        sudo sysctl -w "vm.max_map_count=${VM_MAX_MAP_COUNT}"
        sysctl_changed=true
    fi
    VM_OVERCOMMIT_MEMORY=1
    vm_overcommit_memory="$(sysctl -n vm.overcommit_memory)"
    if [[ "${vm_overcommit_memory}" != "${VM_OVERCOMMIT_MEMORY}" ]]; then
        sudo sysctl -w "vm.overcommit_memory=${VM_OVERCOMMIT_MEMORY}"
        sysctl_changed=true
    fi
    FS_INOTIFY_MAX_WATCHES=655360
    fs_inotify_max_watches="$(sysctl -n fs.inotify.max_user_watches)"
    if [[ "${fs_inotify_max_watches}" != "${FS_INOTIFY_MAX_WATCHES}" ]]; then
        sudo sysctl -w "fs.inotify.max_user_watches=${FS_INOTIFY_MAX_WATCHES}"
        sysctl_changed=true
    fi
    FS_INOTIFY_MAX_INSTANCES=1280
    fs_inotify_max_instances="$(sysctl -n fs.inotify.max_user_instances)"
    if [[ "${fs_inotify_max_instances}" != "${FS_INOTIFY_MAX_INSTANCES}" ]]; then
        sudo sysctl -w "fs.inotify.max_user_instances=${FS_INOTIFY_MAX_INSTANCES}"
        sysctl_changed=true
    fi
    SYSCTL_CONF_FILE="/etc/sysctl.d/99-loom.conf"
    if [[ ! -f "${SYSCTL_CONF_FILE}" ]] || [[ "${sysctl_changed}" = true ]]; then
        sudo tee "${SYSCTL_CONF_FILE}" <<EOF
vm.max_map_count=${VM_MAX_MAP_COUNT}
vm.overcommit_memory=${VM_OVERCOMMIT_MEMORY}
fs.inotify.max_user_watches=${FS_INOTIFY_MAX_WATCHES}
fs.inotify.max_user_instances=${FS_INOTIFY_MAX_INSTANCES}
EOF
    fi
}

create_cluster(){
    minikube start \
        --driver docker \
        --wait all \
        --registry-mirror "${REGISTRY_MIRROR}" \
        --memory max \
        --cpus max \
        --cni calico \
        --addons metrics-server \
        --gpus "${GPUS}"
}

create_namespace(){
    # shellcheck disable=SC2310
    if namespace_exists; then
        echo "[-] Namespace ${NAMESPACE} already exists"
        return
    fi

    kubectl create namespace "${NAMESPACE}"
}

use_namespace(){
    kubectl config set-context \
        --current \
        --namespace="${NAMESPACE}"
}

install_traefik(){
    (
        cd "${SCRIPT_DIR}/traefik"


        # Deploy CRDs as skaffold won't do this
        # Related:
        # https://github.com/GoogleContainerTools/skaffold/issues/8227
        echo "[*] Deploying traefik CRDS"
        helm show crds \
            "traefik-${TRAEFIK_HELM_VERSION}.tgz" \
        | kubectl \
            apply \
                --filename -

        # Wait for all CRDs to be established
        kubectl wait \
            --for condition=established \
                crd \
                    --all

        # Install default tls-store
        echo "[*] Installing traefik tls-store"
        kubectl \
            apply \
                --filename tls-store.yaml

        # We always first delete the existing deployment
        # this is because skaffold will redeploy
        # resources, which won't work as traefik
        # holds exclusive access on certain ports
        # Related:
        #   - https://github.com/GoogleContainerTools/skaffold/issues/9222
        "${TRAEFIK_SKAFFOLD_CMD}" delete \
            --profile "${SKAFFOLD_PROFILE}"

        "${TRAEFIK_SKAFFOLD_CMD}" run \
            --profile "${SKAFFOLD_PROFILE}" \
            "${TRAEFIK_SKAFFOLD_ARGS[@]}" \
            "${@}"
    )
}

install_certificate(){
    if [[ "${CERTIFICATE}" = false ]]; then
        return
    fi
    kubectl \
        delete \
            secret \
                "${CERTIFICATE_SECRET_NAME}" \
                --ignore-not-found true
    kubectl \
        create \
            secret tls \
                "${CERTIFICATE_SECRET_NAME}" \
                --cert "${CERTIFICATE[0]}" \
                --key "${CERTIFICATE[1]}"
}

stop_expose_minikube(){
    if [[ -f "${TUNNEL_PIDFILE}" ]]; then
        sudo pkill \
            --signal SIGINT \
            --pidfile "${TUNNEL_PIDFILE}" \
        || true

        pidwait \
            --pidfile "${TUNNEL_PIDFILE}" \
        || true

        rm \
            --force \
            "${TUNNEL_PIDFILE}"
    fi
}

warn_dev_or_integration() {
    if [[ "${DEVELOPMENT}" = true ]] || [[ "${INTEGRATIONTEST}" = true ]]; then
        echo "[*] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "[*] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "[*] *****************************************"
        echo "[*] WARNING: DO NOT USE THIS IN PRODUCTION!!!"
        echo "[*] *****************************************"
        echo "[*] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "[*] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    fi
}

expose_minikube(){
    # Store the path to the command so that we can use
    # this later in sudo.
    # This is because minikube might be installed in /nix
    # and the system sudo configuration might purge
    # the PATH variable.
    local minikube_cmd
    minikube_cmd="$(command -v minikube)"

    # root required for binding 80 and 443
    #
    # Also we need have to preserve-env so that
    # minikube finds the configuration files.
    echo "[*] Exposing application on ${EXPOSE_IP}"
    sudo \
        --background \
        --preserve-env \
        sh -c "
            mkdir --parents '${TUNNEL_PIDFILE_DIR}'
            echo \$\$ > '${TUNNEL_PIDFILE}'
            exec '${minikube_cmd}' tunnel \
                --bind-address='${EXPOSE_IP}' \
                --cleanup=true
        "
}

install_host_entries(){
    local minikube_ip
    minikube_ip="$(minikube ip)"

    local hosts_file
    hosts_file="$(cat "${HOSTS_FILE}" 2>/dev/null || true)"
    hosts_file+=$'\n'   # always append a trailing newline
                        # which maybe was stripped by bash's
                        # command substitution

    # assemble new hosts file
    local new_hosts_file
    new_hosts_file=""
    new_hosts_file+="$(grep -v "${LOOM_DOMAIN}" <<< "${hosts_file}")";
    new_hosts_file+=$'\n'
    new_hosts_file+="# Hosts for '${LOOM_DOMAIN}' domain"
    new_hosts_file+=$'\n'
    for host in "${LOOM_HOSTS_FQDN[@]}"; do
        new_hosts_file+=$"${minikube_ip} ${host}"
        new_hosts_file+=$'\n'
    done

    if [[ "${new_hosts_file}" == "${hosts_file}" ]]; then
        echo "[-] '${HOSTS_FILE}' does not need to be modified"
        return
    fi

    # Not writable & symlink: this happens on distributions
    # with immutable system state (like NixOS). Hence we apply
    # a bit of a hack here by simply overwriting the file.
    # This most likely won't be persisted, but its probably
    # good enough for now..
    # shellcheck disable=SC2310
    if ! is_hosts_file_writable_as_root && [[ -L "${HOSTS_FILE}" ]]; then
        echo "[*] Replacing the non-writable '${HOSTS_FILE}' with a copy of its symlink destination to make it writable."
        local real_hosts_file
        real_hosts_file="$(realpath "${HOSTS_FILE}")"
        sudo cp \
            --remove-destination \
            "${real_hosts_file}" \
            "${HOSTS_FILE}"
    fi

    # test again
    # shellcheck disable=SC2310
    if ! is_hosts_file_writable_as_root; then
        echo >&2 "[!] '${HOSTS_FILE}' not writable:"
        echo >&2 "[!] you have to manually add the '${LOOM_DOMAIN}' domain hosts to your DNS"
        return
    fi

    echo "[*] Writing new '${HOSTS_FILE}'"
    diff \
        <(echo -n "${new_hosts_file}") \
        <(echo -n "${hosts_file}") \
    || true

    # write new hosts file
    echo -n "${new_hosts_file}" \
        | sudo tee "${HOSTS_FILE}" >/dev/null
}

run_skaffold(){
    skaffold "${SKAFFOLD_COMMAND}" \
        --profile "${SKAFFOLD_PROFILE}" \
        "${SKAFFOLD_ARGS[@]}" \
        "${@}"
}

#
# Atexit Handler
#

atexit(){
    echo "[*] Exiting.."

    if [[ "${SETUP}" = true ]]; then
        return
    fi

    if [[ "${DELETE}" = true ]]; then
        (
            cd "${SCRIPT_DIR}/traefik"

            "${TRAEFIK_SKAFFOLD_CMD}" delete \
                --profile "${SKAFFOLD_PROFILE}"
        )

        skaffold delete \
            --profile "${SKAFFOLD_PROFILE}"
    fi
}
trap atexit EXIT

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>]"
    echo "  -h|--help                   show this help"
    echo "  -v|--verbose                show verbose output"
    echo "  -d|--development            start in development mode: Provides debugging und live reloading."
    echo "  -i|--integrationtest        start in integration test mode"
    echo "  -s|--setup                  only setup system, don't start anything"
    echo "  -e|--expose IP              expose the application to the outside world by binding to IP"
    echo "  -g|--gpus GPUS              allow access to the GPUs. Possible values: all, nvidia, amd"
    echo "  -t|--tail                   tail logs after startup"
    echo "  -o|--offline                run in offline mode"
    echo "  -c|--certificate CERT KEY   install certificate (CERT) with key (KEY)"
    echo "  --delete                    delete the deployment after startup"
    echo "  --skip-STEP                 skip step STEP"
}

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
        -d|--development)
            DEVELOPMENT=true
            shift
        ;;
        -i|--integrationtest)
            INTEGRATIONTEST=true
            shift
        ;;
        -v|--verbose)
            VERBOSE=true
            shift
        ;;
        -s|--setup)
            SETUP=true
            shift
        ;;
        -t|--tail)
            TAIL=true
            shift
        ;;
        -e|--expose)
            EXPOSE=true
            shift
            EXPOSE_IP="${1}"
            shift
        ;;
        -g|--gpus)
            shift
            GPUS="${1}"
            shift
        ;;
        -o|--offline)
            shift
            OFFLINE_MODE=true
        ;;
        -c|--certificate)
            shift
            CERTIFICATE=("${1?Missing CERT}" "${2?Missing KEY}")
            shift
            shift
        ;;
        --delete)
            DELETE=true
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

# assemble STEPS
STEPS=()
STEPS+=(
    "${STEPS_SETUP_SYSTEM[@]}"
    "${STEPS_SETUP_CLUSTER[@]}"
)

if [[ "${EXPOSE}" = true ]]; then
    STEPS+=(expose_minikube)
fi

STEPS+=(run_skaffold)

if [[ "${SETUP}" = true ]]; then
    STEPS=("${STEPS_SETUP_SYSTEM[@]}")
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
