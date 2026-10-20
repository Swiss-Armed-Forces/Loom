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
DOCKER_SECRET_NAME="docker-registry-secret"
DOCKER_CONFIG_FILE="${HOME}/.docker/config.json"
HOSTS_FILE="/etc/hosts"
TUNNEL_PIDFILE_DIR="/run/user/${UID}/"
TUNNEL_PIDFILE="${TUNNEL_PIDFILE_DIR}/${SCRIPT_NAME}.minikube.tunnel.pid"
TRAEFIK_DIR="${SCRIPT_DIR}/traefik"
KEDA_DIR="${SCRIPT_DIR}/keda"
CICD_SKAFFOLD="${SCRIPT_DIR}/cicd/skaffold"
UP_FLAGS_VALUES_FILE="${SCRIPT_DIR}/charts/values-up-flags.yaml"
NO_RESOURCES_VALUES_FILE="${SCRIPT_DIR}/charts/values-no-resources.yaml"
NVIDIA_GPU_VALUES_FILE="${SCRIPT_DIR}/charts/values-nvidia-gpu.yaml"
AMD_GPU_VALUES_FILE="${SCRIPT_DIR}/charts/values-amd-gpu.yaml"
DISABLE_AI_VALUES_FILE="${SCRIPT_DIR}/charts/values-disable-ai-services.yaml"
SCALING_VALUES_FILE="${SCRIPT_DIR}/charts/values-scaling.yaml"
HTTP_VALUES_FILE="${SCRIPT_DIR}/charts/values-http.yaml"
DEBUG_PROBES_VALUES_FILE="${SCRIPT_DIR}/charts/values-debug-probes.yaml"
ONLINE_TEST_URL="https://gitlab.com"
OFFLINE_IMAGE_TAG="latest"
CERTIFICATE_SECRET_NAME="self-signed-cert"
MINIKUBE_HOSTPATH_PROVISIONER_DIR="/var/hostpath-provisioner"
LOOM_CHART_FILE="${SCRIPT_DIR}/charts/Chart.yaml"

WAIT_MAX_RETRIES=30

# The GPU device plugin is itself a pod, so it only registers
# <vendor>.com/gpu once the control plane and the CNI are back. Until it does,
# kubelet rejects every pod requesting the resource with a terminal
# UnexpectedAdmissionError, so the ceiling has to cover a cold plugin image pull.
WAIT_GPU_MAX_RETRIES=300

#
# Minikube host resource reservation
# (leave some resources free on the host)
#
# Note: --cpus expects a number; we compute (nproc - reserve) and FLOOR it to an integer.
# If reserve is 0, we pass "max" to minikube (same for memory).
MINIKUBE_HOST_CPU_RESERVE_CORES="0"
MINIKUBE_HOST_MEM_RESERVE_KIB="0"

#
# Kubelet resource configuration
# CPU and ephemeral-storage are fixed; memory values are computed dynamically
# in compute_kubelet_config() as percentages of the minikube node's RAM allocation.
#
KUBELET_SYSTEM_RESERVED_CPU="250m"
KUBELET_SYSTEM_RESERVED_EPHEMERAL="10Gi"
KUBELET_KUBE_RESERVED_CPU="250m"
KUBELET_KUBE_RESERVED_EPHEMERAL="5Gi"
KUBELET_EVICTION_SOFT_GRACE_PERIOD_MEMORY="90s"
KUBELET_EVICTION_HARD_NODEFS="2Gi"
KUBELET_EVICTION_HARD_IMAGEFS="2Gi"
# Set by compute_kubelet_config():
KUBELET_SYSTEM_RESERVED_MEMORY=""
KUBELET_KUBE_RESERVED_MEMORY=""
KUBELET_EVICTION_HARD_MEMORY=""
KUBELET_EVICTION_SOFT_MEMORY=""

#
# Controller-manager configuration
#
# A pod rejected at admission - a GPU pod that kubelet replayed after a reboot
# before the device plugin had registered, say - is terminal, and the
# ReplicaSet controller does not count terminal pods as active, so it never
# deletes them. Pod GC is what reaps them, and upstream's default threshold of
# 12500 means it effectively never runs here. A value <= 0 disables GC
# entirely; this one sits above the terminated pods a healthy cluster carries
# from the pre-install Jobs.
KUBE_CONTROLLER_TERMINATED_POD_GC_THRESHOLD="50"

#
# Shared variables
#

# variables defined in vars.sh, here for shellcheck:
NAMESPACE=""
LOOM_DOMAIN=""
LOOM_HOSTS_FQDN=()
TRAEFIK_HELM_VERSION=""
KEDA_HELM_VERSION=""
LOOM_MIN_CPU=""
LOOM_MIN_MEMORY=""
LOOM_MIN_GPU=""
LOOM_MINIKUBE_IP=""

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
    set_docker_platform
    set_offline_mode
    set_skaffold_profile
    set_skaffold_command
    set_skaffold_args
    write_up_flags_values
    write_trusted_ca_values
    validate_environment
    compute_minikube_cpu_resources
    compute_minikube_memory_resources
    compute_kubelet_config
    check_host_resources
    setup_system
    create_cluster
    default_use_csi-hostpath-driver
    install_host_entries
)

# Steps to setup the cluster before startup
STEPS_SETUP_CLUSTER=(
    create_namespace
    use_namespace
    detect_deployed_release
    inject_archive_enc_key
    create_docker_secret_from_config
    install_third_party
    install_certificate
    stop_expose_minikube
    warn_dev_or_integration
)

# Steps main appends depending on the flags. Listed here so that --skip-STEP
# accepts them regardless of whether this run assembles them into STEPS.
STEPS_CONDITIONAL=(
    expose_minikube
    run_skaffold
)

