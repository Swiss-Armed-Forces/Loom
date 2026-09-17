#!/usr/bin/env bash
# Builds, and optionally flashes, a Loom appliance USB installer image.
set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CONTEXT_DIR=$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)

# nixpkgs comes from devenv's `inputs.nixpkgs-stable`, exported by the
# build-appliance-image devenv script. That keeps devenv.lock the single
# nixpkgs pin in this repository.
NIXPKGS="${LOOM_NIXPKGS:-}"

OUTPUT_DIR="${CONTEXT_DIR}/.appliance-build"
NIX_SYSTEM="aarch64-linux"
MINIKUBE_IP="192.168.49.2"
LOOM_INTERFACE="eth0"

# 4096 bytes of /dev/urandom, matching boot.initrd.luks.devices.keyFileSize.
KEY_BYTES=4096
KEY_PARTLABEL="loom-key"

TAG=""
SUBNET=""
FLASH_DEVICE=""
KEY_BACKUP=""
ENABLE_GPU=false
ASSUME_YES=false
ALLOW_CROSS=false
VERBOSE=false
SKIP=()

WORK_DIR=""
KEY_DIR=""

# variables defined in vars.sh, here for shellcheck:
LOOM_HOSTS_FQDN=()

STEPS=(
    validate_environment
    resolve_tag
    resolve_subnet
    prepare_workdir
    prepare_repo
    verify_repo
    generate_loom_hosts
    build_image
    report
)

# Appended in Main when --flash is given.
FLASH_STEPS=(
    confirm_flash
    generate_luks_key
    flash_image
    write_key_partition
    verify_flash
    backup_luks_key
)

#
# Helpers
#

check_command(){
    if ! command -v "${1}" > /dev/null; then
        echo >&2 "[!] Error: required command not found: ${1}"
        exit 1
    fi
}

#
# Steps
#

validate_environment(){
    local command host_arch free_gb

    for command in git git-lfs nix-build jq lsblk sgdisk dd sync udevadm partprobe sudo head cmp install file; do
        check_command "${command}"
    done

    if [[ -z "${NIXPKGS}" ]]; then
        echo >&2 "[!] Error: LOOM_NIXPKGS is not set."
        echo >&2 "    Run this through devenv: 'build-appliance-image', not the script directly."
        exit 1
    fi
    if [[ ! -e "${NIXPKGS}/nixos/lib/eval-config.nix" ]]; then
        echo >&2 "[!] Error: '${NIXPKGS}' does not look like a nixpkgs checkout."
        exit 1
    fi

    # The appliance is aarch64 and cross-building a NixOS closure through
    # emulation takes hours, so refuse by default rather than appear to hang.
    host_arch="$(uname -m)"
    if [[ "${ALLOW_CROSS}" != true && "${NIX_SYSTEM}" == "${host_arch}-linux" ]]; then
        : # building natively
    elif [[ "${ALLOW_CROSS}" != true ]]; then
        echo >&2 "[!] Error: building ${NIX_SYSTEM} on ${host_arch}."
        echo >&2 "    Run this on a DGX Spark, or pass --allow-cross if you know what you are doing."
        exit 1
    fi

    # git-lfs payloads must already be local: the appliance build has no network
    # budget for fetching them, and up.sh:412 fails without them on the box.
    local lfs_dir
    lfs_dir="$(git -C "${CONTEXT_DIR}" rev-parse --path-format=absolute --git-common-dir)/lfs/objects"
    if [[ ! -d "${lfs_dir}" ]]; then
        echo >&2 "[!] Error: no git-lfs objects in this checkout."
        echo >&2 "    Run: git lfs fetch --all"
        exit 1
    fi

    install --directory "${OUTPUT_DIR}"
    free_gb="$(df --output=avail --block-size=1G "${OUTPUT_DIR}" | tail --lines=1 | tr --delete ' ')"
    if [[ "${free_gb}" -lt 20 ]]; then
        echo >&2 "[!] Error: only ${free_gb} GB free at ${OUTPUT_DIR}; the image build needs about 20 GB."
        exit 1
    fi
}

