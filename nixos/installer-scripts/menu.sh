#!/usr/bin/env bash
#
# The installer's console menu, on tty1 and on serial.
#
# This is a TUI rather than extra bootloader entries on purpose: a boot menu
# cannot enumerate disks, so it could never show the operator which drive is
# about to be destroyed, and firmware differs wildly in how it renders menus and
# accepts input. A program on a Linux console behaves the same everywhere,
# including over a serial cable.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
# shellcheck disable=SC1091
source "${LOOM_INSTALLER_LIB:?LOOM_INSTALLER_LIB is not set}/common.sh"

show_status() {
    local boot key_dev key_status description eligible targets=() disk
    echo
    echo "  Loom appliance installer"
    echo "  ------------------------"

    boot="$(boot_disk)"
    if [[ -n "${boot}" ]]; then
        description="$(disk_description "${boot}")"
        echo "  Boot medium : ${description}"
        echo "                (never written to by any option below)"
    else
        echo "  Boot medium : COULD NOT BE IDENTIFIED"
        echo "                Install and wipe will refuse to run."
    fi

    key_dev="/dev/disk/by-partlabel/${LOOM_KEY_LABEL}"
    key_status="$(key_state "${key_dev}")"
    if [[ "${key_status}" == "present" ]]; then
        echo "  LUKS key    : present"
    else
        echo "  LUKS key    : ${key_status} -- re-flash with 'build-appliance-image --flash'"
    fi

    eligible="$(target_disks)"
    if [[ -n "${eligible}" ]]; then
        mapfile -t targets <<<"${eligible}"
        for disk in "${targets[@]}"; do
            description="$(disk_description "${disk}")"
            echo "  Target      : ${description}"
        done
    else
        echo "  Target      : no eligible internal NVMe found"
    fi
    echo
}

show_menu() {
    echo "    1) Install Loom appliance to the internal disk"
    echo "    2) ERASE ALL DATA on the internal disks"
    echo "    3) Reboot"
    echo "    4) Power off"
    echo "    5) Rescue shell                         [default]"
    echo
}

# The rescue shell stays the default: it is the one option that cannot destroy
# anything, so an idle keypress lands somewhere harmless. Both destructive
# options additionally run the interlock in common.sh, which demands the
# target's serial number.
rescue_shell() {
    echo "  Rescue shell. Type 'exit' or press Ctrl-D to return to the menu."
    echo

    # --norc --noprofile so that nothing downstream resets PS1; the prompt is
    # then set here and actually survives. PATH has to be spelled out for the
    # same reason: the inherited one is what wrapProgram built for the
    # installer (cryptsetup, nvme-cli, gptfdisk, parted, nixos-install-tools),
    # which is most of what a rescue shell wants but has neither loom-install
    # itself nor the rest of the system profile.
    #
    # TERM matters too: without it bash gives no line editing and nothing can
    # clear the screen, which is most of what makes a bare shell feel broken.
    HOME="${HOME:-/root}" \
        TERM="${TERM:-linux}" \
        PS1='[loom-installer:\w]\$ ' \
        PATH="${LOOM_INSTALLER_BIN:?}:${PATH}:/run/current-system/sw/bin" \
        bash --norc --noprofile -i || true
}

main() {
    local choice
    while true; do
        show_status
        show_menu
        read -r -p "  Choice [5]: " choice
        choice="${choice:-5}"

        case "${choice}" in
        1)
            "${LOOM_INSTALLER_BIN:?}/loom-install" || err "Installation failed."
            read -r -p "  Press enter to return to the menu. "
            ;;
        2)
            "${LOOM_INSTALLER_BIN:?}/loom-wipe" || err "Wipe failed."
            read -r -p "  Press enter to return to the menu. "
            ;;
        3) systemctl reboot ;;
        4) systemctl poweroff ;;
        5) rescue_shell ;;
        *) err "Not a choice: ${choice}" ;;
        esac
    done
}

main "${@}"