# Every step name --skip-STEP accepts.
ALL_STEPS=(
    "${STEPS_SETUP_SYSTEM[@]}"
    "${STEPS_SETUP_CLUSTER[@]}"
    "${STEPS_CONDITIONAL[@]}"
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
# Extended resource the chosen GPU vendor's device plugin advertises. Set
# alongside the addon in create_cluster().
GPU_RESOURCE_NAME=""
RESUME_IF_DEPLOYED=false
OFFLINE_MODE=false
NO_RESOURCES=false
SCALING=false
ENABLE_HTTP=false
DELETE=false
DOWN=false
SKAFFOLD_PROFILE="prod"
SKAFFOLD_ARGS=()
THIRD_PARTY_SKAFFOLD_ARGS=()
UP_FLAG_VALUES=()
SKAFFOLD_COMMAND="run"
SKAFFOLD_CACHE_FILE="${SKAFFOLD_HOME}/cache"
SKAFFOLD_REMOTE_CACHE_DIR="${SKAFFOLD_HOME}/remote-cache"
CERTIFICATE=false
# Host architecture in Docker/Go naming ("amd64", "arm64"). Set by
# set_docker_platform(); initialised here so that --skip-set_docker_platform
# does not leave it unbound for run_skaffold().
TARGETARCH="amd64"
MINIKUBE_MOUNT_STRING=""
TRUSTED_CA_BUNDLE=""
ARCHIVE_ENC_KEY=""

# Computed Minikube resources
MINIKUBE_CPUS=""
# NOTE: This contains the exact value passed to minikube --memory, INCLUDING suffix if needed ("1234kb" or "max")
MINIKUBE_MEMORY_KIB=""

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

# Abort on a malformed command line.
#
# Argument parsing runs with the atexit trap already armed, and atexit tears the
# deployment down once --development or --delete has been parsed. A usage error
# must leave a running deployment untouched, so disarm the trap before exiting.
die_usage() {
    local message
    message="${1}" && shift

    echo >&2 "[!] Error: ${message}"
    echo >&2 ""
    usage >&2
    trap - EXIT
    exit 1
}

# Exact match against ALL_STEPS. A substring test would let a step name that is
# a prefix of another skip both.
is_known_step() {
    local candidate
    candidate="${1}" && shift

    local step
    for step in "${ALL_STEPS[@]}"; do
        if [[ "${step}" == "${candidate}" ]]; then
            return 0
        fi
    done

    return 1
}

is_skipped() {
    local candidate
    candidate="${1}" && shift

    local skipped
    for skipped in "${SKIP[@]}"; do
        if [[ "${skipped}" == "${candidate}" ]]; then
            return 0
        fi
    done

    return 1
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

# Wait for every background job in turn and report the first failure.
#
# `wait pid1 pid2` returns the status of the *last* pid alone, so a job that
# fails anywhere else in the list is taken for a success and whatever depends on
# it runs anyway.
wait_all(){
    local status
    status=0

    local pid
    for pid in "${@}"; do
        wait "${pid}" || status=$?
    done

    return "${status}"
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

# The node advertises the GPU vendor's extended resource. The cluster is
# single-node, so select over .items[*] rather than naming the node; the dots in
# "nvidia.com/gpu" have to be escaped for jsonpath.
is_gpu_resource_registered() {
    local allocatable
    allocatable="$(
        kubectl get nodes \
            --output "jsonpath={.items[*].status.allocatable.${GPU_RESOURCE_NAME//./\\.}}" \
        2>/dev/null
    )" || return 1

    [[ -n "${allocatable}" ]] && [[ "${allocatable}" -ge 1 ]]
}

# A deployment carries the helm.sh/chart label of the chart version we are
# about to deploy. The loom and traefik skaffold configs render with
# `helm template` and apply with kubectl, so no helm release is recorded and
# this label is the only record of what is installed.
is_chart_deployed() {
    local deployment expected actual
    deployment="${1}" && shift
    expected="${1}" && shift

    actual="$(
        kubectl get deployment "${deployment}" \
            --namespace "${NAMESPACE}" \
            --output 'jsonpath={.metadata.labels.helm\.sh/chart}' \
        2>/dev/null
    )" || return 1

    if [[ "${actual}" != "${expected}" ]]; then
        echo "[*] ${deployment}: have '${actual:-nothing}', want '${expected}'."
        return 1
    fi

    return 0
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
        # The dev profile is served over plain http as well as https, and that
        # decision lives in one file rather than being restated in
        # values-development.yaml -- so cicd/check_http_values.sh covers the dev
        # deployment too, and a component added to the chart cannot be widened
        # for `--enable-http` and forgotten here.
        #
        # Appended where the profile is chosen rather than in the flag cases,
        # because both flags arrive here and the integration tests are the half
        # that actually depends on it: they reach Loom over http://rabbit.loom
        # and http://elasticsearch.loom throughout.
        #
        # ENABLE_HTTP is set with it, not just the values file. This step runs before
        # validate_environment, which refuses plain http beside
        # certificate.requireClientCert -- and that guard reads ENABLE_HTTP, so
        # widening every route to the `web` entrypoint while leaving the flag false
        # would accept `up -d` on a deployment requiring a client certificate and
        # serve every host in cleartext: the exact bypass the guard exists for. A
        # duplicate values-file entry when --enable-http is also given is harmless,
        # since yq deep-merges.
        ENABLE_HTTP=true
        UP_FLAG_VALUES+=("${HTTP_VALUES_FILE}")
    fi
    if [[ "${OFFLINE_MODE}" = true ]]; then
        SKAFFOLD_PROFILE="offline"
    fi
}

set_skaffold_command(){
    if [[ "${DEVELOPMENT}" = true ]]; then
        SKAFFOLD_COMMAND="dev"
    fi
}

set_skaffold_args(){
    if [[ "${DEVELOPMENT}" = true ]]; then
        SKAFFOLD_ARGS+=(
            "--auto-build"
            "--auto-deploy"
            "--auto-sync"
            # Forward the ports listed under `portForward` in the dev profile of skaffold.yaml,
            # and nothing else. Without this, skaffold decides for itself which containers look
            # debuggable, which forwards ports into Jobs that never listen on them and into
            # third-party services nobody attaches to.
            "--port-forward=user"
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
        THIRD_PARTY_SKAFFOLD_ARGS+=( "${offline_skaffold_args[@]}" )
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
    THIRD_PARTY_SKAFFOLD_ARGS+=(
        "${skaffold_cache_args[@]}"
    )
}

write_trusted_ca_values() {
    if [[ -z "${TRUSTED_CA_BUNDLE}" ]]; then
        return
    fi
    if [[ ! -f "${TRUSTED_CA_BUNDLE}" ]]; then
        echo >&2 "[!] Error: --trusted-ca-bundle: file not found: ${TRUSTED_CA_BUNDLE}"
        exit 1
    fi
    # Parse the PEM bundle and append trustedCertificates YAML to the shared
    # up-flags values file (last-occurrence wins in Helm's Go YAML parser).
    awk '
        /-----BEGIN CERTIFICATE-----/ { in_cert=1; cert=""; idx++ }
        in_cert { cert = cert $0 "\n" }
        /-----END CERTIFICATE-----/ {
            in_cert = 0
            if (idx == 1) {
                print "trustedCertificates:"
                print "  certs:"
            }
            printf "    - name: trusted-ca-%d\n", idx-1
            printf "      data: |\n"
            n = split(cert, lines, "\n")
            for (i=1; i<=n; i++) {
                if (lines[i] != "") printf "        %s\n", lines[i]
            }
        }
        END {
            if (idx == 0) {
                print "[!] Error: no certificates found in --trusted-ca-bundle file" > "/dev/stderr"
                exit 1
            }
        }
    ' "${TRUSTED_CA_BUNDLE}" >> "${UP_FLAGS_VALUES_FILE}"
}

write_up_flags_values() {
    # Deep-merge active flag-driven values files into UP_FLAGS_VALUES_FILE.
    # Skaffold always includes this file (listed in skaffold.yaml before values-overwrites.yaml).
    # Uses yq to deep-merge so that overlapping top-level keys are combined rather than
    # one file silently overwriting another (e.g. --disable-ai + --no-resources both touch ollama).
    # UP_FLAG_VALUES is populated during argument parsing — add new flags there.
    if [[ ${#UP_FLAG_VALUES[@]} -eq 0 ]]; then
        true > "${UP_FLAGS_VALUES_FILE}"
    else
        # Single quotes are intentional: this is a jq expression, not shell.
        # shellcheck disable=SC2016
        yq -y -s 'reduce .[] as $item ({}; . * $item)' "${UP_FLAG_VALUES[@]}" > "${UP_FLAGS_VALUES_FILE}"
    fi
}

# Whether the values this deployment will render with require a client certificate.
#
# The same deep merge, in the same order, that skaffold performs -- see the
# `valuesFiles` list in skaffold.yaml. charts/values-up-flags.yaml is deliberately left
# out: no up.sh flag sets this key, and the file has not been written yet when this runs.
# Files that parse to null (absent, or comments only) are skipped rather than merged,
# since `{} * null` is an error rather than a no-op.
client_certificate_required() {
    # Prints `true` or `false` rather than answering through its exit status: a
    # function in an `if` condition switches `set -e` off for everything it runs, and
    # this one runs yq over four files.
    local merged
    # Single quotes are intentional: this is a jq expression, not shell.
    # shellcheck disable=SC2016
    merged="$(
        yq -s 'reduce (.[] | select(. != null)) as $item ({}; . * $item) | .certificate.requireClientCert' \
            "${SCRIPT_DIR}/charts/values.yaml" \
            "${SCRIPT_DIR}/charts/values-user.yaml" \
            "${SCRIPT_DIR}/charts/values-appliance.yaml" \
            "${SCRIPT_DIR}/charts/values-overwrites.yaml" 2> /dev/null || true
    )"
    if [[ "${merged}" = "true" ]]; then
        printf 'true'
    else
        printf 'false'
    fi
}

validate_environment() {
    # --scaling enables a resource quota that requires requests on every pod.
    # --no-resources nullifies all requests, so the quota blocks pod creation.
    if [[ "${SCALING}" = true ]] && [[ "${NO_RESOURCES}" = true ]]; then
        echo >&2 "[!] Error: --scaling and --no-resources are incompatible."
        echo >&2 "[!] The scaling resource quota requires CPU/memory requests on every pod,"
        echo >&2 "[!] but --no-resources removes them. Use one or the other."
        exit 1
    fi

    # --enable-http does not weaken certificate.requireClientCert, it bypasses it.
    #
    # The `-mtls` TLSOption is attached as `router.tls.options`, which constrains the
    # TLS handshake and nothing else. Widening every router onto the `web` entrypoint
    # and switching the global redirect off means the same routes answer in cleartext,
    # where no client certificate is asked for at all -- so a deployment that believes
    # it requires one serves every host to anyone who can reach port 80.
    #
    # The appliance is already safe: nixos/modes.nix drops --enable-http from a
    # --require-client-cert image. Nothing guarded a deployment driving up.sh by hand.
    local requires_client_cert
    requires_client_cert="$(client_certificate_required)"
    if [[ "${ENABLE_HTTP}" = true ]] && [[ "${requires_client_cert}" = true ]]; then
        echo >&2 "[!] Error: --enable-http and certificate.requireClientCert are incompatible."
        echo >&2 "[!] The client-certificate requirement only applies to the TLS handshake, so"
        echo >&2 "[!] serving the same routes over plain http bypasses it entirely rather than"
        echo >&2 "[!] weakening it. Drop one of the two."
        exit 1
    fi

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

    # Check git lfs. Objects live under the common git dir, which is shared by all
    # worktrees — resolve it instead of assuming '.git' is a directory, since in a
    # worktree '.git' is a file pointing at the real git dir.
    local git_common_dir
    git_common_dir=$(git -C "${SCRIPT_DIR}" rev-parse --path-format=absolute --git-common-dir)
    if [[ ! -d "${git_common_dir}/lfs/objects" ]]; then
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
    check_command nproc
    check_command awk
    check_command df
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
    check_command yq

    # GPU tools (only required when --gpus is passed)
    if [[ -n "${GPUS}" ]]; then
        case "${GPUS}" in
            amd)
                check_command rocm-smi
            ;;
            nvidia)
                check_command nvidia-smi
            ;;
            *)
                echo >&2 "[!] Error: Invalid GPU type '${GPUS}'. Valid options: amd, nvidia"
                exit 1
            ;;
        esac
    fi
}

compute_minikube_cpu_resources() {
    if [[ "${MINIKUBE_HOST_CPU_RESERVE_CORES}" == "0" ]] || [[ "${MINIKUBE_HOST_CPU_RESERVE_CORES}" == "0.0" ]]; then
        MINIKUBE_CPUS="max"
        return
    fi

    local total_cpus
    total_cpus="$(nproc)"

    # Compute usable CPUs: floor(total - reserve), minimum 1
    MINIKUBE_CPUS="$(
        awk -v total="${total_cpus}" -v reserve="${MINIKUBE_HOST_CPU_RESERVE_CORES}" '
            BEGIN {
                usable = total - reserve;
                if (usable < 1) usable = 1;
                printf("%d\n", usable);
            }
        '
    )"
}