resolve_tag(){
    local answer

    if [[ -n "${TAG}" ]]; then
        if ! git -C "${CONTEXT_DIR}" rev-parse --verify --quiet "refs/tags/${TAG}" > /dev/null; then
            echo >&2 "[!] Error: no such tag: ${TAG}"
            exit 1
        fi
        return
    fi

    # Note: NOT `git describe`, which returns the nearest *ancestor* tag and so
    # happily picks an ancient release when main has moved on.
    TAG="$(git -C "${CONTEXT_DIR}" tag --list --sort=-v:refname | head --lines=1)"
    if [[ -z "${TAG}" ]]; then
        echo >&2 "[!] Error: this repository has no tags."
        echo >&2 "    The appliance runs Loom in offline mode, which requires a tagged checkout (up.sh:236)."
        exit 1
    fi

    echo "[*] Newest tag: ${TAG}"
    if [[ "${ASSUME_YES}" != true ]]; then
        read -r -p "[?] Build the appliance from ${TAG}? [y/N] " answer
        if [[ "${answer}" != "y" && "${answer}" != "Y" ]]; then
            echo >&2 "[!] Aborted. Pass --tag to choose a different one."
            exit 1
        fi
    fi
}

resolve_subnet(){
    local a b

    if [[ -n "${SUBNET}" ]]; then
        return
    fi

    # Randomised so two boxes on one wire cannot collide, and so a visitor's own
    # 10.0.0.0/24 or 192.168.1.0/24 does not either. 0 and 255 are avoided in
    # both octets to keep the range unremarkable.
    a="$(( (RANDOM % 254) + 1 ))"
    b="$(( (RANDOM % 254) + 1 ))"
    SUBNET="10.${a}.${b}"
}

prepare_workdir(){
    local uid
    uid="$(id -u)"
    WORK_DIR="$(mktemp --directory)"
    # The LUKS key must never touch a disk. /run/user is a tmpfs.
    KEY_DIR="$(mktemp --directory --tmpdir="/run/user/${uid}")"
    chmod 0700 "${KEY_DIR}"
}

# Prepared with real git rather than a Nix fetcher, because up.sh's offline mode
# runs `git describe --exact-match --tags HEAD` (up.sh:236) inside the embedded
# checkout, and every Nix fetcher either drops `.git` or leaves git-lfs payloads
# as pointer files.
prepare_repo(){
    local repo="${WORK_DIR}/loom" lfs_dir

    # --no-local forces a real pack transfer. A plain local clone writes
    # .git/objects/info/alternates pointing at this machine, which does not
    # exist on the appliance -- producing a silently corrupt repository.
    git clone --no-hardlinks --no-local --quiet "${CONTEXT_DIR}" "${repo}"
    git -C "${repo}" checkout --force --quiet "tags/${TAG}"

    # Must happen BEFORE `lfs checkout`: without filter.lfs.* configured, the
    # working tree gets real content while the index still holds pointer blobs,
    # so all 138 LFS files show as modified forever.
    git -C "${repo}" lfs install --local

    # Copy this checkout's object cache rather than `git lfs pull`, which needs
    # a reachable remote. Offline, deterministic, and only about 30 MB.
    lfs_dir="$(git -C "${CONTEXT_DIR}" rev-parse --path-format=absolute --git-common-dir)/lfs"
    cp --archive "${lfs_dir}" "${repo}/.git/"
    git -C "${repo}" lfs checkout

    # Nothing on the appliance should point back at a build machine.
    git -C "${repo}" remote remove origin
    git -C "${repo}" reflog expire --expire=now --all
    git -C "${repo}" gc --prune=now --quiet
}

