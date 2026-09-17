#!/usr/bin/env bash
#
# Destroys the data on the box's internal disks.
#
# Layered, cheapest-and-most-effective first. The data is LUKS-encrypted, so
# destroying the key material IS the wipe; everything after layer 1 is defence
# in depth. Each layer is allowed to fail -- an NVMe that refuses `nvme format`
# has still had its keyslots erased.
#
# A full overwrite is deliberately not the default: on a wear-levelling NVMe it
# takes hours and still cannot reach retired or over-provisioned blocks, so it
# is both slower and weaker than a controller-level sanitize.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
# shellcheck disable=SC1091
source "${LOOM_INSTALLER_LIB:?LOOM_INSTALLER_LIB is not set}/common.sh"

main() {
    local boot eligible targets=() disk

    if [[ "${EUID}" -ne 0 ]]; then
        die "The wipe must run as root."
    fi

    boot="$(boot_disk)"
    if [[ -z "${boot}" ]]; then
        die "Could not identify the boot medium. Is a second Loom stick plugged in?"
    fi
    eligible="$(target_disks)"
    if [[ -z "${eligible}" ]]; then
        die "No eligible internal NVMe found. Nothing to wipe."
    fi
    mapfile -t targets <<<"${eligible}"

    confirm_destructive "ERASE ALL DATA" "${boot}" "${targets[@]}"

    release_holders
    for disk in "${targets[@]}"; do
        wipe_disk "${disk}"
    done

    echo
    log "Wipe complete. The encryption keys are gone; the data is unrecoverable."
}

# Anything still holding a target device would make the wipe fail halfway.
release_holders() {
    local mapping
    swapoff --all || true
    for mapping in /dev/mapper/*; do
        [[ -b "${mapping}" ]] || continue
        [[ "$(basename "${mapping}")" == "control" ]] && continue
        cryptsetup close "$(basename "${mapping}")" 2>/dev/null || true
    done
    umount --recursive /mnt 2>/dev/null || true
}

wipe_disk() {
    local disk="${1}" part description
    description="$(disk_description "${disk}")"
    log "Wiping ${description}"

    # Layer 1: cryptographic erase. Sub-second, irreversible, and on its own
    # enough to make the contents unrecoverable.
    for part in "${disk}"p*; do
        [[ -b "${part}" ]] || continue
        if cryptsetup isLuks "${part}" 2>/dev/null; then
            log "  luksErase ${part}"
            cryptsetup luksErase --batch-mode "${part}" || err "  luksErase failed on ${part}"
        fi
    done

    # Layer 2: flatten the headers themselves, including any keyslot cryptsetup
    # did not know about and the header backup area.
    for part in "${disk}"p*; do
        [[ -b "${part}" ]] || continue
        dd if=/dev/urandom of="${part}" bs=1M count=32 oflag=direct conv=fsync status=none 2>/dev/null || true
        wipefs --all "${part}" >/dev/null 2>&1 || true
    done

    # Layer 3: partition table.
    sgdisk --zap-all "${disk}" >/dev/null 2>&1 || true
    wipefs --all "${disk}" >/dev/null 2>&1 || true

    # Layer 4: discard every block. -f drops the exclusive open that util-linux
    # takes by default.
    log "  blkdiscard"
    blkdiscard -f "${disk}" || err "  blkdiscard unsupported or refused; continuing"

    # Layer 5: ask the controller to erase. --ses=1 is a user-data erase,
    # --ses=2 a cryptographic one; not every drive implements either.
    log "  nvme format"
    nvme format "${disk}" --ses=1 --force >/dev/null 2>&1 ||
        nvme format "${disk}" --ses=2 --force >/dev/null 2>&1 ||
        err "  nvme format unsupported; layers 1-4 already applied"

    partprobe "${disk}" 2>/dev/null || true
}

main "${@}"