compute_minikube_memory_resources() {
    # Memory
    # - If reserve is 0 -> use "max" (no suffix!)
    # - Else -> compute KiB and append "kb" suffix here
    if [[ "${MINIKUBE_HOST_MEM_RESERVE_KIB}" == "0" ]]; then
        MINIKUBE_MEMORY_KIB="max"
        return
    fi

    # Memory: keep everything in KiB (MemTotal is in KiB)
    local mem_total_kib
    mem_total_kib="$(
        awk '
            $1 == "MemTotal:" { print $2; exit }
        ' /proc/meminfo
    )"

    if [[ -z "${mem_total_kib}" ]]; then
        echo >&2 "[!] Error: Could not read MemTotal from /proc/meminfo"
        exit 1
    fi

    # Reserve some memory, minimum 524288 KiB (512 MiB)
    local usable_kib
    usable_kib="$(
        awk -v total="${mem_total_kib}" -v reserve="${MINIKUBE_HOST_MEM_RESERVE_KIB}" '
            BEGIN {
                usable = total - reserve;
                if (usable < 524288) usable = 524288;
                printf("%d\n", usable);
            }
        '
    )"

    MINIKUBE_MEMORY_KIB="${usable_kib}kb"
}

compute_kubelet_config() {
    # Determine the minikube node's RAM in MiB.
    # compute_minikube_memory_resources() already ran and set MINIKUBE_MEMORY_KIB.
    local node_mem_mib
    if [[ "${MINIKUBE_MEMORY_KIB}" == "max" ]]; then
        # minikube will use all available host RAM
        node_mem_mib="$(awk '$1 == "MemTotal:" { printf("%d", $2 / 1024); exit }' /proc/meminfo)"
    else
        # MINIKUBE_MEMORY_KIB is "<value>kb"
        local node_mem_kib="${MINIKUBE_MEMORY_KIB%kb}"
        node_mem_mib=$(( node_mem_kib / 1024 ))
    fi

    # Compute memory reservations. Loom runs on the Docker driver (no guest OS inside
    # the minikube container), but pod count scales with node RAM via HPA, so:
    #   system-reserved: fixed 1024 MiB       — init + containerd inside minikube container;
    #                                            fixed overhead independent of pod count
    #   kube-reserved:   4%  (min  512 MiB)  — kubelet tracks per-pod state, scales with pods
    #   eviction-hard:   6%  (min  500 MiB)  — safety buffer scales with node size and pod count
    #   eviction-soft:   8%  (min  750 MiB)  — soft warning with grace period
    local awk_result
    awk_result="$(awk -v mem="${node_mem_mib}" 'BEGIN {
        sys  = 1024;
        kube = int(mem * 0.04); if (kube <  512) kube =  512;
        hard = int(mem * 0.06); if (hard <  500) hard =  500;
        soft = int(mem * 0.08); if (soft <  750) soft =  750;
        printf("%dMi %dMi %dMi %dMi\n", sys, kube, hard, soft);
    }')"
    read -r KUBELET_SYSTEM_RESERVED_MEMORY \
            KUBELET_KUBE_RESERVED_MEMORY \
            KUBELET_EVICTION_HARD_MEMORY \
            KUBELET_EVICTION_SOFT_MEMORY \
        <<< "${awk_result}"
}

