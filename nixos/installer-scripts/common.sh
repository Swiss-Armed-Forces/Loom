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
# disks use `loom-esp` and `loom-pv<N>`. The prefixes must stay disjoint --
# /dev/disk/by-partlabel is not unique, and with both media attached a shared
# name would resolve to whichever udev linked last.
#
# The PV label carries an index for the same reason: every internal disk gets
# one, and two partitions sharing a name would make `by-partlabel` a coin toss
# between the members of the very pool being built.
readonly LOOM_LIVE_ESP_LABEL="loom-live-esp"
readonly LOOM_LIVE_STORE_LABEL="loom-live-store"
readonly LOOM_KEY_LABEL="loom-key"
readonly LOOM_ESP_LABEL="loom-esp"
readonly LOOM_PV_LABEL_PREFIX="loom-pv"

readonly LOOM_KEY_BYTES=4096
# The whole pool, not each disk: a box with two small NVMes has as much room as
# one with a single large one, and refusing it would be arithmetic nobody can
# argue with from the console.
readonly LOOM_MIN_POOL_BYTES=$((250 * 1000 * 1000 * 1000))

# The pool the box boots from. All three come from nixos/storage.nix by way of
# installer.nix's wrapProgram, so the names the installer creates and the names
# the box's stage 1 waits for cannot drift apart -- the one failure in here that
# produces a box which installs perfectly and then never boots again.
readonly LOOM_VG_NAME="${LOOM_VG_NAME:?LOOM_VG_NAME is not set}"
readonly LOOM_LV_NAME="${LOOM_LV_NAME:?LOOM_LV_NAME is not set}"
readonly LOOM_ROOT_DEVICE="${LOOM_ROOT_DEVICE:?LOOM_ROOT_DEVICE is not set}"

# Set by menu.sh before it hands over to an unattended install, so that a menu
# restarted by systemd cannot count down a second time onto a disk the first
# attempt already began partitioning. In tmpfs: it must not survive a reboot,
# because a reboot is how an operator retries.
readonly LOOM_AUTO_MARKER="/run/loom-auto-install-attempted"

# install.sh exits with this when the install itself succeeded but the box may
# not boot into it unattended -- see fix_boot_order there. menu.sh holds the
# console open on it rather than counting down, because the firmware fix it
# asks for is printed nowhere else: the installed box's login banner repeats
# the recovery passphrase, but not this.
readonly LOOM_EXIT_BOOT_ORDER_DEGRADED=2

# Console styling.
#
# Raw ANSI rather than `clear`/`tput`: those need a TERM, and the menu is
# started by systemd on a TTYPath (installer.nix), where nothing sets one. An
# escape sequence is understood by the terminal itself, so it needs nothing from
# the environment.
#
# Everything collapses to the empty string off a terminal, which keeps escapes
# out of `loom-menu | tee` and out of the journal.
if [[ -t 1 ]]; then
    readonly LOOM_BOLD=$'\033[1m'
    readonly LOOM_DIM=$'\033[2m'
    readonly LOOM_RED=$'\033[1;31m'
    readonly LOOM_GREEN=$'\033[32m'
    readonly LOOM_YELLOW=$'\033[33m'
    readonly LOOM_RESET=$'\033[0m'
else
    readonly LOOM_BOLD=""
    readonly LOOM_DIM=""
    readonly LOOM_RED=""
    readonly LOOM_GREEN=""
    readonly LOOM_YELLOW=""
    readonly LOOM_RESET=""
fi

# A fixed width, not ${COLUMNS}: systemd starts this on a TTYPath with no shell
# to set that variable, and a rule that wraps looks far worse than one that is a
# little short. 51 keeps the header and every status line under it inside 80
# columns.
readonly LOOM_RULE="==================================================="

# Home the cursor and clear the screen. Deliberately not \033[3J as well:
# clearing the scrollback is an xterm extension, and the Linux VT this runs on
# does not implement it.
clear_screen() {
    [[ -t 1 ]] || return 0
    printf '\033[H\033[2J'
}