verify_repo(){
    local repo="${WORK_DIR}/loom" described status pointers

    described="$(git -C "${repo}" describe --exact-match --tags HEAD)"
    if [[ "${described}" != "${TAG}" ]]; then
        echo >&2 "[!] Error: embedded checkout describes as '${described}', expected '${TAG}'."
        exit 1
    fi

    if [[ ! -d "${repo}/.git/lfs/objects" ]]; then
        echo >&2 "[!] Error: embedded checkout has no git-lfs objects; up.sh:412 would fail on the box."
        exit 1
    fi

    if [[ -e "${repo}/.git/objects/info/alternates" ]]; then
        echo >&2 "[!] Error: embedded checkout has an alternates file pointing outside itself."
        exit 1
    fi

    status="$(git -C "${repo}" status --porcelain)"
    if [[ -n "${status}" ]]; then
        echo >&2 "[!] Error: embedded checkout is not clean:"
        echo >&2 "${status}"
        exit 1
    fi

    # Any LFS file still listed with '-' is a pointer, not real content.
    pointers="$(git -C "${repo}" lfs ls-files | grep --invert-match ' \* ' || true)"
    if [[ -n "${pointers}" ]]; then
        echo >&2 "[!] Error: git-lfs payloads were not materialised:"
        echo >&2 "${pointers}"
        exit 1
    fi

    # Canary: this chart is LFS-tracked and cicd/skaffold untars it at deploy
    # time, so a pointer file here means bring-up fails on the box.
    if ! file "${repo}/traefik/traefik-39.0.9.tgz" | grep --quiet gzip; then
        echo >&2 "[!] Error: traefik chart is not a real gzip; git-lfs materialisation is broken."
        exit 1
    fi
}

# Sourced from the embedded checkout rather than this one, so the host list
# always matches the tag being shipped. vars.sh stays the single source of truth.
generate_loom_hosts(){
    # shellcheck disable=SC1091
    # shellcheck source=../vars.sh
    source "${WORK_DIR}/loom/vars.sh"
    printf '%s\n' "${LOOM_HOSTS_FQDN[@]}" | jq --raw-input . | jq --slurp --compact-output . \
        > "${WORK_DIR}/loom-hosts.json"
}

build_image(){
    local hosts_json
    hosts_json="$(cat "${WORK_DIR}/loom-hosts.json")"

    echo "[*] Building the ${NIX_SYSTEM} appliance image for ${TAG} on ${SUBNET}.0/24"
    nix-build "${CONTEXT_DIR}/nixos" \
        --attr installerImage \
        --arg nixpkgs "${NIXPKGS}" \
        --argstr system "${NIX_SYSTEM}" \
        --arg repoSrc "${WORK_DIR}/loom" \
        --argstr tag "${TAG}" \
        --argstr loomHostsJson "${hosts_json}" \
        --argstr minikubeIp "${MINIKUBE_IP}" \
        --argstr loomSubnet "${SUBNET}" \
        --argstr loomInterface "${LOOM_INTERFACE}" \
        --arg enableGpu "${ENABLE_GPU}" \
        --out-link "${OUTPUT_DIR}/appliance-image"
}

image_file(){
    find "${OUTPUT_DIR}/appliance-image" -name '*.raw' -type f | head --lines=1
}

confirm_flash(){
    local image size answer mounted root_source

    if [[ ! -b "${FLASH_DEVICE}" ]]; then
        echo >&2 "[!] Error: not a block device: ${FLASH_DEVICE}"
        exit 1
    fi

    root_source="$(findmnt --noheadings --output SOURCE --target / | head --lines=1)"
    if [[ "${root_source}" == "${FLASH_DEVICE}"* ]]; then
        echo >&2 "[!] Error: ${FLASH_DEVICE} backs this machine's root filesystem."
        exit 1
    fi

    mounted="$(lsblk --noheadings --raw --output MOUNTPOINTS "${FLASH_DEVICE}" | tr --delete ' \n')"
    if [[ -n "${mounted}" ]]; then
        echo >&2 "[!] Error: ${FLASH_DEVICE} has mounted partitions. Unmount them first."
        exit 1
    fi

    image="$(image_file)"
    size="$(stat --format=%s "${image}")"

    echo
    echo "[!] This will DESTROY ALL DATA on ${FLASH_DEVICE}:"
    lsblk --nodeps --output NAME,SIZE,MODEL,SERIAL,TRAN "${FLASH_DEVICE}"
    echo "[!] Writing $(( size / 1024 / 1024 )) MiB from $(basename "${image}")"
    echo

    if [[ "${ASSUME_YES}" != true ]]; then
        # The device name rather than 'yes', so this cannot be confirmed by
        # muscle memory on the wrong device.
        read -r -p "[?] Type '$(basename "${FLASH_DEVICE}")' to confirm: " answer
        if [[ "${answer}" != "$(basename "${FLASH_DEVICE}")" ]]; then
            echo >&2 "[!] Aborted."
            exit 1
        fi
    fi
}

