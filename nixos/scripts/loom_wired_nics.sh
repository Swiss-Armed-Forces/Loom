# shellcheck shell=bash
#
# The body of `loom-wired-nics`, which lists the box's wired ports in a stable
# order so the interface fallback can claim the first of them.
# nixos/network.nix reads this file into the writeShellApplication of the same
# name, behind a prologue of `LOOM_*` assignments.
#
# A file rather than a string in that module, so `shellcheck -x -o all` covers
# it: writeShellApplication runs shellcheck at build time, but with nixpkgs'
# default options rather than the ones this repository holds its .sh files to.
#
# `set -euo pipefail` restates what writeShellApplication already applies, so
# the linter reads the program that actually runs.
set -euo pipefail

# Space-separated, and deliberately read unquoted in the loop below.
readonly EXCLUDED="${LOOM_NET_EXCLUDE_DRIVERS-}"

for path in /sys/class/net/*; do
    name="$(basename "${path}")"

    if [[ "${name}" == lo ]]; then
        continue
    fi
    if [[ ! -e "${path}/device" ]]; then
        continue
    fi
    if grep --quiet '^DEVTYPE=' "${path}/uevent" 2> /dev/null; then
        continue
    fi
    if [[ "$(cat "${path}/type" 2> /dev/null || echo 0)" != 1 ]]; then
        continue
    fi

    # The driver is read per port rather than matched against `netMatch`,
    # which is a systemd [Match] block nothing here can evaluate.
    driver=""
    if [[ -e "${path}/device/driver" ]]; then
        driver="$(basename "$(readlink --canonicalize "${path}/device/driver")")"
    fi

    skip=false
    # Unquoted on purpose: the point is to split the list on whitespace.
    # shellcheck disable=SC2086
    for excluded in ${EXCLUDED}; do
        if [[ "${driver}" == "${excluded}" ]]; then
            skip=true
            break
        fi
    done
    if [[ "${skip}" == true ]]; then
        echo >&2 "[*] Skipping ${name}: this platform excludes ${driver}."
        continue
    fi

    printf '%s %s\n' \
        "$(basename "$(readlink --canonicalize "${path}/device")")" \
        "${name}"
done | sort | awk '{ print $2 }'
