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

    # Drawn from the top each time round the loop, so the menu is never buried
    # under the scroll of whatever ran before it. main() puts its "press enter"
    # after an install or a wipe, which is what keeps their output readable
    # until the operator has actually read it.
    clear_screen

    printf '\n'
    loom_banner

    # Names the release and the box this stick was built for. Two sticks on a
    # desk are otherwise indistinguishable, and the only other place that
    # information exists is the banner on an already-installed box. The eyes
    # above are the mark, not the name, so this line still carries it.
    printf '\n  %sLOOM APPLIANCE INSTALLER  %s%s\n' \
        "${LOOM_BOLD}" "${LOOM_TAG:?LOOM_TAG is not set}" "${LOOM_RESET}"
    printf '  %s\n' "${LOOM_PLATFORM:?LOOM_PLATFORM is not set}"
    printf '  %s\n' "${LOOM_RULE}"

    boot="$(boot_disk)"
    if [[ -n "${boot}" ]]; then
        description="$(disk_description "${boot}")"
        printf '  Boot medium : %s\n' "${description}"
        printf '                %s(never written to by any option below)%s\n' \
            "${LOOM_DIM}" "${LOOM_RESET}"
    else
        printf '  Boot medium : %sCOULD NOT BE IDENTIFIED%s\n' \
            "${LOOM_RED}" "${LOOM_RESET}"
        printf '                Install and wipe will refuse to run.\n'
    fi

    key_dev="/dev/disk/by-partlabel/${LOOM_KEY_LABEL}"
    key_status="$(key_state "${key_dev}")"
    if [[ "${key_status}" == "present" ]]; then
        printf '  LUKS key    : %spresent%s\n' "${LOOM_GREEN}" "${LOOM_RESET}"
    else
        # Not cosmetic: installing on a stick with no key produces a box that
        # partitions, encrypts, and then never boots again.
        printf '  LUKS key    : %s%s -- re-flash with '\''build-appliance-image --flash'\''%s\n' \
            "${LOOM_RED}" "${key_status}" "${LOOM_RESET}"
    fi

    eligible="$(target_disks)"
    if [[ -n "${eligible}" ]]; then
        mapfile -t targets <<<"${eligible}"
        for disk in "${targets[@]}"; do
            description="$(disk_description "${disk}")"
            printf '  Target      : %s%s%s\n' \
                "${LOOM_YELLOW}" "${description}" "${LOOM_RESET}"
        done
    else
        printf '  Target      : no eligible internal NVMe found\n'
    fi
    echo
}

# Only the destructive option is coloured. Ranking works by contrast: paint
# every line and none of them stands out.
show_menu() {
    printf '    1) Install Loom appliance to the internal disk\n'
    printf '    2) %sERASE ALL DATA on the internal disks%s\n' \
        "${LOOM_RED}" "${LOOM_RESET}"
    printf '    3) Reboot\n'
    printf '    4) Power off\n'
    printf '    5) Rescue shell                         [default]\n'
    echo
}

# The rescue shell stays the default: it is the one option that cannot destroy
# anything, so an idle keypress lands somewhere harmless. Both destructive
# options additionally run the interlock in common.sh, which demands the
# target's serial number.
rescue_shell() {
    printf '  %sRescue shell.%s Type '\''exit'\'' or press Ctrl-D to return to the menu.\n\n' \
        "${LOOM_BOLD}" "${LOOM_RESET}"

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

# `systemctl reboot` and `systemctl poweroff` only queue the job and return, so
# without the block afterwards the loop redraws the menu on top of the shutdown
# messages and offers a prompt that nobody should be answering.
halt_console() {
    local subcommand="${1}" message="${2}"
    log "${message}"
    systemctl "${subcommand}"
    sleep infinity
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
            if "${LOOM_INSTALLER_BIN:?}/loom-install"; then
                # A finished install reboots rather than returning to the menu:
                # the box is done, and every option left here either destroys
                # the disk that was just written or does nothing for it. The
                # read still blocks first, so the recovery passphrase stays on
                # screen until somebody has acknowledged it -- and it is on the
                # installed box's login banner afterwards either way.
                read -r -p "  Press enter to reboot into the installed appliance. "
                halt_console reboot "Rebooting."
            else
                err "Installation failed."
                read -r -p "  Press enter to return to the menu. "
            fi
            ;;
        2)
            "${LOOM_INSTALLER_BIN:?}/loom-wipe" || err "Wipe failed."
            read -r -p "  Press enter to return to the menu. "
            ;;
        3) halt_console reboot "Rebooting." ;;
        4) halt_console poweroff "Powering off." ;;
        5) rescue_shell ;;
        *) err "Not a choice: ${choice}" ;;
        esac
    done
}

main "${@}"