check_host_resources() {
    if [[ "${NO_RESOURCES}" = true ]]; then
        echo "[*] Skipping host resource check (--no-resources)"
        return
    fi

    local errors=0

    # CPU check
    local host_cpu
    host_cpu="$(nproc)"
    if [[ "${host_cpu}" -lt "${LOOM_MIN_CPU}" ]]; then
        echo >&2 "[!] Error: Host has ${host_cpu} CPU core(s), minimum required is ${LOOM_MIN_CPU}."
        errors=$((errors + 1))
    fi

    # RAM check: /proc/meminfo reports MemTotal in kB; LOOM_MIN_MEMORY is in Gi.
    # Add kubelet overhead (system-reserved + kube-reserved + eviction-hard) so the
    # check reflects memory actually available to Loom workloads.
    local host_mem_kib min_mem_kib
    host_mem_kib="$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)"
    min_mem_kib=$(( ${LOOM_MIN_MEMORY%Gi} * 1024 * 1024 ))
    local kubelet_overhead_kib
    kubelet_overhead_kib=$(( (${KUBELET_SYSTEM_RESERVED_MEMORY%Mi} + ${KUBELET_KUBE_RESERVED_MEMORY%Mi} + ${KUBELET_EVICTION_HARD_MEMORY%Mi}) * 1024 ))
    min_mem_kib=$((min_mem_kib + kubelet_overhead_kib))
    if [[ "${host_mem_kib}" -lt "${min_mem_kib}" ]]; then
        local host_mem_gi min_mem_gi_total
        host_mem_gi=$(awk "BEGIN { printf \"%.1f\", ${host_mem_kib} / 1048576 }")
        min_mem_gi_total=$(awk "BEGIN { printf \"%.1f\", ${min_mem_kib} / 1048576 }")
        echo >&2 "[!] Error: Host has ${host_mem_gi} GiB RAM, minimum required is ${min_mem_gi_total} GiB (${LOOM_MIN_MEMORY} for Loom + kubelet overhead)."
        errors=$((errors + 1))
    fi

    # GPU check: only relevant when --gpus flag is passed
    if [[ -n "${GPUS}" ]]; then
        local host_gpu
        case "${GPUS}" in
            # A failing probe (no driver, no device) must report 0 GPUs through the
            # errors counter below, not abort the script via `set -eo pipefail`.
            # The `||` runs after the assignment, so it overwrites whatever partial
            # output the failed pipeline produced.
            amd)
                # Count AMD GPUs using rocm-smi
                host_gpu="$(rocm-smi 2>/dev/null | grep -cE '^[0-9]+\s')" || host_gpu=0
            ;;
            nvidia)
                host_gpu="$(nvidia-smi --list-gpus 2>/dev/null | wc -l)" || host_gpu=0
            ;;
            *)
                echo >&2 "[!] Error: Invalid GPU type '${GPUS}'. Valid options: amd, nvidia"
                exit 1
            ;;
        esac
        if [[ "${host_gpu}" -lt "${LOOM_MIN_GPU}" ]]; then
            echo >&2 "[!] Error: Host has ${host_gpu} GPU(s), minimum required is ${LOOM_MIN_GPU}."
            errors=$((errors + 1))
        fi
    fi

    if [[ "${errors}" -gt 0 ]]; then
        echo >&2 "[!] Error: Host does not meet minimum resource requirements."
        exit 1
    fi
}

inject_archive_enc_key() {
    if [[ -z "${ARCHIVE_ENC_KEY}" ]]; then
        return
    fi
    echo "[*] Injecting archive encryption key into secret 'archive-enc-master-key'"
    kubectl create secret generic archive-enc-master-key \
        --namespace="${NAMESPACE}" \
        --from-literal=secretkey="${ARCHIVE_ENC_KEY}" \
        --dry-run=client \
        --output yaml \
    | kubectl apply -f -
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
    FS_FILE_MAX=2097152
    fs_file_max="$(sysctl -n fs.file-max)"
    if [[ "${fs_file_max}" -lt "${FS_FILE_MAX}" ]]; then
        sudo sysctl -w "fs.file-max=${FS_FILE_MAX}"
        sysctl_changed=true
    fi
    VM_SWAPPINESS=1
    vm_swappiness="$(sysctl -n vm.swappiness)"
    if [[ "${vm_swappiness}" != "${VM_SWAPPINESS}" ]]; then
        sudo sysctl -w "vm.swappiness=${VM_SWAPPINESS}"
        sysctl_changed=true
    fi
    # Allow more dirty pages to accumulate in RAM before processes are throttled
    # waiting for writeback. Reduces I/O stalls during heavy document processing
    # (e.g. concurrent ImageMagick convert jobs writing large temp files).
    VM_DIRTY_BACKGROUND_RATIO=10
    vm_dirty_background_ratio="$(sysctl -n vm.dirty_background_ratio)"
    if [[ "${vm_dirty_background_ratio}" -lt "${VM_DIRTY_BACKGROUND_RATIO}" ]]; then
        sudo sysctl -w "vm.dirty_background_ratio=${VM_DIRTY_BACKGROUND_RATIO}"
        sysctl_changed=true
    fi
    VM_DIRTY_RATIO=40
    vm_dirty_ratio="$(sysctl -n vm.dirty_ratio)"
    if [[ "${vm_dirty_ratio}" -lt "${VM_DIRTY_RATIO}" ]]; then
        sudo sysctl -w "vm.dirty_ratio=${VM_DIRTY_RATIO}"
        sysctl_changed=true
    fi
    SYSCTL_CONF_FILE="/etc/sysctl.d/99-loom.conf"
    if [[ ! -f "${SYSCTL_CONF_FILE}" ]] || [[ "${sysctl_changed}" = true ]]; then
        sudo tee "${SYSCTL_CONF_FILE}" <<EOF
vm.max_map_count=${VM_MAX_MAP_COUNT}
vm.overcommit_memory=${VM_OVERCOMMIT_MEMORY}
fs.inotify.max_user_watches=${FS_INOTIFY_MAX_WATCHES}
fs.inotify.max_user_instances=${FS_INOTIFY_MAX_INSTANCES}
fs.file-max=${FS_FILE_MAX}
vm.swappiness=${VM_SWAPPINESS}
vm.dirty_background_ratio=${VM_DIRTY_BACKGROUND_RATIO}
vm.dirty_ratio=${VM_DIRTY_RATIO}
EOF
    fi
}

