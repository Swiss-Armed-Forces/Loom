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
    echo "    1) Rescue shell                         [default]"
    echo "    2) Install Loom appliance to the internal disk"
    echo "    3) ERASE ALL DATA on the internal disks"
    echo "    4) Reboot"
    echo "    5) Power off"
    echo
}

# Neither destructive option is reachable by a single keystroke: both run the
# interlock in common.sh, which demands the target's serial number.
main() {
    local choice
    while true; do
        show_status
        show_menu
        printf '  Choice [1]: '
        read -r choice
        choice="${choice:-1}"

        case "${choice}" in
        1)
            echo "  Returning to the menu when this shell exits."
            bash --login || true
            ;;
        2)
            "${LOOM_INSTALLER_BIN:?}/loom-install" || err "Installation failed."
            printf '  Press enter to return to the menu. '
            read -r _
            ;;
        3)
            "${LOOM_INSTALLER_BIN:?}/loom-wipe" || err "Wipe failed."
            printf '  Press enter to return to the menu. '
            read -r _
            ;;
        4) systemctl reboot ;;
        5) systemctl poweroff ;;
        *) err "Not a choice: ${choice}" ;;
        esac
    done
}

main "${@}"
