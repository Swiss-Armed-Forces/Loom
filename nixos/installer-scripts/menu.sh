#!/usr/bin/env bash
#
# The installer's console menu, on tty1.
#
# This is a TUI rather than extra bootloader entries on purpose: a boot menu
# cannot enumerate disks, so it could never show the operator which drive is
# about to be destroyed, and firmware differs wildly in how it renders menus and
# accepts input. A program on a Linux console behaves the same everywhere.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR
# shellcheck source=common.sh
# shellcheck disable=SC1091
source "${LOOM_INSTALLER_LIB:?LOOM_INSTALLER_LIB is not set}/common.sh"

# How long a finished install holds the console before rebooting itself.
#
# Shorter than modes.nix's 60s poweroff grace on purpose, and not drift: that
# one has to be read by whoever happens to walk past, while this screen is only
# ever reached by an operator who just typed INSTALL and is standing there. 30s
# is enough to copy down a 30-character passphrase, and enter cuts it short.
readonly LOOM_REBOOT_GRACE=30

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

# Reboot into the installed appliance, after a grace period the operator can cut
# short with enter.
#
# The grace exists for the recovery passphrase printed directly above: it is
# also on the installed box's login banner (box.nix), so this is convenience
# rather than the last chance to read it -- which is exactly why it is allowed
# to expire on its own instead of stranding the box at a prompt nobody returns
# to. The one case where the console does hold indefinitely is handled by the
# caller, not here.
countdown_to_reboot() {
    local remaining status announced=0

    for ((remaining = LOOM_REBOOT_GRACE; remaining > 0; remaining--)); do
        if [[ -t 1 ]]; then
            # Repainted in place with \r, so the passphrase above stays on
            # screen. %2d keeps the line a fixed width; without it 9s would
            # leave behind the stray digit of the 10s that came before it.
            printf '\r  Press enter to reboot now (rebooting in %2ds). ' "${remaining}"
        elif ((!announced)); then
            # Off a terminal there is nothing to repaint into, and one line per
            # second in a captured log is worse than no countdown at all.
            printf '  Rebooting in %ds, or press enter to reboot now.\n' "${remaining}"
            announced=1
        fi

        # The read doubles as the one-second sleep.
        status=0
        read -r -t 1 _ || status=$?
        # bash returns >128 when -t expires, so that is the only status that
        # keeps counting. 0 is enter; anything else is EOF or a read error, and
        # continuing on those would spin the whole countdown out in
        # milliseconds the moment stdin is closed.
        if ((status <= 128)); then
            break
        fi
    done

    if [[ -t 1 ]]; then
        printf '\n'
    fi

    halt_console reboot "Rebooting."
}

# The install succeeded, but the box will not boot into it without help.
#
# Restated here rather than left to the warnings loom-install already printed:
# those are emitted before the completion block and the recovery passphrase, so
# on a short console they are several screens up by the time anyone reads this.
hold_for_boot_order() {
    echo
    err "The internal disk is NOT the default boot entry -- see the warning above."
    err "Put it first in the firmware boot order, or this box keeps booting the installer."
    echo
    printf '  Press enter to reboot. '
    read -r _
    halt_console reboot "Rebooting."
}

main() {
    local choice status
    while true; do
        show_status
        show_menu
        printf '  Choice [5]: '
        read -r choice
        choice="${choice:-5}"

        case "${choice}" in
        1)
            # A finished install reboots rather than returning to the menu: the
            # box is done, and every option left here either destroys the disk
            # that was just written or does nothing for it. How long it waits
            # first is the only thing the exit status decides.
            status=0
            "${LOOM_INSTALLER_BIN:?}/loom-install" || status=$?
            case "${status}" in
            0) countdown_to_reboot ;;
            "${LOOM_EXIT_BOOT_ORDER_DEGRADED}") hold_for_boot_order ;;
            *)
                err "Installation failed."
                printf '  Press enter to return to the menu. '
                read -r _
                ;;
            esac
            ;;
        2)
            "${LOOM_INSTALLER_BIN:?}/loom-wipe" || err "Wipe failed."
            printf '  Press enter to return to the menu. '
            read -r _
            ;;
        3) halt_console reboot "Rebooting." ;;
        4) halt_console poweroff "Powering off." ;;
        5) rescue_shell ;;
        *) err "Not a choice: ${choice}" ;;
        esac
    done
}

main "${@}"
