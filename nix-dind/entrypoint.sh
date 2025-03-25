#!/usr/bin/env bash
set -euo pipefail

# Source bashrc
# shellcheck disable=SC1091
# shellcheck source=/etc/bashrc
source /etc/bashrc

# Environment
NIX_USER_NAME="${NIX_USER_NAME:-nix}"
NIX_GROUP_NAME="${NIX_GROUP_NAME:-nix}"
NIX_USER_HOMEDIR="${NIX_USER_HOMEDIR:-/home/nix}"
TAILSCALE_AUTHKEY="${TAILSCALE_AUTHKEY:-}"
CI_JOB_NAME="${CI_JOB_NAME:-unknown-job}"
TAILSCALE_HOSTNAME="gitlab-runner-${CI_JOB_NAME}-${RANDOM}"
TAILSCALE_HOSTNAME_SAFE="$(echo -n "${TAILSCALE_HOSTNAME}" | tr -c '[:alnum:]' '-')"
CODE_DIR="${CODE_DIR:-/code}"
CODE_DIR_RO="${CODE_DIR}-ro"
CODE_OVERLAY_DIR="${CODE_OVERLAY_DIR:-/code-overlay}"


# Path to the service sockets
DOCKER_SOCKET="/var/run/docker.sock"
FORK_PID_PREFIX="/var/run/fork."
NIX_DAEMON_SOCKET="/nix/var/nix/daemon-socket/socket"

WAIT_MAX_RETRIES=60

CMD_SUDO=$(command -v sudo)
CMD_BASH=$(command -v bash)
CMD_TO_RUN=("${@:-${CMD_BASH}}")

#
# Utils
#

# fork a command
fork() {
    exec setsid "${@}" &
    # shellcheck disable=SC2128
    echo "${!}" > "${FORK_PID_PREFIX}${RANDOM}${RANDOM}${RANDOM}"
}

is_docker_ready() {
    [[ -S "${DOCKER_SOCKET}" ]] && [[ -r "${DOCKER_SOCKET}" ]] && docker stats --no-stream &>/dev/null
}

is_nix_daemon_ready() {
    [[ -S "${NIX_DAEMON_SOCKET}" ]] && [[ -r "${NIX_DAEMON_SOCKET}" ]] && pgrep -f nix-daemon &>/dev/null
}

is_taiscale_ready() {
    [[ -z "${TAILSCALE_AUTHKEY}" ]] || tailscale status &>/dev/null
}

is_pid_dead(){
    local pid
    pid="${1}" && shift
    [[ ! -d "/sys/${pid}" ]]
}

wait_for(){
    local check_function
    check_function=( "${@}" )

    # Initialize retry counter
    local retry_count
    retry_count=0

    # Loop until check_function is ready or max retries is reached
    while ! "${check_function[@]}"; do
        if [[ "${retry_count}" -ge "${WAIT_MAX_RETRIES}" ]]; then
            echo "${check_function[*]} was not ready after ${WAIT_MAX_RETRIES} seconds."
            exit 1
        fi

        echo "Waiting for ${check_function[*]}... Attempt $((retry_count+1))/${WAIT_MAX_RETRIES}"
        sleep 1
        ((retry_count++)) || true
    done
}

overlay_code_mount(){
    local overlay_dir_upper
    overlay_dir_upper="${CODE_OVERLAY_DIR}/upper"
    local overlay_dir_work
    overlay_dir_work="${CODE_OVERLAY_DIR}/work"
    local overlay_dir_mount
    overlay_dir_mount="${CODE_OVERLAY_DIR}/mount"

    # not a mountpoint: create templfs overlay directory
    if ! mountpoint "${CODE_OVERLAY_DIR}"; then
        mkdir -p "${CODE_OVERLAY_DIR}"
        mount \
            -t tmpfs tmpfs \
            "${CODE_OVERLAY_DIR}"
    fi

    mkdir -p \
        "${CODE_DIR}" \
        "${overlay_dir_upper}" \
        "${overlay_dir_work}" \
        "${overlay_dir_mount}"

    mount \
        -t overlay overlay \
        -o "lowerdir=${CODE_DIR_RO},upperdir=${overlay_dir_upper},workdir=${overlay_dir_work}" \
        "${overlay_dir_mount}"

    bindfs \
        --force-user="${NIX_USER_NAME}" \
        --force-group="${NIX_GROUP_NAME}" \
        "${overlay_dir_mount}" \
        "${CODE_DIR}"
}