generate_luks_key(){
    ( umask 077; head --bytes="${KEY_BYTES}" /dev/urandom > "${KEY_DIR}/luks.key" )
}

flash_image(){
    local image
    image="$(image_file)"

    echo "[*] Writing ${image} to ${FLASH_DEVICE}"
    sudo dd if="${image}" of="${FLASH_DEVICE}" bs=4M status=progress conv=fsync oflag=direct
    sync
    sudo partprobe "${FLASH_DEVICE}"
    sudo udevadm settle
}

# Resolved on the flashed device rather than through /dev/disk/by-partlabel, so
# a second Loom stick in another port cannot be written to by mistake.
key_partition(){
    lsblk --noheadings --raw --paths --output PATH,PARTLABEL "${FLASH_DEVICE}" \
        | awk --assign label="${KEY_PARTLABEL}" '$2 == label { print $1 }' \
        | head --lines=1
}

write_key_partition(){
    local key_part
    key_part="$(key_partition)"

    if [[ -z "${key_part}" ]]; then
        echo >&2 "[!] Error: no '${KEY_PARTLABEL}' partition on ${FLASH_DEVICE} after flashing."
        exit 1
    fi

    echo "[*] Writing the LUKS key to ${key_part}"
    sudo dd if="${KEY_DIR}/luks.key" of="${key_part}" bs="${KEY_BYTES}" count=1 conv=fsync status=none
    sync
}

verify_flash(){
    local key_part label

    for label in loom-live-esp loom-live-store "${KEY_PARTLABEL}"; do
        if ! lsblk --noheadings --raw --output PARTLABEL "${FLASH_DEVICE}" | grep --quiet --line-regexp "${label}"; then
            echo >&2 "[!] Error: partition '${label}' is missing from ${FLASH_DEVICE}."
            exit 1
        fi
    done

    # Read the key back. A stick whose key partition did not take would install
    # fine and then never boot again, which is a miserable thing to discover in
    # the field.
    key_part="$(key_partition)"
    sudo dd if="${key_part}" of="${KEY_DIR}/readback.key" bs="${KEY_BYTES}" count=1 status=none
    if ! cmp --silent "${KEY_DIR}/luks.key" "${KEY_DIR}/readback.key"; then
        echo >&2 "[!] Error: the key read back from ${key_part} does not match what was written."
        exit 1
    fi
    echo "[*] Key verified on ${key_part}"
}