check_mount_string_disk_space() {
    # Parse e.g. "2Gi" into KiB for comparison with df -k output
    local threshold_str="${KUBELET_EVICTION_HARD_NODEFS}"
    local threshold_kib
    threshold_kib="$(awk -v t="${threshold_str}" 'BEGIN {
        val = t + 0
        unit = substr(t, length(t)-1)
        if (unit == "Gi") val = val * 1024 * 1024
        else if (unit == "Mi") val = val * 1024
        else if (unit == "Ki") val = val
        print int(val)
    }')"

    local avail_kib
    avail_kib="$(df -k "${MINIKUBE_MOUNT_STRING}" | awk 'NR==2 { print $4 }')"

    if (( avail_kib < threshold_kib )); then
        local avail_gib
        avail_gib="$(awk -v k="${avail_kib}" 'BEGIN { printf("%.1f", k/1024/1024) }')"
        echo >&2 "[!] --mount-string path '${MINIKUBE_MOUNT_STRING}' is on a filesystem with only ${avail_gib} GiB free."
        echo >&2 "[!] At least ${threshold_str} is required (kubelet eviction threshold)."
        echo >&2 "[!] Please free up disk space or choose a path on a less-full filesystem."
        exit 1
    fi
}

# Pin the Docker platform to the host architecture so that every `docker pull`
# and `docker build` in this run resolves multi-arch manifests to the arch the
# cluster actually runs on. TARGETARCH is the Docker/Go spelling of `uname -m`
# and is reused by run_skaffold() as the default --platform.
set_docker_platform(){
    local host_arch
    host_arch="$(uname -m)"
    case "${host_arch}" in
        aarch64|arm64)
            TARGETARCH="arm64"
        ;;
        x86_64|amd64)
            TARGETARCH="amd64"
        ;;
        *)
            echo >&2 "[!] Error: Unsupported host architecture '${host_arch}'."
            echo >&2 "[!] Loom images are only built for linux/amd64 and linux/arm64."
            exit 1
        ;;
    esac
    export TARGETARCH
    export DOCKER_DEFAULT_PLATFORM="linux/${TARGETARCH}"
    echo "[*] Detected ${host_arch}, setting DOCKER_DEFAULT_PLATFORM=${DOCKER_DEFAULT_PLATFORM}"

    # BuildKit resolves the base image manifest per platform; the legacy builder
    # does not honour DOCKER_DEFAULT_PLATFORM on every code path.
    export DOCKER_BUILDKIT=1

    # skaffold reads SKAFFOLD_PLATFORM from the environment on every subcommand
    # that supports --platform, so exporting it here covers both the application
    # build (run_skaffold) and the third-party ones (cicd/skaffold). A value
    # already set by the caller - e.g. a multi-platform CI build - wins.
    export SKAFFOLD_PLATFORM="${SKAFFOLD_PLATFORM:-linux/${TARGETARCH}}"
    echo "[*] Building for platform: ${SKAFFOLD_PLATFORM}"
}

create_cluster(){
    echo "[*] Minikube resources:"
    echo "[*]   Host CPU reserve: ${MINIKUBE_HOST_CPU_RESERVE_CORES} -> using: ${MINIKUBE_CPUS}"
    echo "[*]   Host Mem reserve: ${MINIKUBE_HOST_MEM_RESERVE_KIB}KiB -> using: ${MINIKUBE_MEMORY_KIB}"
    echo "[*] Kubelet memory reservations:"
    echo "[*]   system-reserved: ${KUBELET_SYSTEM_RESERVED_MEMORY}"
    echo "[*]   kube-reserved:   ${KUBELET_KUBE_RESERVED_MEMORY}"
    echo "[*]   eviction-hard:   memory.available<${KUBELET_EVICTION_HARD_MEMORY}"
    echo "[*]   eviction-soft:   memory.available<${KUBELET_EVICTION_SOFT_MEMORY} (grace: ${KUBELET_EVICTION_SOFT_GRACE_PERIOD_MEMORY})"

    local mount_args=()
    local addons="metrics-server,csi-hostpath-driver"
    if [[ -n "${MINIKUBE_MOUNT_STRING}" ]]; then
        check_mount_string_disk_space
        # With --mount-string we use the standard storage-provisioner (deterministic
        # paths keyed by namespace/pvc-name) instead of CSI (random UUID paths).
        # This allows PVC data to survive a full cluster rebuild as long as the host
        # directory is preserved.
        addons="metrics-server"
        mount_args=(
            "--mount-string=${MINIKUBE_MOUNT_STRING}:${MINIKUBE_HOSTPATH_PROVISIONER_DIR}"
        )
    fi

    # Enable GPU device plugin if GPUs are requested
    local gpu_args=()
    if [[ -n "${GPUS}" ]]; then
        case "${GPUS}" in
            amd)
                addons="${addons},amd-gpu-device-plugin"
                GPU_RESOURCE_NAME="amd.com/gpu"
            ;;
            nvidia)
                # NVIDIA's own plugin, not minikube's `nvidia-gpu-device-plugin`:
                # that one is deprecated upstream and ships a single amd64 image,
                # which cannot run on an aarch64 node such as the DGX Spark.
                addons="${addons},nvidia-device-plugin"
                GPU_RESOURCE_NAME="nvidia.com/gpu"
            ;;
            *)
                echo >&2 "[!] Error: Invalid GPU type '${GPUS}'. Valid options: amd, nvidia"
                exit 1
            ;;
        esac
        gpu_args=(--gpus "${GPUS}")
    fi

    minikube start \
        --driver docker \
        --static-ip "${LOOM_MINIKUBE_IP}" \
        --wait all \
        --registry-mirror "${REGISTRY_MIRROR}" \
        --memory "${MINIKUBE_MEMORY_KIB}" \
        --cpus "${MINIKUBE_CPUS}" \
        --cni calico \
        --addons "${addons}" \
        --extra-config="kubelet.system-reserved=cpu=${KUBELET_SYSTEM_RESERVED_CPU},memory=${KUBELET_SYSTEM_RESERVED_MEMORY},ephemeral-storage=${KUBELET_SYSTEM_RESERVED_EPHEMERAL}" \
        --extra-config="kubelet.kube-reserved=cpu=${KUBELET_KUBE_RESERVED_CPU},memory=${KUBELET_KUBE_RESERVED_MEMORY},ephemeral-storage=${KUBELET_KUBE_RESERVED_EPHEMERAL}" \
        --extra-config="kubelet.eviction-hard=memory.available<${KUBELET_EVICTION_HARD_MEMORY},nodefs.available<${KUBELET_EVICTION_HARD_NODEFS},imagefs.available<${KUBELET_EVICTION_HARD_IMAGEFS}" \
        --extra-config="kubelet.eviction-soft=memory.available<${KUBELET_EVICTION_SOFT_MEMORY}" \
        --extra-config="kubelet.eviction-soft-grace-period=memory.available=${KUBELET_EVICTION_SOFT_GRACE_PERIOD_MEMORY}" \
        --extra-config="controller-manager.terminated-pod-gc-threshold=${KUBE_CONTROLLER_TERMINATED_POD_GC_THRESHOLD}" \
        "${gpu_args[@]}" \
        "${mount_args[@]}"

    assert_minikube_ip
    assert_gpu_resource_registered
}

