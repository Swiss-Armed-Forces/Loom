#!/usr/bin/env bash
#
# Installs the Loom appliance onto the box's internal NVMe.
#
# Everything installed here is already on the stick, so this never touches the
# network: the appliance closure rides along in the `loom-live-store` partition
# and nixos-install only has to copy it.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
# shellcheck disable=SC1091
source "${LOOM_INSTALLER_LIB:?LOOM_INSTALLER_LIB is not set}/common.sh"

readonly MOUNT=/mnt
readonly TARGET_SYSTEM_FILE=/etc/loom/target-system
readonly RECOVERY_FILE_REL=var/lib/loom/recovery-passphrase

# "aa64" or "x64", set by installer.nix from config.nixpkgs.hostPlatform.efiArch
# -- the same value that names the loader it puts on the stick's ESP. Hardcoding
# either spelling here is how the installer and the image it came from drift
# apart without anything failing loudly.
readonly EFI_ARCH="${LOOM_EFI_ARCH:?LOOM_EFI_ARCH is not set}"

main() {
    local boot target key_dev key_status eligible passphrase targets=()

    if [[ "${EUID}" -ne 0 ]]; then
        die "The installer must run as root."
    fi

    boot="$(boot_disk)"
    if [[ -z "${boot}" ]]; then
        die "Could not identify the boot medium. Is a second Loom stick plugged in?"
    fi
    eligible="$(target_disks)"
    if [[ -z "${eligible}" ]]; then
        die "No eligible internal NVMe found. Nothing to install onto."
    fi
    mapfile -t targets <<<"${eligible}"
    target="$(select_target "${targets[@]}")"

    check_disk_size "${target}"

    key_dev="/dev/disk/by-partlabel/${LOOM_KEY_LABEL}"
    key_status="$(key_state "${key_dev}")"
    if [[ "${key_status}" != "present" ]]; then
        die "The ${LOOM_KEY_LABEL} partition is ${key_status}. Re-flash with 'build-appliance-image --flash'."
    fi

    confirm_destructive "INSTALL" "${boot}" "${target}"

    partition "${target}"
    encrypt "${key_dev}"
    make_filesystems
    mount_target
    install_system
    passphrase="$(enroll_recovery_passphrase)"
    fix_boot_order "${target}" "${boot}"
    unmount_target

    echo
    log "Installation complete."
    echo
    echo "    LUKS recovery passphrase: ${passphrase}"
    echo
    echo "    Write this down now and keep it somewhere other than the box."
    echo "    Without the USB stick it is the only way to unlock this disk."
    echo "    It is also shown on every console login."
    echo
    log "Leave the USB stick plugged in. The box cannot boot without it."
}