backup_luks_key(){
    if [[ -z "${KEY_BACKUP}" ]]; then
        echo
        echo "[!] The LUKS key exists on exactly one physical object: this USB stick."
        echo "[!] If it is lost or damaged, the box's data is unrecoverable unless"
        echo "[!] someone wrote down the recovery passphrase shown after installation."
        echo "[!] Pass --key-backup FILE to keep a copy."
        return
    fi

    # Never inside the repository, where `git add -A` could pick it up.
    local resolved
    resolved="$(readlink --canonicalize "${KEY_BACKUP}")"
    if [[ "${resolved}" == "${CONTEXT_DIR}"/* ]]; then
        echo >&2 "[!] Error: refusing to write the LUKS key inside the repository."
        exit 1
    fi

    install --mode=0400 "${KEY_DIR}/luks.key" "${KEY_BACKUP}"
    echo "[*] LUKS key backed up to ${KEY_BACKUP} (mode 0400). Store it away from the box."
}

report(){
    local image checksum

    image="$(image_file)"
    checksum="$(sha256sum "${KEY_DIR}/luks.key" 2>/dev/null | cut --delimiter=' ' --fields=1 || echo 'not generated')"

    echo
    echo "[*] Appliance image ready"
    echo "      image     : ${image}"
    echo "      loom tag  : ${TAG}"
    echo "      system    : ${NIX_SYSTEM}"
    echo "      subnet    : ${SUBNET}.0/24 (box at ${SUBNET}.1, DHCP ${SUBNET}.100-200)"
    echo "      interface : ${LOOM_INTERFACE}"
    echo "      gpu       : ${ENABLE_GPU}"
    if [[ -n "${FLASH_DEVICE}" ]]; then
        echo "      flashed to: ${FLASH_DEVICE}"
        echo "      key sha256: ${checksum}"
        echo
        echo "[*] Boot the box from this stick and choose 'Install'."
        echo "[*] The stick must stay plugged in afterwards: it holds the disk key."
    else
        echo
        echo "[*] Flash it with: build-appliance-image --flash /dev/sdX"
    fi
}

#
# Usage
#

usage(){
    echo "usage: $0 [<options>]"
    echo "  -h|--help                     show this help"
    echo "  -v|--verbose                  show verbose output"
    echo "  -t|--tag TAG                  Loom tag to embed (default: the newest tag)"
    echo "  -o|--output OUTPUT_DIR        where to place the image (default: .appliance-build)"
    echo "  -f|--flash DEVICE             flash to DEVICE, destroying all data on it"
    echo "  -k|--key-backup FILE          also write the generated LUKS key to FILE"
    echo "  -g|--gpu                      (not implemented yet; the appliance is CPU-only)"
    echo "  -s|--system SYSTEM            nix system to build (default: ${NIX_SYSTEM})"
    echo "  -i|--interface INTERFACE      appliance network interface (default: ${LOOM_INTERFACE})"
    echo "  --subnet A.B.C                appliance subnet prefix (default: random 10.x.y)"
    echo "  --minikube-ip MINIKUBE_IP     address '*.loom' resolves to on the box (default: ${MINIKUBE_IP})"
    echo "  --nixpkgs NIXPKGS             nixpkgs source (default: \${LOOM_NIXPKGS} from devenv)"
    echo "  -y|--yes                      do not ask for confirmation"
    echo "  --allow-cross                 allow building for a system other than the host"
    echo "  --skip-STEP                   skip step STEP"
}

#
# Atexit handler
#

atexit(){
    if [[ -n "${KEY_DIR}" && -d "${KEY_DIR}" ]]; then
        rm --recursive --force "${KEY_DIR}"
    fi
    if [[ -n "${WORK_DIR}" && -d "${WORK_DIR}" ]]; then
        rm --recursive --force "${WORK_DIR}"
    fi
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
        -t|--tag)
            shift
            TAG="${1?Missing TAG}"
            shift
        ;;
        -o|--output)
            shift
            OUTPUT_DIR="${1?Missing OUTPUT_DIR}"
            shift
        ;;
        -f|--flash)
            shift
            FLASH_DEVICE="${1?Missing DEVICE}"
            shift
        ;;
        -k|--key-backup)
            shift
            KEY_BACKUP="${1?Missing FILE}"
            shift
        ;;
        -g|--gpu)
            # The NVIDIA driver module is not written yet: mainline Linux is
            # reported to lose the GPU and the ConnectX-7 NIC on a DGX Spark,
            # so this needs validating on real hardware first. Refusing beats
            # producing a box that asks minikube for a GPU it cannot see.
            echo >&2 "[!] Error: --gpu is not implemented yet; the appliance ships CPU-only."
            echo >&2 "    See the 'GPU support' section of Documentation/appliance.md."
            exit 1
        ;;
        -s|--system)
            shift
            NIX_SYSTEM="${1?Missing SYSTEM}"
            shift
        ;;
        -i|--interface)
            shift
            LOOM_INTERFACE="${1?Missing INTERFACE}"
            shift
        ;;
        --subnet)
            shift
            SUBNET="${1?Missing SUBNET}"
            shift
        ;;
        --minikube-ip)
            shift
            MINIKUBE_IP="${1?Missing MINIKUBE_IP}"
            shift
        ;;
        --nixpkgs)
            shift
            NIXPKGS="${1?Missing NIXPKGS}"
            shift
        ;;
        -y|--yes)
            ASSUME_YES=true
            shift
        ;;
        --allow-cross)
            ALLOW_CROSS=true
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

if [[ -n "${FLASH_DEVICE}" ]]; then
    # report last, so it can describe what was flashed.
    STEPS=( "${STEPS[@]:0:${#STEPS[@]}-1}" "${FLASH_STEPS[@]}" report )
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
