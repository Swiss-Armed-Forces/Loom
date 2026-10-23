# shellcheck shell=bash
#
# The body of `loom-wifi-check`, which puts a line on the login screen when
# the access point a `--wifi` image promised is not there: no such interface,
# or hostapd refusing to start on a radio with no AP mode. nixos/wifi.nix
# reads this file into the unit of the same name, behind a prologue of
# `LOOM_*` assignments.
#
# A file rather than a string in that module, because a unit `script` string
# is linted by nothing at all.
#
# `set -e` and nothing more, which is what nixpkgs' makeJobScript wraps a unit
# `script` in (nixos/lib/systemd-lib.nix). Restated so the linter reads the
# program that actually runs.
set -e

readonly WIFI_INTERFACE="${LOOM_WIFI_INTERFACE:?nixos/wifi.nix must set this}"

# `61` sorts after network.nix's 60-loom-network.issue, so a box that is
# wrong about both reports the wired problem first. loom-issue-fragment
# owns the indent, the rule, the atomic rename, the journal copy and the
# rule that no backslash reaches an issue file.
if [[ ! -e "/sys/class/net/${WIFI_INTERFACE}" ]]; then
    lines=(
        --warn "${WIFI_INTERFACE} does not exist -- this box has no access point."
        --warn "The platform's radio match did not select anything. Present instead:"
    )
    for candidate in /sys/class/net/*; do
        name="$(basename "${candidate}")"
        [[ "${name}" == lo ]] && continue
        lines+=(--warn "  ${name}")
    done
    lines+=(
        --warn "Rebuild with --wifi-interface <name>, or without --wifi."
        --warn "The wired port still works."
    )
    loom-issue-fragment 61-loom-wifi "${lines[@]}"
    exit 0
fi

if ! systemctl is-active --quiet hostapd.service; then
    loom-issue-fragment 61-loom-wifi \
        --warn "${WIFI_INTERFACE} exists but hostapd is not running -- no access point." \
        --warn "The usual cause is a radio that does not support AP mode. Check with:" \
        --warn "  iw list | grep -A15 'Supported interface modes'" \
        --warn "and look for a line reading '* AP'. Then: journalctl -u hostapd" \
        --warn "The wired port still works."
    exit 0
fi

# Came up. Clear any fragment a previous boot left behind.
rm -f /run/issue.d/61-loom-wifi.issue
exit 0