# Which disk to install onto, when the box has more than one.
#
# Taking targets[0] unasked was fine while every appliance was a Spark with one
# drive; the EVO-X2 has two M.2 slots, and there "whichever lsblk listed first"
# is not something an operator can predict or verify. menu.sh already lists every
# candidate, and wipe.sh already erases all of them -- this makes install agree.
#
# Everything here goes to stderr: the chosen device is this function's stdout.
select_target() {
    local targets=("${@}") index answer description

    if [[ "${#targets[@]}" -eq 1 ]]; then
        printf '%s' "${targets[0]}"
        return 0
    fi

    echo >&2
    echo >&2 "=== MORE THAN ONE ELIGIBLE INTERNAL DISK ==="
    for index in "${!targets[@]}"; do
        description="$(disk_description "${targets[index]}")"
        printf '    %d) %s\n' "$((index + 1))" "${description}" >&2
    done
    echo >&2
    # A number, not a serial: this only has to disambiguate between the disks
    # listed directly above. The interlock that guards against doing this to the
    # wrong machine is the INSTALL confirmation that follows.
    read -r -p "Install onto which disk? [1-${#targets[@]}]: " answer

    if [[ ! "${answer}" =~ ^[0-9]+$ ]] || ((answer < 1 || answer > ${#targets[@]})); then
        # `die` exits the command substitution rather than the script, but the
        # non-zero status propagates through the assignment under `set -e`.
        die "Not a choice: '${answer}'. Aborted."
    fi
    printf '%s' "${targets[answer - 1]}"
}

check_disk_size() {
    local disk="${1}" bytes
    bytes="$(blockdev --getsize64 "${disk}")"
    if [[ "${bytes}" -lt "${LOOM_MIN_DISK_BYTES}" ]]; then
        # Documentation/installation.md:32 asks for 200 GiB, and the container
        # images alone are around 60 GB.
        die "$(basename "${disk}") is $((bytes / 1000 / 1000 / 1000)) GB; Loom needs at least $((LOOM_MIN_DISK_BYTES / 1000 / 1000 / 1000)) GB."
    fi
}

partition() {
    local disk="${1}"
    log "Partitioning ${disk}"

    wipefs --all "${disk}"
    sgdisk --zap-all "${disk}"
    sgdisk \
        --new=1:0:+1G --typecode=1:ef00 --change-name="1:${LOOM_ESP_LABEL}" \
        --new=2:0:0 --typecode=2:8309 --change-name="2:${LOOM_ROOT_LABEL}" \
        "${disk}"

    partprobe "${disk}"
    udevadm settle
}

encrypt() {
    local key_dev="${1}"
    log "Creating the LUKS2 container"

    # pbkdf2 with a low iteration count is deliberate: the key is 4096 bytes of
    # /dev/urandom, so stretching it buys nothing and only slows every boot.
    cryptsetup luksFormat \
        --type luks2 \
        --batch-mode \
        --pbkdf pbkdf2 \
        --pbkdf-force-iterations 1000 \
        --key-size 512 \
        --cipher aes-xts-plain64 \
        --key-file "${key_dev}" \
        --keyfile-size "${LOOM_KEY_BYTES}" \
        "/dev/disk/by-partlabel/${LOOM_ROOT_LABEL}"

    cryptsetup open \
        --key-file "${key_dev}" \
        --keyfile-size "${LOOM_KEY_BYTES}" \
        "/dev/disk/by-partlabel/${LOOM_ROOT_LABEL}" \
        cryptroot
}

make_filesystems() {
    log "Creating filesystems"
    mkfs.vfat -F 32 -n LOOMESP "/dev/disk/by-partlabel/${LOOM_ESP_LABEL}"
    mkfs.ext4 -q -L loomroot /dev/mapper/cryptroot
}

mount_target() {
    # The live root is a tmpfs built from nothing, so /mnt does not exist until
    # we create it -- unlike on an installed system, where it always does.
    mkdir --parents "${MOUNT}"
    mount /dev/mapper/cryptroot "${MOUNT}"
    mkdir --parents "${MOUNT}/boot"
    mount "/dev/disk/by-partlabel/${LOOM_ESP_LABEL}" "${MOUNT}/boot"
}

unmount_target() {
    umount --recursive "${MOUNT}"
    cryptsetup close cryptroot
}

install_system() {
    local system
    system="$(cat "${TARGET_SYSTEM_FILE}")"
    log "Installing ${system}"

    # --system installs a pre-built closure, so nothing is evaluated or built.
    # nixos-install still shells out to `nix-env --extra-substituters
    # 'auto?trusted=1'` regardless, so the substituters are emptied explicitly
    # as well -- otherwise a store hiccup becomes a hang on a box with no
    # network rather than a clean failure.
    nixos-install \
        --root "${MOUNT}" \
        --system "${system}" \
        --no-channel-copy \
        --no-root-password \
        --option substituters "" \
        --option builders "" \
        --option connect-timeout 1
}

# Generated here rather than at image build time, so it never leaves the box and
# every box gets its own.
enroll_recovery_passphrase() {
    local passphrase target_file
    passphrase="$(generate_passphrase)"
    target_file="${MOUNT}/${RECOVERY_FILE_REL}"

    cryptsetup luksAddKey \
        --key-file "/dev/disk/by-partlabel/${LOOM_KEY_LABEL}" \
        --keyfile-size "${LOOM_KEY_BYTES}" \
        --batch-mode \
        "/dev/disk/by-partlabel/${LOOM_ROOT_LABEL}" \
        <(printf '%s' "${passphrase}") >&2

    # Safe to store in the clear: reading it requires the disk to be unlocked
    # and mounted, which already requires the stick or this very passphrase.
    install --directory --mode=0750 "$(dirname "${target_file}")"
    printf '%s\n' "${passphrase}" >"${target_file}"
    chmod 0440 "${target_file}"
    # root:wheel -- wheel is gid 1 on NixOS, and /etc/group is not readable
    # from here in a way worth parsing.
    chown 0:1 "${target_file}"

    printf '%s' "${passphrase}"
}

generate_passphrase() {
    # Six groups of five lowercase-and-digit characters. Plenty of entropy and
    # still transcribable by someone reading it off a monitor.
    #
    # `head` bounds the read rather than cutting a `tr` that reads /dev/urandom
    # endlessly: systemd runs us with SIGPIPE ignored (IgnoreSIGPIPE defaults to
    # yes), so such a tr does not die quietly on the closed pipe -- it gets EPIPE
    # back, prints "tr: write error: Broken pipe" onto the installer console and
    # exits 1. 256 bytes yield ~32 usable characters, the loop covers the rest.
    local raw=''
    while ((${#raw} < 30)); do
        raw+="$(head --bytes=256 /dev/urandom |
            tr --delete --complement 'abcdefghijkmnpqrstuvwxyz23456789')"
    done

    printf '%s' "${raw:0:30}" |
        sed --regexp-extended 's/(.{5})/\1-/g; s/-$//'
}

# The stick stays plugged in forever and carries the UEFI removable-media
# fallback path, so most firmware would boot the installer on every reboot.
# Give the internal disk a named NVRAM entry and take the stick off the
# fallback path, leaving it reachable from the firmware's own boot menu.
fix_boot_order() {
    local target="${1}" boot="${2}" esp_part_num=1
    log "Making the internal disk the default boot entry"

    # efibootmgr does not check that the loader exists, so a wrong name here
    # produces an entry the firmware silently cannot boot.
    if ! efibootmgr --create \
        --disk "${target}" \
        --part "${esp_part_num}" \
        --loader "\\EFI\\systemd\\systemd-boot${EFI_ARCH}.efi" \
        --label "Loom appliance" >/dev/null 2>&1; then
        err "Could not create an NVRAM boot entry. Select the internal disk manually in firmware."
        return 0
    fi

    local stick_esp fallback
    stick_esp="$(mktemp --directory)"
    if mount "/dev/disk/by-partlabel/${LOOM_LIVE_ESP_LABEL}" "${stick_esp}" 2>/dev/null; then
        fallback="${stick_esp}/EFI/BOOT/BOOT${EFI_ARCH^^}.EFI"
        if [[ -f "${fallback}" ]]; then
            mkdir --parents "${stick_esp}/EFI/loom"
            mv "${fallback}" "${stick_esp}/EFI/loom/boot${EFI_ARCH}.efi"
            log "Installer moved to \\EFI\\loom\\boot${EFI_ARCH}.efi on ${boot}; reach it from the firmware boot menu."
        else
            # Not cosmetic: the stick stays plugged in forever, so as long as it
            # owns the removable-media path most firmware boots the installer
            # instead of the appliance on every restart. Never fail quietly here.
            err "Expected ${fallback} on the stick, but it is not there."
            err "The stick still owns the UEFI removable-media path, so this box may boot"
            err "the installer again. Put the internal disk first in the firmware boot order."
        fi
        umount "${stick_esp}"
    fi
    rmdir "${stick_esp}"
}

main "${@}"
