#!/usr/bin/env bash
#
# This script will create an loom transfer file, a self extracting archive.
# This archive can be used to easily install loom instance on an isolated machine.
#
set -euo pipefail

NOW="$(date --utc "+%Y-%m-%d-%H-%M-%S")"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
TOPLEVEL=$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)
CHARTS_DIR="${TOPLEVEL}/charts"

VERSION="$(git -C "${TOPLEVEL}" describe --tags)"
APP_VERSION="$(helm show all "${CHARTS_DIR}" | yq --raw-output '.appVersion | select( . != null)')"

TRANSFER_NAME="loom-${VERSION}-${NOW}"

TRANSFER_FILENAME="${TRANSFER_NAME}.sh"
DIND_CONTAINER_NAME="${TRANSFER_NAME}"
TRANSFER_DIR="${TRANSFER_NAME}"

DOCKER_VOLUME="${TRANSFER_DIR}/docker"
CODE_VOLUME="${TRANSFER_DIR}/code"
CODE_OVERLAY_VOLUME="${TRANSFER_DIR}/code-overlay"

# Environment
SLEEP_TIME="${SLEEP_TIME:-0}"

SKIP=()
VERBOSE=false

STEPS=(
    make_transfer_dir
    clone_code
    build_stack
    commit_dind_container
    export_dind_container
    write_transfer_file
    append_data_to_transfer_file
    make_executable
)

#
# Utils
#

get_transfer_dir_size(){
    sudo \
        du -scb "${TRANSFER_DIR}" \
    | tail -n1 \
    | awk '{print $1}'
}

#
# Steps
#

make_transfer_dir(){
    mkdir \
        --parent \
        "${TRANSFER_DIR}"
}


clone_code(){
    git \
        clone \
            --depth 1 \
            "file://${TOPLEVEL}" \
            "${CODE_VOLUME}"
}

build_stack(){
    nix-dind \
        --verbose \
        --context-dir "${CODE_VOLUME}" \
        --code-overlay-volume "${CODE_OVERLAY_VOLUME}" \
        --container-name "${DIND_CONTAINER_NAME}" \
        --docker-volume "${DOCKER_VOLUME}" \
        --run \
            "cd /code && \
            devenv --verbose shell -- up --profile prod --setup && \
            devenv --verbose shell -- build --profile prod --tag '${APP_VERSION}'"
}

commit_dind_container(){
    docker container commit \
        --change "CMD [\"/bin/bash\"]" \
        "${DIND_CONTAINER_NAME}" \
        "${DIND_CONTAINER_NAME}"
}

export_dind_container(){
    docker image save \
        --output "${TRANSFER_DIR}/${DIND_CONTAINER_NAME}" \
        "${DIND_CONTAINER_NAME}"
}

write_transfer_file(){
    local transfer_dir_size
    transfer_dir_size="$(get_transfer_dir_size)"

    cat > "${TRANSFER_FILENAME}" <<EOF
#!/usr/bin/env bash
set -eu

check_command(){
    local command
    command="\$1"
    shift

    if ! command -v "\${command}" &> /dev/null; then
        >&2 echo "[!] Error: Command '\${command}' could not be found"
        exit 1
    fi
}

sed_unpack(){
    sed '0,/^#EOF#$/d' "\$0"
}

get_absolute_path(){
    local path
    path="\${1}" && shift

    readlink -m "\${path}"
}

transfer_dir_exists(){
    [[ -d "${TRANSFER_DIR}" ]]
}

unpack_loom(){
    sed_unpack \
        | gunzip \
        | pv \
            --size "${transfer_dir_size}" \
        | sudo \
            tar \
                --extract
}

docker_image_exists(){
    docker image inspect \
        "${DIND_CONTAINER_NAME}" \
    &> /dev/null
}

import_docker_image(){
    docker image load < "${TRANSFER_DIR}/${DIND_CONTAINER_NAME}"
}

#
# Main
#

echo "[*] Checking system setup"
# for this script:
check_command docker
check_command sed
check_command pv
check_command gunzip
check_command sudo
check_command tar

if ! transfer_dir_exists; then
    echo "[*] Unpacking: '${TRANSFER_DIR}'"
    unpack_loom
fi

if ! docker_image_exists; then
    echo "[*] Importing docker image: '${DIND_CONTAINER_NAME}'"
    import_docker_image
fi

echo "[*] Starting '${DIND_CONTAINER_NAME}'"
docker run \
    --rm \
    --privileged \
    --interactive \
    --tty \
    --name "${DIND_CONTAINER_NAME}" \
    --volume "\$(get_absolute_path '${DOCKER_VOLUME}'):/var/lib/docker:rw" \
    --volume "\$(get_absolute_path '${CODE_VOLUME}'):/code-ro:ro" \
    --volume "\$(get_absolute_path '${CODE_OVERLAY_VOLUME}'):/code-overlay:rw" \
    "${DIND_CONTAINER_NAME}"

exit 0
#EOF#
EOF
}

append_data_to_transfer_file(){
    local transfer_dir_size
    transfer_dir_size="$(get_transfer_dir_size)"

    sudo \
        tar \
            --create \
            --to-stdout \
                "${TRANSFER_DIR}" \
    | pv \
        --size "${transfer_dir_size}" \
    | gzip \
    >> "${TRANSFER_FILENAME}"
}

make_executable(){
    chmod +x "${TRANSFER_FILENAME}"
}

#
# Usage
#

usage(){
    cat <<EOF
usage: $0 [OPTION]

where OPTION:
    -h|--help       print this help
    -v|--verbose    make script verbose
    --skip-STEP     skips step specified with STEP
EOF
}

#
# Atexit handler
#

atexit(){
    echo "[*] Exiting.."

    # sudo: because of the docker volume
    sudo rm \
        --recursive \
        --force \
        "${TRANSFER_DIR}"

    echo "[*] sleeping for: ${SLEEP_TIME}"
    sleep "${SLEEP_TIME}"
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

# execute steps
for step in "${STEPS[@]}"; do
    if [[ "${SKIP[*]}" == *"--skip-${step}"* ]]; then
        echo "[*] Skipping: ${step}"
        continue
    fi
    echo "[*] Running: ${step}"
    "${step}" "${@}"
done