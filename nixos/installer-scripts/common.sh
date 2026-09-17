#!/usr/bin/env bash
# shellcheck disable=SC2034
#
# Shared helpers for the Loom appliance installer.
#
# Sourced by install.sh, wipe.sh and menu.sh; the constants below are consumed
# there rather than here, hence the file-level SC2034 (same as vars.sh).
#
# The device interlock is the most important thing in this file: it is what
# keeps the installer from eating the USB stick it is running from, or a disk
# somebody cares about.

# Partition labels. The stick uses `loom-live-*` and `loom-key`; the internal
# disk uses `loom-esp` and `loom-root-luks`. The prefixes must stay disjoint --
# /dev/disk/by-partlabel is not unique, and with both media attached a shared
# name would resolve to whichever udev linked last.
readonly LOOM_LIVE_ESP_LABEL="loom-live-esp"
readonly LOOM_LIVE_STORE_LABEL="loom-live-store"
readonly LOOM_KEY_LABEL="loom-key"
readonly LOOM_ESP_LABEL="loom-esp"
readonly LOOM_ROOT_LABEL="loom-root-luks"

readonly LOOM_KEY_BYTES=4096
readonly LOOM_MIN_DISK_BYTES=$((250 * 1000 * 1000 * 1000))

log() { echo "[*] ${*}"; }
err() { echo >&2 "[!] ${*}"; }
die() {
    err "${@}"
    exit 1
}

# Parent disk of a partition, e.g. /dev/nvme0n1p1 -> /dev/nvme0n1
parent_of() {
    local part="${1}" parents
    parents="$(lsblk --noheadings --raw --paths --output PKNAME "${part}")"
    printf '%s' "${parents%%$'\n'*}"
}

sysfs_attr() {
    local disk="${1}" attr="${2}" base path value
    base="$(basename "${disk}")"
    path="/sys/block/${base}/device/${attr}"
    value="unknown"
    if [[ -r "${path}" ]]; then
        value="$(cat "${path}")"
    fi
    printf '%s' "${value}"
}

disk_description() {
    local disk="${1}" model serial size
    model="$(sysfs_attr "${disk}" model)"
    serial="$(sysfs_attr "${disk}" serial)"
    size="$(lsblk --nodeps --noheadings --raw --output SIZE "${disk}")"
    printf '%s  %s  SN %s  %s' "${disk}" "${model}" "${serial}" "${size}"
}

# The disk we booted from, resolved from our own partition labels rather than
# guessed. Refuses to answer if they do not all live on one device -- which is
# what happens when a second Loom stick is plugged in.
boot_disk() {
    local label part disks=() sorted unique=()

    for label in "${LOOM_KEY_LABEL}" "${LOOM_LIVE_STORE_LABEL}" "${LOOM_LIVE_ESP_LABEL}"; do
        part="$(readlink --canonicalize "/dev/disk/by-partlabel/${label}" || true)"
        if [[ -b "${part}" ]]; then
            disks+=("$(parent_of "${part}")")
        fi
    done

    # Prints nothing when the boot medium is ambiguous -- with a second Loom
    # stick attached the labels resolve to two disks, and guessing would be
    # how the wrong device gets erased. Callers must treat empty as fatal.
    if [[ "${#disks[@]}" -eq 0 ]]; then
        return 0
    fi

    sorted="$(printf '%s\n' "${disks[@]}" | sort --unique)"
    mapfile -t unique <<<"${sorted}"

    if [[ "${#unique[@]}" -ne 1 ]]; then
        return 0
    fi
    printf '%s' "${unique[0]}"
}

# Internal NVMe namespaces only, minus the boot medium and anything removable,
# on the USB bus, or currently mounted.
#
# Restricting candidates to /dev/nvmeXnY is the backstop: USB mass storage
# enumerates as sd*, so a stick can never end up in this list even if every
# other check below were to break.
target_disks() {
    local boot listing filtered candidates=() targets=()
    local disk base removable props mountpoints mounts

    boot="$(boot_disk)"
    if [[ -z "${boot}" ]]; then
        return 0
    fi

    listing="$(lsblk --nodeps --noheadings --raw --paths --output NAME,TYPE)"
    filtered="$(printf '%s\n' "${listing}" |
        awk '$2 == "disk" { print $1 }' |
        grep --extended-regexp '^/dev/nvme[0-9]+n[0-9]+$' || true)"

    if [[ -z "${filtered}" ]]; then
        return 0
    fi
    mapfile -t candidates <<<"${filtered}"

    for disk in "${candidates[@]}"; do
        if [[ "${disk}" == "${boot}" ]]; then
            continue
        fi

        base="$(basename "${disk}")"
        removable=1
        if [[ -r "/sys/block/${base}/removable" ]]; then
            removable="$(cat "/sys/block/${base}/removable")"
        fi
        if [[ "${removable}" == "1" ]]; then
            continue
        fi

        props="$(udevadm info --query=property --name="${disk}" || true)"
        if printf '%s\n' "${props}" | grep --quiet --line-regexp 'ID_BUS=usb'; then
            continue
        fi

        # Anything with a mounted partition is the live system, not a target.
        mountpoints="$(lsblk --noheadings --raw --paths --output MOUNTPOINTS "${disk}")"
        mounts="${mountpoints//[$' \n']/}"
        if [[ -n "${mounts}" ]]; then
            continue
        fi

        targets+=("${disk}")
    done

    if [[ "${#targets[@]}" -gt 0 ]]; then
        printf '%s\n' "${targets[@]}"
    fi
}

# Prints what dies and what survives, then demands the target's serial number.
# Typing a serial rather than "yes" makes it impossible to confirm by muscle
# memory on the wrong machine.
confirm_destructive() {
    local action="${1}" boot="${2}"
    shift 2
    local targets=("${@}")
    local disk description answer serial

    echo
    echo "=== ${action}: THE FOLLOWING WILL BE DESTROYED ==="
    for disk in "${targets[@]}"; do
        description="$(disk_description "${disk}")"
        echo "    ${description}"
    done
    echo
    echo "=== WILL NOT BE TOUCHED (boot medium) ==="
    description="$(disk_description "${boot}")"
    echo "    ${description}"
    echo

    serial="$(sysfs_attr "${targets[0]}" serial)"
    read -r -p "Type the serial of the first disk above to confirm: " answer
    if [[ "${answer}" != "${serial}" ]]; then
        die "Serial does not match. Aborted."
    fi

    read -r -p "Type ${action} to proceed: " answer
    if [[ "${answer}" != "${action}" ]]; then
        die "Aborted."
    fi
}

# "present" when the stick's key partition holds something other than zeroes.
# A stick that was never provisioned would install fine and then never boot, so
# this is checked before doing anything destructive.
#
# Prints a word rather than returning a status: a `if key_is_present` caller
# would silently disable set -e for the whole condition.
key_state() {
    local key_dev="${1}" raw stripped
    if [[ ! -b "${key_dev}" ]]; then
        printf 'missing'
        return 0
    fi
    raw="$(head --bytes="${LOOM_KEY_BYTES}" "${key_dev}")"
    stripped="${raw//$'\0'/}"
    if [[ -n "${stripped}" ]]; then
        printf 'present'
    else
        printf 'empty'
    fi
}