# What --static-ip asked for, against what the node actually got.
#
# minikube treats the flag as advice in three cases: a cluster that already
# exists keeps its address and only warns, a docker network already carrying the
# profile's name wins over it, and a non-kic driver ignores it outright. None of
# those is survivable here. `kubernetes.api` in charts/values.yaml is an ipBlock
# in the `-allow-k8s-api` NetworkPolicy, matched after kube-proxy has rewritten
# 10.96.0.1:443 to the node -- so a node anywhere else leaves every pod in the
# namespace denied its own API server, and the deployment then fails in a dozen
# places that never mention an address.
#
# Called from create_cluster rather than listed in STEPS_SETUP_SYSTEM: it is an
# assertion about the command directly above it and must not be skippable on its
# own. It runs before skaffold puts an image in the node, so the fix it names is
# still free -- `minikube delete` costs the whole image store once the images are
# there, and on an appliance that is not recoverable.
assert_minikube_ip(){
    local minikube_ip

    if ! minikube_ip="$(minikube ip)"; then
        echo >&2 "[!] Error: the cluster started but 'minikube ip' has no address for it."
        echo >&2 "    Run 'minikube delete' and try again."
        exit 1
    fi

    if [[ "${minikube_ip}" != "${LOOM_MINIKUBE_IP}" ]]; then
        echo >&2 "[!] Error: the minikube node is at ${minikube_ip}, not at the"
        echo >&2 "    ${LOOM_MINIKUBE_IP} that 'kubernetes.api' in charts/values.yaml names."
        echo >&2 "    That address is the only egress to the API server every pod has, so"
        echo >&2 "    this cluster would deploy a Loom that cannot reach its own control"
        echo >&2 "    plane."
        echo >&2 ""
        echo >&2 "    --static-ip cannot move a cluster that already exists, and a leftover"
        echo >&2 "    docker network of the same name wins over it:"
        echo >&2 "      minikube delete && docker network rm minikube"
        echo >&2 "    and run this again. If ${LOOM_MINIKUBE_IP} is already routed on this"
        echo >&2 "    host, change 'kubernetes.api' in charts/values.yaml instead."
        exit 1
    fi

    echo "[*] Minikube node is at ${minikube_ip}, as pinned"
}

# What the GPU device plugin addon was asked for, against what the node
# actually advertises.
#
# `minikube start --wait all` waits for the core components and nothing else.
# The device plugin is an ordinary DaemonSet that is scheduled, pulled and
# started after that, and only then registers <vendor>.com/gpu with the kubelet
# -- measured at ~86s on a DGX Spark with the image already on the node.
#
# A pod that requests the resource inside that window is not retried. Kubelet
# rejects it at admission: phase Failed, reason UnexpectedAdmissionError,
# "Allocate failed due to no healthy devices present", and the owning ReplicaSet
# keeps that terminal pod rather than replacing it. Ollama is the only workload
# that asks for a GPU, so the symptom is an appliance whose AI half is down with
# nothing in the log that mentions a race.
#
# Called from create_cluster rather than listed in STEPS_SETUP_SYSTEM, for the
# same reason assert_minikube_ip is: it is an assertion about the command
# directly above it and must not be skippable on its own.
#
# It fails the run rather than warning, which is the choice check_host_resources
# already makes for --gpus on a box whose nvidia-smi finds nothing: a Loom that
# asked for a GPU and was not given one is a misconfiguration, and this is the
# last place it can still be named.
assert_gpu_resource_registered(){
    if [[ -z "${GPUS}" ]]; then
        return
    fi

    echo "[*] Waiting for the node to advertise ${GPU_RESOURCE_NAME}"

    local retry_count
    retry_count=0

    # shellcheck disable=SC2310
    while ! is_gpu_resource_registered; do
        if [[ "${retry_count}" -ge "${WAIT_GPU_MAX_RETRIES}" ]]; then
            echo >&2 "[!] Error: the node still does not advertise ${GPU_RESOURCE_NAME}"
            echo >&2 "    after ${WAIT_GPU_MAX_RETRIES} seconds."
            echo >&2 ""
            echo >&2 "    The ${GPUS} device plugin is what registers that resource. Deploying"
            echo >&2 "    now would put the ollama pod through kubelet admission before it"
            echo >&2 "    exists, and admission rejects rather than retries: the pod would sit"
            echo >&2 "    in UnexpectedAdmissionError for the life of the cluster."
            echo >&2 ""
            echo >&2 "    Look at the plugin:"
            echo >&2 "      kubectl --namespace kube-system get daemonsets,pods | grep device-plugin"
            echo >&2 "    A host whose driver is missing, or a node with no copy of the plugin"
            echo >&2 "    image, shows up there. To bring Loom up without the GPU at all, run"
            echo >&2 "    without --gpus."
            exit 1
        fi

        echo "[*] Waiting for ${GPU_RESOURCE_NAME}... Attempt $((retry_count+1))/${WAIT_GPU_MAX_RETRIES}"
        sleep 1
        retry_count=$((retry_count + 1))
    done

    echo "[*] Node advertises ${GPU_RESOURCE_NAME}"
}