# The amber the eyes are drawn in, measured off the favicon itself
# (Frontend/public/web-app-manifest-512x512.png) rather than eyeballed. The same
# value the plymouth theme paints its progress bar with, so the boot splash and
# the menu agree.
readonly LOOM_AMBER_RGB="f7b718"

# The mark the boot splash just showed, in the two eyes it is actually made of.
#
# The art itself is `loom-eyes`, from branding.nix, because the installed box
# prints the same pair in its login banner and two copies would drift. What
# stays here is the colour, which is the half the two screens do *not* agree on.
#
# `ESC ] P nrrggbb` redefines a palette entry on the Linux VT, which is the only
# way to reach an exact colour there: console_codes(4) records that even a
# 24-bit `38;2;r;g;b` is "shoehorned into 16 basic colors", so ESC[33m lands on
# #ffff55 with bold and #aa5500 without -- both far enough from the logo to read
# as a mistake rather than a colour. Index 3 and index 11 are both set because
# bold promotes one to the other.
#
# Two consequences, both deliberate. It repaints every LOOM_YELLOW in the menu,
# so the target-disk line matches the eyes. And it outlives this function --
# there is no reset, so the rescue shell inherits it too.
#
# Never anywhere but a VT: console_codes(4) warns that xterm hangs on this
# sequence until somebody presses return, and this script is also run by hand
# from a shell that may be one.
loom_banner() {
    local console

    # Assigned separately rather than tested inline: `tty` exits non-zero when
    # stdin is not a terminal, and inside a condition that status would be
    # swallowed rather than handled.
    console="$(tty 2>/dev/null || true)"
    # Off a terminal the escapes are already empty strings, so a captured log
    # stays readable; this only has to keep the palette sequence off it too.
    [[ -t 1 ]] || console="none"

    case "${console}" in
    /dev/tty[0-9]*)
        printf '\033]P3%s\033]PB%s' "${LOOM_AMBER_RGB}" "${LOOM_AMBER_RGB}"
        ;;
    *) ;;
    esac

    printf '%s%s' "${LOOM_YELLOW}" "${LOOM_BOLD}"
    loom-eyes
    printf '%s' "${LOOM_RESET}"
}

log() { printf '%s[*]%s %s\n' "${LOOM_DIM}" "${LOOM_RESET}" "${*}"; }

# The palette is keyed on stdout, so err() checks stderr separately -- otherwise
# `loom-install 2>install.log` from a terminal would write escapes into the log.
err() {
    if [[ -t 2 ]]; then
        printf >&2 '%s[!] %s%s\n' "${LOOM_RED}" "${*}" "${LOOM_RESET}"
    else
        printf >&2 '[!] %s\n' "${*}"
    fi
}
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
        # Trim. NVMe pads the Identify Controller fields to a fixed width with
        # spaces, so a serial arrives as "S6XSNU0T12345       ". Command
        # substitution strips the trailing newline but not that padding, and
        # every consumer of this is a line on the operator's screen -- the menu
        # status block and the disk lists in the destructive interlock. Padding
        # pushes the columns apart and reads as a truncated value.
        value="${value#"${value%%[![:space:]]*}"}"
        value="${value%"${value##*[![:space:]]}"}"
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

    # Sorted, because the order is now load-bearing: every disk here joins the
    # pool, and the first one is the disk that gets the ESP and the NVRAM boot
    # entry. lsblk already lists in kernel order, but "already" is not a
    # guarantee to hang a boot partition on.
    if [[ "${#targets[@]}" -gt 0 ]]; then
        printf '%s\n' "${targets[@]}" | sort
    fi
}

