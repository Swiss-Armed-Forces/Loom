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
# The specialisation whose boot entry a fresh box has to come up on. Written by
# installer.nix from the evaluated configuration, so this never has to spell
# `first-time-setup` and a rename in modes.nix cannot drift away from it.
readonly SETUP_SPECIALISATION_FILE=/etc/loom/setup-specialisation
readonly RECOVERY_FILE_REL=var/lib/loom/recovery-passphrase

# "aa64" or "x64", set by installer.nix from config.nixpkgs.hostPlatform.efiArch
# -- the same value that names the loader it puts on the stick's ESP. Hardcoding
# either spelling here is how the installer and the image it came from drift
# apart without anything failing loudly.
readonly EFI_ARCH="${LOOM_EFI_ARCH:?LOOM_EFI_ARCH is not set}"

# Set by fix_boot_order when the internal disk did not become the default boot
# entry. Deliberately a global rather than a return value: fix_boot_order is
# called directly, not in a command substitution, so it can assign here -- and
# its own non-zero return is already spoken for by the paths that must not abort
# an install that has otherwise completely succeeded.
boot_order_degraded=0

# Set by select_setup_entry when the first-time-setup entry could not be made the
# boot default. Deliberately NOT folded into boot_order_degraded above: that one
# means the firmware will not reach this disk at all, and menu.sh answers it by
# telling the operator to fix the firmware boot order. This one means the disk
# boots fine and merely starts on the wrong entry, where that advice would be
# wrong. It is reported in the completion block instead.
setup_entry_manual=0

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
    select_setup_entry
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
    log "Leave the USB stick plugged in. The box cannot boot without it, and"
    log "removing it from a running box powers that box off ten seconds later."
    echo

    # What happens next, because nothing else says it: this box needs one boot on
    # a network with internet before it is of any use offline.
    if ((setup_entry_manual)); then
        err "Could not preselect the first-time-setup entry -- see the warning above."
        err "At the boot menu, choose 'Loom (first-time-setup)' by hand."
    else
        log "This box boots into first-time setup by itself. Leave it on a network"
        log "with internet until it powers itself off; that run pulls every container"
        log "image, and it never needs the internet again afterwards."
    fi

    # Tested with `if ((...))` rather than as a bare arithmetic command: `((0))`
    # returns 1, which under `set -e` would abort a successful install here.
    if ((boot_order_degraded)); then
        return "${LOOM_EXIT_BOOT_ORDER_DEGRADED}"
    fi
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

# Leave the boot menu pointing at first-time setup.
#
# A fresh box has no container images, so the first boot has to be the
# `Loom (first-time-setup)` entry -- see nixos/modes.nix. Selecting it here is
# not merely a convenience: the default `Loom` entry serves DHCP and wildcard
# *.loom on the appliance NIC, so a box that boots it while still cabled to the
# network it fetches over puts a DHCP server on that network. Choosing correctly
# every time is not something to leave to whoever is watching the menu.
#
# Written by hand rather than by re-running the bootloader builder, because the
# builder cannot express it. It decides which entry is default by comparing its
# DEFAULT-CONFIG argument against the *main* toplevel only, and then calls
# write_loader_conf() with no specialisation -- so `default` can never name
# anything but `nixos-generation-<N>.conf`. Handing it the specialisation's
# toplevel does not select that entry; it matches nothing, and loader.conf is
# left unwritten entirely.
#
# The line stays put because nothing regenerates it: the installed box has no
# nixos-rebuild, no channel and no evaluation. `loom-promote-boot-entry`
# (modes.nix) is what rewrites it, once, at the end of the setup run.
select_setup_entry() {
    local conf entries specialisation current setup selected
    conf="${MOUNT}/boot/loader/loader.conf"
    entries="${MOUNT}/boot/loader/entries"
    specialisation="$(cat "${SETUP_SPECIALISATION_FILE}")"

    # Every failure below warns and returns 0. The disk is partitioned, encrypted
    # and written by this point, and the fallback is exactly the behaviour this
    # step replaces -- an operator picking the entry off the menu themselves. The
    # completion block in main() repeats the instruction where it will be read.
    if [[ ! -r "${conf}" ]]; then
        err "No ${conf} after install; cannot preselect first-time setup."
        setup_entry_manual=1
        return 0
    fi

    # What nixos-install just wrote: `default nixos-generation-<N>.conf`. Read
    # rather than assumed, so the generation number comes from the file -- it is
    # 1 on a freshly mkfs'd root, but nothing here needs to depend on that.
    current="$(awk '$1 == "default" { print $2 }' "${conf}")"
    if [[ -z "${current}" ]]; then
        err "No 'default' line in ${conf}; cannot preselect first-time setup."
        setup_entry_manual=1
        return 0
    fi

    # The filename the systemd-boot builder composes for a specialisation, per
    # its own generation_conf_filename(): the generation's entry, with the
    # specialisation's attribute name appended.
    setup="${current%.conf}-specialisation-${specialisation}.conf"

    # Checked before anything is rewritten. This is what catches a renamed or
    # removed specialisation, and it is why SETUP_SPECIALISATION_FILE is written
    # from the evaluated configuration rather than spelled out here.
    if [[ ! -f "${entries}/${setup}" ]]; then
        err "Expected ${setup} in ${entries}, but it is not there."
        setup_entry_manual=1
        return 0
    fi

    # Only the default line. `timeout`, `editor` and `console-mode` stay exactly
    # as the builder wrote them.
    sed --in-place "s|^default .*|default ${setup}|" "${conf}"

    # Read back into a variable rather than tested inline: a command substitution
    # inside `[[ ]]` masks awk's own exit status, which shellcheck rightly
    # objects to (SC2312).
    selected="$(awk '$1 == "default" { print $2 }' "${conf}")"
    if [[ "${selected}" != "${setup}" ]]; then
        err "Could not select ${setup} in ${conf}."
        setup_entry_manual=1
        return 0
    fi

    log "First-time setup is the default boot entry"
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
        boot_order_degraded=1
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
            boot_order_degraded=1
        fi
        umount "${stick_esp}"
    else
        # Same consequence as the branch above, and until now it was the one way
        # to reach it in silence: an unmountable stick ESP left the fallback
        # loader in place with nothing printed about it.
        err "Could not mount the stick's ${LOOM_LIVE_ESP_LABEL} partition."
        err "The stick still owns the UEFI removable-media path, so this box may boot"
        err "the installer again. Put the internal disk first in the firmware boot order."
        boot_order_degraded=1
    fi
    rmdir "${stick_esp}"
}

main "${@}"