#
# Atexit Handler
#

atexit(){
    echo "Stopping all containers"
    docker ps \
        --all \
        --quiet \
    | xargs \
        --no-run-if-empty \
        docker stop

    echo "Killing forked processes"
    local pidfile
    for pidfile in "${FORK_PID_PREFIX}"*; do
        if [[ ! -f "${pidfile}" ]]; then
            continue
        fi
        local pid
        pid="$(cat "${pidfile}")"
        kill "${pid}"
        wait_for is_pid_dead "${pid}"
        rm -f "${pidfile}"
        echo "${pid} killed"
    done
}
trap atexit EXIT

#
# Main
#

# mount code overlay
if [[ -d "${CODE_DIR_RO}" ]]; then
    overlay_code_mount
fi

# start docker
# shellcheck disable=SC2310
if ! is_docker_ready; then
    (
        # dockerd-entrypoint always spawns a tini processes
        # which, if TINI_SUBREAPER is not defined, expects to
        # to be PID=1 and hence failes sometimes
        # (possibly due concurrency issues)
        # This is why we tell tini here to register as child
        # subreaper. Which will make tini reap only processes
        # belonging to its subtree and allows it to run
        # as PID!=1. Note this only works on kernel >= 3.4
        #
        # ref:
        # - https://github.com/krallin/tini
        # - https://man7.org/linux/man-pages/man2/pr_set_child_subreaper.2const.html
        export TINI_SUBREAPER=1
        fork dockerd-entrypoint.sh
    )
fi
wait_for is_docker_ready

# start nix
# shellcheck disable=SC2310
if ! is_nix_daemon_ready; then
    fork nix-daemon --debug --verbose
fi
wait_for is_nix_daemon_ready

# start tailscale
# shellcheck disable=SC2310
if ! is_taiscale_ready; then
    fork tailscaled

    echo "[*]"
    echo "[*]"
    echo "[*] ============================================================"
    echo "[*] Joining tailscale network as: '${TAILSCALE_HOSTNAME_SAFE}'"
    echo "[*] ============================================================"
    echo "[*]"
    echo "[*]"
    # Do not use tailscale dns.
    # We have seen issues like the following:
    # format("dns: resolver: forward: no upstream resolvers set, returning SERVFAIL")
    tailscale up \
        --authkey="${TAILSCALE_AUTHKEY}" \
        --hostname="${TAILSCALE_HOSTNAME_SAFE}" \
        --accept-dns=false \
        --accept-routes
fi
wait_for is_taiscale_ready

# Run command
# Notes:
#   - we use sudo here becuase su - user -c COMMAND
#     does not work properly if COMMAND contains options
#     like -c, -l ... Dont ask me why
#   - we use env -i here to remove env variables
#     setup by sudo
#   - we explicitly set a few environment variables
#     such as HOME, ...
#   - we tell bash to run a login shell (--login)
#     this is so that bash source files in
#     /etc/profile.d/* which then populates the
#     environment for nix usage
echo "Running command: '${CMD_TO_RUN[*]}'"
"${CMD_SUDO}" \
    --user "${NIX_USER_NAME}" \
    --group "${NIX_GROUP_NAME}" \
    env -i \
        HOME="${NIX_USER_HOMEDIR}" \
        "${CMD_BASH}" \
            --login \
            -c "${CMD_TO_RUN[@]}"