# Prints what dies and what survives, then demands the action word.
#
# The action word is the whole interlock: it is never "yes", so it cannot be
# confirmed by muscle memory, and the disk that is about to be destroyed is
# named on screen directly above the prompt. Transcribing a 20-character NVMe
# serial was the earlier design and was simply too tedious to live with.
confirm_destructive() {
    local action="${1}" boot="${2}"
    shift 2
    local targets=("${@}")
    local disk description answer

    # No clear_screen anywhere below: the list of disks about to die has to stay
    # on screen directly above the prompt.
    echo
    printf '%s=== %s: THE FOLLOWING WILL BE DESTROYED ===%s\n' \
        "${LOOM_RED}" "${action}" "${LOOM_RESET}"
    for disk in "${targets[@]}"; do
        description="$(disk_description "${disk}")"
        printf '    %s%s%s\n' "${LOOM_RED}" "${description}" "${LOOM_RESET}"
    done
    echo
    if [[ "${#targets[@]}" -gt 1 ]]; then
        printf '    %s^^ ALL %s DISKS ABOVE, not just the first.%s\n' \
            "${LOOM_RED}" "${#targets[@]}" "${LOOM_RESET}"
        echo
    fi
    printf '%s=== WILL NOT BE TOUCHED (boot medium) ===%s\n' \
        "${LOOM_GREEN}" "${LOOM_RESET}"
    description="$(disk_description "${boot}")"
    printf '    %s%s%s\n' "${LOOM_DIM}" "${description}" "${LOOM_RESET}"
    echo

    # Printed rather than passed to `read -p`, which writes its prompt to
    # stderr: that is invisible the moment stderr is anywhere but the
    # operator's terminal, and it leaves the prompt outside the palette above.
    printf 'Type %s to proceed: ' "${action}"
    read -r answer
    # Be forgiving about stray whitespace the operator may type or paste.
    answer="${answer#"${answer%%[![:space:]]*}"}"
    answer="${answer%"${answer##*[![:space:]]}"}"
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
    local key_dev="${1}"
    if [[ ! -b "${key_dev}" ]]; then
        printf 'missing'
        return 0
    fi
    # Compared against /dev/zero rather than read into a variable: a command
    # substitution on binary makes bash strip the NUL bytes and print a warning
    # into the middle of the installer menu, and a pipeline would hide the exit
    # status of the read.
    if cmp --quiet --bytes="${LOOM_KEY_BYTES}" "${key_dev}" /dev/zero; then
        printf 'empty'
    else
        printf 'present'
    fi
}

# Total capacity of the disks that would be pooled.
pool_bytes() {
    local disks=("${@}") disk total=0 bytes
    for disk in "${disks[@]}"; do
        bytes="$(blockdev --getsize64 "${disk}" 2>/dev/null || echo 0)"
        total=$((total + bytes))
    done
    printf '%s' "${total}"
}

# Let go of whatever is holding the internal disks, without destroying anything.
#
# Both destructive paths need this before they can touch a partition table, and
# the already-installed probe needs the inverse of it afterwards. Shared rather
# than written twice because the order is the part that matters: the LUKS
# mapping sits on the logical volume, so closing dm-crypt has to come first or
# the group is still in use and `vgchange --activate n` quietly does nothing.
release_storage() {
    local mapping
    swapoff --all 2>/dev/null || true
    umount --recursive /mnt 2>/dev/null || true

    for mapping in /dev/mapper/*; do
        [[ -b "${mapping}" ]] || continue
        [[ "$(basename "${mapping}")" == "control" ]] && continue
        cryptsetup close "$(basename "${mapping}")" 2>/dev/null || true
    done

    vgchange --activate n "${LOOM_VG_NAME}" >/dev/null 2>&1 || true
}

# Destroy the pool itself, so the disks under it can be repartitioned.
#
# Deliberately separate from release_storage above: the probe deactivates, the
# installer destroys, and conflating the two would make looking at a box
# indistinguishable from reinstalling it.
discard_pool() {
    release_storage
    vgremove --force "${LOOM_VG_NAME}" >/dev/null 2>&1 || true
    # Drop what lvm cached about devices that are about to stop existing.
    # Without it `vgcreate` can still see the group it was just told to forget.
    pvscan --cache >/dev/null 2>&1 || true
}

# "yes" when the internal disks already hold a Loom pool that *this* stick's key
# unlocks -- meaning this very stick installed this very box.
#
# This is what replaces the typed INSTALL word for an unattended install. The
# accident it guards against is the one the design otherwise invites: the stick
# stays plugged in forever, so a cleared NVRAM or a firmware that re-scans
# removable media boots the installer again, and without this the box would
# quietly reinstall over its own indexed data with nobody at the keyboard.
#
# A re-flashed stick carries a fresh key, so this never blocks re-provisioning.
# It only blocks a stick meeting the box it already installed.
#
# Prints a word rather than returning a status, like key_state above: an
# `if pool_claimed_by_key` caller would disable set -e for the whole condition.
pool_claimed_by_key() {
    local key_dev="${1}" result="no"

    vgchange --activate y "${LOOM_VG_NAME}" >/dev/null 2>&1 || true
    if [[ -b "${LOOM_ROOT_DEVICE}" ]] &&
        cryptsetup luksOpen --test-passphrase \
            --key-file "${key_dev}" \
            --keyfile-size "${LOOM_KEY_BYTES}" \
            "${LOOM_ROOT_DEVICE}" >/dev/null 2>&1; then
        result="yes"
    fi
    # Leave the box as it was found. An active group would also make the
    # partition table busy if the operator picks Install off the menu anyway.
    vgchange --activate n "${LOOM_VG_NAME}" >/dev/null 2>&1 || true

    printf '%s' "${result}"
}

# Whether this boot may install without anybody confirming it, and if not, why.
#
# Deliberately pure: every input is already-gathered state, passed in. The
# device work happens in the caller, which makes the rule itself something a
# test can exercise exhaustively -- and this is the rule that decides whether a
# disk gets destroyed unattended.
#
# Arguments, in order:
#   attempted     0|1                     the per-boot marker
#   boot          device path, or empty   the medium we booted from
#   key_status    present|empty|missing   from key_state
#   target_count  how many eligible disks there are
#   bytes         total capacity of those disks
#   claimed       yes|no                  from pool_claimed_by_key
#
# Prints `armed` or the reason it is not.
auto_install_decision() {
    local attempted="${1}" boot="${2}" key_status="${3}"
    local target_count="${4}" bytes="${5}" claimed="${6}"

    # First, and before anything looks at a disk: after one attempt this boot
    # the disks may be half-written, and probing them says nothing useful.
    if [[ "${attempted}" != "0" ]]; then
        printf 'attempted'
    elif [[ -z "${boot}" ]]; then
        printf 'no-boot-medium'
    elif [[ "${key_status}" != "present" ]]; then
        printf 'no-key'
    elif [[ "${target_count}" -eq 0 ]]; then
        printf 'no-target'
    elif [[ "${bytes}" -lt "${LOOM_MIN_POOL_BYTES}" ]]; then
        printf 'too-small'
    elif [[ "${claimed}" == "yes" ]]; then
        printf 'already-installed'
    else
        printf 'armed'
    fi
}

# What to tell the operator when the verdict is not `armed`.
#
# Every one of these ends at the menu, which is the safe outcome -- so this is
# not an error report but an explanation of why the box is waiting for them.
auto_install_reason() {
    case "${1}" in
    attempted) printf 'an install was already attempted this boot' ;;
    no-boot-medium) printf 'the boot medium is ambiguous' ;;
    no-key) printf 'the stick carries no LUKS key' ;;
    no-target) printf 'there is no eligible internal disk' ;;
    too-small) printf 'the disks are too small' ;;
    already-installed) printf 'this stick already installed this box' ;;
    *) printf '%s' "${1}" ;;
    esac
}
