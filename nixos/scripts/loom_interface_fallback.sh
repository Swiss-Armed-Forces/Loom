# shellcheck shell=bash
#
# The body of `loom-interface-fallback`, which claims a wired port as the
# appliance interface on a box no platform file matches, and records what it
# did for the login screen. nixos/network.nix reads this file into the unit of
# the same name, behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, because a unit `script` string
# is linted by nothing at all. The comment on `%q` below is there because the
# bug it describes shipped, and shellcheck is the only thing that reads this
# between one boot and the next.
#
# `set -e` and nothing more, which is what nixpkgs' makeJobScript wraps a unit
# `script` in (nixos/lib/systemd-lib.nix). Restated so the linter reads the
# program that actually runs.
set -e

readonly APPLIANCE_INTERFACE="${LOOM_APPLIANCE_INTERFACE:?nixos/network.nix must set this}"
readonly FALLBACK_RECORD="${LOOM_FALLBACK_RECORD:?nixos/network.nix must set this}"
readonly AUTO_SELECT="${LOOM_AUTO_SELECT:?nixos/network.nix must set this}"
# The one value that is legitimately empty: no `--interface` was given.
readonly OVERRIDE="${LOOM_INTERFACE_OVERRIDE-}"

# The wait the missing `After=` never provided. Bounded, because a box
# whose udev queue never drains must still come up with whatever it has.
udevadm settle --timeout=30 || true

# Deliberately not brought up here: the scripted network configures and
# raises it, and in setup mode dhcpcd does.
#
# Written through a temporary file, like key-guard.nix's state, so the
# console check can never read half a record.
claim() {
    local chosen="${1}" reason="${2}" alternatives="${3:-}"

    # Never fail the boot over this. A device that refuses to be renamed
    # leaves the box where it would have been anyway, and
    # loom-network-check still reports it on the console.
    if ! ip link set dev "${chosen}" down \
        || ! ip link set dev "${chosen}" name "${APPLIANCE_INTERFACE}"; then
        echo "[!] Could not rename ${chosen} to ${APPLIANCE_INTERFACE}."
        return 1
    fi

    echo "[*] Claimed ${chosen} as ${APPLIANCE_INTERFACE} (${reason})."

    mkdir --parents /run/loom
    # %q on the one value that can contain a space. The record is
    # `.`-sourced by loom-network-check, and `claim` is called with
    # "${candidates[*]:1}" -- so two or more leftover ports produced
    # `LOOM_FALLBACK_ALTERNATIVES=enp2s0 enp3s0`, which bash reads as an
    # assignment followed by the *command* `enp3s0`. Under the `set -e`
    # nixpkgs wraps a unit script in, that aborted loom-network-check: no
    # issue fragment naming the claimed port, and a stale one from the
    # previous boot left in place -- on exactly the box the fallback
    # exists for, with unknown hardware and several wired ports.
    {
        printf 'LOOM_FALLBACK_INTERFACE=%q\n' "${chosen}"
        printf 'LOOM_FALLBACK_REASON=%q\n' "${reason}"
        printf 'LOOM_FALLBACK_ALTERNATIVES=%q\n' "${alternatives}"
    } > "${FALLBACK_RECORD}.tmp"
    mv "${FALLBACK_RECORD}.tmp" "${FALLBACK_RECORD}"
}

if [[ -e "/sys/class/net/${APPLIANCE_INTERFACE}" ]]; then
    echo "[*] ${APPLIANCE_INTERFACE} already exists; udev claimed it."
    exit 0
fi

# An explicit --interface first, and regardless of AUTO_SELECT: the
# operator named a port, which is an instruction rather than a guess.
# This is the path that makes the flag work at all -- see the netMatch
# comment in nixos/network.nix for why the .link file cannot do it by itself.
if [[ -n "${OVERRIDE}" ]]; then
    if [[ -e "/sys/class/net/${OVERRIDE}" ]]; then
        claim "${OVERRIDE}" override || true
        exit 0
    fi
    echo "[!] --interface named ${OVERRIDE}, which does not exist on this box."
fi

if [[ "${AUTO_SELECT}" != 1 ]]; then
    exit 0
fi

mapfile -t candidates < <(loom-wired-nics)

if [[ "${#candidates[@]}" -eq 0 ]]; then
    echo "[!] No wired interface to claim as ${APPLIANCE_INTERFACE}."
    exit 0
fi

claim "${candidates[0]}" auto "${candidates[*]:1}" || true