default_use_csi-hostpath-driver(){
    if [[ -n "${MINIKUBE_MOUNT_STRING}" ]]; then
        # storage-provisioner is already the default; nothing to do.
        return
    fi
    minikube addons disable storage-provisioner
    minikube addons disable default-storageclass

    kubectl patch storageclass csi-hostpath-sc \
        -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
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

# Skip the deploy when the cluster already carries this checkout's release.
#
# `skaffold run` stamps a fresh skaffold.dev/run-id UUID into every pod template
# on every invocation, so every Deployment in the namespace rolls on every run
# even when nothing changed. A host that runs this script at every boot --
# loom.service on the appliance -- therefore redeploys a stack that was already
# correct, and the new ollama pod goes through kubelet admission while the GPU
# device plugin is still starting.
#
# The chart version is read off live objects rather than from `helm list`: the
# loom and traefik skaffold configs render with `helm template` and apply with
# kubectl, so no helm release is recorded and the helm.sh/chart label is the
# only record of what is installed.
#
# Opt-in, because a developer running `up` expects their working tree to reach
# the cluster whether or not the chart version moved.
detect_deployed_release(){
    if [[ "${RESUME_IF_DEPLOYED}" = false ]]; then
        return
    fi

    local chart_version
    chart_version="$(yq --raw-output '.version' "${LOOM_CHART_FILE}")"

    # Two release names, not three: the dev profile renames the release to
    # `development`, and prod and offline both leave it at `production`.
    local release
    if [[ "${SKAFFOLD_PROFILE}" = "dev" ]]; then
        release="development"
    else
        release="production"
    fi

    # shellcheck disable=SC2310
    if ! is_chart_deployed \
        "${release}-loom-api" "loom-${chart_version}"; then
        echo "[*] Deploying: the cluster does not carry loom-${chart_version}."
        return
    fi

    # shellcheck disable=SC2310
    if ! is_chart_deployed \
        "${release}-traefik" "traefik-${TRAEFIK_HELM_VERSION}"; then
        echo "[*] Deploying: the cluster does not carry traefik-${TRAEFIK_HELM_VERSION}."
        return
    fi

    # KEDA is only installed under --scaling, so asking for it unconditionally
    # would keep every non-scaling deployment off the fast path for good.
    if [[ "${SCALING}" = true ]]; then
        # shellcheck disable=SC2310
        if ! is_chart_deployed \
            "${release}-keda-operator" "keda-${KEDA_HELM_VERSION}"; then
            echo "[*] Deploying: the cluster does not carry keda-${KEDA_HELM_VERSION}."
            return
        fi
    fi

    # install_certificate is deliberately still run: it installs a certificate
    # from files on the host that this script cannot fingerprint, so skipping it
    # would silently keep one the operator has just replaced. It is two kubectl
    # calls, and a no-op without --certificate.
    echo "[*] The cluster already carries loom-${chart_version}; not redeploying."
    # SKIP holds bare step names, not --skip-STEP arguments: the argument parser
    # strips the prefix before appending, and is_skipped() compares what Main
    # passes it -- a bare step name -- verbatim against each entry. A prefixed
    # entry matches nothing and is silently ignored.
    SKIP+=(
        install_third_party
        run_skaffold
    )
}

install_traefik(){
    (
        cd "${TRAEFIK_DIR}"

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

        # Remove the release for the profile we are *not* deploying. Traefik
        # binds the host's ports 80 and 443, so `up` and `up -d` cannot both
        # have one, and the dev profile is the only one that renames the release
        # (prod and offline both deploy it as `production`).
        #
        # The release we *are* deploying needs no delete: traefik/values.yaml
        # sets updateStrategy to Recreate, so an in-place upgrade takes the old
        # pod down before binding the ports again, where a delete costs a full
        # ingress teardown on every bring-up.
        # Related: https://github.com/GoogleContainerTools/skaffold/issues/9222
        if [[ "${SKAFFOLD_PROFILE}" = "dev" ]]; then
            "${CICD_SKAFFOLD}" traefik delete --profile prod || true
        else
            "${CICD_SKAFFOLD}" traefik delete --profile dev  || true
        fi

        "${CICD_SKAFFOLD}" traefik run \
            --profile "${SKAFFOLD_PROFILE}" \
            "${THIRD_PARTY_SKAFFOLD_ARGS[@]}"
    )
}

install_keda(){
    (
        cd "${KEDA_DIR}"

        # Remove the release for the profile we are *not* deploying: `up` and
        # `up -d` each install their own KEDA operator (keda/skaffold.yaml
        # renames the release in the dev profile), and two of them in one
        # cluster fight over the same ScaledObjects.
        #
        # The release we *are* deploying needs no delete: `helm upgrade
        # --install` replaces it in place, where a delete would cost an operator
        # restart on every bring-up.
        #
        # Housekeeping rather than safety -- keda/values.yaml is what keeps an
        # uninstall from taking the CRDs, and every ScaledObject, with it.
        if [[ "${SKAFFOLD_PROFILE}" = "dev" ]]; then
            "${CICD_SKAFFOLD}" keda delete --profile prod || true
        else
            "${CICD_SKAFFOLD}" keda delete --profile dev || true
        fi

        "${CICD_SKAFFOLD}" keda run \
            --profile "${SKAFFOLD_PROFILE}" \
            "${THIRD_PARTY_SKAFFOLD_ARGS[@]}"

        # Wait for the CRD the main deploy applies its ScaledObjects into.
        # Named rather than `crd --all`, which asserts nothing about this one:
        # the Traefik and Calico CRDs in the cluster satisfy a blanket wait on
        # their own, and install_traefik is adding more of them in parallel with
        # this.
        kubectl wait \
            --for condition=established \
                crd/scaledobjects.keda.sh
    )
}

install_third_party(){
    local pids=()

    install_traefik &
    pids+=($!)

    if [[ "${SCALING}" = true ]]; then
        install_keda &
        pids+=($!)
    fi

    wait_all "${pids[@]}"
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

        sudo rm \
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
    # Note that `minikube tunnel` needs the system `ssh` client: with the docker
    # driver it forwards each service port over a connection into the node
    # rather than installing a route. A caller whose PATH has no `ssh` gets a
    # tunnel that starts, logs "error starting ssh tunnel" and binds nothing.
    #
    # The NixOS appliance deliberately does not use this flag for that reason,
    # among others -- it publishes Loom with a DNAT rule instead. See
    # `loom-expose` in nixos/network.nix and Documentation/appliance.md.
    #
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
        --preserve-env=HOME,MINIKUBE_HOME \
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
    # The target platform comes from SKAFFOLD_PLATFORM, exported by
    # set_docker_platform() and read by skaffold itself.
    skaffold "${SKAFFOLD_COMMAND}" \
        --profile "${SKAFFOLD_PROFILE}" \
        "${SKAFFOLD_ARGS[@]}"
}

#
# Teardown
#

teardown(){
    local pids=()

    "${CICD_SKAFFOLD}" traefik delete \
        --profile "${SKAFFOLD_PROFILE}" &
    pids+=($!)

    "${CICD_SKAFFOLD}" keda delete \
        --profile "${SKAFFOLD_PROFILE}" &
    pids+=($!)

    skaffold delete \
        --profile "${SKAFFOLD_PROFILE}" &
    pids+=($!)

    wait_all "${pids[@]}"

    minikube ssh \
        -- \
        docker \
            system prune \
                --force
}

#
# Atexit Handler
#

atexit(){
    echo "[*] Exiting.."

    if [[ "${SETUP}" = true ]]; then
        return
    fi

    if [[ "${DELETE}" = true || "${DEVELOPMENT}" = true ]]; then
        teardown
    fi
}
trap atexit EXIT

#
# Usage
#

usage(){
    echo "usage: ${0} [<options>]"
    echo "  -h|--help                             show this help"
    echo "  -v|--verbose                          show verbose output"
    echo "  -d|--development                      start in development mode: Provides debugging und live reloading."
    echo "  -i|--integrationtest                  start in integration test mode"
    echo "  -s|--setup                            only setup system, don't start anything"
    echo "  -e|--expose IP                        expose the application to the outside world by binding to IP"
    echo "  -g|--gpus GPUS                        allow access to the GPUs. Possible values: amd, nvidia"
    echo "  -t|--tail                             tail logs after startup"
    echo "  -o|--offline                          run in offline mode"
    echo "  -c|--certificate CERT KEY             install certificate (CERT) with key (KEY)"
    echo "  --minikube-host-cpu-reserve N         reserve N CPU cores on the host (default: ${MINIKUBE_HOST_CPU_RESERVE_CORES})"
    echo "  --minikube-host-mem-reserve-kib KiB   reserve KiB of RAM on the host (default: ${MINIKUBE_HOST_MEM_RESERVE_KIB})"
    echo "  --mount-string PATH                   mount host PATH into minikube; PVC data survives cluster rebuilds"
    echo "  --trusted-ca-bundle PATH              inject CA certificate(s) from PEM bundle PATH as trusted roots into all pods"
    echo "  --archive-enc-key KEY                 use KEY (exactly 32 chars) as the archive encryption master key"
    echo "  --no-resources                        deploy without resource requests or limits (see charts/values-no-resources.yaml)"
    echo "  --disable-ai                          disable AI services: ollama and the indexing steps that call"
    echo "                                        it (see charts/values-disable-ai-services.yaml). No summaries,"
    echo "                                        translation, embeddings, auto-tags or RAG."
    echo "  --scaling                             enable autoscaling (KEDA/HPA) for compute-intensive services (see charts/values-scaling.yaml)"
    echo "  --enable-http                         also serve every ingress over plain http, without the"
    echo "                                        redirect to https (see charts/values-http.yaml). Gives up"
    echo "                                        transport security for the whole stack, Elasticsearch,"
    echo "                                        Grafana, S3 and the Traefik dashboard included. Only for a"
    echo "                                        deployment whose network is already trusted."
    echo "  --resume-if-deployed                  skip the deploy when the cluster already carries this"
    echo "                                        checkout's chart versions. For a host that runs this"
    echo "                                        script at every boot; the cluster itself is still started."
    echo "  --down                                tear down the deployment and exit"
    echo "  --delete                              delete the deployment after startup"
    echo "  --skip-STEP                           skip step STEP"
}

#
# Argument parsing
#

while [[ $# -gt 0 ]]; do
    case "${1}" in
        -h|--help)
            usage
            trap - EXIT
            exit 0
        ;;
        -d|--development)
            DEVELOPMENT=true
            # Probe relaxation rides on this flag rather than on values-development.yaml, which
            # --integrationtest also loads: integration tests must keep production probe behaviour.
            UP_FLAG_VALUES+=("${DEBUG_PROBES_VALUES_FILE}")
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
            case "${GPUS}" in
                amd)
                    UP_FLAG_VALUES+=("${AMD_GPU_VALUES_FILE}")
                ;;
                nvidia)
                    UP_FLAG_VALUES+=("${NVIDIA_GPU_VALUES_FILE}")
                ;;
                *)
                    die_usage "Invalid GPU type '${GPUS}'. Valid options: amd, nvidia"
                ;;
            esac
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
        --minikube-host-cpu-reserve)
            shift
            MINIKUBE_HOST_CPU_RESERVE_CORES="${1?Missing reserve cores value (e.g. 0.5)}"
            shift
        ;;
        --minikube-host-mem-reserve-kib)
            shift
            MINIKUBE_HOST_MEM_RESERVE_KIB="${1?Missing reserve memory KiB value (e.g. 512000)}"
            shift
        ;;
        --mount-string)
            shift
            MINIKUBE_MOUNT_STRING="${1?Missing host path for --mount-string (e.g. /mnt/loom-data)}"
            shift
        ;;
        --trusted-ca-bundle)
            shift
            TRUSTED_CA_BUNDLE="${1?Missing path to CA bundle PEM file for --trusted-ca-bundle}"
            shift
        ;;
        --archive-enc-key)
            shift
            ARCHIVE_ENC_KEY="${1?Missing key value for --archive-enc-key}"
            if [[ "${#ARCHIVE_ENC_KEY}" -ne 32 ]]; then
                die_usage "--archive-enc-key must be exactly 32 characters"
            fi
            shift
        ;;
        --no-resources)
            NO_RESOURCES=true
            UP_FLAG_VALUES+=("${NO_RESOURCES_VALUES_FILE}")
            shift
        ;;
        --disable-ai)
            UP_FLAG_VALUES+=("${DISABLE_AI_VALUES_FILE}")
            shift
        ;;
        --scaling)
            SCALING=true
            UP_FLAG_VALUES+=("${SCALING_VALUES_FILE}")
            shift
        ;;
        --enable-http)
            ENABLE_HTTP=true
            UP_FLAG_VALUES+=("${HTTP_VALUES_FILE}")
            shift
        ;;
        --resume-if-deployed)
            RESUME_IF_DEPLOYED=true
            shift
        ;;
        --down)
            DOWN=true
            shift
        ;;
        --delete)
            DELETE=true
            shift
        ;;
        --skip-*)
            skip_step="${1#--skip-}"
            # shellcheck disable=SC2310
            if ! is_known_step "${skip_step}"; then
                echo >&2 "[!] Error: unknown step '${skip_step}' for --skip"
                echo >&2 "[!] Valid steps:"
                printf >&2 '[!]   %s\n' "${ALL_STEPS[@]}"
                trap - EXIT
                exit 1
            fi
            SKIP+=("${skip_step}")
            shift
        ;;
        *)
            # No catch-all passthrough: an unrecognised argument is a typo, and a
            # typo on a negating flag (--no-resource for --no-resources) would
            # otherwise deploy the very thing it was meant to switch off.
            die_usage "unknown argument '${1}'"
        ;;
    esac
done

#
# Main
#

if [[ "${VERBOSE}" = true ]]; then
    set -x
fi

if [[ "${DOWN}" = true ]]; then
    set_skaffold_profile
    trap - EXIT
    teardown
    exit 0
fi

# assemble STEPS
STEPS=()
STEPS+=(
    "${STEPS_SETUP_SYSTEM[@]}"
    "${STEPS_SETUP_CLUSTER[@]}"
)
# Any step appended below must also be listed in STEPS_CONDITIONAL, which is what
# --skip-STEP validates against.

if [[ "${EXPOSE}" = true ]]; then
    STEPS+=(expose_minikube)
fi

STEPS+=(run_skaffold)

if [[ "${SETUP}" = true ]]; then
    STEPS=("${STEPS_SETUP_SYSTEM[@]}")
fi

# execute steps
for step in "${STEPS[@]}"; do
    # shellcheck disable=SC2310
    if is_skipped "${step}"; then
        echo "[*] Skipping: ${step}"
        continue
    fi
    echo "[*] Running: ${step}"
    "${step}"
done
